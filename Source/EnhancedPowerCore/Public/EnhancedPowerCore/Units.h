#pragma once

#include <compare>

namespace EnhancedPower
{

/// Power in megawatts.
struct Megawatts
{
	double Value = 0.0;

	constexpr auto operator<=>(const Megawatts&) const = default;
	constexpr bool operator==(const Megawatts&) const = default;
};

/// Energy in megajoules.
struct Megajoules
{
	double Value = 0.0;

	constexpr auto operator<=>(const Megajoules&) const = default;
	constexpr bool operator==(const Megajoules&) const = default;
};

/// Time in seconds.
struct Seconds
{
	double Value = 0.0;

	constexpr auto operator<=>(const Seconds&) const = default;
	constexpr bool operator==(const Seconds&) const = default;
};

/// Length in meters.
struct Meters
{
	double Value = 0.0;

	constexpr auto operator<=>(const Meters&) const = default;
	constexpr bool operator==(const Meters&) const = default;
};

/// Marks a type as a unit that takes the same-unit arithmetic operators.
template <typename Type>
inline constexpr bool IsUnit = false;

template <>
inline constexpr bool IsUnit<Megawatts> = true;
template <>
inline constexpr bool IsUnit<Megajoules> = true;
template <>
inline constexpr bool IsUnit<Seconds> = true;
template <>
inline constexpr bool IsUnit<Meters> = true;

/// A unit type from this header.
template <typename Type>
concept Unit = IsUnit<Type>;

/// Sum of two values of the same unit.
template <Unit Type>
constexpr Type operator+(Type Left, Type Right)
{
	return Type{Left.Value + Right.Value};
}

/// Difference of two values of the same unit.
template <Unit Type>
constexpr Type operator-(Type Left, Type Right)
{
	return Type{Left.Value - Right.Value};
}

/// Negation of a value.
template <Unit Type>
constexpr Type operator-(Type Operand)
{
	return Type{-Operand.Value};
}

/// Value scaled by a factor.
template <Unit Type>
constexpr Type operator*(Type Left, double Factor)
{
	return Type{Left.Value * Factor};
}

/// Value scaled by a factor.
template <Unit Type>
constexpr Type operator*(double Factor, Type Right)
{
	return Type{Factor * Right.Value};
}

/// Value divided by a divisor.
template <Unit Type>
constexpr Type operator/(Type Left, double Divisor)
{
	return Type{Left.Value / Divisor};
}

/// Ratio of two values of the same unit.
template <Unit Type>
constexpr double operator/(Type Left, Type Right)
{
	return Left.Value / Right.Value;
}

/// Energy that a constant power delivers over a duration.
constexpr Megajoules operator*(Megawatts Power, Seconds Duration)
{
	return Megajoules{Power.Value * Duration.Value};
}

/// Energy that a constant power delivers over a duration.
constexpr Megajoules operator*(Seconds Duration, Megawatts Power)
{
	return Megajoules{Duration.Value * Power.Value};
}

/// Average power that moves an energy over a duration.
constexpr Megawatts operator/(Megajoules Energy, Seconds Duration)
{
	return Megawatts{Energy.Value / Duration.Value};
}

/// Time that a constant power takes to move an energy.
constexpr Seconds operator/(Megajoules Energy, Megawatts Power)
{
	return Seconds{Energy.Value / Power.Value};
}

} // namespace EnhancedPower
