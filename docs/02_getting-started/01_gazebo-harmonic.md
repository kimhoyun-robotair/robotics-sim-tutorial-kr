# Gazebo Harmonic 소개

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [지원 환경과 호환성](00_compatibility.md)

## 학습 목표

- Gazebo 서버, GUI, Transport의 개념을 익히고 담당 범위를 구분한다.
- SDF 월드가 시스템 플러그인을 불러오는 방식을 코드로 확인한다.
- Gazebo Transport 토픽과 ROS 2 토픽이 서로 다른 통신 그래프인 이유를 이해한다.
- 서버 전용 실행, GUI 연결, 토픽 조회를 각각 수행한다.

## 서버, GUI, 통신의 역할

Gazebo Sim은 하나의 창처럼 보이지만 물리 계산, 화면 표시, 통신이 역할을 나눠 맡는다. 이 장은 구조를 먼저 소개한다. 처음 설치하는 경우 [설치 안내](02_installation-jazzy.md)를 마친 뒤 실행 예제로 돌아온다.

| 부분 | 책임 | 대표적인 명령 |
| --- | --- | --- |
| 서버 | 물리 계산, 개체 상태 관리, 시스템 실행 | `gz sim -s -r world.sdf` |
| GUI | 장면 렌더링, 카메라 조작, GUI 플러그인 | `gz sim -g` |
| Transport | Gazebo 프로세스 사이의 토픽·서비스 통신 | `gz topic -l`, `gz service -l` |

GUI가 강제 종료되었다고 해서 항상 물리 서버의 문제인 것은 아니다. 이 구조를 이용하면 SDF 문법 검사, 서버, 렌더링, ROS 브리지를 순서대로 분리해 어디가 문제인지 진단할 수 있다.

## SDF는 월드와 시스템을 구성한다

SDF는 시뮬레이션 월드, 모델, 링크, 조인트, 센서, 플러그인을 표현하는 XML 형식이다. 다음 코드는 `examples/gazebo/worlds/first-world.sdf`의 핵심 구조를 축약한 예이다.

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="first_world">
    <gravity>0 0 -9.8</gravity>
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

    <light name="sun" type="directional">
      <pose>0 0 10 0 0 0</pose>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <model name="ground">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane><normal>0 0 1</normal><size>20 20</size></plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane><normal>0 0 1</normal><size>20 20</size></plane>
          </geometry>
        </visual>
      </link>
    </model>
  </world>
</sdf>
```

`<max_step_size>0.001</max_step_size>`는 시뮬레이션 시간을 한 번 갱신할 때 1 ms씩 진행하게 한다. `<real_time_factor>1.0</real_time_factor>`는 계산 성능이 충분할 때 시뮬레이션 시간과 실제 시간의 목표 비율을 1로 둔다. 센서 갱신률은 각 센서의 `<update_rate>`로 따로 정한다. 계산이 밀리면 실제 1초 동안 받는 센서 메시지 수가 설정값보다 적을 수 있다.

월드에서 명시적으로 불러온 시스템의 역할은 다음과 같다.

| 시스템 플러그인 | 역할 | 주요 설정 위치 |
| --- | --- | --- |
| `Physics` | 조인트와 collision을 포함한 물리 상태를 갱신한다. | `<physics>`의 단계와 실시간 계수 |
| `UserCommands` | 개체 생성·삭제·위치와 자세 변경 서비스를 제공한다. | 일반적으로 별도 파라미터가 필요하지 않다. |
| `SceneBroadcaster` | GUI가 받을 장면 상태를 게시한다. | 일반적으로 별도 파라미터가 필요하지 않다. |
| `Sensors` | 카메라와 GPU LiDAR 등 렌더링 센서를 갱신한다. | `<render_engine>ogre2</render_engine>` |
| `Imu` | IMU 센서 데이터를 갱신한다. | 센서 안의 갱신률과 노이즈 |

렌더링 센서를 사용하는 월드에서는 다음 시스템을 추가한다.

```xml
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
<plugin filename="gz-sim-imu-system"
        name="gz::sim::systems::Imu"/>
