// Copyright 2026 gazebo-sim-tutorial-kr contributors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "gazebo_tutorial_plugins/path_recorder_config.hpp"

#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/common/Time.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/Model.hh>
#include <gazebo_ros/node.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav_msgs/msg/path.hpp>
#include <rclcpp/qos.hpp>
#include <sdf/sdf.hh>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <exception>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>

namespace gazebo
{

/// Event callback이 플러그인 객체보다 오래 살아도 안전하도록 상태를 분리한다.
struct GroundTruthPathState
{
  GroundTruthPathState()
  : rate_gate(std::chrono::milliseconds{100})
  {
  }

  std::atomic<bool> active{false};
  std::mutex mutex;
  physics::ModelPtr model;
  gazebo_ros::Node::SharedPtr ros_node;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr path_publisher;
  gazebo_tutorial_plugins::PathRecorderConfig config;
  gazebo_tutorial_plugins::SimulationRateGate rate_gate;
  nav_msgs::msg::Path path;
  std::optional<std::chrono::nanoseconds> previous_simulation_time;
};

/// Gazebo가 계산한 모델의 world pose를 ROS 2 Path로 기록하는 교육용 ModelPlugin.
class GroundTruthPathPlugin final : public ModelPlugin
{
public:
  GroundTruthPathPlugin()
  : state_(std::make_shared<GroundTruthPathState>())
  {
  }

  ~GroundTruthPathPlugin() override
  {
    // callback은 this가 아니라 weak_ptr<State>를 캡처한다. 이미 시작된 callback은
    // shared_ptr로 상태 수명을 연장하고, 새 callback은 weak_ptr lock에 실패한다.
    auto state = std::move(state_);
    if (!state) {
      return;
    }

    state->active.store(false, std::memory_order_release);
    update_connection_.reset();

    std::lock_guard<std::mutex> lock(state->mutex);
    state->path_publisher.reset();
    state->ros_node.reset();
    state->model.reset();
  }

  void Load(physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    if (!model || !sdf) {
      gzerr << "[GroundTruthPathPlugin] model 또는 SDF 포인터가 비어 있습니다.\n";
      return;
    }

    gazebo_tutorial_plugins::PathRecorderConfig config;
    try {
      config = ReadConfig(sdf);
    } catch (const std::exception & error) {
      gzerr << "[GroundTruthPathPlugin] SDF 파라미터를 읽지 못했습니다: "
            << error.what() << "\n";
      return;
    }
    if (!config.IsValid()) {
      gzerr << "[GroundTruthPathPlugin] 잘못된 설정입니다: update_rate="
            << config.update_rate << ", topic='" << config.topic
            << "', frame='" << config.frame << "', max_points="
            << config.max_points << ". 플러그인을 시작하지 않습니다.\n";
      return;
    }

    try {
      auto ros_node = gazebo_ros::Node::Get(sdf);
      if (!ros_node) {
        gzerr << "[GroundTruthPathPlugin] gazebo_ros::Node를 만들지 못했습니다. "
              << "같은 namespace에 중복된 plugin name이 있는지 확인하세요.\n";
        return;
      }
      auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();
      auto publisher = ros_node->create_publisher<nav_msgs::msg::Path>(config.topic, qos);
      const std::string model_name = model->GetName();
      const std::string resolved_topic = publisher->get_topic_name();
      auto state = state_;

      {
        std::lock_guard<std::mutex> lock(state->mutex);
        state->config = std::move(config);
        state->rate_gate.SetPeriod(state->config.PublishPeriod());
        state->model = std::move(model);
        state->ros_node = std::move(ros_node);
        state->path_publisher = std::move(publisher);
        state->path.header.frame_id = state->config.frame;
        state->path.poses.reserve(state->config.max_points);
        state->previous_simulation_time.reset();
      }

      state->active.store(true, std::memory_order_release);
      const std::weak_ptr<GroundTruthPathState> weak_state{state};
      update_connection_ = event::Events::ConnectWorldUpdateBegin(
        [weak_state](const common::UpdateInfo & info) {
          if (const auto locked_state = weak_state.lock()) {
            GroundTruthPathPlugin::OnUpdate(*locked_state, info);
          }
        });
      if (!update_connection_) {
        throw std::runtime_error("WorldUpdateBegin event 연결을 만들지 못했습니다.");
      }

      RCLCPP_INFO(
        state->ros_node->get_logger(),
        "ground-truth path 시작: model='%s', topic='%s', frame='%s', "
        "update_rate=%.3f Hz, max_points=%zu",
        model_name.c_str(), resolved_topic.c_str(), state->config.frame.c_str(),
        state->config.update_rate, state->config.max_points);
    } catch (const std::exception & error) {
      const auto state = state_;
      state->active.store(false, std::memory_order_release);
      update_connection_.reset();
      std::lock_guard<std::mutex> lock(state->mutex);
      state->path_publisher.reset();
      state->ros_node.reset();
      state->model.reset();
      state->path.poses.clear();
      gzerr << "[GroundTruthPathPlugin] 초기화 실패: " << error.what() << "\n";
    }
  }

private:
  static gazebo_tutorial_plugins::PathRecorderConfig ReadConfig(
    const sdf::ElementPtr & sdf)
  {
    gazebo_tutorial_plugins::PathRecorderConfig config;

    if (sdf->HasElement("update_rate")) {
      config.update_rate = sdf->Get<double>("update_rate");
    }
    if (sdf->HasElement("topic")) {
      config.topic = sdf->Get<std::string>("topic");
    }
    if (sdf->HasElement("frame")) {
      config.frame = sdf->Get<std::string>("frame");
    }
    if (sdf->HasElement("max_points")) {
      const int max_points = sdf->Get<int>("max_points");
      config.max_points = max_points > 0 ? static_cast<std::size_t>(max_points) : 0U;
    }

    return config;
  }

