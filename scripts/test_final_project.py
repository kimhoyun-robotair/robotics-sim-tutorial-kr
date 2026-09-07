#!/usr/bin/env python3
"""Static regressions for the imported rover geometry and ROS/Gazebo interfaces.

Run: python -m pytest scripts/test_final_project.py
Requires pytest, xacro, PyYAML; it does not simulate physics or render RViz.
"""
import math
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import xacro
import xacro.substitution_args
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'examples' / 'ros2_ws' / 'src'
# ros_gz jazzy/ros_gz_bridge/src/bridge_config.cpp::parseQoS.
BRIDGE_QOS_PROFILES = {
    'CLOCK', 'SENSOR_DATA', 'PARAMETERS', 'SERVICES', 'PARAMETER_EVENTS',
    'ROSOUT', 'SYSTEM_DEFAULT', 'BEST_AVAILABLE',
}


def expanded(package, **mappings):
    filename = 'simple_rover.urdf' if package == 'simple_rover' else 'racecar.urdf'
    # Resolve source package shares without requiring a prebuilt ROS overlay.
    # The same Xacro files use ament_index_python in an installed ROS workspace.
    with patch.object(xacro.substitution_args, '_eval_find', lambda name: str(SRC / name)):
        return ET.fromstring(xacro.process_file(
            str(SRC / package / 'urdf' / filename), mappings=mappings).toxml())


@pytest.mark.parametrize('camera', ['rgbd', 'rgb', 'none'])
@pytest.mark.parametrize('optional', ['true', 'false'])
def test_rover_variants_have_a_single_connected_frame_tree(camera, optional):
    robot = expanded('simple_rover', camera=camera, lidar_3d=optional, gps=optional)
    _check_tree_and_sensors(robot)
    cameras = [s for s in robot.findall('.//sensor') if 'camera' in s.attrib['type']]
    assert len(cameras) == (0 if camera == 'none' else 1)
    for sensor in cameras:
        assert sensor.findtext('camera/optical_frame_id') == 'camera_link_optical'
    if cameras:
        rotation = robot.find("joint[@name='camera_optical_joint']/origin").attrib['rpy']
        assert list(map(float, rotation.split())) == pytest.approx([-math.pi / 2, 0, -math.pi / 2])
    names = {link.attrib['name'] for link in robot.findall('link')}
    assert ('lidar3d_link' in names) == (optional == 'true')
    if optional == 'true':
        assert robot.find(".//sensor[@name='gpu_lidar_3d']/topic").text == 'lidar3d'
        assert robot.find(".//sensor[@name='gpu_lidar']/topic").text == 'scan'


def _check_tree_and_sensors(robot):
    links = [link.attrib['name'] for link in robot.findall('link')]
    assert len(links) == len(set(links)), 'Duplicate link names'
    joints = robot.findall('joint')
    children = [joint.find('child').attrib['link'] for joint in joints]
    assert len(children) == len(set(children)), 'Two parents for one TF frame'
    assert set(links) - set(children) == {'base_link'}
    reachable = {'base_link'}
    for _ in joints:
        for joint in joints:
            parent, child = joint.find('parent').attrib['link'], joint.find('child').attrib['link']
            assert parent in links and child in links
            if parent in reachable:
                reachable.add(child)
    assert reachable == set(links), 'Disconnected TF tree or cycle'
    for sensor in robot.findall('.//sensor'):
        assert sensor.findtext('gz_frame_id') in links
    for reference in robot.findall('gazebo'):
        if reference.get('reference'):
            assert reference.attrib['reference'] in links
    assert not robot.findall('.//geometry/material'), 'URDF material must be a visual child'
    for mesh in robot.findall('.//mesh'):
        uri = mesh.attrib['filename']
        if uri.startswith('file://'):
            assert Path(uri[7:]).is_file(), uri


