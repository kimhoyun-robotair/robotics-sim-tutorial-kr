# 120. ROS 2 Launch

권장 학습 순서 **120** · ROS 2 연결과 기본 통신 · 출처 ID `t033`

**목표:** ROS launch가 Isaac Sim 프로세스와 scene 준비 시점을 관리하게 합니다. 로컬 `lesson.launch.py`는 공식 `isaacsim` launch를 포함하고, 로컬 `clock_scene.py`로 Cube/물리/clock 그래프를 만든 뒤 준비 신호를 받아 실제 `/clock` 한 메시지를 관찰합니다. Linux 전용이며 WSL2는 원문에서 지원되지 않습니다.


**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 물리와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 명시하면 해당 스텝 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 3600스텝으로 종료하며, `--steps 0`과 음수는 허용하지 않습니다.

## 외부 launch 패키지 준비

Ubuntu 22.04/ROS 2 Humble, Isaac Sim 5.1.0, 지원 GPU/드라이버가 필요합니다. Python/ROS 환경 분리는 공식 launcher의 `use_internal_libs=true`가 처리합니다. 시스템 ROS용 터미널에서 먼저 공식 workspace를 준비합니다.

```bash
source /opt/ros/humble/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/humble_ws"
git submodule update --init --recursive
rosdep install -i --from-path src --rosdistro humble -y
colcon build
source install/local_setup.bash
ros2 pkg prefix isaacsim
```

`isaacsim`은 여기서 ROS package 이름입니다. Isaac Sim 설치의 Python package와 구분하세요. `carter_navigation`, `iw_hub_navigation`, `isaac_ros_navigation_goal`도 전체 workspace 빌드에 포함됩니다. 이 폴더는 외부 패키지 소스를 재배포하지 않습니다.

## 로컬 launch 실행

이 패키지 폴더로 돌아와 실행합니다.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch ./lesson.launch.py install_path:="$HOME/isaacsim"
```

1. 그래픽 앱이 시작되고 `/World/LaunchCube`가 바닥으로 떨어집니다. 약간의 로딩 시간이 필요합니다.
2. stdout에 `LOCAL_CLOCK_SCENE_READY`가 나온 다음 별도 `ros2 topic echo /clock --once` 프로세스가 실행됩니다. 실제 Clock 메시지 출력이 있어야 관찰 성공입니다. 준비 문구만 출력됐다는 사실은 ROS 통신 검증이 아닙니다.
3. scene은 기본적으로 창을 직접 닫을 때까지 물리와 clock 발행을 계속합니다. 전체 launch 종료는 Ctrl-C입니다. direct standalone 비교는 환경을 따로 설정한 깨끗한 터미널에서 `"$ISAAC_SIM/python.sh" clock_scene.py`입니다. 일반 `python3 clock_scene.py --help`는 Kit 없이 옵션을 볼 수 있습니다.
4. `lesson.launch.py`의 OnProcessIO는 stdout 조각을 이어 붙여 준비 문구가 여러 chunk로 나뉘어도 한 번만 observer를 시작합니다. observer의 stdout은 다시 trigger되지 않습니다.

## 원문의 launch 변형

각 예제 전 이전 launch를 Ctrl-C로 종료합니다.

```bash
# 빈 GUI, 정확한 설치/버전
ros2 launch isaacsim run_isaacsim.launch.py install_path:="$HOME/isaacsim" version:=5.1.0
# 공식 Nova Carter USD를 열고 자동 Play
ros2 launch isaacsim run_isaacsim.launch.py install_path:="$HOME/isaacsim" gui:=https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd play_sim_on_start:=true
# 설치된 공식 standalone MoveIt scene
ros2 launch isaacsim run_isaacsim.launch.py install_path:="$HOME/isaacsim" standalone:="$HOME/isaacsim/standalone_examples/api/isaacsim.ros2.bridge/moveit.py"
# scene 준비 후 Nav2/RViz/자동 목표까지 실행하는 외부 통합 launch
ros2 launch carter_navigation carter_navigation_isaacsim.launch.py
ros2 launch iw_hub_navigation iw_hub_navigation_isaacsim.launch.py
```

Nav2 예제는 해당 로봇/창고 USD assets, RViz, navigation2/nav2_bringup 등 workspace 의존성이 설치돼 있어야 합니다. 로봇의 센서가 RViz에 표시되고 경로 계획 후 실제 움직이는지 봅니다. 자동 목표가 안 생기면 Nav2 lifecycle이 active인지 확인한 후 해당 launch의 `execute_second_node_if_condition_met`에 제공된 초기화 지연 설정을 사용합니다. scene 준비와 Nav2 준비는 서로 다른 사건입니다.

## 주요 launch 인자/API 해설

| 인자 | 의미 |
|---|---|
| `install_path` | Isaac Sim 설치 절대 경로; 지정 시 version 탐색보다 우선 |
| `use_internal_libs=true` | Isaac Sim Python 3.11용 ROS 라이브러리 사용 |
| `dds_type` | `fastdds` 또는 `cyclonedds`; 외부 RMW와 맞춤 |
| `gui` | 로드할 USD 파일/URI |
| `standalone` | SimulationApp을 소유하는 Python 파일 |
| `play_sim_on_start` | GUI scene 로드 후 Play; standalone 루프는 script가 관리 |
| `headless=webrtc` | 공식 GUI launch의 streaming 모드; standalone script의 headless와 구분 |
| `ros_installation_path` | custom Python3.11 ROS/workspace setup 파일들의 쉼표 구분 목록 |
| `exclude_install_path` | 시스템 ROS workspace의 호환되지 않는 Python 경로를 제거할 목록 |

custom 메시지가 필요한 경우 공식 workspace root에서 `./build_ros.sh -d humble -v 22.04`로 Python3.11 build를 만들고 `exclude_install_path:=$ROS_WS_REPO/humble_ws/install`, `ros_installation_path:=$ROS_WS_REPO/build_ws/humble/humble_ws/install/local_setup.bash,$ROS_WS_REPO/build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash`를 지정합니다. Jazzy도 `jazzy`에 대응하는 Python3.11 빌드가 필요합니다.

`IncludeLaunchDescription`은 다른 launch의 동작을 구성에 포함하고 `OnProcessIO`는 출력 이벤트를 처리합니다. 임의 고정 시간 지연 대신 **scene이 실제 준비된 시점**을 사용하지만 DDS discovery/각 lifecycle 준비는 추가 확인해야 합니다. USD reference는 asset 경로를 연결하고 standalone script는 runtime graph/물리 객체를 구성합니다.

## 한 가지 변수 실험과 문제 해결

`clock_scene.py`의 Cube 시작 높이만 2→3 m로 바꿔 낙하 시간이 길어지는지 확인합니다. launch가 시작되지 않으면 `ros2 pkg prefix isaacsim`과 `install_path`를 확인합니다. 준비 메시지는 있는데 clock이 안 오면 두 프로세스의 Domain ID/브리지 활성화를 확인합니다. Python ABI 오류는 `use_internal_libs`와 exclude/source 설정을 확인합니다.

공식 5.1 launcher는 standalone 경로를 shell 명령으로 실행합니다. 로컬 launch는 scene 경로를 `shlex.quote`로 전달합니다. Isaac Sim 설치 경로는 공백이 없는 기본 경로를 사용합니다. stdout은 자식 프로세스에 상속되어 launch의 준비 이벤트에서 관찰됩니다. [고정 버전 launcher 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/humble_ws/src/isaacsim/scripts/run_isaacsim.py)에서 이 동작을 확인할 수 있습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
