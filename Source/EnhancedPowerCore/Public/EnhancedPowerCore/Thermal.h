#pragma once

#include <optional>

#include "EnhancedPowerCore/Export.h"
#include "EnhancedPowerCore/Units.h"

namespace EnhancedPower
{

/// Heat model constants for one transformer.
///
/// Heat is dimensionless; a transformer at its rating settles at heat 1.
/// Preconditions: `TimeConstant > 0` and `0 < WarningHeat < TripHeat`.
struct ThermalParameters
{
	Seconds TimeConstant;
	double WarningHeat = 1.0;
	double TripHeat = 1.44;
};

/// Heat and breaker state of one transformer.
struct ThermalState
{
	double Heat = 0.0;
	bool Tripped = false;
};

/// Display class of a transformer heat state.
enum class ThermalStatus
{
	Normal,
	Warning,
	Tripped
};

/// Advances transformer heat by one step at a constant load ratio.
///
/// `LoadRatio` is load divided by rating; a negative or NaN ratio counts as 0.
/// A step with `Delta <= 0` returns `State` unchanged.
ENHANCEDPOWERCORE_API ThermalState StepThermal(const ThermalParameters& Parameters, const ThermalState& State,
                                               double LoadRatio, Seconds Delta);

/// Classifies a heat state as normal, warning, or tripped.
ENHANCEDPOWERCORE_API ThermalStatus ClassifyThermal(const ThermalParameters& Parameters,
                                                    const ThermalState& State);

/// Time until a trip if `LoadRatio` stays constant.
///
/// Returns `std::nullopt` if the load never trips, and zero if the transformer is
/// tripped or already at trip heat.
ENHANCEDPOWERCORE_API std::optional<Seconds> TimeToTrip(const ThermalParameters& Parameters,
                                                        const ThermalState& State, double LoadRatio);

/// Manual breaker reset.
///
/// Returns `std::nullopt` if the transformer is tripped and its heat is at or
/// above `WarningHeat`.
ENHANCEDPOWERCORE_API std::optional<ThermalState> TryResetThermal(const ThermalParameters& Parameters,
                                                                  const ThermalState& State);

} // namespace EnhancedPower
