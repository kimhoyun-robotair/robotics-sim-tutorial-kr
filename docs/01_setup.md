# 환경 구성: Ubuntu 22.04 · Humble · Gazebo 11

이 장은 **Ubuntu 22.04 LTS를 직접 설치한 컴퓨터와 Bash 터미널**을 기준으로 한다. ROS 2와 Gazebo는 배포 패키지로 설치하고, 이 저장소의 로봇·플러그인·실행 도구는 뒤에서 직접 빌드한다. 먼저 운영체제 확인 → 패키지 저장소 등록 → 설치 → 예제 빌드 순서로 진행한다.

터미널은 `Ctrl+Alt+T`로 연다. 코드 블록에서 `\`로 끝나는 줄은 다음 줄까지 이어지는 하나의 명령이다. 블록 전체를 복사해 실행하면 된다.

## 1. 사용할 Gazebo 버전 구분하기

Gazebo 생태계에는 이름이 비슷한 두 제품군이 있다.

| 이 과정에서 사용 | 이 과정의 대상이 아님 |
| --- | --- |
| Gazebo **Classic 11** | 새 Gazebo(Fortress, Garden, Harmonic 등) |
| 실행 명령 `gazebo`, `gzserver`, `gzclient` | 실행 명령 `ign gazebo` 또는 `gz sim` |
| ROS 패키지 `gazebo_ros_pkgs` | ROS 패키지 `ros_gz` |
| 플러그인 `libgazebo_ros_diff_drive.so` | Gazebo Sim system plugin |

두 제품 모두 월드 파일에 SDF를 사용하지만, ROS 연결 방식과 플러그인 API는 다르다. 인터넷 예제에서 `ros_gz_bridge`, `gz sim`, `GZ_SIM_RESOURCE_PATH`가 보인다면 이 과정의 코드에 그대로 붙이지 않는다.

Gazebo Classic은 2025년 1월에 공식 지원이 종료되었다. 자세한 수명 정책은 [Gazebo Classic 공식 문서](https://classic.gazebosim.org/)와 [ROS 2 Humble 문서](https://docs.ros.org/en/humble/)에서 확인할 수 있다. 이 과정은 Humble 기반의 기존 로봇 소프트웨어을 학습하고 유지보수하려는 목적에 적합하다.

## 2. ROS 2와 필수 패키지 설치

### 2-1. 운영체제와 문자 인코딩 확인

```bash
. /etc/os-release
printf '%s %s\n' "$NAME" "$VERSION_ID"
locale charmap
```

첫 출력은 `Ubuntu 22.04`, 두 번째는 `UTF-8`이어야 한다. `UTF-8`이면 한국어 로캘을 그대로 사용해도 된다. `ANSI_X3.4-1968`처럼 다른 값이면 다음을 실행해 UTF-8을 준비한다.

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
locale charmap
```

이 `export` 설정은 현재 터미널에 적용된다. 새 터미널에서도 `locale charmap`으로 UTF-8인지 확인한다.

### 2-2. ROS 2 패키지 저장소 등록

ROS 패키지는 Ubuntu 기본 저장소에 모두 들어 있지 않다. 아래 과정은 [Humble 공식 Ubuntu 설치 절차](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)의 저장소 등록 방법을 따른다. 이미 ROS 2를 설치한 컴퓨터에서는 `apt policy ros-humble-desktop`에 설치 후보 버전이 나오는지 확인하고 2-3으로 넘어갈 수 있다.

```bash
sudo apt update
sudo apt install -y software-properties-common curl python3
sudo add-apt-repository -y universe
```

공식 `ros2-apt-source` 패키지는 ROS 패키지 저장소 주소와 서명 키를 등록한다. 아래 명령은 현재 릴리스 번호를 조회한 뒤 **Ubuntu 22.04(Jammy)용** 패키지를 내려받아 설치한다.

```bash
humble_apt_source_version=$(curl --fail --silent --show-error \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["tag_name"])')
printf 'ros2-apt-source version: %s\n' "$humble_apt_source_version"
curl --fail --location --output /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${humble_apt_source_version}/ros2-apt-source_${humble_apt_source_version}.jammy_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
apt policy ros-humble-desktop
```

릴리스 번호가 비었거나 다운로드가 실패했다면 다음 명령으로 넘어가지 않는다. 네트워크 연결과 공식 설치 페이지를 확인한다. 마지막 출력의 `Candidate`가 `(none)`이면 아직 ROS 패키지를 설치할 수 없는 상태다.

### 2-3. ROS 2와 실습 도구 설치

처음 설치한 Ubuntu 22.04라면 먼저 기본 패키지를 업데이트한다. 공식 문서는 오래된 `systemd`·`udev` 패키지를 업데이트한 뒤 ROS 2를 설치하도록 안내한다. 다음 명령에서 변경 목록을 확인한 뒤 진행하고, 재부팅을 안내하면 재부팅한다.

