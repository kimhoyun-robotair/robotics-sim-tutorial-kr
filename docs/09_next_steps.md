# 설계 원칙과 다음 실습

앞 장에서 로봇과 센서를 실행했다면, 이제 위치 추정과 제어 알고리즘을 연결할 수 있다. 이 장은 확장할 때 유지해야 할 규칙과 직접 해 볼 만한 실습을 정리한다. 아래 확장 과제는 완성된 Nav2·SLAM 예제를 제공한다는 뜻은 아니다. 각 과제를 시작하기 전에 필요한 입력과 TF를 먼저 확인한다.

이 장의 명령은 [설치와 첫 실행](01_setup.md)을 마친 환경을 기준으로 한다. 새 터미널마다 다음 두 줄을 실행한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
```

## 1. 바퀴로 계산한 위치와 시뮬레이터의 실제 위치를 구분한다

바퀴 회전량으로 이동 거리와 방향을 계산한 값을 **휠 오도메트리**라고 한다. 바퀴가 미끄러지면 이 값과 실제 위치가 달라진다. Gazebo는 물리 계산 결과인 위치와 자세도 알고 있으므로 두 값을 비교할 수 있다.

| 값 | 계산 방법 | 쓰임과 한계 |
| --- | --- | --- |
| `/odom` → `/wheel_odom_path` | 바퀴 회전량을 적분. Ackermann 차량은 앞바퀴 조향각도 사용 | 실제 바퀴 엔코더와 비슷한 입력. 미끄러짐과 바퀴 치수 오차가 누적됨 |
| `/ground_truth_path` | diffbot의 직접 만든 플러그인 또는 Ackermann의 내장 플러그인에서 얻은 월드 좌표 | 시뮬레이션 결과를 평가하는 기준값. 실제 로봇에서는 같은 방식으로 얻을 수 없음 |
| 향후 `/odometry/filtered` | `robot_localization`의 EKF/UKF로 오도메트리와 IMU 등을 융합 | 잡음을 줄일 수 있지만 공분산과 시간 설정이 필요함 |

시뮬레이터의 기준 위치(ground truth)는 **비교와 평가**에 사용한다. 실제 장비를 위한 위치 추정 알고리즘에는 엔코더·IMU·라이다 등 실제로 얻을 수 있는 측정값을 입력한다. 4륜 Ackermann 센서 로봇의 기본 실행에는 `/ground_truth/odom`과 `/ground_truth_path`가 함께 있으므로 `/odom`·`/wheel_odom_path`와 비교할 수 있다.

## 2. 직접 구동 플러그인에서 `ros2_control`로 확장하기

현재 예제는 `gazebo_ros_diff_drive`와 `gazebo_ros_ackermann_drive`가 바퀴 관절을 직접 구동한다. 실제 로봇과 제어 구조를 맞추려면 `ros2_control`로 확장할 수 있다.

| 구성 요소 | 역할 |
| --- | --- |
| `controller_manager` | 제어기의 시작·정지와 갱신 주기를 관리 |
| `diff_drive_controller` | 속도 명령을 좌우 바퀴 속도로 변환 |
| `gazebo_ros2_control` | 제어기의 명령을 Gazebo 관절에 전달하고 관절 상태를 읽음 |

한 관절을 두 제어기가 동시에 구동하면 안 된다. 전환할 때는 기존 구동 플러그인을 제거하거나 Xacro 조건문으로 끄고, 관절의 명령·상태 인터페이스와 제어기 설정을 추가한다. 이 저장소의 기본 실행 인자만 바꿔서 제어 방식이 자동 전환되지는 않는다.

위 표의 `diff_drive_controller`는 차동구동 차량용이다. 센서 실습의 4륜 Ackermann 차량은 앞바퀴 조향과 뒷바퀴 구동을 다루는 제어기가 필요하다. 현재 `/cmd_vel.angular.z`는 조향각(rad)이므로, 새 제어기가 각속도(rad/s)를 받는다면 명령을 그대로 연결하지 말고 축거와 속도에 맞춰 변환해야 한다.

## 3. 같은 TF는 한 곳에서만 발행한다

TF가 빠져 있어도, 같은 TF를 여러 노드가 발행해도 RViz에 문제가 생긴다. 각 자식 프레임의 부모와 발행자를 정해 두면 설정을 바꿀 때 확인하기 쉽다.

| TF 연결 | 기본 발행자 |
| --- | --- |
| `world → odom` | 실행 파일의 고정 TF 발행 노드. 생성 위치와 오도메트리 원점을 연결 |
| `odom → base_footprint` | 차동 구동 플러그인. Ackermann은 `ackermann_odom` 노드 |
| `base_footprint → base_link` | URDF 고정 관절을 읽는 `robot_state_publisher` |
| 차체 → 바퀴·센서 프레임 | URDF와 `/joint_states`를 읽는 `robot_state_publisher` |
| `map → odom` | 기본 예제에는 없음. SLAM 또는 위치 추정 노드를 추가하면 해당 노드가 담당 |

EKF가 `odom → base_footprint`를 발행하도록 바꾸면 기존 발행을 끈다. 차동 구동 모델은 Xacro의 `<publish_odom_tf>false</publish_odom_tf>`, Ackermann은 실행 인자 `ackermann_publish_tf:=false`를 사용한다.

SLAM이나 AMCL이 `map → odom`을 발행할 때는 `publish_world_odom_tf:=false`도 적용한다. 그렇지 않으면 `odom`에 `world`와 `map`이라는 두 부모가 생긴다. `/tf` 발행자가 여러 개인 것 자체는 정상일 수 있으며, **어떤 자식 프레임을 각각 발행하는지** 확인해야 한다.

## 4. 모든 관련 노드가 같은 시간을 사용한다

Gazebo는 `/clock`으로 시뮬레이션 시간을 알린다. 일시 정지 중에는 이 시간이 진행하지 않는다. 실시간 계수(real-time factor)가 0.5라면 실제 시간 2초 동안 시뮬레이션은 약 1초 진행한다.

Gazebo를 실행한 상태에서 확인한다.

```bash
ros2 param get /odom_to_path use_sim_time
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /rviz2 use_sim_time
timeout 10s ros2 topic echo /clock --once
```

파라미터는 모두 `Boolean value is: True`여야 한다. 새 센서 처리 노드에도 `use_sim_time:=true`를 전달한다. 실시간 시계와 시뮬레이션 시간을 섞으면 TF를 요청한 시각과 메시지 시각이 맞지 않는다. 일시 정지 중에도 동작해야 하는 통신 감시 타이머는 별도로 실제 시간을 사용하도록 설계한다.

## 5. 센서 토픽은 QoS까지 맞춘다

토픽 이름과 타입이 같아도 QoS가 호환되지 않으면 데이터를 받지 못한다. 먼저 실제 발행자의 설정을 확인한다.

```bash
ros2 topic info /points --verbose
timeout 10s ros2 topic echo /points --field header --once \
  --qos-reliability best_effort
