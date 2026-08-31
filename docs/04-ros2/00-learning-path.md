# ROS 2 Jazzy 통합 학습 경로

이 장의 목표는 Ubuntu 24.04의 ROS 2 Jazzy와 Isaac Sim 5.1을 연결한 뒤, 토픽을 한 번 확인하는 수준을 넘어 이동 로봇과 매니퓰레이터를 실제 ROS 2 스택으로 운용하는 데 있다. 모든 실습은 **Isaac Sim 5.1**, **Ubuntu 24.04**, **ROS 2 Jazzy**를 기준으로 한다.

## 전체 구조를 먼저 이해하다

Isaac Sim과 ROS 2는 같은 Python 프로세스가 아니다. Isaac Sim 내부의 ROS 2 Bridge가 시뮬레이션 데이터를 ROS 메시지로 직렬화하고, DDS가 외부 Jazzy 노드와 데이터를 교환한다.

```text
Isaac Sim 5.1 (Kit, Python 3.11)
  ├─ USD Stage / PhysX / RTX 센서
  ├─ Action Graph와 ROS 2 Bridge
  └─ 내장 Jazzy 라이브러리
             ⇅ DDS
Ubuntu 24.04 ROS 2 Jazzy (Python 3.12)
  ├─ ros2 CLI / RViz2
  ├─ Nav2 / MoveIt 2
  └─ 사용자 colcon 워크스페이스
```

두 Python 버전이 달라도 DDS 통신에는 문제가 없다. 다만 시스템 Jazzy의 Python 3.12용 `rclpy`를 Isaac Sim의 Python 3.11 프로세스에 직접 로드하면 충돌한다. 커스텀 메시지를 Isaac Sim 내부 Python에서 import할 때만 Python 3.11용 별도 빌드가 필요하다.

## 권장 학습 순서

| 순서 | 문서 | 도달 목표 | 완료 검증 |
|---:|---|---|---|
| 1 | [`01-install-bridge-workspace.md`](01-install-bridge-workspace.md) | Bridge와 공식 워크스페이스를 구성한다. | `/clock`을 한 번 수신한다. |
| 2 | [`02-time-tf-and-motion.md`](02-time-tf-and-motion.md) | 시간, TF, odometry, QoS를 이해한다. | `view_frames`와 `topic info -v`를 통과한다. |
| 3 | [`10-control-cookbook.md`](10-control-cookbook.md) | 차동·Ackermann·관절 제어를 구성한다. | `/cmd_vel` 또는 joint command로 robot을 움직인다. |
| 4 | [`11-sensor-topic-cookbook.md`](11-sensor-topic-cookbook.md) | RGB, depth, camera info, LiDAR, IMU를 발행한다. | RViz2에서 영상과 scan을 확인한다. |
| 5 | [`12-nav2-workshop.md`](12-nav2-workshop.md) | 점유 지도와 Nav2를 연결한다. | 목표 지점까지 자율주행한다. |
| 6 | [`13-moveit2-workshop.md`](13-moveit2-workshop.md) | Franka와 MoveIt 2를 연결한다. | 계획 후 실제 joint가 실행된다. |
| 7 | [`14-custom-interfaces-launch-and-sim-control.md`](14-custom-interfaces-launch-and-sim-control.md) | launch, generic node, 커스텀 인터페이스, simulation control을 다룬다. | 커스텀 메시지와 서비스를 왕복한다. |
| 8 | [`15-diagnostics-playbook.md`](15-diagnostics-playbook.md) | 계층별로 장애를 분리한다. | 새 shell에서 재현 가능한 진단 기록을 만든다. |

## 실습에서 지킬 터미널 규칙

이 튜토리얼은 셸 역할을 고정한다.

```bash
# 터미널 A: 시스템 ROS를 source하지 않고 Isaac Sim을 실행한다.
cd ~/isaacsim
./isaac-sim.sh
```

```bash
# 터미널 B: 외부 ROS 2 도구를 실행한다.
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
```

여러 머신이나 컨테이너를 연결할 때만 공식 워크스페이스의 UDP 프로필을 추가한다.

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
```

## 데이터 흐름을 읽는 법

Action Graph의 ROS 2 파이프라인은 대개 다음 네 부분으로 구성된다.

1. `On Playback Tick` 또는 physics step이 실행을 발생시킨다.
2. `ROS 2 Context`가 Domain ID와 DDS context를 제공한다.
3. Isaac 노드가 Stage, articulation 또는 센서 데이터를 읽는다.
4. ROS 2 publisher/helper가 메시지로 변환해 토픽을 발행한다.

subscriber는 이 흐름을 반대로 수행한다. 메시지가 왔다는 이유만으로 물리 제어가 안전해지는 것은 아니다. 마지막 명령 시각을 추적하고 timeout 때 0 속도를 적용하는 watchdog을 실제 프로젝트에 추가해야 한다.

## 공통 관찰 명령

```bash
ros2 node list
ros2 topic list -t
ros2 topic info /clock -v
ros2 topic hz /joint_states
ros2 service list -t
ros2 action list -t
```

토픽 이름만 보인다고 데이터가 정상인 것은 아니다. 다음 네 가지를 함께 확인한다.

- publisher와 subscriber 수
- 메시지 타입
- QoS 호환성
- 타임스탬프와 frame ID

## 5.1 버전 경계

- Isaac Sim 5.1 문서는 지원 종료 버전임을 표시한다. 이 과정은 재현성을 위해 5.1 API와 확장 ID만 사용한다.
- 4.5 이전의 `omni.isaac.*` 이름을 복사하지 않는다. 5.1에서는 `isaacsim.*` 확장 이름을 사용한다.
- RTX LiDAR는 `OmniLidar` prim 기반이 표준이다. Camera prim과 JSON `sensorModelConfig` 중심 방식은 5.0부터 deprecated이다.
- 공식 ROS 2 C++ custom OmniGraph 튜토리얼은 Humble 전용이다. Jazzy 실습에서는 Python OGN이나 Generic ROS 2 노드를 사용한다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/index.html)
- [Isaac Sim 5.1.0 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1.0 — Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)
- [ROS 2 Jazzy — Concepts](https://docs.ros.org/en/jazzy/Concepts.html)
