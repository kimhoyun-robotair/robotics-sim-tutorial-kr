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


def check_lidar3d_cloud(cloud, minimum: float, maximum: float) -> dict:
    """Validate organized 3D returns in metres, allowing missing rays and sensor noise."""
    assert cloud.width > 0 and cloud.height > 1, "3D LiDAR cloud is empty or has only one row"
    assert cloud.point_step > 0 and cloud.row_step >= cloud.width * cloud.point_step
    assert len(cloud.data) == cloud.row_step * cloud.height, "truncated 3D LiDAR buffer"
    fields = {field.name: field for field in cloud.fields}
    for name in ("x", "y", "z"):
        assert name in fields and fields[name].datatype == 7, f"LiDAR {name} must be FLOAT32"
        assert fields[name].count == 1 and 0 <= fields[name].offset <= cloud.point_step - 4
    assert 0 <= minimum < maximum
    endian = ">" if cloud.is_bigendian else "<"
    distances = []
    sample = None
    for row in range(cloud.height):
        for column in range(cloud.width):
            offset = row * cloud.row_step + column * cloud.point_step
            xyz = [struct.unpack_from(endian + "f", cloud.data,
                   offset + fields[name].offset)[0] for name in ("x", "y", "z")]
            if not all(math.isfinite(value) for value in xyz):
                continue  # No-return rays may contain infinity or NaN.
            distance = math.sqrt(sum(value * value for value in xyz))
            # The supplied sensor has 0.01 m Gaussian noise; allow a 0.05 m margin.
            assert distance > 0 and minimum - 0.05 <= distance <= maximum + 0.05, xyz
            distances.append(distance)
            if sample is None:
                sample = xyz
    assert distances, "3D LiDAR has no finite XYZ returns"
    return {"width": cloud.width, "height": cloud.height,
            "finite_points": len(distances),
            "missing_points": cloud.width * cloud.height - len(distances),
            "example_xyz_m": sample, "sensor_range_m": [minimum, maximum],
            "observed_range_m": [min(distances), max(distances)]}


def check_navsat_fix(fix) -> dict:
    """Check WGS84 degrees/metres near the default arena origin before driving."""
    latitude, longitude, altitude = fix.latitude, fix.longitude, fix.altitude
    assert all(math.isfinite(value) for value in (latitude, longitude, altitude)), "nonfinite GNSS fix"
    assert -90.0 <= latitude <= 90.0, f"latitude outside [-90, 90] degrees: {latitude}"
    assert -180.0 <= longitude <= 180.0, f"longitude outside [-180, 180] degrees: {longitude}"
    assert fix.status.status >= 0, f"GNSS reports no fix: {fix.status.status}"
    origin_latitude, origin_longitude, origin_altitude = 37.5665, 126.9780, 0.0
    # Haversine with mean Earth radius is sufficient for this 5 m origin check.
    # NavSatFix altitude is metres above the WGS84 ellipsoid, not a radian angle.
    latitude_radians, origin_radians = math.radians(latitude), math.radians(origin_latitude)
    delta_latitude = latitude_radians - origin_radians
    delta_longitude = math.radians(longitude - origin_longitude)
    haversine = (math.sin(delta_latitude / 2) ** 2
                 + math.cos(latitude_radians) * math.cos(origin_radians)
                 * math.sin(delta_longitude / 2) ** 2)
    horizontal_error = 2 * 6_371_008.8 * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))
    altitude_error = abs(altitude - origin_altitude)
    assert horizontal_error <= 5.0, f"GNSS is {horizontal_error:.3f} m from the arena origin"
    assert altitude_error <= 5.0, f"GNSS altitude differs by {altitude_error:.3f} m"
    return {"latitude_deg": latitude, "longitude_deg": longitude, "altitude_m": altitude,
            "expected_origin": {"latitude_deg": origin_latitude,
                                "longitude_deg": origin_longitude, "altitude_m": origin_altitude},
            "horizontal_error_m": horizontal_error, "altitude_error_m": altitude_error,
            "status": fix.status.status}


