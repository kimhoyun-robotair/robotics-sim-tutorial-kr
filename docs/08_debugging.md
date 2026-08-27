# Gazebo Classic + ROS 2 디버깅 가이드

시뮬레이터 문제는 화면만 보고 추측하면 오래 걸린다. **프로세스 → simulation clock →
entity → topic/QoS → TF** 순서로 관측하면 대부분의 문제를 빠르게 좁힐 수 있다.

## 1. 가장 먼저 확인할 다섯 가지

한 터미널에서 launch를 실행하고, 다른 터미널은 같은 workspace를 source한다.

```bash
source /opt/ros/humble/setup.bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py verbose:=true
```

```bash
# 1) Gazebo가 simulation clock을 발행하는가?
ros2 topic echo --once /clock

# 2) spawn service와 ROS 노드가 존재하는가?
ros2 service list
ros2 node list

# 3) model이 odometry를 내는가?
ros2 topic hz /odom

# 4) 핵심 TF가 이어지는가?
ros2 run tf2_ros tf2_echo odom base_link

# 5) publisher/subscriber QoS가 호환되는가?
ros2 topic info /odom --verbose
```

첫 실패 지점부터 아래 절을 따라간다. 뒤 단계가 실패해도 앞 단계가 정상이 아니면 먼저
앞 단계를 고쳐야 한다.

## 2. `pause`와 멈춘 simulation time

`pause:=true`로 실행했거나 Gazebo GUI의 재생 버튼이 정지 상태면 `/clock`과 physics가
진행하지 않는다. spawn은 성공해도 wheel, IMU, LiDAR, camera 토픽이 멈춰 있는 것이
정상이다.

```bash
ros2 service call /unpause_physics std_srvs/srv/Empty "{}"
ros2 topic hz /clock
```

반대로 실험 시작 조건을 동일하게 만들고 싶다면 정지 상태로 spawn한 뒤 필요한 노드가
준비되었을 때 `/unpause_physics`를 호출한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py pause:=true
```

GUI의 재생 아이콘과 `/pause_physics`, `/unpause_physics` 서비스는 같은 physics 상태를
바꾼다. `/clock` 메시지가 존재하는지만 보지 말고 값이 계속 증가하는지 확인한다.

## 3. `use_sim_time` 불일치

Gazebo 데이터의 timestamp는 `/clock` 기준이다. 한 노드만 wall clock을 사용하면 TF
조회 시점이 수십 년 차이가 나서 `extrapolation into the past/future` 오류가 생길 수 있다.

```bash
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /odom_to_path use_sim_time
ros2 param get /rviz2 use_sim_time
```

모두 `Boolean value is: True`여야 한다. 이 저장소의 bringup launch는 세 노드에
`use_sim_time:=true`를 기본 전달한다. 별도로 실행한 노드는 직접 지정한다.

```bash
ros2 run my_package my_node --ros-args -p use_sim_time:=true
```

Gazebo world를 reset하면 simulation time이 뒤로 간다. 일부 필터는 과거 데이터를 계속
들고 있어 경고를 낼 수 있으므로 reset 후 문제가 지속되면 해당 노드를 재시작한다.
`odom_to_path`는 시간이 뒤로 간 것을 감지해 이전 궤적을 자동으로 지운다.

## 4. model이 spawn되지 않을 때

launch 로그에서 다음 세 단계를 분리해 본다.

1. Xacro가 URDF로 확장되는가?
2. `/robot_description`이 발행되는가?
3. `/spawn_entity` 서비스가 응답하는가?

```bash
xacro $(ros2 pkg prefix gazebo_tutorial_description)/share/\
gazebo_tutorial_description/urdf/diffbot.urdf.xacro > /tmp/diffbot.urdf
check_urdf /tmp/diffbot.urdf
ros2 topic echo --once /robot_description
ros2 service type /spawn_entity
```

대표적인 원인은 잘못된 Xacro include 경로, 닫히지 않은 XML tag, 0 또는 음수 mass,
잘못된 inertia, 존재하지 않는 mesh URI다. spawn 직후 model이 사라지거나 튀어 오르면
collision이 서로 겹치지 않는지와 초기 `z`가 바닥 아래가 아닌지 확인한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py z:=0.2 verbose:=true
```

## 5. entity와 노드 이름 충돌

