# 03. Ubuntu 24.04에 Isaac Sim 6.0.1과 ROS 2 Jazzy를 설치하다

## 목표와 준비

02단계의 점검을 마친 x86_64 Ubuntu 데스크톱에서 Isaac Sim 앱과 ROS 2를 각각 설치한다. 이 과정은 공식 standalone 배포본을 압축 해제하는 방식을 사용한다. 여기서 “standalone 배포본”은 설치 파일의 배포 형태를 뜻하며, GUI와 Standalone Python 작업 방식을 모두 실행할 수 있다. Python 가상환경에 `pip install isaacsim`을 하는 다른 설치 방식과 섞지 않는다.

현재 터미널에서 다음 두 변수가 올바른지 확인한다. `TUTORIAL_ROOT`가 비어 있으면 저장소 폴더로 이동한 뒤 `export TUTORIAL_ROOT="$PWD"`를 실행한다.

```bash
: "${TUTORIAL_ROOT:?저장소 최상위 경로를 먼저 지정한다}"
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
sudo apt update
sudo apt install -y unzip curl software-properties-common locales
```

## 1. 6.0.1 배포본을 정확히 선택하다

1. [6.0.1 다운로드 페이지](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/download.html)를 연다.
2. 표에서 제품이 `Isaac Sim`, 버전이 `6.0.1`, 플랫폼이 `Linux (x86_64)`인지 확인한다. WebRTC Client나 ARM용 파일을 받지 않는다.
3. 파일을 `Downloads`에 저장한다. 다운로드가 완전히 끝난 뒤 아래 명령에 **다운로드한 ZIP의 절대 경로**를 입력한다. 파일명을 브라우저에 표시된 그대로 사용한다.
4. 기존 5.1.0 설치 폴더에 덮어쓰지 않고 새 폴더에 압축을 푼다.

```bash
read -r -p 'Isaac Sim 6.0.1 ZIP 절대 경로: ' ISAAC_SIM_ZIP
test -f "$ISAAC_SIM_ZIP" || { printf 'ZIP 파일을 찾지 못했다.\n'; exit 1; }
unzip -t "$ISAAC_SIM_ZIP"
mkdir -p "$ISAAC_SIM_PATH"
unzip "$ISAAC_SIM_ZIP" -d "$ISAAC_SIM_PATH"
test -x "$ISAAC_SIM_PATH/isaac-sim.sh"
test -x "$ISAAC_SIM_PATH/python.sh"
```

`unzip -t`는 ZIP 손상 여부를 점검한다. 공식 다운로드 표에 체크섬이 있으면 표의 값과 로컬 파일의 같은 종류 체크섬도 비교한다. 출력이 없더라도 `test -x`가 성공하면 종료 코드는 0이다. 경로 검사에 실패하면 압축 안에 상위 폴더가 한 겹 더 생겼는지 확인한다. `ISAAC_SIM_PATH`는 `isaac-sim.sh`가 실제로 들어 있는 폴더를 가리켜야 한다.

```bash
cd "$ISAAC_SIM_PATH"
./post_install.sh
./isaac-sim.sh
```

처음 실행할 때 셰이더 캐시 준비로 수 분이 걸릴 수 있다. 앱을 실행한 터미널을 닫지 않는다. GUI가 열린 뒤 About 창 또는 시작 로그에서 `6.0.1`을 확인한다. 첫 실행의 빈 장면은 설치 확인용이다. 조명과 물체가 아직 없으므로 화면이 어둡다는 사실만으로 렌더러 오류라고 단정하지 않는다. [공식 workstation 설치](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_workstation.html)

## 2. Jazzy 저장소를 등록하다

Ubuntu 터미널을 하나 더 연다. 먼저 UTF-8 로케일을 확인한다.

```bash
locale
locale charmap
```

`UTF-8`이면 기존 한국어 로케일을 그대로 사용해도 된다. UTF-8이 아니면 다음처럼 이 터미널에서 사용할 로케일을 준비한다.

```bash
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
sudo add-apt-repository universe
```

[ROS 2 Jazzy의 Ubuntu deb 설치 문서](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)는 `ros2-apt-source` 패키지로 ROS 저장소를 등록하는 방식을 안내한다. 이미 등록했다면 중복 설치하지 않고 다음 절로 진행한다. 새 설치라면 아래 절차로 패키지를 받는다.

