# ROS 2 Humble × Gazebo Classic 11 튜토리얼 (한국어)

이 브랜치는 Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11을 기준으로 모바일 로봇 시뮬레이션을 처음부터 끝까지 실습하는 한국어 과정이다. 단순히 모델을 화면에 띄우는 데서 멈추지 않고, 키보드 조종, wheel odometry, TF, RViz 궤적, 카메라·LiDAR·IMU, 그리고 C++ 커스텀 Gazebo 플러그인까지 하나의 워크스페이스에서 재현한다.

> **브랜치 안내**
> 이 내용은 `Humble` 브랜치 전용이다. `main`은 Jazzy/Gazebo Harmonic 과정이므로 이 브랜치의 명령과 섞어 사용하지 않는다.

## 지원 환경

| 항목 | 검증 기준 |
| --- | --- |
| 운영체제 | Ubuntu 22.04 LTS (Jammy) |
| ROS 2 | Humble Hawksbill |
| 시뮬레이터 | Gazebo Classic 11 (`gazebo`, `gzserver`, `gzclient`) |
| ROS 연동 | `gazebo_ros_pkgs` / `gazebo_plugins` |
| 빌드 | `colcon`, CMake, Python 3 |

Gazebo Classic은 2025년 1월에 공식 지원이 종료된 레거시 제품이다. 이 과정은 기존 Humble 시스템을 학습·유지보수하는 데 사용한다. 신규 프로젝트라면 최신 ROS 2와 새 Gazebo 조합도 함께 검토한다.

## 5분 시작

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake git ripgrep \
  liburdfdom-tools python3-venv \
  ros-humble-desktop \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-rviz-imu-plugin \
  ros-humble-xacro \
  ros-humble-teleop-twist-keyboard \
  python3-colcon-common-extensions \
  python3-rosdep

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update --rosdistro humble

cd ~
git clone --branch Humble --single-branch \
  https://github.com/kimhoyun-robotair/gazebo-sim-tutorial-kr.git
cd gazebo-sim-tutorial-kr/ros2_ws

source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
```

첫 번째 로봇을 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

새 터미널에서 같은 환경을 source한 뒤 키보드 조종을 시작한다.

```bash
source /opt/ros/humble/setup.bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

RViz의 `Path` 표시에는 `/wheel_odom_path`를 사용하고, Gazebo 플러그인이 계산한 odometry에는 `/odom`을 사용한다.

## 실습 바로가기

| 실습 | 실행 명령 | 핵심 결과 |
| --- | --- | --- |
| 2륜 + caster | `ros2 launch gazebo_tutorial_bringup diffbot.launch.py` | DiffDrive, `/odom`, TF, RViz Path |
| 4륜 skid/differential | `ros2 launch gazebo_tutorial_bringup rover_diff.launch.py` | 네 바퀴 구동과 skid steering |
| 4륜 Ackermann | `ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py` | 조향 기구, Ackermann 궤적 |
| 센서 전체 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all` | IMU, 카메라, 2D/3D LiDAR |
| 카메라만 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=cameras` | mono, stereo, RGBD, fisheye |
| LiDAR만 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars` | LaserScan, PointCloud2 |

각 launch는 `gui:=false`, `rviz:=false`, `pause:=true`, `world:=...` 같은 인자를 지원한다. 정확한 인자 목록은 다음 명령으로 확인한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py --show-args
```

## 학습 순서

1. [환경 구성](docs/01_setup.md)
2. [URDF·Xacro·SDF 이해](docs/02_urdf_xacro_sdf.md)
3. [2륜 로봇 실습](docs/03_diffbot.md)
4. [4륜 rover 실습](docs/04_rover.md)
5. [Gazebo 센서와 RViz](docs/05_sensors.md)
6. [URDF 기반 TF와 wheel odom 궤적](docs/06_tf_rviz.md)
7. [C++ 커스텀 Gazebo 플러그인](docs/07_custom_plugin.md)
8. [문제 해결과 검증](docs/08_debugging.md)
9. [다음 단계와 설계 원칙](docs/09_next_steps.md)
10. [명령·토픽·프레임 참고표](docs/10_reference.md)

## 저장소 구성

```text
ros2_ws/src/
├── gazebo_tutorial_description/  # URDF/Xacro 로봇과 센서 모델
├── gazebo_tutorial_bringup/      # Gazebo·spawn·RViz 통합 launch/world/config
├── gazebo_tutorial_tools/        # Odom → Path, Ackermann wheel odom 노드
└── gazebo_tutorial_plugins/      # Gazebo Classic C++ ModelPlugin
```

문서 사이트를 로컬에서 보려면 저장소 루트에서 다음을 실행한다.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

## 라이선스

코드와 문서는 [Apache License 2.0](LICENSE)을 따른다.