def test_drive_dimensions_match_actual_wheels():
    rover = expanded('simple_rover')
    plugin = rover.find(".//plugin[@name='gz::sim::systems::DiffDrive']")
    radius = float(rover.find("link[@name='front_left_wheel']/collision/geometry/cylinder").attrib['radius'])
    assert float(plugin.findtext('wheel_radius')) == radius
    left = rover.find("joint[@name='front_left_wheel_joint']/origin").attrib['xyz'].split()
    right = rover.find("joint[@name='front_right_wheel_joint']/origin").attrib['xyz'].split()
    assert float(plugin.findtext('wheel_separation')) == pytest.approx(float(left[1]) - float(right[1]))
    f1 = expanded('f1tenth_sim')
    _check_tree_and_sensors(f1)
    plugin = f1.find(".//plugin[@name='gz::sim::systems::AckermannSteering']")
    radius = float(f1.find("link[@name='left_rear_wheel']/collision/geometry/cylinder").attrib['radius'])
    assert float(plugin.findtext('wheel_radius')) == radius
    rear = list(map(float, f1.find("joint[@name='left_rear_wheel_joint']/origin").attrib['xyz'].split()))
    front = list(map(float, f1.find("joint[@name='left_steering_hinge_joint']/origin").attrib['xyz'].split()))
    assert float(plugin.findtext('wheel_base')) == pytest.approx(front[0] - rear[0])
    offset = abs(float(f1.find("link[@name='left_rear_wheel']/collision/origin").attrib['xyz'].split()[2]))
    assert float(plugin.findtext('wheel_separation')) == pytest.approx(2 * (rear[1] + offset))
    assert f1.find("joint[@name='right_steering_hinge_joint']").attrib['type'] == 'revolute'
    assert float(plugin.findtext('min_velocity')) < 0 < float(plugin.findtext('max_velocity'))


def _origin_matrix(origin):
    """URDF origins use fixed-axis roll, pitch, yaw: Rz(yaw) Ry(pitch) Rx(roll)."""
    values = {} if origin is None else origin.attrib
    x, y, z = map(float, values.get('xyz', '0 0 0').split())
    roll, pitch, yaw = map(float, values.get('rpy', '0 0 0').split())
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return ((cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr, x),
            (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr, y),
            (-sp, cp * sr, cp * cr, z), (0.0, 0.0, 0.0, 1.0))


def _matrix_product(left, right):
    return tuple(tuple(sum(left[i][k] * right[k][j] for k in range(4))
                       for j in range(4)) for i in range(4))


def _assert_footprint_encloses_collisions(robot, footprint):
    """Use exact primitive support bounds, including every joint/collision origin."""
    transforms = {'base_link': _origin_matrix(None)}
    pending = list(robot.findall('joint'))
    while pending:
        ready = [joint for joint in pending
                 if joint.find('parent').attrib['link'] in transforms]
        assert ready, 'Cannot resolve collision transforms from base_link'
        for joint in ready:
            transforms[joint.find('child').attrib['link']] = _matrix_product(
                transforms[joint.find('parent').attrib['link']], _origin_matrix(joint.find('origin')))
            pending.remove(joint)
    assert len(footprint) >= 3
    pairs = list(zip(footprint, footprint[1:] + footprint[:1]))
    area_twice = sum(a[0] * b[1] - b[0] * a[1] for a, b in pairs)
    assert abs(area_twice) > 1e-9, 'Degenerate footprint'
    winding = 1 if area_twice > 0 else -1
    for a, b in pairs:
        nx, ny = winding * (b[1] - a[1]), winding * (a[0] - b[0])
        length = math.hypot(nx, ny)
        assert length > 0
        normal = (nx / length, ny / length, 0.0)
        boundary = normal[0] * a[0] + normal[1] * a[1]
        assert all(normal[0] * x + normal[1] * y <= boundary + 1e-9
                   for x, y in footprint), 'This regression requires a convex footprint'
        for link in robot.findall('link'):
            for collision in link.findall('collision'):
                transform = _matrix_product(transforms[link.attrib['name']],
                                            _origin_matrix(collision.find('origin')))
                direction = [sum(normal[i] * transform[i][j] for i in range(3))
                             for j in range(3)]
                shape = list(collision.find('geometry'))[0]
                if shape.tag == 'box':
                    halves = [float(size) / 2 for size in shape.attrib['size'].split()]
                    extent = sum(abs(d) * half for d, half in zip(direction, halves))
                elif shape.tag == 'cylinder':
                    extent = (float(shape.attrib['radius']) * math.hypot(*direction[:2])
                              + float(shape.attrib['length']) / 2 * abs(direction[2]))
                else:
                    raise AssertionError(f'Add support bounds for collision type {shape.tag}')
                furthest = sum(normal[i] * transform[i][3] for i in range(3)) + extent
                assert furthest <= boundary + 1e-9, (
                    f"{link.attrib['name']} collision exceeds footprint edge {a} -> {b} "
                    f'by {furthest - boundary:.4f} m')


