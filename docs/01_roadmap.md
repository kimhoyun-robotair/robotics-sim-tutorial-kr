# 학습 로드맵

이 튜토리얼 과정은 작은 로봇 `tutorial_bot`을 만들고 기능을 하나씩 붙이는 방식으로 진행한다. 먼저 Gazebo에서 물체와 로봇을 다루고, 센서 데이터를 ROS 2로 전달한 뒤 RViz·제어·자율주행을 연결한다. 고급에서는 플러그인과 자동 검사를 작성하고, 마지막에는 외부 Rover 패키지를 Jazzy/Harmonic으로 옮긴 파이널 프로젝트를 완성한다.

Gazebo를 처음 접한다면 아래 순서대로 진행한다. 이 페이지의 코드는 앞으로 다룰 내용의 예고이며, 실제 실행 준비와 전체 코드는 연결된 장에서 설명한다.

## 각 장의 진행 방식

각 실습은 **목표 → 준비 → 개념과 코드 → 실행 → 결과 확인 → 문제 해결** 순서로 읽는다. 기능을 하나 추가할 때마다 바로 이전 단계도 다시 확인한다. 예를 들어 센서가 RViz에 보이지 않으면 Gazebo 센서 발행, 브리지 전달, ROS 2 메시지, TF 순서로 원인을 좁힌다.

| 구간 | 만드는 것 | 완료 기준 |
| --- | --- | --- |
| 시작하기 | Ubuntu 24.04·Jazzy·Harmonic 실행 환경 | Gazebo 실행과 ROS 패키지 경로 확인 |
| 초급 전반 | 월드와 두 바퀴 로봇 | 물체 표시·충돌·관절·주행 확인 |
| 초급 후반 | LiDAR·카메라·IMU와 ROS 2 연결 | 센서 메시지 수신과 키보드 주행 |
| 중급 | Xacro·TF·RViz·제어·Nav2 통합 | 센서가 올바른 위치에 표시되고 목표까지 주행 |
| 고급 | C++ 시스템 플러그인과 자동 검사 | 정상 동작·오류 처리·프로세스 종료 확인 |
| 파이널 프로젝트 | 이식한 Rover와 F1Tenth 차량 | 빌드·주행·센서·지도·자율주행을 단계별로 확인 |

## 0단계: 실행 환경 맞추기

운영체제나 ROS·Gazebo 버전이 다르면 같은 파일도 의존 패키지와 API 차이로 실행되지 않을 수 있다. [지원 환경](02_getting-started/00_compatibility.md), [Harmonic 소개](02_getting-started/01_gazebo-harmonic.md), [Jazzy 설치](02_getting-started/02_installation-jazzy.md)를 먼저 진행한다.

설치를 마친 터미널에서 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
test "$ROS_DISTRO" = jazzy
gz sim --versions
ros2 pkg prefix ros_gz_bridge
ros2 pkg prefix ros_gz_sim
```

`ROS_DISTRO`는 `jazzy`, Gazebo Sim의 주 버전은 `8`이어야 하며 두 패키지 경로가 출력돼야 한다. 명령을 찾지 못하면 [문제 해결](02_getting-started/03_troubleshooting.md)로 돌아간다. 새 터미널에서도 `source` 명령으로 환경을 불러온다.

## 1단계: Gazebo의 월드와 GUI 익히기

[초급 과정](03_beginner/index.md)의 `Gazebo Sim 개요 → GUI 기초 → SDF 기초 → 첫 월드`를 진행한다. 월드(world)는 물리 설정, 조명, 물체가 들어 있는 가상 환경이다. 이 단계에서는 ROS 노드를 연결하지 않고 Gazebo 자체의 실행과 통신을 확인한다.

저장소 최상위에서 실행한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

첫 명령의 검사가 성공하고, 두 번째 명령에서 바닥과 물체가 보여야 한다. GUI를 켜 둔 채 다른 터미널에서 토픽 목록을 확인한다.

```bash
gz topic -l
```

실습을 마치면 서버를 실행한 터미널에서 `Ctrl+C`로 종료한다.

## 2단계: 로봇 구조와 바퀴 구동 만들기

`첫 로봇 → 바퀴와 관절 → DiffDrive` 순서로 진행한다. 링크는 질량과 형상을 갖는 로봇의 부품이고, 관절은 링크 사이의 연결이다. 바퀴의 회전축과 치수를 정의한 뒤 DiffDrive 플러그인에 같은 값을 전달한다.

다음은 실제 `tutorial_bot`에서 사용하는 설정의 일부다. 두 바퀴 중심 간 거리는 0.38 m, 반지름은 0.06 m다.

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

[DiffDrive 장](03_beginner/07-diff-drive.md)의 빌드·생성 절차를 마친 뒤 속도 명령을 보내 로봇이 움직이고 위치 추정 토픽이 발행되는지 확인한다. 주행 확인 후에는 속도 0 명령을 보내 정지시킨다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0.2}, angular: {z: 0}'
```

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0}, angular: {z: 0}'
```

## 3단계: 센서와 ROS 2 연결하기

`센서 → Gazebo Fuel → ROS 2와 연결 → 초급 프로젝트` 순서로 진행한다. 센서를 Gazebo에서 먼저 실행한 뒤 필요한 토픽을 `ros_gz_bridge`로 ROS 2에 전달한다. 아래는 LiDAR의 브리지 설정이다.

```yaml
- ros_topic_name: "/scan"
  gz_topic_name: "/tutorial_bot/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

