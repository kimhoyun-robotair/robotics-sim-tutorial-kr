// Copyright 2026 gazebo-sim-tutorial-kr contributors
// SPDX-License-Identifier: Apache-2.0

#include "gazebo_tutorial_plugins/path_recorder_config.hpp"

#include <gtest/gtest.h>

#include <chrono>
#include <limits>

using gazebo_tutorial_plugins::PathRecorderConfig;
using gazebo_tutorial_plugins::SimulationRateGate;

TEST(PathRecorderConfig, DefaultsAreValid)
{
  const PathRecorderConfig config;
  EXPECT_TRUE(config.IsValid());
  EXPECT_EQ(config.PublishPeriod(), std::chrono::milliseconds{100});
}

TEST(PathRecorderConfig, RejectsValuesThatCannotProduceABoundedPath)
{
  PathRecorderConfig config;

  config.update_rate = 0.0;
  EXPECT_FALSE(config.IsValid());

  config.update_rate = std::numeric_limits<double>::quiet_NaN();
  EXPECT_FALSE(config.IsValid());

  config.update_rate = 10.0;
  config.topic.clear();
  EXPECT_FALSE(config.IsValid());

  config.topic = "ground_truth_path";
  config.frame.clear();
  EXPECT_FALSE(config.IsValid());

  config.frame = "world";
  config.max_points = 0U;
  EXPECT_FALSE(config.IsValid());
}

TEST(PathRecorderConfig, ClampsExtremeValidRatesWithoutOverflow)
{
  PathRecorderConfig config;

  config.update_rate = std::numeric_limits<double>::max();
  EXPECT_TRUE(config.IsValid());
  EXPECT_EQ(config.PublishPeriod(), std::chrono::nanoseconds{1});

  config.update_rate = std::numeric_limits<double>::min();
  EXPECT_TRUE(config.IsValid());
  EXPECT_EQ(config.PublishPeriod(), std::chrono::nanoseconds::max());
}

TEST(SimulationRateGate, UsesSimulationTimeInsteadOfCallbackCount)
{
  SimulationRateGate gate(std::chrono::milliseconds{100});

  EXPECT_TRUE(gate.ShouldPublish(std::chrono::milliseconds{0}));
  EXPECT_FALSE(gate.ShouldPublish(std::chrono::milliseconds{99}));
  EXPECT_TRUE(gate.ShouldPublish(std::chrono::milliseconds{100}));
  EXPECT_FALSE(gate.ShouldPublish(std::chrono::milliseconds{150}));
  EXPECT_TRUE(gate.ShouldPublish(std::chrono::milliseconds{200}));
}

TEST(SimulationRateGate, PublishesImmediatelyAfterSimulationTimeRewinds)
{
  SimulationRateGate gate(std::chrono::seconds{1});

  EXPECT_TRUE(gate.ShouldPublish(std::chrono::seconds{10}));
  EXPECT_TRUE(gate.ShouldPublish(std::chrono::seconds{0}));
  EXPECT_FALSE(gate.ShouldPublish(std::chrono::milliseconds{999}));
  EXPECT_TRUE(gate.ShouldPublish(std::chrono::seconds{1}));
}
