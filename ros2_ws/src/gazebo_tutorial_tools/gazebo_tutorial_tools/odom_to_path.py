"""Convert a bounded stream of nav_msgs/Odometry messages to nav_msgs/Path."""

from collections import deque
from typing import Deque, Dict, Optional

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)


_RELIABILITY: Dict[str, QoSReliabilityPolicy] = {
    'best_effort': QoSReliabilityPolicy.BEST_EFFORT,
    'reliable': QoSReliabilityPolicy.RELIABLE,
    'system_default': QoSReliabilityPolicy.SYSTEM_DEFAULT,
}

_DURABILITY: Dict[str, QoSDurabilityPolicy] = {
    'volatile': QoSDurabilityPolicy.VOLATILE,
    'transient_local': QoSDurabilityPolicy.TRANSIENT_LOCAL,
    'system_default': QoSDurabilityPolicy.SYSTEM_DEFAULT,
}


def _policy_key(value: str) -> str:
    """Normalize a human-friendly QoS policy name."""
    return value.strip().lower().replace('-', '_')


def _qos_profile(
    reliability: str,
    durability: str,
    depth: int,
) -> QoSProfile:
    """Build a keep-last QoS profile and fail early on invalid settings."""
    reliability_key = _policy_key(reliability)
    durability_key = _policy_key(durability)

    if reliability_key not in _RELIABILITY:
        choices = ', '.join(sorted(_RELIABILITY))
        raise ValueError(
            f'unknown reliability policy {reliability!r}; choose one of: {choices}'
        )
    if durability_key not in _DURABILITY:
        choices = ', '.join(sorted(_DURABILITY))
        raise ValueError(
            f'unknown durability policy {durability!r}; choose one of: {choices}'
        )
    if depth < 1:
        raise ValueError('QoS depth must be at least 1')

    return QoSProfile(
        history=QoSHistoryPolicy.KEEP_LAST,
        depth=depth,
        reliability=_RELIABILITY[reliability_key],
        durability=_DURABILITY[durability_key],
    )


def _stamp_to_nanoseconds(stamp) -> int:
    """Convert builtin_interfaces/Time without depending on a clock instance."""
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


class OdomToPath(Node):
    """Accumulate odometry poses and publish a bounded RViz Path."""

    def __init__(self) -> None:
        super().__init__('odom_to_path')

        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('path_topic', '/wheel_odom_path')
        self.declare_parameter('path_frame', '')
        self.declare_parameter('max_points', 2000)
        self.declare_parameter('input_qos_reliability', 'best_effort')
        self.declare_parameter('input_qos_durability', 'volatile')
        self.declare_parameter('input_qos_depth', 20)
        self.declare_parameter('output_qos_reliability', 'reliable')
        self.declare_parameter('output_qos_durability', 'transient_local')
        self.declare_parameter('output_qos_depth', 1)

        odom_topic = str(self.get_parameter('odom_topic').value)
        path_topic = str(self.get_parameter('path_topic').value)
        self._path_frame = str(self.get_parameter('path_frame').value).strip()
        max_points = int(self.get_parameter('max_points').value)

        input_qos = _qos_profile(
            str(self.get_parameter('input_qos_reliability').value),
            str(self.get_parameter('input_qos_durability').value),
            int(self.get_parameter('input_qos_depth').value),
        )
        output_qos = _qos_profile(
            str(self.get_parameter('output_qos_reliability').value),
            str(self.get_parameter('output_qos_durability').value),
            int(self.get_parameter('output_qos_depth').value),
        )

        # max_points <= 0 deliberately means an unbounded path. A bounded value is
        # strongly recommended for a long-running simulation.
        self._poses: Deque[PoseStamped] = deque(
            maxlen=max_points if max_points > 0 else None
        )
        self._active_frame: Optional[str] = None
        self._last_stamp_ns: Optional[int] = None
        self._reported_frame_mismatch = False

        self._publisher = self.create_publisher(Path, path_topic, output_qos)
        self._subscription = self.create_subscription(
            Odometry,
            odom_topic,
            self._odom_callback,
            input_qos,
        )

        limit_text = str(max_points) if max_points > 0 else 'unbounded'
        frame_text = self._path_frame or '<from odometry>'
        self.get_logger().info(
            f'converting {odom_topic} -> {path_topic}; '
            f'frame={frame_text}, max_points={limit_text}'
        )

    def _clear_path(self) -> None:
        self._poses.clear()
        self._last_stamp_ns = None

    def _odom_callback(self, message: Odometry) -> None:
        source_frame = message.header.frame_id.strip()
        if not source_frame:
            self.get_logger().warning(
                'received odometry with an empty header.frame_id; message ignored',
                once=True,
            )
            return

        output_frame = self._path_frame or source_frame
        if output_frame != source_frame:
            # Relabelling a pose is not a TF transform. Refuse it so RViz never
            # displays a geometrically incorrect trajectory.
            if not self._reported_frame_mismatch:
                self.get_logger().error(
                    'path_frame differs from odometry header.frame_id '
                    f'({output_frame!r} != {source_frame!r}). '
                    'This node does not transform poses; use the odometry frame '
                    'or transform the input first.'
                )
                self._reported_frame_mismatch = True
            return

        if self._active_frame is not None and source_frame != self._active_frame:
            self.get_logger().warning(
                f'odometry frame changed from {self._active_frame!r} to '
                f'{source_frame!r}; clearing the stored path'
            )
            self._clear_path()
        self._active_frame = source_frame

        stamp_ns = _stamp_to_nanoseconds(message.header.stamp)
        if self._last_stamp_ns is not None and stamp_ns < self._last_stamp_ns:
            self.get_logger().warning(
                'simulation time moved backwards; clearing the stored path'
            )
            self._clear_path()

        # message.pose.pose is copied by ROS serialization when Path is published.
        pose = PoseStamped()
        pose.header = message.header
        pose.pose = message.pose.pose
        self._poses.append(pose)
        self._last_stamp_ns = stamp_ns

        path = Path()
        path.header.stamp = message.header.stamp
        path.header.frame_id = output_frame
        path.poses = list(self._poses)
        self._publisher.publish(path)


def main(args=None) -> None:
    """Run the odometry-to-path node."""
    rclpy.init(args=args)
    node = None
    try:
        node = OdomToPath()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
