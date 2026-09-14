"""ROS 2-side Python: NavigateToPose action을 보내고 SUCCEEDED 결과를 확인한다."""

import argparse
import math
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from rclpy.action import ActionClient
from rclpy.parameter import Parameter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x", type=float, default=0.8)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--yaw", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=180.0, help="wall seconds")
    args = parser.parse_args()
    if (
        not all(math.isfinite(v) for v in (args.x, args.y, args.yaw, args.timeout))
        or args.timeout <= 0
    ):
        parser.error("좌표는 유한한 수, timeout은 양수여야 합니다.")
    rclpy.init()
    node = rclpy.create_node(
        "learning_navigation_goal",
        parameter_overrides=[Parameter("use_sim_time", value=True)],
    )
    client = ActionClient(node, NavigateToPose, "navigate_to_pose")
    try:
        if not client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError("Nav2 action server를 찾지 못했습니다.")
        state_client = node.create_client(GetState, "/bt_navigator/get_state")
        if not state_client.wait_for_service(timeout_sec=30.0):
            raise RuntimeError("Nav2 lifecycle service를 찾지 못했습니다.")
        deadline = time.monotonic() + 30.0
        active = False
        while time.monotonic() < deadline:
            state = state_client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(node, state, timeout_sec=1.0)
            if (
                state.done()
                and state.result().current_state.id == State.PRIMARY_STATE_ACTIVE
            ):
                active = True
                break
            time.sleep(0.1)
        node.destroy_client(state_client)
        if not active:
            raise RuntimeError(
                "Nav2가 active 상태가 되지 않았습니다. SLAM/TF 로그를 확인하세요."
            )
        deadline = time.monotonic() + 10.0
        while node.get_clock().now().nanoseconds == 0 and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.get_clock().now().nanoseconds == 0:
            raise RuntimeError("/clock을 수신하지 못했습니다.")
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.position.x, pose.pose.position.y = args.x, args.y
        pose.pose.orientation.z, pose.pose.orientation.w = (
            math.sin(args.yaw / 2),
            math.cos(args.yaw / 2),
        )
        future = client.send_goal_async(NavigateToPose.Goal(pose=pose))
        rclpy.spin_until_future_complete(node, future, timeout_sec=10.0)
        if not future.done():
            raise RuntimeError("Nav2 goal 응답 시간이 초과되었습니다.")
        handle = future.result()
        if handle is None or not handle.accepted:
            raise RuntimeError("Nav2가 goal을 거절했습니다.")
        result = handle.get_result_async()
        rclpy.spin_until_future_complete(node, result, timeout_sec=args.timeout)
        if not result.done():
            cancel = handle.cancel_goal_async()
            rclpy.spin_until_future_complete(node, cancel, timeout_sec=5.0)
            raise RuntimeError("이동 시간이 초과되어 goal 취소를 요청했습니다.")
        status = result.result().status
        if status != GoalStatus.STATUS_SUCCEEDED:
            raise RuntimeError(f"Navigation 실패: action status={status}")
        print("Navigation SUCCEEDED")
    finally:
        client.destroy()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
