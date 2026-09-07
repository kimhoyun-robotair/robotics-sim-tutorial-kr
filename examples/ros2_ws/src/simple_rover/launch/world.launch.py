# Copyright 2025 MOGI-ROS and Gazebo_Harmonic_Rover contributors
# Modifications 2026 robotics-sim-tutorial-kr contributors
# SPDX-License-Identifier: Apache-2.0
"""Launch installed or absolute SDF paths without assuming environment variables exist."""
import os
import shlex

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _start(context):
    share = get_package_share_directory('simple_rover')
    value = lambda name: LaunchConfiguration(name).perform(context)
    world = value('world')
    if not os.path.isabs(world):
        world = os.path.join(share, 'worlds', world)
    if not os.path.isfile(world):
        raise FileNotFoundError(f'World not found: {world}')
    resource_paths = [os.path.dirname(share), value('models_path'), os.environ.get('GZ_SIM_RESOURCE_PATH', '')]
    gz_args = '-r -v 3 '
    if value('gui') == 'false':
        gz_args += '-s '
    if value('headless') == 'true':
        gz_args += '--headless-rendering '
    gz_args += shlex.quote(world)
    return [
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(p for p in resource_paths if p)),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': gz_args, 'on_exit_shutdown': 'true'}.items()),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='rover_arena.sdf'),
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('models_path', default_value=''),
        OpaqueFunction(function=_start),
    ])
