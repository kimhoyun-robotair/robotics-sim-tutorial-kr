# 33. 중간 프로젝트 6 — ROS 폐루프로 목표 위치에 도달하기

[전체 목차](../../README.md) · [이전](32-ros-sensors.md) · [다음](34-command-safety.md)

## 완성할 결과

외부 ROS Python 프로그램이 현재 위치를 읽고, 목표에 가까워질수록 속도를 줄여 정지하는 실험을 만든다. 명령은 ROS를 통해 Isaac Sim에 들어오고, Isaac Sim이 계산한 위치는 odometry와 TF로 돌아간다. 관절·메시·센서 자산 없이 재현하도록 **기구학으로 움직이는 직육면체**를 사용한다. 이 프로젝트의 통과는 DDS 통신과 폐루프 동작의 근거이며 바퀴 접촉, 전도 안정성, 실제 로봇 제동 성능의 근거는 아니다.

필요한 파일은 저장소에 들어 있다.

| 파일 | 역할 |
|---|---|
| [07_ros_scene.py](../../examples/07_ros_scene.py) | 바닥·조명·직육면체, clock, 명령 수신, odometry·TF |
| [ros_goal.py](../../scripts/ros_goal.py) | odometry를 읽는 외부 목표 추종 프로그램 |
| [ros_acceptance.py](../../scripts/ros_acceptance.py) | 실제 수신과 명령 끊김 후 정지를 검사 |
| [ros_topics.yaml](../../config/ros_topics.yaml) | 사용 토픽·제한값을 정리한 명세 |

`ros_topics.yaml`은 ROS parameter 파일이 아니라 설명용 명세이다. 값만 편집해도 Python 프로그램에 자동 적용되는 구성은 아니다.

## 1. 세 터미널의 실행 환경을 맞춘다

29단계의 공통 설정을 터미널 A, B, C에서 적용한다. 각 터미널이 저장소 루트에 있는지 확인하고 기존 clock 예제·teleop·Nav2는 종료한다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
cd "$TUTORIAL_ROOT"
mkdir -p artifacts
```

터미널 A에서 장면을 실행한다.

```bash
"$ISAAC_SIM_PATH/python.sh" examples/07_ros_scene.py --seconds 180 \
  --output artifacts/project6-scene.json
```

`READY`가 출력되고 파란 직육면체가 나타나면 준비된 상태이다. 화면에서 잘 보이지 않으면 Stage의 `/World/TutorialBase`를 선택한 뒤 `F`로 화면을 맞춘다. 처음 위치는 x=0, y=0, yaw=0이다.

## 2. 발행 중인 상태를 읽는다

터미널 B에서 다음을 실행한다.

```bash
ros2 topic info /tutorial/cmd_vel --verbose
ros2 topic echo /tutorial/odom --once
timeout 5s ros2 run tf2_ros tf2_echo odom tutorial_base
```

`/tutorial/cmd_vel`의 구독자는 있어야 하지만 아직 명령 발행자가 없는 것이 정상이다. 메시지의 `header.frame_id`는 `odom`, `child_frame_id`는 `tutorial_base`이다. quaternion은 `(x,y,z,w)=(0,0,0,1)`에서 시작한다.

## 3. 목표 추종을 실행한다

터미널 C에서 먼저 15초의 관찰 검사를 시작한다.

```bash
python3 scripts/ros_acceptance.py --mode scene --duration 15 \
  --output artifacts/project6-observation.json
```

이어서 터미널 B에서 실행한다.

```bash
python3 scripts/ros_goal.py --distance 0.6 --timeout 30 \
  --output artifacts/project6-goal.json
```

컨트롤러는 처음 받은 odometry의 위치와 방향에서 전방 0.6 m 지점을 목표로 정한다. 정상 실행에서는 `final_error_m`가 0.03 미만이 되고, 0 속도를 보내며 odometry 속도가 낮은 상태를 벽시계 0.5초 동안 확인한 뒤 `status: PASS`, `reason: goal_reached`가 출력된다. 장면의 직육면체가 목표 가까이에서 감속해 멈추는지 확인한다. 프로세스가 종료될 때는 0 속도 명령도 보낸다.

핵심 계산은 아래와 같다. 실제 파일에는 수신 timeout, 유한값 검사, 실행시간 제한, 작업영역 검사가 포함되어 있다.

```python
dx = goal_x - current_x
dy = goal_y - current_y
distance = math.hypot(dx, dy)
heading_error = math.atan2(dy, dx) - current_yaw
heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))

