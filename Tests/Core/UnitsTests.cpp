#include "TestSupport.h"

#include <EnhancedPowerCore/Units.h>

#include <compare>
#include <concepts>
#include <type_traits>

using namespace EnhancedPower;
using EnhancedPower::Tests::Tolerance;

namespace
{

template <typename Unit>
concept HasSameUnitArithmetic = requires(Unit Left, Unit Right, double Scalar) {
	{ Left + Right } -> std::same_as<Unit>;
	{ Left - Right } -> std::same_as<Unit>;
	{ -Left } -> std::same_as<Unit>;
	{ Left * Scalar } -> std::same_as<Unit>;
	{ Scalar * Left } -> std::same_as<Unit>;
	{ Left / Scalar } -> std::same_as<Unit>;
	{ Left / Right } -> std::same_as<double>;
	{ Left == Right } -> std::same_as<bool>;
	{ Left <=> Right };
};

template <typename Unit>
concept DividesDouble = requires(double Scalar, Unit Value) { Scalar / Value; };

template <typename Left, typename Right>
concept Addable = requires(Left LeftValue, Right RightValue) { LeftValue + RightValue; };

template <typename Unit>
constexpr bool SameUnitArithmeticIsConstexpr()
{
	constexpr Unit Three{3.0};
	constexpr Unit Two{2.0};
	static_assert((Three + Two).Value == 5.0);
	static_assert((Three - Two).Value == 1.0);
	static_assert((-Three).Value == -3.0);
	static_assert((Three * 2.0).Value == 6.0);
	static_assert((2.0 * Three).Value == 6.0);
	static_assert((Three / 2.0).Value == 1.5);
	static_assert(Three / Two == 1.5);
	static_assert(Two < Three);
	static_assert(Three == Unit{3.0});
	static_assert(Three != Two);
	return true;
}

} // namespace

TEST_CASE("Units support same-unit arithmetic and comparison")
{
	static_assert(HasSameUnitArithmetic<Megawatts>);
	static_assert(HasSameUnitArithmetic<Megajoules>);
	static_assert(HasSameUnitArithmetic<Seconds>);
	static_assert(HasSameUnitArithmetic<Meters>);
	static_assert(SameUnitArithmeticIsConstexpr<Megawatts>());
	static_assert(SameUnitArithmeticIsConstexpr<Megajoules>());
	static_assert(SameUnitArithmeticIsConstexpr<Seconds>());
	static_assert(SameUnitArithmeticIsConstexpr<Meters>());
}

TEST_CASE("Units default to zero")
{
	CHECK(Megawatts{}.Value == 0.0);
	CHECK(Megajoules{}.Value == 0.0);
	CHECK(Seconds{}.Value == 0.0);
	CHECK(Meters{}.Value == 0.0);
}

TEST_CASE("Cross-unit operations give the physical unit")
{
	constexpr Megawatts Power{4.0};
	constexpr Seconds Duration{2.5};
	constexpr Megajoules Energy{10.0};

	static_assert(std::is_same_v<decltype(Power * Duration), Megajoules>);
	static_assert(std::is_same_v<decltype(Duration * Power), Megajoules>);
	static_assert(std::is_same_v<decltype(Energy / Duration), Megawatts>);
	static_assert(std::is_same_v<decltype(Energy / Power), Seconds>);

	static_assert((Power * Duration).Value == 10.0);
	static_assert((Duration * Power).Value == 10.0);
	static_assert((Energy / Duration).Value == 4.0);
	static_assert((Energy / Power).Value == 2.5);

	const Megajoules RoundTrip = (Energy / Duration) * Duration;
	CHECK_NEAR(RoundTrip.Value, Energy.Value, Tolerance);
}

TEST_CASE("Units have no implicit conversions")
{
	static_assert(!std::is_convertible_v<double, Megawatts>);
	static_assert(!std::is_convertible_v<double, Megajoules>);
	static_assert(!std::is_convertible_v<double, Seconds>);
	static_assert(!std::is_convertible_v<double, Meters>);
	static_assert(!std::is_convertible_v<Megawatts, double>);
	static_assert(!std::is_convertible_v<Megawatts, Megajoules>);
	static_assert(!std::is_convertible_v<Megajoules, Megawatts>);
	static_assert(!std::is_convertible_v<Seconds, Meters>);
	static_assert(!std::is_convertible_v<Meters, Seconds>);

	static_assert(!Addable<Megawatts, Megajoules>);
	static_assert(!Addable<Seconds, Meters>);
	static_assert(!Addable<Megawatts, double>);
	static_assert(!Addable<double, Meters>);
}

TEST_CASE("Units divide only by a double, never a double by a unit")
{
	static_assert(!DividesDouble<Megawatts>);
	static_assert(!DividesDouble<Megajoules>);
	static_assert(!DividesDouble<Seconds>);
	static_assert(!DividesDouble<Meters>);
}
