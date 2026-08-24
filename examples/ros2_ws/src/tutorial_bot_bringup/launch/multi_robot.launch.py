import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ament_index_python.packages import get_package_share_directory
from launch import Action, LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
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

NAME_PATTERN: Final = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
NAMESPACE_PATTERN: Final = re.compile(r"/[A-Za-z][A-Za-z0-9_-]*")
WORLD_NAME_PATTERN: Final = re.compile(r"[A-Za-z0-9_-]+")


class _LaunchContractError(RuntimeError):
    pass


def _validated_launch_argument(
    raw_value: str, argument_name: str, pattern: re.Pattern[str]
) -> str:
    if pattern.fullmatch(raw_value) is None:
        raise _LaunchContractError(
            f"{argument_name} has an invalid ROS-compatible value: {raw_value!r}."
        )
    return raw_value


@dataclass(frozen=True, slots=True)
class _RobotSpec:
    entity_name: str
    namespace: str
    tf_prefix: str
    y: str


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


def _robot_actions(
    spec: _RobotSpec, xacro_path: Path, controller_config: Path
) -> list[Action]:
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                str(xacro_path),
                " control_backend:=gz_ros2_control",
                " controller_parameters_file:=",
                str(controller_config),
                " model_name:=",
                spec.entity_name,
                " ros_namespace:=",
                spec.namespace,
                " tf_prefix:=",
                spec.tf_prefix,
                " lidar_topic:=",
                f"{spec.namespace}/lidar",
                " camera_topic:=",
                f"{spec.namespace}/camera",
                " imu_topic:=",
                f"{spec.namespace}/imu",
            ]
        ),
        value_type=str,
    )
    state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=spec.namespace,
        parameters=[
            {
                "robot_description": robot_description,
                "frame_prefix": spec.tf_prefix,
                "use_sim_time": True,
            }
        ],
        output="screen",
    )
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=spec.namespace,
        arguments=[
            "-name",
            spec.entity_name,
            "-topic",
            "robot_description",
            "-y",
            spec.y,
            "-z",
            "0.12",
        ],
        output="screen",
    )
    manager = f"{spec.namespace}/controller_manager"
    spawner_args = [
        "--controller-manager",
        manager,
        "--controller-manager-timeout",
        "60",
        "--switch-timeout",
        "30",
        "--param-file",
        str(controller_config),
    ]
    manager_ready = ExecuteProcess(
        cmd=[
            "timeout",
            "60",
            "/bin/bash",
            "-c",
            f"until ros2 service type {manager}/list_controllers >/dev/null 2>&1; do sleep 0.2; done",
        ],
        name=f"wait_{spec.entity_name}_controller_manager",
        output="screen",
    )
    joint_state_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=spec.namespace,
        arguments=["joint_state_broadcaster", *spawner_args],
        output="screen",
    )
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=spec.namespace,
        arguments=[
            "diff_drive_controller",
            *spawner_args,
            "--controller-ros-args=-r",
            f"--controller-ros-args={spec.namespace}/diff_drive_controller/odom:={spec.namespace}/odom",
        ],
        output="screen",
    )
    return [
        state_publisher,
        spawn,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn,
                on_exit=_after_success(manager_ready, f"{spec.entity_name} spawn"),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=manager_ready,
                on_exit=_after_success(
                    joint_state_spawner,
                    f"{spec.entity_name} controller-manager readiness",
                ),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=joint_state_spawner,
                on_exit=_after_success(
                    diff_drive_spawner,
                    f"{spec.entity_name} joint-state spawner",
                ),
            )
        ),
    ]


def _launch_stack(context: LaunchContext) -> list[Action]:
    world_name = _validated_launch_argument(
        LaunchConfiguration("world").perform(context),
        "world",
        WORLD_NAME_PATTERN,
    )
    first = _RobotSpec(
        _validated_launch_argument(
            LaunchConfiguration("robot1_name").perform(context),
            "robot1_name",
            NAME_PATTERN,
        ),
        _validated_launch_argument(
            LaunchConfiguration("robot1_namespace").perform(context),
            "robot1_namespace",
            NAMESPACE_PATTERN,
        ),
        "robot1/",
        "1.0",
    )
    second = _RobotSpec(
        _validated_launch_argument(
            LaunchConfiguration("robot2_name").perform(context),
            "robot2_name",
            NAME_PATTERN,
        ),
        _validated_launch_argument(
            LaunchConfiguration("robot2_namespace").perform(context),
            "robot2_namespace",
            NAMESPACE_PATTERN,
        ),
        "robot2/",
        "-1.0",
    )
    if first.entity_name == second.entity_name:
        raise _LaunchContractError(
            f"Entity name collision: both robots requested {first.entity_name!r}."
        )
    if first.namespace == second.namespace:
        raise _LaunchContractError(
            f"ROS namespace collision: both robots requested {first.namespace!r}."
        )
    if (first.namespace, second.namespace) != ("/robot1", "/robot2"):
        raise _LaunchContractError(
            "This installed demonstration requires /robot1 and /robot2 namespaces."
        )

    gazebo_share = Path(get_package_share_directory("tutorial_bot_gazebo"))
    bringup_share = Path(get_package_share_directory("tutorial_bot_bringup"))
    description_share = Path(get_package_share_directory("tutorial_bot_description"))
    control_share = Path(get_package_share_directory("tutorial_bot_control"))
    world_path = gazebo_share / "worlds" / f"{world_name}.sdf"
    if not world_path.is_file():
        raise _LaunchContractError(f"Installed world does not exist: {world_path}.")
    xacro_path = description_share / "urdf" / "tutorial_bot.urdf.xacro"
    controller_config = control_share / "config" / "multi_robot_controllers.yaml"
    bridge_config = bringup_share / "config" / "bridge-multi-robot.yaml"
    for required in (xacro_path, controller_config, bridge_config):
        if not required.is_file():
            raise _LaunchContractError(f"Installed resource does not exist: {required}.")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("ros_gz_sim")) / "launch" / "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": f"-s -r {world_path}", "on_exit_shutdown": "true"}.items(),
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
        arguments=["/robot1/camera/image", "/robot2/camera/image"],
        output="screen",
    )
    return [
        gazebo,
        parameter_bridge,
        image_bridge,
        *_robot_actions(first, xacro_path, controller_config),
        *_robot_actions(second, xacro_path, controller_config),
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value="sensor-test"),
            DeclareLaunchArgument("robot1_name", default_value="robot1"),
            DeclareLaunchArgument("robot2_name", default_value="robot2"),
            DeclareLaunchArgument("robot1_namespace", default_value="/robot1"),
            DeclareLaunchArgument("robot2_namespace", default_value="/robot2"),
            OpaqueFunction(function=_launch_stack),
        ]
    )
