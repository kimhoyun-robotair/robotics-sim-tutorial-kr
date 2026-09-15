"""Observe real TF/odometry messages for a bounded interval and report frames."""
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    import rclpy
    from tf2_msgs.msg import TFMessage
    from nav_msgs.msg import Odometry
    rclpy.init()
    node = rclpy.create_node("local_tf_observer")
    edges = set()
    poses = []
    def on_tf(message):
        for transform in message.transforms:
            edges.add((transform.header.frame_id, transform.child_frame_id))
    def on_odom(message):
        poses.append(message)
    try:
        tf_sub = node.create_subscription(TFMessage, "/tf", on_tf, 10)
        odom_sub = node.create_subscription(Odometry, "/odom", on_odom, 10)
        end = time.monotonic() + args.seconds
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
        if not edges or not poses:
            raise TimeoutError(f"Observed {len(edges)} TF edges and {len(poses)} odometry messages")
        print("observed_tf_edges=", sorted(edges))
        message = poses[-1]
        print("odom_frame=", message.header.frame_id, "child=", message.child_frame_id)
        print("pose=", message.pose.pose, "twist=", message.twist.twist)
        if (message.header.frame_id, message.child_frame_id) not in edges:
            raise ValueError("Odometry parent/child edge missing from observed TF tree")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
