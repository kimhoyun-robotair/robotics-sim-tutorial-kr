#!/usr/bin/env python3
"""Bounded live ROS acceptance check. Run with Ubuntu 24.04/Jazzy system Python.

Default operation only subscribes. --exercise-timeout intentionally commands
the provided kinematic scene for two wall seconds, then checks its watchdog.
"""
import argparse
from collections import deque
import json
import math
from pathlib import Path
import time


def nanoseconds(stamp):
    return stamp.sec * 1_000_000_000 + stamp.nanosec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("clock", "scene"), default="scene")
    parser.add_argument("--duration", type=float, default=15)
    parser.add_argument("--exercise-timeout", action="store_true")
    parser.add_argument("--image-topic", help="Optional raw rgb8/bgr8/rgba8/bgra8/mono8 Image topic")
    parser.add_argument("--scan-topic", help="Optional sensor_msgs/LaserScan topic")
    parser.add_argument("--output", type=Path, default=Path("artifacts/ros-acceptance.json"))
    args = parser.parse_args()
    if not 8 <= args.duration <= 300:
        parser.error("duration must be 8..300 wall seconds")
    if args.exercise_timeout and args.mode != "scene":
        parser.error("--exercise-timeout requires --mode scene")
    report = {"status": "FAIL", "mode": args.mode, "scope": "live ROS observations",
              "exercise_timeout": args.exercise_timeout, "checks": {}, "errors": []}
    node = None
    ros = None
    publisher = None
    try:
        import rclpy
        from rclpy.qos import qos_profile_sensor_data, qos_profile_clock
        from rosgraph_msgs.msg import Clock
        from nav_msgs.msg import Odometry
        from tf2_msgs.msg import TFMessage
        from geometry_msgs.msg import Twist
        from sensor_msgs.msg import Image, LaserScan
        ros = rclpy
        ros.init(args=[])
        node = ros.create_node("tutorial_acceptance")
        counts = {"clock": 0, "odom": 0, "tf": 0, "image": 0, "scan": 0}
        stamps = {"clock": None, "odom": None, "tf": None, "image": None, "scan": None}
        monotonic = {key: True for key in stamps}
        last_received = {key: None for key in stamps}
        valid = {"odom": True, "tf": True, "image": True, "scan": True}
        samples = deque(maxlen=20000)
        recent_images = deque(maxlen=5)
        recent_scans = deque(maxlen=5)

        def stamp_check(key, stamp):
            value = nanoseconds(stamp)
            if value <= 0 or (stamps[key] is not None and value <= stamps[key]):
                monotonic[key] = False
            stamps[key] = value
            last_received[key] = time.monotonic()
            counts[key] += 1

        def clock_callback(message):
            stamp_check("clock", message.clock)

        def odom_callback(message):
            stamp_check("odom", message.header.stamp)
            pose = message.pose.pose
            q = pose.orientation
            values = (pose.position.x, pose.position.y, pose.position.z,
                      q.x, q.y, q.z, q.w, message.twist.twist.linear.x,
                      message.twist.twist.angular.z)
            good = all(math.isfinite(x) for x in values)
            good = good and abs(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w - 1) < 1e-3
            good = good and message.header.frame_id == "odom" and message.child_frame_id == "tutorial_base"
            good = good and abs(message.twist.twist.linear.x) <= 0.200001
            good = good and abs(message.twist.twist.angular.z) <= 0.600001
            good = good and max(abs(pose.position.x), abs(pose.position.y)) <= 2.000001
            valid["odom"] = valid["odom"] and good
            samples.append((time.monotonic(), pose.position.x, pose.position.y,
                            message.twist.twist.linear.x, message.twist.twist.angular.z))

        def tf_callback(message):
            for transform in message.transforms:
                if transform.child_frame_id != "tutorial_base":
                    continue
                stamp_check("tf", transform.header.stamp)
                q = transform.transform.rotation
                p = transform.transform.translation
                good = transform.header.frame_id == "odom"
                good = good and all(math.isfinite(v) for v in (p.x, p.y, p.z, q.x, q.y, q.z, q.w))
                good = good and abs(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w - 1) < 1e-3
                valid["tf"] = valid["tf"] and good

        def image_callback(message):
            stamp_check("image", message.header.stamp)
            channels = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4, "mono8": 1}.get(message.encoding)
            good = bool(channels and message.width > 0 and message.height > 0
                        and message.step >= message.width * channels
                        and len(message.data) == message.step * message.height
                        and message.header.frame_id and nanoseconds(message.header.stamp) > 0)
            valid["image"] = valid["image"] and good
            if good:
                # Sample rows/pixels; ignore alpha so opaque black fails the brightness check.
                stride_y = max(1, message.height // 32)
                stride_x = max(1, message.width // 32)
                total = 0
                n = 0
                for row in range(0, message.height, stride_y):
                    for col in range(0, message.width, stride_x):
                        offset = row * message.step + col * channels
                        pixel = message.data[offset:offset + min(channels, 3)]
                        total += sum(pixel)
                        n += len(pixel)
                recent_images.append(total / max(n, 1) > 2.0)
            else:
                recent_images.append(False)

        def scan_callback(message):
            stamp_check("scan", message.header.stamp)
            good = bool(message.ranges and message.header.frame_id
                        and nanoseconds(message.header.stamp) > 0
                        and math.isfinite(message.angle_increment) and message.angle_increment > 0
                        and math.isfinite(message.range_min) and math.isfinite(message.range_max)
                        and 0 <= message.range_min < message.range_max)
            valid["scan"] = valid["scan"] and good
            recent_scans.append(good and any(math.isfinite(v) and message.range_min <= v <= message.range_max
                                            for v in message.ranges))

        node.create_subscription(Clock, "/clock", clock_callback, qos_profile_clock)
        if args.mode == "scene":
            node.create_subscription(Odometry, "/tutorial/odom", odom_callback, qos_profile_sensor_data)
            node.create_subscription(TFMessage, "/tf", tf_callback, qos_profile_sensor_data)
        if args.image_topic:
            node.create_subscription(Image, args.image_topic, image_callback, qos_profile_sensor_data)
        if args.scan_topic:
            node.create_subscription(LaserScan, args.scan_topic, scan_callback, qos_profile_sensor_data)
        if args.exercise_timeout:
            publisher = node.create_publisher(Twist, "/tutorial/cmd_vel", 1)
        began = time.monotonic()
        drive_start = None
        last_command = -math.inf
        while ros.ok() and time.monotonic() - began < args.duration:
            ros.spin_once(node, timeout_sec=0.02)
            now = time.monotonic()
            if publisher is not None and counts["odom"] > 10:
                if drive_start is None:
                    drive_start = now
                if now - drive_start < 2.0 and now - last_command >= 0.1:
                    command = Twist()
                    command.linear.x = 0.1
                    publisher.publish(command)
                    last_command = now
        checks = report["checks"]
        checks["clock_received"] = counts["clock"] >= 10
        checks["clock_strictly_increasing"] = monotonic["clock"]
        checked_at = time.monotonic()
        checks["clock_recent"] = last_received["clock"] is not None and checked_at - last_received["clock"] < 0.5
        if args.mode == "scene":
            for key in ("odom", "tf"):
                checks[f"{key}_received"] = counts[key] >= 10
                checks[f"{key}_strictly_increasing"] = monotonic[key]
                checks[f"{key}_finite_frames_and_bounds"] = valid[key]
                checks[f"{key}_recent"] = last_received[key] is not None and checked_at - last_received[key] < 0.5
            if samples:
                checks["odometry_recent"] = time.monotonic() - samples[-1][0] < 0.5
            if args.exercise_timeout:
                driven = [s for s in samples if drive_start is not None and drive_start + 0.2 < s[0] < drive_start + 2]
                stopped = [s for s in samples if drive_start is not None and s[0] > drive_start + 3]
                first_stop = next((s for s in samples if s[0] > last_command and abs(s[3]) < 1e-6
                                   and abs(s[4]) < 1e-6), None)
                report["observed_stop_latency_wall_seconds"] = (
                    first_stop[0] - last_command if first_stop is not None else None)
                checks["command_caused_motion"] = len(driven) > 2 and math.hypot(driven[-1][1] - driven[0][1],
                                                                                driven[-1][2] - driven[0][2]) > 0.005
                checks["watchdog_observed_stop"] = len(stopped) >= 3 and all(abs(s[3]) < 1e-6 and abs(s[4]) < 1e-6 for s in stopped)
                checks["pose_stable_after_timeout"] = len(stopped) >= 3 and max(
                    math.hypot(s[1] - stopped[0][1], s[2] - stopped[0][2]) for s in stopped) < 1e-4
        if args.image_topic:
            checks["image_received"] = counts["image"] >= 3
            checks["image_layout_valid"] = valid["image"]
            checks["image_has_brightness"] = len(recent_images) >= 3 and all(recent_images)
            checks["image_strictly_increasing"] = monotonic["image"]
            checks["image_recent"] = last_received["image"] is not None and checked_at - last_received["image"] < 2.0
        if args.scan_topic:
            checks["scan_received"] = counts["scan"] >= 3
            checks["scan_layout_valid"] = valid["scan"]
            checks["scan_has_finite_return"] = len(recent_scans) >= 3 and all(recent_scans)
            checks["scan_strictly_increasing"] = monotonic["scan"]
            checks["scan_recent"] = last_received["scan"] is not None and checked_at - last_received["scan"] < 2.0
        report["counts"] = counts
        report["wall_duration_seconds"] = time.monotonic() - began
        report["status"] = "PASS" if all(checks.values()) else "FAIL"
        report["limitations"] = "Sampling checks cannot certify absence of all visual, physical or DDS faults."
    except Exception as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    except KeyboardInterrupt:
        report["errors"].append("interrupted")
    finally:
        if publisher is not None and ros is not None and ros.ok():
            from geometry_msgs.msg import Twist
            for _ in range(3):
                publisher.publish(Twist())
                time.sleep(0.05)
        if node is not None:
            node.destroy_node()
        if ros is not None and ros.ok():
            ros.shutdown()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
