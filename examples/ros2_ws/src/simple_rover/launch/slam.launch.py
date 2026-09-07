"""실행 중인 rover의 /scan과 odom TF로 2D 지도를 만든다."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    """SLAM Toolbox의 공식 launch로 lifecycle을 자동 활성화한다."""
    slam_share = get_package_share_directory('slam_toolbox')
    parameters = RewrittenYaml(
        source_file=LaunchConfiguration('params_file'),
        root_key='',
        param_rewrites={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'base_frame': 'base_link',
            'odom_frame': 'odom',
            'map_frame': 'map',
            'scan_topic': '/scan',
            'mode': 'mapping',
        },
        convert_types=True,
    )
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            slam_share, 'config', 'mapper_params_online_async.yaml')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                slam_share, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'slam_params_file': parameters,
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': 'true',
                'use_lifecycle_manager': 'false',
            }.items(),
        ),
    ])
