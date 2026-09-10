from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import Action, LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    GroupAction,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.events.process import ProcessExited
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_stack(context: LaunchContext) -> list[Action]:
    amcl_enabled = IfCondition(LaunchConfiguration("amcl")).evaluate(context)
    map_path = LaunchConfiguration("map").perform(context)
    params_path = LaunchConfiguration("params_file").perform(context)
    for path in (map_path, params_path):
        if not Path(path).is_file():
            raise RuntimeError(f"Navigation resource does not exist: {path}")

    parameters = [params_path, {"use_sim_time": True}]
    localization_nodes = ["map_server"]
    localization: list[Action] = [
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            parameters=[*parameters, {"yaml_filename": map_path}],
            output="screen",
        ),
    ]
    if amcl_enabled:
        localization_nodes.append("amcl")
        localization.append(
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                parameters=parameters,
                output="screen",
            )
        )
    else:
        localization.extend(
            [
                LogInfo(
                    msg="AMCL disabled: map and odom share the simulation start origin; odometry drift is not corrected."
                ),
                Node(
                    package="tf2_ros",
                    executable="static_transform_publisher",
                    name="map_to_odom",
                    arguments=["--frame-id", "map", "--child-frame-id", "odom"],
                    parameters=[{"use_sim_time": True}],
                    output="screen",
                ),
            ]
        )
    localization.append(
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_localization",
            parameters=[
                {
                    "use_sim_time": True,
                    "autostart": True,
                    "node_names": localization_nodes,
                }
            ],
            output="screen",
        )
    )

    servers = (
        ("nav2_controller", "controller_server"),
        ("nav2_smoother", "smoother_server"),
        ("nav2_planner", "planner_server"),
        ("nav2_behaviors", "behavior_server"),
        ("nav2_velocity_smoother", "velocity_smoother"),
        ("nav2_collision_monitor", "collision_monitor"),
        ("nav2_bt_navigator", "bt_navigator"),
    )
    navigation = GroupAction(
        actions=[
            *[
                Node(
                    package=package,
                    executable=name,
                    name=name,
                    parameters=parameters,
                    remappings=[("cmd_vel", "cmd_vel_nav")]
                    if name
                    in {"controller_server", "behavior_server", "velocity_smoother"}
                    else [],
                    output="screen",
                )
                for package, name in servers
            ],
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_navigation",
                parameters=[
                    {
                        "use_sim_time": True,
                        "autostart": True,
                        "node_names": [name for _, name in servers],
                    }
                ],
                output="screen",
            ),
        ]
    )
    localization_ready = ExecuteProcess(
        cmd=[
            "timeout",
            "60",
            "ros2",
            "run",
            "tutorial_bot_bringup",
            "wait_localization",
        ],
        name="wait_localization",
        output="screen",
    )

    def start_navigation(event: ProcessExited, _: LaunchContext) -> list[Action]:
        if event.returncode == 0:
            return [navigation]
        return [
            EmitEvent(
                event=Shutdown(reason="Map or localization TF did not become ready.")
            )
        ]

    return [
        *localization,
        RegisterEventHandler(
            OnProcessExit(target_action=localization_ready, on_exit=start_navigation)
        ),
        localization_ready,
    ]


def generate_launch_description() -> LaunchDescription:
    bringup = Path(get_package_share_directory("tutorial_bot_bringup"))
    gazebo = Path(get_package_share_directory("tutorial_bot_gazebo"))
    return LaunchDescription(
        [
            DeclareLaunchArgument("amcl", default_value="true"),
            DeclareLaunchArgument(
                "map", default_value=str(gazebo / "maps" / "training.yaml")
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=str(bringup / "config" / "nav2_params.yaml"),
            ),
            OpaqueFunction(function=_launch_stack),
        ]
    )
