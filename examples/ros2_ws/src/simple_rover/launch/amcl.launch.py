"""시뮬레이션을 다시 만들지 않고 저장한 지도와 AMCL만 실행한다."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml


def _launch_localization(context):
    map_path = LaunchConfiguration('map').perform(context)
    if not os.path.isabs(map_path) or not os.path.isfile(map_path):
        raise RuntimeError('map:=/절대/경로/지도.yaml 형식으로 저장한 지도를 지정하세요.')
    configured_params = RewrittenYaml(
        source_file=LaunchConfiguration('params_file').perform(context),
        root_key='',
        param_rewrites={'map_server.ros__parameters.yaml_filename': map_path},
        convert_types=True,
    )
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('nav2_bringup'), 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': map_path,
            'params_file': configured_params,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': 'true',
            'use_composition': 'False',
        }.items(),
    )]


def generate_launch_description():
    """필수 지도 경로를 검사한 뒤 Nav2의 공식 localization launch를 포함한다."""
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value='',
                              description='저장한 지도 YAML의 절대 경로'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            get_package_share_directory('simple_rover'), 'config', 'nav2_params.yaml')),
        OpaqueFunction(function=_launch_localization),
    ])
