# 125. Franka의 경로 계획과 실제 관절 움직임 연결하기

## 이번에 배우는 것

**MoveIt에서 손가락과 팔의 목표 자세를 계획하고, Execute 후 Isaac Sim의 관절이 실제로 움직이는지 확인합니다.**

RViz의 로봇 미리보기가 움직였다고 시뮬레이터의 로봇까지 움직인 것은 아닙니다. MoveIt은 경로를 계획하고, 컨트롤러는 그 경로를 관절 명령으로 전달합니다. 이번에는 **Plan과 Execute를 나누어 눌러** 이 경계를 확인합니다.

| 구성 | 맡는 일 | 확인할 곳 |
|---|---|---|
| MoveIt `move_group` | 목표 자세까지의 관절 경로 계산 | RViz 계획 미리보기 |
| `ros2_control` | 팔 궤적을 시뮬레이터 연결로 전달 | arm controller 상태 |
| `gripper_to_isaac` | Jazzy의 손가락 action을 관절 명령으로 변환 | gripper action 서버와 실제 손가락 위치 |
| `/isaac_joint_commands` | 관절 이름과 목표값 전달 | ROS 토픽 |
| `/isaac_joint_states` | 실제 시뮬레이션 관절값 반환 | ROS 토픽과 RViz 현재 상태 |
| `/Franka` | 물리적으로 연결된 관절 로봇 | Isaac Sim Viewport |

로컬 실행 스크립트는 없습니다. 공식 Franka MoveIt GUI 예제와 별도의 `isaac_moveit` ROS 패키지를 사용합니다.

## 1. Franka 장면과 MoveIt 실행하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0** 기준이며 지원 GPU와 5.1 로봇 자산이 필요합니다. ROS desktop, 초기화된 `rosdep`, `colcon`을 준비하세요.

저장소 루트에서 시작한 ROS용 Bash에서 다음을 실행합니다. 같은 공식 버전을 이미 빌드했다면 기존 `install/local_setup.bash`를 source하세요.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
sudo apt install ros-jazzy-moveit ros-jazzy-topic-based-ros2-control
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
colcon build
source install/local_setup.bash
ros2 pkg prefix isaac_moveit
ros2 pkg prefix moveit_resources_panda_moveit_config
```

**시뮬레이터용 새 Bash**에서는 시스템 ROS를 source하지 않습니다. Isaac Sim의 Python 3.11용 내부 브리지를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Window > Examples > Robotics Examples > ROS2 > MoveIt > Franka MoveIt**을 엽니다.
2. **Load Sample Scene**을 누릅니다. 새 Stage의 `/Franka`, `/background`, `/ActionGraph`를 확인하세요.
3. 자동 Play가 시작되지 않았다면 Play합니다. 공식 예제의 로봇 위치는 외부 설정과 연결되므로 임의로 옮기지 않습니다.
4. 앞의 ROS용 터미널에서 다음을 실행합니다.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch isaac_moveit isaac_moveit.launch.py ros2_control_hardware_type:=isaac use_sim_time:=true
```

### 실행 결과 확인하기

