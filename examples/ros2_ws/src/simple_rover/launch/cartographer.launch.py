"""선택 실습: 실행 중인 rover에 Cartographer 2D SLAM을 연결한다."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Gazebo의 odom → base_link를 유지하고 Cartographer는 map → odom만 만든다."""
    share = get_package_share_directory('simple_rover')
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('configuration_basename', default_value='cartographer.lua'),
        DeclareLaunchArgument('resolution', default_value='0.05'),
        Node(
            package='cartographer_ros', executable='cartographer_node',
            name='cartographer_node', output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            arguments=[
                '-configuration_directory', os.path.join(share, 'config'),
                '-configuration_basename', LaunchConfiguration('configuration_basename'),
            ],
            remappings=[('scan', '/scan'), ('odom', '/odom'), ('imu', '/imu')],
        ),
        Node(
            package='cartographer_ros', executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid', output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            arguments=['-resolution', LaunchConfiguration('resolution'),
                       '-publish_period_sec', '0.5'],
        ),
    ])
