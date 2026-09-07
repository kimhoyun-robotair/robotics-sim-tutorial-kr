# 자율주행 tutorial_bot 프로젝트

> **난이도:** 중급 프로젝트  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Nav2 연동

## 프로젝트 목표

하나의 Xacro 원본에서 시작한 `tutorial_bot`을 Gazebo Harmonic, `gz_ros2_control`, TF, LiDAR, 바퀴 오도메트리, RViz, Nav2까지 연결하고 지정한 위치와 방향에 반복해서 도착한다. 완성 뒤에는 같은 관찰 절차로 4륜 스키드 조향과 Ackermann 로버의 주행 차이도 비교한다.

| 단계 | 확인할 결과 |
|---|---|
| 모델과 실행 | Gazebo에 로봇이 한 대 생긴다 |
| 제어와 센서 | 바퀴가 움직이고 `/scan`, `/odom`이 갱신된다 |
| 시각화 | RViz에서 로봇·센서·주행 궤적이 같은 위치에 보인다 |
| 자율주행 | 지정 목표에 도착하고 위치·방향 오차가 허용 범위 안에 든다 |

## 사용 파일

- 전체 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`
- 로봇 Xacro: `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`
- 컨트롤러: `examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`
- 브리지: `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`
- Nav2 설정: `examples/ros2_ws/src/tutorial_bot_bringup/config/nav2_params.yaml`
- 목표 위치와 자세: `examples/ros2_ws/src/tutorial_bot_bringup/config/project_goal.yaml`
- RViz 설정: `examples/ros2_ws/src/tutorial_bot_bringup/rviz/tutorial_bot.rviz`
- 지도: `examples/ros2_ws/src/tutorial_bot_gazebo/maps/training.yaml`
- 월드: `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`
- 바퀴 이동 경로 노드: `examples/ros2_ws/src/tutorial_bot_bringup/scripts/odom_to_path`

## 1. 빌드와 정적 검사

저장소 루트에서 의존성을 설치하고 패키지를 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build \
  --packages-select tutorial_bot_description tutorial_bot_gazebo \
                    tutorial_bot_control tutorial_bot_bringup \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
cd ../..
```

Xacro, URDF, 변환 SDF, 월드를 시뮬레이션을 시작하기 전에 검사한다.

```bash
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"
control="$(ros2 pkg prefix --share tutorial_bot_control)/config/controllers.yaml"
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/training.sdf"

xacro "$robot" control_backend:=gz_ros2_control \
  controller_parameters_file:="$control" > /tmp/tutorial_bot-project.urdf
check_urdf /tmp/tutorial_bot-project.urdf
gz sdf -p /tmp/tutorial_bot-project.urdf > /tmp/tutorial_bot-project.sdf
gz sdf -k /tmp/tutorial_bot-project.sdf
gz sdf -k "$world"
```

## 2. 전체 시스템 실행

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=true
```

launch는 다음과 같이 구성된다. Gazebo·설명 발행·브리지는 먼저 시작하고, 로봇 생성과 컨트롤러 준비가 확인되면 다음 단계를 진행한다.

1. Gazebo가 `training.sdf`를 실행한다.
2. `robot_state_publisher`가 Xacro 로봇 설명과 TF를 제공한다.
3. `ros_gz_sim create`가 엔티티를 생성한다.
4. 컨트롤러 관리자 준비 뒤 조인트 상태와 DiffDrive 컨트롤러를 활성화한다.
5. 미리 실행된 브리지가 시계·센서 데이터를 ROS로 전달한다.
6. `/scan`, `/odom`, TF 준비 뒤 위치 추정과 Nav2를 활성화한다.
7. `odom_to_path`가 `/wheel_odom_path`를 누적하고 RViz가 관찰값을 표시한다.

## 3. 실제 데이터 확인

새 터미널마다 저장소 루트에서 환경을 먼저 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

다음 명령은 한 줄씩 실행한다. `ros2 topic hz`와 `tf2_echo`는 몇 개 값을 확인한 뒤 `Ctrl+C`로 멈춘다.

```bash
gz model --list
ros2 topic hz /clock
ros2 topic hz /scan
ros2 topic hz /odom
ros2 topic info /wheel_odom_path -v
ros2 control list_controllers
ros2 run tf2_ros tf2_echo map base_link
ros2 action list | grep navigate_to_pose
```

합격 기준은 다음과 같다.

- Gazebo 모델 목록에 `tutorial_bot`이 정확히 한 번 있다.
- `/clock`, `/scan`, `/odom` 메시지가 계속 들어온다.
- `joint_state_broadcaster`, `diff_drive_controller`가 `active`이다.
- `map → odom → base_link → lidar_link`가 연결된다.
- `/navigate_to_pose` 액션 서버가 존재한다.
- `/wheel_odom_path` 발행 노드가 하나 존재한다.

## 4. 수동 주행으로 오도메트리 먼저 확인하기

수동 주행은 [TF·RViz 실습](06-tf-rviz.md)의 `nav2:=false` 상태에서 먼저 확인하는 것이 좋다. 이미 위의 전체 launch를 실행했다면 종료한 뒤 다음처럼 Nav2를 끄고 다시 실행한다. 이 단계의 RViz Fixed Frame은 `odom`이다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=false
```

