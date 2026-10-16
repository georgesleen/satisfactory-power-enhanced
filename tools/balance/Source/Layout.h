#pragma once

#include "Model.h"

namespace EnhancedPower::Balance
{

/// One machine's constant or ramped demand.
struct Consumer
{
	Megawatts Minimum;
	Megawatts Maximum;
	Seconds Cycle;
};

/// Expanded factory wiring and demand.
struct Factory
{
	IslandGraph Graph;
	std::vector<Consumer> Consumers;
	Megawatts Mean;
	Megawatts Peak;
	Megawatts Generation;
};

/// Expands a scenario's building blocks into an island graph.
Factory BuildFactory(const Scenario& Description, const BuildingTable& Buildings,
                     std::optional<Wiring> Override = std::nullopt);

/// Adds a distant feed to a factory graph, preserving the factory entry as node zero.
IslandGraph WithSupply(const Factory& Local, const Scenario& Description);

/// Returns the three candidate distances; throws if a load cannot reach a feed.
std::vector<Meters> Distances(const IslandGraph& Graph);

} // namespace EnhancedPower::Balance
