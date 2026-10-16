#include "TestSupport.h"

#include <EnhancedPowerCore/FastBuffer.h>

#include <algorithm>

using namespace EnhancedPower;
using EnhancedPower::Tests::SeededRandom;
using EnhancedPower::Tests::Tolerance;

namespace
{

constexpr double CapacityMegajoules = 10.0;
constexpr double MaxChargeMegawatts = 4.0;
constexpr double MaxDischargeMegawatts = 5.0;
constexpr double LossyEfficiency = 0.8;

BufferParameters LossyBuffer()
{
	return BufferParameters{
	    .Capacity = Megajoules{CapacityMegajoules},
	    .MaxCharge = Megawatts{MaxChargeMegawatts},
	    .MaxDischarge = Megawatts{MaxDischargeMegawatts},
	    .ChargeEfficiency = LossyEfficiency,
	};
}

BufferState Holding(double StoredMegajoules)
{
	return BufferState{.Stored = Megajoules{StoredMegajoules}};
}

void CheckStep(const BufferStep& Step, double Stored, double Absorbed, double Delivered)
{
	CHECK_NEAR(Step.State.Stored.Value, Stored, Tolerance);
	CHECK_NEAR(Step.Absorbed.Value, Absorbed, Tolerance);
	CHECK_NEAR(Step.Delivered.Value, Delivered, Tolerance);
}

} // namespace

TEST_CASE("StepBuffer does nothing but clamp when Delta is not positive")
{
	const BufferParameters Parameters = LossyBuffer();
	CheckStep(StepBuffer(Parameters, Holding(4.0), Megawatts{-3.0}, Seconds{0.0}), 4.0, 0.0, 0.0);
	CheckStep(StepBuffer(Parameters, Holding(4.0), Megawatts{3.0}, Seconds{-1.0}), 4.0, 0.0, 0.0);
	CheckStep(StepBuffer(Parameters, Holding(12.0), Megawatts{-3.0}, Seconds{0.0}), CapacityMegajoules, 0.0,
	          0.0);
	CheckStep(StepBuffer(Parameters, Holding(-2.0), Megawatts{3.0}, Seconds{0.0}), 0.0, 0.0, 0.0);
}

TEST_CASE("StepBuffer does nothing but clamp when the balance is zero")
{
	const BufferParameters Parameters = LossyBuffer();
	CheckStep(StepBuffer(Parameters, Holding(4.0), Megawatts{0.0}, Seconds{1.0}), 4.0, 0.0, 0.0);
	CheckStep(StepBuffer(Parameters, Holding(15.0), Megawatts{0.0}, Seconds{1.0}), CapacityMegajoules, 0.0,
	          0.0);
	CheckStep(StepBuffer(Parameters, Holding(-1.0), Megawatts{0.0}, Seconds{1.0}), 0.0, 0.0, 0.0);
}

TEST_CASE("A deficit discharges up to the smallest of demand, rate, and stored energy")
{
	const BufferParameters Parameters = LossyBuffer();

	SUBCASE("Demand limits")
	{
		CheckStep(StepBuffer(Parameters, Holding(10.0), Megawatts{-2.0}, Seconds{1.0}), 8.0, 0.0, 2.0);
	}
	SUBCASE("Discharge rate limits")
	{
		CheckStep(StepBuffer(Parameters, Holding(10.0), Megawatts{-20.0}, Seconds{1.0}), 5.0, 0.0, 5.0);
	}
	SUBCASE("Stored energy limits")
	{
		CheckStep(StepBuffer(Parameters, Holding(1.0), Megawatts{-20.0}, Seconds{1.0}), 0.0, 0.0, 1.0);
		CheckStep(StepBuffer(Parameters, Holding(1.0), Megawatts{-20.0}, Seconds{0.5}), 0.0, 0.0, 2.0);
	}
	SUBCASE("An empty buffer delivers nothing")
	{
		CheckStep(StepBuffer(Parameters, Holding(0.0), Megawatts{-3.0}, Seconds{1.0}), 0.0, 0.0, 0.0);
	}
	SUBCASE("Discharge has no efficiency loss")
	{
		CheckStep(StepBuffer(Parameters, Holding(6.0), Megawatts{-4.0}, Seconds{0.5}), 4.0, 0.0, 4.0);
	}
}

TEST_CASE("A surplus charges up to the smallest of surplus, rate, and room after efficiency")
{
	const BufferParameters Parameters = LossyBuffer();

	SUBCASE("Surplus limits")
	{
		CheckStep(StepBuffer(Parameters, Holding(0.0), Megawatts{2.0}, Seconds{1.0}), 2.0 * LossyEfficiency,
		          2.0, 0.0);
	}
	SUBCASE("Charge rate limits")
	{
		CheckStep(StepBuffer(Parameters, Holding(0.0), Megawatts{20.0}, Seconds{1.0}), 4.0 * LossyEfficiency,
		          4.0, 0.0);
	}
	SUBCASE("Room limits, and the buffer fills exactly")
	{
		const double Room = 1.0;
		CheckStep(StepBuffer(Parameters, Holding(CapacityMegajoules - Room), Megawatts{20.0}, Seconds{1.0}),
		          CapacityMegajoules, Room / LossyEfficiency, 0.0);
	}
	SUBCASE("A full buffer absorbs nothing")
	{
		CheckStep(StepBuffer(Parameters, Holding(CapacityMegajoules), Megawatts{3.0}, Seconds{1.0}),
		          CapacityMegajoules, 0.0, 0.0);
	}
}

