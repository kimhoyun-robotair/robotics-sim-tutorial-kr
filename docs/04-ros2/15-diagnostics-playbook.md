# ROS 2 연동 진단 플레이북

이 장은 “topic이 안 보인다”처럼 큰 증상을 재현 가능한 작은 검사로 줄이는 절차이다. Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0을 기준으로 한다. 해결책을 무작위로 바꾸지 말고 **프로세스 → discovery → graph → QoS → time/TF → payload → 성능** 순서로 확인한다.

## 1. 먼저 증거 묶음을 만든다

문제를 고치기 전에 새 터미널에서 다음 결과를 보관한다. 비밀 값이나 사내 URI는 공유 전에 지운다.

```bash
mkdir -p /tmp/isaac_ros_diag

uname -a > /tmp/isaac_ros_diag/uname.txt
lsb_release -a > /tmp/isaac_ros_diag/os.txt 2>&1
nvidia-smi > /tmp/isaac_ros_diag/nvidia-smi.txt
env | sort | grep -E '^(ROS|RMW|FASTRTPS|CYCLONEDDS|LD_LIBRARY_PATH|PYTHONPATH)=' \
  > /tmp/isaac_ros_diag/ros-env.txt || true

source /opt/ros/jazzy/setup.bash
ros2 doctor --report > /tmp/isaac_ros_diag/ros2-doctor.txt 2>&1
ros2 node list > /tmp/isaac_ros_diag/nodes.txt
ros2 topic list -t > /tmp/isaac_ros_diag/topics.txt
ros2 service list -t > /tmp/isaac_ros_diag/services.txt
```

Isaac Sim Console 로그도 저장한다. GUI에서는 `Window > Console`을 열고 오류 시점 전후를 복사한다. 실행 터미널 로그를 파일로 남기려면 다음처럼 시작한다.

```bash
cd ~/isaacsim
./isaac-sim.sh 2>&1 | tee /tmp/isaac_ros_diag/isaac-sim.log
```

보고서에는 아래 재현 조건을 함께 적는다.

- Isaac Sim 정확한 버전과 설치 형태
- GPU·driver, Ubuntu, ROS distro
- 시작 명령과 source한 파일의 순서
- stage USD의 절대 경로와 commit/hash
- `ROS_DOMAIN_ID`, `RMW_IMPLEMENTATION`, DDS 설정 파일
- 재현 단계, 기대 결과, 실제 결과, 발생 빈도

## 2. 60초 기본 분류

```bash
source /opt/ros/jazzy/setup.bash

echo "ROS_DISTRO=$ROS_DISTRO"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-default}"
python3 --version

ros2 node list
ros2 topic list -t
ros2 topic info /clock --verbose
```

결과를 다음처럼 해석한다.

| 관찰 | 다음 검사 |
|---|---|
| Isaac 관련 node/topic이 하나도 없다 | bridge extension, 환경, Domain ID, DDS discovery를 확인한다 |
| topic 이름은 있으나 publisher가 0이다 | Action Graph 실행선·타임라인·sensor prim을 확인한다 |
| publisher는 있으나 `echo`가 없다 | 타입과 QoS를 확인한다 |
| 메시지는 오나 Nav2/MoveIt이 멈춘다 | `/clock`, TF, frame 이름, lifecycle을 확인한다 |
| 처음에는 되다가 느려진다 | 주기·대역폭·CPU/GPU·메모리를 측정한다 |

## 3. bridge와 Python 환경

### 3.1 Extension이 실제로 켜졌는가

Extension Manager에서 `isaacsim.ros2.bridge`가 Enabled인지 확인한다. Standalone에서는 `SimulationApp`을 만든 뒤 extension을 활성화해야 한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

