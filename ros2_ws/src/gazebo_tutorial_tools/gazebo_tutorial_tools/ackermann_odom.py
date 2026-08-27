"""Integrate Ackermann wheel encoders into planar odometry."""

import math
from typing import Dict, Optional

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster

from gazebo_tutorial_tools.ackermann_math import (
    bicycle_increment,
    equivalent_center_steering_angle,
    normalized_angle,
    shortest_angular_delta,
)


def _stamp_to_nanoseconds(stamp) -> int:
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


class AckermannOdom(Node):
    """Publish wheel odometry from rear encoders and front steering joints."""

    def __init__(self) -> None:
        super().__init__('ackermann_odom')

        self.declare_parameter('joint_states_topic', '/joint_states')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('rear_left_joint', 'rear_left_wheel_joint')
        self.declare_parameter('rear_right_joint', 'rear_right_wheel_joint')
        self.declare_parameter('front_left_steering_joint', 'front_left_steering_joint')
        self.declare_parameter('front_right_steering_joint', 'front_right_steering_joint')
        self.declare_parameter('wheel_radius', 0.16)
        self.declare_parameter('wheelbase', 0.56)
        self.declare_parameter('max_wheel_delta', 2.0)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('covariance_x', 0.002)
        self.declare_parameter('covariance_y', 0.01)
        self.declare_parameter('covariance_yaw', 0.02)

        self._joint_states_topic = str(
            self.get_parameter('joint_states_topic').value
        )
        self._odom_topic = str(self.get_parameter('odom_topic').value)
        self._odom_frame = str(self.get_parameter('odom_frame').value)
        self._base_frame = str(self.get_parameter('base_frame').value)
        self._rear_left_joint = str(self.get_parameter('rear_left_joint').value)
        self._rear_right_joint = str(self.get_parameter('rear_right_joint').value)
        self._front_left_steering_joint = str(
            self.get_parameter('front_left_steering_joint').value
        )
        self._front_right_steering_joint = str(
            self.get_parameter('front_right_steering_joint').value
        )
        self._wheel_radius = float(self.get_parameter('wheel_radius').value)
        self._wheelbase = float(self.get_parameter('wheelbase').value)
        self._max_wheel_delta = float(
            self.get_parameter('max_wheel_delta').value
        )
        self._publish_tf = bool(self.get_parameter('publish_tf').value)
        self._covariance_x = float(self.get_parameter('covariance_x').value)
        self._covariance_y = float(self.get_parameter('covariance_y').value)
        self._covariance_yaw = float(
            self.get_parameter('covariance_yaw').value
        )

        if self._wheel_radius <= 0.0:
            raise ValueError('wheel_radius must be greater than zero')
        if self._wheelbase <= 0.0:
            raise ValueError('wheelbase must be greater than zero')
        if not 0.0 < self._max_wheel_delta <= math.pi:
            raise ValueError('max_wheel_delta must be in (0, pi]')

        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0
        self._previous_left: Optional[float] = None
        self._previous_right: Optional[float] = None
        self._last_stamp_ns: Optional[int] = None
        self._reported_missing_joints = False

        input_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=20,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        output_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self._publisher = self.create_publisher(
            Odometry,
            self._odom_topic,
            output_qos,
        )
        self._tf_broadcaster = TransformBroadcaster(self)
        self._subscription = self.create_subscription(
            JointState,
            self._joint_states_topic,
            self._joint_state_callback,
            input_qos,
        )

        self.get_logger().info(
            f'integrating {self._joint_states_topic} -> {self._odom_topic}; '
            f'radius={self._wheel_radius:.3f} m, '
            f'wheelbase={self._wheelbase:.3f} m'
        )

    @property
    def _required_joints(self):
        return (
            self._rear_left_joint,
            self._rear_right_joint,
            self._front_left_steering_joint,
            self._front_right_steering_joint,
        )

    def _reset(self, left: float, right: float, stamp_ns: int) -> None:
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0
        self._previous_left = left
        self._previous_right = right
        self._last_stamp_ns = stamp_ns

    def _joint_state_callback(self, message: JointState) -> None:
        positions: Dict[str, float] = dict(zip(message.name, message.position))
        missing = [name for name in self._required_joints if name not in positions]
        if missing:
            if not self._reported_missing_joints:
                self.get_logger().warning(
                    'waiting for required joints in /joint_states: '
                    + ', '.join(missing)
                )
                self._reported_missing_joints = True
            return
        self._reported_missing_joints = False

        left = positions[self._rear_left_joint]
        right = positions[self._rear_right_joint]
        steering = equivalent_center_steering_angle(
            positions[self._front_left_steering_joint],
            positions[self._front_right_steering_joint],
        )

        stamp = message.header.stamp
        if stamp.sec == 0 and stamp.nanosec == 0:
            stamp = self.get_clock().now().to_msg()
        stamp_ns = _stamp_to_nanoseconds(stamp)

        if self._previous_left is None or self._previous_right is None:
            self._reset(left, right, stamp_ns)
            self._publish(stamp, 0.0, 0.0)
            return

        if self._last_stamp_ns is not None and stamp_ns < self._last_stamp_ns:
            self.get_logger().warning(
                'simulation time moved backwards; resetting Ackermann odometry'
            )
            self._reset(left, right, stamp_ns)
            self._publish(stamp, 0.0, 0.0)
            return
        if self._last_stamp_ns is not None and stamp_ns == self._last_stamp_ns:
            return

        delta_left = shortest_angular_delta(self._previous_left, left)
        delta_right = shortest_angular_delta(self._previous_right, right)
        if (
            abs(delta_left) > self._max_wheel_delta
            or abs(delta_right) > self._max_wheel_delta
        ):
            self.get_logger().warning(
                'wheel position jumped beyond max_wheel_delta; '
                'resetting Ackermann odometry'
            )
            self._reset(left, right, stamp_ns)
            self._publish(stamp, 0.0, 0.0)
            return

        distance = 0.5 * (delta_left + delta_right) * self._wheel_radius
        yaw_delta = bicycle_increment(distance, steering, self._wheelbase)
        heading_midpoint = self._yaw + 0.5 * yaw_delta
        self._x += distance * math.cos(heading_midpoint)
        self._y += distance * math.sin(heading_midpoint)
        self._yaw = normalized_angle(self._yaw + yaw_delta)

        dt = (stamp_ns - self._last_stamp_ns) / 1_000_000_000.0
        linear_velocity = distance / dt
        angular_velocity = yaw_delta / dt

        self._previous_left = left
        self._previous_right = right
        self._last_stamp_ns = stamp_ns
        self._publish(stamp, linear_velocity, angular_velocity)

    def _publish(self, stamp, linear_velocity: float, angular_velocity: float) -> None:
        half_yaw = 0.5 * self._yaw
        quaternion_z = math.sin(half_yaw)
        quaternion_w = math.cos(half_yaw)

        odometry = Odometry()
        odometry.header.stamp = stamp
        odometry.header.frame_id = self._odom_frame
        odometry.child_frame_id = self._base_frame
        odometry.pose.pose.position.x = self._x
        odometry.pose.pose.position.y = self._y
        odometry.pose.pose.orientation.z = quaternion_z
        odometry.pose.pose.orientation.w = quaternion_w
        odometry.twist.twist.linear.x = linear_velocity
        odometry.twist.twist.angular.z = angular_velocity
        odometry.pose.covariance[0] = self._covariance_x
        odometry.pose.covariance[7] = self._covariance_y
        odometry.pose.covariance[14] = 1.0e6
        odometry.pose.covariance[21] = 1.0e6
        odometry.pose.covariance[28] = 1.0e6
        odometry.pose.covariance[35] = self._covariance_yaw
        odometry.twist.covariance = list(odometry.pose.covariance)
        self._publisher.publish(odometry)

        if self._publish_tf:
            transform = TransformStamped()
            transform.header = odometry.header
            transform.child_frame_id = self._base_frame
            transform.transform.translation.x = self._x
            transform.transform.translation.y = self._y
            transform.transform.rotation.z = quaternion_z
            transform.transform.rotation.w = quaternion_w
            self._tf_broadcaster.sendTransform(transform)


def main(args=None) -> None:
    """Run the Ackermann encoder-odometry node."""
    rclpy.init(args=args)
    node = None
    try:
        node = AckermannOdom()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
