"""Launch the four-wheel skid/differential-drive rover."""

from gazebo_tutorial_bringup.launch_api import generate_robot_launch


def generate_launch_description():
    return generate_robot_launch(
        default_xacro='rover_diff.urdf.xacro',
        default_entity='rover_diff',
    )