RViz와 MotionPlanning 패널이 열립니다. 별도의 ROS 터미널에서도 시스템 ROS와 같은 워크스페이스를 source한 뒤 확인하세요.

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1.0/jazzy_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /clock --once
ros2 topic echo /isaac_joint_states --once
ros2 control list_controllers
ros2 action list -t
```

`panda_arm_controller`가 `active`인지, action 목록에 `/panda_hand_controller/gripper_cmd`가 있는지 봅니다. **Jazzy launch는 손가락에 `gripper_to_isaac.py`를 사용하므로 hand controller가 controller 목록에 없어도 정상입니다.** `/isaac_joint_states`의 `name` 배열과 `position` 배열은 같은 인덱스끼리 대응합니다. 회전 관절 위치는 라디안, 직선 운동 관절 위치는 m로 읽습니다. Jazzy 손가락 브리지는 초기 목표를 0.04 m로 두고 발행하므로 이미 손가락이 열린 상태일 수 있습니다.

## 2. 손가락과 팔의 Plan·Execute 비교하기

먼저 작은 동작인 손가락 열기부터 확인합니다.

1. RViz의 **Planning Group**을 `hand`, **Goal State**를 `open`으로 설정합니다.
2. **Plan**을 누릅니다. RViz의 계획 미리보기만 움직이고 Isaac Sim의 실제 손가락은 그대로인지 확인하세요.
3. **Execute**를 누릅니다. 실제 손가락이 벌어지고 상태 토픽의 값이 바뀌는지 봅니다. 이미 open이면 변화가 작을 수 있습니다.
4. 이어서 Planning Group을 `panda_arm`으로 바꾸고 말단 화살표로 가까운 목표를 지정합니다. Plan으로 경로를 확인한 다음 Execute합니다.

팔의 가까운 목표를 확인한 뒤 Goal State에서 **`<random_valid>`**를 선택해 Plan → Execute를 반복할 수 있습니다. 이는 계획 모델에서 유효한 다른 목표 자세를 고르는 방법입니다. 처음부터 큰 무작위 동작으로 시작하지 않고 가까운 목표와 비교하세요.

원문의 `hand/close`에는 일부 환경에서 지연 또는 실패하는 경우가 설명되어 있습니다. close 결과가 이상하면 계획 실패인지 실행 응답 문제인지 나눠 기록하고, 팔의 가까운 목표에서도 같은 문제가 있는지 확인하세요.

### 설정에서 볼 부분

**Window > Graph Editors > Action Graph**에서 `/ActionGraph`를 열면 다음 왕복 경로를 볼 수 있습니다.

```text
Franka 관절 → ROS2 Publish Joint State → /isaac_joint_states
MoveIt 컨트롤러 → /isaac_joint_commands → ROS2 Subscribe Joint State
                                      → Articulation Controller → Franka 관절
```

공식 장면은 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`에 `Gripper=AlternateFinger`, `Mesh=Quality` variant를 선택하고 `Isaac/Environments/Simple_Room/simple_room.usd`를 배경으로 씁니다. Variant는 같은 자산 안에 준비된 구성 선택입니다. 사용자가 별도로 넣은 Franka가 공식 실습과 다른 손가락을 보인다면 이 선택도 비교하세요.

Publisher의 `targetPrim`과 Controller의 `robotPath`는 `/Franka`입니다. Subscriber의 `jointNames`와 `positionCommand` 등이 Controller로 연결됩니다. 이름 배열이 필요한 이유는 “세 번째 숫자”만으로 어느 관절을 움직일지 알 수 없기 때문입니다.

launch의 `ros2_control_hardware_type:=isaac`은 이 토픽 연결을 사용하는 하드웨어 인터페이스를 선택합니다. `use_sim_time:=true`는 외부 계산을 `/clock`에 맞춥니다. 계획에 쓰는 로봇 구조와 관절 한계는 URDF, 계획 그룹과 충돌 제외 정보는 SRDF에서 읽습니다.

### 실행 결과 확인하기

명령을 관찰할 ROS 터미널에서 아래를 먼저 실행하고 RViz에서 Execute를 누르세요.

```bash
ros2 topic echo /isaac_joint_commands
```

Jazzy의 손가락 브리지는 기존 목표도 반복 발행하므로 첫 메시지 하나만으로 이번 Execute를 확인할 수 없습니다. `name` 배열에서 팔 관절인지 손가락 관절인지 구분하고, 목표 변경 전후의 `position`을 비교하세요. 관찰 후 Ctrl+C로 echo를 끝내고 실제 상태를 읽습니다.

```bash
ros2 topic echo /isaac_joint_states --once
```

Jazzy의 손가락 브리지는 요청한 목표를 저장하고 일정 대기 뒤 action 성공을 반환합니다. 이 반환은 실제 관절 도착을 센서값으로 재확인한 결과가 아닙니다. 따라서 `/isaac_joint_states`와 화면을 함께 확인해야 합니다.