```

`--field header`는 큰 점군 배열 대신 시각과 프레임만 출력한다. RViz의 센서 디스플레이는 `Reliability Policy: Best Effort`, `Durability Policy: Volatile`로 시작하면 된다. Reliable 발행자는 Best Effort 구독자에게 전송할 수 있지만 반대 조합은 연결되지 않는다. `/robot_description`과 누적 Path처럼 마지막 값을 늦게 접속한 구독자에게도 전달해야 하는 토픽은 별도로 Transient Local을 사용한다.

## 6. 센서 데이터를 저장하고 같은 입력으로 다시 검사하기

`rosbag2`는 ROS 메시지를 파일로 저장한다. 저장한 입력을 다시 재생하면 알고리즘 수정 전후를 같은 조건에서 비교할 수 있다.

**터미널 A — 센서 로봇 실행**

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars
```

**터미널 B — 기록 시작**

```bash
mkdir -p ~/bags
cd ~/bags
bag_name="humble_sensors_$(date +%Y%m%d_%H%M%S)"
ros2 bag record -o "$bag_name" \
  /tf /tf_static /joint_states /robot_description \
  /cmd_vel /odom /wheel_odom_path /imu/data /scan /points
```

**터미널 C — 짧게 주행**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

`i`와 `u`로 짧게 움직인 뒤 `k`로 멈춘다. 센서 차량은 Ackermann 방식이므로 `u`는 전진하면서 조향하는 명령이며, `j`로 제자리 회전할 수 없다. 터미널 B에서 `Ctrl+C`를 눌러 기록을 끝낸다. 터미널 C의 키보드 노드와 터미널 A의 시뮬레이션도 종료한다.

터미널 B에서 방금 만든 기록을 확인하고 재생한다.

```bash
ros2 bag info "$bag_name"
ros2 bag play "$bag_name" --clock
```

`bag info`에 토픽과 메시지 수가 나오고, 재생이 끝나면 명령도 종료된다. 중간에 멈추려면 `Ctrl+C`를 누른다. 이 예제는 `/clock`을 기록하지 않고 **재생기가 `--clock`으로 시계를 발행**하게 한다. 재생 중에 Gazebo를 함께 실행하면 `/clock`, TF, 센서 데이터가 중복되므로 종료한 상태를 유지한다.

새 터미널에서 기존 설정으로 RViz만 연다.