from isaacsim.core.utils.extensions import enable_extension
enable_extension("isaacsim.ros2.bridge")
```

`SimulationApp` import 전에 Omniverse 모듈을 먼저 import하는 코드는 초기화 순서를 깨뜨릴 수 있다.

### 3.2 Python 3.11과 3.12를 섞지 않았는가

외부 Jazzy 터미널은 Python 3.12가 정상이다. 그러나 Isaac Sim 내부는 Python 3.11이다.

```bash
# 외부 ROS 터미널
source /opt/ros/jazzy/setup.bash
python3 -c 'import sys; print(sys.version)'

# Isaac Sim Python 자체 검사
cd ~/isaacsim
./python.sh -c 'import sys; print(sys.version)'
```

Isaac Sim을 시작하는 shell에서 `/opt/ros/jazzy`의 Python 3.12 module 경로가 `PYTHONPATH`에 들어가면 `rclpy` import 오류나 symbol 오류가 날 수 있다. 기본 인터페이스만 사용한다면 ROS를 source하지 않은 깨끗한 shell에서 내장 Jazzy library로 시작한다.

```bash
env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  DISPLAY="$DISPLAY" \
  XAUTHORITY="${XAUTHORITY:-}" \
  ROS_DOMAIN_ID=27 \
  bash --noprofile --norc
```

위 명령은 진단용 새 shell을 여는 예이다. 필요한 GPU·display 환경은 시스템에 맞게 보존한다. 커스텀 메시지가 필요하면 공식 워크스페이스에서 Python 3.11로 빌드한 `local_setup.bash`만 Isaac Sim 쪽에 source한다.

### 3.3 extension 충돌과 캐시

공식 문제 해결의 publish-rate 복구 절차는 사용자 설정을 초기화해 실행하는 것이다.

```bash
cd ~/isaacsim
./isaac-sim.sh --reset-user
```

이는 사용자 설정을 초기화하므로 현재 설정을 기록한 뒤 수행한다. 문제가 사라지면 stage가 아니라 persistent setting이나 extension 조합을 의심한다.

## 4. DDS discovery와 Domain ID

Isaac Sim의 `ROS2 Context`가 `Use Domain ID Env Var`를 사용하면 Isaac Sim을 시작한 shell의 `ROS_DOMAIN_ID`를 읽는다. 실행 후 다른 터미널에서 값을 바꿔도 이미 뜬 프로세스에는 적용되지 않는다.

```bash
# Isaac Sim과 모든 ROS 터미널에서 동일하게 실행한다.
export ROS_DOMAIN_ID=27
echo "$ROS_DOMAIN_ID"
```

daemon이 이전 환경을 잡고 있으면 다시 시작한다.

```bash
ros2 daemon stop
ros2 daemon start
ros2 node list
```

같은 host의 두 터미널 사이 discovery부터 시험한다.

```bash
# 터미널 A
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=27
ros2 run demo_nodes_cpp talker

