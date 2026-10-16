#pragma once

#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include "EnhancedPowerCore/FastBuffer.h"
#include "EnhancedPowerCore/IslandGraph.h"
#include "EnhancedPowerCore/Loss.h"
#include "EnhancedPowerCore/Thermal.h"

namespace EnhancedPower::Balance
{

/// Power facts for one building class from the derived building table.
struct BuildingFacts
{
	std::string Name;
	Megawatts Power;
	Megawatts Generation;
	double PowerExponent = 1.0;
	double BoostExponent = 2.0;
};

/// Variable power facts for one recipe; the draw ramps linearly from minimum to maximum each cycle.
struct VariableRecipe
{
	std::string Name;
	std::string Building;
	Seconds Duration;
	Megawatts Minimum;
	Megawatts Maximum;
};

/// The derived building table: buildings and variable-power recipes keyed by class name.
struct BuildingTable
{
	std::map<std::string, BuildingFacts> Buildings;
	std::map<std::string, VariableRecipe> VariableRecipes;
};

/// One voltage tier: its loss parameters and the milestone tier that unlocks it.
struct TierTuning
{
	std::string Name;
	TierParameters Parameters;
	int UnlockTier = 0;
};

/// One transformer size from the tuning catalog.
struct TransformerSize
{
	std::string Name;
	Megawatts Rating;
};

/// Build area and material counts for one storage unit.
struct StorageBuild
{
	double FootprintSquareMeters = 0.0;
	std::map<std::string, int> Materials;
};

/// All tunable values the harness reads from the tuning file.
struct Tuning
{
	std::vector<TierTuning> Tiers;
	std::vector<TransformerSize> Transformers;
	ThermalParameters Thermal;
	BufferParameters CapacitorBank;
	Megajoules VanillaStorageCapacity;
	Megawatts VanillaStorageCharge;
	int VanillaStorageComparisonCount = 1;
	StorageBuild CapacitorBuild;
	StorageBuild VanillaStorageBuild;
	double BankSetpointFraction = 1.0;
	double ComfortLoadFraction = 1.0;
	double LocalLossLimit = 0.0;
	Seconds SimulationStep;
	Seconds SimulationDuration;

	const TierTuning& Tier(const std::string& Name) const;
	const TransformerSize& Transformer(const std::string& Name) const;
};

/// How a block wires its machines.
enum class Wiring
{
	PoleBranch,
	DaisyChain,
};

/// A rectangular block of identical machines in rows.
///
/// Positions are meters relative to the scenario origin. Rows run along X; successive rows step along Y.
struct Block
{
	std::string Label;
	std::string Building;
	std::string Recipe;
	int Count = 0;
	int Columns = 1;
	double Clock = 1.0;
	double Boost = 0.0;
	Position Origin;
	double SpacingX = 0.0;
	double SpacingY = 0.0;
	Wiring Layout = Wiring::PoleBranch;
	int MachinesPerPole = 4;
};

/// A factory placed inside a plant scenario.
struct PlacedFactory
{
	std::string Scenario;
	Position Offset;
};

/// Pulse study settings for a scenario with variable-power machines.
struct PulseStudy
{
	std::string Transformer;
	int TransformerCount = 1;
	int BankCount = 0;
};

/// One scenario file: a factory, or a generator plant that feeds several factories.
struct Scenario
{
	std::string File;
	std::string Name;
	int MilestoneTier = 0;
	bool IsPlant = false;
	std::vector<std::string> Assumptions;
	Position Entry;
	std::optional<Position> Supply;
	std::optional<double> SupplyLineLength;
	std::vector<Block> Blocks;
	std::vector<PlacedFactory> Factories;
	std::optional<PulseStudy> Pulse;
};

/// Reads the derived building table. Throws on a missing file or malformed JSON.
BuildingTable LoadBuildingTable(const std::filesystem::path& Path);
/// Reads the tuning file. Throws on a missing file, a missing field, or malformed JSON.
Tuning LoadTuning(const std::filesystem::path& Path);
/// Reads one scenario file. Throws on a missing file, a missing field, or malformed JSON.
Scenario LoadScenario(const std::filesystem::path& Path);

} // namespace EnhancedPower::Balance