다른 터미널에서 키보드 조종을 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p use_sim_time:=true \
  -p frame_id:=base_link \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

RViz에서 Fixed Frame을 `odom`으로 설정하고 다음 표시 항목을 비교한다.

- Odometry `/odom`: 현재 바퀴 오도메트리 위치와 자세와 누적 화살표를 본다.
- Path `/wheel_odom_path`: 실제 주행 궤적을 본다.
- LaserScan `/scan`: 로봇 정면의 벽이 Gazebo 장면과 같은 방향에 있는지 본다.
- TF: `odom`, `base_link`, 센서 좌표계를 본다.

수동 조종과 Nav2가 동시에 속도 명령을 보내지 않게 한다. 테스트가 끝나면 `k`로 정지하고 키보드 조종과 launch를 종료한다. 2절의 `nav2:=true` 명령으로 다시 시작한 뒤 준비 상태를 확인하고 다음 목표를 보낸다. Nav2 실행 시 Fixed Frame은 `map`으로 바꾼다.

## 5. 위치와 자세 목표 전송

CLI에서 프로젝트 목표를 보낸다.

```bash
ros2 action send_goal --feedback \
  /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
```

RViz에서 `/plan`과 `/wheel_odom_path`를 서로 다른 색으로 표시한다. `/plan`은 경로 계획기가 만든 목표 경로이고 바퀴 이동 경로는 컨트롤러를 따라 실제 오도메트리가 누적한 결과이다.

## 6. 도착 위치와 액션 결과 확인

액션 상태가 성공이어도 위치와 자세 오차를 계산한다.

```bash
ros2 topic echo /amcl_pose --once --field pose.pose
ros2 topic echo /odom --once --field pose.pose
ros2 topic echo /wheel_odom_path --once --field poses
```

`/amcl_pose`는 `map` 기준 위치 추정이고 `/odom`은 `odom` 기준 바퀴 추정이다. 서로 다른 좌표계의 위치를 바로 빼지 않는다. 목표 오차는 `map → base_link` TF를 읽어 같은 `map` 기준에서 계산한다. 정지 후 `/amcl_pose --once`가 기다리기만 한다면 새 추정값이 발행되지 않는 상황일 수 있으므로 `tf2_echo map base_link`로 현재 TF를 확인한다.

<figure class="course-figure" id="intermediate-project-runtime">
  <img src="../../assets/intermediate/project-runtime.svg" alt="시뮬레이션 Nav2 action checker로 이어지는 프로젝트 runtime 증거 흐름" loading="lazy">
  <figcaption>그림 1. 프로젝트 완료는 성공 문구가 아니라 액션, TF, 센서, 컨트롤러, 위치와 자세 관찰값의 결합이다.</figcaption>
</figure>

## 계산 예제: 세 번의 재현성

<div class="course-worked" data-worked-example="project-runtime">
세 실행의 위치 오차가 0.05, 0.08, 0.11 m라면 최악 오차 \(\max e_p=0.11\,\mathrm{m}\)이고 모두 0.25 m 기준 안이다. 그러나 액션 상태가 세 번 모두 성공이어도 TF나 `/scan`이 끊겼다면 프로젝트는 합격하지 않는다. 성공 여부와 함께 최종 위치, 센서 수신, TF 연결을 실행별 로그에 남긴다.
</div>

## 7. 자동 반복 검증

재현 가능한 완료 검증은 다음 한 명령으로 수행한다.

```bash
./scripts/check_intermediate_nav2.sh --fresh-build --launch \
  --evidence /tmp/tutorial-intermediate-nav2 \
  --goal-name project_goal.yaml --repeat 3 \
  --position-tolerance 0.25 --yaw-tolerance 0.20
```

