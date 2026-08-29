import re
from collections.abc import Callable
from pathlib import Path
from typing import Final

from ament_index_python.packages import get_package_share_directory
from launch import Action, LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.events.process import ProcessExited
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

DEFAULT_WORLD: Final = "training"
WORLD_NAME_PATTERN: Final = re.compile(r"[A-Za-z0-9_-]+")
MODEL_NAME_PATTERN: Final = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
NAMESPACE_PATTERN: Final = re.compile(
    r"/(?:[A-Za-z][A-Za-z0-9_-]*(?:/[A-Za-z][A-Za-z0-9_-]*)*)?"
)
TF_PREFIX_PATTERN: Final = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9_]*(?:/[A-Za-z][A-Za-z0-9_]*)*/?)?"
)
NAVIGATION_READY_COMMAND: Final = "until " + " && ".join(
    (
        "timeout 2 ros2 topic echo --once /scan sensor_msgs/msg/LaserScan >/dev/null 2>&1",
        "timeout 2 ros2 topic echo --once /odom nav_msgs/msg/Odometry >/dev/null 2>&1",
        "timeout 3 ros2 run tf2_ros tf2_echo odom base_link 2>/dev/null | grep -q '^At time '",
    )
) + "; do sleep 0.2; done"


class _LaunchContractError(RuntimeError):
    pass


def _enabled(raw_value: str, argument_name: str) -> bool:
    normalized = raw_value.casefold()
    enabled = normalized in {"true", "1", "yes"}
    disabled = normalized in {"false", "0", "no"}
    if enabled:
        return True
    if disabled:
        return False
    raise _LaunchContractError(
        f"{argument_name} must be true or false, received {raw_value!r}."
    )


def _validated_xacro_argument(
    raw_value: str, argument_name: str, pattern: re.Pattern[str]
) -> str:
    if pattern.fullmatch(raw_value) is None:
        raise _LaunchContractError(
            f"{argument_name} has an invalid ROS-compatible value: {raw_value!r}."
        )
    return raw_value


def _after_success(
    next_action: Action, completed_name: str
) -> Callable[[ProcessExited, LaunchContext], list[Action]]:
    def transition(event: ProcessExited, _: LaunchContext) -> list[Action]:
        if event.returncode == 0:
            return [next_action]
        return [
            EmitEvent(
                event=Shutdown(
                    reason=f"{completed_name} exited with code {event.returncode}."
                )
            )
        ]

    return transition