Gazebo의 `/tutorial_bot/lidar` 메시지를 ROS 2의 `/scan`으로 보낸다는 뜻이다. 통합 실행 후 별도 터미널에서 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /scan --once --qos-reliability best_effort
```

메시지를 한 번 받으면 명령이 끝난다. `header.frame_id`와 거리 배열을 확인한다. 카메라·IMU도 같은 순서로 확인한 뒤 [초급 프로젝트](03_beginner/11_project-tutorial-bot.md)에서 키보드 주행을 연결한다.

## 4단계: TF·RViz·제어·자율주행 통합하기

[중급 과정](04_intermediate/index.md)에서는 URDF/Xacro를 로봇 구조의 원본으로 관리한다. 반복되는 바퀴·센서 정의는 매크로로 만들고, `robot_state_publisher`가 그 구조에서 TF를 발행하게 한다. TF는 로봇 본체와 센서 좌표계 사이의 위치·회전 관계다.

`고급 SDF → URDF·Xacro·SDF → ROS 2 Launch → 로봇 생성 → 브리지 YAML → TF·RViz → gz_ros2_control → 센서 심화 → 다중 로봇 → Nav2 → 중급 프로젝트` 순서로 진행한다.

중급에서 빌드를 마치면 저장소 최상위에서 통합 실행을 시작한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=false
```

별도 터미널에서 본체 TF를 확인한다. 이 명령은 계속 출력되므로 확인 후 `Ctrl+C`로 끝낸다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run tf2_ros tf2_echo odom base_link
```

완료하려면 로봇 모델, LiDAR, 카메라 점군이 RViz의 같은 기준 좌표계에서 실제 장애물과 맞아야 한다. 토픽 수신뿐 아니라 센서 장착 위치·광학 좌표축·메시지 프레임·QoS를 확인한다. 이후 Nav2를 연결하고 목표 위치까지 이동하는지 검증한다.

## 5단계: 플러그인과 자동 검사 작성하기

[고급 과정](05_advanced/index.md)에서는 로봇의 평면 이동 거리를 누적하는 C++ 시스템 플러그인을 만든다. 플러그인은 SDF에서 설정을 읽고 Gazebo의 갱신 단계마다 로봇 상태를 관찰한다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <publish_period>0.1</publish_period>
</plugin>
```

`ECS 시스템 플러그인 → Transport 인터페이스 → 물리와 주기 디버깅 → GUI 없는 통합 테스트 → CI 재현성 → 고급 프로젝트` 순서로 진행한다. 정상 입력에서 거리·초기화가 동작하고, 잘못된 설정에는 의도한 오류가 나와야 한다. 각 검사가 실행한 프로세스가 모두 끝났는지도 기록한다.

## 6단계: Rover 파이널 프로젝트 완성하기

[파이널 프로젝트](07_final-project/index.md)는 `Gazebo_Harmonic_Rover`의 Rover와 F1Tenth 차량을 ROS 2 Jazzy + Gazebo Harmonic에서 실행하도록 통합한 과정이다. 프로젝트의 파일 구조와 이식 기록을 읽고 **빌드 → 첫 주행 → 센서와 RViz → 지도 작성·자율주행** 순서로 진행한다.

`tutorial_bot`에서 익힌 메시지·TF·제어 원칙을 다른 차량 구조에 적용하는 단계다. 각 차량의 실제 토픽과 프레임 이름은 해당 프로젝트 문서를 따른다.

## 파일별 역할

| 파일 종류 | 담당하는 내용 |
| --- | --- |
| URDF/Xacro | 링크·관절 구조, 관성, 재사용 매크로 |
| SDF 월드 | 물리 설정, 조명, 환경 모델, 월드 플러그인 |
| URDF의 `<gazebo>` 확장 | Gazebo 전용 센서·플러그인과 변환 설정 |
| 브리지 YAML | Gazebo ↔ ROS 2 토픽 이름·메시지 타입·방향·QoS |
| 제어기 YAML | 제어기 종류, 관절 이름, 갱신 주기, 속도 제한 |
| 실행 파일(launch) | 프로세스 시작, 경로와 인자 전달, 실행 순서 |

## 과정 완료 기준

문서를 읽거나 명령이 종료된 것만으로 완료를 판단하지 않는다. 다음 결과를 함께 확인한다.

1. XML·YAML·실행 파일 검사와 빌드가 성공한다.
2. 정상 입력과 의도적으로 잘못된 입력에서 기대한 결과가 나온다.
3. 센서·주행 실습은 실제 메시지와 RViz 화면의 좌표·형상을 확인한다.
4. 검사에서 시작한 프로세스가 종료되고 결과를 다시 확인할 수 있는 로그가 남는다.

문서 작성자는 저장소 최상위에서 다음 명령으로 문서 빌드와 자동 검사 도구의 사용법을 확인한다.

```bash
python3 -m mkdocs build --strict
python3 scripts/run_course_matrix.py --help
python3 scripts/audit_course_evidence.py --help
```
