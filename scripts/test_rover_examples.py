from __future__ import annotations

import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ROVERS = ROOT / "examples/ros2_ws/src/tutorial_bot_description/urdf/rovers"
ODOM_TO_PATH = ROOT / "examples/ros2_ws/src/tutorial_bot_bringup/scripts/odom_to_path"


def expand(filename: str) -> ET.Element:
    completed = subprocess.run(
        ["xacro", str(ROVERS / filename)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return ET.fromstring(completed.stdout)


def plugin(root: ET.Element, class_name: str) -> ET.Element:
    result = root.find(f".//plugin[@name='{class_name}']")
    assert result is not None
    return result


def joint_names(root: ET.Element) -> set[str]:
    return {joint.attrib["name"] for joint in root.findall("joint")}


def test_four_wheel_diff_drive_uses_both_axles() -> None:
    robot = expand("rover_diff.urdf.xacro")
    drive = plugin(robot, "gz::sim::systems::DiffDrive")
    expected_left = {"front_left_wheel_joint", "rear_left_wheel_joint"}
    expected_right = {"front_right_wheel_joint", "rear_right_wheel_joint"}

    assert {item.text for item in drive.findall("left_joint")} == expected_left
    assert {item.text for item in drive.findall("right_joint")} == expected_right
    assert expected_left | expected_right <= joint_names(robot)
    assert float(drive.findtext("wheel_separation", "nan")) == 0.62
    assert float(drive.findtext("wheel_radius", "nan")) == 0.1
    assert drive.findtext("frame_id") == "odom"
    assert drive.findtext("child_frame_id") == "base_footprint"


def test_ackermann_rover_separates_traction_and_steering_joints() -> None:
    robot = expand("rover_ackermann.urdf.xacro")
    drive = plugin(robot, "gz::sim::systems::AckermannSteering")
    expected = {
        "left_joint": "rear_left_wheel_joint",
        "right_joint": "rear_right_wheel_joint",
        "left_steering_joint": "front_left_steering_joint",
        "right_steering_joint": "front_right_steering_joint",
    }

    for tag, joint_name in expected.items():
        assert drive.findtext(tag) == joint_name
        assert joint_name in joint_names(robot)
    assert float(drive.findtext("wheel_base", "nan")) == 0.56
    assert float(drive.findtext("kingpin_width", "nan")) == 0.62
    assert float(drive.findtext("wheel_separation", "nan")) == 0.62
    assert float(drive.findtext("steering_limit", "nan")) == 0.6
    assert drive.findtext("frame_id") == "odom"
    assert drive.findtext("child_frame_id") == "base_footprint"


def test_odom_path_node_is_installed_as_an_executable() -> None:
    assert os.access(ODOM_TO_PATH, os.X_OK)
    completed = subprocess.run(
        ["ros2", "pkg", "prefix", "tutorial_bot_bringup"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    installed = (
        Path(completed.stdout.strip())
        / "lib"
        / "tutorial_bot_bringup"
        / "odom_to_path"
    )
    assert installed.is_file()
    assert os.access(installed, os.X_OK)
