#pragma once

#include <cstddef>
#include <span>

#include "EnhancedPowerCore/Export.h"

namespace EnhancedPower
{

/// A transformer that carries power from its primary island to its secondary
/// island.
struct DirectedLink
{
	std::size_t FromIsland = 0;
	std::size_t ToIsland = 0;
};

/// True if the transformer links form a directed cycle.
///
/// A link with an index at or above `IslandCount` is ignored. A link from an
/// island to itself is a cycle.
ENHANCEDPOWERCORE_API bool HasDirectedCycle(std::size_t IslandCount, std::span<const DirectedLink> Links);

/// True if `Links` plus `Candidate` form a directed cycle.
///
/// An ignored candidate gives the result for `Links` alone.
ENHANCEDPOWERCORE_API bool WouldCreateCycle(std::size_t IslandCount, std::span<const DirectedLink> Links,
                                            DirectedLink Candidate);

} // namespace EnhancedPower
