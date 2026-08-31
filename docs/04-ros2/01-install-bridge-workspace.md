# ROS 2 Jazzy 설치, Bridge, 워크스페이스

이 장에서는 Ubuntu 24.04의 시스템 Jazzy와 Isaac Sim 5.1의 내장 Jazzy를 충돌 없이 구성하고, `/clock` 메시지로 연결을 검증한다.

## 1. 시스템 ROS 2 Jazzy를 설치하다

이미 설치되어 있다면 먼저 확인한다.

```bash
test -f /opt/ros/jazzy/setup.bash && echo "Jazzy installed"
```

새 설치에서는 ROS 2 공식 Ubuntu deb 절차를 따른다. 저장소 등록 명령은 시간이 지나면 바뀔 수 있으므로 공식 페이지가 이 예제와 다르면 공식 페이지를 우선한다.

```bash
sudo apt update
sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo add-apt-repository -y universe
sudo apt update
```

ROS apt source 패키지를 설치한 뒤 Jazzy Desktop과 개발 도구를 설치한다.

```bash
ROS_APT_SOURCE_VERSION=$(curl -s \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F 'tag_name' | awk -F\" '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo "$VERSION_CODENAME")_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools \
  python3-colcon-common-extensions python3-rosdep
```

```bash
source /opt/ros/jazzy/setup.bash
printf 'ROS_DISTRO=%s\n' "$ROS_DISTRO"
python3 --version
ros2 doctor --report | sed -n '1,80p'
```

Ubuntu 24.04의 시스템 Python은 3.12이다. 이는 정상이다.

## 2. Isaac Sim의 내장 Jazzy를 사용하다

새 터미널에서 `/opt/ros/jazzy/setup.bash`를 source하지 않고 실행한다.

```bash
env | grep -E '^(ROS_DISTRO|AMENT_PREFIX_PATH|PYTHONPATH)=' || true
cd ~/isaacsim
./isaac-sim.sh
```

Isaac Sim 5.1은 Ubuntu 24.04에서 내장 Jazzy 라이브러리를 자동 선택한다. GUI에서 `Window > Extensions`를 열고 `isaacsim.ros2.bridge`를 검색해 활성화 상태를 확인한다. Bridge를 자동 활성화하려면 Extension 창에서 `AUTOLOAD`를 켠다.

내장 라이브러리를 명시적으로 선택해야 하는 특수 구성에서는 **새 셸에서 한 번만** 다음을 설정한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}${ISAAC_SIM_PATH}/exts/isaacsim.ros2.bridge/jazzy/lib"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

`LD_LIBRARY_PATH`를 반복해서 덧붙이지 않는다. Bridge 콘솔 로그에 `/opt/ros/jazzy/lib/python3.12`가 나타나면 시스템 ROS 환경이 Isaac Sim 프로세스에 섞인 것이다.

## 3. 외부 ROS 터미널을 준비하다

별도 터미널에서 다음을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
printenv | grep -E '^(ROS_DISTRO|RMW_IMPLEMENTATION|ROS_DOMAIN_ID)='
```

Isaac Sim을 실행한 환경과 외부 노드의 `ROS_DOMAIN_ID`가 같아야 한다. Domain ID는 같은 물리 네트워크 위에 논리적으로 분리된 ROS 그래프를 만든다.

## 4. 공식 ROS 워크스페이스를 빌드하다

NVIDIA가 제공하는 launch 파일, Nav2 구성, MoveIt 구성, 예제 메시지를 사용한다.

```bash
cd ~
git clone https://github.com/isaac-sim/IsaacSim-ros_workspaces.git
cd IsaacSim-ros_workspaces
git submodule update --init --recursive
```

Jazzy 워크스페이스의 의존성을 설치하고 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/IsaacSim-ros_workspaces/jazzy_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --symlink-install --event-handlers console_cohesion+
source install/local_setup.bash
```

`topic_based_ros2_control` rosdep 오류가 발생하면 다음 패키지를 설치한 뒤 다시 빌드한다.

```bash
sudo apt install -y ros-jazzy-topic-based-ros2-control
```

패키지 인식 여부를 확인한다.

```bash
ros2 pkg list | grep -E '^(isaacsim|isaac_moveit|carter_navigation)$'
colcon list | sed -n '1,80p'
```

## 5. `/clock`으로 Bridge를 검증하다

빈 Stage에는 publisher가 없으므로 `ros2 topic list`가 비어 있어도 Bridge 실패가 아니다. 다음 그래프를 만든다.

1. `Window > Graph Editors > Action Graph`에서 `/World/ROS2_Clock` 그래프를 생성한다.
2. `On Playback Tick`, `ROS 2 Context`, `Isaac Read Simulation Time`, `ROS 2 Publish Clock`을 추가한다.
3. `tick → execIn`, `context → context`, `simulationTime → timeStamp`를 연결한다.
4. `ROS 2 Context`의 `Use Domain ID Env Var`를 켠다.
5. Timeline에서 Play를 누른다.

메뉴 단축 경로 `Tools > Robotics > ROS 2 OmniGraphs > Clock`을 사용해도 된다.

외부 터미널에서 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

`rosgraph_msgs/msg/Clock` 메시지가 한 번 출력되면 기본 연결이 완료된 것이다.

## 6. Standalone에서 Bridge를 활성화하다

Standalone 스크립트에서는 `SimulationApp`을 먼저 만들고 그 뒤에 확장을 활성화한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

from isaacsim.core.utils.extensions import enable_extension

enable_extension("isaacsim.ros2.bridge")
simulation_app.update()  # 확장 로딩을 한 프레임 진행한다.

# 이후 World, OmniGraph, rclpy 관련 모듈을 import한다.

while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()
```

```bash
cd ~/isaacsim
./python.sh /절대/경로/bridge_test.py
```

Standalone에서도 외부 ROS CLI는 별도 Jazzy 터미널에서 실행한다.

## 7. 여러 머신과 컨테이너

같은 머신에서는 기본 Fast DDS 공유 메모리가 효율적이다. 여러 머신 또는 Docker 경계를 넘으면 모든 관련 프로세스에 같은 UDP 프로필과 Domain ID를 적용한다.

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
export ROS_DOMAIN_ID=7
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

경로는 각 머신에서 실제로 존재해야 한다. 방화벽, 서브넷, 멀티캐스트, UDP 정책도 별도로 허용해야 한다.

## 완료 체크

```bash
ros2 topic type /clock
ros2 topic echo /clock --once
```

- [ ] Isaac Sim 내부 Python 3.11과 시스템 Jazzy Python 3.12를 분리했다.
- [ ] `isaacsim.ros2.bridge`가 활성화되었다.
- [ ] 공식 `jazzy_ws`를 빌드했다.
- [ ] `/clock`을 외부 터미널에서 수신했다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1.0 — ROS 2 Bridge in Standalone Workflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html)
- [Isaac Sim 5.1.0 — ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)
- [NVIDIA — IsaacSim ROS Workspaces](https://github.com/isaac-sim/IsaacSim-ros_workspaces)
- [ROS 2 Jazzy — Ubuntu deb packages](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