```

센서의 해상도, 시야각, 갱신률, 노이즈는 이 월드 플러그인이 아니라 각 `<sensor>` 요소에서 설정한다. 이후 센서 장에서 실제 센서 XML을 작성한다.

## 첫 월드를 서버와 GUI로 나눠 실행한다

터미널 1에서 저장소 루트로 이동한 뒤 SDF를 검사하고 서버만 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

`-s`는 서버 전용, `-r`은 일시 정지하지 않고 즉시 시뮬레이션을 진행한다는 뜻이다. 터미널 2에서 같은 Gazebo partition의 GUI만 시작한다.

```bash
gz sim -g
```

GUI에 바닥, 붉은 상자, 파란 원기둥이 보이면 서버의 장면이 GUI로 전달된 것이다. 서버와 GUI를 함께 실행하려면 두 터미널에서 먼저 `Ctrl+C`로 종료한 뒤 다음 명령을 사용한다.

```bash
gz sim -r examples/gazebo/worlds/first-world.sdf
```

## Gazebo Transport를 직접 확인한다

터미널 3에서 Gazebo 통신 그래프를 확인한다.

```bash
gz topic -l | sort
gz service -l | sort
```

시뮬레이션 clock 메시지를 직접 구독한다.

```bash
gz topic -e -t /clock
```

시간 필드가 계속 바뀌면 서버가 물리 계산 단계를 진행하고 Transport로 clock을 발행하는 상태이다. 확인을 마치면 구독 중인 터미널에서 `Ctrl+C`를 누른다. 서버는 다음 브리지 실습을 위해 계속 실행해 둔다.

사용 가능한 명령과 옵션은 설치된 버전에서 직접 확인한다.

```bash
gz --commands
gz sim --help
gz topic --help
gz service --help
gz model --help
```

## ROS 2 통신 그래프는 자동으로 생기지 않는다

Gazebo Transport와 ROS 2 DDS는 서로 다른 통신 체계이다. `gz topic -l`에 `/clock`이 보여도 `ros2 topic list`에는 자동으로 나타나지 않는다. 다음처럼 브리지를 실행해야 메시지가 변환된다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
```

문자 `[`는 Gazebo에서 ROS 2로만 전달한다는 뜻이다. 별도 터미널에서 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /clock --once
```

브리지 CLI의 방향 기호는 다음과 같다.

| 기호 | 전달 방향 | 사용 예 |
| --- | --- | --- |
| `@` | 양방향 | 상태와 명령을 양쪽에서 모두 주고받아야 할 때 사용한다. |
| `[` | Gazebo → ROS 2 | 시계, 오도메트리, 센서 데이터에 사용한다. |
| `]` | ROS 2 → Gazebo | `cmd_vel`과 같은 명령에 사용한다. |

토픽이 많아지면 CLI 문자열을 나열하지 않고 YAML 설정으로 옮긴다. YAML 방식은 설치 장에서 최소 예제로 확인하고, 브리지 심화 장에서 queue, lazy, QoS를 함께 다룬다.

## 결과 확인

다음 네 항목을 모두 확인하면 이 장을 완료한다.

1. `gz sdf -k`가 오류 없이 끝나야 한다.
2. 서버 전용 상태에서 `/clock`을 Gazebo Transport로 받아야 한다.
3. 별도의 `gz sim -g`가 실행 중인 서버의 장면을 표시해야 한다.
4. clock 브리지를 실행한 뒤 ROS 2의 `/clock` 메시지를 한 번 받아야 한다.

## 다음 단계

[ROS 2 Jazzy와 Gazebo Harmonic 설치](02_installation-jazzy.md)에서 전체 패키지와 실습 작업 공간을 준비한다. 이미 설치를 마쳤다면 [SDF 기초](../03_beginner/03-sdf-basics.md)와 [첫 월드](../03_beginner/04-first-world.md)를 진행한다.
