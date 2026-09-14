"""ROS 2-side Python (Jazzy): SLAM Toolbox와 최소 Nav2 서버를 실행한다."""

from pathlib import Path

from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node


def generate_launch_description():
    config = str(Path(__file__).resolve().parents[1] / "configs" / "navigation.yaml")
    servers = [
        ("nav2_controller", "controller_server"),
        ("nav2_planner", "planner_server"),
        ("nav2_behaviors", "behavior_server"),
        ("nav2_bt_navigator", "bt_navigator"),
    ]
    nodes = [
        Node(
            package=package,
            executable=name,
            name=name,
            output="screen",
            parameters=[config],
        )
        for package, name in servers
    ]
    nodes.append(
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[config, {"use_lifecycle_manager": True}],
        )
    )
    nodes.append(
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_navigation",
            output="screen",
            parameters=[
                {
                    "use_sim_time": True,
                    "autostart": True,
                    "node_names": ["slam_toolbox"] + [name for _, name in servers],
                }
            ],
        )
    )
    return LaunchDescription(nodes)


if __name__ == "__main__":
    service = LaunchService()
    service.include_launch_description(generate_launch_description())
    raise SystemExit(service.run())
