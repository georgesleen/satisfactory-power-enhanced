#include "Layout.h"
#include "Pulse.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <stdexcept>

namespace EnhancedPower::Balance
{
namespace
{

constexpr double Percent = 100.0;
constexpr std::array<const char*, 3> ProxyNames{"TotalWireLength", "SpatialExtent",
                                                "LoadWeightedFeedDistance"};

void PrintLoss(const char* Label, const IslandGraph& Graph, Megawatts Mean, const Tuning& Tuning,
               int UnlockTier)
{
	const std::vector<Meters> Lengths = Distances(Graph);
	for (std::size_t Proxy = 0; Proxy < Lengths.size(); Proxy++)
	{
		std::cout << "  LOSS " << Label << " proxy=" << ProxyNames[Proxy]
		          << " distanceM=" << Lengths[Proxy].Value;
		for (const TierTuning& Tier : Tuning.Tiers)
		{
			if (Tier.UnlockTier > UnlockTier)
			{
				continue;
			}
			const Megawatts Loss = TierLoss(Tier, Mean, Lengths[Proxy]);
			std::cout << ' ' << Tier.Name << "MW=" << Loss.Value << ' ' << Tier.Name
			          << "Percent=" << Percent * (Loss / Mean);
		}
		std::cout << '\n';
	}
}

void PrintFactory(const Scenario& Description, const BuildingTable& Buildings, const Tuning& Tuning)
{
	const Factory Local = BuildFactory(Description, Buildings);
	if (!Tuning.Tier("LV").Loss)
	{
		throw std::runtime_error("tier 'LV' needs a capacity");
	}
	const TierParameters& LowVoltage = *Tuning.Tier("LV").Loss;
	const double PeakFraction = Local.Peak / LowVoltage.Capacity;
	std::cout << "SCENARIO " << Description.File << " name=\"" << Description.Name
	          << "\" tier=" << Description.MilestoneTier << '\n';
	std::cout << "  LOAD meanMW=" << Local.Mean.Value << " peakMW=" << Local.Peak.Value
	          << " LVcapacityMW=" << LowVoltage.Capacity.Value
	          << " meanPercent=" << Percent * (Local.Mean / LowVoltage.Capacity)
	          << " peakPercent=" << Percent * PeakFraction
	          << " comfortable=" << (PeakFraction <= Tuning.ComfortLoadFraction ? "yes" : "no") << '\n';
	PrintLoss("local", Local.Graph, Local.Mean, Tuning, Description.MilestoneTier);
	const double LocalLossFraction =
	    IslandLoss(LowVoltage, Local.Mean, Distances(Local.Graph).back()) / Local.Mean;
	std::cout << "  LOCAL_CHECK proxy=LoadWeightedFeedDistance lossLimitPercent="
	          << Percent * Tuning.LocalLossLimit
	          << " acceptable=" << (LocalLossFraction <= Tuning.LocalLossLimit ? "yes" : "no") << '\n';
	for (const auto& [Layout, Label] : std::array<std::pair<Wiring, const char*>, 2>{
	         std::pair{Wiring::PoleBranch, "pole-branch"}, std::pair{Wiring::DaisyChain, "daisy-chain"}})
	{
		const Factory Variant = BuildFactory(Description, Buildings, Layout);
		PrintLoss(Label, Variant.Graph, Variant.Mean, Tuning, 0);
	}
	if (Description.Supply)
	{
		PrintLoss("remote-unsplit", WithSupply(Local, Description), Local.Mean, Tuning,
		          Description.MilestoneTier);
		const std::vector<Meters> LocalDistances = Distances(Local.Graph);
		for (const TierTuning& Tier : Tuning.Tiers)
		{
			if (Tier.Name == "LV" || Tier.UnlockTier > Description.MilestoneTier)
			{
				continue;
			}
			for (std::size_t Proxy = 0; Proxy < ProxyNames.size(); Proxy++)
			{
				const Megawatts LocalLoss = IslandLoss(LowVoltage, Local.Mean, LocalDistances[Proxy]);
				IslandGraph Trunk{
				    {{*Description.Supply, {}, true}, {Description.Entry, Local.Mean + LocalLoss, false}},
				    {}};
				const double Length = Description.SupplyLineLength.value_or(std::hypot(
				    Description.Supply->X - Description.Entry.X, Description.Supply->Y - Description.Entry.Y,
				    Description.Supply->Z - Description.Entry.Z));
				Trunk.Edges.push_back({0, 1, Meters{Length}});
				const Megawatts TrunkLoss = TierLoss(Tier, Local.Mean + LocalLoss, Distances(Trunk)[Proxy]);
				std::cout << "  SPLIT tier=" << Tier.Name << " proxy=" << ProxyNames[Proxy]
				          << " localLossMW=" << LocalLoss.Value << " trunkLossMW=" << TrunkLoss.Value
				          << " totalLossPercent=" << Percent * ((LocalLoss + TrunkLoss) / Local.Mean) << '\n';
			}
		}
	}
	if (Description.Pulse)
	{
		PrintPulseStudy(Local, *Description.Pulse, Tuning);
	}
}

void PrintPlant(const Scenario& Description, const std::filesystem::path& Directory,
                const BuildingTable& Buildings, const Tuning& Tuning)
{
	Factory Plant = BuildFactory(Description, Buildings);
	Megawatts Peak;
	for (const PlacedFactory& Placed : Description.Factories)
	{
		const Scenario Child = LoadScenario(Directory / Placed.Scenario);
		const Factory Local = BuildFactory(Child, Buildings);
		const std::size_t Index = Plant.Graph.Nodes.size();
		Plant.Graph.Nodes.push_back({Placed.Offset, Local.Mean, false});
		Plant.Graph.Edges.push_back(
		    {0, Index,
		     Meters{std::hypot(Placed.Offset.X - Description.Entry.X, Placed.Offset.Y - Description.Entry.Y,
		                       Placed.Offset.Z - Description.Entry.Z)}});
		Plant.Mean = Plant.Mean + Local.Mean;
		Peak = Peak + Local.Peak;
	}
	std::cout << "SCENARIO " << Description.File << " name=\"" << Description.Name
	          << "\" tier=" << Description.MilestoneTier << '\n';
	std::cout << "  PLANT generationMW=" << Plant.Generation.Value << " exportMeanMW=" << Plant.Mean.Value
	          << " exportPeakMW=" << Peak.Value;
	for (const TierTuning& Tier : Tuning.Tiers)
	{
		std::cout << ' ' << Tier.Name << "peakPercent=";
		if (Tier.Loss)
		{
			std::cout << Percent * (Peak / Tier.Loss->Capacity);
		}
		else
		{
			std::cout << "n/a";
		}
	}
	std::cout << '\n';
	PrintLoss("aggregate", Plant.Graph, Plant.Mean, Tuning, Description.MilestoneTier);
}

} // namespace
} // namespace EnhancedPower::Balance