# 터미널 B
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=27
ros2 run demo_nodes_py listener
```

이 시험도 실패하면 Isaac Sim보다 ROS/DDS 환경 문제이다. 서로 다른 host라면 다음을 점검한다.

- 같은 IP subnet과 Domain ID를 사용한다.
- 방화벽과 container network가 DDS discovery·data traffic을 허용한다.
- VPN, Wi-Fi multicast 차단, 여러 NIC가 discovery 경로를 바꾸지 않았는지 확인한다.
- Fast DDS profile을 쓴다면 `FASTRTPS_DEFAULT_PROFILES_FILE`이 양쪽 프로세스에서 같은 파일을 가리키는지 확인한다.
- container의 `localhost`는 host의 `localhost`가 아니다. network mode와 discovery server를 명시한다.

RMW를 고정해 비교할 수 있다.

```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 doctor --report | grep -i rmw -A2
```

RMW를 바꿀 때는 관련 프로세스와 daemon을 모두 종료하고 동일 환경에서 다시 시작한다. 한 프로세스만 바꾼 뒤 결과를 비교하면 원인을 분리하기 어렵다.

## 5. ROS graph와 Action Graph

topic이 안 보이면 이름을 추측하지 말고 타입까지 나열한다.

```bash
ros2 node list
ros2 topic list -t | sort
ros2 service list -t | sort
ros2 action list -t | sort
rqt_graph
```

Action Graph에서는 다음을 위에서 아래로 추적한다.

1. `On Playback Tick` 또는 physics step 실행 신호가 흐르는가
2. `ROS2 Context`가 publisher/subscriber에 연결되었는가
3. target prim·render product 경로가 실제 stage와 같은가
4. topic과 frame 이름에 namespace가 중복되지 않았는가
5. 타임라인이 Play 상태인가
6. 그래프 수정 후 stage를 저장했는가

공식 5.1 문서는 ROS Action Graph 값을 설정한 뒤 **Play 전에 stage를 저장**하라고 권고한다. 복잡한 계층에서 Auto Namespace가 모든 노드에 올바르게 적용되지 않을 수 있으므로 실제 결과를 CLI로 검증한다.

```bash
ros2 topic list | grep robot_01
ros2 node info /expected_node_name
```

USD에서 prim 이름을 바꾸었지만 ROS frame 이름을 유지해야 한다면 `isaac:nameOverride`를 확인한다. topic namespace와 TF frame prefix는 다른 개념이므로 각각 명시한다.

## 6. 타입과 QoS

### 6.1 endpoint를 비교한다

```bash
ros2 topic info /camera/front/image_raw --verbose
ros2 topic type /camera/front/image_raw
ros2 interface show sensor_msgs/msg/Image
```

`--verbose` 결과에서 publisher와 subscriber의 Reliability, Durability, History를 비교한다. 센서 publisher가 Best Effort인데 subscriber가 Reliable만 요구하면 연결되지 않을 수 있다.

```bash
ros2 topic echo /camera/front/image_raw --once \
  --qos-reliability best_effort \
  --qos-durability volatile
```

RViz의 Image·PointCloud display에서는 Topic 아래 Reliability Policy를 `Best Effort`로 바꾼다. Isaac Sim 센서·이미지는 Sensor Data QoS를 사용하는 경우가 일반적이다.

### 6.2 custom QoS가 저장되지 않는다

Isaac Sim 5.1의 `ROS2 QoS Profile` OmniGraph 노드는 `createProfile`을 먼저 `Custom`으로 바꾸지 않으면 다른 custom 값이 저장되지 않는 문제가 있다. 순서는 다음과 같다.

1. `createProfile = Custom`으로 정한다.
2. Reliability·Durability·History·Depth를 정한다.
3. stage를 저장한다.
4. 다시 열어 값이 유지되는지 확인한다.

`Transient Local` map처럼 late joiner가 과거 값을 받아야 하는 데이터와, 최신값이 중요한 camera stream을 같은 QoS로 통일하지 않는다.

## 7. simulation time과 timestamp

```bash
ros2 topic echo /clock --once
ros2 topic hz /clock
ros2 param get /rviz use_sim_time
ros2 param get /controller_server use_sim_time
```

`/clock`이 있는데 소비자가 wall time을 쓰면 메시지가 “미래” 또는 “과거”로 판단되어 TF lookup이 실패한다.

```bash
ros2 param set /rviz use_sim_time true
```

launch parameter에는 다음을 넣는다.

```python
Node(
    package="my_localizer",
    executable="localizer_node",
    parameters=[{"use_sim_time": True}],
)
```

`Isaac Read Simulation Time`은 기본적으로 stop/play를 반복해도 단조 증가한다. `resetOnStop=True`를 사용하면 시간이 0으로 되돌아간다. bag, filter, Nav2, MoveIt이 time jump를 처리할 수 있는지 확인한 경우에만 사용한다.

메시지별 timestamp를 비교한다.

```bash
ros2 topic echo /scan --field header --once
ros2 topic echo /odom --field header --once
ros2 topic echo /camera/front/camera_info --field header --once
```

## 8. TF 진단

먼저 전체 graph와 특정 transform을 동시에 본다.

```bash
mkdir -p /tmp/tf-check && cd /tmp/tf-check
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo map base_link
ros2 topic hz /tf
ros2 topic echo /tf_static --once \
  --qos-durability transient_local
