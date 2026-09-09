# Isaac Sim 6.0.1 한국어 튜토리얼

**Ubuntu 24.04 LTS · ROS 2 Jazzy · Isaac Sim 6.0.1 · x86_64**

Isaac Sim을 처음 실행하는 사람을 위한 **40단계 과정**이다. 마우스로 화면을 움직이는 방법부터 USD, Python 자동화, Extension 제작, 관절 로봇, RGBD·LiDAR·IMU, ROS 2 연결과 최종 회귀검사 프로젝트까지 다룬다. 과정 중 **중간 프로젝트 8개**를 완성한다. NVIDIA의 **6.0.1 공식 문서**를 확인하여 새 실습으로 구성했다. 공식 문서의 전체 번역은 아니다.

이 브랜치의 정확한 이름은 **`IsaacSim6.0.1`**이다. 기존 5.1 사용자는 [5.1.0 → 6.0.1 릴리스·이관 설명](docs/release-notes-5.1-to-6.0.1.md)을 먼저 읽는다. 버전 번호만 바꾸는 대신 센서 API, ROS Extension 분리와 import 방식의 변경을 반영했다.

> **검증 상태:** Python 문법, 문서 연결, URDF·설정 파일과 실패 감지 함수는 CPU 환경에서 검사했다. 작성 환경에 Isaac Sim·ROS 2·NVIDIA GPU가 없어 **실제 물리·렌더링·센서·ROS 실행 검증은 수행하지 못했다.** GPU 검사 스크립트와 합격 기준을 함께 제공한다. 상세 결과는 [검증 보고서](docs/validation.md)에 기록한다. 로봇 붕괴·노이즈·블랙아웃이 발생하지 않는다고 보장하지 않는다.

## 처음 시작하다

아래 clone은 이 브랜치만 내려받는다. 아직 Isaac Sim을 설치하지 않았다면 1~3단계부터 읽는다.

```bash
sudo apt update
sudo apt install git
cd "$HOME"
git clone --single-branch --branch IsaacSim6.0.1 \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd robotics-sim-tutorial-kr
export TUTORIAL_ROOT="$PWD"
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
git branch --show-current
```

마지막 출력은 `IsaacSim6.0.1`이어야 한다. 같은 이름의 폴더가 이미 있으면 clone 명령 끝에 새 폴더 이름을 지정한다. `$TUTORIAL_ROOT`는 저장소 루트, `$ISAAC_SIM_PATH`는 `isaac-sim.sh`와 `python.sh`가 있는 설치 폴더이다. 새 터미널에서는 필요한 변수를 다시 설정한다. 예제 결과는 `artifacts/`에 저장하며 Git에 포함하지 않는다.

## 학습 순서

번호 순서로 진행한다. 코드를 실행하기 전에 **터미널용인지, Script Editor용인지, standalone 파일용인지** 확인한다. 각 문서에는 목표·준비·구체 절차·예상 결과·문제 진단·과제가 있다. 중간 프로젝트는 09·15·17·22·27·33·36·38단계이며 최종 심화 프로젝트는 40단계이다.

