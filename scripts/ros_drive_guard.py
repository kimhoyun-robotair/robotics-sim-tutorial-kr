#!/usr/bin/env python3
"""Wall-clock watchdog and finite, bounded Twist relay for simulated robots."""
import argparse
import math
import time


def bounded(value, limit):
    if not math.isfinite(value):
        return 0.0
    return max(-limit, min(limit, value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="/tutorial/cmd_vel_raw")
    parser.add_argument("--output", default="/tutorial/cmd_vel")
    parser.add_argument("--timeout", type=float, default=0.5)
    parser.add_argument("--linear-limit", type=float, default=0.2)
    parser.add_argument("--angular-limit", type=float, default=0.6)
    args = parser.parse_args()
    if args.input == args.output:
        parser.error("input and output topics must differ")
    if not (0.1 <= args.timeout <= 1.0 and 0 < args.linear_limit <= 0.2
            and 0 < args.angular_limit <= 0.6):
        parser.error("timeout: 0.1..1 s; linear limit: 0..0.2 m/s; angular limit: 0..0.6 rad/s")
    import rclpy
    from rclpy.qos import QoSProfile
    from geometry_msgs.msg import Twist

    rclpy.init(args=[])
    node = rclpy.create_node("tutorial_drive_guard")
    publisher = node.create_publisher(Twist, args.output, 1)
    state = {"v": 0.0, "w": 0.0, "time": -math.inf}

    def receive(message):
        if math.isfinite(message.linear.x) and math.isfinite(message.angular.z):
            state["v"] = bounded(message.linear.x, args.linear_limit)
            state["w"] = bounded(message.angular.z, args.angular_limit)
        else:
            state["v"] = state["w"] = 0.0
        state["time"] = time.monotonic()

    node.create_subscription(Twist, args.input, receive, QoSProfile(depth=1))
    print(f"Guard active: {args.input} -> {args.output}, timeout={args.timeout}s (wall time)")
    try:
        while rclpy.ok():
            start = time.monotonic()
            rclpy.spin_once(node, timeout_sec=0.01)
            message = Twist()
            if time.monotonic() - state["time"] <= args.timeout:
                message.linear.x, message.angular.z = state["v"], state["w"]
            publisher.publish(message)
            time.sleep(max(0.0, 0.05 - (time.monotonic() - start)))
    except KeyboardInterrupt:
        pass
    finally:
        # Best effort shutdown; the receiving simulator must also enforce its own watchdog.
        if rclpy.ok():
            for _ in range(3):
                publisher.publish(Twist())
                time.sleep(0.05)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