Gazebo 안의 model entity 이름은 고유해야 한다. 이미 `diffbot`이 있는데 같은 이름으로
spawn하면 `Entity [diffbot] already exists` 오류가 난다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py entity_name:=diffbot_2 x:=1.0
```

기존 entity만 제거하려면 이름을 정확히 확인하고 delete service를 호출한다.

```bash
ros2 service call /delete_entity gazebo_msgs/srv/DeleteEntity "{name: diffbot}"
```

ROS node 이름도 같은 graph 안에서 겹치면 파라미터와 service가 모호해진다. 이 튜토리얼의
launch는 단일 로봇 실습용이다. 여러 로봇을 동시에 띄울 때는 다음 항목을 모두 분리해야
한다.

- Gazebo `entity_name`
- ROS namespace와 node 이름
- `/cmd_vel`, `/odom`, `/joint_states`, sensor topic
- `base_link`, `odom`, sensor frame을 포함한 TF frame 이름
- drive 플러그인의 ROS namespace와 frame parameter

launch를 `Ctrl+C`로 종료했는데 새 Gazebo가 시작되지 않으면 남은 프로세스를 먼저
확인한다.

```bash
ps -ef | grep -E '[g]zserver|[g]zclient'
```

다른 작업의 Gazebo까지 일괄 종료하지 말고, 이 실습에서 시작한 PID임을 확인한 뒤 해당
PID에 `SIGINT`를 보낸다.

```bash
kill -INT <확인한_PID>
```

## 6. topic은 보이는데 데이터가 오지 않을 때: QoS

ROS 2에서는 topic 이름과 message type이 같아도 QoS가 호환되지 않으면 연결되지 않는다.
이 저장소가 기준으로 삼는 Humble `gazebo_ros_pkgs`의 camera·IMU·ray publisher는
Reliable + Volatile을 사용한다. 제공된 RViz sensor display는 이 Reliable publisher와 호환되고
다른 Best Effort 센서로 바꿔도 연결되도록 Best Effort + Volatile로 요청한다.
추측만 하지 말고 아래 `--verbose`로 실제 endpoint를 확인한다.

| 데이터 | 권장 subscriber QoS | 이유 |
|---|---|---|
| Camera, LaserScan, PointCloud2, IMU | Best Effort + Volatile | 오래된 frame보다 최신 frame이 중요 |
| Odometry 입력 | Best Effort + Volatile | Gazebo publisher가 어느 reliability여도 연결하기 쉬움 |
| 누적 Path 출력 | Reliable + Transient Local | 늦게 시작한 RViz도 최신 전체 Path 수신 |
| `/tf_static` | Reliable + Transient Local | 고정 변환을 새 subscriber에 재전달 |

endpoint별 실제 설정을 확인한다.

```bash
ros2 topic info /scan --verbose
ros2 topic info /points --verbose
ros2 topic info /wheel_odom_path --verbose
```

RViz에서 sensor display를 선택한 뒤 Topic의 `Reliability Policy`를 `Best Effort`로 바꾼다.
`Incompatible QoS` 경고가 로그에 있으면 먼저 reliability와 durability를 비교한다. queue
depth만 다르다는 이유로 연결이 끊어지지는 않지만 처리 속도가 느릴 때 유실 양상은 달라진다.

## 7. RViz의 `No transform`과 frame 오류

메시지가 발행되는데 RViz에 보이지 않으면 `header.frame_id`부터 확인한다.

```bash
ros2 topic echo --once /scan --field header
ros2 topic echo --once /odom --field header
ros2 run tf2_ros tf2_echo odom lidar_2d_link
```

다음 항목을 점검한다.

- RViz `Fixed Frame`이 이 실습에서는 `odom`인가?
- sensor 플러그인의 `frame_name`과 URDF link 이름이 정확히 같은가?
- `base_link → sensor_link` fixed joint가 `/tf_static`에 있는가?
- drive 플러그인이 `odom → base_footprint`를 발행하는가?
- movable joint를 위한 `/joint_states`가 발행되는가?
- 같은 child transform을 둘 이상의 노드가 발행하지 않는가?

```bash
ros2 run tf2_tools view_frames
ros2 topic info /tf --verbose
ros2 topic info /tf_static --verbose
```

frame 이름을 맞추기 위해 메시지의 `header.frame_id`만 다른 이름으로 바꾸는 것은 좌표
변환이 아니다. 실제 translation/rotation이 필요하면 TF를 조회해 pose나 point cloud를
변환해야 한다.

## 8. `/cmd_vel`을 보내도 움직이지 않을 때

keyboard teleop 대신 일정한 명령으로 먼저 drive 경로를 검사하면 키 입력 문제를 분리할
수 있다.

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.3}}"
```

몇 초 뒤 `Ctrl+C`로 멈춘다. 이어서 확인한다.

```bash
ros2 topic info /cmd_vel --verbose
ros2 topic hz /odom
ros2 topic hz /joint_states
```

- `/cmd_vel` subscriber가 0이면 플러그인이 로드되지 않았거나 topic/namespace가 다르다.
- subscriber는 있는데 wheel이 안 돌면 joint 이름과 drive 플러그인 parameter를 확인한다.
- wheel은 도는데 본체가 안 움직이면 collision, friction, effort/torque limit를 확인한다.
- Ackermann rover가 꺾이지 않으면 steering joint 축, limit, wheelbase/track 값을 확인한다.
- Ackermann `/odom`이 없으면 `/joint_states`에 rear wheel과 front steering joint 네 개가
  모두 있는지, `/ackermann_odom` 노드가 실행 중인지 확인한다.
- physics가 pause 상태면 command는 도착해도 model은 움직이지 않는다.

