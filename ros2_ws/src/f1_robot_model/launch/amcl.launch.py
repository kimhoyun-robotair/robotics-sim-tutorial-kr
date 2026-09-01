import launch
from launch.substitutions import Command, LaunchConfiguration
import launch_ros
from launch_ros.actions import Node
import os
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml

def generate_launch_description():
    # pkg path
    pkg_share = launch_ros.substitutions.FindPackageShare(package='f1_robot_model').find('f1_robot_model')
    # robot model path
    default_model_path = os.path.join(pkg_share, 'urdf/racecar.urdf')
    # rviz config for sim
    default_rviz_config_path = os.path.join(pkg_share, 'rviz/sim_config.rviz')
    # gazebo world model path
    world_path=os.path.join(pkg_share, 'world/demomap_2/model.sdf')
    # use_sim_time param
    use_sim_time = LaunchConfiguration('use_sim_time')
    # namspace declare
    namespace = LaunchConfiguration('namespace')
    # node respawn param for life cycle node
    use_respawn = LaunchConfiguration('use_respawn')
    # node list for life cycle node
    lifecycle_nodes = ['map_server', 'amcl']
    # autostart setting for nav2 stack (life cycle node)
    autostart = LaunchConfiguration('autostart')
    # param files and map file for amcl and map server
    params_file = LaunchConfiguration('params_file')
    map_yaml_file = LaunchConfiguration('map')
    map_dir = os.path.join(pkg_share, 'map')
    map_file = 'demomap_2.yaml'
    param_dir = os.path.join(pkg_share, 'config')
    param_file = 'amcl.yaml'

    # joy_teleop config file path
    joy_teleop_config_file = os.path.join(pkg_share, 'config/MXswitch.config.yaml')

    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file
    }

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True
    )

    # Position and orientation
    # [X, Y, Z]
    position = [0.0, 0.0, 0.0]
    # [Roll, Pitch, Yaw]
    orientation = [0.0, 0.0, 0.0]

    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace')

    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn', default_value='False',
        description='Whether to respawn if a node crashes. Applied when composition is disabled.'
        )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
        )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically startup the nav2 stack')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(map_dir, map_file),
        description='[localize] Full path to map yaml file to load')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(param_dir, param_file),
        description='Full path to the ROS2 parameters file to use')

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        emulate_tty=True,
        parameters=[{'use_sim_time': use_sim_time, 'robot_description': Command(['xacro ', LaunchConfiguration('model')])}]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}],
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        # output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
        parameters=[{'use_sim_time': use_sim_time}],
    )
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'racecar', '-x', str(position[0]), '-y', str(position[1]), '-z', str(position[2]), '-R', str(orientation[0]), '-P', str(orientation[1]), '-Y', str(orientation[2]),'-topic', '/robot_description'],
        output='screen'
    )

    ackermann_to_twist_converter_node = Node(
        package='f1_robot_model',
        executable='ackermann_to_twist_converter_node',
        name='ackermann_to_twist_converter_node',
        output='screen'
    )

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[configured_params],
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[configured_params],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time},
                    {'autostart': autostart},
                    {'node_names': lifecycle_nodes}],
    )

    joy = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'device_id': 0,          # ls /dev/input/js* to find the device id
            'deadzone': 0.3,         # Deadzone for the joystick axes
            'autorepeat_rate': 20.0, # Autorepeat rate for the joystick buttons
        }]
    )

    joy_teleop = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[joy_teleop_config_file]
    )

    return launch.LaunchDescription([

        launch.actions.DeclareLaunchArgument(name='model', default_value=default_model_path,
                                            description='Absolute path to robot urdf file'),
        launch.actions.DeclareLaunchArgument(name='rvizconfig', default_value=default_rviz_config_path,
                                            description='Absolute path to rviz config file'),
        launch.actions.ExecuteProcess(cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_path], output='screen'),
        declare_namespace_cmd,
        declare_use_sim_time_cmd,
        declare_use_respawn_cmd,
        declare_autostart_cmd,
        declare_params_file_cmd,
        declare_map_yaml_cmd,
        joint_state_publisher_node,
        robot_state_publisher_node,
        spawn_entity,
        rviz_node,
        ackermann_to_twist_converter_node,
        amcl,
        map_server,
        lifecycle_manager,
        joy,
        joy_teleop,
    ])
