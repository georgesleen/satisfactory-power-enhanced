#pragma once

#include <doctest/doctest.h>

#include <cmath>
#include <cstdint>

namespace EnhancedPower::Tests
{

/// Absolute tolerance the core model contract uses for `double` comparisons.
inline constexpr double Tolerance = 1e-9;

/// Absolute tolerance the core model contract uses for transformer link energy invariants, in megajoules.
inline constexpr double EnergyTolerance = 1e-6;

/// Deterministic SplitMix64 generator that gives the same sequence on every compiler and standard library.
class SeededRandom
{
public:
	explicit SeededRandom(std::uint64_t Seed) : State(Seed) {}

	/// Next raw 64-bit value.
	std::uint64_t Next()
	{
		State += 0x9E3779B97F4A7C15ULL;
		std::uint64_t Mixed = State;
		Mixed = (Mixed ^ (Mixed >> 30)) * 0xBF58476D1CE4E5B9ULL;
		Mixed = (Mixed ^ (Mixed >> 27)) * 0x94D049BB133111EBULL;
		return Mixed ^ (Mixed >> 31);
	}

	/// Uniform value in `[Low, High)`.
	double Uniform(double Low, double High)
	{
		constexpr int MantissaBits = 53;
		const double Unit = static_cast<double>(Next() >> (64 - MantissaBits)) /
		                    static_cast<double>(std::uint64_t{1} << MantissaBits);
		return Low + (High - Low) * Unit;
	}

	/// True with probability `Probability`.
	bool Chance(double Probability) { return Uniform(0.0, 1.0) < Probability; }

private:
	std::uint64_t State;
};

} // namespace EnhancedPower::Tests

/// Checks that two doubles differ by at most an absolute tolerance and reports both values on failure.
#define CHECK_NEAR(Actual, Expected, AbsoluteTolerance)                                                      \
	do                                                                                                       \
	{                                                                                                        \
		const double ActualValue = (Actual);                                                                 \
		const double ExpectedValue = (Expected);                                                             \
		CAPTURE(ActualValue);                                                                                \
		CAPTURE(ExpectedValue);                                                                              \
		CHECK(std::abs(ActualValue - ExpectedValue) <= (AbsoluteTolerance));                                 \
	} while (false)
