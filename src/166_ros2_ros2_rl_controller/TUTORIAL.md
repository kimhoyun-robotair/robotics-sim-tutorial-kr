# 166. H1 강화학습 정책을 ROS 2로 실행하기

권장 학습 순서 **166** · 병렬 환경과 학습 정책 활용 · 출처 ID `t004`

예상 결과는 H1이 `/imu`, `/joint_states`, `/clock`을 내보내고, 별도 ROS 정책 프로세스가 `/joint_command`로 자세 목표를 되돌려 주어 서 있거나 앞으로 걷는 것이다. 원문의 완성 asset과 GUI 그래프를 사용하는 실습이며 학습된 정책을 재학습하거나 이 폴더에 복제한 구현이라고 주장하지 않는다.

이 패키지는 이미 실행한 Isaac Sim GUI에서 실습합니다. 로컬 검사·설정 도구가 GUI 수명을 제한하지 않으며, 사용자가 창을 직접 닫을 때까지 유지됩니다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. Standalone `run.py`는 이 확장을 직접 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## 필요한 정책과 로봇을 이 실습 안에서 준비하기

Isaac 5.1 asset pack에서 다음 세 asset을 사용한다. Content Browser의 **Isaac Sim** 루트를 기준으로 찾는다.

| 용도 | asset 경로 |
|---|---|
| 물리 gain/자세가 준비된 로봇 | `Samples/Rigging/H1/h1_rigged.usd` |
| ROS 그래프가 구성된 로봇 | `Samples/ROS2/Robots/h1_ROS.usd` |
| 로봇·창고·200Hz 설정이 완성된 장면 | `Samples/ROS2/Scenario/h1_ros_locomotion_policy_tutorial.usd` |

처음 실행은 완성 장면으로 한다. 따라서 별도 로컬 rigging 튜토리얼을 이수할 필요가 없다. 이후 아래의 재구성 절차로 노드를 하나씩 만든다. 외부 ROS Python에는 PyTorch와 PyYAML이 필요하고 `python3 -c "import torch, yaml; print(torch.__version__)"`로 확인한다. Isaac Sim 내부의 torch와 외부 정책 프로세스의 torch는 별도 환경이다.

ROS workspace는 **IsaacSim-5.1.0** 버전으로 준비한다. 최신 main은 launch 파일 이름/구성이 다를 수 있다.

```bash
git clone --branch IsaacSim-5.1.0 --depth 1 https://github.com/isaac-sim/IsaacSim-ros_workspaces.git ros_workspaces
cd "ros_workspaces/${ROS_DISTRO}_ws"
colcon build --packages-up-to h1_fullbody_controller
source install/setup.bash
ros2 pkg prefix h1_fullbody_controller
```

`colcon`, message_filters 등 package.xml의 빌드·런타임 의존성이 준비되어 있어야 한다. 의존성이 없다면 선택한 ROS 배포판에서 준비하고 다시 build한다. 정책 파일 `policy/h1_policy.pt`와 환경 정의 `policy/h1_env.yaml`은 이 upstream ROS 패키지에 포함된다. 패키지 획득·빌드는 실제 외부 의존성을 준비하는 단계이며 이 튜토리얼 폴더 밖 공통 학습 모듈에 의존하지 않는다.

## 먼저 완성 장면에서 실행하기

1. Isaac Sim에서 `Samples/ROS2/Scenario/h1_ros_locomotion_policy_tutorial.usd`를 연다. 아직 Play하지 않는다.
2. **Window > Script Editor**에서 `inspect_stage.py`를 실행한다. PhysicsScene의 200Hz, GPU dynamics=False, broadphase=MBP, pelvis 아래 IMU, ROS 그래프와 실제 topic 이름을 확인한다. 이 스크립트는 결과를 읽기만 하며 잘못된 rig를 정상으로 꾸미지 않는다.
3. 위 ROS workspace를 source한 터미널에서 정책을 먼저 켠다.

   ```bash
   ros2 launch h1_fullbody_controller h1_fullbody_controller.launch.py
   ```

4. 그 다음 Isaac Sim의 Play를 누른다. 명령이 없으면 정책이 서 있는 자세를 유지한다. 정책을 켜기 전에 물리만 시작하면 로봇이 넘어질 수 있다.
5. 별도 ROS 터미널에서 실제 연결을 관찰한다.

   ```bash
   ros2 topic echo /imu --once
   ros2 topic echo /joint_states --once
   ros2 topic echo /joint_command --once
   ros2 topic hz /clock
   ros2 topic hz /joint_command
   ```

6. `ros2 run teleop_twist_keyboard teleop_twist_keyboard`를 실행한다. 작은 속도로 `i` 전진, `u/o` 전진 회전, `j/l` 좌우 회전, `k` 정지를 시험한다. 이 flat H1 정책은 후진과 옆걸음을 지원하지 않으며 linear/angular 속도를 0.75보다 높이면 실패할 수 있다. 처음에는 0.2m/s 정도로 시작한다.

## 로봇과 그래프를 직접 재구성하기

