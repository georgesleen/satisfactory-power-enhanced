#include "Pulse.h"

#include <algorithm>
#include <cmath>
#include <iostream>

namespace EnhancedPower::Balance
{
namespace
{

constexpr double MeanFraction = 0.5;

struct PulseResult
{
	double MaximumHeat = 0.0;
	std::optional<Seconds> Warning;
	std::optional<Seconds> Trip;
	Megajoules MinimumStored;
	Megajoules FinalStored;
	Megajoules Charged;
	Megajoules Delivered;
	Megajoules Unserved;
	Megawatts MaximumFeed;
	Megajoules TailEnergyChange;
};

Megawatts DemandAt(const Factory& Factory, Seconds Time, bool Staggered, std::size_t PulsedCount)
{
	Megawatts Load;
	std::size_t PulsedIndex = 0;
	for (std::size_t Index = 0; Index < Factory.Consumers.size(); Index++)
	{
		const Consumer& Consumer = Factory.Consumers[Index];
		if (!(Consumer.Cycle > Seconds{}))
		{
			Load = Load + Consumer.Maximum;
			continue;
		}
		const double Offset =
		    Staggered ? static_cast<double>(PulsedIndex) / static_cast<double>(PulsedCount) : 0.0;
		PulsedIndex++;
		const double Phase = std::fmod(Time / Consumer.Cycle + Offset, 1.0);
		Load = Load + Consumer.Minimum + (Consumer.Maximum - Consumer.Minimum) * Phase;
	}
	return Load;
}

PulseResult Simulate(const Factory& Factory, const Tuning& Tuning, Megawatts Rating, int Banks,
                     bool Staggered, bool Sustained, bool Vanilla = false)
{
	const BufferParameters Bank =
	    Vanilla
	        ? BufferParameters{Tuning.VanillaStorageCapacity * Banks, Tuning.VanillaStorageCharge * Banks,
	                           Factory.Peak, 1.0}
	        : BufferParameters{Tuning.CapacitorBank.Capacity * Banks, Tuning.CapacitorBank.MaxCharge * Banks,
	                           Tuning.CapacitorBank.MaxDischarge * Banks,
	                           Tuning.CapacitorBank.ChargeEfficiency};
	BufferState Stored{Bank.Capacity};
	const std::size_t PulsedCount =
	    static_cast<std::size_t>(std::count_if(Factory.Consumers.begin(), Factory.Consumers.end(),
	                                           [](const Consumer& Item) { return Item.Cycle > Seconds{}; }));
	ThermalState Heat;
	PulseResult Result;
	Result.MinimumStored = Stored.Stored;
	Seconds TailWindow;
	for (const Consumer& Consumer : Factory.Consumers)
	{
		TailWindow = std::max(TailWindow, Consumer.Cycle);
	}
	std::optional<Megajoules> TailStart;
	for (Seconds Time{}; Time < Tuning.SimulationDuration; Time = Time + Tuning.SimulationStep)
	{
		const Seconds Delta = std::min(Tuning.SimulationStep, Tuning.SimulationDuration - Time);
		if (!TailStart && Time + Delta * MeanFraction >= Tuning.SimulationDuration - TailWindow)
		{
			TailStart = Stored.Stored;
		}
		const Megawatts Load =
		    Sustained ? Factory.Peak : DemandAt(Factory, Time + Delta * MeanFraction, Staggered, PulsedCount);
		const bool WasTripped = Heat.Tripped;
		const Megawatts Setpoint = WasTripped ? Megawatts{} : Rating * Tuning.BankSetpointFraction;
		const BufferStep Buffer = StepBuffer(Bank, Stored, Setpoint - Load, Delta);
		Stored = Buffer.State;
		const Megawatts Feed = WasTripped ? Megawatts{} : Load + Buffer.Absorbed - Buffer.Delivered;
		Result.MaximumFeed = std::max(Result.MaximumFeed, Feed);
		if (WasTripped)
		{
			Result.Unserved = Result.Unserved + (Load - Buffer.Delivered) * Delta;
		}
		Heat = StepThermal(Tuning.Thermal, Heat, Feed / Rating, Delta);
		Result.MaximumHeat = std::max(Result.MaximumHeat, Heat.Heat);
		if (!Result.Warning && Heat.Heat >= Tuning.Thermal.WarningHeat)
		{
			Result.Warning = Time + Delta;
		}
		if (!Result.Trip && Heat.Tripped)
		{
			Result.Trip = Time + Delta;
		}
		Result.MinimumStored = std::min(Result.MinimumStored, Stored.Stored);
		Result.Charged = Result.Charged + Buffer.Absorbed * Delta;
		Result.Delivered = Result.Delivered + Buffer.Delivered * Delta;
	}
	Result.FinalStored = Stored.Stored;
	Result.TailEnergyChange = Stored.Stored - TailStart.value_or(Stored.Stored);
	return Result;
}

void PrintResult(const char* Mode, const PulseResult& Result, Megawatts Rating, int Banks,
                 const Tuning& Tuning, bool Vanilla = false)
{
	std::cout << "  PULSE " << Mode << " ratingMW=" << Rating.Value << " banks=" << Banks
	          << " maximumHeat=" << Result.MaximumHeat << " warningSeconds=";
	if (Result.Warning)
	{
		std::cout << Result.Warning->Value;
	}
	else
	{
		std::cout << "none";
	}
	std::cout << " tripSeconds=";
	if (Result.Trip)
	{
		std::cout << Result.Trip->Value;
	}
	else
	{
		std::cout << "none";
	}
	const double Initial =
	    (Vanilla ? Tuning.VanillaStorageCapacity.Value : Tuning.CapacitorBank.Capacity.Value) * Banks;
	const double Efficiency = Vanilla ? 1.0 : Tuning.CapacitorBank.ChargeEfficiency;
	const double Residual =
	    Result.FinalStored.Value - Initial - Result.Charged.Value * Efficiency + Result.Delivered.Value;
	std::cout << " minimumMJ=" << Result.MinimumStored.Value << " finalMJ=" << Result.FinalStored.Value
	          << " chargedMJ=" << Result.Charged.Value << " deliveredMJ=" << Result.Delivered.Value
	          << " unservedMJ=" << Result.Unserved.Value << " energyResidualMJ=" << Residual
	          << " maximumFeedMW=" << Result.MaximumFeed.Value
	          << " tailEnergyChangeMJ=" << Result.TailEnergyChange.Value << '\n';
}

} // namespace

void PrintPulseStudy(const Factory& Factory, const PulseStudy& Study, const Tuning& Tuning)
{
	const Megawatts Rating = Tuning.Transformer(Study.Transformer).Rating * Study.TransformerCount;
	PrintResult("synchronized", Simulate(Factory, Tuning, Rating, 0, false, false), Rating, 0, Tuning);
	PrintResult("synchronized", Simulate(Factory, Tuning, Rating, Study.BankCount, false, false), Rating,
	            Study.BankCount, Tuning);
	PrintResult("staggered", Simulate(Factory, Tuning, Rating, 0, true, false), Rating, 0, Tuning);
	const Megawatts Headroom = Factory.Peak / Tuning.ComfortLoadFraction;
	PrintResult("extra-headroom", Simulate(Factory, Tuning, Headroom, 0, false, false), Headroom, 0, Tuning);
	PrintResult("sustained-peak", Simulate(Factory, Tuning, Rating, Study.BankCount, false, true), Rating,
	            Study.BankCount, Tuning);
	PrintResult("vanilla-storage-one", Simulate(Factory, Tuning, Rating, 1, false, false, true), Rating, 1,
	            Tuning, true);
	const int Batteries = Tuning.VanillaStorageComparisonCount;
	PrintResult("vanilla-storage-bank", Simulate(Factory, Tuning, Rating, Batteries, false, false, true),
	            Rating, Batteries, Tuning, true);
	constexpr int SearchLimit = 100;
	constexpr double EnergyToleranceMJ = 0.001;
	for (const bool Vanilla : {false, true})
	{
		bool Found = false;
		for (int Count = 0; Count <= SearchLimit; Count++)
		{
			const PulseResult Result = Simulate(Factory, Tuning, Rating, Count, false, false, Vanilla);
			if (!Result.Trip && Result.Unserved.Value == 0.0 && Result.MaximumFeed <= Rating &&
			    Result.TailEnergyChange.Value >= -EnergyToleranceMJ)
			{
				PrintResult(Vanilla ? "minimum-vanilla-storage" : "minimum-capacitor", Result, Rating, Count,
				            Tuning, Vanilla);
				const StorageBuild& Build = Vanilla ? Tuning.VanillaStorageBuild : Tuning.CapacitorBuild;
				const Megajoules Capacity =
				    (Vanilla ? Tuning.VanillaStorageCapacity : Tuning.CapacitorBank.Capacity) * Count;
				std::cout << "  BUILD type=" << (Vanilla ? "vanilla-storage" : "initial-capacitor")
				          << " units=" << Count << " footprintM2=" << Build.FootprintSquareMeters * Count
				          << " capacityMWh=" << Capacity.Value / 3600.0;
				for (const auto& [Material, Amount] : Build.Materials)
				{
					std::cout << ' ' << Material << '=' << Amount * Count;
				}
				std::cout << '\n';
				Found = true;
				break;
			}
		}
		if (!Found)
		{
			std::cout << "  SIZING no-solution type=" << (Vanilla ? "vanilla-storage" : "capacitor")
			          << " searchLimit=" << SearchLimit << '\n';
		}
	}
}

} // namespace EnhancedPower::Balance