```

확인할 불변 조건은 다음과 같다.

- 모든 child frame에는 부모가 하나뿐이다.
- `map -> odom -> base_link`가 끊기지 않는다.
- sensor message의 `header.frame_id`가 TF tree에 실제로 존재한다.
- joint 이름과 `/joint_states` 이름이 `robot_state_publisher`의 URDF와 일치한다.
- static transform은 `/tf_static`, 동적 transform은 `/tf`에 있다.
- 여러 robot은 frame prefix와 topic namespace를 모두 분리한다.

자주 보이는 오류를 해석한다.

| 오류 | 원인 후보 | 우선 조치 |
|---|---|---|
| `frame does not exist` | 이름 오타·publisher 미실행 | `view_frames`, message `frame_id`를 비교한다 |
| `extrapolation into the future` | clock 불일치·timestamp 앞섬 | 모든 node의 `use_sim_time`을 확인한다 |
| `extrapolation into the past` | 낮은 TF 주기·queue 지연 | publisher 주기와 처리 지연을 측정한다 |
| tree가 두 갈래로 찢어진다 | prefix 또는 static TF 누락 | root부터 sensor까지 한 단계씩 `tf2_echo`한다 |
| robot이 RViz에서 흔들린다 | odom과 TF를 두 source가 발행 | authority를 `topic info --verbose`로 찾는다 |

## 9. 제어가 움직이지 않거나 폭주한다

### 9.1 ROS 측 명령 확인

```bash
ros2 topic info /cmd_vel --verbose
ros2 topic echo /cmd_vel --once
ros2 topic hz /cmd_vel
ros2 topic echo /joint_states --once
```

안전한 짧은 이동 시험을 한다.

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}"
sleep 1
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

### 9.2 시뮬레이터 측 확인

- articulation root가 robot 전체를 포함하는가
- 제어 node의 target prim이 articulation root인가
- joint 이름·순서·drive mode가 명령과 일치하는가
- position과 velocity 목표를 동시에 충돌시켜 보내지 않는가
- stiffness, damping, max force가 단위와 질량에 맞는가
- wheel collider가 바닥에 닿고 friction이 충분한가
- command timeout 후 0속도로 가는 watchdog가 있는가

TurtleBot가 table 위에서 잘 움직이지 않는다면 table과 ground의 물리 재질 차이를 의심한다. wheel/ground friction과 controller parameter를 함께 확인한다.

## 10. camera·LiDAR·IMU 진단

### 10.1 주기와 대역폭을 수치화한다

```bash
ros2 topic hz /camera/front/image_raw --window 100
ros2 topic bw /camera/front/image_raw
ros2 topic hz /camera/front/camera_info --window 100
ros2 topic hz /front/scan --window 100
ros2 topic bw /front/points
ros2 topic hz /imu/data --window 100
```

image가 느리면 먼저 render product 해상도와 발행 주기를 낮춘다. 큰 image message는 network와 DDS queue를 동시에 압박한다. RGB 색이나 왜곡이 이상하면 camera parameter, render product resolution, anti-aliasing을 확인한다.

depth가 흑백 두 구간처럼만 보이면 시야 안의 무한대 depth가 표시 범위를 늘렸을 수 있다. 유효 거리 안에 배경을 두거나 depth 수치를 직접 검사한다.

```bash
ros2 topic echo /camera/front/depth/image_raw --once \
  --qos-reliability best_effort > /tmp/depth-sample.yaml