1. [공식 ros-apt-source 릴리스](https://github.com/ros-infrastructure/ros-apt-source/releases)를 연다.
2. 안정 릴리스의 Assets에서 `ros2-apt-source_`로 시작하고 `.noble_all.deb`로 끝나는 파일을 받는다. `noble`은 Ubuntu 24.04의 코드명이다.
3. 다음 명령에 다운로드한 파일의 절대 경로를 입력한다. `.deb` 내부의 배포판 표시를 먼저 확인한다.

```bash
read -r -p 'ros2-apt-source noble deb 절대 경로: ' ROS_APT_DEB
test -f "$ROS_APT_DEB" || { printf 'deb 파일을 찾지 못했다.\n'; exit 1; }
dpkg-deb --info "$ROS_APT_DEB"
sudo apt install "$ROS_APT_DEB"
sudo apt update
```

## 3. Jazzy와 실습 도구를 설치하다

```bash
sudo apt install -y ros-jazzy-desktop ros-dev-tools \
  ros-jazzy-rmw-fastrtps-cpp ros-jazzy-xacro \
  ros-jazzy-vision-msgs ros-jazzy-ackermann-msgs \
  python3-colcon-common-extensions python3-rosdep
source /opt/ros/jazzy/setup.bash
printf 'ROS 배포판: %s\n' "$ROS_DISTRO"
ros2 pkg prefix rclpy
python3 -c 'import sys; print(sys.version)'
```

`ROS_DISTRO`는 `jazzy`, `rclpy` 경로는 `/opt/ros/jazzy` 아래로 출력되어야 한다. Ubuntu 24.04의 기본 Python 계열은 3.12이며, Isaac Sim 6.0.1도 Python 3.12를 사용한다. 시스템 Python에 Isaac Sim 패키지를 억지로 추가하지 않는다. 앱의 Python은 `python.sh`, 외부 ROS 노드는 Jazzy를 source한 터미널에서 실행한다.

터미널 A에서 `ros2 run demo_nodes_cpp talker`를 실행한다. 터미널 B에서는 다음을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp listener
```

발행한 문자열을 listener가 계속 받으면 ROS 자체의 통신 경로가 동작한다. 두 터미널에서 `Ctrl+C`로 종료한다. 이것은 **ROS 단독 검사**이며 Isaac Sim Bridge 통신 검사는 아니다.

## 4. Jazzy 환경에서 Isaac Sim을 다시 실행하다

앞서 켜 둔 Isaac Sim을 종료한다. 새 터미널에서 실제 저장소 경로를 지정하고 다음 순서로 시작한다.

```bash
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"  # 실제 내려받은 경로로 수정하다
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
mkdir -p "$TUTORIAL_ROOT/artifacts/logs"
cd "$ISAAC_SIM_PATH"
set -o pipefail
./isaac-sim.sh 2>&1 | tee "$TUTORIAL_ROOT/artifacts/logs/first-launch.log"
```

이 튜토리얼은 같은 컴퓨터의 **시스템 Jazzy를 source하는 경로**를 사용한다. 내장 ROS 라이브러리용 `LD_LIBRARY_PATH`를 덧붙이지 않는다. 내장 라이브러리는 시스템 ROS를 사용하지 않는 별도 경로이며, 6.0.1에서는 `exts/isaacsim.ros2.core/jazzy/lib`에 있다. 두 경로를 한 터미널에서 혼합하면 원인 파악이 어려워진다. [공식 ROS 설치와 Bridge 설정](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html)

`Window > Extensions`에서 `isaacsim.ros2.bridge`를 검색해 상태를 확인한다. 6.0 계열에서 Bridge 기능은 core/nodes/ui/examples 구성 요소로 나뉜다. 아직 `/clock`을 발행하는 그래프를 만들지 않았으므로 `ros2 topic list`에 센서나 `/clock`이 없더라도 설치 실패라고 판단하지 않는다.

## 예상 결과와 실패 시 확인

6.0.1 GUI가 열리고 ROS talker/listener가 서로 통신해야 한다. `lib...so`나 `rclpy` 로딩 오류가 있으면 Conda가 활성화되어 있는지, 다른 ROS 배포판을 source했는지, 내장 라이브러리를 중복 추가했는지 먼저 확인한다. 새 터미널에서 이 절의 환경만 설정하고 다시 실행한다. 로그가 멈춘 위치도 함께 기록한다.

## 작은 과제

새 터미널에서 Jazzy source 전후의 `ROS_DISTRO`와 `command -v ros2`를 비교한다. 앱을 시작한 뒤 다른 터미널에서 환경변수를 바꿔도 실행 중인 앱의 환경이 변하지 않는 이유를 설명한다.

## 공식 6.0.1 자료

- [Download Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/download.html)
- [Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_workstation.html)
- [ROS 2 Installation (Default)](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html)
- [Python Environment Installation](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_python.html)

이전: [02. 설치 전 점검](02-preflight.md) · 다음: [04. GUI 첫 조작](04-gui-basics.md)
