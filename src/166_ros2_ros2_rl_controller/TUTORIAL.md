# 166. ROS 2를 거쳐 H1의 관절 명령을 돌려받기

## 이번에 배우는 것

**H1의 IMU·관절 상태를 ROS 2로 보내고, 외부 정책이 계산한 관절 목표가 시뮬레이터로 돌아오는 과정을 확인합니다.**

정책이 시뮬레이터 밖에서 실행되면 상태를 전달하는 통신도 제어의 일부가 됩니다. 센서 메시지가 보이더라도 서로 시각이 맞지 않으면 정책이 계산을 시작하지 못할 수 있습니다. 이번에는 완성된 H1 장면에서 왕복 통신을 확인한 뒤 그래프의 데이터 연결을 읽습니다.

| 구성 요소 | 실행 장소 | 역할 |
|---|---|---|
| H1 USD·물리·ROS 그래프 | Isaac Sim GUI | 센서 상태 발행, 관절 목표 적용 |
| `h1_fullbody_controller` | 외부 ROS Python | 동기화된 상태로 정책 추론 |
| `/cmd_vel` | ROS 명령 터미널 | 원하는 전진·회전 속도 전달 |
| `inspect_stage.py` | Script Editor | 열린 Stage의 물리·IMU·토픽 설정 확인 |

이 폴더에는 정책 노드나 standalone `run.py`가 없습니다. 로컬 검사기는 읽기 전용이며 정책은 공식 ROS workspace에서 준비합니다.

## 1. 완성 장면과 ROS 정책 실행하기

기본 환경은 **Ubuntu 24.04 + ROS 2 Jazzy + Isaac Sim 5.1**입니다. RTX GPU, 5.1 H1 sample assets, `isaacsim.ros2.bridge`가 필요합니다. ROS 설치가 없다면 [Isaac Sim 5.1 ROS 설치 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)를 먼저 따라 준비하세요. Ubuntu 22.04에서는 Humble을 사용하고 아래 `jazzy`, `jazzy_ws`를 각각 `humble`, `humble_ws`로 바꿉니다.

Bash 터미널에서 진행합니다. GUI를 켤 터미널 A와 ROS를 실행할 B·C 모두 같은 ROS 환경과 domain을 설정하세요.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

터미널 A에서 `~/isaacsim/isaac-sim.sh`를 실행합니다. **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화하고 Content Browser의 5.1 Assets에서 다음 완성 장면을 여세요. 아직 Play하지 않습니다.

```text
/Isaac/Samples/ROS2/Scenario/h1_ros_locomotion_policy_tutorial.usd
```

터미널 B는 저장소 루트에서 시작해 외부 패키지를 준비합니다. `colcon`, ROS 메시지·`message_filters`, 외부 Python의 `torch`, `numpy`, `yaml`이 필요합니다. 이 Python 환경은 Isaac Sim 내부 Python과 별개입니다.

```bash
python3 -c "import torch, numpy, yaml; print(torch.__version__)"
mkdir -p src/166_ros2_ros2_rl_controller/output
git clone --branch IsaacSim-5.1.0 --depth 1 https://github.com/isaac-sim/IsaacSim-ros_workspaces.git src/166_ros2_ros2_rl_controller/output/ros_workspaces
cd src/166_ros2_ros2_rl_controller/output/ros_workspaces/jazzy_ws
colcon build --packages-up-to h1_fullbody_controller
source install/setup.bash
ros2 pkg prefix h1_fullbody_controller
```

이미 같은 버전 workspace를 준비했다면 그 workspace의 `install/setup.bash`를 사용하세요. 정책 `policy/h1_policy.pt`와 환경 YAML은 upstream 패키지에 포함되어 있습니다. 버전을 고정하는 이유는 최신 main의 실행 구조와 섞이지 않게 하기 위해서입니다.

### 설정에서 볼 부분

Play 전에 **Window > Script Editor**에서 이 폴더의 `inspect_stage.py` 전체를 실행합니다.

| 검사 출력 | 완성 장면에서 확인할 값 |
|---|---|
| PhysicsScene | `Hz=200`, `gpu_dynamics=False`, `broadphase=MBP` |
| IMU 경로 | H1 pelvis 아래의 IMU |
| ROS 노드 | `/imu`, `/joint_states`, `/joint_command`, `/clock` |
| 그래프 pipeline | 물리 step에 맞춘 실행 구성 |

검사기는 설정을 고치지 않습니다. 다른 값이 나오면 현재 열린 Scene과 실제 Prim을 확인하세요. 완성 장면을 사용하는 이유는 로봇 관절과 센서·그래프가 맞춰진 출발점을 얻기 위해서입니다.

터미널 B에서 정책을 먼저 실행하고, 그다음 GUI의 **Play**를 누릅니다.

```bash
ros2 launch h1_fullbody_controller h1_fullbody_controller.launch.py
```

