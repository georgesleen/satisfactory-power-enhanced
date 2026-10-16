#include "TestSupport.h"

#include <EnhancedPowerCore/IslandGraph.h>

#include <cstddef>
#include <optional>

using namespace EnhancedPower;
using EnhancedPower::Tests::Tolerance;

namespace
{

IslandNode Load(double X, double LoadMegawatts)
{
	return IslandNode{.Location = Position{.X = X}, .Load = Megawatts{LoadMegawatts}, .IsFeed = false};
}

IslandNode Feed(double X, double LoadMegawatts = 0.0)
{
	return IslandNode{.Location = Position{.X = X}, .Load = Megawatts{LoadMegawatts}, .IsFeed = true};
}

IslandEdge Wire(std::size_t From, std::size_t To, double LengthMeters)
{
	return IslandEdge{.From = From, .To = To, .Length = Meters{LengthMeters}};
}

} // namespace

TEST_CASE("TotalWireLength sums valid edges")
{
	CHECK(TotalWireLength(IslandGraph{}).Value == 0.0);

	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(10.0, 1.0), Load(30.0, 1.0)};
	CHECK(TotalWireLength(Graph).Value == 0.0);

	Graph.Edges = {Wire(0, 1, 10.0), Wire(1, 2, 20.0)};
	CHECK_NEAR(TotalWireLength(Graph).Value, 30.0, Tolerance);

	SUBCASE("Edges with an invalid index are ignored")
	{
		Graph.Edges.push_back(Wire(1, 3, 100.0));
		Graph.Edges.push_back(Wire(7, 0, 100.0));
		CHECK_NEAR(TotalWireLength(Graph).Value, 30.0, Tolerance);
	}
	SUBCASE("A negative length counts as zero")
	{
		Graph.Edges.push_back(Wire(0, 2, -50.0));
		CHECK_NEAR(TotalWireLength(Graph).Value, 30.0, Tolerance);
	}
	SUBCASE("Parallel wires both count")
	{
		Graph.Edges.push_back(Wire(1, 0, 10.0));
		CHECK_NEAR(TotalWireLength(Graph).Value, 40.0, Tolerance);
	}
}

TEST_CASE("SpatialExtent is the largest straight-line distance between nodes")
{
	IslandGraph Graph;
	CHECK(SpatialExtent(Graph).Value == 0.0);

	Graph.Nodes = {Feed(5.0)};
	CHECK(SpatialExtent(Graph).Value == 0.0);

	Graph.Nodes = {
	    IslandNode{.Location = Position{.X = 0.0, .Y = 0.0, .Z = 0.0}, .Load = Megawatts{0.0}},
	    IslandNode{.Location = Position{.X = 3.0, .Y = 4.0, .Z = 12.0}, .Load = Megawatts{0.0}},
	    IslandNode{.Location = Position{.X = 1.0, .Y = 1.0, .Z = 1.0}, .Load = Megawatts{0.0}},
	};
	CHECK_NEAR(SpatialExtent(Graph).Value, 13.0, Tolerance);

	SUBCASE("Wires do not matter")
	{
		Graph.Edges = {Wire(0, 2, 1000.0)};
		CHECK_NEAR(SpatialExtent(Graph).Value, 13.0, Tolerance);
	}
	SUBCASE("Negative coordinates count")
	{
		Graph.Nodes.push_back(
		    IslandNode{.Location = Position{.X = -3.0, .Y = -4.0, .Z = -12.0}, .Load = Megawatts{0.0}});
		CHECK_NEAR(SpatialExtent(Graph).Value, 26.0, Tolerance);
	}
}

TEST_CASE("LoadWeightedFeedDistance returns nullopt when it has no answer")
{
	SUBCASE("Empty graph")
	{
		CHECK_FALSE(LoadWeightedFeedDistance(IslandGraph{}).has_value());
	}
	SUBCASE("No feed node")
	{
		IslandGraph Graph;
		Graph.Nodes = {Load(0.0, 5.0), Load(10.0, 5.0)};
		Graph.Edges = {Wire(0, 1, 10.0)};
		CHECK_FALSE(LoadWeightedFeedDistance(Graph).has_value());
	}
	SUBCASE("No positive load")
	{
		IslandGraph Graph;
		Graph.Nodes = {Feed(0.0), Load(10.0, 0.0), Load(20.0, -4.0)};
		Graph.Edges = {Wire(0, 1, 10.0), Wire(1, 2, 10.0)};
		CHECK_FALSE(LoadWeightedFeedDistance(Graph).has_value());
	}
	SUBCASE("A loaded node cannot reach any feed")
	{
		IslandGraph Graph;
		Graph.Nodes = {Feed(0.0), Load(10.0, 5.0), Load(100.0, 1.0)};
		Graph.Edges = {Wire(0, 1, 10.0)};
		CHECK_FALSE(LoadWeightedFeedDistance(Graph).has_value());
	}
	SUBCASE("A loaded node reaches a feed only through an invalid edge")
	{
		IslandGraph Graph;
		Graph.Nodes = {Feed(0.0), Load(10.0, 5.0)};
		Graph.Edges = {Wire(0, 2, 10.0), Wire(2, 1, 10.0)};
		CHECK_FALSE(LoadWeightedFeedDistance(Graph).has_value());
	}
}

