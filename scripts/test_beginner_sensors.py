from __future__ import annotations

import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "examples/ros2_ws/src/tutorial_bot_description/urdf/stages/04-sensors-final.xacro"
GALLERY = ROOT / "examples/ros2_ws/src/tutorial_bot_description/urdf/stages/05-sensor-gallery.xacro"
EXPECTATIONS = ROOT / "examples/ros2_ws/src/tutorial_bot_gazebo/config/sensor_expectations.yaml"
GALLERY_BRIDGE = ROOT / "examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-sensor-gallery.yaml"


def expanded(path: Path) -> ET.Element:
    result = subprocess.run(
        ["xacro", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return ET.fromstring(result.stdout)


def expanded_robot() -> ET.Element:
    return expanded(STAGE)


def sensor(root: ET.Element, name: str) -> ET.Element:
    result = root.find(f".//sensor[@name='{name}']")
    assert result is not None
    return result


def text(node: ET.Element, path: str) -> str:
    result = node.findtext(path)
    assert result is not None
    return result


def test_installed_stage_and_expectations_describe_the_same_sensor_behavior() -> None:
    # Given: the installed final stage and the runtime expectation document.
    robot = expanded_robot()
    expected = yaml.safe_load(EXPECTATIONS.read_text(encoding="utf-8"))

    # When: sensor behavior is parsed from each machine-consumed source.
    lidar = sensor(robot, "lidar")
    camera = sensor(robot, "camera")
    imu = sensor(robot, "imu")
    lidar_type = lidar.attrib["type"]
    lidar_rate = float(text(lidar, "update_rate"))
    lidar_samples = int(text(lidar, "lidar/scan/horizontal/samples"))
    lidar_min_angle = float(text(lidar, "lidar/scan/horizontal/min_angle"))
    lidar_max_angle = float(text(lidar, "lidar/scan/horizontal/max_angle"))
    lidar_min_range = float(text(lidar, "lidar/range/min"))
    lidar_max_range = float(text(lidar, "lidar/range/max"))
    lidar_resolution = float(text(lidar, "lidar/range/resolution"))
    lidar_noise = float(text(lidar, "lidar/noise/stddev"))

    # Then: the parsed values agree, including the inclusive endpoint convention.
    assert lidar_type == "gpu_lidar"
    assert lidar_rate == expected["lidar"]["expected_rate_hz"]
    assert lidar_samples == expected["lidar"]["samples"]
    assert lidar_min_angle == pytest.approx(expected["lidar"]["min_angle_rad"], abs=1e-11)
    assert lidar_max_angle == pytest.approx(expected["lidar"]["max_angle_rad"], abs=1e-11)
    assert lidar_min_range == expected["lidar"]["min_range_m"]
    assert lidar_max_range == expected["lidar"]["max_range_m"]
    assert lidar_resolution == 0.01
    assert lidar_noise == expected["lidar"]["noise_stddev_m"]
    increment = (lidar_max_angle - lidar_min_angle) / (lidar_samples - 1)
    assert math.degrees(increment) == pytest.approx(360 / 359)
    assert camera.attrib["type"] == "rgbd_camera"
    assert float(text(camera, "update_rate")) == expected["camera"]["expected_rate_hz"]
    assert int(text(camera, "camera/image/width")) == expected["camera"]["width_px"]
    assert int(text(camera, "camera/image/height")) == expected["camera"]["height_px"]
    assert float(text(camera, "camera/horizontal_fov")) == expected["camera"]["hfov_rad"]
    assert float(text(camera, "camera/clip/near")) == expected["camera"]["near_clip_m"]
    assert float(text(camera, "camera/clip/far")) == expected["camera"]["far_clip_m"]
    assert float(text(imu, "update_rate")) == expected["imu"]["expected_rate_hz"]
    imu_noise = [float(item.text or "nan") for item in imu.findall(".//stddev")]
    assert imu_noise == [expected["imu"]["noise_stddev"]] * 6


def test_sensor_gallery_topics_frames_and_bridge_stay_aligned() -> None:
    robot = expanded(GALLERY)
    expected_topics = {
        "lidar": "/tutorial_bot/lidar",
        "lidar_3d": "/tutorial_bot/lidar_3d",
        "camera": "/tutorial_bot/camera",
        "mono_camera": "/tutorial_bot/mono/image",
        "stereo_left": "/tutorial_bot/stereo/left/image",
        "stereo_right": "/tutorial_bot/stereo/right/image",
        "fisheye_camera": "/tutorial_bot/fisheye/image",
        "imu": "/tutorial_bot/imu",
    }

    for name, expected_topic in expected_topics.items():
        assert sensor(robot, name).findtext("topic") == expected_topic
    assert sensor(robot, "lidar").findtext("pose") == "0 0 0 0 0 0"

    mappings = yaml.safe_load(GALLERY_BRIDGE.read_text(encoding="utf-8"))
    gz_to_ros = {
        item.get("gz_topic_name", item.get("topic_name")): item.get(
            "ros_topic_name", item.get("topic_name")
        )
        for item in mappings
    }
    assert gz_to_ros["/tutorial_bot/mono/camera_info"] == "/mono/camera_info"
    assert gz_to_ros["/tutorial_bot/stereo/left/camera_info"] == "/stereo/left/camera_info"
    assert gz_to_ros["/tutorial_bot/stereo/right/camera_info"] == "/stereo/right/camera_info"
    assert gz_to_ros["/tutorial_bot/fisheye/camera_info"] == "/fisheye/camera_info"
    assert gz_to_ros["/tutorial_bot/camera/depth_image"] == "/camera/depth/image"


def test_beginner_sensor_routes_explain_the_parsed_runtime_contract() -> None:
    # Given: the four final beginner routes.
    requirements = {
        "08-sensors.md": ("360 - 1", "`inf`", "100 Hz", "30 Hz"),
        "09-gazebo-fuel.md": ("GZ_FUEL_CACHE_PATH", "GZ_SIM_RESOURCE_PATH"),
        "10-ros-gz-bridge.md": ("ros_gz_bridge", "image_bridge", "dependency"),
        "11_project-tutorial-bot.md": ("/scan", "/imu", "/clock"),
    }

    # When: each page is inspected for the concepts that explain the parsed contract.
    for filename, markers in requirements.items():
        page = (ROOT / "docs/03_beginner" / filename).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in page


def test_beginner_sensor_routes_have_registered_visual_learning_evidence() -> None:
    # Given: the Task 7 visual manifest.
    fragment = ROOT / "docs/assets/manifests/task-7.yaml"

    # When: registered routes are parsed from the manifest.
    assets = yaml.safe_load(fragment.read_text(encoding="utf-8"))["assets"]
    routes = {asset["route"] for asset in assets}

    # Then: every route has a registered figure and caption in its page.
    for filename in (
        "08-sensors.md",
        "09-gazebo-fuel.md",
        "10-ros-gz-bridge.md",
        "11_project-tutorial-bot.md",
    ):
        page = (ROOT / "docs/03_beginner" / filename).read_text(encoding="utf-8")
        route = f"03_beginner/{filename.removesuffix('.md')}/"
        assert route in routes
        assert '<figure class="course-figure"' in page
        assert "<figcaption>그림" in page
