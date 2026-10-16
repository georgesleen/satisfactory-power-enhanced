#pragma once

#include "EnhancedPowerCore/Export.h"
#include "EnhancedPowerCore/Units.h"

namespace EnhancedPower
{

/// Constants for the energy accounting of one transformer.
///
/// Preconditions: `Rating > 0`, `0 < Efficiency <= 1`, `EscrowCapacity > 0`,
/// and `MaxRecharge >= 0`.
struct LinkParameters
{
	Megawatts Rating;
	double Efficiency = 1.0;
	Megajoules EscrowCapacity;
	Megawatts MaxRecharge;
};

/// Escrow energy and last delivered power of one transformer.
///
/// Preconditions: `0 <= Escrow <= EscrowCapacity` and `LastDelivered >= 0`.
struct LinkState
{
	Megajoules Escrow;
	Megawatts LastDelivered;
};

/// Power that one transformer offers to its secondary island and requests from
/// its primary island for one step.
struct LinkPlan
{
	Megawatts SecondaryOffer;
	Megawatts PrimaryRequest;
};

/// Result of one transformer step after the engine solve.
///
/// `OverDelivery` and `OverConsumption` are diagnostics for engine behavior that
/// breaks the plan; the escrow neither pays for nor credits them.
struct LinkSettlement
{
	LinkState State;
	Megajoules Loss;
	Megajoules Overflow;
	Megajoules OverDelivery;
	Megajoules OverConsumption;
};

/// Plans the secondary offer and primary request of one transformer for one step.
ENHANCEDPOWERCORE_API LinkPlan PlanLink(const LinkParameters& Parameters, const LinkState& State,
                                        Seconds Delta, bool PrimaryAvailable);

/// Settles the escrow of one transformer from the powers the engine reports.
ENHANCEDPOWERCORE_API LinkSettlement SettleLink(const LinkParameters& Parameters, const LinkState& State,
                                                const LinkPlan& Plan, Seconds Delta,
                                                Megawatts PrimaryConsumed, Megawatts SecondaryDelivered);

} // namespace EnhancedPower
