#!/usr/bin/env python3
"""Exercise the ported AMCL/Nav2 launch and the installed navigation demo.

Run after sourcing ROS 2 Jazzy and the built examples workspace. Evidence includes
the exact SDF/URDF, a map rasterized from their geometry, commands, logs, and JSON.
No ROS installation is reported as exit 69, never as a successful navigation test.
"""
from __future__ import annotations

import argparse
import ast
from collections import deque
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from check_final_project_runtime import stop_owned


def read_static_boxes(world_path: Path) -> list[dict]:
    """Read the arena's axis-aligned static boxes; reject unsupported geometry."""
    world = ET.parse(world_path).getroot().find("world")
    assert world is not None and world.get("name") == "rover_arena", "expected rover_arena"
    assert not world.findall("include") and not world.findall("frame"), "unsupported SDF frame/include"
    boxes = []
    for model in world.findall("model"):
        assert model.findtext("static") == "true", "map source contains a dynamic model"
        assert not model.findall("model"), "nested SDF models are unsupported"
        for link in model.findall("link"):
            for collision in link.findall("collision"):
                position = [0.0, 0.0, 0.0]
                for entity in (model, link, collision):
                    pose = entity.find("pose")
                    if pose is None:
                        continue
                    assert not pose.get("relative_to"), "relative SDF frames are unsupported"
                    assert not pose.get("rotation_format") and not pose.get("degrees")
                    values = [float(value) for value in pose.text.split()]
                    assert len(values) == 6 and all(math.isfinite(v) for v in values)
                    assert all(abs(v) < 1e-12 for v in values[3:]), "rotated SDF box unsupported"
                    position = [a + b for a, b in zip(position, values[:3])]
                geometry = collision.find("geometry")
                assert geometry is not None and len(geometry) == 1
                size_text = geometry.findtext("box/size")
                assert size_text is not None, "non-box collision cannot be silently omitted"
                size = [float(value) for value in size_text.split()]
                assert len(size) == 3 and all(math.isfinite(v) and v > 0 for v in size)
                boxes.append({
                    "name": model.get("name") + "/" + link.get("name") + "/" + collision.get("name"),
                    "model": model.get("name"),
                    "min": [p - s / 2 for p, s in zip(position, size)],
                    "max": [p + s / 2 for p, s in zip(position, size)],
                })
    assert boxes, "arena has no static box collisions"
    return boxes


def lidar_height(robot_xml: str, floor_z: float) -> float:
    """Derive the settled scan plane from this rover's wheel supports and scan joint."""
    robot = ET.fromstring(robot_xml)
    scan = robot.find("joint[@name='scan_joint']")
    assert scan is not None and scan.find("parent").get("link") == "base_link"
    origin = scan.find("origin")
    assert all(abs(float(v)) < 1e-12 for v in origin.get("rpy", "0 0 0").split())
    scan_xyz = [float(v) for v in origin.get("xyz").split()]
    supports = []
    for joint in robot.findall("joint"):
        child = joint.find("child").get("link")
        if not child.endswith("_wheel"):
            continue
        assert joint.find("parent").get("link") == "base_link"
        cylinder = robot.find(f"link[@name='{child}']/collision/geometry/cylinder")
        assert cylinder is not None, "wheel support is no longer a cylinder"
        radius = float(cylinder.get("radius"))
        joint_z = float(joint.find("origin").get("xyz").split()[2])
        supports.append(radius - joint_z)
    assert len(supports) == 4 and max(supports) - min(supports) < 1e-9
    sensor_pose = robot.find("gazebo[@reference='scan_link']/sensor/pose")
    assert sensor_pose is None, "nonzero sensor pose needs an explicit geometry update"
    return floor_z + max(supports) + scan_xyz[2]


