#include "EnhancedPowerCore/TransformerTopology.h"

#include <vector>

namespace EnhancedPower
{

namespace
{

/// True if both link ends are below `IslandCount`.
bool IsValidLink(std::size_t IslandCount, const DirectedLink& Link)
{
	return Link.FromIsland < IslandCount && Link.ToIsland < IslandCount;
}

/// Kahn's algorithm over the valid links in `Links` and in `Extra`.
bool HasCycleInLinks(std::size_t IslandCount, std::span<const DirectedLink> Links,
                     std::span<const DirectedLink> Extra)
{
	std::vector<std::size_t> Offsets(IslandCount + 1, 0);
	std::vector<std::size_t> InDegree(IslandCount, 0);
	std::size_t ValidCount = 0;
	for (const auto Group : {Links, Extra})
	{
		for (const DirectedLink& Link : Group)
		{
			if (IsValidLink(IslandCount, Link))
			{
				++Offsets[Link.FromIsland + 1];
				++InDegree[Link.ToIsland];
				++ValidCount;
			}
		}
	}
	if (ValidCount == 0)
	{
		return false;
	}
	for (std::size_t Island = 0; Island < IslandCount; ++Island)
	{
		Offsets[Island + 1] += Offsets[Island];
	}
	std::vector<std::size_t> Targets(ValidCount);
	std::vector<std::size_t> Cursor(Offsets.begin(), Offsets.end() - 1);
	for (const auto Group : {Links, Extra})
	{
		for (const DirectedLink& Link : Group)
		{
			if (IsValidLink(IslandCount, Link))
			{
				Targets[Cursor[Link.FromIsland]++] = Link.ToIsland;
			}
		}
	}

	std::vector<std::size_t> Ready;
	for (std::size_t Island = 0; Island < IslandCount; ++Island)
	{
		if (InDegree[Island] == 0)
		{
			Ready.push_back(Island);
		}
	}
	std::size_t Removed = 0;
	while (!Ready.empty())
	{
		const std::size_t Island = Ready.back();
		Ready.pop_back();
		++Removed;
		for (std::size_t Index = Offsets[Island]; Index < Offsets[Island + 1]; ++Index)
		{
			if (--InDegree[Targets[Index]] == 0)
			{
				Ready.push_back(Targets[Index]);
			}
		}
	}
	return Removed != IslandCount;
}

} // namespace

bool HasDirectedCycle(std::size_t IslandCount, std::span<const DirectedLink> Links)
{
	return HasCycleInLinks(IslandCount, Links, {});
}

bool WouldCreateCycle(std::size_t IslandCount, std::span<const DirectedLink> Links, DirectedLink Candidate)
{
	return HasCycleInLinks(IslandCount, Links, std::span<const DirectedLink>(&Candidate, 1));
}

} // namespace EnhancedPower