int main(int ArgumentCount, char** Arguments)
{
	using namespace EnhancedPower::Balance;
	try
	{
		if (ArgumentCount < 4 || std::string(Arguments[1]) != "--tuning")
		{
			std::cerr << "Usage: ep-balance --tuning tuning.json scenario.json|directory [...]\n";
			return 1;
		}
		const std::filesystem::path TuningPath = Arguments[2];
		const Tuning Settings = LoadTuning(TuningPath);
		const BuildingTable Buildings = LoadBuildingTable(TuningPath.parent_path() / "buildings.json");
		std::vector<std::filesystem::path> Paths;
		for (int Index = 3; Index < ArgumentCount; Index++)
		{
			const std::filesystem::path Path = Arguments[Index];
			if (std::filesystem::is_directory(Path))
			{
				for (const auto& Entry : std::filesystem::directory_iterator(Path))
				{
					if (Entry.path().extension() == ".json")
					{
						Paths.push_back(Entry.path());
					}
				}
			}
			else
			{
				Paths.push_back(Path);
			}
		}
		std::sort(Paths.begin(), Paths.end());
		std::cout << std::fixed << std::setprecision(3);
		for (const TierTuning& Tier : Settings.Tiers)
		{
			std::cout << "TUNING tier=" << Tier.Name;
			if (Tier.Loss)
			{
				std::cout << " capacityMW=" << Tier.Loss->Capacity.Value
				          << " referenceDistanceM=" << Tier.Loss->ReferenceDistance.Value
				          << " referenceLossFraction=" << Tier.Loss->ReferenceLossFraction << '\n';
			}
			else
			{
				std::cout << " capacityMW=uncapped loss=none\n";
			}
		}
		for (const TransformerSize& Transformer : Settings.Transformers)
		{
			std::cout << "TUNING transformer=" << Transformer.Name << " ratingMW=" << Transformer.Rating.Value
			          << '\n';
		}
		std::cout << "TUNING thermal timeConstantSeconds=" << Settings.Thermal.TimeConstant.Value
		          << " warningHeat=" << Settings.Thermal.WarningHeat
		          << " tripHeat=" << Settings.Thermal.TripHeat << '\n';
		std::cout << "TUNING capacitor capacityMJ=" << Settings.CapacitorBank.Capacity.Value
		          << " chargeMW=" << Settings.CapacitorBank.MaxCharge.Value
		          << " dischargeMW=" << Settings.CapacitorBank.MaxDischarge.Value
		          << " chargeEfficiency=" << Settings.CapacitorBank.ChargeEfficiency
		          << " setpointFraction=" << Settings.BankSetpointFraction << '\n';
		std::cout << "TUNING vanillaStorage capacityMJ=" << Settings.VanillaStorageCapacity.Value
		          << " chargeMW=" << Settings.VanillaStorageCharge.Value << " discharge=unlimited\n";
		std::cout << "TUNING simulation durationSeconds=" << Settings.SimulationDuration.Value
		          << " stepSeconds=" << Settings.SimulationStep.Value << '\n';
		for (const auto& Path : Paths)
		{
			const Scenario Description = LoadScenario(Path);
			if (Description.IsPlant)
			{
				PrintPlant(Description, Path.parent_path(), Buildings, Settings);
			}
			else
			{
				PrintFactory(Description, Buildings, Settings);
			}
		}
		return 0;
	}
	catch (const std::exception& Error)
	{
		std::cerr << "ep-balance: " << Error.what() << '\n';
		return 1;
	}
}
