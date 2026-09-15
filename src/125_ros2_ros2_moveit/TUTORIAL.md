# 125. MoveIt 2 — Franka의 계획과 실제 관절 실행을 구분하기

권장 학습 순서 **125** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t026`

공식 `Franka MoveIt` 장면과 `isaac_moveit` ROS launch를 사용하는 완전한 GUI 실습이다. 손가락 열기와 팔 목표 자세를 계획하고 Isaac Sim에서 실제로 실행한다. USD/ROS 패키지를 이 폴더에 재배포하지 않으며 필요한 준비를 여기서 모두 설명한다.

## 이 실습의 의도

MoveIt의 경로 계획과 ros2_control을 통한 실제 관절 실행이 별도 단계임을 배우는 실습이다. `/Franka`는 `/isaac_joint_states`로 현재 상태를 보내고 `/isaac_joint_commands`로 받은 명령을 Articulation Controller에 적용한다. 로컬 실행기는 없으므로 공식 GUI 장면과 외부 `isaac_moveit` launch를 준비하고, 손가락 `hand/open`과 팔 `panda_arm` 목표를 직접 Plan→Execute한다.

## 실행 후 확인할 것

- **시뮬레이터 연결:** Stage에 `/Franka`와 `/ActionGraph`가 있고 Play 중 `/isaac_joint_states`와 `/clock`을 실제로 수신하는지 확인한다. `ros2 control list_controllers`에서는 arm/hand controller가 active여야 한다.
- **계획 단계:** RViz의 `hand/open` 또는 `panda_arm`에서 Plan을 누르면 경로 미리보기가 생성되는지 본다. 이때 Isaac Sim의 실제 로봇이 그대로 있는 것은 정상이다.
- **실행 단계:** Execute 후 `/isaac_joint_commands`가 전달되고 `/isaac_joint_states`가 변하며 Isaac Sim 손가락 또는 팔이 목표로 움직이는지 확인한다. launch의 `ros2_control_hardware_type:=isaac`도 함께 확인한다.
- **목표의 시작 상태:** 이미 open인 손가락에는 같은 open 명령을 줘도 변화가 작을 수 있다. 다른 자세에서 다시 시험하고, `hand/close` 실패는 계획 실패인지 실행 응답 문제인지 구분해 기록한다.
- **충돌 해석:** `<random_valid>`는 MoveIt의 계획 장면 기준 유효 목표다. Isaac Sim에 별도로 추가한 장애물이 MoveIt에 자동 반영된다고 판단하지 말고, 기본 장면·가까운 목표에서 계획과 실제 실행을 먼저 비교한다.

## 설치와 터미널 준비

이 폴더만 복사해도 실습할 수 있다. 다른 로컬 튜토리얼이나 공통 Python 모듈은 필요 없다. 외부 프로그램인 Isaac Sim 5.1.0, 공식 5.1 자산, ROS 2와 아래 공식 ROS 워크스페이스는 필요하다. 아래 명령은 **Ubuntu 22.04 + Humble**, bash 터미널 기준이다. Ubuntu 24.04에서는 `humble`을 `jazzy`로 바꾼다. Windows는 원문에서도 부분 지원이며 이 실습의 검증 대상으로 삼지 않는다.

ROS 2 desktop이 없으면 [Humble 설치](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) 또는 [Jazzy 설치](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html)를 먼저 수행한다. 다음 명령은 사용자 환경에 의존성을 설치하고 새 워크스페이스를 만드는 준비 절차이며 이 패키지가 자동 실행하지 않는다.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
source /opt/ros/humble/setup.bash
# rosdep을 처음 설치한 컴퓨터에서만 sudo rosdep init 실행
rosdep update
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$HOME/IsaacSim-ros_workspaces-5.1"
cd "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws"
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build
source install/local_setup.bash
```

태그의 확인된 커밋은 `50de00358f220d790d17050c6368cfe9a9cb9f51`이다. 이미 같은 폴더가 있다면 clone을 반복하지 말고 그 폴더의 버전과 빌드 결과를 확인한다. Jazzy에서 `topic_based_ros2_control` rosdep 키가 없으면 공식 설치 문서에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control` 후 재시도한다.

**터미널 A — Isaac Sim:** 일반 `/opt/ros` Python 환경을 source하지 않은 새 터미널에서 실행한다. Isaac Sim은 Python 3.11, Ubuntu의 ROS Python은 3.10/3.12이므로 기본 메시지를 DDS로 교환하는 이 실습은 내부 ROS 라이브러리를 사용한다. 같은 배포판을 A/B 양쪽에서 선택한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
# 새 터미널에서 한 번만 추가한다.
export LD_LIBRARY_PATH="$ISAAC_SIM_PATH/exts/isaacsim.ros2.bridge/$ROS_DISTRO/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

`Window > Extensions`에서 `isaacsim.ros2.bridge`를 검색하여 Enabled를 켠다. 5.1 자산 서버에 접근할 수 있어야 기본 장면을 불러올 수 있다. 로컬 자산팩을 쓰는 경우 Content 창에서 그 팩의 `Isaac` 폴더를 사용한다.

**터미널 B 및 이후 모든 ROS 터미널:** 매번 아래를 실행한 뒤 본문 ROS 명령을 실행한다.

```bash
source /opt/ros/humble/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

