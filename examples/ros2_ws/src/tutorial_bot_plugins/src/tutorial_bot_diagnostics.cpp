#include "tutorial_bot_plugins/tutorial_bot_diagnostics.hpp"

#include <gz/msgs/double.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <sdf/Element.hh>

#include <cmath>
#include <string>

namespace gz::sim::systems
{
void TutorialBotDiagnostics::Configure(
  const Entity &,
  const std::shared_ptr<const sdf::Element> & sdf,
  EntityComponentManager &,
  EventManager &)
{
  if (sdf->HasElement("model_name")) {
    modelName_ = sdf->Get<std::string>("model_name");
  }
  if (sdf->HasElement("distance_topic")) {
    distanceTopic_ = sdf->Get<std::string>("distance_topic");
  }
  if (sdf->HasElement("status_topic")) {
    statusTopic_ = sdf->Get<std::string>("status_topic");
  }

  const double periodSeconds =
    sdf->Get<double>("publish_period", 0.1).first;
  if (modelName_.empty() || !std::isfinite(periodSeconds) || periodSeconds <= 0.0) {
    SetState(State::InvalidConfig);
    statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
    return;
  }

  publishPeriod_ = std::chrono::duration_cast<std::chrono::steady_clock::duration>(
    std::chrono::duration<double>(periodSeconds));
  distancePublisher_ = node_.Advertise<gz::msgs::Double>(distanceTopic_);
  statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
  stateChanged_ = false;
  lastPublishTime_ = std::chrono::steady_clock::duration::zero();
}

void TutorialBotDiagnostics::PostUpdate(
  const UpdateInfo & info,
  const EntityComponentManager & ecm)
{
  if (state_ == State::InvalidConfig) {
    Publish(info.simTime);
    return;
  }

  if (modelEntity_ != kNullEntity && !ecm.HasEntity(modelEntity_)) {
    modelEntity_ = kNullEntity;
    previousPose_.reset();
    SetState(State::ModelRemoved);
  } else if (modelEntity_ == kNullEntity) {
    BindOrWait(ecm);
  }

  if (modelEntity_ != kNullEntity) {
    const auto poseComponent = ecm.Component<components::Pose>(modelEntity_);
    if (poseComponent != nullptr) {
      const auto pose = worldPose(modelEntity_, ecm);
      const bool poseIsFinite =
        std::isfinite(pose.Pos().X()) && std::isfinite(pose.Pos().Y());
      if (poseIsFinite && previousPose_.has_value()) {
        distance_ += std::hypot(
          pose.Pos().X() - previousPose_->Pos().X(),
          pose.Pos().Y() - previousPose_->Pos().Y());
      }
      if (poseIsFinite) {
        previousPose_ = pose;
        SetState(State::Ready);
      }
    }
  }

  Publish(info.simTime);
}

void TutorialBotDiagnostics::BindOrWait(const EntityComponentManager & ecm)
{
  const Entity candidate = ecm.EntityByComponents(
    components::Model(), components::Name(modelName_));
  if (candidate == kNullEntity) {
    if (state_ != State::ModelRemoved) {
      SetState(State::WaitingForModel);
    }
    return;
  }

  modelEntity_ = candidate;
  previousPose_.reset();
  distance_ = 0.0;
}

void TutorialBotDiagnostics::Publish(
  const std::chrono::steady_clock::duration & simTime)
{
  const bool periodElapsed = !lastPublishTime_.has_value() ||
    simTime < *lastPublishTime_ || simTime - *lastPublishTime_ > publishPeriod_;
  if (!stateChanged_ && !periodElapsed) {
    return;
  }

  gz::msgs::StringMsg status;
  status.set_data(StateName(state_));
  statusPublisher_.Publish(status);
  if (state_ != State::InvalidConfig) {
    gz::msgs::Double distance;
    distance.set_data(distance_);
    distancePublisher_.Publish(distance);
  }
  stateChanged_ = false;
  lastPublishTime_ = simTime;
}

void TutorialBotDiagnostics::SetState(const State state)
{
  if (state_ != state) {
    state_ = state;
    stateChanged_ = true;
  }
}

const char * TutorialBotDiagnostics::StateName(const State state)
{
  switch (state) {
    case State::WaitingForModel:
      return "WAITING_FOR_MODEL";
    case State::Ready:
      return "READY";
    case State::ModelRemoved:
      return "MODEL_REMOVED";
    case State::InvalidConfig:
      return "INVALID_CONFIG";
  }
  return "INVALID_CONFIG";
}
}

GZ_ADD_PLUGIN(
  gz::sim::systems::TutorialBotDiagnostics,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(
  gz::sim::systems::TutorialBotDiagnostics,
  "gz::sim::systems::TutorialBotDiagnostics")
