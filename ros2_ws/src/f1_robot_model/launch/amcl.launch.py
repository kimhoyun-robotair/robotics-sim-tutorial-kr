"""Localization only: match a saved map to the selected Gazebo world."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = get_package_share_directory('f1_robot_model')
    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('map', default_value=os.path.join(share, 'map', 'demomap_2.yaml')),
        DeclareLaunchArgument('world', default_value=os.path.join(share, 'world', 'demomap_2', 'model.sdf')),
        DeclareLaunchArgument('params_file', default_value=os.path.join(share, 'config', 'amcl.yaml')),
        DeclareLaunchArgument('rvizconfig', default_value=os.path.join(share, 'rviz', 'sim_config.rviz')),
    ]
    simulation = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(share, 'launch', 'robot_spawn.launch.py')),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'rvizconfig': LaunchConfiguration('rvizconfig'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items())
    localization = IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
        get_package_share_directory('nav2_bringup'), 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'), 'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'), 'autostart': 'true',
            'use_composition': 'False',
        }.items())
    return LaunchDescription(arguments + [simulation, localization])
