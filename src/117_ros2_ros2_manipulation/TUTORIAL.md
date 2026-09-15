# 117. ROS 관절 명령을 보내고 실제 Franka 상태 읽기

## 이번에 배우는 것

**Franka의 관절 상태를 ROS에서 읽고, 한 관절에 목표 위치를 보내 물리 로봇의 응답을 확인합니다.**

관절 제어에는 두 방향이 있습니다. 시뮬레이터는 현재 상태를 밖으로 보내고, 외부 프로그램은 원하는 목표를 안으로 보냅니다. 이번 실습에서는 같은 JointState 메시지 타입을 쓰더라도 **상태와 명령의 의미가 다르다**는 점을 살펴봅니다.

| 구성 | 방향 | 역할 |
|---|---|---|
| `/joint_states` | Isaac Sim → ROS | 실제 관절 상태 발행 |
| `/joint_command` | ROS → Isaac Sim | 원하는 관절 위치 전달 |
| `run.py` | 시뮬레이터 | Franka·발행기·수신기·제어기 구성 |
| `send_command.py` | 외부 ROS Python | 한 관절 목표를 일정 시간 반복 송신 |

기본 목표는 `panda_joint1`의 0.3 rad입니다. `run.py`가 스스로 이 목표를 만드는 것은 아니며 송신기를 따로 실행해야 합니다.

## 1. Franka 실행하고 현재 상태 읽기

Isaac Sim 5.1, 지원 NVIDIA GPU, 공식 Franka Panda 자산과 Ubuntu 24.04의 ROS 2 Jazzy를 준비합니다. 저장소 루트의 Bash에서 실행하세요. Ubuntu 22.04/Humble은 아래 `jazzy` 값과 경로를 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 내부 브리지를 사용합니다. 설치 위치가 다르면 `ISAAC_SIM`을 수정하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/117_ros2_ros2_manipulation/run.py
```

코드는 5.1 자산의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 `/panda`에 참조로 불러옵니다. 자산 서버 또는 로컬 asset pack에 접근할 수 있어야 합니다. GUI는 창을 닫을 때까지 실행되며 `--steps 1200`은 1200스텝 뒤 종료합니다. `--headless`만 지정하면 3600스텝을 사용합니다.

터미널 B에서 시스템 ROS를 준비합니다. `rclpy`와 `sensor_msgs`가 필요합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /joint_states --once
```

### 실행 결과 확인하기

콘솔의 `actual_joint_names`와 메시지의 `name` 배열을 비교하세요. `panda_joint1`을 찾고 **같은 인덱스**의 `position`을 읽습니다. 관절이 항상 첫 번째에 있다고 추측하지 않습니다.

| JointState 항목 | 이번 Franka 회전관절에서의 의미 |
|---|---|
| `name[i]` | i번째 값이 어느 관절인지 나타내는 이름 |
| `position[i]` | 관절 각도(rad) |
| `velocity[i]` | 관절 각속도(rad/s) |
| `effort[i]` | 관절 토크(N·m) |
| `header.stamp` | 상태에 붙인 시뮬레이션 시각 |

