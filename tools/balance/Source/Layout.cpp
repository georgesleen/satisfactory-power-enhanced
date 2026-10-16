#include "Layout.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace EnhancedPower::Balance
{
namespace
{

constexpr double MeanFraction = 0.5;

Meters Separation(Position First, Position Second)
{
	return Meters{std::hypot(First.X - Second.X, First.Y - Second.Y, First.Z - Second.Z)};
}

std::size_t AddNode(IslandGraph& Graph, Position Location, Megawatts Load = {}, bool Feed = false)
{
	Graph.Nodes.push_back({Location, Load, Feed});
	return Graph.Nodes.size() - 1;
}

void Connect(IslandGraph& Graph, std::size_t From, std::size_t To)
{
	Graph.Edges.push_back({From, To, Separation(Graph.Nodes[From].Location, Graph.Nodes[To].Location)});
}

Consumer Demand(const Block& Description, const BuildingTable& Buildings)
{
	const BuildingFacts& Facts = Buildings.Buildings.at(Description.Building);
	const double Multiplier = std::pow(Description.Clock, Facts.PowerExponent) *
	                          std::pow(1.0 + Description.Boost, Facts.BoostExponent);
	if (Description.Recipe.empty())
	{
		return {Facts.Power * Multiplier, Facts.Power * Multiplier, Seconds{}};
	}
	const VariableRecipe& Recipe = Buildings.VariableRecipes.at(Description.Recipe);
	if (Recipe.Building != Description.Building || !(Recipe.Duration > Seconds{}))
	{
		throw std::runtime_error("invalid variable recipe for " + Description.Label);
	}
	return {Recipe.Minimum * Multiplier, Recipe.Maximum * Multiplier, Recipe.Duration / Description.Clock};
}

} // namespace

Factory BuildFactory(const Scenario& Description, const BuildingTable& Buildings,
                     std::optional<Wiring> Override)
{
	Factory Result;
	AddNode(Result.Graph, Description.Entry, {}, true);
	for (const Block& Block : Description.Blocks)
	{
		const Consumer Consumer = Demand(Block, Buildings);
		const Megawatts Mean = (Consumer.Minimum + Consumer.Maximum) * MeanFraction;
		const BuildingFacts& Facts = Buildings.Buildings.at(Block.Building);
		Result.Generation =
		    Result.Generation + Facts.Generation * Block.Clock * static_cast<double>(Block.Count);
		const Wiring Layout = Override.value_or(Block.Layout);
		const int Rows = (Block.Count + Block.Columns - 1) / Block.Columns;
		for (int Row = 0; Row < Rows; Row++)
		{
			const int Count = std::min(Block.Columns, Block.Count - Row * Block.Columns);
			const Position Head{Block.Origin.X - Block.SpacingX, Block.Origin.Y + Row * Block.SpacingY,
			                    Block.Origin.Z};
			const std::size_t HeadIndex = AddNode(Result.Graph, Head);
			Connect(Result.Graph, 0, HeadIndex);
			std::size_t Previous = HeadIndex;
			std::size_t Pole = HeadIndex;
			for (int Column = 0; Column < Count; Column++)
			{
				const Position Location{Block.Origin.X + Column * Block.SpacingX,
				                        Block.Origin.Y + Row * Block.SpacingY, Block.Origin.Z};
				if (Layout == Wiring::PoleBranch && Column % Block.MachinesPerPole == 0)
				{
					const Position PoleLocation{Location.X, Location.Y - Block.SpacingY * MeanFraction,
					                            Location.Z};
					const std::size_t NextPole = AddNode(Result.Graph, PoleLocation);
					Connect(Result.Graph, Pole, NextPole);
					Pole = NextPole;
				}
				const std::size_t Machine = AddNode(Result.Graph, Location, Mean);
				Connect(Result.Graph, Layout == Wiring::PoleBranch ? Pole : Previous, Machine);
				Previous = Machine;
				Result.Consumers.push_back(Consumer);
				Result.Mean = Result.Mean + Mean;
				Result.Peak = Result.Peak + Consumer.Maximum;
			}
		}
	}
	return Result;
}

IslandGraph WithSupply(const Factory& Local, const Scenario& Description)
{
	IslandGraph Result = Local.Graph;
	if (Description.Supply)
	{
		for (IslandNode& Node : Result.Nodes)
		{
			Node.IsFeed = false;
		}
		const std::size_t Feed = AddNode(Result, *Description.Supply, {}, true);
		const Meters Length = Description.SupplyLineLength
		                          ? Meters{*Description.SupplyLineLength}
		                          : Separation(*Description.Supply, Description.Entry);
		Result.Edges.push_back({Feed, 0, Length});
	}
	return Result;
}

std::vector<Meters> Distances(const IslandGraph& Graph)
{
	const std::optional<Meters> Weighted = LoadWeightedFeedDistance(Graph);
	if (!Weighted)
	{
		throw std::runtime_error("island has no reachable positive load");
	}
	return {TotalWireLength(Graph), SpatialExtent(Graph), *Weighted};
}

} // namespace EnhancedPower::Balance
