"""Receive a retained String sample with explicit subscriber QoS and timeout."""
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/topic")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--volatile", action="store_true", help="do not request retained history")
    parser.add_argument("--best-effort", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    import rclpy
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from std_msgs.msg import String
    rclpy.init()
    node = rclpy.create_node("local_qos_observer")
    samples = []
    profile = QoSProfile(depth=1,
        durability=DurabilityPolicy.VOLATILE if args.volatile else DurabilityPolicy.TRANSIENT_LOCAL,
        reliability=ReliabilityPolicy.BEST_EFFORT if args.best_effort else ReliabilityPolicy.RELIABLE)
    try:
        subscription = node.create_subscription(String, args.topic, lambda message: samples.append(message.data), profile)
        end = time.monotonic() + args.timeout
        while rclpy.ok() and time.monotonic() < end and not samples:
            rclpy.spin_once(node, timeout_sec=0.1)
        if not samples:
            raise TimeoutError(f"No String received on {args.topic} within {args.timeout} s")
        print("received_data=", repr(samples[0]))
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
