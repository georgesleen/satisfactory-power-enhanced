#include "TestSupport.h"

#include <EnhancedPowerCore/TransformerLink.h>

#include <algorithm>

using namespace EnhancedPower;
using EnhancedPower::Tests::EnergyTolerance;
using EnhancedPower::Tests::SeededRandom;
using EnhancedPower::Tests::Tolerance;

namespace
{

constexpr double RatingMegawatts = 10.0;
constexpr double LossyEfficiency = 0.9;
constexpr double EscrowCapacityMegajoules = 5.0;
constexpr double MaxRechargeMegawatts = 2.0;

LinkParameters LossyLink()
{
	return LinkParameters{
	    .Rating = Megawatts{RatingMegawatts},
	    .Efficiency = LossyEfficiency,
	    .EscrowCapacity = Megajoules{EscrowCapacityMegajoules},
	    .MaxRecharge = Megawatts{MaxRechargeMegawatts},
	};
}

LinkState Holding(double EscrowMegajoules, double LastDeliveredMegawatts)
{
	return LinkState{.Escrow = Megajoules{EscrowMegajoules},
	                 .LastDelivered = Megawatts{LastDeliveredMegawatts}};
}

void CheckPlan(const LinkPlan& Plan, double Offer, double Request)
{
	CHECK_NEAR(Plan.SecondaryOffer.Value, Offer, Tolerance);
	CHECK_NEAR(Plan.PrimaryRequest.Value, Request, Tolerance);
}

} // namespace

TEST_CASE("PlanLink returns an empty plan when Delta is not positive")
{
	const LinkParameters Parameters = LossyLink();
	const LinkState Full = Holding(EscrowCapacityMegajoules, 4.0);
	CheckPlan(PlanLink(Parameters, Full, Seconds{0.0}, true), 0.0, 0.0);
	CheckPlan(PlanLink(Parameters, Full, Seconds{-1.0}, true), 0.0, 0.0);
	CheckPlan(PlanLink(Parameters, Full, Seconds{0.0}, false), 0.0, 0.0);
}

TEST_CASE("An empty link offers nothing and requests the startup charge")
{
	const LinkParameters Parameters = LossyLink();
	const LinkState Empty = Holding(0.0, 0.0);

	SUBCASE("MaxRecharge limits the request on a short step")
	{
		const double Delta = 0.1;
		const double Expected =
		    std::min(EscrowCapacityMegajoules / (LossyEfficiency * Delta), MaxRechargeMegawatts);
		CHECK(Expected == MaxRechargeMegawatts);
		CheckPlan(PlanLink(Parameters, Empty, Seconds{Delta}, true), 0.0, Expected);
	}
	SUBCASE("Escrow room limits the request on a long step")
	{
		const double Delta = 10.0;
		const double Expected =
		    std::min(EscrowCapacityMegajoules / (LossyEfficiency * Delta), MaxRechargeMegawatts);
		CHECK(Expected < MaxRechargeMegawatts);
		CheckPlan(PlanLink(Parameters, Empty, Seconds{Delta}, true), 0.0, Expected);
	}
	SUBCASE("No primary means no request")
	{
		CheckPlan(PlanLink(Parameters, Empty, Seconds{0.1}, false), 0.0, 0.0);
	}
}

TEST_CASE("An empty link supplies the secondary side only after the primary side pays in")
{
	const LinkParameters Parameters = LossyLink();
	const Seconds Delta{0.1};
	constexpr double SecondaryLoad = 3.0;

	const LinkState Empty = Holding(0.0, 0.0);
	const LinkPlan First = PlanLink(Parameters, Empty, Delta, true);
	const LinkSettlement FirstSettled =
	    SettleLink(Parameters, Empty, First, Delta, First.PrimaryRequest, Megawatts{SecondaryLoad});
	CHECK(FirstSettled.State.LastDelivered.Value == 0.0);
	CHECK_NEAR(FirstSettled.OverDelivery.Value, SecondaryLoad * Delta.Value, Tolerance);
	CHECK_NEAR(FirstSettled.State.Escrow.Value, First.PrimaryRequest.Value * Delta.Value * LossyEfficiency,
	           Tolerance);
	CHECK(FirstSettled.State.Escrow.Value > 0.0);

	const LinkPlan Second = PlanLink(Parameters, FirstSettled.State, Delta, true);
	CHECK_NEAR(Second.SecondaryOffer.Value, FirstSettled.State.Escrow.Value / Delta.Value, Tolerance);
	CHECK(Second.SecondaryOffer.Value > 0.0);
}

