"""4륜 skid-steer 또는 Ackermann rover를 실행하는 launch 파일이다."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _launch_rover(context: LaunchContext):
    drive_mode = LaunchConfiguration("drive_mode").perform(context)
    if drive_mode not in {"diff", "ackermann"}:
        raise RuntimeError("drive_mode must be either 'diff' or 'ackermann'")

    default_model_name = f"rover_{drive_mode}"
    model_name = LaunchConfiguration("model_name").perform(context)
    gui = LaunchConfiguration("gui").perform(context).casefold() in {"true", "1", "yes"}

    description_share = Path(get_package_share_directory("tutorial_bot_description"))
    bringup_share = Path(get_package_share_directory("tutorial_bot_bringup"))
    gazebo_share = Path(get_package_share_directory("tutorial_bot_gazebo"))
    xacro_file = description_share / "urdf" / "rovers" / f"{default_model_name}.urdf.xacro"
    world_file = gazebo_share / "worlds" / "training.sdf"
    rviz_file = bringup_share / "rviz" / "rover.rviz"

    description = ParameterValue(
        Command(["xacro ", str(xacro_file), " model_name:=", model_name]),
        value_type=str,
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("ros_gz_sim")) / "launch" / "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"{'-r' if gui else '-s -r'} {world_file}",
            "on_exit_shutdown": "true",
        }.items(),
    )
    state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": description, "use_sim_time": True}],
        output="screen",
    )
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", model_name, "-topic", "robot_description", "-z", "0.02"],
        output="screen",
    )

    gz_cmd_vel = f"/model/{model_name}/cmd_vel"
    gz_odom = f"/model/{model_name}/odometry"
    gz_tf = f"/model/{model_name}/tf"
    gz_joint_state = f"/model/{model_name}/joint_state"
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            f"{gz_cmd_vel}@geometry_msgs/msg/Twist]gz.msgs.Twist",
            f"{gz_odom}@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"{gz_tf}@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            f"{gz_joint_state}@sensor_msgs/msg/JointState[gz.msgs.Model",
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        remappings=[
            (gz_cmd_vel, "/cmd_vel"),
            (gz_odom, "/odom"),
            (gz_tf, "/tf"),
            (gz_joint_state, "/joint_states"),
        ],
        output="screen",
    )
    path = Node(
        package="tutorial_bot_bringup",
        executable="odom_to_path",
        parameters=[{"use_sim_time": True}],
        output="screen",
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", str(rviz_file)],
        parameters=[{"use_sim_time": True}],
        output="screen",
        condition=IfCondition(LaunchConfiguration("rviz")),
    )
    return [gazebo, state_publisher, spawn, bridge, path, rviz]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "drive_mode",
                default_value="diff",
                description="diff 또는 ackermann",
            ),
            DeclareLaunchArgument(
                "model_name",
                default_value="rover",
                description="Gazebo entity와 topic에 사용할 이름",
            ),
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("rviz", default_value="true"),
            OpaqueFunction(function=_launch_rover),
        ]
    )