1. `h1_rigged.usd`를 새 실습 Stage에 연다. `/h1/pelvis`를 오른쪽 클릭하고 **Create > Isaac > Sensors > Imu Sensor**로 `/h1/pelvis/Imu_Sensor`를 만든다. torso의 IMU를 대신 쓰면 pelvis frame 변환이 추가로 필요하다.
2. **Create > Scope**로 `/Graph`를 만든다. 그 아래 **Create > Visual Scripting > ActionGraph**를 세 개 만들고 `ROS_Imu`, `ROS_Joint_States`, `ROS_Clock`으로 부른다. 각 그래프 Property의 `pipelineStage`를 **pipelineStageOnDemand**로 설정한다. **On Physics Step**이 물리 step마다 이를 실행한다.
3. IMU 그래프에 On Physics Step, ROS2 Context, ROS2 QoS Profile, Isaac Read IMU, Isaac Read Simulation Time, ROS2 Publish IMU를 둔다. Physics Step의 실행 출력을 Read IMU.execIn에 연결하고 Read IMU.execOut을 Publish IMU.execIn에 연결한다. Read IMU의 linearAcceleration/angularVelocity/orientation을 publisher의 같은 입력에 연결한다. Time.simulationTime은 timeStamp, Context.context는 context, QoS.qosProfile은 qosProfile에 연결한다. imuPrim=`/h1/pelvis/Imu_Sensor`, Read Gravity=False, topicName=`/imu`, frameId=`pelvis`, Time.resetOnStop=True다.
4. Joint 그래프에는 On Physics Step, Context, QoS, Time, ROS2 Publish Joint State, ROS2 Subscribe Joint State, Articulation Controller를 넣는다. Physics Step은 발행/수신/제어 execIn에, Context와 QoS는 두 ROS 노드에, Time은 publisher.timeStamp에 연결한다. publisher.targetPrim=`/h1`, publisher.topicName=`/joint_states`, subscriber.topicName=`/joint_command`, controller.targetPrim=`/h1`이다. Subscriber의 jointNames/positionCommand/velocityCommand/effortCommand를 controller의 같은 입력에 연결한다. resetOnStop=True로 맞춘다.
5. Clock 그래프에서는 Physics Step → ROS2 Publish Clock.execIn, Time.simulationTime → timeStamp, Context → context, QoS → qosProfile을 연결한다. topicName=`/clock`, resetOnStop=True다.
6. 로봇을 `output/h1_ros_01.usd`처럼 새 이름으로 저장한다. 새 Stage에 **Environments > Simple_Warehouse > warehouse.usd**를 reference로 놓고 이 로봇을 추가한다. 로봇 Z=1.0으로 둔다.
7. **Create > Physics > Physics Scene**을 추가한다. **Time Steps Per Second=200**, **Enable GPU Dynamics=False**, **Broadphase Type=MBP**로 설정한다. Physics의 dt=0.005초와 정책의 5ms ROS timer가 맞아야 한다. 저장하고 앞의 순서로 정책을 먼저 실행한다.

## 정책 입력과 rig를 이해하기

정책 관측은 pelvis 좌표계 선속도·각속도·중력 방향, 원하는 x/y/z회전 속도, 기본 자세로부터의 joint position 차이, joint velocity, 이전 action 순서로 구성된다. IMU는 속도를 직접 주는 센서가 아니므로 외부 노드가 orientation으로 gravity 방향을 계산하고 가속도 등을 처리한다. 관절 순서와 기본 자세도 학습 당시와 일치해야 한다. 출력은 joint 위치 목표이며 공식 외부 노드는 200Hz timer에서 4회마다 정책을 계산한다(정책 계산 주기 약 50Hz).

[5.1 H1 환경 YAML](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Policies/H1_Policies/h1_env.yaml)의 기본 자세는 hip_pitch=-0.28rad, knee=0.79rad, ankle=-0.52rad, shoulder_pitch=0.28rad, elbow=0.52rad이며 나머지 정의된 축은 0이다. USD GUI에서는 약 -16.04°, 45.26°, -29.79°, 16.04°, 29.79°로 입력한다. YAML은 rad이고 GUI는 degree라는 차이를 놓치지 않는다.

rig를 수정한다면 YAML의 gain도 비교한다. hip yaw/roll stiffness=150, hip pitch/knee/torso=200, damping=5; ankle stiffness=20, damping=4; arm stiffness=40, damping=10이다. legs/arms effort limit=300, ankle=100이다. 이미 제공된 `h1_rigged.usd`를 사용하는 이유는 이 관절 구성과 자세를 같은 조건으로 시작하기 위해서다. YAML에 남아 있는 학습용 GPU/4096환경 설정을 이 단일 로봇 실습의 CPU/200Hz 설정으로 그대로 덮어쓰지 않는다.

## 한 가지 바꾸기·문제 해결

전진 속도만 0.2에서 0.3으로 바꾸어 추종을 본다. 후진·옆걸음으로 정책 능력을 추정하지 않는다. 넘어지면 정책 시작 순서, joint 이름·기본 자세, 물리200Hz, pelvis IMU와 topic 타임스탬프를 차례로 확인한다. PyTorch/yaml import 실패는 외부 ROS Python 환경 문제다. 정지 중 약간의 drift는 원문에서 예상한 현상이다. `/joint_command`의 실제 수신과 안정된 몸체 자세를 함께 관찰해야 성공이다.

추가 소스: [5.1.0에 고정한 H1 ROS 패키지](https://github.com/isaac-sim/IsaacSim-ros_workspaces/tree/50de00358f220d790d17050c6368cfe9a9cb9f51/humble_ws/src/humanoid_locomotion_policy_example/h1_fullbody_controller). 이 패키지가 실제 관측 구성과 신경망 추론을 담당한다.

## 출처와 검증 범위

- [공식 5.1 정책 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html#about-the-h1-flat-terrain-locomotion-policy)
- [공식 5.1 IMU 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html#create-imu-publisher-node)
- [공식 5.1 joint 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html#create-joint-state-publisher-and-subscriber-nodes)
- [공식 5.1 환경·시계](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html#publish-ros-clock-and-set-up-environment)
- [공식 5.1 실행](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html#run-ros-2-policy)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