| 단계 | 실습 |
|---:|---|
| 01 | [# 01. Isaac Sim으로 무엇을 만들 수 있는가](docs/lessons/01-platforms.md) |
| 02 | [# 02. 설치 전에 컴퓨터와 저장 경로를 점검하다](docs/lessons/02-preflight.md) |
| 03 | [# 03. Ubuntu 24.04에 Isaac Sim 6.0.1과 ROS 2 Jazzy를 설치하다](docs/lessons/03-installation.md) |
| 04 | [# 04. GUI에서 물체를 만들고 화면을 조작하다](docs/lessons/04-gui-basics.md) |
| 05 | [# 05. Prim 계층, 좌표계, 단위를 이해하다](docs/lessons/05-transforms-units.md) |
| 06 | [# 06. 바닥, 조명, 재질로 확인하기 쉬운 장면을 만들다](docs/lessons/06-ground-light-material.md) |
| 07 | [# 07. 강체, 충돌체, 시간 간격을 설정하다](docs/lessons/07-rigid-body-physics.md) |
| 08 | [# 08. USD 레이어·참조와 URDF·Xacro·MJCF를 구분하다](docs/lessons/08-usd-composition.md) |
| 09 | [# 09. 중간 프로젝트 1 — GUI로 작은 실험실을 만들다](docs/lessons/09-project-lab.md) |
| 10 | [# 10. 물리 안정성을 점검하고 Robot Inspector를 사용하다](docs/lessons/10-stability-inspection.md) |
| 11 | [GUI, Extension, Python의 관계를 이해하기](docs/lessons/11-workflows.md) |
| 12 | [Script Editor에서 장면을 만들다](docs/lessons/12-script-editor.md) |
| 13 | [Python 파일에서 Isaac Sim을 시작하고 종료하기](docs/lessons/13-standalone.md) |
| 14 | [물리 시간과 렌더링 시간을 구분하기](docs/lessons/14-timing.md) |
| 15 | [중간 프로젝트 2 — 결과를 검사하는 낙하 실험을 만들다](docs/lessons/15-project-drop-test.md) |
| 16 | [Extension의 구조와 수명주기를 익히다](docs/lessons/16-extension-basics.md) |
| 17 | [중간 프로젝트 3 — 재사용 장면 생성 도구를 완성하기](docs/lessons/17-project-scene-extension.md) |
| 18 | [OmniGraph를 GUI와 Python에서 구성하기](docs/lessons/18-omnigraph.md) |
| 19 | [# 19. URDF를 가져오기 전에 질량과 관성부터 확인하다](docs/lessons/19-urdf-inertia.md) |
| 20 | [# 20. Articulation과 관절 Drive를 구분하다](docs/lessons/20-articulation-drives.md) |
| 21 | [# 21. 고정식 로봇의 제어 안정성을 검사하다](docs/lessons/21-manipulator-stability.md) |
| 22 | [# 22. 중간 프로젝트 4 — 단일 관절 검사용 로봇을 완성하다](docs/lessons/22-project-joint-rig.md) |
| 23 | [# 23. 카메라 좌표계와 조명을 먼저 맞추다](docs/lessons/23-camera-coordinates.md) |
| 24 | [# 24. RGB와 깊이 프레임을 수치로 검사하다](docs/lessons/24-rgbd-validation.md) |
| 25 | [# 25. RTX LiDAR의 한 바퀴 스캔을 검증하다](docs/lessons/25-rtx-lidar.md) |
| 26 | [# 26. IMU와 접촉 센서의 물리 데이터를 읽다](docs/lessons/26-imu-contact.md) |
| 27 | [# 27. 중간 프로젝트 5 — RGBD·LiDAR 센서 검사실을 만들다](docs/lessons/27-project-sensor-lab.md) |
| 28 | [# 28. 성능 저하·노이즈·블랙아웃의 원인을 나누어 찾다](docs/lessons/28-performance-diagnostics.md) |
| 29 | [# 29. Jazzy와 Isaac Sim을 연결하는 ROS 2 Bridge](docs/lessons/29-ros2-bridge.md) |
| 30 | [# 30. `/clock`, 시뮬레이션 시간, QoS](docs/lessons/30-clock-qos.md) |
| 31 | [# 31. TF, odometry, joint state와 6.0의 새 연결 구조](docs/lessons/31-tf-odometry-joints.md) |
| 32 | [# 32. 카메라와 LiDAR 데이터를 ROS로 내보내기](docs/lessons/32-ros-sensors.md) |
| 33 | [# 33. 중간 프로젝트 6 — ROS 폐루프로 목표 위치에 도달하기](docs/lessons/33-project6-ros-loop.md) |
| 34 | [# 34. 조종 명령의 제한과 timeout 정지](docs/lessons/34-command-safety.md) |
| 35 | [# 35. rosbag 기록과 공식 Nova Carter Nav2 실습](docs/lessons/35-rosbag-nav2.md) |
| 36 | [# 36. 중간 프로젝트 7 — 기록 재생과 통신 검증](docs/lessons/36-project7-replay.md) |
| 37 | [RGB와 정답 라벨을 함께 저장하다](docs/lessons/37-synthetic-data.md) |
| 38 | [중간 프로젝트 8: 조건이 기록된 검사 부품 데이터셋](docs/lessons/38-project-dataset.md) |
| 39 | [GUI 실험을 자동 실행과 검사 기록으로 옮기다](docs/lessons/39-batch-and-evidence.md) |
| 40 | [최종 심화 프로젝트: 로봇·센서·ROS 회귀검사 실험실](docs/lessons/40-capstone-regression-lab.md) |

## GUI·Extension·Python을 구분하다

GUI는 장면을 눈으로 구성하는 인터페이스이며 Extension은 기능을 로딩하는 모듈이다. Python은 Script Editor, Extension, standalone 모두에서 사용한다. 세 방식은 서로 배타적인 제품이 아니다. [작업 방식 상세 비교](docs/workflows.md)에서 같은 장면을 각 방식으로 만드는 예와 사용 시점을 설명한다.

| 파일 | 실행 위치 | 실습 |
|---|---|---|
| [01_drop_cube.py](examples/01_drop_cube.py) | Isaac Sim `python.sh` | 낙하·정착과 시간 간격 |
| [02_script_editor_scene.py](examples/02_script_editor_scene.py) | GUI Script Editor | 현재 장면 수정 |
| [tutorial.scene](extensions/tutorial.scene/config/extension.toml) | Extension Manager | 장면 도구와 UI |
| [03_robot_stability.py](examples/03_robot_stability.py) | Isaac Sim `python.sh` | 제공 URDF의 관절 검사 |
| [04_camera_check.py](examples/04_camera_check.py) | Isaac Sim `python.sh` | RGB·ideal depth 검사 |
| [05_lidar_check.py](examples/05_lidar_check.py) | Isaac Sim `python.sh` | RTX LiDAR 검사 |
| [06_ros_clock.py](examples/06_ros_clock.py) | Isaac Sim `python.sh` | Clock graph |
| [07_ros_scene.py](examples/07_ros_scene.py) | Isaac Sim `python.sh` | ROS 운동학 장면 |
| [08_dataset.py](examples/08_dataset.py) | Isaac Sim `python.sh` | RGB·분할 기록 |
| [ros_acceptance.py](scripts/ros_acceptance.py) | Jazzy 시스템 Python | 메시지·명령·자동 정지 관찰 |
| [runtime_suite.py](scripts/runtime_suite.py) | 검사 전용 Python 환경 | 물리·센서·ROS 종합 실행 |

기본 강체 실습은 PhysX를 기준으로 한다. 새 Core/Sensor API의 `experimental` 표기와 legacy API의 사용 범위는 본문에서 설명한다. 물리적 stereo depth noise와 이상적인 깊이 영상, RTX LiDAR와 물리 raycast도 구분한다. 최종 프로젝트는 독립 물리·센서·ROS 장면의 결과를 하나의 회귀검사 절차로 모은다. ROS 운동학 상자는 바퀴 접촉을 구현한 차량이 아니며 실제 이동 로봇은 35단계의 Carter/Nav2 실습에서 다룬다.

## 검사하다

GPU 없이 수행하는 검사는 다음과 같다. 실제 시뮬레이션 실행을 대신하지 않는다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_repo.py
.venv/bin/python -m unittest discover -s tests -v
```

Isaac Sim을 설치한 PC에서는 각 단계의 개별 예제를 먼저 실행한다. 마지막에는 40단계 설명에 따라 다음 명령으로 종합 검사한다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
.venv/bin/python scripts/runtime_suite.py --isaac-path "$ISAAC_SIM_PATH" \
  --with-ros --output-dir artifacts/capstone-01
```

GUI 저장·복원, 로봇 외형·관절 방향, RGB·깊이·점군의 공간 대응도 직접 확인한다. **PARTIAL·NOT_RUN·환경 없음은 PASS가 아니다.**

## 공식 자료

공식 문서 확인일은 **2026-09-09**이다. [6.0.1 시작 페이지](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/index.html), [다운로드](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/download.html), [릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/release_notes.html), [알려진 문제](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)를 기준으로 삼는다. 각 단계 끝에 실습에 사용한 공식 자료를 연결했다. `latest` 문서 대신 본 과정의 버전 문서를 확인한다.
