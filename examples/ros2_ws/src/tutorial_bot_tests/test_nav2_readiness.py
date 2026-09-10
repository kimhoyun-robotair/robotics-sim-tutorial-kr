import os
from pathlib import Path
import subprocess
import sys

import pytest
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import OccupancyGrid
from rclpy.context import Context
from rclpy.qos import DurabilityPolicy, QoSProfile
from tf2_ros import StaticTransformBroadcaster

WAITER = Path(__file__).parents[1] / "tutorial_bot_bringup/scripts/wait_localization"


@pytest.mark.parametrize(
    ("publish_map", "publish_tf", "expected_exit"),
    [(True, False, 1), (False, True, 1), (True, True, 0)],
)
def test_localization_requires_both_latched_map_and_tf(
    publish_map: bool, publish_tf: bool, expected_exit: int, tmp_path: Path
) -> None:
    domain = 200 + os.getpid() % 20
    context = Context()
    rclpy.init(context=context, domain_id=domain)
    node = rclpy.create_node("localization_fixture", context=context)
    try:
        publisher = node.create_publisher(
            OccupancyGrid, "/map",
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        broadcaster = StaticTransformBroadcaster(node)
        if publish_map:
            message = OccupancyGrid()
            message.header.frame_id = "map"
            message.info.width = message.info.height = 1
            message.info.resolution = 1.0
            message.data = [0]
            publisher.publish(message)
        if publish_tf:
            transforms = []
            for parent, child in [("map", "odom"), ("odom", "base_link")]:
                transform = TransformStamped()
                transform.header.frame_id = parent
                transform.child_frame_id = child
                transform.transform.rotation.w = 1.0
                transforms.append(transform)
            broadcaster.sendTransform(transforms)

        result = subprocess.run(
            [sys.executable, str(WAITER), "--deadline", "3"],
            env=dict(os.environ, ROS_DOMAIN_ID=str(domain), ROS_HOME=str(tmp_path)),
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == expected_exit, result.stdout + result.stderr
        if expected_exit == 0:
            assert "map_to_odom=ready" in result.stdout
        else:
            assert "Localization timed out" in result.stderr
            assert "map_to_odom=ready" not in result.stdout
    finally:
        node.destroy_node()
        context.try_shutdown()
