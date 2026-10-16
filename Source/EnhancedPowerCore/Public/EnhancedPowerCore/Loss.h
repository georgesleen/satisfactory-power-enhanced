#pragma once

#include "EnhancedPowerCore/Export.h"
#include "EnhancedPowerCore/Units.h"

namespace EnhancedPower
{

/// Loss constants for one voltage tier.
///
/// At `Capacity` load over `ReferenceDistance`, an island loses
/// `ReferenceLossFraction` of its load. Preconditions: `Capacity > 0`,
/// `ReferenceDistance > 0`, and `ReferenceLossFraction >= 0`.
struct TierParameters
{
	Megawatts Capacity;
	Meters ReferenceDistance;
	double ReferenceLossFraction;
};

/// Transmission loss of one island, quadratic in load and linear in distance.
///
/// Returns 0 if `Load <= 0` or `Distance <= 0`. The result is not clamped to the
/// load.
ENHANCEDPOWERCORE_API Megawatts IslandLoss(const TierParameters& Tier, Megawatts Load, Meters Distance);

} // namespace EnhancedPower
