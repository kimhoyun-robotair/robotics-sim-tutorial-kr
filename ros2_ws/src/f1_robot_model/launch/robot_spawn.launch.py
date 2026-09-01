import launch
from launch.substitutions import Command, LaunchConfiguration
import launch_ros
from launch_ros.actions import Node
import os
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    # path to the robot model
    pkg_share = launch_ros.substitutions.FindPackageShare(
        package='f1_robot_model'
    ).find('f1_robot_model')
    default_model_path = os.path.join(pkg_share, 'urdf/racecar.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz/urdf_config.rviz')

    # param for using simulation time
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Position and orientation for spawning robot in gazebo
    # [X, Y, Z]
    position = [0.0, 0.0, 0.0]
    # [Roll, Pitch, Yaw]
    orientation = [0.0, 0.0, 0.0]

    # joy_teleop config file path
    joy_teleop_config_file = os.path.join(pkg_share, 'config/MXswitch.config.yaml')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        emulate_tty=True,
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': Command(['xacro ', LaunchConfiguration('model')])
        }]
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
        arguments=[
            '-entity', 'racecar',
            '-x', str(position[0]),
            '-y', str(position[1]),
            '-z', str(position[2]),
            '-R', str(orientation[0]),
            '-P', str(orientation[1]),
            '-Y', str(orientation[2]),
            '-topic', '/robot_description'
        ],
        output='screen'
    )
    # if you want to use ackermanndrivestamped topic to control vehicle, plz uncomment node codes
    """
    ackermann_to_twist_converter_node = Node(
        package='f1_robot_model',
        executable='ackermann_to_twist_converter_node',
        name='ackermann_to_twist_converter_node',
        output='screen'
    )
    """

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
        DeclareLaunchArgument(
            name='model',
            default_value=default_model_path,
            description='Absolute path to robot urdf file'
        ),
        DeclareLaunchArgument(
            name='rvizconfig',
            default_value=default_rviz_config_path,
            description='Absolute path to rviz config file'
        ),
        launch.actions.ExecuteProcess(
            cmd=[
                'gazebo', '--verbose', '-s',
                'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'
            ],
            output='screen'
        ),
        declare_use_sim_time_cmd,
        joint_state_publisher_node,
        robot_state_publisher_node,
        spawn_entity,
        rviz_node,
        # ackermann_to_twist_converter_node,
        joy,
        joy_teleop,
    ])
