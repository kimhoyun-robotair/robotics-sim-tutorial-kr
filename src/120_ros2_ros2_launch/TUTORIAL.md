# 120. 장면이 준비된 뒤 ROS 관찰을 시작하려면?

## 이번에 배우는 것

**ROS launch로 Isaac Sim을 시작하고, 장면의 준비 신호를 받은 다음 `/clock` 메시지를 관찰합니다.**

프로그램을 실행했다는 사실만으로 장면을 곧바로 사용할 수 있는 것은 아닙니다. 앱이 뜨고, 물체와 그래프가 만들어지고, 물리가 시작되는 데 각각 시간이 필요합니다. 이번에는 큐브를 떨어뜨리는 작은 장면으로 이 순서를 확인합니다.

| 파일 또는 신호 | 맡는 일 | 확인할 내용 |
|---|---|---|
| `lesson.launch.py` | 공식 launcher와 관찰 프로세스 연결 | 어느 시점에 echo를 시작하는지 |
| `clock_scene.py` | 큐브·바닥·시계 그래프 생성과 물리 진행 | 큐브 낙하와 시뮬레이션 시간 |
| `LOCAL_CLOCK_SCENE_READY` | 첫 물리 단계가 끝났다는 출력 | 장면 준비 여부 |
| `/clock` 메시지 | ROS로 도착한 시뮬레이션 시간 | 실제 외부 통신 여부 |

준비 신호와 수신 메시지를 나란히 확인하면 장면 초기화와 ROS 통신을 구분할 수 있습니다.

## 1. ROS launch로 장면 실행하기

아래는 **Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0** 기준 Bash 명령입니다. 지원 NVIDIA GPU와 ROS 개발 도구가 필요합니다. Linux에서 진행하며 WSL2는 원문의 지원 범위에 포함되지 않습니다.

먼저 저장소 루트에서 실습 경로를 보관하고 공식 ROS 워크스페이스를 준비합니다. 같은 5.1.0 워크스페이스를 이미 빌드했다면 clone과 빌드를 반복하지 않고 해당 `install/local_setup.bash`를 source하세요.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
export LESSON_DIR="$PWD/src/120_ros2_ros2_launch"
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
colcon build
source install/local_setup.bash
ros2 pkg prefix isaacsim
```

`rosdep`은 설치·초기화된 상태여야 합니다. 여기서 `isaacsim`은 **ROS launch 패키지 이름**입니다. 시뮬레이터 설치 폴더와 다른 위치가 출력되는 것이 정상입니다.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch "$LESSON_DIR/lesson.launch.py" install_path:="$HOME/isaacsim" ros_distro:=jazzy
```

설치 위치가 다르면 `install_path`를 바꾸세요. 로컬 launch는 공식 launcher에 `use_internal_libs=true`를 전달하여 Isaac Sim의 Python 3.11용 ROS 라이브러리를 사용합니다.

### 실행 결과 확인하기

1. `/World/LaunchCube`와 바닥이 나타납니다. 큐브는 중심 높이 2 m에서 떨어집니다.
2. 터미널에 `LOCAL_CLOCK_SCENE_READY`가 출력됩니다.
3. 자동 실행된 `ros2 topic echo /clock --once`가 `clock:`, `sec:`, `nanosec:` 필드를 출력하는지 확인하세요. 이 메시지가 실제 수신의 근거입니다.
4. echo는 한 메시지를 받은 뒤 끝나지만 GUI와 물리는 계속 실행됩니다. launch 터미널의 **Ctrl+C**로 실습을 종료합니다.

충분히 기다린 큐브의 중심 높이는 약 0.2 m입니다. 한 변이 0.4 m이므로 바닥에 닿아도 중심은 0 m가 되지 않습니다. 코드가 정상 종료 경로에 도달하면 `Final cube world position:`을 출력합니다. 강제 종료에서는 마지막 문구가 생략될 수 있습니다. CSV는 만들지 않습니다.

## 2. 준비 신호를 보내고 받는 코드 살펴보기

### 코드에서 볼 부분

`clock_scene.py`는 앱을 시작한 뒤 `World`, 충돌 가능한 큐브, 바닥을 만듭니다. `/LaunchClock` 그래프는 Play Tick에 맞춰 시뮬레이션 시간을 발행합니다.

```text
On Playback Tick ─────────────────→ ROS2 Publish Clock 실행
Isaac Read Simulation Time ───────→ timeStamp
```

이후 다음 코드가 준비 신호의 의미를 정합니다.

```python
world.reset()
world.play()
world.step(render=True)
print('LOCAL_CLOCK_SCENE_READY', flush=True)
```

신호를 출력하기 전에 물리를 한 번 진행합니다. `flush=True`는 출력이 버퍼에 남아 launch가 뒤늦게 읽지 않도록 즉시 내보내는 설정입니다. 다만 이 단계는 DDS가 외부 수신자를 발견했다는 뜻까지 포함하지 않습니다.