  static std::chrono::nanoseconds ToNanoseconds(const common::Time & time) noexcept
  {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::seconds{time.sec} + std::chrono::nanoseconds{time.nsec});
  }

  static void OnUpdate(GroundTruthPathState & state, const common::UpdateInfo & info)
  {
    if (!state.active.load(std::memory_order_acquire)) {
      return;
    }

    std::lock_guard<std::mutex> lock(state.mutex);
    // destructor가 lock을 먼저 얻은 경우를 위해 보호 영역 안에서 다시 확인한다.
    if (!state.active.load(std::memory_order_relaxed) ||
      !state.model || !state.path_publisher)
    {
      return;
    }

    const auto simulation_time = ToNanoseconds(info.simTime);
    if (state.previous_simulation_time &&
      simulation_time < *state.previous_simulation_time)
    {
      // simulation time reset 뒤에는 서로 다른 시간축의 점을 섞지 않는다.
      state.path.poses.clear();
      state.rate_gate.Reset();
      RCLCPP_INFO(
        state.ros_node->get_logger(), "simulation time reset 감지: 경로를 초기화합니다.");
    }
    state.previous_simulation_time = simulation_time;

    if (!state.rate_gate.ShouldPublish(simulation_time)) {
      return;
    }

    const auto world_pose = state.model->WorldPose();
    geometry_msgs::msg::PoseStamped pose;
    pose.header.frame_id = state.config.frame;
    pose.header.stamp.sec = static_cast<std::int32_t>(info.simTime.sec);
    pose.header.stamp.nanosec = static_cast<std::uint32_t>(info.simTime.nsec);
    pose.pose.position.x = world_pose.Pos().X();
    pose.pose.position.y = world_pose.Pos().Y();
    pose.pose.position.z = world_pose.Pos().Z();
    pose.pose.orientation.x = world_pose.Rot().X();
    pose.pose.orientation.y = world_pose.Rot().Y();
    pose.pose.orientation.z = world_pose.Rot().Z();
    pose.pose.orientation.w = world_pose.Rot().W();

    if (state.path.poses.size() >= state.config.max_points) {
      state.path.poses.erase(state.path.poses.begin());
    }
    state.path.poses.emplace_back(std::move(pose));
    state.path.header.frame_id = state.config.frame;
    state.path.header.stamp = state.path.poses.back().header.stamp;
    state.path_publisher->publish(state.path);
  }

  event::ConnectionPtr update_connection_;
  std::shared_ptr<GroundTruthPathState> state_;
};

GZ_REGISTER_MODEL_PLUGIN(GroundTruthPathPlugin)

}  // namespace gazebo