def make_map(world_path: Path, robot_xml: str, output: Path, resolution=0.05) -> dict:
    """Rasterize collision boxes at scan height and flood-fill the origin's room."""
    boxes = read_static_boxes(world_path)
    floors = [box for box in boxes if box["model"] == "floor"]
    assert len(floors) == 1, "expected exactly one floor collision"
    floor = floors[0]
    height_z = lidar_height(robot_xml, floor["max"][2])
    obstacles = [box for box in boxes if box["min"][2] <= height_z <= box["max"][2]]
    assert obstacles and floor not in obstacles, "invalid scan plane"
    origin = floor["min"][:2]
    dimensions = [(floor["max"][i] - origin[i]) / resolution for i in (0, 1)]
    assert all(abs(value - round(value)) < 1e-8 for value in dimensions)
    width, height = map(round, dimensions)
    assert 0 < width <= 1000 and 0 < height <= 1000
    # Grid storage starts at the lower left; PGM rows are flipped only on writing.
    cells = bytearray([205]) * (width * height)
    for box in obstacles:
        lower = [math.floor((box["min"][i] - origin[i]) / resolution + 1e-9) for i in (0, 1)]
        upper = [math.ceil((box["max"][i] - origin[i]) / resolution - 1e-9) for i in (0, 1)]
        assert 0 <= lower[0] < upper[0] <= width and 0 <= lower[1] < upper[1] <= height
        for y in range(lower[1], upper[1]):
            for x in range(lower[0], upper[0]):
                cells[y * width + x] = 0
    start_x, start_y = [math.floor(-coordinate / resolution) for coordinate in origin]
    assert 0 <= start_x < width and 0 <= start_y < height
    start = start_y * width + start_x
    assert cells[start] == 205, "spawn is inside an obstacle"
    queue = deque([(start_x, start_y)])
    cells[start] = 254
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and cells[ny * width + nx] == 205:
                cells[ny * width + nx] = 254
                queue.append((nx, ny))
    # Open/broken perimeter must not silently turn outside space into known free space.
    assert all(cells[y * width + x] != 254 for y in (0, height - 1) for x in range(width))
    assert all(cells[y * width + x] != 254 for x in (0, width - 1) for y in range(height))
    output.mkdir(parents=True, exist_ok=True)
    pgm = output / "arena.pgm"
    pgm.write_bytes(f"P5\n{width} {height}\n255\n".encode() + b"".join(
        cells[y * width:(y + 1) * width] for y in reversed(range(height))))
    map_yaml = output / "arena.yaml"
    map_yaml.write_text(
        f"image: arena.pgm\nmode: trinary\nresolution: {resolution}\n"
        f"origin: [{origin[0]}, {origin[1]}, 0.0]\nnegate: 0\n"
        "occupied_thresh: 0.65\nfree_thresh: 0.25\n")
    return {
        "yaml": str(map_yaml), "resolution": resolution, "origin": origin,
        "width": width, "height": height, "lidar_height_m": height_z,
        "obstacles": obstacles, "occupied_cells": cells.count(0),
        "free_cells": cells.count(254), "unknown_cells": cells.count(205),
        "pgm_sha256": hashlib.sha256(pgm.read_bytes()).hexdigest(),
    }


def check_corridor(map_info: dict, half_x: float, half_y: float, goal_x=0.6) -> None:
    """Reject a goal whose straight swept footprint overlaps an actual SDF obstacle."""
    assert math.isfinite(half_x) and math.isfinite(half_y) and half_x > 0 and half_y > 0
    for box in map_info["obstacles"]:
        overlaps_x = box["min"][0] < goal_x + half_x and box["max"][0] > -half_x
        overlaps_y = box["min"][1] < half_y and box["max"][1] > -half_y
        assert not (overlaps_x and overlaps_y), f"goal corridor intersects {box['name']}"