ros2 topic echo /camera/front/camera_info --once
```

RTX LiDAR는 sensor prim, render product, helper node 세 요소를 확인한다. scan frame과 point cloud frame이 TF에 있고, min/max range 안에 표적이 있는지도 본다.

IMU는 physics step보다 빠르게 새 물리 정보를 만들 수 없다. 발행 주기만 올렸는데 값이 반복되면 physics rate와 sensor period를 비교한다.

## 11. Nav2 진단

```bash
ros2 lifecycle nodes
ros2 lifecycle get /controller_server
ros2 action info /navigate_to_pose
ros2 topic echo /amcl_pose --once
ros2 topic echo /map --once \
  --qos-durability transient_local
ros2 topic hz /scan
ros2 run tf2_ros tf2_echo map base_link
```

아래 순서로 분리한다.

1. map의 resolution·origin·frame이 실제 environment와 맞는지 확인한다.
2. 초기 pose를 주고 `map -> odom`이 생기는지 확인한다.
3. `/scan`의 frame·angle·range와 장애물 방향이 맞는지 확인한다.
4. global plan이 생기는지, local costmap이 update되는지 확인한다.
5. `/cmd_vel`이 생성되는지 확인한다.
6. 명령이 있는데 robot이 안 움직이면 controller/physics로 내려간다.

다중 robot Nav2는 CPU 사용량이 높아 sensor 동기화와 controller command가 누락될 수 있는 5.1 알려진 문제가 있다. 공식 해결 순서는 LiDAR graph의 `Publish Full Scan`을 켜고, 그래도 실패하면 다음 옵션을 시험하는 것이다.

```bash
cd ~/isaacsim
./isaac-sim.sh \
  --/app/asyncRendering=true \
  --/app/renderFrameTimeout=60 \
  --/app/asyncPhysics=true
```

비동기 설정은 시간 순서와 재현성에 영향을 줄 수 있으므로 적용 전후 timestamp·RTF·성공률을 같은 scenario에서 비교한다.

## 12. MoveIt 2 진단

```bash
ros2 action list -t | grep -E 'move_group|trajectory'
ros2 topic echo /joint_states --once
ros2 topic hz /joint_states
ros2 run tf2_ros tf2_echo world panda_link0
ros2 node info /move_group
```

RViz에 robot이 없으면 URDF/SRDF, `robot_state_publisher`, fixed frame부터 확인한다. planning은 되지만 실행이 안 되면 다음을 확인한다.

- trajectory action 이름과 bridge/controller 이름이 같은가
- joint 이름과 순서가 USD articulation, URDF, SRDF, MoveIt controller 설정에서 같은가
- `/joint_states` timestamp가 simulation time인가
- planning group과 end-effector link가 존재하는가
- mimic/parallel gripper joint가 올바르게 모델링되었는가
- self-collision matrix가 실제 robot에 맞는가

Isaac Sim 5.1 공식 문제 해결에는 MoveIt RViz가 검게 보이는 경우 Mesa driver 갱신 안내가 있다. host를 즉시 변경하기 전에 RViz console, OpenGL renderer, container GPU 전달을 확인하고 driver 변경은 별도 복구 계획을 세운 뒤 수행한다.

## 13. 성능과 publish rate

목표 주기와 실제 주기를 각각 기록한다.

```bash
ros2 topic hz /clock --window 200
ros2 topic hz /tf --window 200
ros2 topic hz /joint_states --window 200
ros2 topic hz /camera/front/image_raw --window 50
nvidia-smi dmon -s pucm
```

한 번에 한 요소만 바꾼다.

1. 사용하지 않는 viewport·sensor·annotator를 끈다.
2. camera 해상도와 RTX LiDAR sample 수를 낮춘다.
3. sensor publisher마다 Simulation Gate로 필요한 주기만 발행한다.
4. image·point cloud subscriber queue와 처리 시간을 측정한다.
5. physics·render rate와 real-time factor를 함께 기록한다.
6. headless 실행을 비교한다.

`On Playback Tick`에 모든 publisher를 직접 연결했다고 동일 주기가 보장되지는 않는다. renderer나 CPU가 목표 frame을 못 맞추면 wall-clock publish rate도 낮아진다. simulation timestamp 간격과 wall-clock 수신 간격을 구분한다.

장시간 뒤에만 문제가 생기면 RSS와 GPU memory를 시간에 따라 기록한다.

```bash
pid=$(pgrep -n -f isaac-sim)
while kill -0 "$pid" 2>/dev/null; do
  date -Is
  ps -o pid,rss,vsz,%cpu,etime,cmd -p "$pid"
  nvidia-smi --query-compute-apps=pid,used_memory \
    --format=csv,noheader,nounits
  sleep 30
