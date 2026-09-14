"""Isaac Sim에 포함된 Python 3.11 rclpy로 실행하는 simulator 측 ROS interface."""

import time

from builtin_interfaces.msg import Time
from geometry_msgs.msg import TransformStamped, Twist
from isaacsim.core.utils.rotations import quat_to_rot_matrix
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, LaserScan
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

from command import VelocityCommand


def ros_time(seconds: float) -> Time:
    nanoseconds = round(seconds * 1_000_000_000)
    return Time(sec=nanoseconds // 1_000_000_000, nanosec=nanoseconds % 1_000_000_000)


def set_quaternion(message, wxyz) -> None:
    message.w, message.x, message.y, message.z = map(float, wxyz)


class RobotInterface(Node):
    def __init__(self, camera):
        super().__init__("learning_robot")
        self.command = VelocityCommand()
        self.subscription = self.create_subscription(
            Twist, "/cmd_vel", self.on_command, 10
        )
        self.odom = self.create_publisher(Odometry, "/odom", 10)
        self.imu = self.create_publisher(Imu, "/imu", qos_profile_sensor_data)
        self.scan = self.create_publisher(LaserScan, "/scan", qos_profile_sensor_data)
        self.scan_subscription = self.create_subscription(
            LaserScan, "/scan_raw", self.on_scan, qos_profile_sensor_data
        )
        self.tf = TransformBroadcaster(self)
        self.static_tf = StaticTransformBroadcaster(self)
        camera_position, camera_rotation = camera.get_local_pose(camera_axes="ros")
        transforms = []
        for child, position, rotation in (
            ("laser", [0.0, 0.0, 0.25], [1.0, 0.0, 0.0, 0.0]),
            ("imu_link", [0.0, 0.0, 0.15], [1.0, 0.0, 0.0, 0.0]),
            ("camera_optical_frame", camera_position, camera_rotation),
        ):
            transform = TransformStamped()
            transform.header.frame_id = "base_link"
            transform.child_frame_id = child
            (
                transform.transform.translation.x,
                transform.transform.translation.y,
                transform.transform.translation.z,
            ) = map(float, position)
            set_quaternion(transform.transform.rotation, rotation)
            transforms.append(transform)
        self.static_tf.sendTransform(transforms)

    def on_command(self, message: Twist) -> None:
        self.command.receive(message.linear.x, message.angular.z, time.monotonic())

    def on_scan(self, message: LaserScan) -> None:
        if not message.ranges:
            return
        # 5.1 RTX 출력의 endpoint/count 불일치로 SLAM Toolbox가 scan을 거부하므로 마지막 beam 각도를 명시한다.
        message.angle_max = (
            message.angle_min + (len(message.ranges) - 1) * message.angle_increment
        )
        self.scan.publish(message)

    def publish_state(self, chassis, imu, seconds: float) -> None:
        position, rotation = chassis.get_world_pose()
        to_body = quat_to_rot_matrix(rotation).T
        velocity = to_body @ chassis.get_linear_velocity()
        angular = to_body @ chassis.get_angular_velocity()
        stamp = ros_time(seconds)
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        (
            odom.pose.pose.position.x,
            odom.pose.pose.position.y,
            odom.pose.pose.position.z,
        ) = map(float, position)
        set_quaternion(odom.pose.pose.orientation, rotation)
        # Odometry의 pose는 odom 좌표계, twist는 child_frame_id 좌표계이다.
        (
            odom.twist.twist.linear.x,
            odom.twist.twist.linear.y,
            odom.twist.twist.linear.z,
        ) = map(float, velocity)
        (
            odom.twist.twist.angular.x,
            odom.twist.twist.angular.y,
            odom.twist.twist.angular.z,
        ) = map(float, angular)
        self.odom.publish(odom)
        transform = TransformStamped()
        transform.header = odom.header
        transform.child_frame_id = "base_link"
        (
            transform.transform.translation.x,
            transform.transform.translation.y,
            transform.transform.translation.z,
        ) = map(float, position)
        transform.transform.rotation = odom.pose.pose.orientation
        self.tf.sendTransform(transform)

        frame = imu.get_current_frame(read_gravity=True)
        if frame["time"] <= 0:
            return
        message = Imu()
        message.header.stamp = ros_time(frame["time"])
        message.header.frame_id = "imu_link"
        set_quaternion(message.orientation, frame["orientation"])
        (
            message.angular_velocity.x,
            message.angular_velocity.y,
            message.angular_velocity.z,
        ) = map(float, frame["ang_vel"])
        (
            message.linear_acceleration.x,
            message.linear_acceleration.y,
            message.linear_acceleration.z,
        ) = map(float, frame["lin_acc"])
        self.imu.publish(message)
