"""Run the F1TENTH model in Gazebo Classic 11 with one TF publisher per edge."""
import os
import tempfile

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction, RegisterEventHandler)
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _launch_rviz(context):
    """Enable displays only for sensors selected in this simulation."""
    if not IfCondition(LaunchConfiguration('rviz')).evaluate(context):
        return []
    share = get_package_share_directory('f1_robot_model')
    source = LaunchConfiguration('rvizconfig').perform(context)
    packaged_configs = [os.path.join(share, 'rviz', name)
                        for name in ('urdf_config.rviz', 'sim_config.rviz')]
    actions = []
    if os.path.realpath(source) in [os.path.realpath(path) for path in packaged_configs]:
        with open(source, encoding='utf-8') as stream:
            config = yaml.safe_load(stream)
        depth = IfCondition(LaunchConfiguration('depth_camera')).evaluate(context)
        lidar = IfCondition(LaunchConfiguration('lidar_3d')).evaluate(context)
        states = {'Depth points': depth, 'RGB camera': depth,
                  '3D LiDAR (optional)': lidar}
        for display in config['Visualization Manager']['Displays']:
            if display.get('Name') in states:
                display['Enabled'] = states[display['Name']]
        temporary = tempfile.TemporaryDirectory(prefix='f1-rviz-')
        source = os.path.join(temporary.name, 'selected_sensors.rviz')
        with open(source, 'w', encoding='utf-8') as stream:
            yaml.safe_dump(config, stream, sort_keys=False)

        def cleanup(_context):
            temporary.cleanup()
            return []

        actions.append(RegisterEventHandler(OnShutdown(
            on_shutdown=[OpaqueFunction(function=cleanup)])))
    actions.append(Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', source],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]))
    return actions


def generate_launch_description():
    share = get_package_share_directory('f1_robot_model')
    use_sim_time = LaunchConfiguration('use_sim_time')
    sensor_defaults = {
        'depth_camera': 'false', 'stereo_camera': 'false',
        'lidar_3d': 'false', 'gps': 'false',
    }
    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('joystick', default_value='false'),
        DeclareLaunchArgument('ackermann_adapter', default_value='true'),
        DeclareLaunchArgument('model', default_value=os.path.join(share, 'urdf', 'racecar.urdf')),
        DeclareLaunchArgument('world', default_value=os.path.join(share, 'world', 'demomap_2', 'model.sdf')),
        DeclareLaunchArgument('rvizconfig', default_value=os.path.join(share, 'rviz', 'urdf_config.rviz')),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
    ]
    command = [FindExecutable(name='xacro'), ' ', LaunchConfiguration('model')]
    for name, default in sensor_defaults.items():
        arguments.append(DeclareLaunchArgument(name, default_value=default))
        command.extend([' ', name, ':=', LaunchConfiguration(name)])
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')),
        launch_arguments={
            'world': LaunchConfiguration('world'), 'gui': LaunchConfiguration('gui'),
            'verbose': 'true',
        }.items(),
    )
    nodes = [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             output='screen', parameters=[{
                 'use_sim_time': use_sim_time,
                 'robot_description': ParameterValue(Command(command), value_type=str),
             }]),
        Node(package='gazebo_ros', executable='spawn_entity.py', output='screen',
             arguments=['-entity', 'racecar', '-topic', '/robot_description',
                        '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                        '-z', LaunchConfiguration('z'), '-Y', LaunchConfiguration('yaw')]),
        OpaqueFunction(function=_launch_rviz),
        Node(package='f1_robot_model', executable='ackermann_to_twist_converter_node',
             condition=IfCondition(LaunchConfiguration('ackermann_adapter')),
             parameters=[{'use_sim_time': use_sim_time}], output='screen'),
        Node(package='joy', executable='joy_node', name='joy_node',
             condition=IfCondition(LaunchConfiguration('joystick')),
             parameters=[{'device_id': 0, 'deadzone': 0.1, 'autorepeat_rate': 20.0}]),
        Node(package='teleop_twist_joy', executable='teleop_node',
             name='teleop_twist_joy_node',
             condition=IfCondition(LaunchConfiguration('joystick')),
             parameters=[os.path.join(share, 'config', 'MXswitch.config.yaml')]),
    ]
    return LaunchDescription(arguments + [simulation] + nodes)
