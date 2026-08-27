# 환경 구성: Ubuntu 22.04 · Humble · Gazebo 11

이 장은 **Ubuntu 22.04 LTS**의 네이티브 설치를 기준으로 합니다. ROS 2 Humble의 Tier 1 바이너리와 Gazebo Classic 11을 함께 설치하면 이 저장소의 예제를 별도 소스 빌드 없이 시작할 수 있습니다.

## 1. 이름부터 구분하기

Gazebo 생태계에는 이름이 비슷한 두 제품군이 있습니다.

| 이 과정에서 사용 | 이 과정의 대상이 아님 |
| --- | --- |
| Gazebo **Classic 11** | 새 Gazebo(Fortress, Garden, Harmonic 등) |
| 실행 명령 `gazebo`, `gzserver`, `gzclient` | 실행 명령 `ign gazebo` 또는 `gz sim` |
| ROS 패키지 `gazebo_ros_pkgs` | ROS 패키지 `ros_gz` |
| 플러그인 `libgazebo_ros_diff_drive.so` | Gazebo Sim system plugin |

두 제품은 world 파일에 SDF를 쓴다는 점만 비슷할 뿐, ROS 연결 방식과 플러그인 ABI가 다릅니다. 인터넷 예제에서 `ros_gz_bridge`, `gz sim`, `GZ_SIM_RESOURCE_PATH`가 보인다면 이 과정의 코드에 그대로 붙이지 마세요.