@pytest.mark.parametrize('configuration', ['nav2_params.yaml', 'simple_rover.yaml', 'amcl.yaml'])
@pytest.mark.parametrize('costmap', ['local_costmap', 'global_costmap'])
def test_costmap_footprint_encloses_actual_rover_collisions(configuration, costmap):
    params = yaml.safe_load((SRC / 'simple_rover' / 'config' / configuration).read_text())
    footprint = yaml.safe_load(params[costmap][costmap]['ros__parameters']['footprint'])
    # Collision geometry must fit before adding footprint_padding as extra clearance.
    # The rover's continuous wheel joints rotate cylinders about their symmetry axes.
    _assert_footprint_encloses_collisions(expanded('simple_rover'), footprint)


@pytest.mark.parametrize('package', ['simple_rover', 'f1tenth_sim'])
def test_bridge_directions_qos_and_default_world(package):
    bridge = yaml.safe_load((SRC / package / 'config' / 'bridge.yaml').read_text())
    topics = {entry['ros_topic_name']: entry for entry in bridge}
    assert len(topics) == len(bridge)
    for topic, entry in topics.items():
        if 'qos_profile' in entry:
            assert entry['qos_profile'] in BRIDGE_QOS_PROFILES, (topic, entry['qos_profile'])
        assert entry['direction'] == ('ROS_TO_GZ' if topic == '/cmd_vel' else 'GZ_TO_ROS')
        if entry['ros_type_name'].startswith('sensor_msgs/'):
            assert entry['qos_profile'] == 'SENSOR_DATA'
    if package == 'simple_rover':
        # Harmonic XYZ is body-frame data despite its optical header upstream.
        assert topics['/camera/points']['frame_id'] == 'depth_link'
        assert all('frame_id' not in topics['/camera/' + t] for t in ['image', 'depth_image', 'camera_info'])
    world = ET.parse(SRC / package / 'worlds' / 'rover_arena.sdf').getroot()
    assert not world.findall('.//uri'), 'Default world must need no downloaded models'
    required = {'Physics', 'UserCommands', 'SceneBroadcaster', 'Sensors', 'Imu', 'NavSat'}
    assert {p.attrib['name'].split('::')[-1] for p in world.findall('.//plugin')} >= required
    assert world.find('world').attrib['name'] == 'rover_arena'
    rviz = yaml.safe_load((SRC / package / 'rviz' / 'rviz.rviz').read_text())
    assert rviz['Visualization Manager']['Global Options']['Fixed Frame'] == 'odom'
    for display in rviz['Visualization Manager']['Displays']:
        if display['Class'].endswith(('LaserScan', 'PointCloud2', '/Image')):
            assert display['Topic']['Reliability Policy'] == 'Best Effort'


@pytest.mark.parametrize('filename', sorted(SRC.glob('*/config/bridge*.yaml')),
                         ids=lambda path: str(path.relative_to(SRC)))
def test_all_bridge_qos_profiles_are_accepted_by_jazzy(filename):
    for entry in yaml.safe_load(filename.read_text()):
        if 'qos_profile' in entry:
            assert entry['qos_profile'] in BRIDGE_QOS_PROFILES, (
                filename, entry['ros_topic_name'], entry['qos_profile'])


def test_no_personal_paths_or_legacy_ros_interfaces_in_launch():
    for package in ['simple_rover', 'f1tenth_sim', 'nav2_programming']:
        for f in (SRC / package).rglob('*.py'):
            text = f.read_text()
            assert '/home/kimhoyun' not in text
            assert 'ros_ign_' not in text
        manifest = ET.parse(SRC / package / 'package.xml').getroot()
        assert manifest.findtext('license') == 'Apache-2.0'
        assert (SRC / package / 'LICENSE').is_file()
