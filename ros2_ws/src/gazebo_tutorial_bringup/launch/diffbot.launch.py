"""Launch the two-wheel differential-drive tutorial robot."""

from gazebo_tutorial_bringup.launch_api import generate_robot_launch


def generate_launch_description():
    return generate_robot_launch(
        default_xacro='diffbot.urdf.xacro',
        default_entity='diffbot',
    )