Gazebo Classic은 2025년 1월에 공식 지원이 종료되었습니다. 자세한 수명 정책은 [Gazebo Classic 공식 문서](https://classic.gazebosim.org/)와 [ROS 2 Humble 문서](https://docs.ros.org/en/humble/)에서 확인할 수 있습니다. 이 과정은 Humble 기반의 기존 로봇 스택을 학습하고 유지보수하려는 목적에 적합합니다.

## 2. ROS 2와 필수 패키지 설치

ROS 2 Humble이 아직 없다면 먼저 [공식 Ubuntu 설치 절차](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)를 따라 apt 저장소를 등록하세요. 그다음 다음 패키지를 설치합니다.

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

각 패키지의 역할은 다음과 같습니다.

- `ros-humble-desktop`: RViz, `robot_state_publisher`, 기본 메시지와 도구
- `ros-humble-gazebo-ros-pkgs`: Gazebo Classic 실행·spawn API와 ROS 센서/구동 플러그인
- `ros-humble-xacro`: Xacro를 URDF XML로 전개
- `teleop-twist-keyboard`: `geometry_msgs/Twist` 키보드 명령 송신
- `tf2-tools`: TF tree 진단 도구
- `rqt-image-view`: 카메라가 실제로 영상을 publish하는지 빠르게 확인
- `rviz-imu-plugin`: IMU orientation을 RViz의 축/화살표로 시각화
- `ripgrep`: 문서의 `rg` 진단 명령에서 토픽·라이브러리 이름을 빠르게 검색
- `liburdfdom-tools`: 전개한 URDF를 `check_urdf`로 구문·트리 검사

`rosdep`을 처음 쓰는 시스템에서만 초기화합니다. 이미 초기화되어 있다는 메시지는 오류가 아닙니다.

```bash
sudo rosdep init
rosdep update --rosdistro humble
```

## 3. 설치 결과 확인

새 터미널을 열고 ROS 환경을 읽습니다.

```bash
source /opt/ros/humble/setup.bash
echo "$ROS_DISTRO"
gazebo --version
ros2 pkg prefix gazebo_ros
ros2 pkg prefix gazebo_plugins
```

기대 결과는 `humble`, `Gazebo multi-robot simulator, version 11.x`, 그리고 두 ROS 패키지의 설치 경로입니다. `gazebo --version`이 없으면 `ros-humble-gazebo-ros-pkgs` 설치 여부를 다시 확인하세요.

GUI와 렌더러까지 간단히 시험합니다.

```bash
gazebo --verbose
```

빈 world가 열리면 종료합니다. VM이나 원격 데스크톱에서 검은 화면이 보이면 먼저 소프트웨어 렌더링으로 원인을 분리할 수 있습니다.

```bash
LIBGL_ALWAYS_SOFTWARE=1 gazebo --verbose
```

이 설정은 진단용입니다. 정상 GPU 환경에서 항상 켜 두면 카메라와 LiDAR 렌더링이 느려질 수 있습니다.

## 4. Humble 브랜치 받기

```bash
cd ~
git clone --branch Humble --single-branch \
  https://github.com/kimhoyun-robotair/gazebo-sim-tutorial-kr.git
cd gazebo-sim-tutorial-kr
git branch --show-current
```

마지막 출력이 반드시 `Humble`이어야 합니다. `main`은 Jazzy/Gazebo Harmonic용이라 이 과정과 호환되지 않습니다.

## 5. 의존성 설치와 빌드

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
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

`--symlink-install`은 Python, launch, URDF, RViz 설정을 고친 뒤 매번 복사 설치하지 않아도 되게 합니다. C++ 플러그인을 수정한 경우에는 다시 `colcon build`해야 합니다.

패키지 네 개가 보이는지 확인합니다.

```bash
ros2 pkg list | grep '^gazebo_tutorial_'
```

예상 패키지는 다음과 같습니다.

```text
gazebo_tutorial_bringup
gazebo_tutorial_description
gazebo_tutorial_plugins
gazebo_tutorial_tools
```

## 6. 터미널마다 source하기

ROS 2 실습에서는 Gazebo, teleop, 토픽 진단을 서로 다른 터미널에서 실행합니다. **모든 새 터미널**에서 아래 두 줄을 실행하세요.

```bash
source /opt/ros/humble/setup.bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
```

원한다면 정확한 경로를 확인한 뒤 `~/.bashrc`에 추가할 수 있습니다. 여러 ROS 배포판을 함께 쓰는 컴퓨터라면 자동 source보다 터미널별 수동 source가 안전합니다.

## 7. 첫 통합 검사

GUI 없이 20초 동안 실행하면 모델 spawn과 플러그인 로딩을 빠르게 확인할 수 있습니다.

```bash
timeout --signal=INT 20s \
  ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  gui:=false rviz:=false
```

다른 터미널에서 실행 중인 동안 다음을 확인합니다.

```bash
ros2 topic list | sort
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_footprint
```

`/clock`, `/odom`, `/tf`, `/joint_states`가 보이고 TF 값이 출력되면 환경 구성은 끝났습니다. 다음 장에서 모델 파일의 각 요소가 왜 필요한지 살펴봅니다.

## 자주 만나는 설치 문제

### `Package 'gazebo_ros' not found`

현재 터미널에서 `/opt/ros/humble/setup.bash`를 source했는지 확인하고, `apt policy ros-humble-gazebo-ros-pkgs`로 설치 상태를 확인합니다.

### `libgazebo_ros_*.so: cannot open shared object file`

워크스페이스의 `install/setup.bash`를 source하지 않았거나, 다른 ROS 배포판의 환경이 섞였을 가능성이 큽니다.

```bash
echo "$AMENT_PREFIX_PATH" | tr ':' '\n'
echo "$GAZEBO_PLUGIN_PATH" | tr ':' '\n'
```

경로에 Humble과 현재 워크스페이스만 있는지 확인한 뒤 새 터미널에서 다시 source합니다.

### Gazebo가 즉시 종료됨

터미널의 첫 번째 `Err` 또는 `FATAL` 줄을 찾으세요. GUI 문제인지 서버/모델 문제인지 구분하려면 `gui:=false`로 `gzserver`만 실행합니다. 더 자세한 진단 순서는 [문제 해결](08_debugging.md)에 정리되어 있습니다.
