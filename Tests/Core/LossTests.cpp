#include "TestSupport.h"

#include <EnhancedPowerCore/Loss.h>

using namespace EnhancedPower;
using EnhancedPower::Tests::Tolerance;

namespace
{

constexpr double CapacityMegawatts = 600.0;
constexpr double ReferenceDistanceMeters = 1000.0;
constexpr double ReferenceLossFraction = 0.05;

TierParameters MediumVoltage()
{
	return TierParameters{
	    .Capacity = Megawatts{CapacityMegawatts},
	    .ReferenceDistance = Meters{ReferenceDistanceMeters},
	    .ReferenceLossFraction = ReferenceLossFraction,
	};
}

double LossAt(double LoadMegawatts, double DistanceMeters)
{
	return IslandLoss(MediumVoltage(), Megawatts{LoadMegawatts}, Meters{DistanceMeters}).Value;
}

} // namespace

TEST_CASE("No load or no distance means no loss")
{
	CHECK(LossAt(0.0, ReferenceDistanceMeters) == 0.0);
	CHECK(LossAt(-50.0, ReferenceDistanceMeters) == 0.0);
	CHECK(LossAt(CapacityMegawatts, 0.0) == 0.0);
	CHECK(LossAt(CapacityMegawatts, -10.0) == 0.0);
	CHECK(LossAt(-50.0, -10.0) == 0.0);
}

TEST_CASE("Full capacity over the reference distance loses the reference fraction")
{
	CHECK_NEAR(LossAt(CapacityMegawatts, ReferenceDistanceMeters), ReferenceLossFraction * CapacityMegawatts,
	           Tolerance);
}

TEST_CASE("Loss is quadratic in load")
{
	const double Base = LossAt(100.0, ReferenceDistanceMeters);
	CHECK(Base > 0.0);
	CHECK_NEAR(LossAt(200.0, ReferenceDistanceMeters), 4.0 * Base, Tolerance);
	CHECK_NEAR(LossAt(300.0, ReferenceDistanceMeters), 9.0 * Base, Tolerance);
	CHECK_NEAR(LossAt(50.0, ReferenceDistanceMeters), 0.25 * Base, Tolerance);
}

TEST_CASE("Loss is linear in distance")
{
	const double Base = LossAt(300.0, 250.0);
	CHECK(Base > 0.0);
	CHECK_NEAR(LossAt(300.0, 500.0), 2.0 * Base, Tolerance);
	CHECK_NEAR(LossAt(300.0, 2500.0), 10.0 * Base, Tolerance);
}

TEST_CASE("The loss fraction grows with load, so a lightly loaded island loses a smaller share")
{
	const double LightShare = LossAt(60.0, ReferenceDistanceMeters) / 60.0;
	const double FullShare = LossAt(CapacityMegawatts, ReferenceDistanceMeters) / CapacityMegawatts;
	CHECK_NEAR(LightShare, ReferenceLossFraction * 0.1, Tolerance);
	CHECK(LightShare < FullShare);
}

TEST_CASE("A zero reference fraction is lossless")
{
	TierParameters Tier = MediumVoltage();
	Tier.ReferenceLossFraction = 0.0;
	CHECK(IslandLoss(Tier, Megawatts{CapacityMegawatts}, Meters{ReferenceDistanceMeters}).Value == 0.0);
}

TEST_CASE("Loss is not clamped, so an unworkable layout loses more than its load")
{
	constexpr double Load = 2.0 * CapacityMegawatts;
	constexpr double Distance = 20.0 * ReferenceDistanceMeters;
	const double Loss = LossAt(Load, Distance);
	CHECK(Loss > Load);
	CHECK_NEAR(Loss, ReferenceLossFraction * 2.0 * 20.0 * Load, Tolerance);
}
