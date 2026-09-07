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


def test_rviz_imu_box_does_not_cover_the_robot():
    config = yaml.safe_load((SOURCE / "gazebo_tutorial_bringup/rviz/sensors.rviz").read_text())
    display = next(d for d in config["Visualization Manager"]["Displays"]
                   if d["Class"] == "rviz_imu_plugin/Imu")
    if not display["Box properties"].get("Enable box", False):
        return
    # imu_tools recognizes these three keys; a generic Scale key is ignored.
    sizes = [display["Box properties"].get(axis + "_scale", 1.) for axis in "xyz"]
    body = expand().find("link[@name='base_link']/visual/geometry/box")
    assert all(0 < size <= bound for size, bound in zip(sizes, vector(body.get("size"))))


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
            centre, _ = compose(transforms[name], origin(collision.find("origin")))
            radius = float(geometry.get("radius"))
            if abs(centre[2] - radius) < 1e-5:
                contacts.append(centre[:2])
    assert len(contacts) >= 3
    polygon = hull(contacts)
    cx, cy, _ = [value / mass_sum for value in weighted]
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        margin = ((b[0] - a[0]) * (cy - a[1]) - (b[1] - a[1]) * (cx - a[0])) / math.dist(a, b)
        assert margin >= 0.005, (filename, profile, "support margin", margin)