정책보다 물리를 먼저 시작하면 로봇이 지지 명령을 받기 전에 넘어질 수 있습니다. 종료할 때는 GUI를 Pause하고 ROS 프로세스를 Ctrl+C로 종료하세요. GUI 창은 직접 닫을 때까지 남습니다.

### 실행 결과 확인하기

같은 ROS 환경을 설정한 터미널 C에서 실제 메시지를 읽습니다.

```bash
ros2 topic echo /imu --once
ros2 topic echo /joint_states --once
ros2 topic echo /joint_command --once
ros2 topic echo /clock --once
ros2 topic hz /joint_command
```

마지막 빈도 관찰은 Ctrl+C로 끝냅니다. 토픽 목록에 이름이 있다는 것과 메시지가 실제로 전달된다는 것은 다릅니다. 상태뿐 아니라 **돌아오는 `/joint_command`**를 확인하세요. 이름 배열과 위치 배열이 대응하는지, GUI에서 몸통이 지지되는지도 함께 봅니다.

작은 전진 명령은 다음처럼 보낼 수 있습니다. 잠시 관찰한 뒤 Ctrl+C로 발행을 끝내고 정지 명령을 보냅니다.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: 0.0}}'
```

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

발행 프로세스를 종료하는 것만으로 마지막 속도 명령이 자동으로 0이 되지는 않습니다. 정지 메시지 후 자세와 이동 감소를 확인하세요.

키보드로 비교하려면 `teleop_twist_keyboard`가 설치된 같은 ROS 환경에서 다음을 실행할 수 있습니다. 앞의 자동 발행기는 먼저 종료해 두 입력이 경쟁하지 않게 하세요.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

작은 속도에서 `i` 전진, `u/o` 전진 회전, `j/l` 제자리 회전, `k` 정지를 비교합니다. 터미널에 표시되는 속도 조절 키로 선속도를 약 0.2 m/s부터 맞추세요. 이 H1 flat 정책의 후진·옆걸음을 성공 기준으로 삼지는 않습니다.

## 2. 그래프와 정책의 시간 연결 읽기

### 코드에서 볼 부분

고정된 5.1.0 ROS 패키지는 두 센서 메시지의 시간표시를 맞춘 콜백에서 정책을 진행합니다.

```python
self.sync = TimeSynchronizer(subscribers, queue_size)
self.sync.registerCallback(self._tick)
```

여기서 subscribers는 `/joint_states`와 `/imu`입니다. 두 메시지가 모두 보여도 timestamp가 맞지 않으면 `_tick`이 실행되지 않을 수 있습니다. launch의 `publish_period_ms` 이름만 보고 독립적인 5 ms timer가 정책을 실행한다고 해석하지 마세요. 해당 버전에서는 동기화된 메시지 콜백이 실제 실행 경로입니다.

정책은 동기 콜백 네 번마다 한 번 계산하고, 관절 명령은 콜백마다 발행합니다. 센서가 시뮬레이션 시간 기준 200 Hz로 동기 전달되면 추론은 약 50 Hz입니다. `ros2 topic hz`는 수신 환경과 실행 속도의 영향을 받으므로 실시간 측정값이 항상 200 또는 50으로 고정되지는 않습니다.

### 설정에서 볼 부분

완성 장면을 이해한 뒤 `/Isaac/Samples/Rigging/H1/h1_rigged.usd`의 복사본에서 그래프를 재구성할 수 있습니다. pelvis 아래에 IMU를 만들고, `/Graph` 아래 세 Action Graph를 둡니다. 그래프는 `pipelineStageOnDemand`와 **On Physics Step**을 사용합니다.

| 그래프 | 실행·데이터 연결 | 중요한 설정 |
|---|---|---|
| IMU | Physics Step → Read IMU → Publish IMU | pelvis IMU, Read Gravity=False, topic `/imu` |
| Joint | Physics Step → Publish/Subscribe Joint State 및 Articulation Controller | `/joint_states`, `/joint_command`, 실제 H1 target Prim |
| Clock | Physics Step → Publish Clock | simulationTime을 `/clock`에 전달 |

직접 구성할 때는 다음 순서로 연결하세요.

1. `/h1/pelvis`를 선택해 **Create > Isaac > Sensors > Imu Sensor**로 `/h1/pelvis/Imu_Sensor`를 만듭니다. **Create > Scope**로 `/Graph`를 만들고 그 아래 **Create > Visual Scripting > ActionGraph**로 세 그래프를 추가합니다. 각 그래프의 `pipelineStage`를 `pipelineStageOnDemand`로 맞춥니다.
2. IMU 그래프에서 **On Physics Step → Isaac Read IMU → ROS2 Publish IMU**의 실행 핀을 잇습니다. Read IMU의 `linearAcceleration`, `angularVelocity`, `orientation`을 publisher의 대응 입력에 연결합니다. `imuPrim`은 pelvis 센서, `Read Gravity=False`, `frameId=pelvis`, `topicName=/imu`로 지정합니다.
3. Joint 그래프의 Physics Step 출력을 publisher·subscriber·Articulation Controller의 실행 입력에 연결합니다. publisher와 controller의 `targetPrim`은 실제 articulation인 `/h1`, 토픽은 각각 `/joint_states`와 `/joint_command`입니다.
4. Clock 그래프에서 Physics Step을 **ROS2 Publish Clock**의 실행 입력에 연결하고 토픽을 `/clock`으로 맞춥니다.
5. 로봇을 새 `output/h1_ros_01.usd`로 저장합니다. 새 Stage에 창고와 이 로봇을 참조하고 로봇 초기 Z를 1.0 m로 둡니다. Physics Scene을 추가해 **Time Steps Per Second=200**, **Enable GPU Dynamics=False**, **Broadphase Type=MBP**로 맞춘 뒤 앞 절의 정책 실행 순서를 따릅니다.

세 그래프의 ROS 노드에는 Context와 QoS를 연결합니다. IMU·Joint·Clock의 timeStamp는 같은 **Isaac Read Simulation Time** 기준으로 맞추고 `resetOnStop=True`를 사용합니다. Joint subscriber의 `jointNames`, `positionCommand`, `velocityCommand`, `effortCommand`를 controller의 대응 입력에 연결하세요. 실행 선은 **언제 계산하는지**, 데이터 선은 **무엇을 넘기는지**를 정합니다.

정책은 IMU 방향으로 몸체에서 본 중력 방향을 계산하고, 가속도를 적분해 선속도를 추정합니다. 관절은 메시지 도착 순서 대신 이름을 찾아 정책 순서로 재배열합니다. 기본 자세와 gain도 학습 조건에 맞아야 하므로 처음에는 준비된 rig를 사용하세요. 관절 설정을 바꾸면 YAML의 rad와 GUI 각도 단위도 구별해야 합니다. 예를 들어 기본 무릎 위치 0.79 rad는 약 45.26°이고 발목 -0.52 rad는 약 -29.79°입니다. 두 숫자를 같은 단위로 입력하면 기준 자세부터 달라집니다.

## 3. 왕복 제어의 확인 지점 정리

```text
H1 물리 상태
    → 같은 시각의 IMU·JointState 발행
    → 외부 노드의 TimeSynchronizer
    → 관측 69개 → 정책 행동 19개
    → 기준 관절 위치 + 0.5 × 행동
    → /joint_command → Articulation Controller
    → 다음 물리 상태
