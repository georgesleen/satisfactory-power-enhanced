#include "EnhancedPowerCore/FastBuffer.h"
#include "EnhancedPowerCore/Loss.h"
#include "EnhancedPowerCore/Thermal.h"
#include "EnhancedPowerCore/TransformerLink.h"
#include "tuning.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <emscripten/emscripten.h>

namespace
{
using namespace EnhancedPower;
namespace Tuning = UiTuning;

const ThermalParameters Thermal{Seconds{Tuning::TimeConstant}, Tuning::WarningHeat, Tuning::TripHeat};
const BufferParameters Buffer{Megajoules{Tuning::BufferCapacity}, Megawatts{Tuning::MaxCharge},
                              Megawatts{Tuning::MaxDischarge}, Tuning::ChargeEfficiency};
const LinkParameters Link{Megawatts{Tuning::Rating}, 1.0, Megajoules{Tuning::Rating * Tuning::StepSeconds},
                          Megawatts{Tuning::Rating}};
const TierParameters Tier{Megawatts{Tuning::TierCapacity}, Meters{Tuning::ReferenceDistance},
                          Tuning::ReferenceLoss};
constexpr std::size_t SnapshotCapacity = 8192;
char Snapshot[SnapshotCapacity];

struct Simulation
{
	int Scenario = 0;
	std::uint64_t Tick = 0;
	double Time = 0.0;
	bool ConnectionRequested = true;
	bool BufferConnected = true;
	ThermalState Heat;
	BufferState Storage;
	LinkState Escrow;
	double Transfer = 0.0;
	double Primary = 0.0;
	double PrimaryRequest = 0.0;
	double Offer = 0.0;
	double Demand = 0.0;
	double Served = 0.0;
	double Absorbed = 0.0;
	double Delivered = 0.0;
	double Loss = 0.0;
	double Capacity = 0.0;
	double ThermalRatio = 0.0;
	double Overflow = 0.0;
	double EnergyResidual = 0.0;
};
Simulation State;

bool Connected()
{
	return State.ConnectionRequested && !State.Heat.Tripped;
}

bool UpstreamAvailable()
{
	return State.Scenario != 4 && (State.Scenario != 3 || State.Time < Tuning::TimeConstant);
}

double OverloadRatio()
{
	return std::sqrt(Tuning::TripHeat) / Tuning::Setpoint;
}

double RequestedDemand()
{
	if (State.Scenario == 4)
	{
		return 0.0;
	}
	if (State.Scenario == 1 || State.Scenario == 5)
	{
		return Tuning::Rating * OverloadRatio();
	}
	if (State.Scenario == 2)
	{
		const auto Phase = static_cast<std::uint64_t>(std::floor(State.Time / Tuning::TimeConstant));
		return Tuning::Rating * (Phase % 2 == 0 ? Tuning::Comfort : OverloadRatio());
	}
	return Tuning::Rating * Tuning::Comfort;
}

double LossAt(double Demand)
{
	return IslandLoss(Tier, Megawatts{Demand}, Meters{Tuning::ReferenceDistance}).Value;
}

void Advance(Seconds Delta)
{
	const bool Closed = Connected();
	const bool Available = UpstreamAvailable();
	State.Demand = RequestedDemand();
	const double Required = State.Demand + LossAt(State.Demand);
	auto Plan = PlanLink(Link, State.Escrow, Delta, Available && Closed);
	if (!Closed)
	{
		Plan = {};
	}
	const double FeedLimit = State.Scenario == 2 ? Tuning::Rating * Tuning::Setpoint : Tuning::Rating;
	const double ChargeRoom =
	    (Tuning::BufferCapacity - State.Storage.Stored.Value) / (Delta.Value * Tuning::ChargeEfficiency);
	const double DesiredFeed =
	    Required + (State.BufferConnected ? std::min(Tuning::MaxCharge, ChargeRoom) : 0.0);
	State.Transfer = std::min({Plan.SecondaryOffer.Value, FeedLimit, DesiredFeed});
	const auto PreviousStorage = State.Storage;
	const auto StorageStep = StepBuffer(
	    Buffer, State.Storage, Megawatts{State.BufferConnected ? State.Transfer - Required : 0.0}, Delta);
	State.Storage = StorageStep.State;
	State.Absorbed = StorageStep.Absorbed.Value;
	State.Delivered = StorageStep.Delivered.Value;
	const double Supplied = State.Transfer + State.Delivered - State.Absorbed;
	const double LossCoefficient = LossAt(1.0);
	State.Served =
	    std::min(State.Demand, 2.0 * Supplied / (1.0 + std::sqrt(1.0 + 4.0 * LossCoefficient * Supplied)));
	State.Loss = LossAt(State.Served);
	const double RoomAfterDraw =
	    Link.EscrowCapacity.Value - State.Escrow.Escrow.Value + State.Transfer * Delta.Value;
	State.Primary = std::min(Plan.PrimaryRequest.Value, RoomAfterDraw / (Link.Efficiency * Delta.Value));
	const auto PreviousEscrow = State.Escrow;
	const auto Settlement =
	    SettleLink(Link, State.Escrow, Plan, Delta, Megawatts{State.Primary}, Megawatts{State.Transfer});
	State.Escrow = Settlement.State;
	State.Overflow += Settlement.Overflow.Value;
	State.PrimaryRequest = Plan.PrimaryRequest.Value;
	State.Offer = Plan.SecondaryOffer.Value;
	State.Capacity =
	    Plan.SecondaryOffer.Value +
	    (State.BufferConnected ? std::min(Tuning::MaxDischarge, PreviousStorage.Stored.Value / Delta.Value)
	                           : 0.0);
	State.ThermalRatio =
	    Closed ? (State.Scenario == 1 ? OverloadRatio() : State.Transfer / Tuning::Rating) : 0.0;
	State.Heat = StepThermal(Thermal, State.Heat, State.ThermalRatio, Delta);
	const double StorageLoss = State.Absorbed * (1.0 - Tuning::ChargeEfficiency);
	State.EnergyResidual +=
	    State.Primary * Delta.Value - (State.Served + State.Loss + StorageLoss) * Delta.Value -
	    (State.Escrow.Escrow.Value - PreviousEscrow.Escrow.Value) -
	    (State.Storage.Stored.Value - PreviousStorage.Stored.Value) - Settlement.Overflow.Value;
	State.Time += Delta.Value;
	State.Tick++;
}
} // namespace

