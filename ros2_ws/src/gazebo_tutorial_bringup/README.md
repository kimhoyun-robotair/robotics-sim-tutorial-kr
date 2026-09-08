# gazebo_tutorial_bringup

Gazebo Classic 11 서버, 로봇 생성, TF, 주행 궤적, RViz를 함께 실행하는 ROS 2 Humble 패키지다.

## 1. 빌드

[설치 안내](../../../docs/01_setup.md)를 마친 뒤 **터미널 A**에서 실행한다.

```bash
source /opt/ros/humble/setup.bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
```

## 2. 로봇 하나 실행

다음 표에서 **하나만** 골라 실행한다. 기본 토픽과 TF를 공유하므로 여러 모델을 동시에 실행하면 충돌한다.

| 모델 | 명령 |
| --- | --- |
| 바퀴 두 개와 보조 바퀴 | `ros2 launch gazebo_tutorial_bringup diffbot.launch.py` |
| 4륜 스키드·차동 구동 | `ros2 launch gazebo_tutorial_bringup rover_diff.launch.py` |
| 4륜 Ackermann | `ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py` |
| 4륜 Ackermann 센서 차량 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all` |

`Successfully spawned entity` 로그와 Gazebo·RViz 창을 확인한다. 다른 모델로 바꾸려면 실행 중인 터미널에서 `Ctrl+C`를 누르고 종료를 기다린다.

실행 파일은 Xacro를 전개해 `robot_description`으로 전달하고, `robot_state_publisher`와 `spawn_entity.py`를 시작한다. `odom_to_path` 노드가 `/odom`의 위치를 누적해 `/wheel_odom_path`를 발행한다.

## 3. 별도 터미널에서 조종·확인

**터미널 B**에서 환경을 읽고 키보드 조종을 시작한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

`i`는 전진, `u`는 전진하며 왼쪽 회전, `k`는 정지다. 기본 Ackermann 차량과 센서 차량은 제자리 회전할 수 없으므로 곡선 주행 키를 쓴다. 두 차량에서 `/cmd_vel.linear.x`는 속도 [m/s], `/cmd_vel.angular.z`는 조향각 [rad]이다. 차동 구동 차량에서 `angular.z`로 지정하는 회전 속도 [rad/s]와 의미가 다르다. 종료할 때는 `k`로 정지한 뒤 `Ctrl+C`를 누른다.

센서 차량을 낮은 속도로 직접 조종하려면 키보드 조종을 종료한 뒤 다음 명령을 실행한다. 5초 동안 0.2 m/s로 왼쪽으로 움직이고 나서 정지 명령을 보낸다. 첫 번째 명령은 `timeout` 때문에 종료 코드 124로 끝나는 것이 정상이다.

```bash
timeout 5s ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.2}}"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

이 플러그인은 명령 발행이 멈춰도 마지막 속도를 유지한다. 실습을 끝낼 때는 반드시 정지 명령을 보내고 시뮬레이션을 종료한다.

**터미널 C**에서도 같은 환경 두 줄을 읽고 데이터를 확인한다.

```bash
timeout 10s ros2 topic echo /odom --field header --once
timeout 10s ros2 run tf2_ros tf2_echo odom base_footprint
```

`frame_id: odom`과 연결된 TF가 나와야 한다. 계속 출력하는 명령은 `timeout`이 10초 뒤 끝낸다.

## 자주 쓰는 실행 인자

| 인자 | 기본값 | 설명 |
| --- | --- | --- |
| `gui` | `true` | Gazebo 화면인 `gzclient` 실행 여부 |
| `rviz` | `true` | RViz 실행 여부 |
| `pause` | `false` | 물리 계산을 일시 정지한 상태로 시작 |
| `use_sim_time` | `true` | ROS 노드가 Gazebo의 `/clock`을 사용 |
| `entity_name` | 모델별 이름 | Gazebo 모델 이름 |
| `x`, `y`, `z`, `yaw` | `0, 0, 0.1, 0` | 모델 생성 위치와 방향 |
| `world` | 모델별 기본 월드 | 다른 `.world` 파일의 절대 경로 |
| `odom_topic` / `path_topic` | `/odom` / `/wheel_odom_path` | 궤적 노드의 입력·출력 |
| `path_frame` | 빈 문자열 | 비어 있으면 입력 프레임 사용. 좌표 변환 기능은 없음 |
| `max_points` | `2000` | 누적 궤적의 최대 점 수 |
| `sensor_profile` | 센서 실행은 `all` | `all`, `cameras`, `lidars`, `minimal` |
| `publish_world_odom_tf` | `true` | 생성 위치를 반영한 `world → odom` 고정 TF |
| `ackermann_publish_tf` | `true` | Ackermann 오도메트리의 TF 발행 |
| `ground_truth_odom_topic` | `/ground_truth/odom` | Ackermann의 월드 기준 위치 입력 |
| `ground_truth_path_topic` | `/ground_truth_path` | Ackermann의 기준 궤적 출력 |

예를 들어 카메라 없이 거리 센서를 실습하려면 다음 명령을 쓴다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars
```

GUI 없이 실행하려면 `gui:=false rviz:=false`를 추가한다. 카메라는 GUI를 꺼도 OpenGL 렌더링 환경이 필요하다. 전체 인자와 현재 기본값은 다음 명령으로 확인한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py --show-args
```

`empty.world`와 `sensor.world`는 지면·조명을 파일 안에 정의하므로 외부 모델 다운로드가 필요 없다. 센서 월드에는 색상과 거리가 다른 상자·원통·벽이 있다. 센서 RViz는 `world`, 기본 주행 RViz는 `odom`을 고정 프레임으로 사용한다.

기본 Ackermann 차량과 모든 센서 프로필은 같은 오도메트리 구성을 사용한다. Ackermann 내장 플러그인의 `/ground_truth/odom`은 바퀴 엔코더가 아닌 Gazebo의 실제 위치다. 별도 `ackermann_odom` 노드가 뒷바퀴 회전량과 앞바퀴 조향각으로 `/odom`을 계산하고, 뒤 차축에서 차체 중심까지 0.28 m의 차이도 반영한다. 자세한 비교는 [TF·RViz 실습](../../../docs/06_tf_rviz.md)을 참고한다.
