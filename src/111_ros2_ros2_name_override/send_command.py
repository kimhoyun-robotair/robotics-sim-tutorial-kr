"""Send a small, bounded position command to one Franka joint with ROS 2."""
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint", default="shoulder_pan")
    parser.add_argument("--position", type=float, default=0.3, help="radians")
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    import rclpy
    from sensor_msgs.msg import JointState
    rclpy.init()
    node = rclpy.create_node("local_joint_command")
    try:
        pub = node.create_publisher(JointState, "/joint_command", 10)
        end = time.monotonic() + args.seconds
        while rclpy.ok() and time.monotonic() < end:
            message = JointState()
            message.header.stamp = node.get_clock().now().to_msg()
            message.name = [args.joint]
            message.position = [args.position]
            pub.publish(message)
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
