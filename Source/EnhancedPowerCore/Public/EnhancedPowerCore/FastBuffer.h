#pragma once

#include "EnhancedPowerCore/Export.h"
#include "EnhancedPowerCore/Units.h"

namespace EnhancedPower
{

/// Constants for one capacitor bank.
///
/// Preconditions: `Capacity >= 0`, `MaxCharge >= 0`, `MaxDischarge >= 0`, and
/// `0 < ChargeEfficiency <= 1`.
struct BufferParameters
{
	Megajoules Capacity;
	Megawatts MaxCharge;
	Megawatts MaxDischarge;
	double ChargeEfficiency = 1.0;
};

/// Stored energy of one capacitor bank.
struct BufferState
{
	Megajoules Stored;
};

/// Result of one capacitor bank step.
///
/// `Absorbed` is the power taken from the island surplus. `Delivered` is the
/// power given to the island deficit.
struct BufferStep
{
	BufferState State;
	Megawatts Absorbed;
	Megawatts Delivered;
};

/// Advances a capacitor bank by one step against the island balance.
///
/// `Balance` is the island balance without the buffer: positive is surplus,
/// negative is deficit.
ENHANCEDPOWERCORE_API BufferStep StepBuffer(const BufferParameters& Parameters, const BufferState& State,
                                            Megawatts Balance, Seconds Delta);

} // namespace EnhancedPower
