#ifndef TUTORIAL_BOT_PLUGINS__TEST__DIAGNOSTICS_TEST_FIXTURE_HPP_
#define TUTORIAL_BOT_PLUGINS__TEST__DIAGNOSTICS_TEST_FIXTURE_HPP_

#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/double.pb.h>
#include <gz/msgs/empty.pb.h>
#include <gz/msgs/entity.pb.h>
#include <gz/msgs/entity_factory.pb.h>
#include <gz/msgs/pose.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/sim/Server.hh>
#include <gz/sim/ServerConfig.hh>
#include <gz/transport/Node.hh>

#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstddef>
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
  : enableTopic_(withModel ? "/tutorial_bot/diagnostics/enable" :
      "/unbound_bot/diagnostics/enable"),
    resetService_(withModel ? "/tutorial_bot/diagnostics/reset" :
      "/unbound_bot/diagnostics/reset"),
    server_(MakeConfig(withModel))
  {
    enablePublisher_ =
      node_.Advertise<gz::msgs::Boolean>(enableTopic_);
    node_.Subscribe(
      "/tutorial_bot/diagnostics/status",
      &DiagnosticsFixture::OnStatus, this);
    node_.Subscribe(
      "/tutorial_bot/diagnostics/distance",
      &DiagnosticsFixture::OnDistance, this);
  }

  bool Run(const std::uint64_t iterations)
  {
    if (!server_.Run(true, iterations, false)) {
      return false;
    }
    std::unique_lock<std::mutex> lock(mutex_);
    if (!awaitingResetPublication_) {
      return true;
    }
    const bool published = condition_.wait_for(
      lock, std::chrono::milliseconds(200), [this]() {
        return distances_.size() > resetDistanceCount_ &&
          std::abs(distances_.back()) <= 1e-6;
      });
    awaitingResetPublication_ = !published;
    return true;
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

  bool ControlEndpointsAvailable()
  {
    if (!Run(20) || !enablePublisher_.HasConnections()) {
      return false;
    }
    bool accepted = false;
    return Reset(accepted) && accepted && Run(1);
  }

  bool PublishEnabled(const bool enabled)
  {
    gz::msgs::Boolean message;
    message.set_data(enabled);
    return enablePublisher_.Publish(message);
  }

  bool Reset(bool & accepted)
  {
    gz::msgs::Empty request;
    gz::msgs::Boolean reply;
    bool result = false;
    const bool requested = node_.Request(
      resetService_, request, 200u, reply, result);
    accepted = requested && result && reply.data();
    if (accepted) {
      std::lock_guard<std::mutex> lock(mutex_);
      awaitingResetPublication_ = true;
      resetDistanceCount_ = distances_.size();
    }
    return requested && result;
  }

  bool RunUntilStatus(const std::string & expected)
  {
    for (std::uint64_t iteration = 0; iteration < 1000; ++iteration) {
      if (!Run(1)) {
        return false;
      }
      const auto statuses = Statuses();
      if (!statuses.empty() && statuses.back() == expected) {
        return true;
      }
    }
    return false;
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
    std::string world =
      std::string(kWorldPrefix) + (withModel ? kModel : "") + kWorldSuffix;
    if (!withModel) {
      const auto pluginEnd = world.find("</plugin>");
      world.insert(
        pluginEnd,
        "<enable_topic>/unbound_bot/diagnostics/enable</enable_topic>"
        "<reset_service>/unbound_bot/diagnostics/reset</reset_service>");
    }
    config.SetSdfString(world);
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
    condition_.notify_all();
  }

  std::string enableTopic_;
  std::string resetService_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher enablePublisher_;
  gz::sim::Server server_;
  mutable std::mutex mutex_;
  std::condition_variable condition_;
  std::vector<std::string> statuses_;
  std::vector<double> distances_;
  bool awaitingResetPublication_{false};
  std::size_t resetDistanceCount_{0};
};
}

#endif
