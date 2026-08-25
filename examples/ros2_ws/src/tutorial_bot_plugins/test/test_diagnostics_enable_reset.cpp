#include "diagnostics_test_fixture.hpp"

#include <gtest/gtest.h>

#include <atomic>
#include <cmath>
#include <cstddef>
#include <thread>

namespace tutorial_bot_plugins::test
{
#if defined(DIAGNOSTICS_ENABLE_RESET)
TEST(DiagnosticsEnableReset, AppliesControlsAtUpdateBoundaryWithoutDistanceJump)
{
  // Given: a bound plugin with working real Transport control endpoints.
  DiagnosticsFixture fixture(true);
  ASSERT_TRUE(fixture.ControlEndpointsAvailable())
    << "enable/reset endpoint unavailable";
  ASSERT_TRUE(fixture.SetPose(1.0, 0.0));
  ASSERT_TRUE(fixture.Run(20));
  ASSERT_NEAR(1.0, fixture.Distances().back(), 1e-6);

  // When: diagnostics is disabled, moved, re-enabled, moved, and reset.
  ASSERT_TRUE(fixture.PublishEnabled(false));
  ASSERT_TRUE(fixture.RunUntilStatus("DISABLED"));
  const double disabledBaseline = fixture.Distances().back();
  ASSERT_TRUE(fixture.SetPose(5.0, 0.0));
  ASSERT_TRUE(fixture.Run(20));
  const double disabledDistance = fixture.Distances().back();
  ASSERT_TRUE(fixture.PublishEnabled(true));
  ASSERT_TRUE(fixture.RunUntilStatus("READY"));
  const double reenabledDistance = fixture.Distances().back();
  ASSERT_TRUE(fixture.SetPose(6.0, 0.0));
  ASSERT_TRUE(fixture.Run(20));
  const double resumedDistance = fixture.Distances().back();
  bool resetAccepted = false;
  ASSERT_TRUE(fixture.Reset(resetAccepted));
  ASSERT_TRUE(resetAccepted);
  ASSERT_TRUE(fixture.Run(1));

  // Then: disabled motion does not drift or jump, and bound reset is zero.
  EXPECT_NEAR(disabledBaseline, disabledDistance, 1e-6);
  EXPECT_NEAR(disabledBaseline, reenabledDistance, 1e-6);
  EXPECT_NEAR(disabledBaseline + 1.0, resumedDistance, 1e-6);
  EXPECT_NEAR(0.0, fixture.Distances().back(), 1e-6);

  DiagnosticsFixture unbound(false);
  ASSERT_TRUE(unbound.Run(20));
  bool unboundAccepted = true;
  ASSERT_TRUE(unbound.Reset(unboundAccepted));
  EXPECT_FALSE(unboundAccepted);
  EXPECT_EQ("WAITING_FOR_MODEL", unbound.Statuses().back());
}
#endif

#if defined(DIAGNOSTICS_ENABLE_RESET_CONCURRENCY)
TEST(DiagnosticsEnableResetConcurrency, HandlesOneHundredCrossThreadCycles)
{
  // Given: a bound plugin and real Transport endpoints on worker threads.
  DiagnosticsFixture fixture(true);
  ASSERT_TRUE(fixture.ControlEndpointsAvailable())
    << "enable/reset endpoint unavailable";
  std::atomic<bool> complete{false};
  std::atomic<std::size_t> acceptedResets{0};

  // When: Transport callbacks enqueue 100 enable/reset cycles while updates run.
  std::thread callbacks([&fixture, &complete, &acceptedResets]() {
    for (std::size_t cycle = 0; cycle < 100; ++cycle) {
      if (!fixture.PublishEnabled(cycle % 2 == 0)) {
        continue;
      }
      bool accepted = false;
      if (fixture.Reset(accepted) && accepted) {
        ++acceptedResets;
      }
    }
    complete = true;
  });
  bool updatesSucceeded = true;
  while (!complete) {
    if (!fixture.Run(10)) {
      updatesSucceeded = false;
      break;
    }
  }
  callbacks.join();
  ASSERT_TRUE(updatesSucceeded);
  ASSERT_TRUE(fixture.Run(20));

  // Then: every bounded request completes and shared state stays finite.
  EXPECT_EQ(100u, acceptedResets.load());
  ASSERT_FALSE(fixture.Distances().empty());
  EXPECT_TRUE(std::isfinite(fixture.Distances().back()));
}
#endif
}