TEST_CASE("Unreachable nodes without load do not matter")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(10.0, 5.0), Load(500.0, 0.0), Load(600.0, -2.0)};
	Graph.Edges = {Wire(0, 1, 10.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, 10.0, Tolerance);
}

TEST_CASE("LoadWeightedFeedDistance weights path distance by load")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(10.0, 1.0), Load(40.0, 3.0)};
	Graph.Edges = {Wire(0, 1, 10.0), Wire(1, 2, 30.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, (1.0 * 10.0 + 3.0 * 40.0) / 4.0, Tolerance);
}

TEST_CASE("Edges are undirected")
{
	IslandGraph Graph;
	Graph.Nodes = {Load(0.0, 2.0), Feed(25.0)};
	Graph.Edges = {Wire(0, 1, 25.0)};
	const std::optional<Meters> Forward = LoadWeightedFeedDistance(Graph);
	Graph.Edges = {Wire(1, 0, 25.0)};
	const std::optional<Meters> Backward = LoadWeightedFeedDistance(Graph);
	REQUIRE(Forward.has_value());
	REQUIRE(Backward.has_value());
	CHECK_NEAR(Forward->Value, 25.0, Tolerance);
	CHECK_NEAR(Backward->Value, 25.0, Tolerance);
}

TEST_CASE("Distance follows the shortest wire path, not the straight line")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(5.0, 1.0), Load(200.0, 0.0)};
	Graph.Edges = {Wire(0, 2, 100.0), Wire(2, 1, 100.0), Wire(0, 1, 500.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, 200.0, Tolerance);
}

TEST_CASE("Each node uses its nearest feed")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(10.0, 2.0), Load(90.0, 2.0), Feed(100.0)};
	Graph.Edges = {Wire(0, 1, 10.0), Wire(1, 2, 80.0), Wire(2, 3, 10.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, 10.0, Tolerance);
}

TEST_CASE("A loaded feed node contributes distance zero")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0, 3.0), Load(20.0, 1.0)};
	Graph.Edges = {Wire(0, 1, 20.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, (3.0 * 0.0 + 1.0 * 20.0) / 4.0, Tolerance);

	IslandGraph Alone;
	Alone.Nodes = {Feed(0.0, 3.0)};
	const std::optional<Meters> AloneDistance = LoadWeightedFeedDistance(Alone);
	REQUIRE(AloneDistance.has_value());
	CHECK(AloneDistance->Value == 0.0);
}

TEST_CASE("A negative edge length counts as zero in the path distance")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(50.0, 1.0)};
	Graph.Edges = {Wire(0, 1, -50.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK(Distance->Value == 0.0);
}

TEST_CASE("Invalid edges do not shorten paths")
{
	IslandGraph Graph;
	Graph.Nodes = {Feed(0.0), Load(50.0, 1.0)};
	Graph.Edges = {Wire(0, 1, 50.0), Wire(1, 9, 0.0), Wire(9, 0, 0.0)};
	const std::optional<Meters> Distance = LoadWeightedFeedDistance(Graph);
	REQUIRE(Distance.has_value());
	CHECK_NEAR(Distance->Value, 50.0, Tolerance);
}

TEST_CASE("A compact factory has a smaller load-weighted feed distance than a long feeder")
{
	constexpr std::size_t BranchCount = 20;
	constexpr double BranchLength = 10.0;
	constexpr double FeederLength = 200.0;
	constexpr double LoadPerMachine = 5.0;

	IslandGraph Compact;
	Compact.Nodes.push_back(Feed(0.0));
	for (std::size_t Branch = 0; Branch < BranchCount; Branch++)
	{
		Compact.Nodes.push_back(Load(BranchLength, LoadPerMachine));
		Compact.Edges.push_back(Wire(0, Compact.Nodes.size() - 1, BranchLength));
	}

	IslandGraph Feeder;
	Feeder.Nodes.push_back(Feed(0.0));
	Feeder.Nodes.push_back(Load(FeederLength, 0.0));
	Feeder.Edges.push_back(Wire(0, 1, FeederLength));
	constexpr double StubLength = 1.0;
	for (std::size_t Machine = 0; Machine < BranchCount; Machine++)
	{
		Feeder.Nodes.push_back(Load(FeederLength + StubLength, LoadPerMachine));
		Feeder.Edges.push_back(Wire(1, Feeder.Nodes.size() - 1, StubLength));
	}

	CHECK(TotalWireLength(Compact).Value <= TotalWireLength(Feeder).Value);

	const std::optional<Meters> CompactDistance = LoadWeightedFeedDistance(Compact);
	const std::optional<Meters> FeederDistance = LoadWeightedFeedDistance(Feeder);
	REQUIRE(CompactDistance.has_value());
	REQUIRE(FeederDistance.has_value());
	CHECK_NEAR(CompactDistance->Value, BranchLength, Tolerance);
	CHECK_NEAR(FeederDistance->Value, FeederLength + StubLength, Tolerance);
	CHECK(CompactDistance->Value < FeederDistance->Value);
}
