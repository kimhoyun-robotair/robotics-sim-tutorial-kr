#include "diagnostics_test_fixture.hpp"

#include <gtest/gtest.h>

#include <algorithm>
#include <string>
#include <vector>

namespace tutorial_bot_plugins::test
{
TEST(DiagnosticsModelLifecycle, RebindsSameNameWithFreshBaselineAfterRemoval)
{
  // Given: diagnostics starts before its configured model exists.
  DiagnosticsFixture fixture(false);
  ASSERT_TRUE(fixture.Run(20));
  EXPECT_EQ(std::vector<std::string>{"WAITING_FOR_MODEL"}, fixture.Statuses());

  // When: the model is spawned, moved, removed, and spawned again by services.
  ASSERT_TRUE(fixture.Spawn());
  ASSERT_TRUE(fixture.Run(20));
  ASSERT_TRUE(fixture.SetPose(2.0, 0.0));
  ASSERT_TRUE(fixture.Run(20));
  const double distanceBeforeRemoval = fixture.Distances().back();
  ASSERT_TRUE(fixture.Remove());
  ASSERT_TRUE(fixture.Run(20));
  const double distanceWhileRemoved = fixture.Distances().back();
  ASSERT_TRUE(fixture.Spawn());
  ASSERT_TRUE(fixture.Run(20));

  // Then: states are truthful, removal freezes distance, and respawn resets it.
  const auto statuses = fixture.Statuses();
  EXPECT_NE(statuses.end(), std::find(statuses.begin(), statuses.end(), "READY"));
  EXPECT_NE(
    statuses.end(), std::find(statuses.begin(), statuses.end(), "MODEL_REMOVED"));
  EXPECT_DOUBLE_EQ(distanceBeforeRemoval, distanceWhileRemoved);
  EXPECT_DOUBLE_EQ(0.0, fixture.Distances().back());
}
}