TEST_CASE("StepBuffer clamps the stored energy before it steps")
{
	const BufferParameters Parameters = LossyBuffer();
	CheckStep(StepBuffer(Parameters, Holding(15.0), Megawatts{-2.0}, Seconds{1.0}), 8.0, 0.0, 2.0);
	CheckStep(StepBuffer(Parameters, Holding(15.0), Megawatts{2.0}, Seconds{1.0}), CapacityMegajoules, 0.0,
	          0.0);
	CheckStep(StepBuffer(Parameters, Holding(-5.0), Megawatts{-2.0}, Seconds{1.0}), 0.0, 0.0, 0.0);
	CheckStep(StepBuffer(Parameters, Holding(-5.0), Megawatts{2.0}, Seconds{1.0}), 2.0 * LossyEfficiency, 2.0,
	          0.0);
}

TEST_CASE("A zero-capacity buffer never moves energy")
{
	BufferParameters Parameters = LossyBuffer();
	Parameters.Capacity = Megajoules{0.0};
	CheckStep(StepBuffer(Parameters, Holding(0.0), Megawatts{5.0}, Seconds{1.0}), 0.0, 0.0, 0.0);
	CheckStep(StepBuffer(Parameters, Holding(0.0), Megawatts{-5.0}, Seconds{1.0}), 0.0, 0.0, 0.0);
}

TEST_CASE("A full buffer covers a short peak and then stops")
{
	const BufferParameters Parameters = LossyBuffer();
	constexpr double PeakMegawatts = 5.0;
	constexpr double StepSeconds = 0.1;
	constexpr int StepCount = 100;
	const double CoverSeconds = CapacityMegajoules / PeakMegawatts;

	BufferState State = Holding(CapacityMegajoules);
	double DeliveredEnergy = 0.0;
	double CoveredSeconds = 0.0;
	for (int Step = 0; Step < StepCount; Step++)
	{
		const BufferStep Result =
		    StepBuffer(Parameters, State, Megawatts{-PeakMegawatts}, Seconds{StepSeconds});
		DeliveredEnergy += Result.Delivered.Value * StepSeconds;
		if (Result.Delivered.Value >= PeakMegawatts - Tolerance)
		{
			CoveredSeconds += StepSeconds;
		}
		State = Result.State;
	}
	CHECK_NEAR(DeliveredEnergy, CapacityMegajoules, Tolerance);
	CHECK_NEAR(CoveredSeconds, CoverSeconds, StepSeconds + Tolerance);
	CHECK_NEAR(State.Stored.Value, 0.0, Tolerance);
}

TEST_CASE("Randomized steps never deliver more than stored and keep the energy ledger")
{
	const BufferParameters Parameters = LossyBuffer();
	SeededRandom Random{0x5EEDBA77E2ULL};
	constexpr int StepCount = 200000;
	constexpr double LedgerTolerance = Tolerance;

	BufferState State = Holding(Random.Uniform(0.0, CapacityMegajoules));
	const double InitialStored = State.Stored.Value;
	long double TotalDelivered = 0.0L;
	long double TotalStoredIn = 0.0L;

	for (int Step = 0; Step < StepCount; Step++)
	{
		const double Delta = Random.Chance(0.02) ? Random.Uniform(-1.0, 0.0) : Random.Uniform(0.001, 2.0);
		const double Balance = Random.Chance(0.05) ? 0.0 : Random.Uniform(-12.0, 12.0);
		const double Before = std::clamp(State.Stored.Value, 0.0, CapacityMegajoules);

		const BufferStep Result = StepBuffer(Parameters, State, Megawatts{Balance}, Seconds{Delta});
		const double After = Result.State.Stored.Value;
		const double Absorbed = Result.Absorbed.Value;
		const double Delivered = Result.Delivered.Value;

		REQUIRE(After >= 0.0);
		REQUIRE(After <= CapacityMegajoules);
		REQUIRE(Absorbed >= 0.0);
		REQUIRE(Delivered >= 0.0);
		REQUIRE((Absorbed == 0.0 || Delivered == 0.0));
		if (Delta <= 0.0)
		{
			REQUIRE(Absorbed == 0.0);
			REQUIRE(Delivered == 0.0);
			REQUIRE(After == Before);
		}
		else
		{
			REQUIRE(Delivered <= MaxDischargeMegawatts + Tolerance);
			REQUIRE(Absorbed <= MaxChargeMegawatts + Tolerance);
			REQUIRE(Delivered <= std::max(-Balance, 0.0) + Tolerance);
			REQUIRE(Absorbed <= std::max(Balance, 0.0) + Tolerance);
			REQUIRE(Delivered * Delta <= Before + LedgerTolerance);
			REQUIRE(std::abs(After - (Before - Delivered * Delta + Absorbed * Delta * LossyEfficiency)) <=
			        LedgerTolerance);
			TotalDelivered += Delivered * Delta;
			TotalStoredIn += Absorbed * Delta * LossyEfficiency;
		}
		State = Result.State;
	}
	CHECK(TotalDelivered <= InitialStored + TotalStoredIn + LedgerTolerance);
	CHECK_NEAR(State.Stored.Value, InitialStored + TotalStoredIn - TotalDelivered, LedgerTolerance);
}
