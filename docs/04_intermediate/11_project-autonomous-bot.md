# 자율주행 tutorial_bot 프로젝트

> **난이도:** 중급 프로젝트  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Nav2 연동

## 프로젝트 목표

하나의 Xacro 원본에서 시작한 `tutorial_bot`을 Gazebo Harmonic, `gz_ros2_control`, TF, LiDAR, wheel odometry, RViz, Nav2까지 연결하고 pose goal을 반복해서 달성한다. 완성 뒤에는 같은 관찰 절차로 4륜 skid-steer와 Ackermann rover의 주행 차이도 비교한다.

```text
Xacro ── URDF tree ── robot_state_publisher ── sensor TF
  └──── Gazebo SDF 변환 ── physics·sensor·joint
                                 │
                      gz_ros2_control / ros_gz
                                 │
                  /odom · /scan · /wheel_odom_path
                                 │
                       AMCL · planner · controller
                                 │
                          stamped velocity
```

## 사용 파일

- 전체 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`
- 로봇 Xacro: `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`
- controller: `examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`
- bridge: `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`
- Nav2 설정: `examples/ros2_ws/src/tutorial_bot_bringup/config/nav2_params.yaml`
- 목표 pose: `examples/ros2_ws/src/tutorial_bot_bringup/config/project_goal.yaml`
- RViz 설정: `examples/ros2_ws/src/tutorial_bot_bringup/rviz/tutorial_bot.rviz`
- map: `examples/ros2_ws/src/tutorial_bot_gazebo/maps/training.yaml`
- world: `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`
- wheel path node: `examples/ros2_ws/src/tutorial_bot_bringup/scripts/odom_to_path`

## 1. build와 정적 검사

저장소 루트에서 의존성을 설치하고 package를 빌드한다.

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

Xacro, URDF, 변환 SDF, world를 runtime 전에 검사한다.

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

## 2. 전체 stack 실행

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=true
```

launch는 다음 순서를 보장한다.

1. Gazebo가 `training.sdf`를 실행한다.
2. `robot_state_publisher`가 Xacro description과 TF를 제공한다.
3. `ros_gz_sim create`가 entity를 spawn한다.
4. controller manager 준비 뒤 joint state와 DiffDrive controller를 활성화한다.
5. bridge가 clock·sensor를 ROS로 전달한다.
6. `/scan`, `/odom`, TF 준비 뒤 localization과 Nav2를 활성화한다.
7. `odom_to_path`가 `/wheel_odom_path`를 누적하고 RViz가 관찰값을 표시한다.

## 3. runtime preflight

다른 terminal에서 다음 값을 확인한다.

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

- Gazebo model 목록에 `tutorial_bot`이 정확히 한 번 있다.
- `/clock`, `/scan`, `/odom` message가 계속 들어온다.
- `joint_state_broadcaster`, `diff_drive_controller`가 `active`이다.
- `map → odom → base_link → lidar_link`가 연결된다.
- `/navigate_to_pose` action server가 존재한다.
- `/wheel_odom_path` publisher가 하나 존재한다.

## 4. 수동 주행으로 odometry 먼저 확인하기

Nav2 goal을 보내기 전에 controller와 wheel odometry를 keyboard teleop으로 분리 검증한다. Nav2가 command를 발행 중이지 않은 상태에서 수행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p frame_id:=base_link \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

RViz에서 Fixed Frame을 `map`으로 유지하고 다음 display를 비교한다.

- Odometry `/odom`: 현재 wheel odometry pose와 누적 arrow를 본다.
- Path `/wheel_odom_path`: 실제 주행 궤적을 본다.
- LaserScan `/scan`: 로봇 pose와 map wall이 일치하는지 본다.
- TF: `map`, `odom`, `base_link`, sensor frame을 본다.

manual teleop과 Nav2가 동시에 velocity를 보내지 않게 한다. 테스트를 끝낸 뒤 teleop terminal을 종료한다.

## 5. pose goal 전송

CLI에서 project goal을 보낸다.

```bash
ros2 action send_goal --feedback \
  /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
```

RViz에서 `/plan`과 `/wheel_odom_path`를 서로 다른 색으로 표시한다. `/plan`은 planner가 만든 목표 경로이고 wheel path는 controller를 따라 실제 odometry가 누적한 결과이다.

## 6. 최종 pose와 action 결과 확인

action status가 success여도 pose 오차를 계산한다.

```bash
ros2 topic echo /amcl_pose --once --field pose.pose
ros2 topic echo /odom --once --field pose.pose
ros2 topic echo /wheel_odom_path --once --field poses
```

`/amcl_pose`는 map 기준 localization 결과이고 `/odom`은 odom 기준 wheel estimate이다. 두 position 숫자를 직접 빼려면 frame이 다르므로 먼저 TF로 같은 frame에 변환해야 한다.