`lesson.launch.py`에서는 `OnProcessIO`가 프로세스의 표준 출력을 읽습니다.

```python
state['tail'] = (state['tail'] + event.text.decode(errors='replace'))[-4096:]
if 'LOCAL_CLOCK_SCENE_READY' in state['tail']:
    state['started'] = True
    return [observer]
```

출력은 한 줄씩 도착한다는 보장이 없습니다. 앞에서 받은 문자열과 새 조각을 이어 붙이므로 준비 문구가 중간에서 나뉘어도 찾을 수 있습니다. `started`가 이미 참이면 새 observer를 만들지 않아 한 번만 관찰합니다.

### 독립 실행과 비교하기

launch를 종료한 뒤 **시스템 ROS를 source하지 않은 새 Bash**를 열고 저장소 루트에서 실행하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/120_ros2_ros2_launch/clock_scene.py --steps 120
```

큐브와 시계 그래프는 같지만 자동 echo는 없습니다. 그 부분은 `lesson.launch.py`가 맡기 때문입니다. `--steps 120`은 **준비용 1단계 이후 반복문에서 120단계**를 더 진행한다는 뜻입니다. GUI에서 옵션을 생략하면 창을 닫을 때까지 실행하고, `--headless`만 지정하면 반복문 3600단계 뒤 종료합니다.


### 공식 launcher의 실행 방식 바꾸기

로컬 launch의 첫 실행을 확인한 뒤에는 공식 launcher를 직접 호출하여 장면을 여는 방법을 비교할 수 있습니다. 아래 명령은 **시스템 Jazzy와 공식 workspace를 source한 ROS 터미널**에서 한 번에 하나씩 실행합니다. 다음 예제로 넘어가기 전 이전 launch를 Ctrl+C로 종료하세요.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:="$HOME/isaacsim" version:=5.1.0 ros_distro:=jazzy
```

이 호출은 빈 GUI를 엽니다. 기존 USD를 열고 재생하려면 `gui`와 `play_sim_on_start`를 함께 사용합니다.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:="$HOME/isaacsim" ros_distro:=jazzy \
  gui:=https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd \
  play_sim_on_start:=true
```

반대로 앱과 반복문을 소유한 Python 예제를 실행할 때는 `standalone`을 사용합니다.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:="$HOME/isaacsim" ros_distro:=jazzy \
  standalone:="$HOME/isaacsim/standalone_examples/api/isaacsim.ros2.bridge/moveit.py"
```

| 인자 | 선택할 때 확인할 점 |
|---|---|
| `install_path` / `version` | 실제 설치 경로를 지정하면 version에 의한 경로 탐색보다 우선합니다. |
| `gui` / `standalone` | USD 장면을 여는 경로와 Python이 앱을 실행하는 경로입니다. |
| `play_sim_on_start` | GUI로 연 장면의 자동 Play입니다. standalone 루프는 Python이 맡습니다. |
| `dds_type` | `fastdds` 또는 `cyclonedds`이며 외부 ROS의 RMW와 함께 맞춥니다. |
| `headless:=webrtc` | 공식 GUI launcher의 스트리밍 방식입니다. 로컬 스크립트의 `--headless`와 구분합니다. |
| `ros_installation_path` | Python 3.11 ROS·사용자 패키지의 setup 파일 목록입니다. |
| `exclude_install_path` | Isaac Sim 프로세스에 섞이면 안 되는 시스템 Python용 workspace 경로입니다. |

사용자 Python 메시지가 필요하다면 공식 workspace 루트에서 Docker 기반 `./build_ros.sh -d jazzy -v 24.04`로 Python 3.11 결과를 먼저 만듭니다. 그러고 나서 ROS용 터미널에서 다음처럼 외부 launch 패키지는 유지하고 **자식 Isaac Sim이 읽을 환경만** 구분합니다.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:="$HOME/isaacsim" ros_distro:=jazzy \
  exclude_install_path:="$ROS_WS_REPO/jazzy_ws/install" \
  ros_installation_path:="$ROS_WS_REPO/build_ws/jazzy/jazzy_ws/install/local_setup.bash,$ROS_WS_REPO/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash"
