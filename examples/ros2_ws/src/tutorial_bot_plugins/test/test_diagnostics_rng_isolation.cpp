#include "tutorial_bot_plugins/tutorial_bot_diagnostics.hpp"

#include <gtest/gtest.h>

#include <gz/math/Rand.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/EventManager.hh>
#include <sdf/Root.hh>
#include <sdf/World.hh>

TEST(DiagnosticsRngIsolation, ConfigurePreservesGazeboGlobalRandomSequence)
{
  // Given: a known process-global RNG sequence and a directly parsed plugin.
  constexpr unsigned int kControlSeed = 8243u;
  gz::math::Rand::Seed(kControlSeed);
  const double expectedNext = gz::math::Rand::DblUniform();
  gz::math::Rand::Seed(kControlSeed);
  sdf::Root root;
  const sdf::Errors errors = root.LoadSdfString(R"(
    <sdf version="1.10">
      <world name="rng_isolation">
        <plugin filename="libTutorialBotDiagnosticsSystem.so"
                name="gz::sim::systems::TutorialBotDiagnostics">
          <model_name>tutorial_bot</model_name>
          <publish_period>0.1</publish_period>
          <deterministic_seed>17</deterministic_seed>
        </plugin>
      </world>
    </sdf>
  )");
  ASSERT_TRUE(errors.empty());
  ASSERT_NE(nullptr, root.WorldByIndex(0));
  ASSERT_EQ(1u, root.WorldByIndex(0)->Plugins().size());
  const auto pluginElement = root.WorldByIndex(0)->Plugins().front().Element();
  ASSERT_NE(nullptr, pluginElement);
  gz::sim::systems::TutorialBotDiagnostics diagnostics;
  gz::sim::EntityComponentManager ecm;
  gz::sim::EventManager events;

  // When: Configure runs without any random behavior to initialize.
  diagnostics.Configure(gz::sim::kNullEntity, pluginElement, ecm, events);

  // Then: the next process-global random value remains unchanged.
  EXPECT_DOUBLE_EQ(expectedNext, gz::math::Rand::DblUniform());
}