같은 컴퓨터에서는 Fast DDS 기본 설정을 쓴다. 다른 컴퓨터/컨테이너라면 위 워크스페이스의 `fastdds.xml` 절대 경로를 `FASTRTPS_DEFAULT_PROFILES_FILE`로 **A와 B 모두** 지정하고 통신 가능한 네트워크를 사용한다. 배포판/Domain ID가 다르면 노드가 발견되지 않는다.

## MoveIt 의존성과 장면 구조

```bash
sudo apt install ros-humble-moveit ros-humble-topic-based-ros2-control
ros2 pkg prefix isaac_moveit
ros2 pkg prefix moveit_resources_panda_moveit_config
```

의존성은 위 `rosdep install` 단계에서도 해결한다. `topic_based_ros2_control` 패키지와 공식 workspace의 submodule이 누락되지 않게 확인한다.

- **MoveIt**은 로봇의 URDF(연결 구조/관절 한계), SRDF(계획 그룹/충돌 제외), planner 설정으로 관절 경로를 계산한다. **Plan**은 계산과 미리보기, **Execute**는 실제 컨트롤러에 궤적을 보내는 별도 작업이다.
- **USD Stage**는 장면 전체, `/Franka` prim은 Franka 모델의 reference다. 기본 자산은 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`, 배경은 `Isaac/Environments/Simple_Room/simple_room.usd`다. 예제는 `Gripper=AlternateFinger`, `Mesh=Quality` variant를 선택한다. Variant는 같은 USD 안의 미리 정의된 대안 선택이다.
- **Articulation**은 관절로 연결된 강체 집합이다. MoveIt의 관절 이름이 시뮬레이터 Articulation의 이름과 일치해야 정확한 관절이 움직인다.
- **ros2_control**은 궤적 컨트롤러와 하드웨어 인터페이스를 연결한다. 이 실습은 `ros2_control_hardware_type:=isaac`을 사용하여 `/isaac_joint_commands`와 `/isaac_joint_states` 토픽으로 시뮬레이터와 교환한다.

## 1. 공식 Franka 장면 실행

1. Isaac Sim에서 `Window > Examples > Robotics Examples > ROS2 > MoveIt > Franka MoveIt`을 선택한다.
2. **Load Sample Scene**을 누른다. 새 Stage에 `/Franka`, `/background`, `/ActionGraph`가 생성된다. 다른 장면에 만든 작업이 있다면 로드 전에 저장한다.
3. 타임라인이 멈춰 있으면 **Play**를 누른다. 원본 5.1 예제 로더는 장면 생성 후 자동 Play를 시작할 수 있다.
4. `Window > Graph Editors > Action Graph`에서 `/ActionGraph`를 열고 다음 연결을 따라간다.

| 노드/설정 | 맡는 일 |
|---|---|
| `On Playback Tick` | 매 시뮬레이션 프레임 관절 게시/명령 수신/제어 실행 |
| `ROS 2 Context` | ROS Domain과 DDS context 제공 |
| `Isaac Read Simulation Time` | 관절 상태와 clock의 동일 시간 기준 |
| `ROS 2 Publish Joint State` | targetPrim `/Franka`, topicName `isaac_joint_states` |
| `ROS 2 Subscribe Joint State` | topicName `isaac_joint_commands`; jointNames/positionCommand 등을 출력 |
| `Isaac Articulation Controller` | robotPath `/Franka`; 수신한 이름과 명령을 관절에 적용 |
| `ROS 2 Publish Clock` | `/clock` 게시 |

`ROS2PublishJointState`, `ROS2SubscribeJointState`, `IsaacArticulationController`는 위 UI 표시의 실제 5.1 OmniGraph 노드 API다. 수신 노드의 jointNames→controller jointNames, positionCommand→positionCommand, velocityCommand→velocityCommand, effortCommand→effortCommand 연결을 확인한다.

## 2. MoveIt/컨트롤러 시작

ROS 터미널에서 다음을 실행한다.

```bash
ros2 launch isaac_moveit isaac_moveit.launch.py ros2_control_hardware_type:=isaac use_sim_time:=true
```

launch는 `move_group`, RViz, robot_state_publisher, controller_manager, arm/hand controller spawner를 시작한다. **mock_components**를 선택하면 RViz 내부 움직임만 보고 성공으로 착각할 수 있으므로 이 실습은 `isaac` 값을 명시한다. 새 ROS 터미널에서 통신과 컨트롤러 상태를 확인한다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /isaac_joint_states --once
ros2 control list_controllers
ros2 topic info /isaac_joint_commands -v
```