완료 조건은 다음과 같다.

- 세 번의 `NavigateToPose`가 모두 성공 상태로 끝난다.
- 매 실행의 위치 오차가 0.25 m 이하이다.
- 매 실행의 요 각도 오차가 0.20 rad 이하이다.
- 실행 내내 TF, `/scan`, `/odom`, 컨트롤러가 살아 있다.
- 실패 목표는 의도한 실패 종료로 끝나며 시스템은 계속 동작한다.

## 8. 4륜 로버 비교 실습

2륜 launch와 키보드 조종을 종료한 뒤 4륜 주행 방식을 비교한다. 4륜 예제는 `/cmd_vel`의 `Twist`를 사용하므로 2륜의 `/diff_drive_controller/cmd_vel`·`TwistStamped`와 구분한다. `/odom`과 `/wheel_odom_path`를 관찰하는 절차는 같다.

### 스키드 조향 DiffDrive

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

### AckermannSteering

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

위 두 모드는 한 번에 하나만 실행한다. 모드를 바꿀 때는 기존 launch와 조종 노드를 종료한다. 각 실행에서 다음 키보드 조종 명령을 사용한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

다음 차이를 기록한다.

| 관찰 | 4륜 스키드 조향 | Ackermann |
|---|---|---|
| `linear.x=0`, `angular.z≠0` | 제자리 회전이 가능하다 | 일반적으로 이동하지 않는다 |
| 회전 중 타이어 | 횡방향 미끄럼이 생긴다 | 앞바퀴가 서로 다른 각도로 조향한다 |
| 최소 회전반경 | 이상적으로 0까지 가능하다 | 축간 거리와 조향각 제한로 제한된다 |
| 오도메트리 오차 원인 | 횡방향 미끄럼과 마찰 | 조향 형상과 타이어 미끄럼 |

RViz의 `/wheel_odom_path`에서 동일한 키 입력으로 만들어지는 궤적을 비교한다. 이 비교는 Nav2 설정을 그대로 재사용한다는 뜻이 아니다. Ackermann Nav2에는 옆으로 바로 이동할 수 없는 주행 제약과 최소 회전반경을 지원하는 컨트롤러·경로 계획기 설정이 필요하다.

## 완료 체크리스트

- [ ] Xacro, URDF, SDF, 월드 정적 검사가 통과한다.
- [ ] 한 launch 명령으로 Gazebo, 로봇 생성, 브리지, 컨트롤러, RViz, Nav2가 시작된다.
- [ ] `/clock`, `/scan`, `/odom`, `/wheel_odom_path`가 실제 메시지를 발행한다.
- [ ] `map → odom → base_link`와 센서 링크가 연결된다.
- [ ] 키보드 조종 주행이 RViz 바퀴 오도메트리 궤적에 나타난다.
- [ ] Nav2 목표를 세 번 반복해 위치·요 각도 허용오차를 만족한다.
- [ ] 4륜 DiffDrive와 Ackermann의 회전 방식 차이를 설명할 수 있다.

## 문제 해결

- 실패를 단순 재시작으로 덮지 않고 가장 먼저 실패한 프로세스와 액션 상태를 확인한다.
- TF가 끊기면 누락된 연결의 소유자부터 확인한다.
- `/scan`은 있으나 비용 지도에 장애물이 없으면 프레임 ID, QoS, 비용 지도의 관측 토픽 설정을 확인한다.
- `/wheel_odom_path`가 비면 `/odom` 수신과 경로 노드 파라미터를 확인한다.
- Nav2와 키보드 조종 명령이 충돌하면 동시에 실행 중인 발행 노드를 `ros2 topic info -v`로 확인한다.
- `unreachable_goal.yaml`은 실패하는 것이 정상이며 실패 종료 뒤 센서와 노드가 살아 있어야 한다.

## 정리

이 프로젝트는 Gazebo Classic이 아니라 Harmonic에서 실제 ROS 2 Jazzy 데이터 흐름을 끝까지 검증한다. 모델 원본, 실행 순서, 메시지 브리지, TF 소유권, 컨트롤러 형상, 센서 관찰, 자율주행 결과를 각각 코드와 실제 실행 결과로 연결하면 다른 로봇에도 같은 검증 방법을 적용할 수 있다.

[다음 과정: 고급 ECS·Transport](../05_advanced/index.md)
