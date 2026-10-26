#include "Model.h"

#include <fstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

namespace EnhancedPower::Balance
{
namespace
{

using Json = nlohmann::json;

Json ReadJson(const std::filesystem::path& Path)
{
	std::ifstream Stream(Path);
	if (!Stream)
	{
		throw std::runtime_error("cannot open " + Path.string());
	}
	try
	{
		return Json::parse(Stream);
	}
	catch (const Json::exception& Error)
	{
		throw std::runtime_error(Path.string() + ": " + Error.what());
	}
}

Position ReadPosition(const Json& Value)
{
	Position Result;
	Result.X = Value.at(0).get<double>();
	Result.Y = Value.at(1).get<double>();
	Result.Z = Value.size() > 2 ? Value.at(2).get<double>() : 0.0;
	return Result;
}

std::vector<std::string> ReadStrings(const Json& Value, const char* Key)
{
	return Value.contains(Key) ? Value.at(Key).get<std::vector<std::string>>() : std::vector<std::string>{};
}

Wiring ReadWiring(const std::string& Name)
{
	if (Name == "pole-branch")
	{
		return Wiring::PoleBranch;
	}
	if (Name == "daisy-chain")
	{
		return Wiring::DaisyChain;
	}
	throw std::runtime_error("unknown wiring '" + Name + "'");
}

Block ReadBlock(const Json& Value)
{
	Block Result;
	Result.Label = Value.at("label").get<std::string>();
	Result.Building = Value.at("building").get<std::string>();
	Result.Recipe = Value.value("recipe", std::string{});
	Result.Count = Value.at("count").get<int>();
	Result.Columns = Value.value("columns", Result.Count);
	Result.Clock = Value.value("clock", 1.0);
	Result.Boost = Value.value("boost", 0.0);
	Result.Origin = ReadPosition(Value.at("origin"));
	Result.SpacingX = Value.at("spacing").at(0).get<double>();
	Result.SpacingY = Value.at("spacing").at(1).get<double>();
	Result.Layout = ReadWiring(Value.at("wiring").get<std::string>());
	Result.MachinesPerPole = Value.value("machinesPerPole", Result.MachinesPerPole);
	if (Result.Count <= 0 || Result.Columns <= 0 || Result.MachinesPerPole <= 0)
	{
		throw std::runtime_error("block '" + Result.Label +
		                         "' needs positive count, columns, and machines per pole");
	}
	return Result;
}

} // namespace

const TierTuning& Tuning::Tier(const std::string& Name) const
{
	for (const TierTuning& Candidate : Tiers)
	{
		if (Candidate.Name == Name)
		{
			return Candidate;
		}
	}
	throw std::runtime_error("unknown tier '" + Name + "'");
}

const TransformerSize& Tuning::Transformer(const std::string& Name) const
{
	for (const TransformerSize& Candidate : Transformers)
	{
		if (Candidate.Name == Name)
		{
			return Candidate;
		}
	}
	throw std::runtime_error("unknown transformer '" + Name + "'");
}

Megawatts TierLoss(const TierTuning& Tier, Megawatts Load, Meters Distance)
{
	return Tier.Loss ? IslandLoss(*Tier.Loss, Load, Distance) : Megawatts{};
}

BuildingTable LoadBuildingTable(const std::filesystem::path& Path)
{
	const Json Root = ReadJson(Path);
	BuildingTable Table;
	for (const auto& [Key, Value] : Root.at("buildings").items())
	{
		BuildingFacts Facts;
		Facts.Name = Value.at("name").get<std::string>();
		Facts.Power = Megawatts{Value.value("powerMegawatts", 0.0)};
		Facts.Generation = Megawatts{Value.value("generatorMegawatts", 0.0)};
		Facts.PowerExponent = Value.value("powerExponent", 1.0);
		Facts.BoostExponent = Value.value("boostExponent", 2.0);
		Table.Buildings.emplace(Key, Facts);
	}
	for (const auto& [Key, Value] : Root.at("variableRecipes").items())
	{
		VariableRecipe Recipe;
		Recipe.Name = Value.at("name").get<std::string>();
		Recipe.Building = Value.at("building").get<std::string>();
		Recipe.Duration = Seconds{Value.at("durationSeconds").get<double>()};
		Recipe.Minimum = Megawatts{Value.at("minMegawatts").get<double>()};
		Recipe.Maximum = Megawatts{Value.at("maxMegawatts").get<double>()};
		Table.VariableRecipes.emplace(Key, Recipe);
	}
	return Table;
}

Tuning LoadTuning(const std::filesystem::path& Path)
{
	const Json Root = ReadJson(Path);
	Tuning Result;
	for (const Json& Value : Root.at("tiers"))
	{
		TierTuning Tier;
		Tier.Name = Value.at("name").get<std::string>();
		Tier.UnlockTier = Value.at("unlockTier").get<int>();
		const Json& Capacity = Value.at("capacityMegawatts");
		if (Capacity.is_null())
		{
			if (Value.contains("referenceDistanceMeters") || Value.contains("referenceLossFraction"))
			{
				throw std::runtime_error("uncapped tier '" + Tier.Name + "' has no loss reference");
			}
		}
		else
		{
			Tier.Loss = TierParameters{Megawatts{Capacity.get<double>()},
			                           Meters{Value.at("referenceDistanceMeters").get<double>()},
			                           Value.at("referenceLossFraction").get<double>()};
		}
		Result.Tiers.push_back(Tier);
	}
	for (const Json& Value : Root.at("transformers"))
	{
		Result.Transformers.push_back(
		    {Value.at("name").get<std::string>(), Megawatts{Value.at("ratingMegawatts").get<double>()}});
	}
	const Json& Thermal = Root.at("thermal");
	Result.Thermal.TimeConstant = Seconds{Thermal.at("timeConstantSeconds").get<double>()};
	Result.Thermal.WarningHeat = Thermal.at("warningHeat").get<double>();
	Result.Thermal.TripHeat = Thermal.at("tripHeat").get<double>();
	const Json& Bank = Root.at("capacitorBank");
	Result.CapacitorBank.Capacity = Megajoules{Bank.at("capacityMegajoules").get<double>()};
	Result.CapacitorBank.MaxCharge = Megawatts{Bank.at("maxChargeMegawatts").get<double>()};
	Result.CapacitorBank.MaxDischarge = Megawatts{Bank.at("maxDischargeMegawatts").get<double>()};
	Result.CapacitorBank.ChargeEfficiency = Bank.at("chargeEfficiency").get<double>();
	Result.BankSetpointFraction = Bank.at("setpointFraction").get<double>();
	Result.CapacitorBuild = {Bank.at("footprintSquareMeters").get<double>(),
	                         Bank.at("initialBuildMaterials").get<std::map<std::string, int>>()};
	const Json& VanillaStorage = Root.at("vanillaPowerStorage");
	Result.VanillaStorageCapacity = Megajoules{VanillaStorage.at("capacityMegajoules").get<double>()};
	Result.VanillaStorageCharge = Megawatts{VanillaStorage.at("maxChargeMegawatts").get<double>()};
	Result.VanillaStorageComparisonCount = VanillaStorage.at("comparisonCount").get<int>();
	Result.VanillaStorageBuild = {VanillaStorage.at("footprintSquareMeters").get<double>(),
	                              VanillaStorage.at("buildMaterials").get<std::map<std::string, int>>()};
	const Json& Acceptance = Root.at("acceptance");
	Result.ComfortLoadFraction = Acceptance.at("comfortLoadFraction").get<double>();
	Result.LocalLossLimit = Acceptance.at("localLossLimit").get<double>();
	const Json& Simulation = Root.at("simulation");
	Result.SimulationStep = Seconds{Simulation.at("stepSeconds").get<double>()};
	Result.SimulationDuration = Seconds{Simulation.at("durationSeconds").get<double>()};
	return Result;
}

Scenario LoadScenario(const std::filesystem::path& Path)
{
	const Json Root = ReadJson(Path);
	Scenario Result;
	Result.File = Path.filename().string();
	Result.Name = Root.at("name").get<std::string>();
	Result.MilestoneTier = Root.at("milestoneTier").get<int>();
	Result.IsPlant = Root.value("kind", std::string{"factory"}) == "plant";
	Result.Assumptions = ReadStrings(Root, "assumptions");
	Result.Entry = ReadPosition(Root.at("entry"));
	if (Root.contains("supply"))
	{
		const Json& Supply = Root.at("supply");
		Result.Supply = ReadPosition(Supply.at("position"));
		if (Supply.contains("lineLengthMeters"))
		{
			Result.SupplyLineLength = Supply.at("lineLengthMeters").get<double>();
		}
	}
	for (const Json& Value : Root.value("blocks", Json::array()))
	{
		Result.Blocks.push_back(ReadBlock(Value));
	}
	for (const Json& Value : Root.value("factories", Json::array()))
	{
		Result.Factories.push_back(
		    {Value.at("scenario").get<std::string>(), ReadPosition(Value.at("offset"))});
	}
	if (Root.contains("pulse"))
	{
		const Json& Pulse = Root.at("pulse");
		Result.Pulse = PulseStudy{Pulse.at("transformer").get<std::string>(),
		                          Pulse.value("transformerCount", 1), Pulse.value("bankCount", 0)};
	}
	return Result;
}

} // namespace EnhancedPower::Balance