TEST_CASE("An empty link without a primary never supplies the secondary side")
{
	const LinkParameters Parameters = LossyLink();
	const Seconds Delta{0.1};
	constexpr int StepCount = 100;
	LinkState State = Holding(0.0, 0.0);
	for (int Step = 0; Step < StepCount; Step++)
	{
		const LinkPlan Plan = PlanLink(Parameters, State, Delta, false);
		CHECK(Plan.SecondaryOffer.Value == 0.0);
		CHECK(Plan.PrimaryRequest.Value == 0.0);
		const LinkSettlement Settled =
		    SettleLink(Parameters, State, Plan, Delta, Megawatts{1.0}, Megawatts{1.0});
		CHECK(Settled.State.LastDelivered.Value == 0.0);
		CHECK(Settled.State.Escrow.Value == 0.0);
		State = Settled.State;
	}
}

TEST_CASE("The secondary offer is the reserved escrow, capped by the rating")
{
	const LinkParameters Parameters = LossyLink();
	const LinkState Full = Holding(EscrowCapacityMegajoules, 0.0);
	CHECK_NEAR(PlanLink(Parameters, Full, Seconds{0.1}, true).SecondaryOffer.Value, RatingMegawatts,
	           Tolerance);
	CHECK_NEAR(PlanLink(Parameters, Full, Seconds{1.0}, true).SecondaryOffer.Value, EscrowCapacityMegajoules,
	           Tolerance);
	CHECK_NEAR(PlanLink(Parameters, Holding(0.2, 0.0), Seconds{0.1}, true).SecondaryOffer.Value, 2.0,
	           Tolerance);
	CHECK_NEAR(PlanLink(Parameters, Full, Seconds{0.1}, false).SecondaryOffer.Value, RatingMegawatts,
	           Tolerance);
}

TEST_CASE("PlanLink requests the expected draw plus recharge, bounded by escrow room")
{
	const LinkParameters Parameters = LossyLink();

	SUBCASE("Recharge limits")
	{
		const double Delta = 0.5;
		const double Room = EscrowCapacityMegajoules - (3.0 - 4.0 * Delta);
		const double Expected =
		    std::min(Room / (LossyEfficiency * Delta), 4.0 / LossyEfficiency + MaxRechargeMegawatts);
		CHECK(Expected == 4.0 / LossyEfficiency + MaxRechargeMegawatts);
		CheckPlan(PlanLink(Parameters, Holding(3.0, 4.0), Seconds{Delta}, true), 6.0, Expected);
	}
	SUBCASE("Room limits")
	{
		const double Delta = 1.0;
		const double Room = EscrowCapacityMegajoules - (EscrowCapacityMegajoules - 1.0 * Delta);
		const double Expected = Room / (LossyEfficiency * Delta);
		CheckPlan(PlanLink(Parameters, Holding(EscrowCapacityMegajoules, 1.0), Seconds{Delta}, true),
		          EscrowCapacityMegajoules, Expected);
	}
	SUBCASE("The expected draw never exceeds the reserved escrow")
	{
		const double Delta = 0.1;
		const double Reserved = 0.2;
		const double Room = EscrowCapacityMegajoules - (Reserved - Reserved);
		const double Expected =
		    std::min(Room / (LossyEfficiency * Delta), 8.0 / LossyEfficiency + MaxRechargeMegawatts);
		CheckPlan(PlanLink(Parameters, Holding(Reserved, 8.0), Seconds{Delta}, true), Reserved / Delta,
		          Expected);
	}
}

TEST_CASE("PlanLink clamps an escrow outside its range")
{
	const LinkParameters Parameters = LossyLink();
	const Seconds Delta{1.0};
	const LinkPlan Over = PlanLink(Parameters, Holding(8.0, 0.0), Delta, true);
	const LinkPlan AtCapacity = PlanLink(Parameters, Holding(EscrowCapacityMegajoules, 0.0), Delta, true);
	CheckPlan(Over, AtCapacity.SecondaryOffer.Value, AtCapacity.PrimaryRequest.Value);

	const LinkPlan Under = PlanLink(Parameters, Holding(-1.0, 0.0), Delta, true);
	const LinkPlan AtZero = PlanLink(Parameters, Holding(0.0, 0.0), Delta, true);
	CheckPlan(Under, AtZero.SecondaryOffer.Value, AtZero.PrimaryRequest.Value);
}

