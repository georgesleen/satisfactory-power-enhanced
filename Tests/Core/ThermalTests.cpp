#include "TestSupport.h"

#include <EnhancedPowerCore/Thermal.h>

#include <cmath>
#include <limits>
#include <optional>

using namespace EnhancedPower;
using EnhancedPower::Tests::Tolerance;

namespace
{

constexpr double TimeConstantSeconds = 60.0;

ThermalParameters DefaultParameters()
{
	return ThermalParameters{.TimeConstant = Seconds{TimeConstantSeconds}};
}

/// Parameters whose trip heat is the exact square of `ExactTripRatio`.
constexpr double ExactTripRatio = 1.5;
ThermalParameters ExactTripParameters()
{
	return ThermalParameters{
	    .TimeConstant = Seconds{TimeConstantSeconds},
	    .WarningHeat = 1.0,
	    .TripHeat = ExactTripRatio * ExactTripRatio,
	};
}

void CheckSameState(const ThermalState& Actual, const ThermalState& Expected)
{
	CHECK(Actual.Heat == Expected.Heat);
	CHECK(Actual.Tripped == Expected.Tripped);
}

} // namespace

TEST_CASE("StepThermal returns the state unchanged when Delta is not positive")
{
	const ThermalParameters Parameters = DefaultParameters();
	const ThermalState Warm{.Heat = 0.8, .Tripped = false};
	const ThermalState Hot{.Heat = 1.7, .Tripped = true};

	CheckSameState(StepThermal(Parameters, Warm, 2.0, Seconds{0.0}), Warm);
	CheckSameState(StepThermal(Parameters, Warm, 2.0, Seconds{-5.0}), Warm);
	CheckSameState(StepThermal(Parameters, Hot, 0.0, Seconds{0.0}), Hot);
	CheckSameState(StepThermal(Parameters, Hot, 0.0, Seconds{-1.0}), Hot);
}

TEST_CASE("A transformer at exactly its rating settles at heat 1 and never trips")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double RatedLoad = 1.0;
	constexpr double StepSeconds = 1.0;
	constexpr int StepCount = 10000;

	CHECK_FALSE(TimeToTrip(Parameters, ThermalState{}, RatedLoad).has_value());

	ThermalState State{};
	for (int Step = 0; Step < StepCount; Step++)
	{
		State = StepThermal(Parameters, State, RatedLoad, Seconds{StepSeconds});
		REQUIRE_FALSE(State.Tripped);
		REQUIRE(State.Heat <= 1.0 + Tolerance);
	}
	CHECK_NEAR(State.Heat, 1.0, Tolerance);
	CHECK(ClassifyThermal(Parameters, State) != ThermalStatus::Tripped);
}

TEST_CASE("One step of 2d equals two steps of d when no trip occurs")
{
	const ThermalParameters Parameters = DefaultParameters();
	struct Case
	{
		double StartHeat;
		double LoadRatio;
		double DeltaSeconds;
	};
	const Case Cases[] = {
	    {0.0, 1.1, 7.5}, {1.3, 0.5, 20.0}, {0.9, 0.0, 45.0}, {0.2, 1.0, 0.016}, {1.0, 1.15, 120.0},
	};
	for (const Case& Each : Cases)
	{
		CAPTURE(Each.StartHeat);
		CAPTURE(Each.LoadRatio);
		CAPTURE(Each.DeltaSeconds);
		const ThermalState Start{.Heat = Each.StartHeat, .Tripped = false};
		const ThermalState Once =
		    StepThermal(Parameters, Start, Each.LoadRatio, Seconds{2.0 * Each.DeltaSeconds});
		const ThermalState Half = StepThermal(Parameters, Start, Each.LoadRatio, Seconds{Each.DeltaSeconds});
		const ThermalState Twice = StepThermal(Parameters, Half, Each.LoadRatio, Seconds{Each.DeltaSeconds});
		CHECK_FALSE(Once.Tripped);
		CHECK_FALSE(Twice.Tripped);
		CHECK_NEAR(Once.Heat, Twice.Heat, Tolerance);
	}
}

