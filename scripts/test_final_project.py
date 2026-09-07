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


@pytest.mark.parametrize('package', ['simple_rover', 'f1tenth_sim'])
def test_bridge_directions_qos_and_default_world(package):
    bridge = yaml.safe_load((SRC / package / 'config' / 'bridge.yaml').read_text())
    topics = {entry['ros_topic_name']: entry for entry in bridge}
    assert len(topics) == len(bridge)
    for topic, entry in topics.items():
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


def test_no_personal_paths_or_legacy_ros_interfaces_in_launch():
    for package in ['simple_rover', 'f1tenth_sim', 'nav2_programming']:
        for f in (SRC / package).rglob('*.py'):
            text = f.read_text()
            assert '/home/kimhoyun' not in text
            assert 'ros_ign_' not in text
        manifest = ET.parse(SRC / package / 'package.xml').getroot()
        assert manifest.findtext('license') == 'Apache-2.0'
        assert (SRC / package / 'LICENSE').is_file()