TEST_CASE("SettleLink returns the state unchanged when Delta is not positive")
{
	const LinkParameters Parameters = LossyLink();
	const LinkState State = Holding(2.5, 3.0);
	for (const double Delta : {0.0, -0.5})
	{
		CAPTURE(Delta);
		const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
		const LinkSettlement Settled =
		    SettleLink(Parameters, State, Plan, Seconds{Delta}, Megawatts{9.0}, Megawatts{9.0});
		CHECK(Settled.State.Escrow.Value == State.Escrow.Value);
		CHECK(Settled.State.LastDelivered.Value == State.LastDelivered.Value);
		CHECK(Settled.Loss.Value == 0.0);
		CHECK(Settled.Overflow.Value == 0.0);
		CHECK(Settled.OverDelivery.Value == 0.0);
		CHECK(Settled.OverConsumption.Value == 0.0);
	}
}

TEST_CASE("SettleLink moves energy through the escrow and charges the efficiency loss")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.5;
	const LinkState State = Holding(3.0, 4.0);
	const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
	const double Consumed = 2.0;
	const double Delivered = 4.0;

	const LinkSettlement Settled =
	    SettleLink(Parameters, State, Plan, Seconds{Delta}, Megawatts{Consumed}, Megawatts{Delivered});
	CHECK_NEAR(Settled.State.Escrow.Value, 3.0 - Delivered * Delta + Consumed * Delta * LossyEfficiency,
	           Tolerance);
	CHECK_NEAR(Settled.State.LastDelivered.Value, Delivered, Tolerance);
	CHECK_NEAR(Settled.Loss.Value, Consumed * Delta * (1.0 - LossyEfficiency), Tolerance);
	CHECK(Settled.Overflow.Value == 0.0);
	CHECK(Settled.OverDelivery.Value == 0.0);
	CHECK(Settled.OverConsumption.Value == 0.0);
}

TEST_CASE("A lossless link loses nothing")
{
	LinkParameters Parameters = LossyLink();
	Parameters.Efficiency = 1.0;
	const double Delta = 1.0;
	const LinkState State = Holding(1.0, 1.0);
	const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
	const LinkSettlement Settled =
	    SettleLink(Parameters, State, Plan, Seconds{Delta}, Plan.PrimaryRequest, Megawatts{1.0});
	CHECK(Settled.Loss.Value == 0.0);
	CHECK_NEAR(Settled.State.Escrow.Value, 1.0 - 1.0 + Plan.PrimaryRequest.Value, Tolerance);
}

TEST_CASE("Engine reports above the plan are diagnosed and never move escrow")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.5;
	const LinkState State = Holding(3.0, 4.0);
	const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
	const double Offer = Plan.SecondaryOffer.Value;
	const double Request = Plan.PrimaryRequest.Value;
	constexpr double Excess = 7.0;

	const LinkSettlement Honest =
	    SettleLink(Parameters, State, Plan, Seconds{Delta}, Plan.PrimaryRequest, Plan.SecondaryOffer);
	const LinkSettlement Greedy = SettleLink(Parameters, State, Plan, Seconds{Delta},
	                                         Megawatts{Request + Excess}, Megawatts{Offer + Excess});

	CHECK_NEAR(Greedy.OverDelivery.Value, Excess * Delta, Tolerance);
	CHECK_NEAR(Greedy.OverConsumption.Value, Excess * Delta, Tolerance);
	CHECK_NEAR(Greedy.State.Escrow.Value, Honest.State.Escrow.Value, Tolerance);
	CHECK_NEAR(Greedy.State.LastDelivered.Value, Offer, Tolerance);
	CHECK_NEAR(Greedy.Loss.Value, Honest.Loss.Value, Tolerance);
	CHECK_NEAR(Greedy.Overflow.Value, Honest.Overflow.Value, Tolerance);
	CHECK(Honest.OverDelivery.Value == 0.0);
	CHECK(Honest.OverConsumption.Value == 0.0);
}

