"""Launch the four-wheel Ackermann-steering rover."""

from gazebo_tutorial_bringup.launch_api import generate_robot_launch


def generate_launch_description():
    return generate_robot_launch(
        default_xacro='rover_ackermann.urdf.xacro',
        default_entity='rover_ackermann',
        use_ackermann_encoder_odom=True,
    )
