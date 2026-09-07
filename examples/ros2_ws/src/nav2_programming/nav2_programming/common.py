# Copyright 2026 kimhoyun
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Nav2 실습에서 사용하는 입력 검사, 준비 확인, 결과 처리."""

import math
import time

from geometry_msgs.msg import PoseStamped
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.signals import SignalHandlerOptions
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


def validate_poses(values):
    """[x, y, yaw, ...] 배열을 검사하고 세 값씩 묶는다."""
    if not values or len(values) % 3:
        raise ValueError('좌표는 [x, y, yaw] 세 값씩 입력하세요. yaw 단위는 rad입니다.')
    if not all(math.isfinite(value) for value in values):
        raise ValueError('좌표에는 NaN이나 무한대를 사용할 수 없습니다.')
    return [values[index:index + 3] for index in range(0, len(values), 3)]


def make_pose(navigator, values, frame):
    """지도 좌표와 yaw를 유효한 단위 quaternion을 가진 PoseStamped로 바꾼다."""
    pose = PoseStamped()
    pose.header.frame_id = frame
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(values[0])
    pose.pose.position.y = float(values[1])
    pose.pose.orientation.z = math.sin(values[2] / 2.0)
    pose.pose.orientation.w = math.cos(values[2] / 2.0)
    return pose


def wait_for_ready(navigator, buffer, frame, server, timeout):
    """초기 위치를 덮어쓰지 않고 Nav2 활성화와 map TF를 제한 시간 동안 기다린다."""
    deadline = time.monotonic() + timeout
    client = navigator.create_client(GetState, server + '/get_state')
    request = GetState.Request()
    try:
        while rclpy.ok() and time.monotonic() < deadline:
            if not client.wait_for_service(timeout_sec=0.2):
                continue
            future = client.call_async(request)
            rclpy.spin_until_future_complete(navigator, future, timeout_sec=0.5)
            if future.done() and future.result() is not None:
                active = future.result().current_state.id == State.PRIMARY_STATE_ACTIVE
                if active and buffer.can_transform(frame, 'base_link', Time()):
                    return
            else:
                client.remove_pending_request(future)
            rclpy.spin_once(navigator, timeout_sec=0.1)
    finally:
        navigator.destroy_client(client)
    raise RuntimeError(
        'Nav2 또는 map → base_link TF가 준비되지 않았습니다. '
        'Gazebo의 재생 상태, SLAM/AMCL, RViz의 2D Pose Estimate를 확인하세요.')


def run_demo(mode, args=None):
    """목표를 한 번 실행하고 성공 여부에 따라 종료 코드를 반환한다."""
    # Ctrl+C를 직접 처리하여 취소 요청을 보낸 뒤 ROS context를 종료한다.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    navigator = None
    listener = None
    task_running = False
    exit_code = 1
    try:
        navigator = BasicNavigator(node_name='rover_' + mode)
        if not navigator.get_parameter('use_sim_time').value:
            raise ValueError('시뮬레이션 예제입니다. --ros-args -p use_sim_time:=true를 추가하세요.')
        frame = navigator.declare_parameter('frame_id', 'map').value
        timeout = navigator.declare_parameter('timeout_sec', 180.0).value
        startup_timeout = navigator.declare_parameter('startup_timeout_sec', 60.0).value
        if not frame or not all(
                math.isfinite(value) and value > 0 for value in (timeout, startup_timeout)):
            raise ValueError('frame_id를 지정하고 timeout 값은 양의 유한수로 입력하세요.')

        if mode == 'navigate_to_pose':
            values = navigator.declare_parameter('goal', [1.0, 0.0, 0.0]).value
            triples = validate_poses(values)
            if len(triples) != 1:
                raise ValueError('goal에는 [x, y, yaw] 한 개만 입력하세요.')
        else:
            values = navigator.declare_parameter(
                'waypoints', [1.0, 0.0, 0.0, 1.0, 1.0, 1.57]).value
            triples = validate_poses(values)

        buffer = Buffer()
        listener = TransformListener(buffer, navigator)
        server = 'waypoint_follower' if mode == 'follow_waypoints' else 'bt_navigator'
        navigator.get_logger().info('Nav2와 지도 좌표계를 확인합니다. 초기 위치는 RViz에서 지정하세요.')
        wait_for_ready(navigator, buffer, frame, server, startup_timeout)
        poses = [make_pose(navigator, triple, frame) for triple in triples]
        if mode == 'navigate_to_pose':
            accepted = navigator.goToPose(poses[0])
        elif mode == 'navigate_through_poses':
            accepted = navigator.goThroughPoses(poses)
        else:
            accepted = navigator.followWaypoints(poses)
        if not accepted:
            raise RuntimeError('Nav2가 목표를 거절했습니다. 좌표와 서버 상태를 확인하세요.')

        task_running = True
        started = time.monotonic()
        last_report = started
        while rclpy.ok() and not navigator.isTaskComplete():
            now = time.monotonic()
            if now - started > timeout:
                navigator.cancelTask()
                raise RuntimeError(f'이동 제한 시간 {timeout:.0f}초를 넘겨 목표를 취소했습니다.')
            if now - last_report >= 2.0:
                feedback = navigator.getFeedback()
                if feedback and hasattr(feedback, 'distance_remaining'):
                    navigator.get_logger().info(
                        f'남은 거리: {feedback.distance_remaining:.2f} m')
                elif feedback and hasattr(feedback, 'current_waypoint'):
                    navigator.get_logger().info(
                        f'이동 중인 waypoint: {feedback.current_waypoint + 1}/{len(poses)}')
                last_report = now

        task_running = False
        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            navigator.get_logger().info('목표 이동을 완료했습니다.')
            exit_code = 0
        elif result == TaskResult.CANCELED:
            navigator.get_logger().warning('목표 이동이 취소되었습니다.')
        else:
            navigator.get_logger().error(f'목표 이동에 실패했습니다: {result}')
    except KeyboardInterrupt:
        exit_code = 130
    except ExternalShutdownException:
        exit_code = 130
    except (ValueError, RuntimeError) as error:
        if navigator is not None:
            navigator.get_logger().error(str(error))
        else:
            print(error)
    finally:
        if navigator is not None:
            if task_running and rclpy.ok():
                navigator.cancelTask()
            if listener is not None:
                listener.unregister()
            navigator.destroyNode()
        if rclpy.ok():
            rclpy.shutdown()
    return exit_code

