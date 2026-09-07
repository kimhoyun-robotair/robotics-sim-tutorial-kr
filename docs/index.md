# Gazebo Harmonic 한국어 튜토리얼

> **기준 환경:** Ubuntu 24.04 LTS · ROS 2 Jazzy · Gazebo Harmonic · amd64

이 튜토리얼은 Gazebo를 처음 사용하는 사람을 위한 실습 과정이다. 작은 가상 공간을 만든 뒤 로봇과 센서를 하나씩 추가한다. 각 장의 설명을 읽고 코드를 실행한 다음, Gazebo 화면과 ROS 2 토픽, TF, RViz에서 결과를 확인한다. 코드가 어디에 들어가는지, 어느 터미널에서 실행하는지, 성공했을 때 무엇이 보여야 하는지를 함께 다룬다.

## 진행하는 프로젝트

처음에는 바닥·조명·상자로 구성된 작은 월드를 실행한다. 이후 `tutorial_bot`에 차체, 바퀴, 차동 구동, LiDAR, 카메라, IMU를 순서대로 추가한다. 중급에서는 ROS 2 실행 파일인 launch로 TF, RViz, 센서 브리지, 제어기, Nav2를 함께 실행한다. 고급에서는 C++ 시스템 플러그인과 자동화 테스트를 작성한다. 마지막 [Rover 파이널 프로젝트](07_final-project/index.md)에서는 이 내용을 4륜 로버와 F1Tenth 차량에 적용한다.

| 단계 | 직접 작성하는 코드 | 시각화를 통한 확인 |
| --- | --- | --- |
| 가상 환경 | SDF의 `<world>`, 물리·장면 플러그인 | Gazebo 화면과 `/clock` |
| 로봇 형상 | URDF 링크·관절과 Xacro 매크로 | 로봇 형상과 좌표계 연결 관계 |
| 주행 | DiffDrive 플러그인과 `cmd_vel` 브리지 | 이동, `/odom`, RViz의 이동 궤적 |
| 센서 | 센서 정의와 브리지 YAML | 스캔, 영상, 점군, 관성 측정값 |
| 통합 | Python launch와 제어기 YAML | 한 명령으로 실행하는 로봇 시뮬레이션 |
| 확장 | C++ 시스템 플러그인과 테스트 | 입력에 따른 동작과 자동 검사 결과 |
| 파이널 프로젝트 | 이식한 Rover 패키지와 Nav2 코드 | 센서 정렬, 지도 작성, 목표 위치 도착 |

## 세 가지 파일 형식

**SDF**는 가상 공간인 월드, 물리 설정, Gazebo 센서를 정의한다. **URDF**는 ROS 2가 사용하는 로봇의 부품(링크)과 관절 연결 관계를 정의한다. **Xacro**는 변수와 매크로로 반복 코드를 줄여 URDF 등을 만드는 도구다. 처음부터 모든 문법을 외울 필요는 없다. 실습에서 각 파일을 작성하며 익힌다.

다음은 월드의 물리 계산 간격을 0.001초로 설정하는 SDF 발췌다. 바닥과 조명은 생략했으므로 실행할 때는 아래에 안내한 전체 파일을 사용한다.

```xml
<sdf version="1.10">
  <world name="first_world">
    <physics name="default_physics" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster"/>
  </world>
</sdf>
```

전체 코드는 `examples/gazebo/worlds/first-world.sdf`다. [환경 설치](02_getting-started/02_installation-jazzy.md)를 마친 뒤, 저장소 루트에서 다음 두 명령으로 문법 검사와 실행을 차례대로 진행한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

## Gazebo와 ROS 2 사이의 경계

Gazebo 토픽과 ROS 2 토픽은 서로 다른 통신 방식을 사용한다. **`ros_gz_bridge`**가 두 시스템 사이에서 메시지를 변환하고 전달한다. 설정에는 양쪽 토픽 이름, 메시지 형식, 전달 방향을 적는다. 다음은 Gazebo DiffDrive를 사용하는 초급 예제의 일부다.

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ

- ros_topic_name: "/odom"
  gz_topic_name: "/model/tutorial_bot/odometry"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS
```

전체 설정은 `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`에서 확인한다. `ROS_TO_GZ`는 키보드 조종 명령을 Gazebo로 보내고, `GZ_TO_ROS`는 Gazebo의 위치 추정값을 ROS 2로 전달한다. 중급에서 사용하는 `gz_ros2_control`은 주행 명령을 ROS 2 제어기로 직접 보내므로 이 주행 브리지를 함께 켜지 않는다. 실행 방법은 [브리지 실습](03_beginner/10-ros-gz-bridge.md), 설정 형식은 [Jazzy 공식 문서](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)를 참고한다.

## 시작 전 환경 확인

새 터미널에서 ROS 2 기본 환경을 먼저 불러온다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    ```

다음 진단에서 `ROS_DISTRO`는 `jazzy`이고, `gz sim --versions`는 Gazebo Sim 8 계열이어야 한다.

```bash
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-unset}"
gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
```

`gz sim`은 Gazebo Harmonic의 명령이다. Gazebo Classic의 `gazebo`, 구형 명칭의 `ign gazebo`, Classic용 `gazebo_ros_pkgs`와 섞이지 않도록 주의한다.

## 권장 학습 순서

1. [지원 환경과 호환성](02_getting-started/00_compatibility.md)을 확인하고 [Jazzy 환경 설치](02_getting-started/02_installation-jazzy.md)를 완료한다.
2. [SDF 기초](03_beginner/03-sdf-basics.md)와 [첫 월드](03_beginner/04-first-world.md)에서 ROS 2 없이 Gazebo를 실행해 본다.
3. 초급에서 링크·관절, DiffDrive, 센서를 구성하고 Gazebo 토픽을 확인한다.
4. `ros_gz_bridge`로 주행 명령, 위치 추정값, 센서 데이터를 ROS 2에 연결하고 RViz에서 확인한다.
5. 중급에서 Xacro 재사용, TF, `gz_ros2_control`, 다중 로봇, Nav2를 하나의 launch로 통합한다.
6. 고급에서 C++ 시스템 플러그인과 화면 없이 실행하는 테스트를 작성한다.
7. [Rover 파이널 프로젝트](07_final-project/index.md)에서 4륜 주행, 센서 정렬, 지도 작성, Nav2 주행, F1Tenth 조향을 실습한다.

학습 순서와 선행 조건은 `docs/course-manifest.yaml`에도 정리되어 있다. 실제 검증 범위와 실행하지 못한 항목은 [Jazzy 점검 기록](06_reference/04_jazzy-audit.md)에서 확인한다.

!!! tip "CLI 실행 원칙"

    별도 안내가 없으면 명령은 저장소 루트(`~/robotics-sim-tutorial-kr`)에서 실행한다. 실습용 새 터미널마다 ROS 2와 작업 공간의 `setup.bash`를 불러온다. `pwd`와 `git branch --show-current`로 현재 폴더와 `Jazzy` 브랜치를 확인하면 경로 실수를 줄일 수 있다.