## 9. 플러그인 로드 실패

`Failed to load plugin ... .so` 오류는 파일을 찾지 못했거나 동적 라이브러리 의존성이
빠졌다는 뜻이다. workspace를 다시 빌드하고 현재 터미널에서 install space를 source한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
colcon build --symlink-install
source install/setup.bash
printenv GAZEBO_PLUGIN_PATH
```

custom 플러그인의 실제 파일과 의존성도 확인할 수 있다.

```bash
find install -name 'lib*.so'
ldd install/gazebo_tutorial_plugins/lib/libground_truth_path_plugin.so
```

`not found`가 있으면 해당 dependency를 설치하거나 `package.xml`과 CMake export를 고친다.
ABI가 맞지 않는 ROS/Gazebo 배포판에서 만든 `.so`를 복사해 쓰지 말고 Humble + Gazebo 11
환경에서 다시 빌드한다.

## 10. GUI 없는 headless 검증

CI나 원격 서버에서는 gzclient와 RViz를 끄고 gzserver만 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  gui:=false rviz:=false verbose:=true
```

화면이 없으므로 관측 가능한 계약으로 성공 여부를 확인한다.

```bash
ros2 topic hz /clock
ros2 topic hz /odom
ros2 topic echo --once /wheel_odom_path
ros2 run tf2_ros tf2_echo odom base_link
```

고정된 속도 명령을 잠깐 발행한 뒤 Odometry pose가 변했는지 비교하면 단순히 프로세스가
살아 있는 것보다 강한 검증이 된다. 종료 코드와 launch 로그도 CI artifact로 남긴다.

Camera/RGBD/fisheye는 `gui:=false`여도 gzserver 안에서 렌더링 센서를 사용한다. 디스플레이가
전혀 없는 서버에서 OGRE context 생성에 실패하면 Xvfb 같은 가상 X server가 필요할 수
있다.

```bash
sudo apt install -y xvfb
xvfb-run -a ros2 launch gazebo_tutorial_bringup sensors.launch.py \
  gui:=false rviz:=false sensor_profile:=cameras
```

LiDAR와 IMU만 검증할 때는 렌더링 부담이 없는 profile을 고른다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py \
  gui:=false rviz:=false sensor_profile:=lidars
```

## 11. 시뮬레이션이 느릴 때

Gazebo의 목표는 wall time과 똑같이 빨리 보이는 것이 아니라 설정한 physics와 센서를
결정론적으로 계산하는 것이다. 부하가 크면 real-time factor(RTF)가 1 아래로 내려간다.

```bash
gz stats -p
ros2 topic hz /camera/image_raw
ros2 topic hz /points
```

성능 영향이 큰 항목을 한 번에 하나씩 줄인다.

| 항목 | 비용을 줄이는 방법 | 주의점 |
|---|---|---|
| RGBD/stereo/fisheye | 해상도와 `update_rate` 감소 | calibration과 최소 Nyquist 조건 유지 |
| 3D LiDAR | horizontal/vertical sample 수 감소 | 시야각과 angular resolution 기록 |
| RViz PointCloud2 | decay time, queue size, point size 감소 | sensor 원본 성능과 RViz 성능을 구분 |
| GUI rendering | `gui:=false rviz:=false` | camera sensor rendering은 여전히 필요할 수 있음 |
| physics | `real_time_update_rate`, solver iteration 조정 | 안정성과 contact 정확도를 다시 검증 |
| 센서 묶음 | `sensor_profile:=minimal`부터 추가 | 최종 실습은 필요한 센서를 다시 활성화 |

`max_step_size`를 무작정 키우면 빨라질 수 있지만 빠른 wheel/contact가 불안정해지고
odometry가 달라질 수 있다. 성능 변경 전후에 RTF뿐 아니라 `/odom`, TF 주기, 센서 실제
발행률과 궤적도 함께 비교한다.

`odom_to_path`는 기본 2,000개 pose만 유지한다. RViz Path가 길어져 느리면 값을 더 줄인다.

```bash
ros2 launch gazebo_tutorial_bringup rover_diff.launch.py max_points:=500
```

## 12. 재현 가능한 문제 보고

문제를 공유할 때 다음 정보를 함께 남기면 원인을 재현하기 쉽다.

- Ubuntu, ROS 2 Humble, Gazebo 11의 정확한 버전
- 실행한 launch 명령과 모든 변경 인자
- 사용한 commit SHA와 깨끗한 build 여부
- 오류가 처음 나타난 전체 로그
- `ros2 node list`, `ros2 topic list`, 문제 topic의 `--verbose` 결과
- `view_frames` 결과와 RViz Fixed Frame
- GUI/headless 여부, sensor profile, RTF
- 최소 재현 model/world

로그를 줄이려고 오류 한 줄만 잘라내면 그 앞의 plugin 로드 실패나 Xacro 경고를 놓치기
쉽다. 최초 오류부터 보고, 증상과 원인을 구분해 기록한다.
