# ROS 2 Humble × Gazebo Classic 11 튜토리얼 (한국어)

Ubuntu 22.04에서 ROS 2 Humble과 Gazebo Classic 11로 모바일 로봇을 만들고 움직여 보는 한국어 실습 과정이다. 로봇 모델을 띄운 뒤 키보드 조종, 바퀴 회전량으로 계산한 위치 추정(휠 오도메트리), 좌표 변환(TF), RViz 궤적 표시, 카메라·라이다·IMU, C++ 플러그인을 차례로 실습한다.

> 이 문서와 실행 명령은 **`Humble` 브랜치 전용**이다. 다른 브랜치의 모델·플러그인·명령을 섞어 사용하지 않는다.

문서·센서·TF를 재점검하면서 수정한 내용과 실제 Gazebo·RViz 검증 결과는 [재점검 기록](docs/11_review.md)에 정리했다.

## 실습 환경

| 항목 | 사용 환경 |
| --- | --- |
| 운영체제 | Ubuntu 22.04 LTS (Jammy) |
| ROS 2 | Humble Hawksbill |
| 시뮬레이터 | Gazebo Classic 11 (`gazebo`, `gzserver`, `gzclient`) |
| ROS 연동 | `gazebo_ros_pkgs` / `gazebo_plugins` |
| 빌드 | `colcon`, CMake, Python 3 |

Gazebo Classic의 공식 지원은 2025년 1월에 종료됐다. 이 과정은 기존 Humble 시스템을 학습하고 유지보수하는 데 맞춰져 있다. [Gazebo Classic 공식 안내](https://classic.gazebosim.org/)에서 지원 종료 정보를 확인할 수 있다.

## 처음 시작하기

**ROS 2가 처음이라면 [환경 구성](docs/01_setup.md)부터 진행한다.** Ubuntu 기본 패키지 저장소만 등록된 상태에서는 `ros-humble-*` 패키지를 설치할 수 없다. 환경 구성 문서에서 ROS 패키지 저장소 등록, 설치, `rosdep` 초기화까지 마친 뒤 아래 명령을 실행한다. 설치·빌드 시간은 인터넷 연결과 컴퓨터 성능에 따라 달라진다.

### 1. Humble 브랜치 받기와 빌드

아래 명령은 홈 폴더에 같은 이름의 저장소가 없는 경우를 기준으로 한다. 이미 다른 브랜치로 받은 저장소가 있다면 [별도 폴더에 받는 방법](docs/01_setup.md#4-humble-브랜치-받기)을 따른다.

```bash
cd ~
git clone --branch Humble --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
```

`colcon` 요약에 실패한 패키지가 없는지 확인한다. 오류가 있으면 launch를 실행하기 전에 빌드 로그의 첫 오류부터 해결한다.

### 2. 터미널 1: Gazebo와 RViz 실행

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

Gazebo에 차체·구동 바퀴 두 개·뒤쪽 보조 바퀴가 나타나고 RViz에 같은 로봇이 보이면 다음 단계로 진행한다. 이 명령은 시뮬레이션이 끝날 때까지 계속 실행되므로 터미널을 열어 둔다.

### 3. 터미널 2: 키보드로 움직이기

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

영문 입력 상태로 이 터미널을 선택한 뒤 `i`로 전진, `j`로 제자리 좌회전, `k`로 정지한다. RViz의 초록색 `/wheel_odom_path`가 주행에 따라 늘어나는지 확인한다. 끝날 때는 `k`로 정지한 뒤 터미널 2와 1에서 차례로 `Ctrl+C`를 누른다.

## 실습 바로가기

아래 launch는 **한 번에 하나씩** 실행한다. 각 실행은 같은 기본 토픽과 프레임 이름을 사용한다.

| 실습 | 실행 명령 | 확인할 결과 |
| --- | --- | --- |
| 2륜 + 보조 바퀴 | `ros2 launch gazebo_tutorial_bringup diffbot.launch.py` | 차동구동, `/odom`, TF, RViz 궤적 |
| 4륜 차동구동 | `ros2 launch gazebo_tutorial_bringup rover_diff.launch.py` | 네 바퀴 구동과 옆 미끄러짐을 동반한 회전 |
| 4륜 Ackermann | `ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py` | 앞바퀴 조향과 곡선 궤적 |
| 센서 전체 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all` | IMU, 카메라, 2D·3D 라이다 |
| 카메라만 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=cameras` | 단안·스테레오·RGB-D·어안 카메라 |
| 라이다만 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars` | LaserScan, PointCloud2 |

각 launch는 `gui:=false`, `rviz:=false`, `pause:=true`, `world:=...` 등의 인자를 지원한다. 실행 가능한 인자와 기본값은 다음 명령으로 확인한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py --show-args
```

## 미니 프로젝트: F1TENTH 시뮬레이션

기본 실습을 마쳤다면 `f1_robot_model`과 `velodyne_simulator`로 F1TENTH 크기의 차량을 실행해 본다. 앞바퀴 조향, ROS 2 제어 명령, Velodyne 3D 라이다를 하나의 차량에서 연결하는 실습이다. 준비 과정과 조종 방법은 [프로젝트 소개](F1TENTH.md)와 [사용 안내](F1TENTH_USERGUIDE.md)에 있다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install --packages-up-to f1_robot_model velodyne_simulator
source install/setup.bash
ros2 launch f1_robot_model display.launch.py
```

이전 Gazebo 실습을 종료하고 실행한다. 창이 열린 뒤에는 사용 안내의 별도 조종 터미널을 준비한다.

## 학습 순서

1. [환경 구성](docs/01_setup.md)
2. [URDF·Xacro·SDF 이해](docs/02_urdf_xacro_sdf.md)
3. [2륜 로봇 실습](docs/03_diffbot.md)
4. [4륜 로버 실습](docs/04_rover.md)
5. [Gazebo 센서와 RViz](docs/05_sensors.md)
6. [URDF 기반 TF와 휠 오도메트리 궤적](docs/06_tf_rviz.md)
7. [C++ Gazebo 플러그인 만들기](docs/07_custom_plugin.md)
8. [문제 해결과 검증](docs/08_debugging.md)
9. [다음 단계와 설계 원칙](docs/09_next_steps.md)
10. [명령·토픽·프레임 참고표](docs/10_reference.md)

## 저장소 구성

| 경로 (`ros2_ws/src/` 기준) | 내용 |
| --- | --- |
| `gazebo_tutorial_description/` | URDF/Xacro 로봇·센서 모델 |
| `gazebo_tutorial_bringup/` | Gazebo·모델 생성·RViz 실행, 월드·설정 파일 |
| `gazebo_tutorial_tools/` | Odom → Path, Ackermann 휠 오도메트리 노드 |
| `gazebo_tutorial_plugins/` | Gazebo Classic C++ ModelPlugin |
| `f1_robot_model/` | F1TENTH 차량·월드·실행 파일 |
| `velodyne_simulator/` | Velodyne 모델·Gazebo 센서 플러그인 |

문서 사이트를 로컬에서 보려면 새 터미널에서 다음을 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-docs.txt
mkdocs serve
```

브라우저에서 `http://127.0.0.1:8000`을 연다. 문서 서버는 `Ctrl+C`로 종료한다.

## 라이선스

이 튜토리얼에서 작성한 코드와 문서는 [Apache License 2.0](LICENSE)을 따른다. 포함된 Velodyne 코드는 해당 디렉터리의 BSD 라이선스를 따르며, F1 차량 모델·메시의 출처와 권리 표시는 [원본과 수정 범위](ros2_ws/src/f1_robot_model/UPSTREAM.md)에 정리했다.
