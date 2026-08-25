#ifndef TUTORIAL_BOT_PLUGINS__TEST__DIAGNOSTICS_TEST_FIXTURE_HPP_
#define TUTORIAL_BOT_PLUGINS__TEST__DIAGNOSTICS_TEST_FIXTURE_HPP_

#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/double.pb.h>
#include <gz/msgs/entity.pb.h>
#include <gz/msgs/entity_factory.pb.h>
#include <gz/msgs/pose.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/sim/Server.hh>
#include <gz/sim/ServerConfig.hh>
#include <gz/transport/Node.hh>

#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

namespace tutorial_bot_plugins::test
{
inline constexpr char kWorldPrefix[] = R"(
<sdf version="1.10">
  <world name="diagnostics">
    <physics name="step" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="libTutorialBotDiagnosticsSystem.so"
            name="gz::sim::systems::TutorialBotDiagnostics">
      <model_name>tutorial_bot</model_name>
      <publish_period>0.01</publish_period>
    </plugin>
)";

inline constexpr char kModel[] = R"(
    <model name="tutorial_bot">
      <static>true</static>
      <link name="base_link"/>
    </model>
)";

inline constexpr char kWorldSuffix[] = R"(
  </world>
</sdf>
)";

class DiagnosticsFixture
{
public:
  explicit DiagnosticsFixture(const bool withModel)
  : server_(MakeConfig(withModel))
  {
    node_.Subscribe(
      "/tutorial_bot/diagnostics/status",
      &DiagnosticsFixture::OnStatus, this);
    node_.Subscribe(
      "/tutorial_bot/diagnostics/distance",
      &DiagnosticsFixture::OnDistance, this);
  }

  bool Run(const std::uint64_t iterations)
  {
    return server_.Run(true, iterations, false);
  }

  bool SetPose(const double x, const double y)
  {
    gz::msgs::Pose request;
    request.set_name("tutorial_bot");
    request.mutable_position()->set_x(x);
    request.mutable_position()->set_y(y);
    gz::msgs::Boolean reply;
    bool result = false;
    return node_.Request(
      "/world/diagnostics/set_pose", request, 1000u, reply, result) &&
      result && reply.data();
  }

  bool Spawn()
  {
    gz::msgs::EntityFactory request;
    request.set_sdf(
      "<sdf version='1.10'><model name='tutorial_bot'><static>true</static>"
      "<link name='base_link'/></model></sdf>");
    gz::msgs::Boolean reply;
    bool result = false;
    return node_.Request(
      "/world/diagnostics/create", request, 1000u, reply, result) &&
      result && reply.data();
  }

  bool Remove()
  {
    gz::msgs::Entity request;
    request.set_name("tutorial_bot");
    request.set_type(gz::msgs::Entity::MODEL);
    gz::msgs::Boolean reply;
    bool result = false;
    return node_.Request(
      "/world/diagnostics/remove", request, 1000u, reply, result) &&
      result && reply.data();
  }

  std::vector<std::string> Statuses() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return statuses_;
  }

  std::vector<double> Distances() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return distances_;
  }

private:
  static gz::sim::ServerConfig MakeConfig(const bool withModel)
  {
    gz::sim::ServerConfig config;
    config.SetSdfString(
      std::string(kWorldPrefix) + (withModel ? kModel : "") + kWorldSuffix);
    return config;
  }

  void OnStatus(const gz::msgs::StringMsg & message)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    statuses_.push_back(message.data());
  }

  void OnDistance(const gz::msgs::Double & message)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    distances_.push_back(message.data());
  }

  gz::transport::Node node_;
  gz::sim::Server server_;
  mutable std::mutex mutex_;
  std::vector<std::string> statuses_;
  std::vector<double> distances_;
};
}

#endif
