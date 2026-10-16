#include "EnhancedPowerCore/IslandGraph.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <queue>
#include <utility>

namespace EnhancedPower
{

namespace
{

/// True if both edge ends are valid node indices.
bool IsValidEdge(const IslandGraph& Graph, const IslandEdge& Edge)
{
	return Edge.From < Graph.Nodes.size() && Edge.To < Graph.Nodes.size();
}

/// Edge length with negative and NaN values replaced by 0.
double EdgeLength(const IslandEdge& Edge)
{
	return Edge.Length > Meters{} ? Edge.Length.Value : 0.0;
}

/// Adjacency of an undirected graph in compressed sparse row form.
struct Adjacency
{
	std::vector<std::size_t> Offsets;
	std::vector<std::pair<std::size_t, double>> Neighbors;
};

/// Builds the adjacency of the valid edges.
Adjacency BuildAdjacency(const IslandGraph& Graph)
{
	const std::size_t NodeCount = Graph.Nodes.size();
	Adjacency Result;
	Result.Offsets.assign(NodeCount + 1, 0);
	for (const IslandEdge& Edge : Graph.Edges)
	{
		if (IsValidEdge(Graph, Edge))
		{
			++Result.Offsets[Edge.From + 1];
			++Result.Offsets[Edge.To + 1];
		}
	}
	for (std::size_t Node = 0; Node < NodeCount; ++Node)
	{
		Result.Offsets[Node + 1] += Result.Offsets[Node];
	}
	Result.Neighbors.resize(Result.Offsets[NodeCount]);
	std::vector<std::size_t> Cursor(Result.Offsets.begin(), Result.Offsets.end() - 1);
	for (const IslandEdge& Edge : Graph.Edges)
	{
		if (IsValidEdge(Graph, Edge))
		{
			const double Length = EdgeLength(Edge);
			Result.Neighbors[Cursor[Edge.From]++] = {Edge.To, Length};
			Result.Neighbors[Cursor[Edge.To]++] = {Edge.From, Length};
		}
	}
	return Result;
}

} // namespace

Meters TotalWireLength(const IslandGraph& Graph)
{
	double Total = 0.0;
	for (const IslandEdge& Edge : Graph.Edges)
	{
		if (IsValidEdge(Graph, Edge))
		{
			Total += EdgeLength(Edge);
		}
	}
	return Meters{Total};
}

Meters SpatialExtent(const IslandGraph& Graph)
{
	double LargestSquared = 0.0;
	const std::size_t NodeCount = Graph.Nodes.size();
	for (std::size_t First = 0; First < NodeCount; ++First)
	{
		const Position& A = Graph.Nodes[First].Location;
		for (std::size_t Second = First + 1; Second < NodeCount; ++Second)
		{
			const Position& B = Graph.Nodes[Second].Location;
			const double DeltaX = A.X - B.X;
			const double DeltaY = A.Y - B.Y;
			const double DeltaZ = A.Z - B.Z;
			LargestSquared = std::max(LargestSquared, DeltaX * DeltaX + DeltaY * DeltaY + DeltaZ * DeltaZ);
		}
	}
	return Meters{std::sqrt(LargestSquared)};
}

std::optional<Meters> LoadWeightedFeedDistance(const IslandGraph& Graph)
{
	const std::size_t NodeCount = Graph.Nodes.size();
	constexpr double Unreached = std::numeric_limits<double>::infinity();

	using Entry = std::pair<double, std::size_t>;
	std::priority_queue<Entry, std::vector<Entry>, std::greater<>> Frontier;
	std::vector<double> Distance(NodeCount, Unreached);
	for (std::size_t Node = 0; Node < NodeCount; ++Node)
	{
		if (Graph.Nodes[Node].IsFeed)
		{
			Distance[Node] = 0.0;
			Frontier.emplace(0.0, Node);
		}
	}
	if (Frontier.empty())
	{
		return std::nullopt;
	}

	const Adjacency Links = BuildAdjacency(Graph);
	while (!Frontier.empty())
	{
		const auto [NodeDistance, Node] = Frontier.top();
		Frontier.pop();
		if (NodeDistance > Distance[Node])
		{
			continue;
		}
		for (std::size_t Index = Links.Offsets[Node]; Index < Links.Offsets[Node + 1]; ++Index)
		{
			const auto [Neighbor, Length] = Links.Neighbors[Index];
			const double Candidate = NodeDistance + Length;
			if (Candidate < Distance[Neighbor])
			{
				Distance[Neighbor] = Candidate;
				Frontier.emplace(Candidate, Neighbor);
			}
		}
	}

	double WeightedSum = 0.0;
	double LoadSum = 0.0;
	for (std::size_t Node = 0; Node < NodeCount; ++Node)
	{
		const Megawatts Load = Graph.Nodes[Node].Load;
		if (!(Load > Megawatts{}))
		{
			continue;
		}
		if (Distance[Node] == Unreached)
		{
			return std::nullopt;
		}
		WeightedSum += Load.Value * Distance[Node];
		LoadSum += Load.Value;
	}
	if (!(LoadSum > 0.0))
	{
		return std::nullopt;
	}
	return Meters{WeightedSum / LoadSum};
}

} // namespace EnhancedPower
