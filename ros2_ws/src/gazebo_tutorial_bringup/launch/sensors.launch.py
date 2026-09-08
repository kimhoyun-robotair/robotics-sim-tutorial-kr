"""Launch the four-wheel Ackermann sensor vehicle in Gazebo Classic."""

from gazebo_tutorial_bringup.launch_api import generate_robot_launch


def generate_launch_description():
    return generate_robot_launch(
        default_xacro='sensor_bot.urdf.xacro',
        default_entity='sensor_bot',
        default_rviz_config='sensors.rviz',
        default_sensor_profile='all',
        default_world_file='sensor.world',
        use_ackermann_encoder_odom=True,
        pass_sensor_profile=True,
    )