command.angular.z = max(-0.5, min(0.5, 2.0 * heading_error))
if abs(heading_error) < 0.3:
    command.linear.x = min(0.15, 0.8 * distance)
if distance < 0.03:
    command = Twist()
```

목표가 옆이나 뒤에 있으면 우선 방향을 맞춘다. 목표와의 거리에 비례해 선속도를 낮추되 상한을 둔다. 매번 0.6 m를 무조건 이동시키는 시간 명령과 달리, 실제 수신한 odometry를 다음 명령 계산에 사용하므로 폐루프이다.

Isaac Sim 쪽은 다음과 같이 1/60초의 기구학을 적분한다.

```python
next_x = x + linear_velocity * math.cos(yaw) * dt
next_y = y + linear_velocity * math.sin(yaw) * dt
next_yaw = yaw + angular_velocity * dt
```

직육면체에는 Rigid Body API와 관절을 붙이지 않았다. 따라서 transform을 갱신하는 작업이 PhysX의 rigid-body pose 갱신과 충돌하지 않는다. 실제 로봇으로 교체할 때는 이 코드를 그대로 몸체에 적용하지 않고, 로봇 controller의 바퀴·관절 명령으로 바꾸어야 한다.

## 4. 명령 연결이 끊기는 상황을 시험한다

`ros_goal.py`가 끝난 뒤 다른 teleop이나 guard가 없는 상태에서 실행한다.

```bash
python3 scripts/ros_acceptance.py --mode scene --duration 10 \
  --exercise-timeout --output artifacts/project6-timeout.json
```

이 옵션은 관찰만 하는 옵션이 아니다. 검사기가 직접 0.1 m/s 명령을 2초간 보내다가 발행을 멈춘다. 시뮬레이터는 마지막 명령을 받은 뒤 **벽시계 0.5초**가 지나면 선속도와 각속도를 0으로 만든다. 이후 pose가 더 변하지 않는지 검사한다.

```python
if time.monotonic() - last_command_wall_time > 0.5:
    linear_velocity = 0.0
    angular_velocity = 0.0
```

정상 결과에는 `command_caused_motion`, `watchdog_observed_stop`, `pose_stable_after_timeout`이 모두 `true`로 나타난다. 렌더링 한 프레임이 매우 오래 걸린다면 정지 처리도 다음 루프까지 지연된다. 이 값은 GPU가 멈춘 상태에서도 0.5초 안에 실제 하드웨어를 제동한다는 보장이 아니다.

## 제출할 결과와 과제

`project6-goal.json`, `project6-observation.json`, `project6-timeout.json`과 정지 직전·직후 odometry를 저장한다. `project6-scene.json`은 장면 실행 자체의 결과이며 외부 메시지 수신을 대신 증명하지 않는다. 검사를 실제로 수행하지 않았다면 결과를 생성하거나 PASS라고 기록하지 않는다.

과제로 목표 거리를 0.3 m와 0.9 m로 바꾸어 도달시간과 최종 오차를 비교한다. 세 번째 실행부터는 작업영역 경계에 가까워질 수 있으므로 장면을 종료하고 다시 실행해 원점에서 시작한다. `Stop/Play`로 시간만 되감는 방식은 이 예제의 새 실행 절차로 사용하지 않는다.

실패하면 환경 문제는 29단계, 시간·QoS는 30단계, 좌표계는 31단계로 돌아간다. 목표가 작업영역 밖이면 `goal_outside_fixture_workspace`, 메시지가 없거나 느려 목표에 도달하지 못하면 `timeout`으로 실패한다. timeout을 무조건 늘리기 전에 odometry의 최근 수신 여부와 RTF를 확인한다.

구성 원리는 NVIDIA의 [standalone ROS 연결](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_python.html)과 [generic subscriber](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html)를 참고했으며, 이 장면과 검사기는 본 튜토리얼의 독립 예제이다.
