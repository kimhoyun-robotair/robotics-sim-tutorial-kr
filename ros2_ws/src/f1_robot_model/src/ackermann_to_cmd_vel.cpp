// Copyright 2026 robotics-sim-tutorial-kr contributors
// SPDX-License-Identifier: Apache-2.0
#include <cmath>
#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "ackermann_msgs/msg/ackermann_drive_stamped.hpp"
#include "geometry_msgs/msg/twist.hpp"

// gazebo_ros_ackermann_drive uses angular.z as a steering angle, then
// multiplies it by sign(linear.x). This is NOT a generic Twist converter.
class AckermannToTwistConverter : public rclcpp::Node
{
public:
  AckermannToTwistConverter() : Node("ackermann_to_twist_converter_node")
  {
    publisher_ = create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);
    subscriber_ = create_subscription<ackermann_msgs::msg::AckermannDriveStamped>(
      "drive", 10, std::bind(&AckermannToTwistConverter::convert, this, std::placeholders::_1));
  }

private:
  void convert(const ackermann_msgs::msg::AckermannDriveStamped::SharedPtr msg)
  {
    geometry_msgs::msg::Twist command;
    if (!std::isfinite(msg->drive.speed) || !std::isfinite(msg->drive.steering_angle)) {
      RCLCPP_WARN(get_logger(), "Non-finite drive command rejected; sending stop");
    } else {
      command.linear.x = msg->drive.speed;
      command.angular.z = msg->drive.steering_angle * std::copysign(1.0, msg->drive.speed);
    }
    publisher_->publish(command);
  }
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
  rclcpp::Subscription<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr subscriber_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<AckermannToTwistConverter>());
  rclcpp::shutdown();
  return 0;
}
