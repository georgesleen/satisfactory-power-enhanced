#include "EnhancedPowerCore/FastBuffer.h"

#include <algorithm>

namespace EnhancedPower
{

namespace
{

/// Energy limited to `[0, Capacity]`; NaN maps to 0.
Megajoules ClampStored(Megajoules Stored, Megajoules Capacity)
{
	return std::max(Megajoules{}, std::min(Stored, Capacity));
}

} // namespace

BufferStep StepBuffer(const BufferParameters& Parameters, const BufferState& State, Megawatts Balance,
                      Seconds Delta)
{
	const Megajoules Stored = ClampStored(State.Stored, Parameters.Capacity);
	if (!(Delta > Seconds{}) || Balance == Megawatts{})
	{
		return BufferStep{BufferState{Stored}, Megawatts{}, Megawatts{}};
	}
	Megajoules Next = Stored;
	Megawatts Absorbed;
	Megawatts Delivered;
	if (Balance < Megawatts{})
	{
		Delivered = std::min({-Balance, Parameters.MaxDischarge, Stored / Delta});
		Next = Stored - Delivered * Delta;
	}
	else if (Balance > Megawatts{})
	{
		Absorbed = std::min({Balance, Parameters.MaxCharge,
		                     (Parameters.Capacity - Stored) / (Delta * Parameters.ChargeEfficiency)});
		Next = Stored + Absorbed * Delta * Parameters.ChargeEfficiency;
	}
	return BufferStep{BufferState{ClampStored(Next, Parameters.Capacity)}, Absorbed, Delivered};
}

} // namespace EnhancedPower