TEST_CASE("Negative engine reports count as zero and are not diagnosed")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.5;
	const LinkState State = Holding(3.0, 4.0);
	const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
	const LinkSettlement Settled =
	    SettleLink(Parameters, State, Plan, Seconds{Delta}, Megawatts{-5.0}, Megawatts{-5.0});
	CHECK_NEAR(Settled.State.Escrow.Value, 3.0, Tolerance);
	CHECK(Settled.State.LastDelivered.Value == 0.0);
	CHECK(Settled.Loss.Value == 0.0);
	CHECK(Settled.OverDelivery.Value == 0.0);
	CHECK(Settled.OverConsumption.Value == 0.0);
}

TEST_CASE("Lowered engine plans constrain settlement and preserve funded energy")
{
	const LinkParameters Parameters = LossyLink();
	const Seconds Delta{0.5};
	const LinkState State = Holding(3.0, 4.0);
	const LinkPlan Original = PlanLink(Parameters, State, Delta, true);
	constexpr double OfferFraction = 0.25;
	constexpr double RequestFraction = 0.5;
	LinkPlan Lowered = Original;
	Lowered.SecondaryOffer = Original.SecondaryOffer * OfferFraction;
	Lowered.PrimaryRequest = Original.PrimaryRequest * RequestFraction;

	const LinkSettlement Settled =
	    SettleLink(Parameters, State, Lowered, Delta, Original.PrimaryRequest, Original.SecondaryOffer);
	CHECK_NEAR(Settled.State.LastDelivered.Value, Lowered.SecondaryOffer.Value, Tolerance);
	CHECK(Settled.OverDelivery.Value > 0.0);
	CHECK(Settled.OverConsumption.Value > 0.0);
	CHECK_NEAR(Settled.OverDelivery.Value,
	           (Original.SecondaryOffer - Lowered.SecondaryOffer).Value * Delta.Value, Tolerance);
	CHECK_NEAR(Settled.OverConsumption.Value,
	           (Original.PrimaryRequest - Lowered.PrimaryRequest).Value * Delta.Value, Tolerance);
	const double AcceptedInput = Lowered.PrimaryRequest.Value * Delta.Value;
	const double PaidOutput = Settled.State.LastDelivered.Value * Delta.Value;
	CHECK(PaidOutput <= State.Escrow.Value + EnergyTolerance);
	CHECK_NEAR(State.Escrow.Value + AcceptedInput,
	           Settled.State.Escrow.Value + PaidOutput + Settled.Loss.Value + Settled.Overflow.Value,
	           EnergyTolerance);

	LinkPlan Open = Original;
	Open.SecondaryOffer = Megawatts{0.0};
	Open.PrimaryRequest = Megawatts{0.0};
	const LinkSettlement OpenSettled =
	    SettleLink(Parameters, State, Open, Delta, Original.PrimaryRequest, Original.SecondaryOffer);
	CHECK(OpenSettled.State.LastDelivered.Value == 0.0);
	CHECK(OpenSettled.State.Escrow.Value == State.Escrow.Value);
	CHECK(OpenSettled.Loss.Value == 0.0);
	CHECK(OpenSettled.OverDelivery.Value > 0.0);
	CHECK(OpenSettled.OverConsumption.Value > 0.0);
}

TEST_CASE("Energy the escrow cannot hold is reported as overflow")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.5;
	const LinkState State = Holding(EscrowCapacityMegajoules, 4.0);
	const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
	REQUIRE(Plan.PrimaryRequest.Value > 0.0);

	const LinkSettlement Settled =
	    SettleLink(Parameters, State, Plan, Seconds{Delta}, Plan.PrimaryRequest, Megawatts{0.0});
	const double Credit = Plan.PrimaryRequest.Value * Delta * LossyEfficiency;
	CHECK_NEAR(Settled.State.Escrow.Value, EscrowCapacityMegajoules, Tolerance);
	CHECK_NEAR(Settled.Overflow.Value, Credit, Tolerance);
	CHECK(Settled.OverConsumption.Value == 0.0);
	CHECK_NEAR(Settled.Loss.Value, Plan.PrimaryRequest.Value * Delta * (1.0 - LossyEfficiency), Tolerance);
}