done | tee /tmp/isaac_ros_diag/memory-series.txt
```

5.1 문서는 일부 ROS sample과 joint-state 조합에서 장시간 memory leak 가능성을 알려 준다. 재현 stage를 최소화하고 증가율을 함께 보고한다.

## 14. 최소 bag으로 재현한다

전체 topic을 기록하면 문제가 더 심해질 수 있다. 원인에 필요한 topic만 고른다.

```bash
ros2 bag record -o /tmp/isaac_repro \
  /clock /tf /tf_static /joint_states /cmd_vel /odom /scan
```

기록 내용을 확인한다.

```bash
ros2 bag info /tmp/isaac_repro
```

camera 문제에는 raw image 전체 대신 짧은 구간과 `camera_info`, TF를 기록한다. 재생 시험에서는 실제 controller에 명령이 다시 전달되지 않도록 Domain ID나 command topic을 분리한다.

## 15. 증상별 빠른 표

| 증상 | 가장 가능성 높은 원인 | 첫 명령 |
|---|---|---|
| topic이 전혀 없다 | bridge·domain·graph 미실행 | `ros2 topic list -t` |
| topic만 있고 데이터가 없다 | tick·timeline·target prim | `ros2 topic info TOPIC --verbose` |
| RViz만 안 보인다 | QoS·fixed frame | `ros2 topic echo TOPIC --qos-reliability best_effort` |
| `rclpy` import 실패 | Python ABI 혼합 | `./python.sh -c 'import sys; print(sys.version)'` |
| TF future/past 오류 | clock 불일치 | `ros2 topic echo /clock --once` |
| Nav2가 명령을 안 낸다 | lifecycle·localization·scan | `ros2 lifecycle nodes` |
| 명령은 있는데 안 움직인다 | articulation·drive·friction | `ros2 topic echo /cmd_vel --once` |
| image가 느리다 | 해상도·DDS 대역폭 | `ros2 topic bw IMAGE_TOPIC` |
| 다중 robot 충돌 | CPU·sensor 동기화 | `ros2 topic hz /scan` |
| stage 재개 후 값이 다르다 | custom QoS 미저장 | `createProfile=Custom` 확인 |

## 16. 종료 기준

문제를 해결했다고 판단하려면 다음을 남긴다.

- 최소 재현 stage와 시작 명령
- 원인을 보여 주는 전후 로그 또는 수치
- 바꾼 설정 한 개와 이유
- 동일 seed로 여러 번 실행한 성공률
- regression bag 또는 자동 검증 명령
- 임시 workaround인지 근본 수정인지 구분

“재시작하니 된다”는 종료 기준이 아니다. 어떤 상태가 달랐고 어떻게 다시 검증할지를 기록해야 한다.

## 출처

- [Isaac Sim 5.1 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
- [Isaac Sim 5.1 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1 — ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)
- [Isaac Sim 5.1 — ROS 2 Quality of Service](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)
- [Isaac Sim 5.1 — ROS2 Setting Publish Rates](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html)
- [Isaac Sim 5.1 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
- [Isaac Sim 5.1 — Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- [ROS 2 Jazzy — Understanding ROS 2 Topics](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- [ROS 2 Jazzy — tf2 debugging](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Debugging-Tf2-Problems.html)
