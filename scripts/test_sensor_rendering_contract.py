"""Frame/geometry regressions; these checks do not claim to render Gazebo or RViz."""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "examples/ros2_ws/src"
BRINGUP = SRC / "tutorial_bot_bringup"
DESCRIPTION = SRC / "tutorial_bot_description/urdf"
EXPECTATIONS = SRC / "tutorial_bot_gazebo/config/sensor_expectations.yaml"


def robot(filename: str = "tutorial_bot.urdf.xacro") -> ET.Element:
    result = subprocess.run(
        ["xacro", str(DESCRIPTION / filename)],
        check=True, capture_output=True, text=True,
    )
    return ET.fromstring(result.stdout)


def origin_transform(origin: ET.Element | None) -> list[list[float]]:
    attributes = origin.attrib if origin is not None else {}
    x, y, z = map(float, attributes.get("xyz", "0 0 0").split())
    roll, pitch, yaw = map(float, attributes.get("rpy", "0 0 0").split())
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr, x],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr, y],
        [-sp, cp * sr, cp * cr, z],
        [0.0, 0.0, 0.0, 1.0],
    ]


def compose(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


@pytest.mark.parametrize("filename", [
    "tutorial_bot.urdf.xacro",
    "stages/02-wheels-and-joints.xacro",
    "stages/03-diff-drive.xacro",
    "stages/04-sensors-final.xacro",
    "stages/05-sensor-gallery.xacro",
])
def test_center_of_mass_has_a_margin_inside_the_three_contact_points(filename: str) -> None:
    model = robot(filename)
    poses = {"base_link": origin_transform(None)}
    pending = list(model.findall("joint"))
    while pending:
        resolved = [joint for joint in pending if joint.find("parent").attrib["link"] in poses]
        assert resolved, "Every link must connect to base_link."
        for joint in resolved:
            parent, child = joint.find("parent").attrib["link"], joint.find("child").attrib["link"]
            poses[child] = compose(poses[parent], origin_transform(joint.find("origin")))
            pending.remove(joint)

    total_mass, moment = 0.0, [0.0, 0.0, 0.0]
    for link in model.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        mass = float(inertial.find("mass").attrib["value"])
        pose = compose(poses[link.attrib["name"]], origin_transform(inertial.find("origin")))
        total_mass += mass
        moment = [value + mass * pose[axis][3] for axis, value in enumerate(moment)]
    center = [value / total_mass for value in moment]

    # At the initial joint angles these round contacts project to their centers.
    # Traverse left wheel -> rear caster -> right wheel counterclockwise.
    support = []
    for name in ("left_wheel_link", "caster_link", "right_wheel_link"):
        collision = model.find(f"link[@name='{name}']/collision")
        pose = compose(poses[name], origin_transform(collision.find("origin")))
        support.append((pose[0][3], pose[1][3]))
    margins = []
    for (ax, ay), (bx, by) in zip(support, support[1:] + support[:1]):
        margins.append(((bx - ax) * (center[1] - ay) - (by - ay) * (center[0] - ax)) / math.hypot(bx - ax, by - ay))
    assert min(margins) > 0.01, f"{filename}: COM={center}, support edge margins={margins}"


@pytest.mark.parametrize("filename", [
    "bridge.yaml", "bridge-intermediate.yaml", "bridge-sensor-gallery.yaml",
    "bridge-multi-robot.yaml",
])
def test_rgbd_points_use_the_frame_of_their_actual_xyz_axes(filename: str) -> None:
    # gz-rendering8 emits x forward and gz-sensors8 copies those XYZ values.
    # Merely attaching an optical frame id would rotate an obstacle in RViz.
    mappings = yaml.safe_load((BRINGUP / "config" / filename).read_text())
    clouds = [m for m in mappings if m.get("gz_topic_name", "").endswith("/camera/points")]
    assert clouds
    for mapping in clouds:
        topic = mapping["ros_topic_name"]
        prefix = topic.removesuffix("camera/points").lstrip("/")
        assert mapping.get("frame_id") == prefix + "camera_link"
        assert mapping["direction"] == "GZ_TO_ROS"
        assert mapping["qos_profile"] == "SENSOR_DATA"
        image_mappings = [m for m in mappings if m.get("ros_topic_name") == "/" + prefix + "camera/camera_info"]
        assert len(image_mappings) == 1
        assert "frame_id" not in image_mappings[0]


def test_camera_optical_joint_rotates_forward_right_down_into_body_axes() -> None:
    joint = robot().find("joint[@name='camera_optical_joint']")
    assert joint is not None
    roll, pitch, yaw = map(float, joint.find("origin").attrib["rpy"].split())
    cr, sr, cp, sp, cy, sy = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw)
    # Rz(yaw) Ry(pitch) Rx(roll), columns are optical x, y, z in body axes.
    columns = [
        (cy * cp, sy * cp, -sp),
        (cy * sp * sr - sy * cr, sy * sp * sr + cy * cr, cp * sr),
        (cy * sp * cr + sy * sr, sy * sp * cr - cy * sr, cp * cr),
    ]
    for actual, expected in zip(columns, [(0, -1, 0), (0, 0, -1), (1, 0, 0)]):
        assert actual == pytest.approx(expected, abs=1e-9)


