# Ubuntu 24.04와 ROS 2 Jazzy 연결

이 장에서는 Isaac Sim 5.1의 ROS 2 Bridge를 Ubuntu 24.04의 ROS 2 Jazzy 노드와 연결하다. 핵심은 **시뮬레이터 프로세스와 외부 ROS 노드의 Python 환경을 분리하는 것**이다.

## 먼저 이해할 두 Python 환경

| 역할 | Python | 실행 위치 | 용도 |
|---|---:|---|---|
| Isaac Sim과 ROS 2 Bridge | 3.11 | `~/isaacsim` 내부 | 시뮬레이터, OmniGraph, 내장 Jazzy 라이브러리 |
| Ubuntu 24.04의 ROS 2 Jazzy | 3.12 | `/opt/ros/jazzy` | RViz, CLI, 외부 노드, 일반 colcon 워크스페이스 |

DDS는 Python 프로세스 사이의 직렬화된 메시지를 전송하므로 두 프로세스의 Python 버전이 같을 필요는 없다. 반면, 시스템 Jazzy의 Python 3.12용 `rclpy`와 라이브러리를 Isaac Sim의 Python 3.11 프로세스 안에 직접 로드하려 하면 충돌할 수 있다.

따라서 기본 학습 구성은 다음처럼 운영하다.

- **터미널 A:** 시스템 ROS를 source하지 않고 `~/isaacsim/isaac-sim.sh`를 실행하다. Ubuntu 24.04에서는 Isaac Sim이 내장 Jazzy 라이브러리를 자동 선택하다.
- **터미널 B:** `source /opt/ros/jazzy/setup.bash` 후 외부 ROS 노드와 CLI를 실행하다.

`~/.bashrc`에서 ROS를 항상 source하는 설정은 초보자에게 원인 추적을 어렵게 하다. 이 튜토리얼에서는 필요한 터미널에서 명시적으로 source하다.

## 1단계: ROS 2 Jazzy 설치

이미 `/opt/ros/jazzy`가 있다면 버전 확인으로 건너뛰다.

```bash
test -f /opt/ros/jazzy/setup.bash && echo "ROS 2 Jazzy: installed"
```

새로 설치한다면 ROS 2 공식 Ubuntu deb 절차를 따르다. 아래 명령은 Ubuntu 24.04에서 locale과 Universe 저장소를 준비하고, ROS가 제공하는 `ros2-apt-source` 패키지로 저장소를 등록하는 흐름이다.

```bash
sudo apt update
sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo add-apt-repository -y universe
sudo apt update
```

ROS apt-source의 최신 릴리스 이름을 받아 설치하다.

```bash
ROS_APT_SOURCE_VERSION=$(curl -s \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F 'tag_name' | awk -F\" '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo "$VERSION_CODENAME")_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools
```

공식 ROS 설치 페이지의 명령이 이 문서와 달라졌다면 공식 페이지를 우선하다. 설치 후 새 터미널에서 확인하다.

```bash
source /opt/ros/jazzy/setup.bash
printf 'ROS_DISTRO=%s\n' "$ROS_DISTRO"
ros2 --help >/dev/null && echo "ros2 CLI: OK"
python3 --version
```

선택 메시지 패키지도 필요에 따라 설치하다.

```bash
sudo apt install -y ros-jazzy-vision-msgs ros-jazzy-ackermann-msgs
```

`vision_msgs`는 2D/3D 검출 메시지, `ackermann_msgs`는 Ackermann 조향 예제에서 사용하다. 쓰지 않는다면 설치하지 않아도 되다.

## 2단계: 터미널 A에서 Isaac Sim의 내장 Jazzy 사용

**새 터미널을 열고 `/opt/ros/jazzy/setup.bash`를 source하지 않은 상태**에서 확인하다.

```bash
echo "ROS_DISTRO=${ROS_DISTRO:-<not set>}"
export ROS_DOMAIN_ID=0
cd ~/isaacsim
./isaac-sim.sh
```

