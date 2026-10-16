#include "EnhancedPowerCore/Loss.h"

namespace EnhancedPower
{

Megawatts IslandLoss(const TierParameters& Tier, Megawatts Load, Meters Distance)
{
	if (!(Load > Megawatts{}) || !(Distance > Meters{}))
	{
		return Megawatts{};
	}
	return Tier.ReferenceLossFraction * (Load / Tier.Capacity) * (Distance / Tier.ReferenceDistance) * Load;
}

} // namespace EnhancedPower
