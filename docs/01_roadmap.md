# 학습 로드맵

이 과정은 `tutorial_bot` 하나를 계속 확장하는 방식으로 진행한다. 먼저 Gazebo만으로 world와 model을 이해하고, 그다음 ROS 2 통신과 시각화를 연결하며, 마지막에 제어·자율주행·커스텀 plugin·테스트를 추가한다. 이 순서를 따르면 오류가 생겼을 때 SDF, Gazebo Transport, ROS 2 bridge, TF 가운데 어느 계층이 원인인지 분리할 수 있다.

## 각 장에서 반복하는 학습 방식

각 장은 `완성 목표 → 핵심 개념 → 저장소의 실제 파일 → 실행 명령 → 관찰 결과 → 실패 진단` 순서를 반복한다. 새 기능을 추가할 때마다 직전 단계의 observable을 다시 확인하므로, 마지막에 여러 기능을 한꺼번에 연결하고도 어느 경계에서 문제가 생겼는지 추적할 수 있다.

예를 들어 DiffDrive 장은 plugin 이름을 설명하는 데서 끝나지 않는다. 실제 Xacro의 joint와 plugin parameter를 읽고, world를 실행하고, `cmd_vel`을 발행하고, Gazebo odometry와 ROS 2 `/odom`을 차례대로 관찰한다.

## 전체 학습 흐름

| 구간 | 완성 상태 | 핵심 산출물 | 대표 검증 |
| --- | --- | --- | --- |
| 시작하기 | Jazzy/Harmonic 설치와 환경 진단 | 재현 가능한 개발 환경 | `gz sim --versions`, `ros2 pkg prefix ros_gz_sim` |
| 초급 전반 | SDF world와 두 바퀴 로봇 | 물리·collision·joint·DiffDrive | `gz sdf -k`, `gz topic -l` |
| 초급 후반 | 센서와 ROS 2 bridge | LiDAR·camera·IMU, bridge YAML | `ros2 topic echo /scan --once` |
| 중급 | URDF/Xacro, TF, RViz, control, Nav2 | 통합 launch와 controller 설정 | `ros2 launch ...`, `tf2_echo` |
| 고급 | C++ System Plugin과 자동화 | plugin library, headless test, CI | `colcon test`, 과정 matrix |

## 0단계: 실행 환경을 고정한다

Ubuntu, ROS 2, Gazebo 조합이 맞지 않으면 같은 SDF와 plugin 이름이라도 패키지나 ABI가 달라질 수 있다. 첫 실습 전에 다음 계약을 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
test "$ROS_DISTRO" = jazzy
gz sim --versions
ros2 pkg prefix ros_gz_bridge
ros2 pkg prefix ros_gz_sim
```

이 단계에서는 [지원 환경과 호환성](02_getting-started/00_compatibility.md), [Harmonic 소개](02_getting-started/01_gazebo-harmonic.md), [Jazzy 환경 설치](02_getting-started/02_installation-jazzy.md), [문제 해결](02_getting-started/03_troubleshooting.md)을 순서대로 진행한다.

## 1단계: ROS 2 없이 Gazebo를 이해한다

SDF world를 먼저 실행해 물리 server, GUI, system plugin, Gazebo Transport를 확인한다. ROS 2를 아직 연결하지 않으므로 world가 열리지 않는 문제와 bridge 문제를 혼동하지 않는다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

초급의 `Gazebo Sim 개요 → GUI 기초 → SDF 기초 → 첫 World` 순서가 이 구간에 해당한다. 완료 기준은 바닥과 물체를 GUI에서 확인하고, 별도 터미널에서 Gazebo 토픽을 찾는 것이다.

```bash
gz topic -l | sort
```

## 2단계: 로봇 구조와 주행을 만든다

링크에 관성·collision·visual을 추가하고 joint로 바퀴를 연결한다. 이후 DiffDrive system에 joint 이름과 실제 기구 치수를 전달한다.

```xml
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>0.38</wheel_separation>
  <wheel_radius>0.06</wheel_radius>
  <odom_publish_frequency>30</odom_publish_frequency>
</plugin>
```

`첫 Robot → 바퀴와 Joint → DiffDrive` 순서로 진행한다. 완료 기준은 Gazebo Transport의 velocity 명령으로 로봇이 이동하고 odometry가 발행되는 것이다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist \
  -p 'linear: {x: 0.4}, angular: {z: 0.3}'
gz topic -e -t /model/tutorial_bot/odometry
```

## 3단계: 센서를 추가하고 ROS 2로 연결한다

LiDAR, camera, IMU를 Gazebo sensor로 먼저 실행하고 Gazebo Transport 토픽을 확인한다. 그다음 필요한 토픽만 `ros_gz_bridge` YAML에 선언한다.

