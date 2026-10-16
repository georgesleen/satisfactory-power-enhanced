#pragma once

#include <cstddef>
#include <optional>
#include <vector>

#include "EnhancedPowerCore/Export.h"
#include "EnhancedPowerCore/Units.h"

namespace EnhancedPower
{

/// A point in world space, in meters.
struct Position
{
	double X = 0.0;
	double Y = 0.0;
	double Z = 0.0;
};

/// A building or pole on an island wire graph.
struct IslandNode
{
	Position Location;
	Megawatts Load;
	bool IsFeed = false;
};

/// An undirected wire between two nodes.
///
/// An edge with an invalid node index is ignored. A negative length counts as 0.
struct IslandEdge
{
	std::size_t From = 0;
	std::size_t To = 0;
	Meters Length;
};

/// The wire graph of one island.
struct IslandGraph
{
	std::vector<IslandNode> Nodes;
	std::vector<IslandEdge> Edges;
};

/// Sum of the lengths of the valid edges.
ENHANCEDPOWERCORE_API Meters TotalWireLength(const IslandGraph& Graph);

/// Largest straight-line distance between any two nodes.
///
/// Returns 0 for fewer than two nodes.
ENHANCEDPOWERCORE_API Meters SpatialExtent(const IslandGraph& Graph);

/// Load-weighted mean of the wire-path distance from each loaded node to its
/// nearest feed node.
///
/// Returns `std::nullopt` if there is no feed node, no node has a positive load,
/// or a node with a positive load cannot reach a feed node.
ENHANCEDPOWERCORE_API std::optional<Meters> LoadWeightedFeedDistance(const IslandGraph& Graph);

} // namespace EnhancedPower