def quaternion_yaw(orientation) -> float:
    """Read a finite odometry quaternion as a heading in radians."""
    x, y, z, w = (orientation.x, orientation.y, orientation.z, orientation.w)
    assert all(math.isfinite(value) for value in (x, y, z, w)), "nonfinite odometry quaternion"
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    assert abs(norm - 1.0) < 0.05, f"invalid odometry quaternion norm: {norm}"
    x, y, z, w = (value / norm for value in (x, y, z, w))
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def read_steering_joints(robot) -> dict:
    """Resolve the Ackermann joints, their base-frame axis signs, and URDF limits."""
    plugin = robot.find(".//plugin[@name='gz::sim::systems::AckermannSteering']")
    assert plugin is not None, "AckermannSteering plugin missing from robot_description"
    joints = {joint.attrib["name"]: joint for joint in robot.findall("joint")}
    parents = {joint.find("child").attrib["link"]: joint for joint in joints.values()}
    result = {}
    for side in ("left", "right"):
        name = plugin.findtext(side + "_steering_joint")
        assert name in joints, f"missing {side} steering joint: {name}"
        joint = joints[name]
        assert joint.attrib["type"] == "revolute", f"{name} must have bounded revolute motion"
        axis = joint.find("axis")
        vector = list(map(float, (axis.attrib.get("xyz", "1 0 0")
                                 if axis is not None else "1 0 0").split()))
        norm = math.sqrt(sum(value * value for value in vector))
        assert math.isfinite(norm) and norm > 0
        vector = [value / norm for value in vector]
        current = joint
        visited = set()
        while current is not None:
            assert current.attrib["name"] not in visited, "cycle in steering joint ancestry"
            visited.add(current.attrib["name"])
            origin = current.find("origin")
            roll, pitch, yaw = map(float, (origin.attrib.get("rpy", "0 0 0")
                                         if origin is not None else "0 0 0").split())
            # URDF fixed-axis RPY rotates a joint-frame vector into its parent.
            x, y, z = vector
            y, z = math.cos(roll) * y - math.sin(roll) * z, math.sin(roll) * y + math.cos(roll) * z
            x, z = math.cos(pitch) * x + math.sin(pitch) * z, -math.sin(pitch) * x + math.cos(pitch) * z
            vector = [math.cos(yaw) * x - math.sin(yaw) * y,
                      math.sin(yaw) * x + math.cos(yaw) * y, z]
            parent = current.find("parent").attrib["link"]
            if parent == "base_link":
                break
            assert parent in parents, f"{name} has no ancestry to base_link"
            current = parents[parent]
            assert current.attrib["type"] == "fixed", "steering parent must be fixed to the base"
        assert abs(vector[2]) > 0.999, f"{name} does not steer about the base vertical axis: {vector}"
        limit = joint.find("limit")
        assert limit is not None
        lower, upper = float(limit.attrib["lower"]), float(limit.attrib["upper"])
        assert math.isfinite(lower) and math.isfinite(upper) and lower < 0 < upper
        result[name] = {"side": side, "axis_in_base": vector,
                        "limits_rad": [lower, upper], "positive_left_turn_sign": math.copysign(1, vector[2])}
    assert len(result) == 2, "left and right steering joints must be distinct"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", choices=["simple_rover", "f1tenth_sim"], required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--rviz", action="store_true")
    parser.add_argument("--extra-sensors", action="store_true",
                        help="Enable and verify simple_rover's 3D LiDAR and GNSS as well")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.extra_sensors and args.package != "simple_rover":
        parser.error("--extra-sensors is supported only with --package simple_rover")
    output = args.evidence.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"package": args.package, "extra_sensors": args.extra_sensors,
              "status": "failed", "checks": {}, "errors": []}
    try:
        import rclpy
        from rclpy.duration import Duration
        from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
        from rclpy.signals import SignalHandlerOptions
        from rclpy.time import Time
        from geometry_msgs.msg import Twist
        from nav_msgs.msg import Odometry
        from rosgraph_msgs.msg import Clock
        from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan, NavSatFix, PointCloud2
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
    if args.extra_sensors:
        command += ["lidar_3d:=true", "gps:=true"]
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
            if args.extra_sensors:
                topics.update({"/lidar3d/points": PointCloud2, "/navsat": NavSatFix})

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
            if args.extra_sensors:
                frames.update({"/lidar3d/points": "lidar3d_link", "/navsat": "navsat_link"})
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
            if args.extra_sensors:
                limits = robot.find(".//sensor[@name='gpu_lidar_3d']/lidar/range")
                assert limits is not None, "3D LiDAR is absent from robot_description"
                report["checks"]["lidar3d_xyz"] = check_lidar3d_cloud(
                    messages["/lidar3d/points"], float(limits.findtext("min")),
                    float(limits.findtext("max")))
                report["checks"]["gnss_wgs84_fix"] = check_navsat_fix(messages["/navsat"])
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
            if args.package == "f1tenth_sim":
                steering = read_steering_joints(robot)
                arc_pose = messages["/odom"].pose.pose
                arc_x, arc_y = arc_pose.position.x, arc_pose.position.y
                initial_yaw = previous_yaw = quaternion_yaw(arc_pose.orientation)
                previous_odom_count = counts["/odom"]
                initial_joint_count = counts["/joint_states"]
                initial_positions = dict(zip(messages["/joint_states"].name,
                                             messages["/joint_states"].position))
                assert steering.keys() <= initial_positions.keys()
                assert all(math.isfinite(initial_positions[name]) for name in steering)
                turn = Twist()
                turn.linear.x, turn.angular.z = 0.12, 0.12
                arc = {"command_linear_m_s": turn.linear.x, "command_yaw_rad_s": turn.angular.z,
                       "initial_yaw_rad": initial_yaw, "yaw_change_rad": 0.0,
                       "displacement_m": 0.0, "forward_displacement_m": 0.0,
                       "left_displacement_m": 0.0, "steering_joints": steering,
                       "stop_command_sent": False}
                report["checks"]["ackermann_left_arc"] = arc
                yaw_change = 0.0
                deadline = time.monotonic() + 45
                stop_error = None
                try:
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            raise AssertionError(f"launch exited during Ackermann turn: {process.returncode}")
                        publisher.publish(turn)
                        rclpy.spin_once(node, timeout_sec=0.1)
                        pose = messages["/odom"].pose.pose
                        heading = quaternion_yaw(pose.orientation)
                        if counts["/odom"] != previous_odom_count:
                            yaw_change += math.atan2(math.sin(heading - previous_yaw),
                                                     math.cos(heading - previous_yaw))
                            previous_yaw = heading
                            previous_odom_count = counts["/odom"]
                        dx, dy = pose.position.x - arc_x, pose.position.y - arc_y
                        assert math.isfinite(dx) and math.isfinite(dy)
                        arc.update({"yaw_change_rad": yaw_change, "displacement_m": math.hypot(dx, dy),
                                    "forward_displacement_m": math.cos(initial_yaw) * dx + math.sin(initial_yaw) * dy,
                                    "left_displacement_m": -math.sin(initial_yaw) * dx + math.cos(initial_yaw) * dy})
                        state = messages["/joint_states"]
                        positions = dict(zip(state.name, state.position))
                        assert steering.keys() <= positions.keys(), "steering joints disappeared from JointState"
                        correct_signs = True
                        for name, details in steering.items():
                            angle = positions[name]
                            lower, upper = details["limits_rad"]
                            assert math.isfinite(angle) and lower - 0.02 <= angle <= upper + 0.02, (name, angle)
                            signed_angle = details["positive_left_turn_sign"] * angle
                            signed_change = details["positive_left_turn_sign"] * (angle - initial_positions[name])
                            details.update({"initial_angle_rad": initial_positions[name],
                                            "angle_rad": angle, "angle_change_rad": angle - initial_positions[name],
                                            "left_steering_angle_rad": signed_angle,
                                            "left_steering_change_rad": signed_change})
                            correct_signs &= signed_angle > 0.03 and signed_change > 0.03
                        assert yaw_change > -0.05, f"positive yaw command turned right: {yaw_change} rad"
                        assert yaw_change <= 0.75, "turn exceeded the probe angle before steering checks passed"
                        if (yaw_change >= 0.15 and arc["forward_displacement_m"] >= 0.12
                                and arc["left_displacement_m"] > 0.003 and correct_signs
                                and counts["/joint_states"] >= initial_joint_count + 3):
                            break
                    assert arc["yaw_change_rad"] >= 0.15, f"no positive Ackermann yaw response: {arc}"
                    assert arc["forward_displacement_m"] >= 0.12 and arc["left_displacement_m"] > 0.003, arc
                    assert all(value["left_steering_angle_rad"] > 0.03
                               and value["left_steering_change_rad"] > 0.03
                               for value in steering.values()), steering
                    assert counts["/joint_states"] >= initial_joint_count + 3, "steering JointState stalled"
                    arc["observed_radius_m"] = arc["displacement_m"] / (2 * math.sin(yaw_change / 2))
                finally:
                    # Keep the original failure if stopping also fails; outer cleanup still runs.
                    try:
                        assert rclpy.ok(), "ROS context stopped before the zero command"
                        for _ in range(5):
                            publisher.publish(Twist())
                            rclpy.spin_once(node, timeout_sec=0.1)
                        arc["stop_command_sent"] = True
                    except Exception as error:
                        stop_error = error
                        report["errors"].append(f"Ackermann stop failed: {error}")
                assert stop_error is None, "could not send the Ackermann stop command"
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
