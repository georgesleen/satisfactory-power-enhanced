#include "EnhancedPowerCore/Thermal.h"

#include <cmath>

namespace EnhancedPower
{

namespace
{

/// Load ratio with negative and NaN values replaced by 0.
double NonNegativeRatio(double LoadRatio)
{
	return LoadRatio > 0.0 ? LoadRatio : 0.0;
}

} // namespace

ThermalState StepThermal(const ThermalParameters& Parameters, const ThermalState& State, double LoadRatio,
                         Seconds Delta)
{
	if (!(Delta > Seconds{}))
	{
		return State;
	}
	const double Ratio = NonNegativeRatio(LoadRatio);
	const bool AlreadyTripped = State.Tripped || State.Heat >= Parameters.TripHeat;
	const double Target = AlreadyTripped ? 0.0 : Ratio * Ratio;
	double Heat = Target + (State.Heat - Target) * std::exp(-(Delta / Parameters.TimeConstant));
	if (!AlreadyTripped && Target <= Parameters.TripHeat && Heat >= Parameters.TripHeat)
	{
		Heat = std::nextafter(Parameters.TripHeat, 0.0);
	}
	const bool Tripped = AlreadyTripped || Heat >= Parameters.TripHeat;
	return ThermalState{Heat, Tripped};
}

ThermalStatus ClassifyThermal(const ThermalParameters& Parameters, const ThermalState& State)
{
	if (State.Tripped || State.Heat >= Parameters.TripHeat)
	{
		return ThermalStatus::Tripped;
	}
	if (State.Heat >= Parameters.WarningHeat)
	{
		return ThermalStatus::Warning;
	}
	return ThermalStatus::Normal;
}

std::optional<Seconds> TimeToTrip(const ThermalParameters& Parameters, const ThermalState& State,
                                  double LoadRatio)
{
	if (State.Tripped || State.Heat >= Parameters.TripHeat)
	{
		return Seconds{};
	}
	const double Ratio = NonNegativeRatio(LoadRatio);
	const double Target = Ratio * Ratio;
	if (Target <= Parameters.TripHeat)
	{
		return std::nullopt;
	}
	return Parameters.TimeConstant * std::log((Target - State.Heat) / (Target - Parameters.TripHeat));
}

std::optional<ThermalState> TryResetThermal(const ThermalParameters& Parameters, const ThermalState& State)
{
	if (!State.Tripped)
	{
		return State;
	}
	if (State.Heat >= Parameters.WarningHeat)
	{
		return std::nullopt;
	}
	return ThermalState{State.Heat, false};
}

} // namespace EnhancedPower
