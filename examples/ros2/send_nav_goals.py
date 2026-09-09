#!/usr/bin/env python3
"""Send map-frame goals sequentially and record actual ROS action results."""

import argparse
import json
import math
import time
from pathlib import Path

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.signals import SignalHandlerOptions


def spin_until(node, predicate, timeout):
    deadline = time.monotonic() + timeout
    while rclpy.ok() and not predicate():
        if time.monotonic() >= deadline:
            raise TimeoutError("ROS response timed out; check Play, /clock, TF and Nav2 lifecycle")
        rclpy.spin_once(node, timeout_sec=0.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goals", type=Path, help='JSON array: [{"x": ..., "y": ..., "yaw": ...}]')
    parser.add_argument("--action", default="/navigate_to_pose")
    parser.add_argument("--timeout", type=float, default=180.0, help="wall seconds per goal")
    parser.add_argument("--output", type=Path, default=Path("navigation_results.json"))
    args, ros_args = parser.parse_known_args()
    goals = json.loads(args.goals.read_text())
    if not isinstance(goals, list) or not goals:
        parser.error("goals must be a nonempty JSON array")
    for goal in goals:
        if not all(key in goal and math.isfinite(float(goal[key])) for key in ("x", "y", "yaw")):
            parser.error("each goal requires finite x, y and yaw values")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    # Keep the context alive during Ctrl+C cleanup so cancellation can be sent.
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)
    node = Node("course_navigation_test", parameter_overrides=[Parameter("use_sim_time", value=True)])
    client = ActionClient(node, NavigateToPose, args.action)
    results, active, current_index, request = [], None, None, None
    completed = False
    try:
        if not client.wait_for_server(timeout_sec=30.0):
            raise TimeoutError("NavigateToPose server is unavailable")
        spin_until(node, lambda: node.get_clock().now().nanoseconds > 0, 30.0)
        for index, coordinates in enumerate(goals):
            current_index = index
            goal = NavigateToPose.Goal()
            goal.pose.header.frame_id = "map"
            goal.pose.header.stamp = node.get_clock().now().to_msg()
            goal.pose.pose.position.x = float(coordinates["x"])
            goal.pose.pose.position.y = float(coordinates["y"])
            yaw = float(coordinates["yaw"])
            goal.pose.pose.orientation.z = math.sin(yaw / 2)
            goal.pose.pose.orientation.w = math.cos(yaw / 2)
            started = time.monotonic()
            request = client.send_goal_async(goal)
            spin_until(node, request.done, 10.0)
            active = request.result()
            if active is None or not active.accepted:
                raise RuntimeError(f"goal {index} was rejected")
            response = active.get_result_async()
            spin_until(node, response.done, args.timeout)
            result = response.result()
            record = {
                "index": index, "goal": coordinates, "status": int(result.status),
                "wall_seconds": time.monotonic() - started,
                "succeeded": result.status == GoalStatus.STATUS_SUCCEEDED,
            }
            results.append(record)
            active = None
            print(json.dumps(record), flush=True)
            if not record["succeeded"]:
                raise RuntimeError(f"goal {index} did not succeed; remaining goals were skipped")
        completed = True
    except BaseException as error:
        if current_index is not None and not any(row["index"] == current_index for row in results):
            results.append({
                "index": current_index, "goal": goals[current_index],
                "succeeded": False, "error": type(error).__name__ + ": " + str(error),
            })
        raise
    finally:
        # A request can be accepted remotely after our local wait times out.
        # Try to recover its handle, but report uncertainty if that is impossible.
        cancellation = None
        if active is None and not completed and request is not None and rclpy.ok():
            try:
                spin_until(node, request.done, 5.0)
                handle = request.result()
                if handle is not None and handle.accepted:
                    active = handle
            except (TimeoutError, RuntimeError):
                cancellation = "acceptance_unknown_pause_required"
                print("Goal acceptance is unknown. Pause Isaac Sim before inspecting.", flush=True)
        if active is not None and rclpy.ok():
            cancel = active.cancel_goal_async()
            try:
                spin_until(node, cancel.done, 5.0)
                if not cancel.result().goals_canceling:
                    cancellation = "not_confirmed_pause_required"
                    print("Cancellation was not confirmed. Pause Isaac Sim before inspecting.", flush=True)
                else:
                    cancellation = "requested_and_acknowledged"
            except (TimeoutError, RuntimeError):
                cancellation = "timed_out_pause_required"
                print("Cancellation timed out. Pause Isaac Sim before inspecting.", flush=True)
        if cancellation is not None and results:
            results[-1]["cancellation"] = cancellation
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2) + "\n")
        client.destroy()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
