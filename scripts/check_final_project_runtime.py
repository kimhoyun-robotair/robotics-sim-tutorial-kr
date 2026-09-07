#!/usr/bin/env python3
"""Run each ported rover and check the data and transforms consumed by RViz.

Requires a built Jazzy workspace. Run under xvfb-run for --rviz screenshots.
Exit 69 means dependencies are absent; it is not a successful simulation test.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import shutil
import statistics
import struct
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def stop_owned(process: subprocess.Popen) -> list[int]:
    """Signal only the process group created by this checker, then list survivors."""
    for sig, seconds in ((signal.SIGINT, 8), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                return []
            time.sleep(0.1)
    process.poll()
    listing = subprocess.check_output(["ps", "-eo", "pid=,pgid=,stat="], text=True)
    return [int(p) for line in listing.splitlines()
            for p, g, state in [line.split()]
            if int(g) == process.pid and not state.startswith("Z")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", choices=["simple_rover", "f1tenth_sim"], required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--rviz", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    output = args.evidence.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"package": args.package, "status": "failed", "checks": {}, "errors": []}
    try:
        import rclpy
        from rclpy.duration import Duration
        from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
        from rclpy.signals import SignalHandlerOptions
        from rclpy.time import Time
        from geometry_msgs.msg import Twist
        from nav_msgs.msg import Odometry
        from rosgraph_msgs.msg import Clock
        from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan, PointCloud2
        from std_msgs.msg import String
        from tf2_ros import Buffer, TransformListener
    except ImportError as error:
        report["errors"].append(f"ROS runtime unavailable: {error}")
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        return 69

    required_commands = ["ros2", "ps"] + (["xdotool", "import"] if args.rviz else [])
    missing = [name for name in required_commands if shutil.which(name) is None]
    if missing:
        report["errors"].append(f"Required commands unavailable: {missing}")
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        return 69

    os.environ["ROS_DOMAIN_ID"] = str(100 + os.getpid() % 100)
    os.environ["GZ_PARTITION"] = f"jazzy_final_{args.package}_{os.getpid()}"
    os.environ["ROS2CLI_DISABLE_DAEMON"] = "1"
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    command = ["ros2", "launch", args.package, "spawn_robot.launch.py",
               "gui:=false", "headless:=true", f"rviz:={str(args.rviz).lower()}"]
    (output / "command.json").write_text(json.dumps(command) + "\n")
    process = None
    node = None
    initialized = False

    def interrupted(signum, _frame):
        raise InterruptedError(f"checker received signal {signum}")

    previous_handlers = {sig: signal.signal(sig, interrupted)
                         for sig in (signal.SIGINT, signal.SIGTERM)}
    with (output / "launch.log").open("w") as log:
        try:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            # Keep our handlers so SIGTERM also reaches the owned-process cleanup.
            rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
            initialized = True
            node = rclpy.create_node("final_project_probe")
            node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
            buffer = Buffer(cache_time=Duration(seconds=30))
            listener = TransformListener(buffer, node)
            messages = {}
            counts = {}
            first_stamps = {}
            last_stamps = {}
            timestamp_errors = set()
            subscriptions = []
            topics = {"/clock": Clock, "/scan": LaserScan, "/imu": Imu,
                      "/odom": Odometry, "/joint_states": JointState}
            if args.package == "simple_rover":
                topics.update({"/camera/image": Image, "/camera/depth_image": Image,
                               "/camera/camera_info": CameraInfo, "/camera/points": PointCloud2})

            def remember(topic, message):
                messages[topic] = message
                counts[topic] = counts.get(topic, 0) + 1
                stamp = message.clock if topic == "/clock" else getattr(getattr(message, "header", None), "stamp", None)
                if stamp is not None:
                    nanoseconds = stamp.sec * 1_000_000_000 + stamp.nanosec
                    first_stamps.setdefault(topic, nanoseconds)
                    if nanoseconds < last_stamps.get(topic, nanoseconds):
                        timestamp_errors.add(topic)
                    last_stamps[topic] = nanoseconds

            for topic, message_type in topics.items():
                subscriptions.append(node.create_subscription(
                    message_type, topic, lambda msg, t=topic: remember(t, msg),
                    qos_profile_sensor_data))
            subscriptions.append(node.create_subscription(
                String, "/robot_description", lambda msg: remember("description", msg),
                QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)))

            def spin_until(predicate, seconds):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise AssertionError(f"launch exited early: {process.returncode}")
                    rclpy.spin_once(node, timeout_sec=0.1)
                    if predicate():
                        return
                raise AssertionError(f"condition timed out; received message counts: {counts}")

            spin_until(lambda: all(counts.get(t, 0) >= 5 for t in topics)
                       and "description" in messages, args.timeout)
            assert not timestamp_errors, f"timestamps went backwards: {timestamp_errors}"
            assert all(last_stamps[t] > first_stamps[t] for t in topics), "one or more streams have frozen timestamps"
            clock = messages["/clock"].clock
            assert clock.sec + clock.nanosec / 1e9 > 0, "simulation clock is not advancing"
            frames = {"/scan": "scan_link" if args.package == "simple_rover" else "laser",
                      "/imu": "imu_link"}
            if args.package == "simple_rover":
                frames.update({"/camera/image": "camera_link_optical",
                               "/camera/depth_image": "camera_link_optical",
                               "/camera/camera_info": "camera_link_optical",
                               "/camera/points": "depth_link"})
            for topic, frame in frames.items():
                message = messages[topic]
                assert message.header.frame_id == frame, (topic, message.header.frame_id, frame)
                assert message.header.stamp.sec + message.header.stamp.nanosec / 1e9 > 0
                stamp = Time.from_msg(message.header.stamp)
                spin_until(lambda f=frame, t=stamp: buffer.can_transform("odom", f, t), 15)
            report["checks"]["sensor_frames_and_timestamped_tf"] = frames

            scan = messages["/scan"]
            finite_ranges = [r for r in scan.ranges if math.isfinite(r)]
            assert len(scan.ranges) > 100 and finite_ranges, "empty or unrendered LiDAR"
            assert all(scan.range_min <= r <= scan.range_max for r in finite_ranges)
            robot = ET.fromstring(messages["description"].data)
            links = {link.attrib["name"] for link in robot.findall("link")}
            spin_until(lambda: all(buffer.can_transform("odom", link, Time()) for link in links), 20)
            report["checks"]["connected_tf_links"] = sorted(links)
            movable = {j.attrib["name"] for j in robot.findall("joint")
                       if j.attrib["type"] != "fixed"}
            joints = messages["/joint_states"]
            assert movable <= set(joints.name), f"missing moving joints: {movable - set(joints.name)}"
            assert len(joints.name) == len(joints.position)
            assert all(math.isfinite(v) for v in joints.position)
            report["checks"]["joint_states"] = sorted(movable)
            imu = messages["/imu"]
            assert all(math.isfinite(v) for v in [imu.linear_acceleration.x,
                imu.linear_acceleration.y, imu.linear_acceleration.z,
                imu.angular_velocity.x, imu.angular_velocity.y, imu.angular_velocity.z])

            if args.package == "simple_rover":
                rgb = messages["/camera/image"]
                info = messages["/camera/camera_info"]
                depth = messages["/camera/depth_image"]
                cloud = messages["/camera/points"]
                assert rgb.width == info.width == depth.width == cloud.width
                assert rgb.height == info.height == depth.height == cloud.height
                assert rgb.width > 0 and rgb.height > 0 and info.k[0] > 0 and info.k[4] > 0
                assert len(rgb.data) == rgb.step * rgb.height
                assert len(set(rgb.data)) > 1, "RGB image is blank"
                assert depth.encoding == "32FC1", depth.encoding
                fields = {f.name: f for f in cloud.fields}
                assert all(n in fields and fields[n].datatype == 7 for n in ("x", "y", "z"))
                u, v = cloud.width // 2, cloud.height // 2
                offset = v * cloud.row_step + u * cloud.point_step
                endian = ">" if cloud.is_bigendian else "<"
                xyz = [struct.unpack_from(endian + "f", cloud.data,
                       offset + fields[n].offset)[0] for n in ("x", "y", "z")]
                depth_value = struct.unpack_from(
                    (">" if depth.is_bigendian else "<") + "f", depth.data,
                    v * depth.step + 4 * u)[0]
                assert all(math.isfinite(value) for value in xyz), xyz
                assert xyz[0] > 0 and abs(xyz[1]) < 0.1 * xyz[0] and abs(xyz[2]) < 0.1 * xyz[0], xyz
                assert math.isclose(xyz[0], depth_value, abs_tol=0.12), (xyz, depth_value)
                transform = buffer.lookup_transform("depth_link", "camera_link_optical", Time())
                q = transform.transform.rotation
                # Rotate optical +Z into the camera mounting link: it must point along +X.
                forward = (2 * (q.x * q.z + q.w * q.y),
                           2 * (q.y * q.z - q.w * q.x), 1 - 2 * (q.x * q.x + q.y * q.y))
                assert all(abs(a - b) < 1e-5 for a, b in zip(forward, (1, 0, 0))), forward
                report["checks"]["rgbd_body_xyz_and_optical_tf"] = {
                    "center_point": xyz, "depth_m": depth_value, "optical_forward_in_body": forward}

            if args.rviz:
                # A screenshot supplements numeric checks; it is not an automatic visual verdict.
                windows = []

                def rviz_window_ready():
                    found = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "rviz"],
                                           capture_output=True, text=True, timeout=5)
                    windows[:] = found.stdout.split()
                    return found.returncode == 0 and bool(windows)

                spin_until(rviz_window_ready, 30)
                subprocess.run(["import", "-window", windows[-1], str(output / "rviz.png")],
                               check=True, timeout=15)
                report["checks"]["rviz_capture"] = "rviz.png (requires visual review)"

            odom = messages["/odom"]
            assert odom.header.frame_id == "odom" and odom.child_frame_id == "base_link"
            start_x, start_y = odom.pose.pose.position.x, odom.pose.pose.position.y
            assert math.isfinite(start_x) and math.isfinite(start_y)

            def forward_range(message):
                assert message.angle_increment > 0
                center = round(-message.angle_min / message.angle_increment)
                values = [r for r in message.ranges[max(0, center - 2):center + 3] if math.isfinite(r)]
                assert values, "no finite LiDAR returns ahead of the rover"
                return statistics.median(values)

            initial_front_range = forward_range(messages["/scan"])
            publisher = node.create_publisher(Twist, "/cmd_vel", 10)
            twist = Twist()
            twist.linear.x = 0.12
            deadline = time.monotonic() + 45
            distance = 0.0
            while time.monotonic() < deadline and distance < 0.12:
                if process.poll() is not None:
                    raise AssertionError(f"launch exited during motion: {process.returncode}")
                publisher.publish(twist)
                rclpy.spin_once(node, timeout_sec=0.1)
                position = messages["/odom"].pose.pose.position
                distance = math.hypot(position.x - start_x, position.y - start_y)
            for _ in range(5):
                publisher.publish(Twist())
                rclpy.spin_once(node, timeout_sec=0.1)
            assert distance >= 0.12, f"cmd_vel did not move the rover: {distance} m"
            scans_before_stop = counts["/scan"]
            spin_until(lambda: counts["/scan"] >= scans_before_stop + 3, 15)
            front_range_change = initial_front_range - forward_range(messages["/scan"])
            assert front_range_change > 0.05, f"wheel odometry moved but the rendered front wall did not approach: {front_range_change} m"
            report["checks"]["rendered_front_wall_approach_m"] = front_range_change
            report["checks"]["commanded_displacement_m"] = distance
            report["checks"]["message_counts"] = counts
            report["status"] = "passed"
        except Exception as error:
            report["errors"].append(f"{type(error).__name__}: {error}")
        finally:
            # A second interrupt must not skip launch process cleanup.
            for sig in previous_handlers:
                signal.signal(sig, signal.SIG_IGN)
            try:
                if node is not None:
                    node.destroy_node()
                if initialized:
                    rclpy.shutdown()
            except Exception as error:
                report["status"] = "failed"
                report["errors"].append(f"ROS shutdown failed: {error}")
            report["survivors"] = stop_owned(process) if process is not None else []
            if report["survivors"]:
                report["status"] = "failed"
                report["errors"].append("owned processes survived cleanup")
            (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