```bash
sudo apt upgrade
```

이제 실습에 필요한 패키지를 설치한다.

```bash
sudo apt update
sudo apt install -y \
  git build-essential cmake ripgrep \
  liburdfdom-tools python3-venv \
  python3-colcon-common-extensions python3-rosdep \
  ros-humble-desktop \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-xacro \
  ros-humble-joint-state-publisher-gui \
  ros-humble-teleop-twist-keyboard \
  ros-humble-rqt-image-view \
  ros-humble-rviz-imu-plugin \
  ros-humble-tf2-tools
```

각 패키지의 역할은 다음과 같다.

- `ros-humble-desktop`: RViz, `robot_state_publisher`, 기본 메시지와 도구
- `ros-humble-gazebo-ros-pkgs`: Gazebo Classic 실행·모델 생성 API와 ROS 센서·구동 플러그인
- `ros-humble-xacro`: Xacro의 변수·매크로를 풀어 URDF XML로 변환
- `teleop-twist-keyboard`: `geometry_msgs/Twist` 키보드 명령 송신
- `tf2-tools`: TF 트리 진단 도구
- `rqt-image-view`: 카메라 영상을 직접 확인
- `rviz-imu-plugin`: IMU 자세를 RViz의 축·화살표로 표시
- `ripgrep`: 문서의 `rg` 진단 명령에서 토픽·라이브러리 이름을 빠르게 검색
- `liburdfdom-tools`: 전개한 URDF를 `check_urdf`로 구문·트리 검사

### 2-4. 의존성 관리 도구 초기화

`rosdep`은 각 패키지의 `package.xml`을 읽고 필요한 시스템 패키지를 설치하는 도구다. 초기화 파일이 없을 때만 `rosdep init`을 실행하고, 패키지 목록 갱신은 현재 사용자로 실행한다.

```bash
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update --rosdistro humble
```

## 3. 설치 결과 확인

새 터미널을 열고 ROS 환경을 읽는다.

```bash
source /opt/ros/humble/setup.bash
echo "$ROS_DISTRO"
gazebo --version
ros2 pkg prefix gazebo_ros
ros2 pkg prefix gazebo_plugins
```

기대 결과는 `humble`, `Gazebo multi-robot simulator, version 11.x`, 그리고 두 ROS 패키지의 설치 경로이다. `gazebo --version` 명령을 찾지 못하면 `ros-humble-gazebo-ros-pkgs` 설치 여부를 다시 확인한다.

GUI와 렌더러까지 간단히 시험한다.

```bash
gazebo --verbose
```

빈 월드가 열리면 창을 닫고 터미널에서 `Ctrl+C`로 실행이 끝났는지 확인한다. VM이나 원격 데스크톱에서 검은 화면이 보이면 먼저 소프트웨어 렌더링으로 원인을 분리할 수 있다.

```bash
LIBGL_ALWAYS_SOFTWARE=1 gazebo --verbose
```

이 설정은 진단용이다. 정상 GPU 환경에서 항상 켜 두면 카메라와 LiDAR 렌더링이 느려질 수 있다.

## 4. Humble 브랜치 받기

```bash
cd ~
git clone --branch Humble --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd robotics-sim-tutorial-kr
git branch --show-current
```

마지막 출력은 반드시 `Humble`이어야 한다. 이 과정에서는 다른 브랜치로 전환하지 않는다.

홈 폴더에 이미 같은 이름의 저장소가 있다면 기존 작업을 덮어쓰지 말고 아래처럼 별도 폴더에 받는다.

```bash
cd ~
git clone --branch Humble --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git \
  robotics-sim-tutorial-kr-humble
```

이 방법을 선택했다면 이후 모든 명령의 `~/robotics-sim-tutorial-kr`를 `~/robotics-sim-tutorial-kr-humble`로 바꾼다. 아래 설명은 기본 폴더명을 기준으로 계속 진행한다.

## 5. 의존성 설치와 빌드

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash

rosdep install \
  --from-paths src \
  --ignore-src \
  --rosdistro humble \
  -r -y

colcon build \
  --symlink-install \
  --event-handlers console_direct+