def _launch_stack(context: LaunchContext) -> list[Action]:
    world_name = LaunchConfiguration("world").perform(context)
    nav2_enabled = _enabled(LaunchConfiguration("nav2").perform(context), "nav2")
    gui_enabled = _enabled(LaunchConfiguration("gui").perform(context), "gui")
    rviz_enabled = _enabled(LaunchConfiguration("rviz").perform(context), "rviz")
    if WORLD_NAME_PATTERN.fullmatch(world_name) is None:
        raise _LaunchContractError(
            f"world must be an installed world name, received {world_name!r}."
        )
    model_name = _validated_xacro_argument(
        LaunchConfiguration("model_name").perform(context),
        "model_name",
        MODEL_NAME_PATTERN,
    )
    namespace = _validated_xacro_argument(
        LaunchConfiguration("namespace").perform(context),
        "namespace",
        NAMESPACE_PATTERN,
    )
    tf_prefix = _validated_xacro_argument(
        LaunchConfiguration("tf_prefix").perform(context),
        "tf_prefix",
        TF_PREFIX_PATTERN,
    )
    gazebo_share = Path(get_package_share_directory("tutorial_bot_gazebo"))
    bringup_share = Path(get_package_share_directory("tutorial_bot_bringup"))
    description_share = Path(get_package_share_directory("tutorial_bot_description"))
    control_share = Path(get_package_share_directory("tutorial_bot_control"))
    world_path = gazebo_share / "worlds" / f"{world_name}.sdf"
    if not world_path.is_file():
        raise _LaunchContractError(
            f"Installed world does not exist: {world_path}. No source-tree fallback is used."
        )

    xacro_path = description_share / "urdf" / "tutorial_bot.urdf.xacro"
    controller_config = control_share / "config" / "controllers.yaml"
    bridge_config = bringup_share / "config" / "bridge-intermediate.yaml"
    rviz_config = bringup_share / "rviz" / "tutorial_bot.rviz"
    map_path = gazebo_share / "maps" / "training.yaml"
    nav2_params = bringup_share / "config" / "nav2_params.yaml"
    if nav2_enabled and world_name != DEFAULT_WORLD:
        raise _LaunchContractError(
            "nav2:=true requires the installed training world and ground-truth map."
        )
    if nav2_enabled and (not map_path.is_file() or not nav2_params.is_file()):
        raise _LaunchContractError(
            f"Installed Nav2 assets do not exist: {map_path}, {nav2_params}."
        )
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                str(xacro_path),
                " control_backend:=gz_ros2_control",
                " controller_parameters_file:=",
                str(controller_config),
                " model_name:=",
                model_name,
                " ros_namespace:=",
                namespace,
                " tf_prefix:=",
                tf_prefix,
            ]
        ),
        value_type=str,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("ros_gz_sim")) / "launch" / "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"{'-r' if gui_enabled else '-s -r'} {world_path}",
            "on_exit_shutdown": "true",
        }.items(),
    )
    state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=namespace,
        parameters=[
            {"robot_description": robot_description, "frame_prefix": tf_prefix, "use_sim_time": True}
        ],
        output="screen",
    )
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=namespace,
        arguments=["-name", model_name, "-topic", "robot_description", "-z", "0.12"],
        output="screen",
    )
    parameter_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": str(bridge_config)}],
        output="screen",
    )
    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/tutorial_bot/camera/image"],
        remappings=[
            ("/tutorial_bot/camera/image", "/camera/image"),
        ],
        output="screen",
    )
    spawner_args = [
        "--controller-manager",
        "/controller_manager",
        "--controller-manager-timeout",
        "60",
        "--switch-timeout",
        "30",
        "--param-file",
        str(controller_config),
    ]
    joint_state_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", *spawner_args],
        output="screen",
    )
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "diff_drive_controller",
            *spawner_args,
            "--controller-ros-args=-r",
            "--controller-ros-args=/diff_drive_controller/odom:=/odom",
        ],
        output="screen",
    )
    trajectory_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", *spawner_args, "--inactive"],
        output="screen",
    )
    controller_manager_ready = ExecuteProcess(
        cmd=[
            "timeout",
            "60",
            "/bin/bash",
            "-c",
            "until ros2 service type /controller_manager/list_controllers >/dev/null 2>&1; do sleep 0.2; done",
        ],
        name="wait_controller_manager",
        output="screen",
    )
    navigation_ready = ExecuteProcess(
        cmd=[
            "timeout",
            "90",
            "/bin/bash",
            "-c",
            NAVIGATION_READY_COMMAND,
        ],
        name="wait_navigation_inputs",
        output="screen",
    )
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(
                Path(get_package_share_directory("nav2_bringup"))
                / "launch"
                / "localization_launch.py"
            )
        ),
        launch_arguments={
            "map": str(map_path),
            "params_file": str(nav2_params),
            "use_sim_time": "true",
            "autostart": "false",
            "use_composition": "False",
        }.items(),
    )
    localization_ready = ExecuteProcess(
        cmd=[
            "timeout",
            "60",
            "ros2",
            "run",
            "tutorial_bot_bringup",
            "activate_localization",
            "--phase",
            "startup",
            "--deadline",
            "55",
            "--call-timeout",
            "4",
        ],
        name="wait_localization",
        output="screen",
    )
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(
                Path(get_package_share_directory("nav2_bringup"))
                / "launch"
                / "navigation_launch.py"
            )
        ),
        launch_arguments={
            "params_file": str(nav2_params),
            "use_sim_time": "true",
            "autostart": "false",
            "use_composition": "False",
        }.items(),
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", str(rviz_config)],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )
    wheel_odom_path = Node(
        package="tutorial_bot_bringup",
        executable="odom_to_path",
        name="wheel_odom_to_path",
        parameters=[
            {
                "use_sim_time": True,
                "odom_topic": "/odom",
                "path_topic": "/wheel_odom_path",
                "max_poses": 2000,
                "minimum_translation": 0.01,
            }
        ],
        output="screen",
    )

    actions: list[Action] = [
        gazebo,
        state_publisher,
        spawn,
        parameter_bridge,
        image_bridge,
        wheel_odom_path,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn,
                on_exit=_after_success(controller_manager_ready, "robot spawn"),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=controller_manager_ready,
                on_exit=_after_success(
                    joint_state_spawner, "controller-manager readiness"
                ),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=joint_state_spawner,
                on_exit=_after_success(
                    diff_drive_spawner, "joint_state_broadcaster spawner"
                ),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=diff_drive_spawner,
                on_exit=_after_success(
                    trajectory_spawner, "diff_drive_controller spawner"
                ),
            )
        ),
    ]
    if nav2_enabled:
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=trajectory_spawner,
                    on_exit=_after_success(
                        navigation_ready, "joint_trajectory_controller spawner"
                    ),
                )
            )
        )
        navigation_actions: list[Action] = [localization, navigation, localization_ready]
        if rviz_enabled:
            navigation_actions.append(rviz)
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=navigation_ready,
                    on_exit=_after_success(
                        GroupAction(actions=navigation_actions),
                        "navigation input readiness",
                    ),
                )
            )
        )
    elif rviz_enabled:
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=trajectory_spawner,
                    on_exit=_after_success(rviz, "joint_trajectory_controller spawner"),
                )
            )
        )
    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value=DEFAULT_WORLD),
            DeclareLaunchArgument("model_name", default_value="tutorial_bot"),
            DeclareLaunchArgument("namespace", default_value="/"),
            DeclareLaunchArgument("tf_prefix", default_value=""),
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("nav2", default_value="true"),
            OpaqueFunction(function=_launch_stack),
        ]
    )