```bash
rviz2 -d "$(ros2 pkg prefix gazebo_tutorial_bringup)/share/gazebo_tutorial_bringup/rviz/sensors.rviz" \
  --ros-args -p use_sim_time:=true
```

라이다 프로필로 저장했으므로 카메라 디스플레이에는 영상이 없는 것이 정상이다. 카메라 데이터를 비교할 때는 카메라 프로필을 실행하고 기록할 영상·CameraInfo·점군 토픽을 추가한다. 결과를 비교할 때는 화면뿐 아니라 위치 오차, 메시지 시각 간격, 누락 횟수를 함께 기록한다.

## 7. 성능과 물리 설정을 하나씩 바꾼다

Gazebo가 실행 중일 때 다음 명령으로 약 10초씩 관찰한다. `timeout`의 종료 코드 124는 지정한 관찰 시간이 끝났다는 뜻이다.

```bash
timeout 10s gz stats -p
timeout 10s ros2 topic hz /scan
timeout 10s ros2 topic hz /imu/data
timeout 10s ros2 topic bw /points
```

센서를 모두 켠 상태가 느리면 `minimal → lidars → cameras → all` 순서로 바꿔 부하가 커지는 구간을 찾는다. 프로필을 바꾸기 전에는 기존 실행을 종료한다.

- 카메라가 느리면 해상도와 발행 주기를 낮춘다.
- 3D 라이다가 느리면 수평·수직 샘플 수를 줄인다.
- 차체가 떨리거나 바닥을 뚫으면 충돌 형상, 질량, 관성, 접촉 설정을 먼저 확인한다.
- 물리 계산 간격인 `max_step_size`를 줄이면 안정성이 나아질 수 있지만 계산량도 늘어난다.

명령줄에서 관찰한 수신률은 컴퓨터 부하와 시뮬레이션 속도의 영향을 받는다. 설정한 센서 주기를 검증할 때는 메시지 헤더의 **시뮬레이션 시각 차이**도 비교한다.

## 8. 다중 로봇에 필요한 분리

현재 예제는 한 번에 로봇 하나를 실행하도록 구성되어 있다. 두 대를 동시에 실행하려면 아래 이름을 각각 구분하도록 Xacro와 실행 파일을 함께 수정해야 한다.

| 대상 | 분리 예 |
| --- | --- |
| Gazebo 모델 이름 | `robot1`, `robot2` |
| ROS 토픽·노드 네임스페이스 | `/robot1/cmd_vel`, `/robot2/cmd_vel` |
| TF 프레임 | `robot1/base_link`, `robot2/base_link` |
| 로봇 설명 | 각 네임스페이스의 `robot_description` |

ROS 네임스페이스를 붙여도 메시지 내부의 `frame_id`는 자동으로 바뀌지 않는다. `robot_state_publisher`의 `frame_prefix`, 구동 플러그인의 프레임 설정, 센서의 `frame_name`을 같은 규칙으로 맞춘다. 전역 `/clock`은 같은 시뮬레이션의 로봇들이 공유한다.

## 9. 확장 과제와 완료 기준

| 단계 | 실습 | 확인할 결과 |
| --- | --- | --- |
| 초급 | 센서 차량의 바퀴 형상은 두고 `ackermann_odom`의 `wheel_radius`만 5% 변경 | 기준 위치와 오도메트리 사이에 이동 거리 오차가 생기는지 비교 |
| 초급 | 바퀴의 `mu1`, `mu2`를 낮춤 | 같은 주행 명령에서 미끄러짐과 궤적 차이 관찰 |
| 초급 | 카메라의 `update_rate`를 절반으로 변경 | 시뮬레이션 시각 기준 영상 간격이 약 두 배가 되는지 확인 |
| 중급 | `robot_localization`으로 `/odom`과 `/imu/data` 융합 | 출력 프레임·공분산·TF 발행자를 확인하고 원본과 비교 |
| 중급 | `slam_toolbox`로 지도 작성 | `map → odom → base_footprint → lidar_2d_link` 연결과 지도 윤곽 확인 |
| 중급 | `gazebo_ros2_control`로 구동 교체 | 기존 구동 플러그인을 끈 상태에서 바퀴 명령·상태와 odometry 확인 |
| 고급 | 자동 주행 검사 추가 | 바퀴가 도는 것에 더해 월드 기준 로봇 위치가 실제로 변하는지 확인 |

새 Gazebo로 이전할 때는 URDF의 링크·관절과 ROS 토픽 설계를 재사용할 수 있다. Classic의 ModelPlugin/WorldPlugin, 센서 플러그인, 실행 파일과 자원 탐색 경로는 새 Gazebo에 맞게 바꿔야 한다. 토픽·타입·TF·QoS와 기대하는 측정값을 먼저 기록해 두면 이전 결과를 같은 기준으로 비교할 수 있다.