def test_namespaced_controller_frames_join_the_state_publisher_tree_once() -> None:
    configs = yaml.safe_load((SRC / "tutorial_bot_control/config/multi_robot_controllers.yaml").read_text())
    for name in ("robot1", "robot2"):
        params = configs[f"/{name}/diff_drive_controller"]["ros__parameters"]
        # Jazzy defaults to adding the controller namespace when enabled.
        prefix = params.get("tf_frame_prefix", "") or name + "/"
        if not params.get("tf_frame_prefix_enable", True):
            prefix = ""
        assert prefix + params["base_frame_id"] == name + "/base_link"
        assert prefix + params["odom_frame_id"] == name + "/odom"
        assert "use_stamped_vel" not in params


def test_costmap_footprint_contains_the_wheel_collision_extents() -> None:
    model = robot()
    config = yaml.safe_load((BRINGUP / "config/nav2_params.yaml").read_text())
    for name in ("local_costmap", "global_costmap"):
        params = config[name][name]["ros__parameters"]
        footprint = yaml.safe_load(params["footprint"])
        max_y, min_y = max(p[1] for p in footprint), min(p[1] for p in footprint)
        for side in ("left", "right"):
            joint = model.find(f"joint[@name='{side}_wheel_joint']/origin")
            cylinder = model.find(f"link[@name='{side}_wheel_link']/collision/geometry/cylinder")
            y = float(joint.attrib["xyz"].split()[1])
            half_width = float(cylinder.attrib["length"]) / 2
            assert min_y <= y - half_width
            assert max_y >= y + half_width


def ray_box_distance(origin: tuple[float, float], angle: float, box: tuple[float, float, float, float]) -> float:
    low, high = -math.inf, math.inf
    for position, direction, lower, upper in zip(origin, (math.cos(angle), math.sin(angle)), box[:2], box[2:]):
        if abs(direction) < 1e-12:
            if not lower <= position <= upper:
                return math.inf
            continue
        a, b = (lower - position) / direction, (upper - position) / direction
        low, high = max(low, min(a, b)), min(high, max(a, b))
    return max(0.0, low) if high >= max(0.0, low) else math.inf


def test_lidar_reference_ranges_include_the_offset_mount_and_the_visible_target() -> None:
    config = yaml.safe_load(EXPECTATIONS.read_text())
    world = ET.parse(SRC / "tutorial_bot_gazebo/worlds/sensor-test.sdf")
    model = robot()
    mount = model.find("joint[@name='lidar_joint']/origin")
    mx, my, mz = map(float, mount.attrib["xyz"].split())
    sensor_height = 0.12 + mz
    boxes = []
    for item in world.findall(".//world/model"):
        xyz = [float(v) for v in item.findtext("pose", "0 0 0 0 0 0").split()[:3]]
        for visual in item.findall("link/visual"):
            shape = visual.find("geometry/box/size")
            if shape is None:
                continue
            offset = [float(v) for v in visual.findtext("pose", "0 0 0 0 0 0").split()[:3]]
            x, y, z = [a + b for a, b in zip(xyz, offset)]
            sx, sy, sz = map(float, shape.text.split())
            if z - sz / 2 <= sensor_height <= z + sz / 2:
                boxes.append((x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2))
    scan = config["lidar"]
    expected = []
    for i in range(scan["samples"]):
        angle = scan["min_angle_rad"] + i * (scan["max_angle_rad"] - scan["min_angle_rad"]) / (scan["samples"] - 1)
        expected.append(min(ray_box_distance((mx, my), angle, box) for box in boxes))
    assert scan["truth_ranges_m"] == pytest.approx(expected, abs=1e-8)
    assert expected[179] == pytest.approx(1.70, abs=0.001)


@pytest.mark.parametrize("filename", ["tutorial_bot.rviz", "rover.rviz"])
def test_rviz_can_receive_the_description_when_opened_after_robot_spawn(filename: str) -> None:
    config = yaml.safe_load((BRINGUP / "rviz" / filename).read_text())
    display = next(d for d in config["Visualization Manager"]["Displays"] if d["Class"] == "rviz_default_plugins/RobotModel")
    assert display["Description Topic"]["Durability Policy"] == "Transient Local"
