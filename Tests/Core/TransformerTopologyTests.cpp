#include "TestSupport.h"

#include <EnhancedPowerCore/TransformerTopology.h>

#include <array>
#include <vector>

using namespace EnhancedPower;

TEST_CASE("An empty topology has no cycle")
{
	CHECK_FALSE(HasDirectedCycle(0, {}));
	CHECK_FALSE(HasDirectedCycle(5, {}));
	CHECK_FALSE(WouldCreateCycle(0, {}, DirectedLink{0, 0}));
	CHECK(WouldCreateCycle(1, {}, DirectedLink{0, 0}));
}

TEST_CASE("Directional chains and converging branches do not cycle")
{
	const std::array Chain{DirectedLink{0, 1}, DirectedLink{1, 2}, DirectedLink{2, 3}};
	CHECK_FALSE(HasDirectedCycle(4, Chain));
	CHECK_FALSE(WouldCreateCycle(4, Chain, DirectedLink{0, 3}));
	CHECK(WouldCreateCycle(4, Chain, DirectedLink{3, 0}));
	CHECK(WouldCreateCycle(4, Chain, DirectedLink{3, 1}));

	const std::array Diamond{DirectedLink{0, 1}, DirectedLink{0, 2}, DirectedLink{1, 3}, DirectedLink{2, 3}};
	CHECK_FALSE(HasDirectedCycle(4, Diamond));
	CHECK_FALSE(WouldCreateCycle(4, Diamond, DirectedLink{1, 2}));
	CHECK(WouldCreateCycle(4, Diamond, DirectedLink{3, 0}));
}

TEST_CASE("Self links and opposite directions are cycles")
{
	const std::array Self{DirectedLink{2, 2}};
	CHECK(HasDirectedCycle(3, Self));
	const std::array Pair{DirectedLink{0, 1}, DirectedLink{1, 0}};
	CHECK(HasDirectedCycle(2, Pair));
	const std::array Ring{DirectedLink{0, 1}, DirectedLink{1, 2}, DirectedLink{2, 0}};
	CHECK(HasDirectedCycle(3, Ring));
}

TEST_CASE("Parallel links in the same direction are not a cycle")
{
	const std::array Parallel{DirectedLink{0, 1}, DirectedLink{0, 1}, DirectedLink{1, 2}, DirectedLink{1, 2}};
	CHECK_FALSE(HasDirectedCycle(3, Parallel));
	CHECK_FALSE(WouldCreateCycle(3, Parallel, DirectedLink{0, 1}));
	CHECK(WouldCreateCycle(3, Parallel, DirectedLink{2, 0}));
}

TEST_CASE("Invalid links and candidates are ignored")
{
	const std::array Invalid{DirectedLink{0, 1}, DirectedLink{1, 3}, DirectedLink{3, 0}, DirectedLink{9, 9}};
	CHECK_FALSE(HasDirectedCycle(3, Invalid));
	CHECK_FALSE(WouldCreateCycle(3, Invalid, DirectedLink{3, 3}));
	CHECK_FALSE(WouldCreateCycle(3, Invalid, DirectedLink{99, 0}));
	CHECK_FALSE(WouldCreateCycle(3, Invalid, DirectedLink{0, 99}));
	CHECK(WouldCreateCycle(3, Invalid, DirectedLink{1, 0}));

	const std::array ExistingCycle{DirectedLink{0, 1}, DirectedLink{1, 0}};
	CHECK(WouldCreateCycle(3, ExistingCycle, DirectedLink{99, 99}));
	CHECK(WouldCreateCycle(3, ExistingCycle, DirectedLink{1, 2}));
}

TEST_CASE("A cycle in a disconnected component still counts")
{
	const std::array Links{DirectedLink{0, 1}, DirectedLink{3, 4}, DirectedLink{4, 5}, DirectedLink{5, 3}};
	CHECK(HasDirectedCycle(7, Links));
}

TEST_CASE("A large acyclic topology stays acyclic until a back link closes a path")
{
	constexpr std::size_t IslandCount = 1000;
	constexpr std::size_t Skip = 17;
	std::vector<DirectedLink> Links;
	for (std::size_t Island = 0; Island + 1 < IslandCount; Island++)
	{
		Links.push_back(DirectedLink{Island, Island + 1});
		if (Island + Skip < IslandCount)
		{
			Links.push_back(DirectedLink{Island, Island + Skip});
		}
	}
	CHECK_FALSE(HasDirectedCycle(IslandCount, Links));
	CHECK_FALSE(WouldCreateCycle(IslandCount, Links, DirectedLink{0, IslandCount - 1}));
	CHECK(WouldCreateCycle(IslandCount, Links, DirectedLink{IslandCount - 1, 0}));
}
