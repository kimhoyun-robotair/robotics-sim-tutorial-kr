#ifndef TUTORIAL_BOT_PLUGINS__TUTORIAL_BOT_DIAGNOSTICS_HPP_
#define TUTORIAL_BOT_PLUGINS__TUTORIAL_BOT_DIAGNOSTICS_HPP_

#include <gz/math/Pose3.hh>
#include <gz/sim/System.hh>
#include <gz/transport/Node.hh>

#include <chrono>
#include <memory>
#include <optional>
#include <string>

namespace gz::sim::systems
{
class TutorialBotDiagnostics final :
  public System,
  public ISystemConfigure,
  public ISystemPostUpdate
{
public:
  void Configure(
    const Entity & entity,
    const std::shared_ptr<const sdf::Element> & sdf,
    EntityComponentManager & ecm,
    EventManager & eventManager) override;

  void PostUpdate(
    const UpdateInfo & info,
    const EntityComponentManager & ecm) override;

private:
  enum class State
  {
    WaitingForModel,
    Ready,
    ModelRemoved,
    InvalidConfig
  };

  void BindOrWait(const EntityComponentManager & ecm);
  void Publish(const std::chrono::steady_clock::duration & simTime);
  void SetState(State state);
  static const char * StateName(State state);

  std::string modelName_{"tutorial_bot"};
  std::string distanceTopic_{"/tutorial_bot/diagnostics/distance"};
  std::string statusTopic_{"/tutorial_bot/diagnostics/status"};
  std::chrono::steady_clock::duration publishPeriod_{std::chrono::milliseconds(100)};
  Entity modelEntity_{kNullEntity};
  std::optional<gz::math::Pose3d> previousPose_;
  double distance_{0.0};
  State state_{State::WaitingForModel};
  bool stateChanged_{true};
  std::optional<std::chrono::steady_clock::duration> lastPublishTime_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher distancePublisher_;
  gz::transport::Node::Publisher statusPublisher_;
};
}

#endif
