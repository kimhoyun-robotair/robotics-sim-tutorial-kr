"""Check camera geometry and robot stability after expanding the actual Xacros.

Gazebo Classic's depth plugin writes optical XYZ and uses (width-1)/2 when
unprojecting pixels. Its default CameraInfo principal point differs by one
pixel. A stereo baseline must also describe the same physical camera centres
in the sensor poses, TF tree, and right projection matrix.

Source: ros-simulation/gazebo_ros_pkgs, gazebo_plugins/src/gazebo_ros_camera.cpp
(ROS 2 branch, GazeboRosCamera::Load and OnNewDepthFrame).
"""
from __future__ import annotations

import math
import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import xacro
import xacro.substitution_args
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ros2_ws" / "src"
DESCRIPTION = SOURCE / "gazebo_tutorial_description" / "urdf"
IDENTITY = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


def vector(text="0 0 0"):
    return tuple(float(value) for value in text.split())


def rotation(rpy):
    roll, pitch, yaw = rpy
    cr, sr, cp, sp, cy, sy = (
        math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch),
        math.cos(yaw), math.sin(yaw))
    return ((cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
            (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
            (-sp, cp * sr, cp * cr))


def rotated(matrix, value):
    return tuple(sum(a * b for a, b in zip(row, value)) for row in matrix)


def compose(first, second):
    a, ar = first
    b, br = second
    rb = rotated(ar, b)
    return (tuple(x + y for x, y in zip(a, rb)),
            tuple(tuple(sum(ar[i][k] * br[k][j] for k in range(3))
                        for j in range(3)) for i in range(3)))


def origin(element):
    if element is None:
        return ((0., 0., 0.), IDENTITY)
    return vector(element.get("xyz", "0 0 0")), rotation(vector(element.get("rpy", "0 0 0")))


def frames(robot):
    children = {j.find("child").get("link") for j in robot.findall("joint")}
    roots = {link.get("name") for link in robot.findall("link")} - children
    assert len(roots) == 1
    result = {roots.pop(): ((0., 0., 0.), IDENTITY)}
    pending = list(robot.findall("joint"))
    while pending:
        progress = False
        for joint in pending[:]:
            parent = joint.find("parent").get("link")
            if parent not in result:
                continue
            result[joint.find("child").get("link")] = compose(result[parent], origin(joint.find("origin")))
            pending.remove(joint)
            progress = True
        assert progress, "URDF joints do not form one connected tree"
    return result


def expand(filename="sensor_bot.urdf.xacro", profile="all"):
    with patch.object(xacro.substitution_args, "_eval_find", lambda name: str(SOURCE / name)):
        rendered = xacro.process_file(str(DESCRIPTION / filename), mappings={"sensor_profile": profile})
    return ET.fromstring(rendered.toxml())


def expand_f1(**options):
    with patch.object(xacro.substitution_args, "_eval_find", lambda name: str(SOURCE / name)):
        rendered = xacro.process_file(
            str(SOURCE / "f1_robot_model/urdf/racecar.urdf"),
            mappings={name: str(value).lower() for name, value in options.items()})
    return ET.fromstring(rendered.toxml())


def xml_signature(element):
    """Compare model values while ignoring source indentation and comments."""
    return (element.tag, tuple(sorted(element.attrib.items())),
            (element.text or "").strip(), tuple(xml_signature(child) for child in element))


@pytest.mark.parametrize("profile", ["all", "cameras", "lidars", "minimal"])
def test_sensor_profiles_keep_the_existing_four_wheel_ackermann_vehicle(profile):
    vehicle, robot = expand("rover_ackermann.urdf.xacro"), expand(profile=profile)
    for tag in ("link", "joint"):
        actual = {element.get("name"): element for element in robot.findall(tag)}
        assert not any("caster" in name for name in actual)
        for original in vehicle.findall(tag):
            assert xml_signature(actual[original.get("name")]) == xml_signature(original)
    for tag in ("front_left_joint", "front_right_joint", "rear_left_joint", "rear_right_joint"):
        joint_name = robot.findtext(f"gazebo/plugin[@filename='libgazebo_ros_ackermann_drive.so']/{tag}")
        joint = robot.find(f"joint[@name='{joint_name}']")
        assert joint is not None and joint.get("type") == "continuous"
    for side in ("left", "right"):
        joint = robot.find(f"joint[@name='front_{side}_steering_joint']")
        assert joint is not None and joint.get("type") == "revolute"
        assert vector(joint.find("axis").get("xyz")) == (0., 0., 1.)
        assert float(joint.find("limit").get("lower")) < 0 < float(joint.find("limit").get("upper"))
    assert not robot.findall("gazebo/plugin[@filename='libgazebo_ros_diff_drive.so']")
    plugins = robot.findall("gazebo/plugin[@filename='libgazebo_ros_ackermann_drive.so']")
    assert len(plugins) == 1
    assert xml_signature(plugins[0]) == xml_signature(
        vehicle.find("gazebo/plugin[@filename='libgazebo_ros_ackermann_drive.so']"))


@pytest.mark.parametrize("depth,lidar", [(False, False), (True, False), (False, True), (True, True)])
def test_f1_optional_sensors_do_not_change_the_base_vehicle(depth, lidar):
    robot = expand_f1(depth_camera=depth, lidar_3d=lidar)
    expected = {"imu", "hokuyo_sensor"}
    if depth:
        expected.add("depth_camera_sensor")
    if lidar:
        expected.add("velodyne2-HDL32E")
    sensors = list(robot.iter("sensor"))
    names = [sensor.get("name") for sensor in sensors]
    assert len(names) == len(set(names))
    assert set(names) == expected
    transforms = frames(robot)
    for sensor in sensors:
        plugin = sensor.find("plugin")
        assert plugin is not None
        assert plugin.findtext("frame_name") in transforms
    assert ("camera_link_optical" in transforms) is depth
    assert ("lidar_3d_link" in transforms) is lidar
    assert not any("gps" in name for name in transforms)
    for tag in ("link", "joint"):
        actual = {element.get("name"): element for element in robot.findall(tag)}
        for original in expand_f1().findall(tag):
            assert xml_signature(actual[original.get("name")]) == xml_signature(original)
    assert len(robot.findall("joint[@type='continuous']")) == 4
    assert len(robot.findall("joint[@type='revolute']")) == 2


def test_f1_default_model_contains_only_imu_and_planar_lidar():
    robot = expand_f1()
    assert {sensor.get("name") for sensor in robot.iter("sensor")} == {"imu", "hokuyo_sensor"}
    lidar = next(sensor for sensor in robot.iter("sensor") if sensor.get("name") == "hokuyo_sensor")
    assert lidar.find("ray/scan/vertical") is None
    assert lidar.findtext("plugin/output_type") == "sensor_msgs/LaserScan"


def test_f1_building_editor_map_is_preserved_byte_for_byte():
    world = SOURCE / "f1_robot_model/world/demomap_2/model.sdf"
    # User's original map at d1b01698b16af03616a62b414a132926989091a6.
    assert hashlib.sha256(world.read_bytes()).hexdigest() == (
        "5bb46412d580673fff69987b3455fbde8f24d61f8b9f4ec362b7c1c116de5dbc")


def test_f1_meshes_resolve_after_gazebo_converts_package_uris_to_model_uris():
    share = SOURCE / "f1_robot_model"
    package = ET.parse(share / "package.xml").getroot()
    exported_paths = [
        Path(export.get("gazebo_model_path").replace("${prefix}", str(share))).resolve()
        for export in package.findall("export/gazebo_ros")
        if export.get("gazebo_model_path")
    ]
    assert exported_paths, "Gazebo must receive the model search path from package.xml"
    robot = expand_f1(depth_camera=True, lidar_3d=True)
    filenames = {mesh.get("filename") for mesh in robot.iter("mesh")}
    assert len(filenames) >= 8  # Chassis, four wheels, two hinges, and the Hokuyo.
    for filename in filenames:
        assert filename.startswith("package://f1_robot_model/")
        model_uri = filename.replace("package://", "model://", 1)
        relative = model_uri.removeprefix("model://")
        candidates = [directory / relative for directory in exported_paths]
        expected_asset = SOURCE / filename.removeprefix("package://")
        assert any(asset.is_file() and asset.resolve() == expected_asset.resolve()
                   for asset in candidates), model_uri


@pytest.mark.parametrize("filename", ["urdf_config.rviz", "sim_config.rviz"])
def test_f1_default_rviz_subscribes_only_to_present_sensors(filename):
    config = yaml.safe_load((SOURCE / "f1_robot_model/rviz" / filename).read_text())
    displays = {display["Name"]: display
                for display in config["Visualization Manager"]["Displays"]}
    for name, topic in {"2D LiDAR": "/scan", "IMU": "/imu/data"}.items():
        assert displays[name]["Enabled"] is True
        assert displays[name]["Topic"]["Value"] == topic
        assert displays[name]["Topic"]["Reliability Policy"] == "Best Effort"
    for name, topic in {"Depth points": "/camera/points", "RGB camera": "/camera/image_raw",
                        "3D LiDAR (optional)": "/lidar_3d/points"}.items():
        assert displays[name]["Enabled"] is False
        assert displays[name]["Topic"]["Value"] == topic
        assert displays[name]["Topic"]["Reliability Policy"] == "Best Effort"
    assert displays["Depth points"]["Color Transformer"] == "RGB8"
    imu = displays["IMU"]
    assert imu["fixed_frame_orientation"] is True
    assert imu["Acceleration properties"]["Derotate acceleration"] is True
    scale = imu["Acceleration properties"]["Acc. vector scale"]
    assert 0 < (9.80665 + 1.) * scale <= 0.72


def camera_geometry(robot):
    transforms = frames(robot)
    cameras = {}
    for gazebo in robot.findall("gazebo"):
        for sensor in gazebo.findall("sensor"):
            if sensor.get("type") not in {"camera", "depth", "multicamera"}:
                continue
            plugin = sensor.find("plugin")
            pose = vector(sensor.findtext("pose", "0 0 0 0 0 0"))
            sensor_transform = compose(transforms[gazebo.get("reference")], (pose[:3], rotation(pose[3:])))
            for camera in sensor.findall("camera"):
                camera_pose = vector(camera.findtext("pose", "0 0 0 0 0 0"))
                physical = compose(sensor_transform, (camera_pose[:3], rotation(camera_pose[3:])))
                optical = transforms[plugin.findtext("frame_name")]
                name = plugin.findtext("camera_name")
                if sensor.get("type") == "multicamera":
                    name += "/" + camera.get("name")
                cameras[name] = (camera, plugin, physical, optical)
    return cameras


@pytest.mark.parametrize("name", ["camera", "stereo/left", "stereo/right", "rgbd"])
def test_physical_camera_origin_and_axes_match_its_optical_tf(name):
    _, _, physical, optical = camera_geometry(expand())[name]
    assert optical[0] == pytest.approx(physical[0], abs=1e-9)
    for optical_axis, body_axis in [((0, 0, 1), (1, 0, 0)),
                                     ((1, 0, 0), (0, -1, 0)),
                                     ((0, 1, 0), (0, 0, -1))]:
        assert rotated(optical[1], optical_axis) == pytest.approx(rotated(physical[1], body_axis), abs=1e-9)


def test_stereo_projection_recovers_depth_from_physical_disparity():
    cameras = camera_geometry(expand())
    left, lp, lt, _ = cameras["stereo/left"]
    right, rp, rt, _ = cameras["stereo/right"]
    physical_baseline = lt[0][1] - rt[0][1]
    assert physical_baseline > 0
    assert lt[0][0] == pytest.approx(rt[0][0], abs=1e-9)
    assert lt[0][2] == pytest.approx(rt[0][2], abs=1e-9)
    assert float(lp.findtext("hack_baseline", "0")) == 0
    width = float(left.findtext("image/width"))
    focal = width / (2 * math.tan(float(left.findtext("horizontal_fov")) / 2))
    assert right.findtext("horizontal_fov") == left.findtext("horizontal_fov")
    assert right.findtext("image/width") == left.findtext("image/width")
    # A point five metres ahead of the left camera produces positive disparity.
    depth = 5.0
    disparity = focal * physical_baseline / depth
    projection_tx = -focal * float(rp.findtext("hack_baseline", "0"))
    assert -projection_tx / disparity == pytest.approx(depth, abs=1e-9)


@pytest.mark.parametrize("pixel", [(0, 0), (159, 119), (319, 239)])
def test_rgbd_camera_info_reprojects_native_point_to_original_pixel(pixel):
    camera, plugin, _, _ = camera_geometry(expand())["rgbd"]
    width, height = (int(camera.findtext("image/" + key)) for key in ("width", "height"))
    focal = width / (2 * math.tan(float(camera.findtext("horizontal_fov")) / 2))
    cx = float(plugin.findtext("cx", str((width + 1) / 2)))
    cy = float(plugin.findtext("cy", str((height + 1) / 2)))
    u, v = pixel
    depth = 5.625
    # This is the documented Classic plugin conversion, independently of K.
    x, y, z = ((u - (width - 1) / 2) * depth / focal,
               (v - (height - 1) / 2) * depth / focal, depth)
    assert (focal * x / z + cx, focal * y / z + cy) == pytest.approx(pixel, abs=1e-9)


@pytest.mark.parametrize("lidar", [False, True])
def test_f1_rgbd_optical_tf_and_camera_info_match_native_points(lidar):
    robot = expand_f1(depth_camera=True, lidar_3d=lidar)
    camera, plugin, physical, optical = camera_geometry(robot)["camera"]
    assert physical[0] == pytest.approx(optical[0], abs=1e-9)
    for optical_axis, body_axis in [((0, 0, 1), (1, 0, 0)),
                                     ((1, 0, 0), (0, -1, 0)),
                                     ((0, 1, 0), (0, 0, -1))]:
        assert rotated(optical[1], optical_axis) == pytest.approx(rotated(physical[1], body_axis), abs=1e-9)
    width, height = (int(camera.findtext("image/" + key)) for key in ("width", "height"))
    focal = width / (2 * math.tan(float(camera.findtext("horizontal_fov")) / 2))
    cx, cy = float(plugin.findtext("cx")), float(plugin.findtext("cy"))
    for u, v in [(0, 0), (width // 2, height // 2), (width - 1, height - 1)]:
        depth = 2.75
        x = (u - (width - 1) / 2) * depth / focal
        y = (v - (height - 1) / 2) * depth / focal
        assert (focal * x / depth + cx, focal * y / depth + cy) == pytest.approx((u, v), abs=1e-9)


@pytest.mark.parametrize("depth", [False, True])
def test_f1_3d_lidar_has_vertical_layers_and_its_own_ros_frame(depth):
    robot = expand_f1(depth_camera=depth, lidar_3d=True)
    sensor = robot.find("gazebo[@reference='lidar_3d_link']/sensor")
    assert sensor is not None
    assert int(sensor.findtext("ray/scan/vertical/samples")) == 32
    assert float(sensor.findtext("ray/scan/vertical/min_angle")) < 0
    assert float(sensor.findtext("ray/scan/vertical/max_angle")) > 0
    assert sensor.findtext("plugin/frame_name") == "lidar_3d_link"
    assert sensor.findtext("plugin/ros/namespace") == "/lidar_3d"
    assert sensor.findtext("plugin/ros/remapping") == "~/out:=points"
    assert frames(robot)["lidar_3d_link"][0] == pytest.approx((0., 0., 0.247), abs=1e-9)


@pytest.mark.parametrize("spawn_yaw,imu_rpy", [
    (0.4, (0., 0., 0.7)),
    (0., (0.15, -0.2, 0.7)),
    (-0.3, (-0.1, 0.15, -0.5)),
])
def test_rviz_imu_orientation_and_acceleration_share_the_world_reference(spawn_yaw, imu_rpy):
    config = yaml.safe_load((SOURCE / "gazebo_tutorial_bringup/rviz/sensors.rviz").read_text())
    manager = config["Visualization Manager"]
    display = next(d for d in manager["Displays"] if d["Class"] == "rviz_imu_plugin/Imu")
    fixed_frame = manager["Global Options"]["Fixed Frame"]
    world_fixed = IDENTITY if fixed_frame == "world" else rotation((0., 0., spawn_yaw))
    world_imu = rotation(imu_rpy)
    fixed_world = tuple(zip(*world_fixed))
    fixed_imu = compose(((0., 0., 0.), fixed_world), ((0., 0., 0.), world_imu))[1]
    # imu_tools applies the message quaternion beneath the chosen scene node.
    parent = IDENTITY if display.get("fixed_frame_orientation", True) else fixed_imu
    visual = compose(((0., 0., 0.), parent), ((0., 0., 0.), world_imu))[1]
    assert rotated(world_fixed, rotated(visual, (1., 0., 0.))) == pytest.approx(
        rotated(world_imu, (1., 0., 0.)), abs=1e-9)
    world_acceleration = (0.3, -0.2, 9.80665)
    measured = rotated(tuple(zip(*world_imu)), world_acceleration)
    if display["Acceleration properties"].get("Derotate acceleration", True):
        measured = rotated(world_imu, measured)
    displayed = rotated(world_fixed, rotated(parent, measured))
    assert displayed == pytest.approx(world_acceleration, abs=1e-9)


def test_rviz_imu_markers_do_not_cover_the_robot():
    config = yaml.safe_load((SOURCE / "gazebo_tutorial_bringup/rviz/sensors.rviz").read_text())
    display = next(d for d in config["Visualization Manager"]["Displays"]
                   if d["Class"] == "rviz_imu_plugin/Imu")
    body = expand().find("link[@name='base_link']/visual/geometry/box")
    dimensions = vector(body.get("size"))
    if display["Box properties"].get("Enable box", False):
        # imu_tools recognizes these three keys; a generic Scale key is ignored.
        sizes = [display["Box properties"].get(axis + "_scale", 1.) for axis in "xyz"]
        assert all(0 < size <= bound for size, bound in zip(sizes, dimensions))
    acceleration = display["Acceleration properties"]
    if acceleration.get("Enable acceleration", False):
        # imu_tools 2.1.5 draws a |a|*scale shaft plus a 1.0*scale head.
        # Keep the stationary gravity arrow within two chassis lengths.
        scale = acceleration.get("Acc. vector scale", 1.)
        arrow_length = (9.80665 + 1.0) * scale
        assert 0 < arrow_length <= 2 * dimensions[0]


def hull(points):
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def half(sequence):
        result = []
        for p in sequence:
            while len(result) >= 2 and cross(result[-2], result[-1], p) <= 0:
                result.pop()
            result.append(p)
        return result
    return half(points)[:-1] + half(reversed(points))[:-1]


@pytest.mark.parametrize("filename,profile", [
    ("sensor_bot.urdf.xacro", p) for p in ("all", "cameras", "lidars", "minimal")
] + [(name + ".urdf.xacro", "minimal") for name in ("diffbot", "rover_diff", "rover_ackermann")])
def test_total_mass_is_inside_actual_wheel_support_polygon(filename, profile):
    robot = expand(filename, profile)
    transforms = frames(robot)
    contacts, weighted, mass_sum = [], [0., 0., 0.], 0.
    for link in robot.findall("link"):
        name = link.get("name")
        inertial = link.find("inertial")
        if inertial is not None:
            mass = float(inertial.find("mass").get("value"))
            assert mass > 0
            centre, _ = compose(transforms[name], origin(inertial.find("origin")))
            weighted = [a + mass * b for a, b in zip(weighted, centre)]
            mass_sum += mass
            inertia = inertial.find("inertia")
            xx, yy, zz, xy, xz, yz = (float(inertia.get(k)) for k in ("ixx", "iyy", "izz", "ixy", "ixz", "iyz"))
            assert xx > 0 and xx * yy - xy ** 2 > 0
            assert xx * yy * zz + 2 * xy * xz * yz - xx * yz ** 2 - yy * xz ** 2 - zz * xy ** 2 > 0
            assert xx + yy >= zz and xx + zz >= yy and yy + zz >= xx
        if "wheel" not in name and name != "caster_link":
            continue
        for collision in link.findall("collision"):
            cylinder, sphere = collision.find("geometry/cylinder"), collision.find("geometry/sphere")
            geometry = cylinder if cylinder is not None else sphere
            if geometry is None:
                continue
            centre, orientation = compose(transforms[name], origin(collision.find("origin")))
            radius = float(geometry.get("radius"))
            vertical_extent = radius
            if cylinder is not None:
                axis_z = abs(rotated(orientation, (0., 0., 1.))[2])
                vertical_extent = (axis_z * float(cylinder.get("length")) / 2
                                   + math.sqrt(max(0., 1 - axis_z ** 2)) * radius)
            if abs(centre[2] - vertical_extent) < 1e-5:
                contacts.append(centre[:2])
    assert len(contacts) >= 3
    if filename in {"rover_ackermann.urdf.xacro", "sensor_bot.urdf.xacro"}:
        assert sorted(contacts) == pytest.approx(sorted([
            (-0.28, -0.31), (-0.28, 0.31), (0.28, -0.31), (0.28, 0.31)]), abs=1e-9)
    polygon = hull(contacts)
    cx, cy, _ = [value / mass_sum for value in weighted]
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        margin = ((b[0] - a[0]) * (cy - a[1]) - (b[1] - a[1]) * (cx - a[0])) / math.dist(a, b)
        assert margin >= 0.005, (filename, profile, "support margin", margin)
