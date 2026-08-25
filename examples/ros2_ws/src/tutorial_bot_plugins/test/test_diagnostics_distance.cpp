#include "diagnostics_test_fixture.hpp"

#include <gtest/gtest.h>

namespace tutorial_bot_plugins::test
{
TEST(DiagnosticsDistance, AccumulatesPlanarDistanceFromConsecutiveWorldPoses)
{
  // Given: a bound model has published its initial zero-distance baseline.
  DiagnosticsFixture fixture(true);
  ASSERT_TRUE(fixture.Run(20));

  // When: the real Gazebo user-command surface moves it along two axes.
  ASSERT_TRUE(fixture.SetPose(3.0, 0.0));
  ASSERT_TRUE(fixture.Run(20));
  ASSERT_TRUE(fixture.SetPose(3.0, 4.0));
  ASSERT_TRUE(fixture.Run(20));

  // Then: the plugin publishes the travelled 3 + 4 metres, not displacement.
  const auto distances = fixture.Distances();
  ASSERT_FALSE(distances.empty());
  EXPECT_DOUBLE_EQ(0.0, distances.front());
  EXPECT_NEAR(7.0, distances.back(), 1e-9);
}
}