arm/hand controller가 active 상태인지 확인한다. `ros2_control` 명령은 ROS 배포판의 `ros2controlcli` 패키지가 설치되어 있어야 한다. 실행이 끝나면 launch는 Ctrl+C로 종료한다.

## 3. 손가락 열기

1. RViz의 **MotionPlanning** 패널에서 **Planning Group = hand**를 선택한다.
2. **Goal State = open**을 선택한다. **Commands > Plan**을 누른다. 미리보기 손가락이 움직여도 Isaac Sim 로봇이 아직 움직이지 않는 것이 정상이다.
3. **Execute**를 누른다. Isaac Sim에서 두 손가락이 벌어지는지 관찰한다. 이미 open 자세이면 먼저 다른 자세로 움직인 후 다시 open을 시험한다.
4. `/isaac_joint_commands`에 명령이 나가고 `/isaac_joint_states`의 finger joint position이 변하는지 확인한다.

```bash
ros2 topic echo /isaac_joint_commands --once
ros2 topic echo /isaac_joint_states --once
```

원문은 특정 컴퓨터에서 `hand/close`가 지연되거나 실패한 뒤 다음 실행 때 움직일 수 있다고 명시한다. close 실패는 계획 자체와 실행 단계를 분리해 기록하고 첫 성공 실험은 open으로 한다.

## 4. 팔 자세 계획과 실행

1. **Planning Group = panda_arm**으로 변경한다. 손가락 그룹을 그대로 두면 팔 목표를 계획하지 않는다.
2. 말단의 이동 화살표로 목표를 조금 옮기고 회전 디스크로 방향을 바꾼다. 처음에는 현재 자세 가까이에서 시작한다.
3. **Plan**을 누르고 계획 경로가 로봇 자체와 충돌하지 않는지 미리보기한다. 실패하면 목표를 가까이 옮겨 다시 계획한다.
4. **Execute**를 누르고 Isaac Sim 팔이 그 경로를 따라 움직이는지 확인한다. RViz 미리보기만 움직이면 command topic/컨트롤러/Play를 확인한다.
5. **Goal State = <random_valid>**로 바꿔 다른 유효 자세를 생성한 뒤 Plan → Execute를 반복한다. valid는 설정된 계획 장면 기준이므로 Isaac Sim에 추가한 임의 장애물이 자동으로 MoveIt planning scene에 포함되는 것은 아니다.

## 확인과 한 변수 실험

성공은 arm/hand active controller, 관절 상태 수신, Plan 미리보기, Execute 후 실제 USD Articulation의 위치 변화로 판단한다. 한 변수 실험은 같은 목표에 대해 RViz의 Velocity Scaling만 낮추고 계획/실행하여 이동 시간이 어떻게 달라지는지 보는 것이다. 나머지 가속도/목표/플래너는 고정한다.

검은 RViz 화면은 우선 ROS 터미널 로그와 그래픽 컨텍스트 문제를 확인한다. 원문에는 Mesa 드라이버 교체 예시가 있지만 시스템 전체 업그레이드를 이 실습이 자동 실행하지 않는다. ROS 상태가 안 들어오면 Python ABI 혼용, Domain ID, Play, ROS Bridge 순으로 확인한다. 경로는 나오나 로봇이 안 움직이면 `ros2_control_hardware_type`, controller active 상태, 명령 토픽 publisher/subscriber 연결을 본다. 로봇을 USD에서 임의 이동하면 launch의 `world → panda_link0` 고정 TF와 불일치하므로 기본 위치로 복원한다.

## 출처와 검증 범위

- [Isaac Sim 5.1 MoveIt 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_moveit.html): hand/open, panda_arm, Plan/Execute, 알려진 hand/close 문제.
- [5.1 ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html).
- [5.1 isaac_moveit launch](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/humble_ws/src/moveit/isaac_moveit/launch/isaac_moveit.launch.py).
- [MoveIt Humble 문서](https://moveit.picknik.ai/humble/index.html).

노드/토픽/자산/variant는 설치된 5.1 `isaacsim.ros2.bridge/.../impl/samples/ros_moveit_sample.py`에 대조했다. GPU·DDS·MoveIt 실제 실행은 수행하지 않았으며 `verification: not_run`이다.