TEST_CASE("StepThermal moves heat toward the square of the load ratio")
{
	const ThermalParameters Parameters = DefaultParameters();
	const ThermalState Cold{};
	const ThermalState Heated = StepThermal(Parameters, Cold, 1.1, Seconds{TimeConstantSeconds});
	CHECK(Heated.Heat > 0.0);
	CHECK(Heated.Heat < 1.1 * 1.1);
	CHECK_NEAR(Heated.Heat, 1.1 * 1.1 * (1.0 - std::exp(-1.0)), Tolerance);

	const ThermalState Cooled = StepThermal(Parameters, ThermalState{.Heat = 1.2}, 0.5, Seconds{30.0});
	CHECK(Cooled.Heat < 1.2);
	CHECK(Cooled.Heat > 0.25);
}

TEST_CASE("A negative or NaN load ratio counts as zero")
{
	const ThermalParameters Parameters = DefaultParameters();
	const ThermalState Warm{.Heat = 1.2, .Tripped = false};
	const Seconds Delta{10.0};
	const ThermalState Idle = StepThermal(Parameters, Warm, 0.0, Delta);

	const ThermalState Negative = StepThermal(Parameters, Warm, -3.0, Delta);
	CHECK_NEAR(Negative.Heat, Idle.Heat, Tolerance);
	CHECK_FALSE(Negative.Tripped);

	const ThermalState NotANumber =
	    StepThermal(Parameters, Warm, std::numeric_limits<double>::quiet_NaN(), Delta);
	CHECK(std::isfinite(NotANumber.Heat));
	CHECK_NEAR(NotANumber.Heat, Idle.Heat, Tolerance);
	CHECK_FALSE(NotANumber.Tripped);

	CHECK_FALSE(TimeToTrip(Parameters, ThermalState{}, -3.0).has_value());
	CHECK_FALSE(TimeToTrip(Parameters, ThermalState{}, std::numeric_limits<double>::quiet_NaN()).has_value());
}

TEST_CASE("Heat equal to TripHeat trips")
{
	const ThermalParameters Parameters = ExactTripParameters();
	const ThermalState AtTrip{.Heat = Parameters.TripHeat, .Tripped = false};
	const ThermalState Next = StepThermal(Parameters, AtTrip, ExactTripRatio, Seconds{1.0});
	CHECK_NEAR(Next.Heat, Parameters.TripHeat * std::exp(-1.0 / TimeConstantSeconds), Tolerance);
	CHECK(Next.Tripped);
}

TEST_CASE("A load whose square equals TripHeat never trips in finite time")
{
	const ThermalParameters Parameters = ExactTripParameters();
	CHECK_FALSE(TimeToTrip(Parameters, ThermalState{}, ExactTripRatio).has_value());
	CHECK_FALSE(TimeToTrip(Parameters, ThermalState{.Heat = 1.9}, ExactTripRatio).has_value());

	ThermalState State{};
	constexpr int StepCount = 600;
	for (int Step = 0; Step < StepCount; Step++)
	{
		State = StepThermal(Parameters, State, ExactTripRatio, Seconds{1.0});
		REQUIRE_FALSE(State.Tripped);
	}
	CHECK(State.Heat < Parameters.TripHeat);
}

TEST_CASE("A threshold-equilibrium load never trips through rounding on long or subsequent steps")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double ThresholdLoadRatio = 1.2;
	constexpr double LongStepSeconds = 2400.0;
	constexpr double NextStepSeconds = 1.0;
	const ThermalState Cold{};
	CHECK_FALSE(TimeToTrip(Parameters, Cold, ThresholdLoadRatio).has_value());
	const ThermalState Settled = StepThermal(Parameters, Cold, ThresholdLoadRatio, Seconds{LongStepSeconds});
	CHECK_FALSE(Settled.Tripped);
	CHECK(Settled.Heat == std::nextafter(Parameters.TripHeat, 0.0));
	CHECK(Settled.Heat < Parameters.TripHeat);
	CHECK(ClassifyThermal(Parameters, Settled) != ThermalStatus::Tripped);
	CHECK_FALSE(TimeToTrip(Parameters, Settled, ThresholdLoadRatio).has_value());
	const ThermalState Next = StepThermal(Parameters, Settled, ThresholdLoadRatio, Seconds{NextStepSeconds});
	CHECK_FALSE(Next.Tripped);
	CHECK(Next.Heat < Parameters.TripHeat);
	CHECK(ClassifyThermal(Parameters, Next) != ThermalStatus::Tripped);
}