def navigation_lifecycle_nodes(launch_file: Path) -> list[str]:
    """Read the installed Jazzy launch's actual managed server list."""
    for item in ast.walk(ast.parse(launch_file.read_text())):
        if isinstance(item, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "lifecycle_nodes"
                for target in item.targets):
            result = ast.literal_eval(item.value)
            assert isinstance(result, list) and result and all(isinstance(n, str) for n in result)
            return result
    raise AssertionError("cannot determine lifecycle nodes from installed Nav2 launch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=240.0,
                        help="Total wall-clock budget including cleanup, 180 to 240 seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 180 <= args.timeout <= 240:
        parser.error("--timeout must be between 180 and 240 seconds")
    output = args.evidence.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"status": "failed", "checks": {}, "errors": [], "commands": [],
              "timeout_sec": args.timeout}
    started = time.monotonic()
    # Three owned groups need at most 15 seconds each, plus a second for reporting.
    run_deadline = started + args.timeout - 46.0

    def save_report():
        report["elapsed_sec"] = round(time.monotonic() - started, 3)
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        from ament_index_python.packages import get_package_share_directory
        import rclpy
        from rclpy.duration import Duration
        from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
        from rclpy.signals import SignalHandlerOptions
        from rclpy.time import Time
        from action_msgs.msg import GoalStatus, GoalStatusArray
        from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
        from lifecycle_msgs.msg import State
        from lifecycle_msgs.srv import GetState
        from rcl_interfaces.srv import GetParameters
        from nav_msgs.msg import OccupancyGrid, Odometry
        from rosgraph_msgs.msg import Clock
        from sensor_msgs.msg import LaserScan
        from std_msgs.msg import String
        from tf2_ros import Buffer, TransformListener
        import yaml
        assert os.environ.get("ROS_DISTRO") == "jazzy", "source ROS 2 Jazzy first"
        shares = {name: Path(get_package_share_directory(name))
                  for name in ("simple_rover", "nav2_bringup", "nav2_programming")}
        missing = [command for command in ("ros2", "ps") if shutil.which(command) is None]
        if missing:
            raise ImportError(f"missing commands: {missing}")
    except (ImportError, LookupError, AssertionError) as error:
        report["errors"].append(f"ROS runtime unavailable: {error}")
        save_report()
        return 69

    os.environ["ROS_DOMAIN_ID"] = str(100 + os.getpid() % 100)
    os.environ["GZ_PARTITION"] = f"jazzy_navigation_{os.getpid()}"
    os.environ["ROS2CLI_DISABLE_DAEMON"] = "1"
    os.environ["ROS_LOG_DIR"] = str(output / "ros_logs")
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    report["environment"] = {key: os.environ[key]
                             for key in ("ROS_DISTRO", "ROS_DOMAIN_ID", "GZ_PARTITION")}
    processes = {}
    node = None
    listener = None
    initialized = False
    messages, counts, first_stamps, last_stamps = {}, {}, {}, {}
    lifecycle_states, statuses = {}, {}

    def interrupted(signum, _frame):
        raise InterruptedError(f"checker received signal {signum}")

    previous_handlers = {sig: signal.signal(sig, interrupted)
                         for sig in (signal.SIGINT, signal.SIGTERM)}
    with ExitStack() as stack:
        try:
            world = shares["simple_rover"] / "worlds" / "rover_arena.sdf"
            shutil.copyfile(world, output / "source_world.sdf")
            params_path = shares["simple_rover"] / "config" / "nav2_params.yaml"
            shutil.copyfile(params_path, output / "source_nav2_params.yaml")
            params = yaml.safe_load(params_path.read_text())
            managed = ["map_server", "amcl"] + navigation_lifecycle_nodes(
                shares["nav2_bringup"] / "launch" / "navigation_launch.py")
            managed = list(dict.fromkeys(managed))
            report["expected_lifecycle_nodes"] = managed

            def launch(name, command):
                report["commands"].append({"name": name, "argv": command})
                (output / "commands.json").write_text(json.dumps(report["commands"], indent=2) + "\n")
                log = stack.enter_context((output / f"{name}.log").open("w"))
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                processes[name] = process
                return process

            launch("simulation", ["ros2", "launch", "simple_rover", "spawn_robot.launch.py",
                                 "gui:=false", "headless:=true", "rviz:=false",
                                 "camera:=none", "x:=0.0", "y:=0.0", "yaw:=0.0"])
            rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
            initialized = True
            node = rclpy.create_node("final_project_navigation_probe")
            node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
            buffer = Buffer(cache_time=Duration(seconds=30))
            listener = TransformListener(buffer, node)
            subscriptions = []

            def remember(topic, message):
                messages[topic] = message
                counts[topic] = counts.get(topic, 0) + 1
                stamp = message.clock if topic == "/clock" else getattr(
                    getattr(message, "header", None), "stamp", None)
                if stamp is not None:
                    value = stamp.sec * 1_000_000_000 + stamp.nanosec
                    first_stamps.setdefault(topic, value)
                    assert value >= last_stamps.get(topic, value), f"{topic} time went backwards"
                    last_stamps[topic] = value

            for topic, message_type in {"/clock": Clock, "/odom": Odometry, "/scan": LaserScan}.items():
                subscriptions.append(node.create_subscription(
                    message_type, topic, lambda msg, t=topic: remember(t, msg),
                    qos_profile_sensor_data))
            for topic, message_type in {"/robot_description": String, "/map": OccupancyGrid,
                                       "/amcl_pose": PoseWithCovarianceStamped}.items():
                subscriptions.append(node.create_subscription(
                    message_type, topic, lambda msg, t=topic: remember(t, msg),
                    QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)))

            def action_status(message):
                for status in message.status_list:
                    identifier = bytes(status.goal_info.goal_id.uuid).hex()
                    statuses.setdefault(identifier, [])
                    if not statuses[identifier] or statuses[identifier][-1] != status.status:
                        statuses[identifier].append(status.status)

            subscriptions.append(node.create_subscription(
                GoalStatusArray, "/navigate_to_pose/_action/status", action_status,
                QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)))
            moving_commands = []
            subscriptions.append(node.create_subscription(
                Twist, "/cmd_vel", lambda msg: moving_commands.append(
                    [msg.linear.x, msg.angular.z]) if abs(msg.linear.x) > 0.01 else None, 10))

            def spin_until(predicate, phase, seconds, tick=None):
                deadline = min(run_deadline, time.monotonic() + seconds)
                while time.monotonic() < deadline:
                    for name in ("simulation", "navigation"):
                        if name in processes and processes[name].poll() is not None:
                            raise AssertionError(f"{name} launch exited: {processes[name].returncode}")
                    if tick is not None:
                        tick()
                    rclpy.spin_once(node, timeout_sec=0.05)
                    if predicate():
                        return
                raise AssertionError(f"{phase} timed out; topics={counts}; lifecycle={lifecycle_states}")

            spin_until(lambda: all(counts.get(t, 0) >= 5 for t in ("/clock", "/odom", "/scan"))
                       and "/robot_description" in messages
                       and last_stamps.get("/clock", 0) > first_stamps.get("/clock", 0),
                       "simulation readiness", 60)
            robot_xml = messages["/robot_description"].data
            (output / "source_robot.urdf").write_text(robot_xml)
            map_info = make_map(world, robot_xml, output / "map")
            report["checks"]["source_map"] = map_info
            costmap = params["local_costmap"]["local_costmap"]["ros__parameters"]
            footprint = json.loads(costmap["footprint"])
            padding = costmap["footprint_padding"]
            half_x = max(abs(p[0]) for p in footprint) + padding
            half_y = max(abs(p[1]) for p in footprint) + padding
            check_corridor(map_info, half_x, half_y)
            report["checks"]["clear_swept_footprint_m"] = [half_x, half_y]
            launch("navigation", ["ros2", "launch", "simple_rover", "navigation.launch.py",
                                  "map:=" + map_info["yaml"], "use_sim_time:=true"])

            clients = {name: node.create_client(GetState, "/" + name + "/get_state")
                       for name in managed}
            pending, last_queries = {}, {}
            map_parameter_client = node.create_client(GetParameters, '/map_server/get_parameters')
            map_parameter_future = None
            initial_pub = node.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)
            last_initial = 0.0
            initial_count = 0

            def tick_readiness():
                nonlocal last_initial, initial_count, map_parameter_future
                now = time.monotonic()
                for name, client in clients.items():
                    if name in pending:
                        future, submitted = pending[name]
                        if future.done():
                            response = future.result()
                            if response is not None:
                                lifecycle_states[name] = response.current_state.id
                            del pending[name]
                        elif now - submitted > 1.0:
                            client.remove_pending_request(future)
                            del pending[name]
                    if (name not in pending and client.service_is_ready()
                            and now - last_queries.get(name, 0) >= 0.5):
                        pending[name] = (client.call_async(GetState.Request()), now)
                        last_queries[name] = now
                if (map_parameter_future is None
                        and lifecycle_states.get('map_server') == State.PRIMARY_STATE_ACTIVE
                        and map_parameter_client.service_is_ready()):
                    request = GetParameters.Request()
                    request.names = ['yaml_filename']
                    map_parameter_future = map_parameter_client.call_async(request)
                if map_parameter_future is not None and map_parameter_future.done():
                    response = map_parameter_future.result()
                    assert response is not None and len(response.values) == 1
                    actual_path = response.values[0].string_value
                    report['checks']['map_server_yaml_filename'] = actual_path
                    assert actual_path == map_info['yaml'], (
                        f'map_server loaded wrong yaml_filename: {actual_path!r}; '
                        f'expected {map_info["yaml"]!r}')
                # Stop resetting AMCL as soon as it has localized; never reset during movement.
                if (lifecycle_states.get("amcl") == State.PRIMARY_STATE_ACTIVE
                        and "/amcl_pose" not in messages and now - last_initial >= 1.0
                        and initial_pub.get_subscription_count() > 0):
                    initial = PoseWithCovarianceStamped()
                    initial.header.frame_id = "map"
                    initial.header.stamp = node.get_clock().now().to_msg()
                    initial.pose.pose.orientation.w = 1.0
                    initial.pose.covariance[0] = 0.0025
                    initial.pose.covariance[7] = 0.0025
                    initial.pose.covariance[35] = 0.0025
                    initial_pub.publish(initial)
                    initial_count += 1
                    last_initial = now

            spin_until(lambda: all(lifecycle_states.get(n) == State.PRIMARY_STATE_ACTIVE for n in managed)
                       and "/map" in messages and "/amcl_pose" in messages
                       and "map_server_yaml_filename" in report["checks"]
                       and buffer.can_transform("map", "base_link", Time()),
                       "AMCL/Nav2 readiness", 75, tick_readiness)
            assert initial_count > 0, "no initial pose was sent"
            report["checks"]["active_lifecycle_nodes"] = sorted(lifecycle_states)
            report["checks"]["initial_pose_publications"] = initial_count
            grid = messages["/map"]
            assert (grid.info.width, grid.info.height) == (map_info["width"], map_info["height"])
            assert abs(grid.info.resolution - map_info["resolution"]) < 1e-7
            assert sum(value == 100 for value in grid.data) == map_info["occupied_cells"]
            start_odom = messages["/odom"]
            assert start_odom.header.frame_id == "odom" and start_odom.child_frame_id == "base_link"
            start_xy = [start_odom.pose.pose.position.x, start_odom.pose.pose.position.y]
            assert math.hypot(*start_xy) < 0.05, f"unexpected spawn odometry: {start_xy}"
            start_stamp = last_stamps["/odom"]
            goal = [0.6, 0.0, 0.0]
            report["goal_map_xy_yaw"] = goal
            demo = launch("navigate_to_pose", [
                "ros2", "run", "nav2_programming", "navigate_to_pose", "--ros-args",
                "-p", "use_sim_time:=true", "-p", "goal:=[0.6, 0.0, 0.0]",
                "-p", "startup_timeout_sec:=20.0", "-p", "timeout_sec:=75.0"])
            spin_until(lambda: demo.poll() is not None, "navigation demo", 95)
            report["checks"]["demo_exit_code"] = demo.returncode
            assert demo.returncode == 0, f"navigation demo failed with exit {demo.returncode}"
            end_count = counts["/odom"]
            spin_until(lambda: counts["/odom"] >= end_count + 3 and any(
                GoalStatus.STATUS_SUCCEEDED in history for history in statuses.values()),
                "fresh odometry and successful action result", 10)
            assert any(GoalStatus.STATUS_EXECUTING in history for history in statuses.values()), (
                "never observed an accepted/executing navigation goal")
            assert moving_commands, "Nav2 never published a nonzero Twist to /cmd_vel"
            assert last_stamps["/odom"] > start_stamp, "odometry timestamps stopped"
            end_xy = [messages["/odom"].pose.pose.position.x, messages["/odom"].pose.pose.position.y]
            distance = math.dist(start_xy, end_xy)
            assert distance >= 0.35, f"successful action without required rover motion: {distance}"
            transform = buffer.lookup_transform("map", "base_link", Time())
            tf_stamp = transform.header.stamp.sec * 1_000_000_000 + transform.header.stamp.nanosec
            assert tf_stamp > start_stamp, "final map TF did not advance during navigation"
            assert abs(last_stamps["/clock"] - tf_stamp) < 500_000_000, "final map TF is stale"
            position, q = transform.transform.translation, transform.transform.rotation
            yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            error_xy = math.hypot(position.x - goal[0], position.y - goal[1])
            error_yaw = abs(math.atan2(math.sin(yaw - goal[2]), math.cos(yaw - goal[2])))
            checker = params["controller_server"]["ros__parameters"]["general_goal_checker"]
            assert error_xy <= checker["xy_goal_tolerance"], f"final map position error {error_xy}"
            assert error_yaw <= checker["yaw_goal_tolerance"], f"final map yaw error {error_yaw}"
            report["checks"]["navigation"] = {
                "start_odom_xy": start_xy, "end_odom_xy": end_xy, "displacement_m": distance,
                "final_map_xy_yaw": [position.x, position.y, yaw],
                "final_tf_stamp_ns": tf_stamp,
                "position_error_m": error_xy, "yaw_error_rad": error_yaw,
                "configured_goal_tolerances": checker,
                "nonzero_cmd_vel_messages": len(moving_commands)}
            report["status"] = "passed"
        except Exception as error:
            report["errors"].append(f"{type(error).__name__}: {error}")
        finally:
            for sig in previous_handlers:
                signal.signal(sig, signal.SIG_IGN)
            # Stop action client, then navigation, then the simulation they command.
            survivors = {}
            for name, process in reversed(list(processes.items())):
                try:
                    survivors[name] = stop_owned(process)
                except Exception as error:
                    survivors[name] = ["cleanup failed"]
                    report["errors"].append(f"{name} cleanup: {error}")
            report["survivors"] = survivors
            if any(survivors.values()):
                report["status"] = "failed"
                report["errors"].append("owned processes survived cleanup")
            try:
                if listener is not None:
                    listener.unregister()
                if node is not None:
                    node.destroy_node()
                if initialized and rclpy.ok():
                    rclpy.shutdown()
            except Exception as error:
                report["status"] = "failed"
                report["errors"].append(f"ROS shutdown failed: {error}")
            report["checks"]["message_counts"] = counts
            report["checks"]["action_status_history"] = statuses
            if time.monotonic() - started > args.timeout:
                report["status"] = "failed"
                report["errors"].append("total wall-clock budget exceeded")
            save_report()
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