Ubuntu 24.04에서 다른 ROS 환경이 source되지 않았다면 Isaac Sim 5.1은 내장 ROS 2 Jazzy 라이브러리를 자동 로드하다. 설치 경로가 기본값이 아니거나 명시적으로 선택해야 한다면 새 터미널에서 한 번만 다음 환경을 설정하다.

```bash
export isaac_sim_package_path="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}${isaac_sim_package_path}/exts/isaacsim.ros2.bridge/jazzy/lib"
"$isaac_sim_package_path/isaac-sim.sh"
```

같은 터미널에서 이 블록을 여러 번 실행하면 `LD_LIBRARY_PATH`가 중복 누적되므로 새 터미널에서 한 번만 실행하다.

GUI에서 `Window > Extensions`를 열고 `ROS 2 Bridge` 또는 확장 ID `isaacsim.ros2.bridge`를 검색하다. 활성 상태를 확인하고 Console에서 라이브러리 로드 오류가 반복되지 않는지 확인하다. Ubuntu 24.04의 Full 앱은 기본 내장 Jazzy 구성을 제공하지만, 사용자가 앱 설정을 바꾼 경우에는 확장 상태를 직접 확인해야 하다.

## 3단계: 터미널 B에서 외부 Jazzy 노드 준비

별도 터미널에서 다음을 실행하다.

```bash
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0

printenv | grep -E '^(ROS_DISTRO|RMW_IMPLEMENTATION|ROS_DOMAIN_ID)='
```

터미널 A와 B에서 `ROS_DOMAIN_ID`가 같아야 자동 발견되다. 한 머신의 기본 Fast DDS 구성은 공유 메모리 전송을 사용할 수 있어 공식 문서가 권장하다.

## 4단계: `/clock`으로 연결 검증

토픽은 publisher가 있어야 목록에 나타나다. 빈 Stage에서 `ros2 topic list`만 실행해 아무것도 보이지 않는다고 Bridge 실패로 단정하지 않다. 다음 Action Graph를 만들어 명시적으로 시뮬레이션 시간을 발행하다.

1. Isaac Sim에서 `Window > Graph Editors > Action Graph`를 열다.
2. **New Action Graph**를 눌러 `/World/ROS2_Clock`에 그래프를 만들다.
3. 다음 노드를 검색해 추가하다.

   - `On Playback Tick`
   - `ROS 2 Context`
   - `Isaac Read Simulation Time`
   - `ROS 2 Publish Clock`

4. `On Playback Tick.tick`을 `ROS 2 Publish Clock.execIn`에 연결하다.
5. `ROS 2 Context.context`를 `ROS 2 Publish Clock.context`에 연결하다.
6. `Isaac Read Simulation Time.simulationTime`을 `ROS 2 Publish Clock.timeStamp`에 연결하다.
7. 툴바의 **Play**를 누르다. 노드의 포트 표기는 확장 UI에 따라 공백과 대소문자가 다르게 보일 수 있으므로 포트의 의미로 연결하다.

터미널 B에서 확인하다.

```bash
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0

ros2 topic list
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

`/clock`이 보이고 한 개의 `rosgraph_msgs/msg/Clock` 메시지가 출력되면 기본 연결에 성공한 것이다. 데이터가 나오지 않으면 Isaac Sim의 Timeline이 Play 상태인지 먼저 확인하다.

## 5단계: Isaac Sim ROS 워크스페이스

NVIDIA 튜토리얼 패키지와 launch 파일을 사용하려면 공식 워크스페이스를 별도로 받다.

```bash
cd ~
git clone https://github.com/isaac-sim/IsaacSim-ros_workspaces.git
cd IsaacSim-ros_workspaces
git submodule update --init --recursive
```

시스템 Jazzy용 워크스페이스를 빌드하다. 저장소 구조에서 `jazzy_ws` 경로가 존재하는지 먼저 확인하다.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install -y python3-rosdep build-essential \
  python3-colcon-common-extensions

cd ~/IsaacSim-ros_workspaces/jazzy_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --symlink-install
source install/local_setup.bash
```