```

통신 확인은 메시지 수신으로, 제어 확인은 몸체 자세와 이동으로 합니다. 두 센서가 존재하지만 회신이 없으면 동기화를, 회신이 있지만 로봇이 무너지면 관절 대응과 물리 설정을 먼저 조사할 수 있습니다.

## 4. 간단한 확인 실험

같은 초기 Scene에서 전진 명령의 `linear.x`만 0.2에서 0.3으로 바꿔 보세요. 각각 같은 시뮬레이션 시간 동안 관찰한 뒤 0 명령을 보냅니다.

- `/joint_command`가 계속 돌아오는지 확인합니다.
- 로봇이 몸통을 지지하며 더 빠르게 이동하는지 비교합니다.
- 물리 주기와 관절 gain을 함께 바꾸지 않습니다. 후진·옆걸음은 이 H1 flat 정책의 성공 기준으로 사용하지 않습니다.

## 실행할 때 막히면

- **ROS 패키지를 못 찾음**: 빌드한 workspace의 `install/setup.bash`를 해당 터미널에서 source하세요.
- **torch·yaml import 실패**: 외부 ROS Python 환경을 확인하세요. Isaac Sim 내부에 설치되어 있다는 사실만으로 외부 프로세스에서도 사용할 수 있는 것은 아닙니다.
- **센서는 보이는데 joint_command가 없음**: IMU·JointState의 timestamp, QoS와 실제 동기 메시지 도착을 확인하세요.
- **아무 토픽도 수신하지 못함**: GUI Play, ROS bridge 활성화, 두 프로세스의 `ROS_DOMAIN_ID`와 RMW를 확인하세요.
- **로봇이 시작하자마자 넘어짐**: 정책을 먼저 켰는지, pelvis IMU와 200 Hz 물리, 준비된 rig를 사용했는지 확인하세요.
- **정지해도 약간 움직임**: 0 명령을 실제 발행했는지 먼저 확인합니다. 작은 자세 보정과 계속된 전진 명령을 구별하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Running a Reinforcement Learning Policy through ROS 2 and Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html)에 대응합니다. 외부 실행 구조는 [5.1.0 Jazzy H1 controller 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/IsaacSim-5.1.0/jazzy_ws/src/humanoid_locomotion_policy_example/h1_fullbody_controller/scripts/h1_fullbody_controller.py)를 기준으로 설명했습니다.

`tutorial.json`은 `not_run`입니다. 로컬 검사기는 Stage 설정만 읽으며 ROS 메시지 수신이나 실제 보행을 검증하지 않습니다. GUI·정책·DDS 통신을 함께 실행해 위 관찰 항목을 확인해야 합니다.