TEST_CASE("A load at or below the trip threshold never trips on any step size")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double ThresholdLoadRatio = 1.2;
	constexpr double BelowThresholdLoadRatio = 1.19;
	const double LoadRatios[] = {ThresholdLoadRatio, BelowThresholdLoadRatio};
	const double StartHeats[] = {0.0, 1.0, 1.43, std::nextafter(Parameters.TripHeat, 0.0)};
	const double Durations[] = {0.016, 1.0, TimeConstantSeconds, 2400.0, 1e6};
	constexpr int StepCount = 5;
	for (const double LoadRatio : LoadRatios)
	{
		CAPTURE(LoadRatio);
		for (const double StartHeat : StartHeats)
		{
			CAPTURE(StartHeat);
			for (const double Duration : Durations)
			{
				CAPTURE(Duration);
				ThermalState State{.Heat = StartHeat, .Tripped = false};
				for (int Step = 0; Step < StepCount && !State.Tripped; Step++)
				{
					State = StepThermal(Parameters, State, LoadRatio, Seconds{Duration});
					CHECK_FALSE(State.Tripped);
					CHECK(State.Heat < Parameters.TripHeat);
					CHECK(ClassifyThermal(Parameters, State) != ThermalStatus::Tripped);
				}
			}
		}
	}
}

TEST_CASE("Heat at or above TripHeat latches before cooling even under a safe load")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double AboveTripHeat = 2.0;
	constexpr double LowLoadRatio = 0.5;
	const double InitialHeats[] = {Parameters.TripHeat, AboveTripHeat};
	const double Durations[] = {1.0, 10.0 * TimeConstantSeconds, 1e6};
	for (const double InitialHeat : InitialHeats)
	{
		CAPTURE(InitialHeat);
		const ThermalState Start{.Heat = InitialHeat, .Tripped = false};
		CHECK(ClassifyThermal(Parameters, Start) == ThermalStatus::Tripped);
		CHECK(TimeToTrip(Parameters, Start, LowLoadRatio) == Seconds{0.0});
		CheckSameState(StepThermal(Parameters, Start, LowLoadRatio, Seconds{0.0}), Start);
		CheckSameState(StepThermal(Parameters, Start, LowLoadRatio, Seconds{-1.0}), Start);
		for (const double Duration : Durations)
		{
			CAPTURE(Duration);
			const ThermalState Next = StepThermal(Parameters, Start, LowLoadRatio, Seconds{Duration});
			CHECK(Next.Tripped);
			CHECK_NEAR(Next.Heat, InitialHeat * std::exp(-Duration / TimeConstantSeconds), Tolerance);
			CHECK(ClassifyThermal(Parameters, Next) == ThermalStatus::Tripped);
			CHECK(TimeToTrip(Parameters, Next, LowLoadRatio) == Seconds{0.0});
			const ThermalState Later = StepThermal(Parameters, Next, LowLoadRatio, Seconds{Duration});
			CHECK(Later.Tripped);
			CHECK(Later.Heat <= Next.Heat);
		}
	}
}