위 단위는 이번에 움직이는 팔의 회전관절 기준입니다. Franka 손가락처럼 직선으로 움직이는 관절은 위치 m, 속도 m/s, 힘 N을 사용합니다. [Jazzy JointState 정의](https://raw.githubusercontent.com/ros2/common_interfaces/jazzy/sensor_msgs/msg/JointState.msg)에서 각 배열은 이름 배열과 길이가 같거나 비어 있을 수 있으므로, 값이 없는 배열을 임의의 0 측정값으로 읽지 마세요.

콘솔의 `joint_positions_rad`는 120스텝 간격으로 출력됩니다. `/joint_states`는 playback tick에 연결되어 있으므로 콘솔과 ROS 메시지의 출력 빈도는 다릅니다.

## 2. 위치 명령을 보내고 제어 경로 읽기

터미널 B에서 다음 명령을 실행합니다.

```bash
python3 src/117_ros2_ros2_manipulation/send_command.py --joint panda_joint1 --position 0.3 --seconds 10
```

0.3 rad는 약 17.2°입니다. 같은 환경을 설정한 다른 ROS 터미널에서 `ros2 topic echo /joint_states`를 실행하고 첫 관절의 상태가 목표로 접근하는지 관찰하세요. 지속 관찰은 Ctrl+C로 종료합니다.

### 코드에서 볼 부분

송신기는 JointState에서 사용할 이름과 위치만 채웁니다.

```python
message.name = [args.joint]
message.position = [args.position]
pub.publish(message)
```

`velocity`와 `effort`를 비워 두어 이번 명령이 위치 제어임을 분명히 합니다. 송신 시간은 `time.monotonic()`으로 제한하며 루프의 `spin_once(..., timeout_sec=0.1)` 사이에 메시지를 반복 발행합니다. 이 주기는 외부 ROS의 실제 시간 기준이며 시뮬레이션의 1/60초 물리 간격과 같지 않습니다.

`run.py`의 `/JointGraph`는 받은 배열을 다음처럼 연결합니다.

```text
/joint_command
    → ROS2 Subscribe Joint State
    → jointNames·positionCommand·velocityCommand·effortCommand
    → Articulation Controller(robotPath=/panda)
    → 물리 관절
    → ROS2 Publish Joint State(targetPrim=/panda)
    → /joint_states
```

`targetPrim`과 `robotPath`는 Stage의 로봇 주소입니다. 메시지의 `name`은 그 articulation 안의 관절 이름입니다. 주소와 관절 이름을 서로 바꿔 넣으면 제어 대상을 찾을 수 없습니다.

### GUI에서 연결 확인하기

**Window > Graph Editors > Action Graph**에서 `/JointGraph`를 엽니다. Tick의 실행 출력은 Publish·Subscribe·Actuator에, Context는 두 ROS 노드에 연결되어 있습니다. Simulation Time은 상태 publisher의 `timeStamp`로 들어갑니다. 수신기에서 나오는 네 배열이 Actuator의 같은 입력으로 이어지는지 확인하세요.

새 GUI 장면에서 같은 구조를 만들 때는 Franka를 먼저 불러온 뒤 **Tools > Robotics > ROS 2 OmniGraphs > JointStates**에서 articulation prim, Publisher·Subscriber·Articulation Controller를 지정할 수 있습니다. Python으로 구성할 때는 이미 열린 앱에서 `og.Controller.edit()`로 노드·값·연결을 만듭니다. `run.py` 전체에는 `SimulationApp`과 물리 루프가 있으므로 Script Editor에 그대로 붙여 넣지 않습니다.

Script Editor에서 직접 재구성하려면 `/panda`가 있는 새 Franka 장면에서 `import omni.graph.core as og`와 `keys = og.Controller.Keys`를 먼저 실행합니다. 이어서 `run.py`의 `nodes`, `links`, `values`, `og.Controller.edit(...)` 부분만 사용하세요. 이미 `/JointGraph`가 있으면 다른 그래프 경로를 지정합니다. 이 부분은 로봇을 불러오지 않으므로 모델 준비를 생략할 수 없습니다.

### 실행 결과 확인하기

관절이 회전하고 `/joint_states`의 해당 `position`이 0.3 rad 쪽으로 접근하는지 함께 봅니다. **수신된 명령값을 echo한 것만으로 물리 제어까지 성공한 것은 아닙니다.** 상태 publisher는 실제 articulation을 읽으므로 명령과 상태를 따로 비교할 수 있습니다.

송신기가 끝나도 0 rad로 돌아오지 않습니다. 복귀시키려면 목표를 따로 보냅니다.

```bash
python3 src/117_ros2_ros2_manipulation/send_command.py --joint panda_joint1 --position 0.0 --seconds 5
```

## 3. 명령과 상태의 차이 정리

```text
목표 q* = 0.3 rad
    → 위치 drive가 목표에 접근하도록 토크 생성
    → 물리 계산 후 실제 위치 q가 변함
    → 상태 메시지에서 q를 관찰
```

명령은 순간이동 좌표가 아닙니다. 관절 drive의 stiffness·damping, 로봇의 관성 등에 따라 목표로 접근합니다. 위치 제어와 속도 제어는 drive 설정도 다릅니다. 속도 drive는 일반적으로 stiffness=0과 damping>0을 사용합니다. 이번 송신기는 위치만 채우므로 여러 제어 모드가 한 관절에 충돌하지 않게 구성되어 있습니다.

기본 그래프에는 `/clock`과 TF가 없습니다. 송신기는 벽시계로 동작하므로 `/clock` 없이도 끝나지만, 이후 `use_sim_time=true`인 외부 제어기를 추가한다면 Clock 발행도 준비해야 합니다.

## 4. 간단한 확인 실험

같은 관절·송신 시간을 유지하고 **`--position`만 0.3에서 0.1로 바꿔 보세요.**

```bash
python3 src/117_ros2_ros2_manipulation/send_command.py --joint panda_joint1 --position 0.1 --seconds 10
```

목표 각도는 약 5.7°입니다. 원점에서 시작했다면 더 작은 회전이, 이전 목표 0.3에 있었다면 0.1 쪽으로 되돌아가는 움직임이 예상됩니다. 실행 전 현재 위치를 읽어야 같은 명령의 움직임을 올바르게 예상할 수 있습니다.

## 실행할 때 막히면

- **명령은 보이지만 로봇이 움직이지 않음**: Play 상태, Actuator의 `/panda` 대상, jointNames와 positionCommand 연결을 확인하세요.
- **관절을 찾지 못함**: 콘솔과 `/joint_states.name`의 실제 이름을 사용하세요. 메시지에 USD 전체 경로를 넣지 않습니다.
- **원위치로 돌아오지 않음**: 송신기 종료는 복귀 명령이 아닙니다. 위치 0을 명시적으로 보내세요.
- **자산 로딩 오류**: 기대하는 Franka 5.1 경로와 asset root 접근을 확인하세요. ROS 연결과 모델 준비는 별도 단계입니다.
- **headless 검사 중 외부 송신이 늦음**: DDS 발견과 로딩에 시간이 필요합니다. 관찰에는 `--steps` 없는 GUI 또는 충분한 단계 수를 사용하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS2 Joint Control: Extension Python Scripting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html)에 대응합니다. 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 그래프 구성에 독립 실행 진입점과 한 관절용 ROS 송신기를 더했습니다. GUI·Script Editor의 같은 연결 원리를 설명하지만 로컬 `run.py`는 standalone 파일입니다. `tutorial.json`은 `verification: not_run`이며 실제 DDS 수신·관절 운동을 이번 개정에서 실측하지 않았습니다.