```

build_ros.sh는 기존 `build_ws/jazzy` 생성물을 다시 만듭니다. 사용자 변경이 있는 빌드 폴더라면 보존하거나 새 실습 checkout을 사용하세요. 기본 큐브·Clock 실습에는 이 사용자 메시지 빌드가 필요하지 않습니다. Python 3.11 빌드 준비와 기본 내부 라이브러리 선택은 [공식 ROS 설치 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)를 따릅니다.

### Nav2를 함께 실행하고 장면 준비 뒤 자동 목표 보내기

공식 workspace에는 Isaac Sim과 Nav2/RViz를 함께 시작하고, **장면 준비 문구를 받은 뒤 자동 목표 생성기**를 실행하는 launch도 있습니다. Nav2 자체가 준비 문구를 기다리는 구조는 아닙니다. ROS 터미널에서 의존성을 확인하세요.

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-pointcloud-to-laserscan
ros2 pkg prefix carter_navigation
ros2 pkg prefix isaac_ros_navigation_goal
ros2 launch carter_navigation carter_navigation_isaacsim.launch.py install_path:="$HOME/isaacsim" ros_distro:=jazzy
```

창고 장면이 로드된 뒤 RViz의 센서 표시와 로봇 주행을 확인합니다. 이 통합 launch가 기다리는 공식 준비 문구는 `Stage loaded and simulation is playing.`이며 로컬 큐브의 신호와 다릅니다. 장면이 준비되어도 Nav2의 lifecycle과 action 서버가 아직 준비되지 않을 수 있습니다. 자동 목표가 일찍 시작된다면 실습 checkout의 `carter_navigation_isaacsim.launch.py`에서 `execute_second_node_if_condition_met`의 초기화 지연 안내를 확인하고 해당 패키지를 다시 빌드·source하세요.

Carter 실행을 종료한 뒤 iw_hub의 같은 흐름도 실행할 수 있습니다.

```bash
ros2 launch iw_hub_navigation iw_hub_navigation_isaacsim.launch.py install_path:="$HOME/isaacsim" ros_distro:=jazzy
```

각 통합 launch는 해당 5.1 로봇·창고 자산에 접근할 수 있어야 합니다. RViz가 열리거나 목표 생성기가 종료된 사실만 보지 말고 센서 수신, action 결과와 실제 로봇 도착을 확인하세요.

## 3. 시작·준비·수신의 차이 정리

```text
ROS launch → 공식 launcher가 Isaac Sim 시작
  → 장면 생성 및 첫 물리 단계 진행 → 준비 문구 출력
    → launch가 echo 시작 → DDS 연결 뒤 Clock 메시지 수신
```

**준비 문구까지 보이면 장면 초기화를, Clock 메시지까지 보이면 외부 관찰 경로를 확인한 것입니다.** Nav2 같은 다른 프로그램에는 자체 초기화 과정이 더 있으므로, 이 신호 하나로 모든 프로그램의 준비를 판단하지 않습니다.

## 4. 간단한 확인 실험

`clock_scene.py`의 `position=np.array([0,0,2.0])`에서 높이 **2.0만 3.0**으로 바꾸고 같은 launch를 다시 실행해 보세요.

- 바닥에 닿기까지 더 오래 걸리는지 관찰합니다.
- 충분히 기다렸을 때 최종 중심 높이는 여전히 약 0.2 m인지 확인합니다.
- 준비 문구는 착지보다 먼저 나옵니다. 이 신호는 첫 물리 단계 완료를 뜻합니다.

## 실행할 때 막히면

- **Jazzy 빌드 준비에서 `topic_based_ros2_control` rosdep 오류**: 공식 설치 안내에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control`을 실행한 뒤 rosdep 명령을 다시 수행하세요.
- **`Package 'isaacsim' not found`**: ROS 워크스페이스의 빌드 결과를 source한 터미널인지 확인하고 `ros2 pkg prefix isaacsim`부터 실행하세요.
- **앱 경로를 찾지 못함**: `install_path`가 `isaac-sim.sh`를 포함하는 설치 디렉터리인지 확인하세요. 공식 launcher의 shell 실행을 고려해 설치 경로는 공백 없는 경로를 사용합니다.
- **준비 문구는 있는데 echo가 기다림**: 같은 Domain ID와 RMW인지, GUI에서 물리가 진행 중인지 확인하세요.
- **직접 실행에서 Python/ROS 심볼 오류**: 시스템 Jazzy의 Python 경로가 섞이지 않은 새 터미널에서 내부 라이브러리 환경을 설정하세요.
- **`steps must be positive`**: `--steps 0`으로 무제한 실행을 표현하지 않습니다. GUI를 계속 열어 두려면 옵션을 생략하세요.

Ubuntu 22.04/Humble을 사용한다면 위 명령의 `jazzy`를 `humble`로 맞추세요. 시뮬레이터와 외부 ROS의 배포판을 함께 변경합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS 2 Launch](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html)에 대응합니다. 외부 패키지 준비와 Python 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

공식 launcher 위에 큐브 장면과 준비 신호, 한 번의 Clock 관찰을 구성한 로컬 실습입니다. 원문의 Nav2 통합 launch까지 자동 실행하지 않습니다. 코드와 공식 자료를 대조했으며, GPU 장면·ROS launch·DDS 수신의 실행 상태는 `tutorial.json`의 `verification: not_run`입니다.