TEST_CASE("Sustained 130 percent load trips within the time TimeToTrip predicts")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double Overload = 1.3;
	constexpr double StepSeconds = 0.01;
	constexpr int StepLimit = 1000000;

	const double StartHeats[] = {0.0, 0.5, 1.0, 1.4};
	for (const double StartHeat : StartHeats)
	{
		CAPTURE(StartHeat);
		const ThermalState Start{.Heat = StartHeat, .Tripped = false};
		const std::optional<Seconds> Predicted = TimeToTrip(Parameters, Start, Overload);
		REQUIRE(Predicted.has_value());
		const double Expected = TimeConstantSeconds * std::log((Overload * Overload - StartHeat) /
		                                                       (Overload * Overload - Parameters.TripHeat));
		CHECK_NEAR(Predicted->Value, Expected, Tolerance);

		ThermalState State = Start;
		int Steps = 0;
		while (!State.Tripped && Steps < StepLimit)
		{
			State = StepThermal(Parameters, State, Overload, Seconds{StepSeconds});
			Steps++;
		}
		REQUIRE(State.Tripped);
		const double Elapsed = Steps * StepSeconds;
		CAPTURE(Elapsed);
		CAPTURE(Predicted->Value);
		CHECK(Elapsed >= Predicted->Value - StepSeconds);
		CHECK(Elapsed <= Predicted->Value + StepSeconds);
	}
}

TEST_CASE("A single step just past TimeToTrip trips and a step just before does not")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double Overload = 1.5;
	constexpr double Margin = 1e-6;
	const ThermalState Start{.Heat = 0.3, .Tripped = false};
	const std::optional<Seconds> Predicted = TimeToTrip(Parameters, Start, Overload);
	REQUIRE(Predicted.has_value());
	CHECK(Predicted->Value > 0.0);

	const ThermalState Exact = StepThermal(Parameters, Start, Overload, *Predicted);
	CHECK_NEAR(Exact.Heat, Parameters.TripHeat, Tolerance);
	CHECK(StepThermal(Parameters, Start, Overload, *Predicted * (1.0 + Margin)).Tripped);
	CHECK_FALSE(StepThermal(Parameters, Start, Overload, *Predicted * (1.0 - Margin)).Tripped);
}

TEST_CASE("TimeToTrip precedence")
{
	const ThermalParameters Parameters = DefaultParameters();

	SUBCASE("A tripped state returns zero for any load")
	{
		const ThermalState Tripped{.Heat = 0.0, .Tripped = true};
		CHECK(TimeToTrip(Parameters, Tripped, 0.0) == Seconds{0.0});
		CHECK(TimeToTrip(Parameters, Tripped, 1.0) == Seconds{0.0});
		CHECK(TimeToTrip(Parameters, Tripped, 3.0) == Seconds{0.0});
	}
	SUBCASE("A safe load returns zero when the state is already above TripHeat")
	{
		const ThermalState Overheated{.Heat = 1.6, .Tripped = false};
		CHECK(TimeToTrip(Parameters, Overheated, 1.0) == Seconds{0.0});
	}
	SUBCASE("An unsafe load returns zero when heat is at or above TripHeat")
	{
		CHECK(TimeToTrip(Parameters, ThermalState{.Heat = Parameters.TripHeat}, 2.0) == Seconds{0.0});
		CHECK(TimeToTrip(Parameters, ThermalState{.Heat = 1.6}, 2.0) == Seconds{0.0});
	}
	SUBCASE("A hotter state trips sooner")
	{
		const std::optional<Seconds> Cold = TimeToTrip(Parameters, ThermalState{.Heat = 0.0}, 1.4);
		const std::optional<Seconds> Warm = TimeToTrip(Parameters, ThermalState{.Heat = 1.0}, 1.4);
		REQUIRE(Cold.has_value());
		REQUIRE(Warm.has_value());
		CHECK(*Warm < *Cold);
	}
	SUBCASE("A heavier load trips sooner")
	{
		const std::optional<Seconds> Light = TimeToTrip(Parameters, ThermalState{}, 1.3);
		const std::optional<Seconds> Heavy = TimeToTrip(Parameters, ThermalState{}, 2.0);
		REQUIRE(Light.has_value());
		REQUIRE(Heavy.has_value());
		CHECK(*Heavy < *Light);
	}
}