```yaml
- ros_topic_name: "/scan"
  gz_topic_name: "/tutorial_bot/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

`센서 → Gazebo Fuel → ROS 2와 연결 → 초급 프로젝트` 순서로 진행한다. 완료 기준은 ROS 2 쪽에서 센서 메시지를 한 번 이상 받고, keyboard teleop으로 주행 명령을 보내는 것이다.

```bash
ros2 topic echo /scan --once
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

## 4단계: URDF/Xacro와 ROS 2 도구를 통합한다

중급에서는 로봇 구조의 원본을 URDF/Xacro로 관리한다. 반복되는 바퀴와 센서는 macro로 만들고, `robot_state_publisher`가 같은 로봇 설명에서 TF를 생성하게 한다. Gazebo 전용 system과 sensor는 `<gazebo>` 확장 태그에 둔다.

```xml
<xacro:macro name="wheel" params="side y_position">
  <link name="${side}_wheel_link"> ... </link>
  <joint name="${side}_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="${side}_wheel_link"/>
    <origin xyz="0 ${y_position} -0.06"/>
    <axis xyz="0 1 0"/>
  </joint>
</xacro:macro>

<xacro:wheel side="left" y_position="0.19"/>
<xacro:wheel side="right" y_position="-0.19"/>
```

`고급 SDF → URDF·Xacro·SDF → ROS 2 Launch → Robot Spawn → bridge YAML → TF·RViz → gz_ros2_control → 센서 심화 → 다중 로봇 → Nav2 → 중급 프로젝트` 순서로 진행한다.

통합 stack은 한 명령으로 시작한다.

```bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=false
```

완료 기준은 `odom → base_link → sensor frame` TF를 조회하고, RViz에서 robot model, LaserScan, odometry trajectory를 같은 좌표계에 표시하는 것이다.

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 topic echo /odom --once
```

## 5단계: plugin과 검증을 코드로 만든다

고급에서는 Gazebo Entity-Component-System의 update 단계에 참여하는 C++ System Plugin을 작성한다. plugin 설정은 SDF에서 주입하고, 정상 동작과 잘못된 설정을 모두 headless 테스트로 검증한다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <publish_period>0.1</publish_period>
</plugin>
```

`ECS System Plugin → Transport 인터페이스 → 물리와 주기 디버깅 → Headless 통합 테스트 → CI 재현성 → 고급 프로젝트` 순서로 진행한다. 완료 기준은 GUI 없이 같은 입력에서 같은 observable과 cleanup receipt를 얻는 것이다.

## 파일별 책임

| 파일 종류 | 책임 | 중복하지 않는 내용 |
| --- | --- | --- |
| URDF/Xacro | 링크·joint tree, 관성, 재사용 macro | 별도의 동일 로봇 SDF 원본 |
| SDF world | 물리, 조명, 환경 model, world system | ROS 2 노드 orchestration |
| `<gazebo>` 확장 | Gazebo sensor·system과 URDF-SDF 보완 | ROS 2 bridge 방향 |
| bridge YAML | Gazebo↔ROS 토픽·타입·방향 | 센서 자체의 해상도와 noise |
| controller YAML | controller type, joint, 주기·제한 | 로봇 기하 구조 |
| launch | 파일 경로, process 순서, 인자 | 링크·sensor XML 본문 |

이 경계를 지키면 센서를 다른 로봇에 재사용하거나 world를 바꿀 때 수정 범위를 줄일 수 있다.

## 과정 완료 조건

초급 12개, 중급 12개, 고급 7개 경로와 선행 조건은 `docs/course-manifest.yaml`에 고정한다. 문서를 읽는 것만으로 완료하지 않고 다음 세 종류의 증거를 함께 남긴다.

1. XML, YAML, launch 파일이 정적 검사와 빌드를 통과해야 한다.
2. nominal과 fault scenario에서 의도한 observable을 확인해야 한다.
3. 실행이 끝난 뒤 이 과정이 시작한 process가 남지 않았다는 cleanup receipt를 확인해야 한다.

```bash
python3 -m mkdocs build --strict
python3 scripts/run_course_matrix.py --help
python3 scripts/audit_course_evidence.py --help
```

runtime을 건너뛴 결과나 source SHA가 달라진 과거 결과는 현재 과정의 통과 증거로 인정하지 않는다.

## 학습 흐름 참고

주제를 작은 실행 단위로 나누고 model과 sensor를 점진적으로 확장하는 흐름은 MOGI-ROS의 [Week-3-4-Gazebo-basics](https://github.com/MOGI-ROS/Week-3-4-Gazebo-basics)와 [Week-5-6-Gazebo-sensors](https://github.com/MOGI-ROS/Week-5-6-Gazebo-sensors)를 참고한다. 코드와 문장은 복사하지 않고 `tutorial_bot`, ROS 2 Jazzy, Gazebo Harmonic API와 이 저장소의 검증 구조에 맞게 독자적으로 작성한다.