source install/setup.bash
```

`rosdep` 마지막에 `All required rosdeps installed successfully`가 나타나고 `colcon` 요약에 실패한 패키지가 없어야 한다. 빌드에 실패했다면 환경 설정을 읽어도 실패한 패키지를 실행할 수 없으므로 첫 오류부터 해결한다.

`--symlink-install`은 설치 파일 일부를 원본과 연결해 수정 내용을 쉽게 반영하도록 하는 옵션이다. C++ 코드, `CMakeLists.txt`, `setup.py`를 수정하거나 설치할 파일을 추가했으면 다시 빌드한다. 파일의 설치 방식은 패키지마다 다르므로 launch·URDF·설정을 수정한 뒤에도 재빌드하고 시뮬레이션을 다시 실행하면 변경 여부를 확실히 확인할 수 있다.

기본 실습 패키지 네 개가 보이는지 확인한다. 전체 빌드에는 F1TENTH와 Velodyne 패키지도 포함되므로 빌드 패키지 수는 네 개보다 많다.

```bash
ros2 pkg list | rg '^gazebo_tutorial_'
```

예상 패키지는 다음과 같다.

```text
gazebo_tutorial_bringup
gazebo_tutorial_description
gazebo_tutorial_plugins
gazebo_tutorial_tools
```

## 6. 터미널마다 source하기

ROS 2 실습에서는 Gazebo, teleop, 토픽 진단을 서로 다른 터미널에서 실행한다. **모든 새 터미널**에서 아래 두 줄을 실행한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
```

원한다면 정확한 경로를 확인한 뒤 `~/.bashrc`에 추가할 수 있다. 여러 ROS 배포판을 함께 쓰는 컴퓨터라면 자동 source보다 터미널별 수동 source가 안전하다.

`source`는 설정 스크립트를 현재 터미널에 읽어 패키지·플러그인 경로를 등록하는 명령이다. 순서는 **기본 ROS 환경 → 현재 워크스페이스**이다. 순서가 맞는지는 실제 패키지 경로로 확인한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash

ros2 pkg prefix gazebo_ros
ros2 pkg prefix gazebo_tutorial_description
echo "$AMENT_PREFIX_PATH" | tr ':' '\n'
```

첫 경로는 `/opt/ros/humble` 아래를, 두 번째 경로는 현재 워크스페이스의 `install/` 아래를 가리켜야 한다. 다른 워크스페이스 경로가 먼저 나온다면 새 터미널에서 이 두 환경만 순서대로 읽는다.

## 7. 첫 통합 검사

**터미널 1**에서 모델을 실행한다. GUI를 끄더라도 모델 생성·물리 계산·ROS 토픽 발행은 계속 진행된다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py gui:=false rviz:=false
```

로그에 모델 생성 성공 메시지가 나타나면 이 터미널을 그대로 두고 **터미널 2**에서 데이터를 확인한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 topic list | sort
ros2 topic echo /clock --once
ros2 topic echo /odom --once
ros2 topic echo /joint_states --once
```

`/clock`, `/odom`, `/tf`, `/joint_states`가 보이고 각 `echo`가 메시지 한 개를 출력한 뒤 종료되면 통신이 연결된 것이다. 이어서 주기와 좌표 변환을 하나씩 확인한다.

```bash
ros2 topic hz /odom
```

주기가 몇 번 출력되면 `Ctrl+C`로 이 명령만 종료하고 다음을 실행한다.

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

위치와 회전 값이 반복 출력되면 `Ctrl+C`로 종료한다. `/odom` 메시지의 `header.frame_id`는 `odom`, `child_frame_id`는 `base_footprint`여야 한다. 마지막으로 터미널 1에서 `Ctrl+C`를 눌러 시뮬레이션을 종료한다.

`ros2 launch`, `ros2 topic hz`, `tf2_echo`는 계속 실행되는 명령이다. 한 터미널에 붙여 넣으면 첫 명령이 끝날 때까지 다음 명령을 실행하지 않으므로, 이후 실습에서도 명령별 종료 안내를 따른다.

## 자주 만나는 설치 문제

### `Package 'gazebo_ros' not found`

현재 터미널에서 `/opt/ros/humble/setup.bash`를 source했는지 확인하고, `apt policy ros-humble-gazebo-ros-pkgs`로 설치 상태를 확인한다.

### `libgazebo_ros_*.so: cannot open shared object file`

워크스페이스의 `install/setup.bash`를 source하지 않았거나, 다른 ROS 배포판의 환경이 섞였을 가능성이 크다.

```bash
echo "$AMENT_PREFIX_PATH" | tr ':' '\n'
echo "$GAZEBO_PLUGIN_PATH" | tr ':' '\n'
```

경로에 Humble과 현재 워크스페이스만 있는지 확인한 뒤 새 터미널에서 다시 source한다.

### Gazebo가 즉시 종료됨

터미널의 첫 번째 `Err` 또는 `FATAL` 줄을 찾는다. GUI 문제인지 서버·모델 문제인지 구분하려면 `gui:=false`로 `gzserver`만 실행한다. 카메라 센서가 있는 모델은 GUI를 꺼도 렌더링 환경이 필요하므로, 센서 실습의 화면·OpenGL 오류는 [센서 장](05_sensors.md)의 안내도 확인한다. 더 자세한 진단 순서는 [문제 해결](08_debugging.md)에 정리되어 있다.
