#include "EnhancedPowerCore/TransformerLink.h"

#include <algorithm>

namespace EnhancedPower
{

namespace
{

/// Value limited to `[Low, High]`; NaN maps to `Low`.
template <Unit Type>
Type Clamp(Type Value, Type Low, Type High)
{
	return std::max(Low, std::min(Value, High));
}

} // namespace

LinkPlan PlanLink(const LinkParameters& Parameters, const LinkState& State, Seconds Delta,
                  bool PrimaryAvailable)
{
	if (!(Delta > Seconds{}))
	{
		return LinkPlan{};
	}
	const Megajoules Escrow = Clamp(State.Escrow, Megajoules{}, Parameters.EscrowCapacity);
	const Megajoules Reserved = std::min(Escrow, Parameters.Rating * Delta);
	const Megawatts SecondaryOffer = Reserved / Delta;
	if (!PrimaryAvailable)
	{
		return LinkPlan{SecondaryOffer, Megawatts{}};
	}
	const Megajoules ExpectedDraw = std::min(State.LastDelivered * Delta, Reserved);
	const Megajoules Room = Parameters.EscrowCapacity - (Escrow - ExpectedDraw);
	const Megawatts PrimaryRequest =
	    std::min(Room / (Parameters.Efficiency * Delta),
	             State.LastDelivered / Parameters.Efficiency + Parameters.MaxRecharge);
	return LinkPlan{SecondaryOffer, PrimaryRequest};
}

LinkSettlement SettleLink(const LinkParameters& Parameters, const LinkState& State, const LinkPlan& Plan,
                          Seconds Delta, Megawatts PrimaryConsumed, Megawatts SecondaryDelivered)
{
	if (!(Delta > Seconds{}))
	{
		return LinkSettlement{State, Megajoules{}, Megajoules{}, Megajoules{}, Megajoules{}};
	}
	const Megajoules Escrow = Clamp(State.Escrow, Megajoules{}, Parameters.EscrowCapacity);

	const Megawatts Delivered = Clamp(SecondaryDelivered, Megawatts{}, Plan.SecondaryOffer);
	const Megajoules OverDelivery = std::max(SecondaryDelivered - Plan.SecondaryOffer, Megawatts{}) * Delta;

	const Megawatts Consumed = Clamp(PrimaryConsumed, Megawatts{}, Plan.PrimaryRequest);
	const Megajoules OverConsumption = std::max(PrimaryConsumed - Plan.PrimaryRequest, Megawatts{}) * Delta;

	const Megajoules Credit = Consumed * Delta * Parameters.Efficiency;
	const Megajoules Loss = Consumed * Delta * (1.0 - Parameters.Efficiency);

	const Megajoules Unbounded = Escrow - Delivered * Delta + Credit;
	const Megajoules Overflow = std::max(Unbounded - Parameters.EscrowCapacity, Megajoules{});
	const Megajoules Next = Clamp(Unbounded, Megajoules{}, Parameters.EscrowCapacity);

	return LinkSettlement{LinkState{Next, Delivered}, Loss, Overflow, OverDelivery, OverConsumption};
}

} // namespace EnhancedPower