`topic_based_ros2_control` rosdep 규칙 오류가 나면 공식 5.1 문서의 우회 패키지를 설치한 뒤 다시 실행하다.

```bash
sudo apt install -y ros-jazzy-topic-based-ros2-control
```

## 커스텀 메시지와 `rclpy`의 중요한 예외

표준 메시지만 DDS로 주고받을 때는 외부 노드가 Python 3.12여도 문제없다. 그러나 Isaac Sim 내부 Python 코드나 커스텀 OmniGraph 노드가 사용자 정의 ROS 인터페이스를 직접 import한다면 다음 두 빌드가 모두 필요하다.

1. Isaac Sim Python 3.11에서 로드할 워크스페이스
2. Ubuntu 24.04의 일반 ROS 2 Jazzy/Python 3.12 외부 노드용 워크스페이스

NVIDIA 저장소의 Dockerfile을 사용해 Python 3.11 쪽을 만들다.

```bash
cd ~/IsaacSim-ros_workspaces
./build_ros.sh -d jazzy -v 24.04

source build_ws/jazzy/jazzy_ws/install/local_setup.bash
source build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
~/isaacsim/isaac-sim.sh
```

빌드 시간이 오래 걸리고 네트워크와 디스크를 많이 사용하다. 커스텀 인터페이스가 필요하지 않다면 이 단계를 생략하다.

## 여러 머신 또는 Docker에서 발견이 안 될 때

같은 머신은 기본 Fast DDS 구성을 유지하다. 여러 머신이나 Docker 경계를 넘으면 공식 워크스페이스 루트의 `fastdds.xml`을 모든 관련 터미널에서 같은 경로로 지정하고 UDP 전송을 사용하다.

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
export ROS_DOMAIN_ID=7
```

방화벽, 서브넷, 멀티캐스트/UDP 정책도 함께 점검하다. 단순히 환경 변수 하나를 설정했다고 클라우드 네트워크를 자동 통과하는 것은 아니다.

## 진단 체크리스트

```bash
# 터미널 A와 B에서 각각 비교하다.
printenv | grep -E '^(ROS_DISTRO|RMW_IMPLEMENTATION|ROS_DOMAIN_ID|FASTRTPS_DEFAULT_PROFILES_FILE)='

# 외부 ROS 그래프를 새로 조회하다.
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

- Bridge 로그에 Python 3.12 라이브러리 경로가 섞였다면 Isaac Sim 터미널에서 시스템 ROS를 source한 것이 아닌지 확인하다.
- `/clock`은 보이지만 메시지가 없으면 Timeline의 Play와 Action Graph 실행선을 확인하다.
- 서로 다른 머신에서만 실패하면 같은 `ROS_DOMAIN_ID`, 같은 RMW 구현, Fast DDS UDP 프로필과 방화벽을 확인하다.
- 토픽은 보이지만 subscribe가 안 되면 `ros2 topic info <topic> -v`로 QoS 호환성을 확인하다.

## 완료 체크포인트

- [ ] Isaac Sim 내부 Python 3.11과 시스템 Jazzy Python 3.12의 역할을 구분했다.
- [ ] 터미널 A에서 내장 Jazzy로 Isaac Sim을 실행했다.
- [ ] 터미널 B에서 시스템 Jazzy CLI를 실행했다.
- [ ] Action Graph가 발행한 `/clock` 메시지를 외부 터미널에서 받았다.
- [ ] 커스텀 인터페이스를 쓸 때 이중 빌드가 필요한 이유를 이해했다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [ROS 2 Jazzy — Ubuntu deb packages](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [NVIDIA — IsaacSim ROS Workspaces](https://github.com/isaac-sim/IsaacSim-ros_workspaces)
- [Isaac Sim 5.1.0 — ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)
- [Isaac Sim 5.1.0 — ROS 2 QoS](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)