TEST_CASE("A steady load below the rating settles at the load with only the efficiency loss")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.1;
	constexpr double SecondaryLoad = 3.0;
	constexpr int StepCount = 1000;

	LinkState State = Holding(0.0, 0.0);
	LinkPlan Plan{};
	LinkSettlement Settled{};
	for (int Step = 0; Step < StepCount; Step++)
	{
		Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
		const double Drawn = std::min(SecondaryLoad, Plan.SecondaryOffer.Value);
		Settled = SettleLink(Parameters, State, Plan, Seconds{Delta}, Plan.PrimaryRequest, Megawatts{Drawn});
		State = Settled.State;
	}
	CHECK_NEAR(State.LastDelivered.Value, SecondaryLoad, Tolerance);
	CHECK_NEAR(State.Escrow.Value, EscrowCapacityMegajoules, EnergyTolerance);
	CHECK_NEAR(Plan.PrimaryRequest.Value, SecondaryLoad / LossyEfficiency, EnergyTolerance);
	CHECK_NEAR(Settled.Loss.Value, SecondaryLoad / LossyEfficiency * Delta * (1.0 - LossyEfficiency),
	           EnergyTolerance);
	CHECK_NEAR(Settled.Overflow.Value, 0.0, EnergyTolerance);
}

TEST_CASE("A steady load above the rating is held at the rating")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.1;
	constexpr double SecondaryLoad = 15.0;
	constexpr int StepCount = 1000;

	LinkState State = Holding(0.0, 0.0);
	for (int Step = 0; Step < StepCount; Step++)
	{
		const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, true);
		REQUIRE(Plan.SecondaryOffer.Value <= RatingMegawatts + Tolerance);
		const double Drawn = std::min(SecondaryLoad, Plan.SecondaryOffer.Value);
		State =
		    SettleLink(Parameters, State, Plan, Seconds{Delta}, Plan.PrimaryRequest, Megawatts{Drawn}).State;
	}
	CHECK_NEAR(State.LastDelivered.Value, RatingMegawatts, Tolerance);
}

TEST_CASE("Losing the primary drains the escrow and then the secondary browns out")
{
	const LinkParameters Parameters = LossyLink();
	const double Delta = 0.1;
	constexpr double SecondaryLoad = 3.0;
	constexpr int StepCount = 100;

	LinkState State = Holding(EscrowCapacityMegajoules, SecondaryLoad);
	double DeliveredEnergy = 0.0;
	for (int Step = 0; Step < StepCount; Step++)
	{
		const LinkPlan Plan = PlanLink(Parameters, State, Seconds{Delta}, false);
		REQUIRE(Plan.PrimaryRequest.Value == 0.0);
		const double Drawn = std::min(SecondaryLoad, Plan.SecondaryOffer.Value);
		const LinkSettlement Settled =
		    SettleLink(Parameters, State, Plan, Seconds{Delta}, Megawatts{0.0}, Megawatts{Drawn});
		DeliveredEnergy += Settled.State.LastDelivered.Value * Delta;
		State = Settled.State;
	}
	CHECK_NEAR(DeliveredEnergy, EscrowCapacityMegajoules, EnergyTolerance);
	CHECK_NEAR(State.Escrow.Value, 0.0, EnergyTolerance);
	CHECK(PlanLink(Parameters, State, Seconds{Delta}, false).SecondaryOffer.Value <= EnergyTolerance / Delta);
}

