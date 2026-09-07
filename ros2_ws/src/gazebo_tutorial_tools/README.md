# gazebo_tutorial_tools

ROS 2 Humble 실습에서 오도메트리와 경로를 계산하는 Python 노드를 모은 패키지다.
`odom_to_path`는 오도메트리를 RViz에 그릴 경로로 바꾸고, `ackermann_odom`은
Ackermann 로버의 바퀴·조향 조인트 상태에서 이동량을 계산한다.

## 준비

[Humble 환경 설정](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/docs/01_setup.md)을
마친 뒤 전체 작업 공간을 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

새 터미널을 열 때마다 `/opt/ros/humble/setup.bash`와 이 작업 공간의
`install/setup.bash`를 차례로 불러온다. 아래 `ros2 run` 명령은 해당 노드를
직접 연결하는 별도 구성용이다. 기본 실행 파일이 이미 같은 노드를 시작했다면
중복 실행하지 않는다.

## `odom_to_path`: 오도메트리를 경로로 표시하기

입력 `nav_msgs/msg/Odometry`의 위치와 자세를 누적해 `nav_msgs/msg/Path`로
발행한다. 기본 입력은 `/odom`, 출력은 `/wheel_odom_path`다. 최근 2,000개
기록만 보관하므로 기본 설정에서는 실행 시간이 길어져도 기록 개수가 계속 늘지 않는다.

### 기본 로봇에서 확인하기

터미널 1에서 로봇을 실행한다. 이 실행 파일이 `odom_to_path`도 함께 시작한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

터미널 2에서 환경을 불러온 뒤 출력 헤더를 확인한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 topic echo /wheel_odom_path --once --field header \
  --qos-reliability reliable --qos-durability transient_local
```

`frame_id: odom`이 나오고, 주행할 때 RViz의 초록색 경로가 늘어나야 한다.
데이터가 오지 않으면 `Ctrl+C`로 대기를 끝내고 `/odom` 발행 여부부터 확인한다.

### 별도 로봇에 연결하기

직접 구성한 로봇이 `/odom`을 발행하고 있다면 새 터미널에서 다음 노드를 실행한다.
이 명령은 노드를 계속 실행하며 `Ctrl+C`로 종료한다.

```bash
ros2 run gazebo_tutorial_tools odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_points:=2000
```

| 파라미터 | 기본값 | 의미 |
|---|---:|---|
| `odom_topic` | `/odom` | 입력 오도메트리 토픽 |
| `path_topic` | `/wheel_odom_path` | 출력 경로 토픽 |
| `path_frame` | 빈 문자열 | 비어 있으면 입력의 `header.frame_id` 사용 |
| `max_points` | `2000` | 보관할 기록 수. 0 이하는 무제한이므로 장시간 실습에는 양수 권장 |
| `input_qos_reliability` | `best_effort` | 입력 메시지의 신뢰성 설정 |
| `input_qos_durability` | `volatile` | 접속 후 새 입력 메시지만 수신 |
| `input_qos_depth` | `20` | 입력 대기열 크기 |
| `output_qos_reliability` | `reliable` | 경로 메시지의 신뢰성 설정 |
| `output_qos_durability` | `transient_local` | 늦게 접속한 RViz에도 마지막 전체 경로 전달 |
| `output_qos_depth` | `1` | 보관할 출력 메시지 수 |

`path_frame`은 좌표 변환 옵션이 아니다. 입력 프레임과 다르게 지정하면 잘못된
경로를 만들지 않도록 메시지를 거부한다. 입력 시각이 뒤로 돌아가거나 프레임이
바뀌면 기존 경로를 비운다.

## `ackermann_odom`: 바퀴에서 이동량 계산하기

Gazebo Classic의 기본 Ackermann 플러그인이 발행하는 오도메트리는 Gazebo의
모델 위치를 사용한다. 바퀴 측정값과 시뮬레이터 참값을 구분하기 위해 이 노드는
두 뒷바퀴의 회전량과 두 앞바퀴의 조향각으로 별도의 `/odom`을 계산한다.

터미널 1의 이전 실행을 종료한 뒤 Ackermann 로버를 실행한다. 이 실행 파일이
`ackermann_odom`과 경로 변환 노드를 함께 시작한다.

```bash
ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py
```

터미널 2에서 입력과 출력을 확인한다.

```bash
ros2 node list
ros2 topic echo /joint_states --once --qos-reliability best_effort
ros2 topic echo /odom --once --field pose.pose --qos-reliability best_effort
```

노드 목록에 `/ackermann_odom`이 있고, `/joint_states`에 아래 표의 두 뒷바퀴와
두 조향 조인트가 모두 있어야 한다. `/odom`은 `odom` 기준 위치와 자세를,
`odom → base_footprint` TF는 로봇의 이동 변환을 제공한다.

다른 로봇에 직접 연결할 때만 별도 터미널에서 노드를 실행한다.

```bash
ros2 run gazebo_tutorial_tools ackermann_odom --ros-args \
  -p use_sim_time:=true \
  -p wheel_radius:=0.16 \
  -p wheelbase:=0.56 \
  -p rear_axle_offset:=0.28
```

| 파라미터 | 기본값 | 의미 |
|---|---:|---|
| `joint_states_topic` | `/joint_states` | 바퀴·조향 조인트 위치 입력 |
| `odom_topic` | `/odom` | 바퀴 오도메트리 출력 |
| `odom_frame` | `odom` | 오도메트리 기준 프레임 |
| `base_frame` | `base_footprint` | 위치·속도를 나타내는 로봇 프레임 |
| `rear_left_joint` | `rear_left_wheel_joint` | 왼쪽 뒷바퀴 조인트 |
| `rear_right_joint` | `rear_right_wheel_joint` | 오른쪽 뒷바퀴 조인트 |
| `front_left_steering_joint` | `front_left_steering_joint` | 왼쪽 앞 조향 조인트 |
| `front_right_steering_joint` | `front_right_steering_joint` | 오른쪽 앞 조향 조인트 |
| `wheel_radius` | `0.16` | 바퀴 반지름(m) |
| `wheelbase` | `0.56` | 앞뒤 차축 간 거리(m) |
| `rear_axle_offset` | `0.28` | 뒷차축 중앙에서 로봇 프레임 원점까지 전방 거리(m) |
| `max_wheel_delta` | `2.0` | 한 측정 간격에서 허용할 최대 바퀴 회전량(rad) |
| `publish_tf` | `true` | 로봇 이동 TF 발행 여부 |

바퀴 각도가 ±π 경계를 넘어가면 최단 각도 차이로 연결해 적분한다. 시간 역행이나
허용 범위를 넘는 회전량 변화가 감지되면 적분 기준을 초기화한다. 바퀴 치수나 로봇
프레임의 위치가 다른 모델에는 해당 값을 맞춰야 한다.

회전 중에는 뒷차축 중앙과 차체 중앙이 서로 다른 궤적을 그린다. 이 노드는 뒷차축의
이동을 계산한 뒤 `rear_axle_offset`를 반영해 차체 기준 위치와 속도로 바꾼다.
따라서 회전 중 `twist.twist.linear.y`가 0이 아닐 수 있으며, 이는 차체 중앙의
횡방향 속도다. 출력 QoS는 `Reliable + Volatile`이다.

실습을 마치면 직접 시작한 노드와 터미널 1의 launch를 각각 `Ctrl+C`로 종료한다.
좌표계·QoS·주행 명령 확인은
[문제 해결](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/docs/08_debugging.md)을 참고한다.
