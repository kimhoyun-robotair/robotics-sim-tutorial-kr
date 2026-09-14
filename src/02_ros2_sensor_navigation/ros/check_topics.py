"""ROS 2-side Python: 실제 센서 토픽과 TF가 도착하는지 확인하는 smoke check."""

import argparse
import json
import math
import time
from collections import Counter

import rclpy
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, Image, Imu, LaserScan
from tf2_ros import Buffer, TransformListener


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds는 유한한 양수여야 합니다.")
    rclpy.init()
    node = rclpy.create_node("learning_topic_check")
    counts = Counter()
    messages = {}
    subscriptions = []
    tf_buffer = Buffer()
    listener = TransformListener(tf_buffer, node)
    try:
        topics = [
            ("/clock", Clock),
            ("/odom", Odometry),
            ("/imu", Imu),
            ("/scan", LaserScan),
            ("/camera/rgb", Image),
            ("/camera/depth", Image),
            ("/camera/camera_info", CameraInfo),
        ]
        for topic, kind in topics:

            def receive(message, topic=topic):
                counts[topic] += 1
                messages[topic] = message

            subscriptions.append(
                node.create_subscription(kind, topic, receive, qos_profile_sensor_data)
            )
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        missing = [topic for topic, _ in topics if counts[topic] == 0]
        if missing:
            raise RuntimeError(f"수신하지 못한 토픽: {missing}")
        for topic in ("/camera/rgb", "/camera/depth", "/camera/camera_info"):
            if (messages[topic].width, messages[topic].height) != (320, 240):
                raise RuntimeError(f"예상하지 않은 해상도: {topic}")
        scan = messages["/scan"]
        expected_beams = (
            round((scan.angle_max - scan.angle_min) / scan.angle_increment) + 1
        )
        if len(scan.ranges) != expected_beams or not any(
            scan.range_min < r < scan.range_max for r in scan.ranges
        ):
            raise RuntimeError("LaserScan beam 수 또는 유효 range를 확인하세요.")
        for frame in ("base_link", "laser", "imu_link", "camera_optical_frame"):
            if not tf_buffer.can_transform("odom", frame, rclpy.time.Time()):
                raise RuntimeError(f"TF가 끊겼습니다: odom → {frame}")
        print(
            json.dumps(
                {
                    "counts": dict(counts),
                    "scan_beams": len(scan.ranges),
                    "tf_connected": True,
                },
                indent=2,
            )
        )
    finally:
        listener.unregister()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
