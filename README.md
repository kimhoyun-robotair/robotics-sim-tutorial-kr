# Gazebo Sim 튜토리얼 (한국어)

Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic 조합에서 Gazebo Sim을 처음 실행하는 단계부터 ROS 2 연동, 센서, 주행 제어, System Plugin, 자동화 테스트까지 학습하는 실행 중심 튜토리얼이다.

이 저장소의 `Jazzy` 브랜치는 ROS 2 Jazzy와 Gazebo Harmonic 전용 과정이다. 본문에서는 `tutorial_bot`을 한 단계씩 확장한다. 마지막에는 [Gazebo Harmonic Rover 파이널 프로젝트](docs/07_final-project/index.md)에서 4륜 로버와 F1Tenth 차량으로 센서·주행·지도 작성·자율주행을 실습한다.

```text
SDF world → URDF/Xacro 로봇 → 주행·센서 → ros_gz bridge
→ TF·RViz·ros2_control·Nav2 → C++ System Plugin·headless test·CI
```

## 지원 환경

| 항목 | 본편 기준 |
| --- | --- |
| 운영체제 | Ubuntu 24.04 LTS (Noble) |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (`gz sim` 8 계열) |
| SDFormat | 14 계열 |
| 테스트 대상 아키텍처 | amd64 |
| 렌더링 | 화면 없이 센서 영상을 생성하는 실행 방식과 소프트웨어 렌더링을 지원한다. GUI/RViz 확인 절차도 각 실습에 안내한다. |

환경 조합과 검증 범위는 [지원 환경과 호환성](docs/02_getting-started/00_compatibility.md)에서 확인한다. 테스트를 제공한다는 사실과 해당 코드의 실행이 통과했다는 사실은 구분한다. 최근 점검에서 실제로 확인한 항목은 [Jazzy 점검 기록](docs/06_reference/04_jazzy-audit.md)에 정리한다.

## 첫 시뮬레이션 실행하기

먼저 [Jazzy 환경 설치](docs/02_getting-started/02_installation-jazzy.md)를 마친다. 다음은 저장소를 처음 받는 경우다. 아래 문서들은 `~/robotics-sim-tutorial-kr`에 받았다고 가정한다. 다른 경로에 받았다면 `cd` 경로를 바꾼다.

```bash
git clone --single-branch --branch Jazzy \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git \
  ~/robotics-sim-tutorial-kr
cd ~/robotics-sim-tutorial-kr
git branch --show-current  # Jazzy
```

ROS 2 환경과 설치된 Gazebo 조합을 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
test "$ROS_DISTRO" = jazzy
gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
```

첫 world는 ROS 2 workspace를 빌드하지 않아도 실행할 수 있다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

첫 명령은 SDF 문법과 참조를 검사한다. 오류가 없으면 두 번째 명령으로 시뮬레이터와 화면을 실행한다. 바닥과 상자가 보이면 첫 실행에 성공한 것이다. 터미널에서 `Ctrl+C`를 눌러 종료한다.

## 전체 ROS 2 예제 빌드

설치가 끝난 뒤 workspace 의존성을 설치하고 모든 예제를 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/robotics-sim-tutorial-kr/examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

빌드가 끝나면 같은 터미널에서 로봇·제어기·센서 브리지를 함께 실행한다. 다음 명령은 Gazebo 화면과 RViz를 연다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  gui:=true rviz:=true nav2:=false
```

시뮬레이터는 켜 둔다. 새 터미널에서 ROS 2 기본 환경과 방금 빌드한 패키지 환경을 불러온 뒤 토픽을 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/robotics-sim-tutorial-kr
source examples/ros2_ws/install/setup.bash
ros2 topic list
ros2 topic echo /odom --once
ros2 topic echo /scan --once --field header --qos-reliability best_effort
```

`/odom`에 로봇 위치가 나오고 `/scan`의 `frame_id`가 `lidar_link`이면 ROS 2까지 데이터가 전달된 것이다. RViz에서 스캔이 로봇과 맞게 놓이는지는 [TF·RViz 실습](docs/04_intermediate/06-tf-rviz.md) 순서대로 확인한다. 화면 없는 서버에서는 launch 인자를 `gui:=false rviz:=false`로 바꾼다.

## 파이널 프로젝트

[Gazebo_Harmonic_Rover](https://github.com/kimhoyun-robotair/Gazebo_Harmonic_Rover)의 세 패키지를 이 저장소 안에서 빌드하도록 이식했다.

| 패키지 | 실습 |
| --- | --- |
| `simple_rover` | 4륜 주행, 2D/3D LiDAR, RGB-D, IMU, GPS, 지도 작성과 Nav2 |
| `f1tenth_sim` | 앞바퀴 조향 방식의 차량 주행 |
| `nav2_programming` | 목표 위치와 여러 경유점으로 이동하는 Python 예제 |

위의 전체 빌드를 마쳤다면 다음 명령으로 시작한다.

```bash
ros2 launch simple_rover spawn_robot.launch.py
```

기본 월드는 저장소에 포함되어 있다. 외부 모델을 별도로 받지 않아도 첫 실습을 시작할 수 있다. 설치부터 센서 확인, 지도 저장, 경로 주행까지는 [파이널 프로젝트 안내](docs/07_final-project/index.md)를 따른다. 원본 커밋·라이선스·달라진 기능은 [이식 기록](docs/07_final-project/05_porting-notes.md)에 정리했다.

## 문서 보기

```bash
cd ~/robotics-sim-tutorial-kr
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-docs.txt
mkdocs serve
```

브라우저에서 터미널에 표시된 주소를 연다. 링크와 코드 블록을 포함한 정적 빌드를 엄격하게 검사하려면 다음 명령을 실행한다.

```bash
mkdocs build --strict
```

## 저장소 구성

- `docs/`는 MkDocs 문서 원본을 보관한다.
- `docs/assets/`는 문서에서 사용하는 그림과 그림 목록을 보관한다.
- `examples/gazebo/`는 ROS 2 없이 실행하는 SDF 예제를 보관한다.
- `examples/ros2_ws/`는 ROS 2와 Gazebo를 함께 사용하는 작업 공간이다.
- `scripts/`는 문서·코드 검사와 시뮬레이터 실행 검사를 보관한다.

전체 과정의 정적·실행 증거는 `scripts/run_course_matrix.py`와 `scripts/audit_course_evidence.py`로 검사한다. 실행을 건너뛴 결과는 통과로 인정하지 않는다.

외부 자료를 이식한 파이널 프로젝트는 원본의 라이선스와 저작권 표시를 보존한다.

## 라이선스

이 저장소는 [Apache License 2.0](LICENSE)을 따른다.