extern "C"
{
	EMSCRIPTEN_KEEPALIVE void ui_reset(int Scenario)
	{
		State = {};
		State.Scenario = std::clamp(Scenario, 0, 5);
		State.Storage.Stored = Megajoules{State.Scenario == 4 ? 0.0 : Tuning::BufferCapacity};
		State.Escrow.Escrow = State.Scenario == 4 ? Megajoules{} : Link.EscrowCapacity;
		State.Demand = RequestedDemand();
	}

	EMSCRIPTEN_KEEPALIVE void ui_set_connected(int Connected)
	{
		State.ConnectionRequested = Connected != 0;
	}

	EMSCRIPTEN_KEEPALIVE void ui_set_buffer_connected(int Connected)
	{
		State.BufferConnected = Connected != 0;
	}

	EMSCRIPTEN_KEEPALIVE int ui_reset_breaker()
	{
		const auto Reset = TryResetThermal(Thermal, State.Heat);
		if (!Reset)
		{
			return 0;
		}
		State.Heat = *Reset;
		return 1;
	}

	EMSCRIPTEN_KEEPALIVE void ui_step(double DeltaSeconds)
	{
		if (!std::isfinite(DeltaSeconds) || DeltaSeconds <= 0.0)
		{
			return;
		}
		while (DeltaSeconds > 0.0)
		{
			double Boundary = (std::floor(State.Time / Tuning::TimeConstant) + 1.0) * Tuning::TimeConstant;
			if (Boundary <= State.Time)
			{
				Boundary += Tuning::TimeConstant;
			}
			const double Delta = std::min({DeltaSeconds, Tuning::StepSeconds, Boundary - State.Time});
			Advance(Seconds{Delta});
			DeltaSeconds -= Delta;
		}
	}

	EMSCRIPTEN_KEEPALIVE const char* ui_snapshot()
	{
		const auto Status = ClassifyThermal(Thermal, State.Heat);
		const char* StatusName = Status == ThermalStatus::Tripped   ? "tripped"
		                         : Status == ThermalStatus::Warning ? "warning"
		                                                            : "normal";
		const auto UntilTrip = TimeToTrip(Thermal, State.Heat, State.ThermalRatio);
		char TripSeconds[64];
		if (UntilTrip)
		{
			std::snprintf(TripSeconds, sizeof(TripSeconds), "%.12g", UntilTrip->Value);
		}
		else
		{
			std::snprintf(TripSeconds, sizeof(TripSeconds), "null");
		}
		const double Production = State.Transfer + State.Delivered;
		const double UpstreamCapacity =
		    UpstreamAvailable() ? Link.Rating.Value + Link.MaxRecharge.Value : 0.0;
		const int Length = std::snprintf(
		    Snapshot, sizeof(Snapshot),
		    "{\"tick\":%llu,\"scenario\":%d,\"seconds\":%.12g,"
		    "\"production\":%.12g,\"consumption\":%.12g,\"capacity\":%.12g,\"maxConsumption\":%.12g,"
		    "\"transfer\":%.12g,\"rating\":%.12g,\"loadPercent\":%.12g,\"heat\":%.12g,\"heatPercent\":%.12g,"
		    "\"thermalStatus\":\"%s\",\"timeToTrip\":%s,\"upstreamAvailable\":%s,\"connected\":%s,"
		    "\"connectionRequested\":%s,\"bufferConnected\":%s,\"bufferStoredMJ\":%.12g,\"bufferCapacityMJ\":"
		    "%.12g,"
		    "\"bufferAbsorbedMW\":%.12g,\"bufferDeliveredMW\":%.12g,\"lossMW\":%.12g,"
		    "\"requestedLoadMW\":%.12g,\"requestedLoadPercent\":%.12g,\"unservedMW\":%.12g,\"saturated\":%s,"
		    "\"diagnostic\":%s,\"imposedThermalRatio\":%.12g,\"thermalLoadRatio\":%.12g,"
		    "\"escrowStoredMJ\":%.12g,\"escrowCapacityMJ\":%.12g,\"overflowMJ\":%.12g,\"energyResidualMJ\":%."
		    "12g,"
		    "\"input\":{\"production\":%.12g,\"consumption\":%.12g,\"capacity\":%.12g,\"maxConsumption\":%."
		    "12g},"
		    "\"output\":{\"production\":%.12g,\"consumption\":%.12g,\"capacity\":%.12g,\"maxConsumption\":%."
		    "12g},"
		    "\"tuning\":%s}",
		    static_cast<unsigned long long>(State.Tick), State.Scenario, State.Time, Production, State.Served,
		    State.Capacity, State.Demand, State.Transfer, Tuning::Rating,
		    State.Transfer / Tuning::Rating * 100.0, State.Heat.Heat,
		    State.Heat.Heat / Tuning::TripHeat * 100.0, StatusName, TripSeconds,
		    UpstreamAvailable() ? "true" : "false", Connected() ? "true" : "false",
		    State.ConnectionRequested ? "true" : "false", State.BufferConnected ? "true" : "false",
		    State.Storage.Stored.Value, Tuning::BufferCapacity, State.Absorbed, State.Delivered, State.Loss,
		    State.Demand, State.Demand / Tuning::Rating * 100.0, std::max(0.0, State.Demand - State.Served),
		    State.Demand + LossAt(State.Demand) > State.Transfer ? "true" : "false",
		    State.Scenario == 1 ? "true" : "false", State.Scenario == 1 ? OverloadRatio() : 0.0,
		    State.ThermalRatio, State.Escrow.Escrow.Value, Link.EscrowCapacity.Value, State.Overflow,
		    State.EnergyResidual, State.Primary, State.Primary, UpstreamCapacity, State.PrimaryRequest,
		    Production, State.Served, State.Capacity, State.Demand, Tuning::Provenance);
		if (Length < 0 || static_cast<std::size_t>(Length) >= sizeof(Snapshot))
		{
			return "{\"error\":\"snapshot serialization exceeded fixed capacity\"}";
		}
		return Snapshot;
	}
}
