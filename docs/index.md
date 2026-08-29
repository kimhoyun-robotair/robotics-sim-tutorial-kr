# Gazebo Sim 튜토리얼에 오신 것을 환영한다

> **기준 환경:** Ubuntu 24.04 LTS · ROS 2 Jazzy · Gazebo Harmonic · amd64 · headless/software rendering

이 튜토리얼은 Gazebo Sim을 단순한 3D 뷰어가 아니라 재현 가능한 로봇 시뮬레이션 프로젝트로 사용하는 방법을 다룬다. 개념을 읽은 직후 대응하는 SDF, URDF/Xacro, YAML, launch 코드를 확인하고, 실행 결과를 Gazebo Transport 토픽, ROS 2 토픽, TF, RViz로 검증한다.

## 무엇을 완성하는가

처음에는 바닥·조명·상자로 구성된 작은 SDF world를 실행한다. 이후 같은 `tutorial_bot`에 차체, 바퀴, DiffDrive, LiDAR, 카메라, IMU를 순서대로 추가한다. 중급에서는 ROS 2 launch, TF, RViz, `ros_gz_bridge`, `gz_ros2_control`, Nav2를 연결한다. 고급에서는 Gazebo ECS와 C++ System Plugin, headless 통합 테스트, CI까지 확장한다.

| 단계 | 직접 작성하는 코드 | 눈으로 확인하는 결과 |
| --- | --- | --- |
| World | SDF의 `<world>`, 물리·scene system | Gazebo GUI와 `/clock` |
| Robot | URDF 링크·joint와 Xacro macro | model 형상과 TF tree |
| 주행 | DiffDrive system과 `cmd_vel` bridge | 이동, `/odom`, RViz trajectory |
| 센서 | SDF sensor와 bridge YAML | LaserScan, Image, PointCloud2, Imu |
| 통합 | Python launch와 controller YAML | 한 명령으로 시작하는 simulation stack |
| 확장 | C++ System Plugin과 테스트 | 결정적인 headless 검증 결과 |

## 먼저 구분할 세 가지 파일

SDF는 world와 Gazebo 전용 system·sensor를 표현하는 데 강하다. URDF는 ROS 2가 사용하는 로봇 링크·joint tree의 기준이다. Xacro는 반복되는 URDF XML을 macro와 인자로 생성한다.

다음은 실제 첫 world에서 물리 system과 simulation step을 설정하는 부분이다.

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

전체 코드는 `examples/gazebo/worlds/first-world.sdf`에 있다. 다음 두 명령으로 문법과 실행을 차례대로 확인한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

## Gazebo와 ROS 2 사이의 경계

Gazebo 내부 토픽은 Gazebo Transport를 사용하고 ROS 2 토픽은 DDS를 사용한다. 두 이름과 메시지 형식이 비슷해도 자동으로 연결되지 않는다. `ros_gz_bridge` 설정에서 양쪽 토픽, 양쪽 메시지 형식, 전달 방향을 명시한다.

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

전체 설정은 `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`에서 확인한다. `ROS_TO_GZ`는 keyboard teleop 명령을 Gazebo로 전달하고, `GZ_TO_ROS`는 Gazebo odometry를 ROS 2와 RViz로 전달한다.

## 시작 전 환경 확인

새 터미널에서 ROS 2 underlay를 먼저 불러온다.

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

`gz sim`은 Gazebo Harmonic의 명령이다. Gazebo Classic의 `gazebo`, 구형 명칭의 `ign gazebo`, Classic용 `gazebo_ros_pkgs`와 섞지 않는다.

## 권장 학습 순서

1. [지원 환경과 호환성](02_getting-started/00_compatibility.md)을 확인하고 [Jazzy 환경 설치](02_getting-started/02_installation-jazzy.md)를 완료한다.
2. [SDF 기초](03_beginner/03-sdf-basics.md)와 [첫 World](03_beginner/04-first-world.md)를 실행해 ROS 2 없이도 Gazebo server를 진단할 수 있게 한다.
3. 초급에서 링크·joint, DiffDrive, 센서를 구성하고 Gazebo Transport 토픽을 확인한다.
4. `ros_gz_bridge`로 `cmd_vel`, odometry, 센서를 ROS 2에 연결하고 RViz에서 시각화한다.
5. 중급에서 Xacro 재사용, TF, `gz_ros2_control`, 다중 로봇, Nav2를 하나의 launch로 통합한다.
6. 고급에서 C++ System Plugin과 headless 테스트를 작성해 동작을 자동으로 검증한다.

전체 경로의 선행 조건과 구현 산출물은 `docs/course-manifest.yaml`에 고정한다.

!!! tip "명령 실행 원칙"

    별도 안내가 없으면 명령은 저장소 루트에서 실행한다. 먼저 `pwd`와 `git branch --show-current`를 확인하면 잘못된 상대 경로나 브랜치에서 작업하는 실수를 줄일 수 있다.
