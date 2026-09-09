#!/usr/bin/env python3
"""Clamp Twist commands and publish zero after a wall-time timeout.

Route the simulator subscriber to /cmd_vel_safe. Keep this node running in
an external ROS Jazzy process. A simulator-side timeout is still required
to handle failure of this relay process itself.
"""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions


class SafeCmdVel(Node):
    def __init__(self):
        super().__init__("course_safe_cmd_vel")
        self.declare_parameter("input_topic", "/cmd_vel")
        self.declare_parameter("output_topic", "/cmd_vel_safe")
        self.publisher = self.create_publisher(Twist, self.get_parameter("output_topic").value, 10)
        self.subscription = self.create_subscription(
            Twist, self.get_parameter("input_topic").value, self.on_command, 10
        )
        self.command = Twist()
        self.received_at = None
        self.shutting_down = False
        self.steady_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.timer = self.create_timer(0.05, self.on_timer, clock=self.steady_clock)

    def on_command(self, message):
        if self.shutting_down:
            return
        values = (message.linear.x, message.linear.y, message.linear.z,
                  message.angular.x, message.angular.y, message.angular.z)
        command = Twist()
        if all(math.isfinite(value) for value in values):
            command.linear.x = max(-0.15, min(0.15, message.linear.x))
            command.angular.z = max(-0.5, min(0.5, message.angular.z))
        else:
            self.get_logger().error("Non-finite Twist rejected; applying zero command")
        self.command = command
        self.received_at = time.monotonic()

    def on_timer(self):
        fresh = not self.shutting_down and self.received_at is not None
        fresh = fresh and time.monotonic() - self.received_at < 0.25
        self.publisher.publish(self.command if fresh else Twist())


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = SafeCmdVel()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutting_down = True
        node.timer.cancel()
        node.destroy_subscription(node.subscription)
        node.command = Twist()
        node.received_at = None
        for _ in range(5):
            node.publisher.publish(Twist())
            rclpy.spin_once(node, timeout_sec=0.05)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
