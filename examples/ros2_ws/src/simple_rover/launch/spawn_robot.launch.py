# Copyright 2025 MOGI-ROS and Gazebo_Harmonic_Rover contributors
# Modifications 2026 robotics-sim-tutorial-kr contributors
# SPDX-License-Identifier: Apache-2.0
"""Start one robot, Gazebo, ROS bridges, and optionally RViz/joystick."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('simple_rover')
    lc = LaunchConfiguration
    sim_time = ParameterValue(lc('use_sim_time'), value_type=bool)
    robot_command = [FindExecutable(name='xacro'), ' ', os.path.join(share, 'urdf', 'simple_rover.urdf')]
    robot_command += [' camera:=', lc('camera'), ' lidar_3d:=', lc('lidar_3d'), ' gps:=', lc('gps')]
    description = ParameterValue(Command(robot_command), value_type=str)
    args = [
        DeclareLaunchArgument('world', default_value='rover_arena.sdf'),
        DeclareLaunchArgument('world_name', default_value='rover_arena', description='SDF world name, not the filename'),
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('use_sim_time', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('joy', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('models_path', default_value='', description='Optional directory containing external model folders'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.12'),
        DeclareLaunchArgument('camera', default_value='rgbd', choices=['rgbd', 'rgb', 'none']),
        DeclareLaunchArgument('lidar_3d', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('gps', default_value='false', choices=['true', 'false']),
    ]
    world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'world.launch.py')),
        launch_arguments={key: lc(key) for key in ['world', 'gui', 'headless', 'models_path']}.items())
    publisher = Node(package='robot_state_publisher', executable='robot_state_publisher',
                     parameters=[{'robot_description': description, 'use_sim_time': sim_time}], output='screen')
    # create waits for the world service and robot_description; no arbitrary sleep.
    spawn = Node(package='ros_gz_sim', executable='create', output='screen',
                 arguments=['-world', lc('world_name'), '-name', 'simple_rover',
                            '-topic', '/robot_description', '-allow_renaming', 'false',
                            '-x', lc('x'), '-y', lc('y'), '-z', lc('z'), '-Y', lc('yaw')])
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', name='rover_bridge',
                  parameters=[{'config_file': os.path.join(share, 'config', 'bridge.yaml'),
                               'use_sim_time': sim_time}], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', condition=IfCondition(lc('rviz')),
                arguments=['-d', os.path.join(share, 'rviz', 'rviz.rviz')],
                parameters=[{'use_sim_time': sim_time}])
    joy = Node(package='joy', executable='joy_node', condition=IfCondition(lc('joy')),
               parameters=[{'device_id': 0, 'deadzone': 0.15, 'autorepeat_rate': 20.0,
                            'use_sim_time': sim_time}])
    teleop = Node(package='teleop_twist_joy', executable='teleop_node',
                  condition=IfCondition(lc('joy')),
                  parameters=[os.path.join(share, 'config', 'MXswitch.config.yaml'),
                              {'use_sim_time': sim_time, 'publish_stamped_twist': False}])
    return LaunchDescription(args + [world, publisher, spawn, bridge, rviz, joy, teleop])