TEST_CASE("ClassifyThermal thresholds")
{
	const ThermalParameters Parameters = DefaultParameters();
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 0.0}) == ThermalStatus::Normal);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 0.999}) == ThermalStatus::Normal);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = Parameters.WarningHeat}) ==
	      ThermalStatus::Warning);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 1.2}) == ThermalStatus::Warning);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 1.6, .Tripped = false}) == ThermalStatus::Tripped);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 0.0, .Tripped = true}) == ThermalStatus::Tripped);
	CHECK(ClassifyThermal(Parameters, ThermalState{.Heat = 1.6, .Tripped = true}) == ThermalStatus::Tripped);
}

TEST_CASE("TryResetThermal leaves an untripped state unchanged")
{
	const ThermalParameters Parameters = DefaultParameters();
	const ThermalState Hot{.Heat = 1.3, .Tripped = false};
	const std::optional<ThermalState> Result = TryResetThermal(Parameters, Hot);
	REQUIRE(Result.has_value());
	CheckSameState(*Result, Hot);
}

TEST_CASE("TryResetThermal refuses while heat is at or above WarningHeat")
{
	const ThermalParameters Parameters = DefaultParameters();
	CHECK_FALSE(TryResetThermal(Parameters, ThermalState{.Heat = Parameters.WarningHeat, .Tripped = true})
	                .has_value());
	CHECK_FALSE(TryResetThermal(Parameters, ThermalState{.Heat = 1.5, .Tripped = true}).has_value());

	const std::optional<ThermalState> Cool =
	    TryResetThermal(Parameters, ThermalState{.Heat = 0.7, .Tripped = true});
	REQUIRE(Cool.has_value());
	CheckSameState(*Cool, ThermalState{.Heat = 0.7, .Tripped = false});
}

TEST_CASE("Trip latch: overload trips, the latch holds while cooling, and reset works only once cool")
{
	const ThermalParameters Parameters = DefaultParameters();
	constexpr double Overload = 1.5;
	constexpr double StepSeconds = 0.5;
	constexpr int StepLimit = 100000;

	ThermalState State{};
	int Steps = 0;
	while (!State.Tripped && Steps < StepLimit)
	{
		State = StepThermal(Parameters, State, Overload, Seconds{StepSeconds});
		Steps++;
	}
	REQUIRE(State.Tripped);
	CHECK(ClassifyThermal(Parameters, State) == ThermalStatus::Tripped);
	CHECK_FALSE(TryResetThermal(Parameters, State).has_value());

	const double HeatAtTrip = State.Heat;
	State = StepThermal(Parameters, State, Overload, Seconds{StepSeconds});
	CHECK(State.Tripped);
	CHECK(State.Heat < HeatAtTrip);

	Steps = 0;
	while (State.Heat >= Parameters.WarningHeat && Steps < StepLimit)
	{
		REQUIRE_FALSE(TryResetThermal(Parameters, State).has_value());
		State = StepThermal(Parameters, State, Overload, Seconds{StepSeconds});
		REQUIRE(State.Tripped);
		Steps++;
	}
	REQUIRE(State.Heat < Parameters.WarningHeat);

	for (int Step = 0; Step < StepLimit && State.Heat > Tolerance; Step++)
	{
		State = StepThermal(Parameters, State, Overload, Seconds{TimeConstantSeconds});
	}
	CHECK(State.Tripped);
	CHECK(ClassifyThermal(Parameters, State) == ThermalStatus::Tripped);

	const std::optional<ThermalState> Reset = TryResetThermal(Parameters, State);
	REQUIRE(Reset.has_value());
	CHECK_FALSE(Reset->Tripped);
	CHECK(Reset->Heat == State.Heat);
	CHECK(ClassifyThermal(Parameters, *Reset) == ThermalStatus::Normal);

	const ThermalState Reheated = StepThermal(Parameters, *Reset, Overload, Seconds{StepSeconds});
	CHECK(Reheated.Heat > Reset->Heat);
}
