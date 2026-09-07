"""실행 중인 rover에 Jazzy Nav2를 연결한다."""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import yaml


def _merge(base, overrides):
    """설치된 Nav2 기본 설정에 rover 설정을 재귀적으로 덮어쓴다."""
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _launch_nav2(context):
    bringup = get_package_share_directory('nav2_bringup')
    params_path = LaunchConfiguration('params_file').perform(context)
    map_path = LaunchConfiguration('map').perform(context)
    if map_path and (not os.path.isabs(map_path) or not os.path.isfile(map_path)):
        raise RuntimeError('map에는 존재하는 지도 YAML의 절대 경로를 입력하세요.')

    # Nav2 패치 버전에 따라 추가된 서버의 기본 설정도 함께 보존한다.
    with open(os.path.join(bringup, 'params', 'nav2_params.yaml'), encoding='utf-8') as file:
        params = yaml.safe_load(file)
    with open(params_path, encoding='utf-8') as file:
        _merge(params, yaml.safe_load(file))
    if map_path:
        # map_server의 노드별 빈 값이 launch의 일반 파라미터보다 우선하지 않게 한다.
        # 검증한 CLI 경로를 실제로 읽는 YAML에도 기록하여 두 입력을 일치시킨다.
        params.setdefault('map_server', {}).setdefault('ros__parameters', {})[
            'yaml_filename'] = map_path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as file:
        yaml.safe_dump(params, file, sort_keys=False)
        merged_path = file.name

    def cleanup(event, launch_context):
        if os.path.exists(merged_path):
            os.unlink(merged_path)
        return []

    arguments = {
        'use_sim_time': LaunchConfiguration('use_sim_time'),
        'autostart': 'true',
        'params_file': merged_path,
        'use_composition': 'False',
    }
    actions = [RegisterEventHandler(OnShutdown(on_shutdown=cleanup))]
    if map_path:
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup, 'launch', 'localization_launch.py')),
            launch_arguments={**arguments, 'map': map_path}.items(),
        ))
    else:
        actions.append(LogInfo(msg=(
            'map 인자가 비어 있습니다. 먼저 slam.launch.py 또는 별도 위치 추정 노드를 '
            '실행하여 /map과 map → odom TF를 제공하세요.')))
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup, 'launch', 'navigation_launch.py')),
        launch_arguments=arguments.items(),
    ))
    return actions


def generate_launch_description():
    """지도 인자가 있으면 AMCL도 실행하고, 없으면 외부 SLAM을 사용한다."""
    share = get_package_share_directory('simple_rover')
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value='',
                              description='저장한 지도 YAML의 절대 경로; SLAM 중에는 생략'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            share, 'config', 'nav2_params.yaml')),
        OpaqueFunction(function=_launch_nav2),
    ])