명령과 상태는 같은 순간 같은 값일 필요가 없습니다. 명령은 가려는 값이고 상태는 움직이는 도중의 값일 수 있습니다. **Execute 후 실제 관절이 목표를 향해 변하고 도착하는지**를 확인하세요. 실습 종료 시 launch는 Ctrl+C로, Isaac Sim은 창을 닫아 종료합니다.

## 3. 계획과 실행의 차이 정리

| 단계 | 만들어진 것 | 아직 별도로 확인할 것 |
|---|---|---|
| Plan 성공 | 모델과 계획 장면 기준 유효한 경로 | 컨트롤러 전달과 물리 실행 |
| 명령 토픽 수신 | 관절 목표가 ROS 연결을 통과함 | 실제 관절 상태 변화 |
| 상태 변화와 도착 | 시뮬레이션 로봇의 실행 결과 | 추가 장애물까지 포함한 계획 여부 |

`<random_valid>`의 valid도 MoveIt의 **계획 장면 기준**입니다. Isaac Sim에 상자를 하나 추가했다고 그 상자가 MoveIt의 충돌 장면에 자동으로 들어가는 것은 아닙니다. 기본 장면에서 계획과 관절 실행의 연결을 먼저 이해하세요.

## 4. 간단한 확인 실험

같은 팔 시작 자세와 같은 목표를 준비하고 RViz의 **Velocity Scaling만 낮춰** 다시 Plan → Execute해 보세요. 목표·가속도 설정·플래너는 유지합니다.

두 실행 사이에는 launch를 종료하고 Franka 예제를 다시 Load → Play한 뒤 launch를 재시작해 같은 실제 시작 자세를 복원합니다. RViz에서 기록한 동일 목표 pose를 넣고 배율만 바꾸세요.

경로의 공간적 목표는 같지만 이동 시간이 길어지는 경향을 확인할 수 있습니다. 다른 관절 한계나 가속도 제약도 있으므로 배율을 절반으로 했다고 시간을 정확히 두 배로 단정하지 않습니다. Viewport의 최종 모습보다 실행 소요 시간과 관절 상태의 변화 속도를 비교하세요.

## 실행할 때 막히면

- **`isaac_moveit` 또는 설정 패키지가 없음**: submodule을 포함하여 5.1.0 워크스페이스를 빌드했는지, 현재 터미널에 source했는지 확인하세요.
- **Plan은 되지만 로봇이 안 움직임**: `ros2_control_hardware_type:=isaac`, controller의 active 상태, Play와 명령 토픽 연결을 차례로 봅니다.
- **`/isaac_joint_states`가 없음**: 브리지와 `/ActionGraph`의 targetPrim, Domain ID를 확인하세요.
- **가까운 목표도 계획 실패**: `hand`와 `panda_arm` 중 올바른 그룹을 선택했는지, 시작 관절 상태가 갱신되는지 확인하세요.
- **로봇 모델 위치가 어긋남**: 기본 장면을 다시 로드하세요. USD 배치와 launch의 world 기준 설정을 한쪽만 바꾸면 좌표가 맞지 않습니다.

Ubuntu 22.04/Humble을 사용한다면 ROS 경로·패키지·브리지 라이브러리의 `jazzy`를 `humble`로 바꿉니다. Humble launch는 손가락도 `panda_hand_controller`를 spawn하므로 이 경우에는 팔과 손가락 controller가 모두 active인지 확인합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [MoveIt 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_moveit.html)에 대응합니다. [고정 버전 Jazzy launch](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/moveit/isaac_moveit/launch/isaac_moveit.launch.py), [Jazzy 손가락 브리지](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/moveit/isaac_moveit/scripts/gripper_to_isaac.py), [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)와 설치된 `ros_moveit_sample.py`를 대조했습니다.

장면·컨트롤러 패키지는 외부 의존성입니다. 이 개정은 GUI 절차와 실제 관절 실행의 판정 기준을 정리한 것이며 GPU·DDS·MoveIt 실행을 수행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
