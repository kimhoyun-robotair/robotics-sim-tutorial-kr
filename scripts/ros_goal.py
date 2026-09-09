#!/usr/bin/env python3
"""Move the tutorial kinematic scene toward a relative XY goal using odometry."""
import argparse
import json
import math
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distance", type=float, default=0.6)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=Path("artifacts/ros_goal.json"))
    args = parser.parse_args()
    if not (0.1 <= args.distance <= 1.0 and 5 <= args.timeout <= 120):
        parser.error("distance must be 0.1..1 m, timeout 5..120 s")
    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from rclpy.qos import qos_profile_sensor_data

    rclpy.init(args=[])
    node = rclpy.create_node("tutorial_relative_goal")
    publisher = node.create_publisher(Twist, "/tutorial/cmd_vel", 1)
    state = {"odom": None, "received": -math.inf, "stamp": None, "invalid": None}

    def receive(message):
        stamp = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        if stamp <= 0 or (state["stamp"] is not None and stamp <= state["stamp"]):
            state["invalid"] = "nonmonotonic_odometry_timestamp"
        if message.header.frame_id != "odom" or message.child_frame_id != "tutorial_base":
            state["invalid"] = "unexpected_odometry_frames"
        state["stamp"] = stamp
        state["odom"] = message
        state["received"] = time.monotonic()

    node.create_subscription(Odometry, "/tutorial/odom", receive, qos_profile_sensor_data)
    report = {"status": "FAIL", "reason": "timeout", "distance": args.distance}
    goal = None
    settled_since = None
    deadline = time.monotonic() + args.timeout
    try:
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.02)
            message = Twist()
            if state["invalid"] is not None:
                report["reason"] = state["invalid"]
                break
            odom = state["odom"]
            if odom is not None and time.monotonic() - state["received"] < 0.5:
                pose = odom.pose.pose
                q = pose.orientation
                values = (pose.position.x, pose.position.y, q.x, q.y, q.z, q.w)
                if not all(math.isfinite(v) for v in values):
                    report["reason"] = "nonfinite_odometry"
                    break
                if abs(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w - 1.0) > 1e-3:
                    report["reason"] = "unnormalized_odometry_quaternion"
                    break
                yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y*q.y + q.z*q.z))
                if goal is None:
                    goal = (pose.position.x + args.distance * math.cos(yaw),
                            pose.position.y + args.distance * math.sin(yaw))
                    if max(abs(goal[0]), abs(goal[1])) > 1.8:
                        report["reason"] = "goal_outside_fixture_workspace"
                        break
                    report["goal_xy"] = list(goal)
                dx, dy = goal[0] - pose.position.x, goal[1] - pose.position.y
                distance = math.hypot(dx, dy)
                report["final_error_m"] = distance
                if distance < 0.03:
                    velocity = odom.twist.twist
                    if abs(velocity.linear.x) < 0.005 and abs(velocity.angular.z) < 0.01:
                        if settled_since is None:
                            settled_since = time.monotonic()
                        if time.monotonic() - settled_since >= 0.5:
                            report.update(status="PASS", reason="goal_reached", settled_wall_seconds=0.5)
                            break
                    else:
                        settled_since = None
                else:
                    settled_since = None
                    error = math.atan2(math.sin(math.atan2(dy, dx) - yaw),
                                       math.cos(math.atan2(dy, dx) - yaw))
                    message.angular.z = max(-0.5, min(0.5, 2.0 * error))
                    if abs(error) < 0.3:
                        message.linear.x = min(0.15, 0.8 * distance)
            else:
                settled_since = None
            publisher.publish(message)
            time.sleep(0.03)
    except KeyboardInterrupt:
        report["reason"] = "interrupted"
    finally:
        if rclpy.ok():
            for _ in range(5):
                publisher.publish(Twist())
                time.sleep(0.05)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
