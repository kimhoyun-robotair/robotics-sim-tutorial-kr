# Copyright 2025 MOGI-ROS and Gazebo_Harmonic_Rover contributors
# Modifications 2026 robotics-sim-tutorial-kr contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect the rover description without simulation."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('simple_rover')
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false']),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': ParameterValue(Command([
                 FindExecutable(name='xacro'), ' ', os.path.join(share, 'urdf', 'simple_rover.urdf')]), value_type=str)}]),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             condition=IfCondition(LaunchConfiguration('gui'))),
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             condition=UnlessCondition(LaunchConfiguration('gui'))),
        Node(package='rviz2', executable='rviz2', arguments=['-d', os.path.join(share, 'rviz', 'urdf.rviz')]),
    ])
