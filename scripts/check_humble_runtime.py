#!/usr/bin/env python3
"""Check real Humble / Gazebo Classic 11 data, TF, rendering and motion.

Run after sourcing ROS and the built workspace, under xvfb-run when using RViz.
The installed world is copied into the evidence directory with a diagnostic
gazebo_ros_state plugin. Its independent world poses distinguish actual vehicle
motion from spinning wheels. No existing Gazebo or ROS process is stopped.
Exit 69 means the runtime is unavailable, never a successful simulation check.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import statistics
import struct
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def quaternion_rpy(q):
    """Validate a quaternion and return fixed-axis roll, pitch and yaw."""
    x, y, z, w = q.x, q.y, q.z, q.w
    assert all(math.isfinite(v) for v in (x, y, z, w)), "nonfinite quaternion"
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    assert abs(norm - 1) < 0.03, f"invalid quaternion norm {norm}"
    x, y, z, w = (v / norm for v in (x, y, z, w))
    return (math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)),
            math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x)))),
            math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def rotated(q, xyz):
    """Rotate a vector with a unit quaternion, without extra dependencies."""
    quaternion_rpy(q)
    x, y, z = xyz
    tx, ty, tz = 2 * (q.y * z - q.z * y), 2 * (q.z * x - q.x * z), 2 * (q.x * y - q.y * x)
    return (x + q.w * tx + q.y * tz - q.z * ty,
            y + q.w * ty + q.z * tx - q.x * tz,
            z + q.w * tz + q.x * ty - q.y * tx)


def cloud_xyz(cloud, row, column):
    """Read XYZ while respecting field offsets, endianness and row padding."""
    assert cloud.width > 0 and cloud.height > 0 and cloud.point_step > 0
    assert cloud.row_step >= cloud.width * cloud.point_step
    assert len(cloud.data) == cloud.row_step * cloud.height, "truncated cloud buffer"
    fields = {f.name: f for f in cloud.fields}
    for name in ("x", "y", "z"):
        assert name in fields and fields[name].datatype == 7 and fields[name].count == 1
        assert 0 <= fields[name].offset <= cloud.point_step - 4
    assert 0 <= row < cloud.height and 0 <= column < cloud.width
    offset = row * cloud.row_step + column * cloud.point_step
    endian = ">" if cloud.is_bigendian else "<"
    return [struct.unpack_from(endian + "f", cloud.data, offset + fields[n].offset)[0]
            for n in ("x", "y", "z")]


def front_range(scan):
    assert scan.angle_increment > 0 and len(scan.ranges) > 100
    center = round(-scan.angle_min / scan.angle_increment)
    values = [r for r in scan.ranges[max(0, center - 2):center + 3] if math.isfinite(r)]
    assert values, "no finite forward LiDAR returns"
    return statistics.median(values)


def check_wheel_path(path):
    """Validate the Path geometry and simulation stamps consumed by RViz."""
    assert path.header.frame_id == "odom", path.header.frame_id
    assert len(path.poses) >= 2, "wheel odometry path has fewer than two poses"
    stamps = []
    for stamped in path.poses:
        assert stamped.header.frame_id == "odom", stamped.header.frame_id
        position = stamped.pose.position
        assert all(math.isfinite(value) for value in (position.x, position.y, position.z)), "nonfinite Path position"
        quaternion_rpy(stamped.pose.orientation)
        stamps.append(stamped.header.stamp.sec * 1_000_000_000 + stamped.header.stamp.nanosec)
    assert all(0 <= previous <= current for previous, current in zip(stamps, stamps[1:])), "Path pose stamps went backwards"
    assert stamps[-1] > stamps[0], "Path pose stamps do not advance"
    header_stamp = path.header.stamp.sec * 1_000_000_000 + path.header.stamp.nanosec
    assert header_stamp == stamps[-1], "Path header does not match the final pose stamp"
    first, last = path.poses[0].pose.position, path.poses[-1].pose.position
    return {"poses": len(path.poses), "frame": path.header.frame_id,
            "first_stamp_ns": stamps[0], "last_stamp_ns": stamps[-1],
            "first_xy_m": [first.x, first.y], "last_xy_m": [last.x, last.y],
            "endpoint_distance_m": math.hypot(last.x - first.x, last.y - first.y)}


def add_state_plugin(source, destination):
    """Preserve the demonstration world and add only an observing world plugin."""
    tree = ET.parse(source)
    world = tree.getroot().find("world")
    assert world is not None, f"no world in {source}"
    plugin = ET.SubElement(world, "plugin", name="humble_probe_state",
                           filename="libgazebo_ros_state.so")
    ET.SubElement(ET.SubElement(plugin, "ros"), "namespace").text = "/probe"
    ET.SubElement(plugin, "update_rate").text = "20"
    tree.write(destination, encoding="utf-8", xml_declaration=True)


def stop_owned(process):
    """Bounded cleanup of the process group created by this checker only."""
    for sig, seconds in ((signal.SIGINT, 8), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
        if sig == signal.SIGINT:
            # ros2 launch forwards SIGINT to its children. Sending it to the
            # whole group as well interrupts their shutdown handlers twice.
            try:
                if process.poll() is None:
                    process.send_signal(sig)
            except ProcessLookupError:
                pass  # The launch parent exited; its group may still exist.
        else:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                return []
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                return []
            time.sleep(0.1)
    process.poll()
    rows = subprocess.check_output(["ps", "-eo", "pid=,pgid=,stat="], text=True, timeout=3)
    return [int(pid) for row in rows.splitlines() for pid, pgid, state in [row.split()]
            if int(pgid) == process.pid and not state.startswith("Z")]


def capture_rviz(output):
    """Capture the largest RViz window, including displays and their statuses."""
    found = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "rviz"],
                           capture_output=True, text=True, timeout=4)
    candidates = []
    for window in found.stdout.split():
        result = subprocess.run(["xdotool", "getwindowgeometry", "--shell", window],
                                capture_output=True, text=True, timeout=4)
        if result.returncode:
            continue
        values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        width, height = int(values.get("WIDTH", 0)), int(values.get("HEIGHT", 0))
        candidates.append((width * height, window, width, height))
    if not candidates:
        return None
    _, window, width, height = max(candidates)
    if width < 1000 or height < 700:
        return None
    subprocess.run(["import", "-window", window, str(output / "rviz.png")],
                   check=True, timeout=15)
    return {"file": "rviz.png", "width": width, "height": height,
            "review": "full window captured; human visual review is required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True,
                        choices=["sensor_bot", "diffbot", "rover_diff", "rover_ackermann", "f1"])
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--rviz", action="store_true")
    parser.add_argument("--timeout", type=float, default=300,
                        help="total active wall-clock budget per model; cleanup adds at most 18 s")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    output = args.evidence.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"model": args.model, "status": "failed", "checks": {}, "errors": []}

    def write_report():
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        import rclpy
        from ament_index_python.packages import get_package_share_directory
        from rclpy.duration import Duration
        from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
        from rclpy.signals import SignalHandlerOptions
        from rclpy.time import Time
        from gazebo_msgs.msg import ModelStates
        from geometry_msgs.msg import Twist
        from ackermann_msgs.msg import AckermannDriveStamped
        from nav_msgs.msg import Odometry, Path as RosPath
        from rosgraph_msgs.msg import Clock
        from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan, NavSatFix, PointCloud2
        from std_msgs.msg import String
        from tf2_ros import Buffer, TransformListener
    except ImportError as error:
        report["errors"].append(f"ROS runtime unavailable: {error}")
        write_report()
        return 69
    commands = ["ros2", "ps"] + (["xdotool", "import"] if args.rviz else [])
    missing = [name for name in commands if shutil.which(name) is None]
    if missing or (args.rviz and not os.environ.get("DISPLAY")):
        report["errors"].append(f"runtime commands/display unavailable: {missing}; run under xvfb-run")
        write_report()
        return 69

    # Allocate a currently free port instead of connecting to a user's Gazebo.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        gazebo_port = reservation.getsockname()[1]
    os.environ["GAZEBO_MASTER_URI"] = f"http://127.0.0.1:{gazebo_port}"
    os.environ["ROS_DOMAIN_ID"] = str(100 + os.getpid() % 100)
    os.environ["ROS_LOCALHOST_ONLY"] = "1"
    os.environ["ROS2CLI_DISABLE_DAEMON"] = "1"
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    report["isolation"] = {key: os.environ[key] for key in
                           ("GAZEBO_MASTER_URI", "ROS_DOMAIN_ID", "ROS_LOCALHOST_ONLY")}

    process = node = publisher = drive_publisher = None
    initialized = False
    messages, counts, first_stamps, last_stamps = {}, {}, {}, {}
    imu_samples, timestamp_errors = deque(maxlen=300), set()
    started = time.monotonic()
    global_deadline = started + args.timeout

    def interrupted(signum, _frame):
        raise InterruptedError(f"checker received signal {signum}")

    previous_handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    with (output / "launch.log").open("w") as log:
        try:
            package = "f1_robot_model" if args.model == "f1" else "gazebo_tutorial_bringup"
            share = Path(get_package_share_directory(package))
            world_source = share / ("world/sensor_arena.world" if args.model == "f1" else
                                    "worlds/sensor.world" if args.model == "sensor_bot" else "worlds/empty.world")
            world_copy = output / "probe.world"
            add_state_plugin(world_source, world_copy)
            launch = "robot_spawn.launch.py" if args.model == "f1" else (
                "sensors.launch.py" if args.model == "sensor_bot" else args.model + ".launch.py")
            command = ["ros2", "launch", package, launch, "gui:=false",
                       "rviz:=" + str(args.rviz).lower(), "world:=" + str(world_copy), "use_sim_time:=true"]
            if args.model == "sensor_bot":
                command.append("sensor_profile:=all")
            if args.model == "f1":
                command += ["depth_camera:=true", "stereo_camera:=true", "lidar_3d:=true",
                            "gps:=true", "joystick:=false", "ackermann_adapter:=true"]
            report["command"] = command
            report["world_source"] = str(world_source)
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
            initialized = True
            node = rclpy.create_node("humble_runtime_probe")
            node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
            buffer = Buffer(cache_time=Duration(seconds=30))
            listener = TransformListener(buffer, node)
            subscriptions = []
            topics = {"/clock": Clock, "/odom": Odometry, "/joint_states": JointState,
                      "/probe/model_states": ModelStates}
            frames, image_pairs = {}, []
            depth_topics = None
            scan_topic = imu_topic = cloud3d_topic = None
            if args.model == "sensor_bot":
                scan_topic, imu_topic, cloud3d_topic = "/scan", "/imu/data", "/points"
                frames.update({scan_topic: "lidar_2d_link", imu_topic: "imu_link",
                               cloud3d_topic: "lidar_3d_link"})
                for prefix, frame, encoding in (
                    ("/camera", "camera_optical_frame", "mono8"),
                    ("/rgbd", "rgbd_camera_optical_frame", "rgb8"),
                    ("/stereo/left", "stereo_camera_left_optical_frame", "rgb8"),
                    ("/stereo/right", "stereo_camera_right_optical_frame", "rgb8"),
                    ("/fisheye", "fisheye_camera_optical_frame", "rgb8"),
                ):
                    image_pairs.append((prefix + "/image_raw", prefix + "/camera_info", encoding))
                    frames[prefix + "/image_raw"] = frames[prefix + "/camera_info"] = frame
                depth_topics = ("/rgbd/depth/image_raw", "/rgbd/depth/camera_info", "/rgbd/points")
                frames.update({t: "rgbd_camera_optical_frame" for t in depth_topics})
            elif args.model == "f1":
                # These are the public topics of the maintained F1 model.
                scan_topic, imu_topic, cloud3d_topic = "/scan", "/imu/data", "/lidar_3d/points"
                frames.update({scan_topic: "laser", imu_topic: "imu", cloud3d_topic: "lidar_3d_link"})
                image_pairs.append(("/camera/image_raw", "/camera/camera_info", "bgr8"))
                for side in ("left", "right"):
                    prefix, frame = "/" + side + "_camera", side + "_camera_link_optical"
                    image_pairs.append((prefix + "/image_raw", prefix + "/camera_info", "bgr8"))
                    frames[prefix + "/image_raw"] = frames[prefix + "/camera_info"] = frame
                depth_topics = ("/camera/depth/image_raw", "/camera/depth/camera_info", "/camera/points")
                frames.update({t: "camera_link_optical" for t in
                               ("/camera/image_raw", "/camera/camera_info", *depth_topics)})
                topics["/gps/data"] = NavSatFix
                frames["/gps/data"] = "gps"
            if scan_topic:
                topics[scan_topic], topics[imu_topic], topics[cloud3d_topic] = LaserScan, Imu, PointCloud2
            for image_topic, info_topic, _ in image_pairs:
                topics[image_topic], topics[info_topic] = Image, CameraInfo
            if depth_topics:
                topics[depth_topics[0]], topics[depth_topics[1]], topics[depth_topics[2]] = Image, CameraInfo, PointCloud2
            if args.model == "diffbot":
                topics["/ground_truth_path"] = RosPath
            if args.model != "f1":
                topics["/wheel_odom_path"] = RosPath
            if args.model == "rover_ackermann":
                topics["/ground_truth/odom"] = Odometry

            def remember(topic, message):
                messages[topic] = message
                counts[topic] = counts.get(topic, 0) + 1
                stamp = message.clock if topic == "/clock" else getattr(getattr(message, "header", None), "stamp", None)
                if stamp is not None:
                    ns = stamp.sec * 1_000_000_000 + stamp.nanosec
                    first_stamps.setdefault(topic, ns)
                    if ns < last_stamps.get(topic, ns):
                        timestamp_errors.add(topic)
                    last_stamps[topic] = ns
                if topic == imu_topic:
                    a, w = message.linear_acceleration, message.angular_velocity
                    imu_samples.append((a.x, a.y, a.z, w.x, w.y, w.z))

            for topic, msg_type in topics.items():
                subscriptions.append(node.create_subscription(msg_type, topic,
                    lambda msg, t=topic: remember(t, msg), qos_profile_sensor_data))
            subscriptions.append(node.create_subscription(String, "/robot_description",
                lambda msg: remember("description", msg),
                QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)))
            publisher = node.create_publisher(Twist, "/cmd_vel", 10)
            if args.model == "f1":
                drive_publisher = node.create_publisher(AckermannDriveStamped, "/drive", 10)
                subscriptions.append(node.create_subscription(Twist, "/cmd_vel",
                    lambda msg: remember("/cmd_vel", msg), qos_profile_sensor_data))
                report["checks"]["ackermann_adapter"] = {
                    "input": "/drive (AckermannDriveStamped)", "output": "/cmd_vel (Twist)",
                    "straight_output_verified": False, "turn_output_verified": False}

            def publish_command(command):
                if drive_publisher is None:
                    publisher.publish(command)
                else:
                    drive = AckermannDriveStamped()
                    drive.header.stamp = node.get_clock().now().to_msg()
                    drive.drive.speed = command.linear.x
                    drive.drive.steering_angle = command.angular.z
                    drive_publisher.publish(drive)

            def adapter_output_matches(speed, steering, phase):
                if drive_publisher is None:
                    return True
                observed = messages.get("/cmd_vel")
                matched = observed is not None and (
                    abs(observed.linear.x - speed) < 1e-6
                    and abs(observed.angular.z - steering) < 1e-6)
                if observed is not None:
                    report["checks"]["ackermann_adapter"][phase + "_last_output"] = {
                        "linear_x": observed.linear.x, "angular_z": observed.angular.z}
                if matched:
                    report["checks"]["ackermann_adapter"][phase + "_output_verified"] = True
                return matched

            def spin_until(predicate, seconds, label):
                deadline = min(global_deadline, time.monotonic() + seconds)
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise AssertionError(f"launch exited {process.returncode} during {label}")
                    rclpy.spin_once(node, timeout_sec=0.05)
                    if predicate():
                        return
                raise AssertionError(f"timed out: {label}; message counts {counts}")

            def ground_pose():
                state = messages["/probe/model_states"]
                entity = "racecar" if args.model == "f1" else args.model
                assert entity in state.name, f"missing model {entity}; present {state.name}"
                return state.pose[state.name.index(entity)]

            def stop_commands():
                for _ in range(5):
                    publish_command(Twist())
                    # A direct zero remains available if the adapter stops responding.
                    publisher.publish(Twist())
                    rclpy.spin_once(node, timeout_sec=0.02)

            spin_until(lambda: all(counts.get(t, 0) >= 5 for t in topics) and "description" in messages,
                       150, "all model and sensor streams")
            if drive_publisher is not None:
                spin_until(lambda: drive_publisher.get_subscription_count() > 0,
                           10, "Ackermann adapter subscribed to /drive")
            initial_clock = last_stamps["/clock"]
            # Wait in simulation time for spawn settling and accumulate meaningful sensor samples.
            spin_until(lambda: last_stamps["/clock"] - initial_clock >= 2_000_000_000,
                       45, "two seconds of advancing simulation time")
            assert not timestamp_errors, f"timestamps went backwards: {timestamp_errors}"
            for topic in topics:
                if topic in first_stamps:
                    assert last_stamps[topic] > first_stamps[topic], f"frozen timestamp: {topic}"
            report["checks"]["advancing_streams"] = sorted(topics)
            (output / "robot.urdf").write_text(messages["description"].data)
            robot = ET.fromstring(messages["description"].data)
            links = {link.attrib["name"] for link in robot.findall("link")}
            movable = {j.attrib["name"] for j in robot.findall("joint") if j.attrib["type"] != "fixed"}
            spin_until(lambda: all(buffer.can_transform("odom", link, Time()) for link in links),
                       20, "all robot links connected to odom")
            joint_state = messages["/joint_states"]
            assert len(joint_state.name) == len(joint_state.position)
            assert movable <= set(joint_state.name), f"missing JointState: {movable - set(joint_state.name)}"
            assert all(math.isfinite(value) for value in joint_state.position)
            report["checks"]["connected_tf_links"] = sorted(links)
            report["checks"]["moving_joints"] = sorted(movable)
            for topic, expected in frames.items():
                message = messages[topic]
                assert message.header.frame_id == expected, (topic, message.header.frame_id, expected)
                stamp = Time.from_msg(message.header.stamp)
                assert stamp.nanoseconds > 0
                spin_until(lambda f=expected, t=stamp: buffer.can_transform("odom", f, t),
                           15, f"timestamped TF {topic}")
            report["checks"]["sensor_frames_and_timestamped_tf"] = frames
            odom = messages["/odom"]
            assert odom.header.frame_id == "odom"
            assert odom.child_frame_id == ("base_link" if args.model == "f1" else "base_footprint")
            for topic in ("/ground_truth_path", "/ground_truth/odom"):
                if topic in topics:
                    message = messages[topic]
                    assert message.header.frame_id == "world"
                    if topic.endswith("path"):
                        assert message.poses and all(p.header.frame_id == "world" for p in message.poses)
            report["checks"]["stationary_ground_rpy_rad"] = quaternion_rpy(ground_pose().orientation)
            if args.model != "f1":
                report["checks"]["wheel_odom_path_initial"] = check_wheel_path(messages["/wheel_odom_path"])

            for image_topic, info_topic, encoding in image_pairs:
                image, info = messages[image_topic], messages[info_topic]
                assert image.width == info.width > 0 and image.height == info.height > 0
                assert image.encoding == encoding, (image_topic, image.encoding, encoding)
                assert len(image.data) == image.step * image.height and len(set(image.data)) > 1, image_topic
                if "fisheye" not in image_topic:
                    assert info.k[0] > 0 and info.k[4] > 0
                    assert all(math.isfinite(v) for v in (*info.k, *info.p))
                report["checks"][image_topic] = {"encoding": image.encoding, "width": image.width,
                                                 "height": image.height,
                                                 "calibration": "placeholder; equidistant image" if "fisheye" in image_topic else "pinhole"}
            if depth_topics:
                depth, info, cloud = [messages[t] for t in depth_topics]
                assert depth.encoding == "32FC1", depth.encoding
                assert depth.width == info.width == cloud.width and depth.height == info.height == cloud.height
                assert len(depth.data) == depth.step * depth.height
                u, v = depth.width // 2, depth.height // 2
                xyz = cloud_xyz(cloud, v, u)
                distance = struct.unpack_from((">" if depth.is_bigendian else "<") + "f",
                                              depth.data, v * depth.step + 4 * u)[0]
                assert all(math.isfinite(n) for n in (*xyz, distance)), (xyz, distance)
                # Classic gazebo_ros_camera emits optical XYZ. Harmonic's body XYZ
                # convention must not be copied into this check or the URDF frame.
                assert xyz[2] > 0 and abs(xyz[0]) < 0.1 * xyz[2] and abs(xyz[1]) < 0.1 * xyz[2], xyz
                assert abs(xyz[2] - distance) < 0.05, (xyz, distance)
                predicted = ((u - info.k[2]) * distance / info.k[0],
                             (v - info.k[5]) * distance / info.k[4], distance)
                assert all(abs(a - b) < 0.02 for a, b in zip(predicted, xyz)), (predicted, xyz)
                projection_errors = []
                for sample_u, sample_v in ((u - 40, v), (u + 40, v), (u, v - 30), (u, v + 30)):
                    point = cloud_xyz(cloud, sample_v, sample_u)
                    sample_depth = struct.unpack_from((">" if depth.is_bigendian else "<") + "f",
                        depth.data, sample_v * depth.step + 4 * sample_u)[0]
                    assert all(math.isfinite(n) for n in (*point, sample_depth)), point
                    expected = ((sample_u - info.k[2]) * sample_depth / info.k[0],
                                (sample_v - info.k[5]) * sample_depth / info.k[4], sample_depth)
                    error = max(abs(a - b) for a, b in zip(expected, point))
                    assert error < 0.04, f"off-center optical projection mismatch: {point}, {expected}"
                    projection_errors.append(error)
                transform = buffer.lookup_transform("base_link", cloud.header.frame_id, Time())
                forward = rotated(transform.transform.rotation, (0, 0, 1))
                assert max(abs(a - b) for a, b in zip(forward, (1, 0, 0))) < 1e-5, forward
                if args.model == "sensor_bot":
                    assert abs(distance - 5.625) < 0.12, f"front wall depth {distance}, expected 5.625 m"
                else:
                    assert abs(distance - 2.8) < 0.12, f"front wall depth {distance}, expected 2.8 m"
                report["checks"]["rgbd_optical_xyz"] = {"center_xyz_m": xyz, "center_depth_m": distance,
                                                        "calibrated_projection_xyz_m": predicted,
                                                        "off_center_projection_errors_m": projection_errors,
                                                        "optical_forward_in_base": forward}
            if args.model == "sensor_bot":
                left, right = messages["/stereo/left/camera_info"], messages["/stereo/right/camera_info"]
                assert abs(left.p[3]) < 1e-9 and right.p[0] > 0
                baseline = -right.p[3] / right.p[0]
                assert abs(baseline - 0.08) < 1e-6, baseline
                transform = buffer.lookup_transform(left.header.frame_id, right.header.frame_id, Time())
                t = transform.transform.translation
                assert abs(t.x - baseline) < 1e-6 and abs(t.y) < 1e-6 and abs(t.z) < 1e-6, (t, baseline)
                report["checks"]["stereo_baseline_m"] = baseline
                assert abs(front_range(messages[scan_topic]) - 5.795) < 0.15, front_range(messages[scan_topic])
                assert max(abs(v) for v in quaternion_rpy(ground_pose().orientation)[:2]) < 0.03, "sensor robot tilts at rest"
            if args.model == "f1":
                left, right = messages["/left_camera/camera_info"], messages["/right_camera/camera_info"]
                assert abs(left.p[3]) < 1e-9 and right.p[0] > 0
                baseline = -right.p[3] / right.p[0]
                assert abs(baseline - 0.2) < 1e-6, baseline
                transform = buffer.lookup_transform(left.header.frame_id, right.header.frame_id, Time())
                t = transform.transform.translation
                assert abs(t.x - baseline) < 1e-6 and abs(t.y) < 1e-6 and abs(t.z) < 1e-6
                report["checks"]["stereo_baseline_m"] = baseline
                assert abs(front_range(messages[scan_topic]) - 2.9) < 0.15, front_range(messages[scan_topic])
                fix = messages["/gps/data"]
                assert all(math.isfinite(v) for v in (fix.latitude, fix.longitude, fix.altitude))
                assert -90 <= fix.latitude <= 90 and -180 <= fix.longitude <= 180 and fix.status.status >= 0
                world = ET.parse(world_source).getroot().find("world")
                latitude = float(world.findtext("spherical_coordinates/latitude_deg", "0"))
                longitude = float(world.findtext("spherical_coordinates/longitude_deg", "0"))
                altitude = float(world.findtext("spherical_coordinates/elevation", "0"))
                assert abs(fix.latitude - latitude) < 0.0001 and abs(fix.longitude - longitude) < 0.0001
                assert abs(fix.altitude - altitude) < 5, "GNSS altitude must be metres above world datum"
                report["checks"]["gnss"] = {"latitude_deg": fix.latitude, "longitude_deg": fix.longitude,
                                             "altitude_m": fix.altitude, "status": fix.status.status}
            if scan_topic:
                scan = messages[scan_topic]
                finite = [r for r in scan.ranges if math.isfinite(r)]
                assert finite and all(scan.range_min <= r <= scan.range_max for r in finite)
                report["checks"]["lidar"] = {"rays": len(scan.ranges), "finite_rays": len(finite),
                                              "forward_range_m": front_range(scan)}
                cloud = messages[cloud3d_topic]
                # Classic ray plugin may flatten scan rows to height=1.
                xyzs = [cloud_xyz(cloud, row, column) for row in range(cloud.height)
                        for column in range(cloud.width)]
                finite_xyzs = [xyz for xyz in xyzs if all(math.isfinite(n) for n in xyz)]
                assert len(xyzs) >= 1000 and len(finite_xyzs) >= 100, "empty 3D LiDAR"
                vertical_angles = [math.atan2(z, math.hypot(x, y)) for x, y, z in finite_xyzs]
                assert max(vertical_angles) - min(vertical_angles) > 0.1, "3D scan collapsed to a plane"
                assert all(0.01 < math.sqrt(sum(n * n for n in xyz)) < 100 for xyz in finite_xyzs)
                forward_returns = [x for x, y, z in finite_xyzs
                                   if x > 0 and abs(y / x) < 0.025 and abs(z / x) < 0.035]
                assert forward_returns, "3D cloud has no +X forward wall returns in its mounting frame"
                expected_wall = 6.045 if args.model == "sensor_bot" else 3.0
                cloud_wall = statistics.median(forward_returns)
                assert abs(cloud_wall - expected_wall) < 0.15, (cloud_wall, expected_wall)
                report["checks"]["lidar3d"] = {"width": cloud.width, "height": cloud.height,
                    "finite_points": len(finite_xyzs), "vertical_angle_span_rad": max(vertical_angles) - min(vertical_angles),
                    "forward_wall_x_m": cloud_wall}
                # Drop startup impact samples before checking the stationary IMU.
                samples = list(imu_samples)[-100:]
                assert len(samples) >= 20 and all(math.isfinite(n) for row in samples for n in row)
                means = [statistics.mean(row[i] for row in samples) for i in range(6)]
                assert abs(means[0]) < 0.35 and abs(means[1]) < 0.35 and abs(means[2] - 9.80665) < 0.35, means
                assert max(abs(v) for v in means[3:]) < 0.1, means
                report["checks"]["stationary_imu_means"] = means

            initial_pose = ground_pose()
            start_xy = initial_pose.position.x, initial_pose.position.y
            start_odom = messages["/odom"].pose.pose.position
            initial_front = front_range(messages[scan_topic]) if scan_topic else None
            if args.model != "f1":
                path_start = messages["/wheel_odom_path"].poses[-1].pose.position
                path_start_xy = path_start.x, path_start.y
                path_start_stamp = last_stamps["/wheel_odom_path"]
            command = Twist()
            command.linear.x = 0.15
            movement = {"command_linear_m_s": 0.15, "ground_distance_m": 0.0, "odom_distance_m": 0.0}
            report["checks"]["straight_motion"] = movement
            def drive_straight():
                publish_command(command)
                pose, odom_position = ground_pose(), messages["/odom"].pose.pose.position
                movement["ground_distance_m"] = math.hypot(pose.position.x - start_xy[0], pose.position.y - start_xy[1])
                movement["odom_distance_m"] = math.hypot(odom_position.x - start_odom.x, odom_position.y - start_odom.y)
                converted = adapter_output_matches(0.15, 0.0, "straight")
                return movement["ground_distance_m"] >= 0.20 and movement["odom_distance_m"] >= 0.15 and converted
            try:
                spin_until(drive_straight, 55, "commanded straight physical motion and odometry")
            finally:
                stop_commands()
            if args.model != "f1":
                def wheel_path_moved():
                    path = messages["/wheel_odom_path"]
                    endpoint = path.poses[-1].pose.position
                    distance = math.hypot(endpoint.x - path_start_xy[0], endpoint.y - path_start_xy[1])
                    return last_stamps["/wheel_odom_path"] > path_start_stamp and distance >= 0.15
                spin_until(wheel_path_moved, 15, "wheel Path endpoint advanced at least 0.15 m")
                path_check = check_wheel_path(messages["/wheel_odom_path"])
                path_check["displacement_since_command_m"] = math.hypot(
                    path_check["last_xy_m"][0] - path_start_xy[0],
                    path_check["last_xy_m"][1] - path_start_xy[1])
                assert path_check["endpoint_distance_m"] >= 0.15, path_check
                report["checks"]["wheel_odom_path_after_straight"] = path_check
            if scan_topic:
                old_count = counts[scan_topic]
                spin_until(lambda: counts[scan_topic] >= old_count + 3, 15, "fresh LiDAR after stopping")
                movement["front_wall_approach_m"] = initial_front - front_range(messages[scan_topic])
                assert movement["front_wall_approach_m"] > 0.08, movement

            if args.model in ("rover_ackermann", "f1"):
                start_pose = ground_pose()
                start_x, start_y = start_pose.position.x, start_pose.position.y
                initial_yaw = previous_yaw = quaternion_rpy(start_pose.orientation)[2]
                yaw_change = 0.0
                steering_names = {j.attrib["name"] for j in robot.findall("joint")
                                  if "steering" in j.attrib["name"] and "wheel" not in j.attrib["name"]
                                  and j.attrib["type"] == "revolute"}
                assert len(steering_names) == 2, steering_names
                command = Twist()
                # Gazebo Classic Ackermann uses angular.z as steering ANGLE.
                command.linear.x, command.angular.z = 0.15, 0.20
                arc = {"command_speed_m_s": 0.15, "command_steering_angle_rad": 0.20}
                report["checks"]["ackermann_left_arc"] = arc
                def drive_arc():
                    nonlocal yaw_change, previous_yaw
                    publish_command(command)
                    pose = ground_pose()
                    yaw = quaternion_rpy(pose.orientation)[2]
                    yaw_change += math.atan2(math.sin(yaw - previous_yaw), math.cos(yaw - previous_yaw))
                    previous_yaw = yaw
                    dx, dy = pose.position.x - start_x, pose.position.y - start_y
                    positions = dict(zip(messages["/joint_states"].name, messages["/joint_states"].position))
                    assert steering_names <= positions.keys()
                    angles = {name: positions[name] for name in steering_names}
                    assert all(math.isfinite(v) and abs(v) < 0.8 for v in angles.values()), angles
                    arc.update({"ground_yaw_change_rad": yaw_change,
                                "forward_m": math.cos(initial_yaw) * dx + math.sin(initial_yaw) * dy,
                                "left_m": -math.sin(initial_yaw) * dx + math.cos(initial_yaw) * dy,
                                "steering_angles_rad": angles})
                    assert -0.05 < yaw_change < 0.65, arc
                    converted = adapter_output_matches(0.15, 0.20, "turn")
                    return yaw_change >= 0.12 and arc["forward_m"] > 0.15 and arc["left_m"] > 0.003 and all(abs(v) > 0.03 for v in angles.values()) and converted
                try:
                    spin_until(drive_arc, 55, "physical Ackermann left turn and steering joints")
                finally:
                    stop_commands()

            # The screenshot should show the completed path and final vehicle pose.
            # All camera geometry checks above remain at the initial stationary pose.
            stopped_clock = last_stamps["/clock"]
            spin_until(lambda: last_stamps["/clock"] - stopped_clock >= 500_000_000,
                       15, "half a simulation second for final RViz data to update")
            if args.model != "f1":
                report["checks"]["wheel_odom_path_final"] = check_wheel_path(messages["/wheel_odom_path"])
            assert not timestamp_errors, f"timestamps went backwards during motion: {timestamp_errors}"
            if args.rviz:
                capture = []
                def capture_when_ready():
                    result = capture_rviz(output)
                    if result:
                        capture.append(result)
                    return bool(capture)
                spin_until(capture_when_ready, 25, "full RViz window after completed motion")
                report["checks"]["rviz_capture"] = capture[0]

            report["status"] = "passed"
        except Exception as error:
            report["errors"].append(f"{type(error).__name__}: {error}")
        finally:
            for sig in previous_handlers:
                signal.signal(sig, signal.SIG_IGN)
            if node is not None and publisher is not None:
                try:
                    for _ in range(5):
                        if drive_publisher is not None:
                            drive_publisher.publish(AckermannDriveStamped())
                        publisher.publish(Twist())
                        rclpy.spin_once(node, timeout_sec=0.02)
                    report["stop_command_sent"] = True
                except Exception as error:
                    report["status"] = "failed"
                    report["errors"].append(f"stop command failed: {error}")
            try:
                if node is not None:
                    node.destroy_node()
                if initialized:
                    rclpy.shutdown()
            except Exception as error:
                report["status"] = "failed"
                report["errors"].append(f"ROS shutdown failed: {error}")
            try:
                report["survivors"] = stop_owned(process) if process is not None else []
                if report["survivors"]:
                    report["status"] = "failed"
                    report["errors"].append("owned processes survived cleanup")
            except Exception as error:
                report["status"] = "failed"
                report["errors"].append(f"process cleanup failed: {error}")
            report["message_counts"] = counts
            report["elapsed_wall_seconds"] = time.monotonic() - started
            write_report()
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
