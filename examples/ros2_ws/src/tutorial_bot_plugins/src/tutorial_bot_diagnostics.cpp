#include "tutorial_bot_plugins/tutorial_bot_diagnostics.hpp"

#include <gz/common/Console.hh>
#include <gz/msgs/double.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/sim/Conversions.hh>
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
  if (sdf->HasElement("enable_topic")) {
    enableTopic_ = sdf->Get<std::string>("enable_topic");
  }
  if (sdf->HasElement("reset_service")) {
    resetService_ = sdf->Get<std::string>("reset_service");
  }
  if (sdf->HasElement("world_stats_topic")) {
    worldStatsTopic_ = sdf->Get<std::string>("world_stats_topic");
  }
  finalStatsIteration_ = sdf->Get<std::uint64_t>("final_stats_iteration", 0u).first;

  const double periodSeconds =
    sdf->Get<double>("publish_period", 0.1).first;
  if (modelName_.empty() || !std::isfinite(periodSeconds) || periodSeconds <= 0.0) {
    SetState(State::InvalidConfig);
    statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
    gzerr << "TutorialBotDiagnostics configuration state=INVALID_CONFIG"
          << " model_name=" << modelName_
          << " publish_period=" << periodSeconds << std::endl;
    return;
  }

  publishPeriod_ = std::chrono::duration_cast<std::chrono::steady_clock::duration>(
    std::chrono::duration<double>(periodSeconds));
  distancePublisher_ = node_.Advertise<gz::msgs::Double>(distanceTopic_);
  statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
  if (!worldStatsTopic_.empty() && finalStatsIteration_ > 0u) {
    worldStatsPublisher_ =
      node_.Advertise<gz::msgs::WorldStatistics>(worldStatsTopic_);
  }
  node_.Subscribe(enableTopic_, &TutorialBotDiagnostics::OnEnable, this);
  node_.Advertise(
    resetService_, &TutorialBotDiagnostics::OnReset, this);
  stateChanged_ = false;
  lastPublishTime_ = std::chrono::steady_clock::duration::zero();
  gzerr << "TutorialBotDiagnostics configured"
        << " model_name=" << modelName_
        << " publish_period=" << periodSeconds
        << " distance_topic=" << distanceTopic_
        << " status_topic=" << statusTopic_
        << " world_stats_topic=" << worldStatsTopic_
        << " final_stats_iteration=" << finalStatsIteration_ << std::endl;
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

  ApplyPendingCommands(modelEntity_ != kNullEntity);

  if (modelEntity_ != kNullEntity) {
    const auto poseComponent = ecm.Component<components::Pose>(modelEntity_);
    if (poseComponent != nullptr) {
      const auto pose = worldPose(modelEntity_, ecm);
      const bool poseIsFinite =
        std::isfinite(pose.Pos().X()) && std::isfinite(pose.Pos().Y());
      if (enabled_ && poseIsFinite && previousPose_.has_value()) {
        distance_ += std::hypot(
          pose.Pos().X() - previousPose_->Pos().X(),
          pose.Pos().Y() - previousPose_->Pos().Y());
      }
      if (enabled_ && poseIsFinite) {
        previousPose_ = pose;
        SetState(State::Ready);
      } else if (!enabled_) {
        previousPose_.reset();
        SetState(State::Disabled);
      }
    }
  }

  Publish(info.simTime);
  if (worldStatsPublisher_ && info.iterations == finalStatsIteration_) {
    worldStatsPublisher_.Publish(gz::sim::convert<gz::msgs::WorldStatistics>(info));
  }
}

void TutorialBotDiagnostics::ApplyPendingCommands(const bool modelBound)
{
  std::optional<bool> enable;
  bool reset = false;
  {
    std::lock_guard<std::mutex> lock(commandMutex_);
    resetBound_ = modelBound;
    enable = pendingEnable_;
    reset = pendingReset_;
    pendingEnable_.reset();
    pendingReset_ = false;
  }

  if (enable.has_value() && enabled_ != *enable) {
    enabled_ = *enable;
    previousPose_.reset();
    stateChanged_ = true;
  }
  if (reset) {
    distance_ = 0.0;
    previousPose_.reset();
    stateChanged_ = true;
  }
}

void TutorialBotDiagnostics::OnEnable(const gz::msgs::Boolean & message)
{
  std::lock_guard<std::mutex> lock(commandMutex_);
  pendingEnable_ = message.data();
}

bool TutorialBotDiagnostics::OnReset(
  const gz::msgs::Empty &, gz::msgs::Boolean & response)
{
  std::lock_guard<std::mutex> lock(commandMutex_);
  response.set_data(resetBound_);
  if (resetBound_) {
    pendingReset_ = true;
  }
  return true;
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
    gzerr << "TutorialBotDiagnostics state_transition"
          << " model_name=" << modelName_
          << " from=" << StateName(state_)
          << " to=" << StateName(state) << std::endl;
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
    case State::Disabled:
      return "DISABLED";
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