<figure class="course-figure" id="intermediate-project-runtime">
  <img src="../../assets/intermediate/project-runtime.svg" alt="시뮬레이션 Nav2 action checker로 이어지는 프로젝트 runtime 증거 흐름" loading="lazy">
  <figcaption>그림 1. 프로젝트 완료는 성공 문구가 아니라 action, TF, sensor, controller, pose 관찰값의 결합이다.</figcaption>
</figure>

## 계산 예제: 세 번의 재현성

<div class="course-worked" data-worked-example="project-runtime">
세 실행의 위치 오차가 0.05, 0.08, 0.11 m라면 최악 오차 \(\max e_p=0.11\,\mathrm{m}\)이고 모두 0.25 m 기준 안이다. 그러나 action status가 세 번 모두 success여도 TF나 `/scan`이 끊겼다면 프로젝트는 합격하지 않는다. 검증 matrix는 각 scenario의 parsed observable을 요구하므로 “PASS” banner만 있는 출력은 증거가 아니다.
</div>

## 7. 자동 반복 검증

재현 가능한 완료 검증은 다음 한 명령으로 수행한다.

```bash
./scripts/check_intermediate_nav2.sh --fresh-build --launch \
  --goal-name project_goal.yaml --repeat 3 \
  --position-tolerance 0.25 --yaw-tolerance 0.20
```

완료 조건은 다음과 같다.

- 세 번의 `NavigateToPose`가 모두 성공 status로 끝난다.
- 매 실행의 위치 오차가 0.25 m 이하이다.
- 매 실행의 yaw 오차가 0.20 rad 이하이다.
- 실행 내내 TF, `/scan`, `/odom`, controller가 살아 있다.
- 실패 goal은 의도한 abort로 끝나며 stack은 계속 동작한다.

## 8. 4륜 rover 비교 실습

2륜 프로젝트를 완료한 뒤 같은 `/cmd_vel`, `/odom`, `/wheel_odom_path`, RViz 계약으로 4륜 주행 방식을 비교한다.

### skid-steer DiffDrive

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

### AckermannSteering

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

각 실행에서 같은 teleop을 사용한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

다음 차이를 기록한다.

| 관찰 | 4륜 skid-steer | Ackermann |
|---|---|---|
| `linear.x=0`, `angular.z≠0` | 제자리 회전이 가능하다 | 일반적으로 이동하지 않는다 |
| 회전 중 타이어 | 횡방향 slip이 생긴다 | 앞바퀴가 서로 다른 각도로 조향한다 |
| 최소 회전반경 | 이상적으로 0까지 가능하다 | wheelbase와 steering limit로 제한된다 |
| odometry 오차 원인 | 횡 slip과 마찰 | 조향 geometry와 타이어 slip |

RViz의 `/wheel_odom_path`에서 동일한 key 입력으로 만들어지는 궤적을 비교한다. 이 비교는 Nav2 설정을 그대로 재사용한다는 뜻이 아니다. Ackermann Nav2에는 nonholonomic constraint와 최소 회전반경을 지원하는 controller·planner 설정이 필요하다.

## 완료 체크리스트

- [ ] Xacro, URDF, SDF, world 정적 검사가 통과한다.
- [ ] 한 launch 명령으로 Gazebo, spawn, bridge, controller, RViz, Nav2가 시작된다.
- [ ] `/clock`, `/scan`, `/odom`, `/wheel_odom_path`가 실제 message를 발행한다.
- [ ] `map → odom → base_link`와 sensor link가 연결된다.
- [ ] keyboard teleop 주행이 RViz wheel odometry trajectory에 나타난다.
- [ ] Nav2 goal을 세 번 반복해 위치·yaw 허용오차를 만족한다.
- [ ] 4륜 DiffDrive와 Ackermann의 회전 방식 차이를 설명할 수 있다.

## 문제 해결

- 실패를 단순 재시작으로 덮지 않고 가장 먼저 실패한 process와 action status를 확인한다.
- TF가 끊기면 누락된 edge의 소유자부터 확인한다.
- `/scan`은 있으나 costmap에 장애물이 없으면 frame ID, QoS, observation source를 확인한다.
- `/wheel_odom_path`가 비면 `/odom` 수신과 path node parameter를 확인한다.
- Nav2와 teleop command가 충돌하면 동시에 실행 중인 publisher를 `ros2 topic info -v`로 확인한다.
- `unreachable_goal.yaml`은 실패하는 것이 정상이며 abort 뒤 sensor와 node가 살아 있어야 한다.

## 정리

이 프로젝트는 Gazebo Classic이 아니라 Harmonic에서 실제 ROS 2 Jazzy 데이터 흐름을 끝까지 검증한다. 모델 원본, 실행 순서, message bridge, TF 소유권, controller geometry, sensor 관찰, navigation 결과를 각각 코드와 runtime 증거로 연결하면 다른 로봇에도 같은 검증 방법을 적용할 수 있다.

[다음 과정: 고급 ECS·Transport](../05_advanced/index.md)