TEST_CASE("Randomized adversarial engine reports and lowered plans never create energy")
{
	struct Variant
	{
		double Efficiency;
		double MaxRecharge;
		std::uint64_t Seed;
	};
	const Variant Variants[] = {
	    {LossyEfficiency, MaxRechargeMegawatts, 0xA11CE5EEDULL},
	    {1.0, MaxRechargeMegawatts, 0xB0B5EEDULL},
	    {0.35, 0.0, 0xCAFE5EEDULL},
	    {0.97, 40.0, 0xD00D5EEDULL},
	};
	constexpr int StepCount = 100000;

	for (const Variant& Each : Variants)
	{
		CAPTURE(Each.Efficiency);
		CAPTURE(Each.MaxRecharge);
		LinkParameters Parameters = LossyLink();
		Parameters.Efficiency = Each.Efficiency;
		Parameters.MaxRecharge = Megawatts{Each.MaxRecharge};
		SeededRandom Random{Each.Seed};

		LinkState State = Holding(Random.Uniform(0.0, EscrowCapacityMegajoules), Random.Uniform(0.0, 12.0));
		const double InitialEscrow = State.Escrow.Value;
		double TotalCredit = 0.0;
		double TotalDelivered = 0.0;
		double TotalOverflow = 0.0;

		for (int Step = 0; Step < StepCount; Step++)
		{
			const double Delta = Random.Chance(0.01) ? Random.Uniform(-0.5, 0.0) : Random.Uniform(0.001, 0.5);
			const bool PrimaryAvailable = Random.Chance(0.8);
			const LinkPlan Planned = PlanLink(Parameters, State, Seconds{Delta}, PrimaryAvailable);
			LinkPlan Plan = Planned;
			if (Random.Chance(0.3))
			{
				Plan.SecondaryOffer = Planned.SecondaryOffer * Random.Uniform(0.0, 1.0);
				Plan.PrimaryRequest = Planned.PrimaryRequest * Random.Uniform(0.0, 1.0);
			}
			const double Offer = Plan.SecondaryOffer.Value;
			const double Request = Plan.PrimaryRequest.Value;

			const auto Report = [&Random](double PlannedPower)
			{
				const double Pick = Random.Uniform(0.0, 1.0);
				if (Pick < 0.5)
				{
					return PlannedPower * Random.Uniform(0.0, 1.0);
				}
				if (Pick < 0.7)
				{
					return PlannedPower;
				}
				if (Pick < 0.85)
				{
					return PlannedPower + Random.Uniform(0.0, 50.0);
				}
				if (Pick < 0.95)
				{
					return -Random.Uniform(0.0, 20.0);
				}
				return 0.0;
			};
			const double PrimaryConsumed =
			    Report(Random.Chance(0.5) ? Request : Planned.PrimaryRequest.Value);
			const double SecondaryDelivered =
			    Report(Random.Chance(0.5) ? Offer : Planned.SecondaryOffer.Value);

			const LinkSettlement Settled =
			    SettleLink(Parameters, State, Plan, Seconds{Delta}, Megawatts{PrimaryConsumed},
			               Megawatts{SecondaryDelivered});
			const double Before = State.Escrow.Value;
			const double After = Settled.State.Escrow.Value;
			const double Delivered = Settled.State.LastDelivered.Value;

			REQUIRE(After >= 0.0);
			REQUIRE(After <= EscrowCapacityMegajoules + Tolerance);
			REQUIRE(Settled.Loss.Value >= 0.0);
			REQUIRE(Settled.Overflow.Value >= 0.0);
			REQUIRE(Settled.OverDelivery.Value >= 0.0);
			REQUIRE(Settled.OverConsumption.Value >= 0.0);

			if (Delta <= 0.0)
			{
				REQUIRE(Offer == 0.0);
				REQUIRE(Request == 0.0);
				REQUIRE(After == Before);
				REQUIRE(Delivered == State.LastDelivered.Value);
				continue;
			}

			REQUIRE(Offer >= 0.0);
			REQUIRE(Offer <= RatingMegawatts + Tolerance);
			REQUIRE(Request >= 0.0);
			if (!PrimaryAvailable)
			{
				REQUIRE(Request == 0.0);
			}
			REQUIRE(Request <= State.LastDelivered.Value / Each.Efficiency + Each.MaxRecharge + Tolerance);

			const double Consumed = std::clamp(PrimaryConsumed, 0.0, Request);
			const double Credit = Consumed * Delta * Each.Efficiency;
			REQUIRE(Delivered >= 0.0);
			REQUIRE(Delivered <= Offer + Tolerance);
			REQUIRE(Delivered * Delta <= Before + EnergyTolerance);
			REQUIRE(std::abs((After - Before) - (Credit - Delivered * Delta - Settled.Overflow.Value)) <=
			        EnergyTolerance);
			REQUIRE(std::abs(Settled.Loss.Value - Consumed * Delta * (1.0 - Each.Efficiency)) <=
			        EnergyTolerance);
			REQUIRE(std::abs(Settled.OverDelivery.Value -
			                 std::max(SecondaryDelivered - Offer, 0.0) * Delta) <= EnergyTolerance);
			REQUIRE(std::abs(Settled.OverConsumption.Value -
			                 std::max(PrimaryConsumed - Request, 0.0) * Delta) <= EnergyTolerance);

			TotalCredit += Credit;
			TotalDelivered += Delivered * Delta;
			TotalOverflow += Settled.Overflow.Value;
			State = Settled.State;
		}

		CHECK(TotalDelivered <= InitialEscrow + TotalCredit + EnergyTolerance);
		CHECK_NEAR(State.Escrow.Value, InitialEscrow + TotalCredit - TotalDelivered - TotalOverflow,
		           EnergyTolerance);
	}
}
