"""Shared launch description for all tutorial robots."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _argument(name, default_value, description, choices=None):
    """Create a consistently documented launch argument."""
    kwargs = {
        'name': name,
        'default_value': default_value,
        'description': description,
    }
    if choices is not None:
        kwargs['choices'] = choices
    return DeclareLaunchArgument(**kwargs)


def generate_robot_launch(
    default_xacro: str,
    default_entity: str,
    default_rviz_config: str = 'odom.rviz',
    default_sensor_profile: str = 'minimal',
    default_world_file: str = 'empty.world',
    odom_origin_follows_spawn: bool = True,
    use_ackermann_encoder_odom: bool = False,
    pass_sensor_profile: bool = False,
) -> LaunchDescription:
    """Build Gazebo, robot state, spawn, Path, and optional RViz actions."""
    description_package = LaunchConfiguration('description_package')
    xacro_file = LaunchConfiguration('xacro_file')
    sensor_profile = LaunchConfiguration('sensor_profile')
    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    pause = LaunchConfiguration('pause')
    verbose = LaunchConfiguration('verbose')
    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz = LaunchConfiguration('rviz')
    rviz_config = LaunchConfiguration('rviz_config')
    entity_name = LaunchConfiguration('entity_name')
    odom_topic = LaunchConfiguration('odom_topic')
    path_topic = LaunchConfiguration('path_topic')
    path_frame = LaunchConfiguration('path_frame')
    max_points = LaunchConfiguration('max_points')
    publish_world_odom_tf = LaunchConfiguration('publish_world_odom_tf')
    ground_truth_odom_topic = LaunchConfiguration('ground_truth_odom_topic')
    ground_truth_path_topic = LaunchConfiguration('ground_truth_path_topic')
    ackermann_publish_tf = LaunchConfiguration('ackermann_publish_tf')

    default_world = PathJoinSubstitution([
        FindPackageShare('gazebo_tutorial_bringup'),
        'worlds',
        default_world_file,
    ])
    default_rviz = PathJoinSubstitution([
        FindPackageShare('gazebo_tutorial_bringup'),
        'rviz',
        default_rviz_config,
    ])
    model_path = PathJoinSubstitution([
        FindPackageShare(description_package),
        'urdf',
        xacro_file,
    ])

    xacro_command = [FindExecutable(name='xacro'), ' ', model_path]
    if pass_sensor_profile:
        xacro_command.extend([' sensor_profile:=', sensor_profile])
    robot_description = ParameterValue(
        Command(xacro_command),
        value_type=str,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gazebo.launch.py',
            ])
        ),
        launch_arguments={
            'world': world,
            'gui': gui,
            'pause': pause,
            'verbose': verbose,
        }.items(),
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
        }],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=[
            '-entity', entity_name,
            '-topic', 'robot_description',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    odom_path = Node(
        package='gazebo_tutorial_tools',
        executable='odom_to_path',
        name='odom_to_path',
        output='screen',
        parameters=[{
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
            'odom_topic': odom_topic,
            'path_topic': path_topic,
            'path_frame': path_frame,
            'max_points': ParameterValue(max_points, value_type=int),
        }],
    )

    extra_odometry_nodes = []
    if use_ackermann_encoder_odom:
        extra_odometry_nodes.extend([
            Node(
                package='gazebo_tutorial_tools',
                executable='ackermann_odom',
                name='ackermann_odom',
                output='screen',
                parameters=[{
                    'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
                    'odom_topic': odom_topic,
                    'wheel_radius': 0.16,
                    'wheelbase': 0.56,
                    'publish_tf': ParameterValue(
                        ackermann_publish_tf,
                        value_type=bool,
                    ),
                }],
            ),
            Node(
                package='gazebo_tutorial_tools',
                executable='odom_to_path',
                name='ground_truth_odom_to_path',
                output='screen',
                parameters=[{
                    'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
                    'odom_topic': ground_truth_odom_topic,
                    'path_topic': ground_truth_path_topic,
                    'path_frame': 'world',
                    'max_points': ParameterValue(max_points, value_type=int),
                }],
            ),
        ])

    # Encoder odometry starts at (0, 0, 0), so its odom origin is the spawn pose
    # expressed in world. A world-pose odometry source already uses world as its
    # origin and therefore needs an identity transform.
    world_odom_x = LaunchConfiguration('x') if odom_origin_follows_spawn else '0'
    world_odom_y = LaunchConfiguration('y') if odom_origin_follows_spawn else '0'
    world_odom_yaw = LaunchConfiguration('yaw') if odom_origin_follows_spawn else '0'
    world_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='world_to_odom',
        output='log',
        arguments=[
            '--x', world_odom_x,
            '--y', world_odom_y,
            '--z', '0',
            '--roll', '0',
            '--pitch', '0',
            '--yaw', world_odom_yaw,
            '--frame-id', 'world',
            '--child-frame-id', 'odom',
        ],
        condition=IfCondition(publish_world_odom_tf),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config],
        parameters=[{
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
        }],
        condition=IfCondition(rviz),
    )

    arguments = [
        _argument(
            'description_package',
            'gazebo_tutorial_description',
            'Xacro 파일을 제공하는 패키지',
        ),
        _argument('xacro_file', default_xacro, 'description 패키지 urdf/ 아래 Xacro'),
        _argument(
            'sensor_profile',
            default_sensor_profile,
            'sensor_bot 센서 묶음',
            choices=['all', 'cameras', 'lidars', 'minimal'],
        ),
        _argument('world', default_world, 'Gazebo Classic world 파일'),
        _argument('gui', 'true', 'gzclient 실행 여부', choices=['true', 'false']),
        _argument('pause', 'false', 'physics를 정지한 채 시작', choices=['true', 'false']),
        _argument('verbose', 'false', 'Gazebo 상세 로그', choices=['true', 'false']),
        _argument(
            'use_sim_time',
            'true',
            'ROS 노드에서 /clock 사용',
            choices=['true', 'false'],
        ),
        _argument('rviz', 'true', 'RViz 자동 실행', choices=['true', 'false']),
        _argument('rviz_config', default_rviz, '불러올 RViz 설정 파일'),
        _argument('entity_name', default_entity, 'Gazebo model entity의 고유 이름'),
        _argument('x', '0.0', '초기 x [m]'),
        _argument('y', '0.0', '초기 y [m]'),
        _argument('z', '0.10', '초기 z [m]'),
        _argument('yaw', '0.0', '초기 yaw [rad]'),
        _argument('odom_topic', '/odom', 'Path로 바꿀 Odometry 토픽'),
        _argument('path_topic', '/wheel_odom_path', 'RViz용 Path 출력 토픽'),
        _argument(
            'ground_truth_odom_topic',
            '/ground_truth/odom',
            'Ackermann built-in world-pose Odometry 토픽',
        ),
        _argument(
            'ground_truth_path_topic',
            '/ground_truth_path',
            'Ackermann world-pose 비교용 Path 토픽',
        ),
        _argument(
            'path_frame',
            '',
            'Path 프레임. 빈 값은 Odometry header.frame_id를 그대로 사용',
        ),
        _argument('max_points', '2000', 'Path에 보관할 최대 pose 수'),
        _argument(
            'publish_world_odom_tf',
            'true',
            'spawn x/y/yaw를 반영한 world → odom static TF 발행',
            choices=['true', 'false'],
        ),
        _argument(
            'ackermann_publish_tf',
            'true',
            'Ackermann wheel odometry의 odom → base_footprint TF 발행',
            choices=['true', 'false'],
        ),
    ]

    return LaunchDescription(
        arguments + [
            gazebo,
            state_publisher,
            world_to_odom,
            spawn_entity,
            *extra_odometry_nodes,
            odom_path,
            rviz_node,
        ]
    )
