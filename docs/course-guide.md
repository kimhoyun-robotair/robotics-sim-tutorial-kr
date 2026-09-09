# 처음 시작하는 사람을 위한 36단계 실습 과정

Isaac Sim을 한 번도 사용하지 않았다는 전제로 시작한다. 먼저 마우스로 작은 장면을 만들고, 같은 작업을 Python으로 옮긴다. 그다음 로봇과 센서를 하나씩 추가한 뒤 ROS 2와 최종 프로젝트를 연결한다. **각 단계의 ‘완료 기준’을 확인한 뒤 다음 단계로 넘어간다.** 세부 메뉴, 전체 코드, 문제 해결은 각 단계에 연결한 본문에서 이어서 설명한다.

36단계는 순서대로 진행하는 본 과정이다. 다섯 프로젝트 중 1·2는 중간 복습, 3·4는 통합 실습, 5는 학습된 정책을 적용하는 심화 과제로 구성한다. 모든 항목을 하루에 끝낼 필요는 없다. 실패했을 때는 마지막으로 통과한 장면을 다시 열어, 방금 추가한 기능부터 살펴본다.

## 시작 전에: 파일과 터미널 준비

명령 앞의 `$`는 입력하지 않는다. 코드 블록은 오른쪽 복사 버튼으로 복사한다. `<...>`가 들어간 명령은 예시이므로 자신의 값으로 바꿔야 한다. Python 조각에 ‘Script Editor’라고 적혀 있으면 터미널에 붙이지 않는다.

| 표기 | 실행 위치 | 주요 용도 |
| --- | --- | --- |
| SIM 터미널 | 시스템 ROS를 source하지 않은 새 터미널 | `isaac-sim.sh`, 내장 Python 3.11 `python.sh` |
| ROS 터미널 | `source /opt/ros/jazzy/setup.bash`를 실행한 터미널 | Python 3.12, ROS CLI·RViz·Nav2 |
| Script Editor | Isaac Sim의 `Window > Script Editor` | 이미 실행 중인 앱의 장면 편집 |
| DOC 터미널 | 문서용 가상환경 | 문서 빌드와 정적 검사 |

먼저 SIM 터미널에서 작업 폴더를 만든다. `ISAACSIM_PATH`는 **설치 폴더**, `TUTORIAL_REPO`는 **이 저장소를 내려받은 폴더**다. 아래 clone은 처음 한 번만 실행한다. 이미 저장소가 있으면 그 폴더로 이동해 `export TUTORIAL_REPO="$PWD"`만 실행한다.

```bash
mkdir -p "$HOME/isaacsim-course"/{assets,stages,ros2_ws/src,logs,outputs}
export ISAACSIM_COURSE="$HOME/isaacsim-course"
export ISAACSIM_PATH="$HOME/isaacsim"
git clone --single-branch --branch IsaacSim5.1 \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git \
  "$HOME/isaacsim-course/tutorial"
export TUTORIAL_REPO="$HOME/isaacsim-course/tutorial"
cd "$TUTORIAL_REPO"
```

새 터미널에서는 `export`한 값이 자동으로 이어지지 않는다. 필요한 경로를 다시 설정한다. 다운로드한 원본은 `assets`, 저장한 장면은 `stages`, 측정값과 이미지는 `outputs`, 오류 기록은 `logs`에 둔다.

## 01단계 — Isaac Sim이 하는 일 이해하기

[Omniverse·Kit·Isaac Sim·Isaac Lab](01-foundations/01-ecosystem.md)을 읽는다. 로봇과 바닥을 표현하는 USD, 충돌과 관절을 계산하는 PhysX, 센서 영상을 만드는 RTX, 외부 노드와 연결하는 ROS 2 Bridge의 역할을 구분한다. 아직 Isaac Lab이나 Nucleus를 설치할 필요는 없다.

**완료 기준:** “장면은 USD에 저장하고, 로봇의 움직임은 물리 엔진이 계산하며, 외부 제어기는 ROS 메시지를 보낸다”는 흐름을 설명할 수 있다.

## 02단계 — Ubuntu와 RTX GPU 확인하기

[사전 점검](02-getting-started/01-system-requirements.md)의 OS·VRAM·Vulkan 검사부터 실행한다. `nvidia-smi`의 GPU 이름과 드라이버 버전을 로그로 남긴다. GPU가 보이지 않으면 센서 예제를 먼저 실행하지 않는다.

```bash
cat /etc/os-release
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
vulkaninfo --summary
```

**완료 기준:** Ubuntu 24.04 x86_64와 RTX GPU가 확인되고, 사용 가능한 메모리를 공식 요구사항과 비교했다.

## 03단계 — 5.1.0 설치하고 첫 창 열기

[워크스테이션 설치](02-getting-started/02-workstation-installation.md)에 따라 ZIP을 풀고 `post_install.sh`, Compatibility Checker, `isaac-sim.sh` 순서로 실행한다. 처음 셰이더를 준비할 때는 로그의 진행 여부를 살펴본다. 다른 버전의 설치 폴더에 덮어쓰지 않는다.

**완료 기준:** 시작 로그에서 5.1.0을 확인하고 GUI가 열린다. Checker 결과도 보관한다. 이전 버전 경험이 있다면 [4.x→5.0→5.1 변경사항](appendices/release-notes-4x-to-5-1.md)을 함께 읽는다.

## 04단계 — 화면에서 물체 찾고 시점 움직이기

[GUI 설명](02-getting-started/04-gui-interface.md)의 첫 실습을 따른다. `File > New`를 선택하고 Cube를 만든다. Stage에서 Cube 행을 클릭한 뒤 **마우스를 Viewport 위로 옮겨 `F`**를 누른다. 마우스 오른쪽 버튼을 누른 상태의 `W`는 시점 이동이고, 누르지 않은 상태의 `W`는 물체 이동 도구다.

**완료 기준:** Viewport, Stage, Property를 찾고, 물체를 옮기는 것과 바라보는 시점을 옮기는 것을 구분한다.

## 05단계 — 크기와 좌표를 숫자로 지정하기

[첫 장면](02-getting-started/05-first-scene-and-physics.md)에서 Cube의 한 변을 0.2 m, 중심 위치를 `(0, 0, 1)`로 정한다. Stage 단위는 미터, 위쪽은 Z축이다. 크기를 설정하는 `size`와 Transform의 `scale`을 중복 적용하지 않는다.

**완료 기준:** 20 cm 상자가 지면보다 1 m 높은 곳에 있다. 단위를 잘못 잡아 거대한 상자가 되면 물리 설정 전에 크기를 고친다.

## 06단계 — 바닥, 강체, 충돌체 추가하기

같은 장면에 Ground Plane, Physics Scene, Cube의 Rigid Body·Collider를 추가한다. Play 후 상자가 바닥에 닿는 것을 관찰하고 Stop으로 초기 위치에 돌아간다. Pause는 현재 위치에서 멈춘다는 점도 비교한다.

**완료 기준:** 상자가 바닥을 통과하지 않는다. 중심의 Z는 반 높이인 약 0.1 m 부근에 머문다. [물리 설명](03-core/03-physics-material-light-sensors.md)에서 충돌 형상 표시 방법을 확인한다.

## 07단계 — 조명과 시뮬레이션 카메라 구분하기

첫 장면에 Dome Light를 넣는다. Viewport의 편집용 조명에만 기대지 말고 Stage에 실제 Light prim이 있는지 확인한다. Perspective 시점은 작업자가 보는 화면이며, 나중에 데이터를 출력할 Camera prim과 구별한다.

**완료 기준:** Stage의 조명을 껐다 켰을 때 장면 밝기가 바뀐다. 검은 카메라 영상이 나오면 먼저 조명·카메라 방향·대상을 살펴봐야 한다는 것을 이해한다.

## 08단계 — 저장한 장면 다시 열기

Stop 후 첫 장면을 `$HOME/isaacsim-course/stages/falling_cube.usda`로 저장한다. `File > New`로 새 장면을 연 다음 저장한 파일을 다시 연다. `.usda`는 읽을 수 있는 텍스트 형식이다.

**완료 기준:** 원래 창을 닫고 다시 열어도 같은 위치에서 같은 낙하 실험을 할 수 있다. [프로젝트 1](07-projects/01-usd-physics-lab.md)의 기본 장면을 여기서 준비한다.

## 09단계 — USD의 경로와 레이어 이해하기

[USD 기초](01-foundations/02-usd-fundamentals.md)와 [USD Python 도구](01-foundations/03-usd-tools-and-python.md)를 따른다. `/World/Cube`는 파일 경로가 아니라 장면 안의 prim 경로다. 원본 레이어와 수정 레이어를 분리하고 어느 레이어의 값이 최종 적용되는지 확인한다.

**완료 기준:** 원본 에셋을 덮어쓰지 않고 별도 레이어에서 위치를 수정하며, 다시 열었을 때 수정값이 유지된다.

## 10단계 — URDF·Xacro·MJCF와 USD 비교하기

[형식 변환](01-foundations/04-format-conversion.md)의 작은 URDF부터 가져온다. 이 단계에서는 ROS 설치가 필요 없는 일반 URDF부터 사용한다. Xacro는 23단계에서 ROS를 설치한 뒤 URDF로 펼쳐 같은 실습을 반복한다. 시각 mesh가 보이는지와 collider·질량·관절이 만들어졌는지를 따로 확인한다. 변환은 모든 정보를 왕복 보존하는 작업이 아니다.

**완료 기준:** 링크 이름, 관절 축, 크기를 원본과 대조하고 변환 시 잃는 정보를 기록했다.

## 11단계 — 첫 standalone Python 실행하기

[첫 장면의 Python 실습](02-getting-started/05-first-scene-and-physics.md)을 따라 저장소의 전체 예제를 실행한다. 시스템 `python3` 대신 설치 폴더의 `python.sh`를 쓴다.

```bash
cd "$TUTORIAL_REPO"
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py
```

**완료 기준:** 유한한 횟수만큼 계산한 뒤 종료하고, 상자의 최종 높이를 확인한다. 문법 검사 통과와 실제 물리 검사 통과는 다르게 기록한다.

## 12단계 — GUI·Extension·Python 실행 방식 비교하기

[실행 방식 비교](06-developer/01-python-workflows.md)의 같은 상자 예제를 순서대로 실행한다. GUI와 Extension은 이미 켜진 Kit의 실행 루프를 사용한다. standalone Python은 `SimulationApp`을 만들고 반복 계산과 종료를 직접 관리한다. Extension도 Python으로 만들 수 있다.

**완료 기준:** Script Editor에 `SimulationApp` 생성 코드를 붙여 넣지 않고, GUI 콜백 안에 긴 `while` 루프를 넣지 않는 이유를 설명할 수 있다.

## 13단계 — 버튼이 있는 Extension 설치하기

[Extension 실습](06-developer/02-extension-and-omnigraph.md)에서 제공한 폴더를 확장 검색 경로에 등록한다. 활성화하고 장면 생성 버튼을 누른다. 비활성화한 뒤 다시 활성화해 창과 콜백이 중복되지 않는지 살펴본다.

**완료 기준:** `extension.toml`, Python 모듈, `on_startup`·`on_shutdown`의 역할을 구분하고 창을 닫아도 앱이 멈추지 않는다.

## 14단계 — Action Graph 연결하기

[GUI의 Action Graph 실습](02-getting-started/04-gui-interface.md)에서 `On Playback Tick`과 `Print Text`를 연결한다. 실행 신호와 숫자 데이터는 다른 포트로 흐른다. 출력이 빠르게 쌓이면 Pause 또는 Stop을 누른다.

**완료 기준:** Play 중에만 출력이 발생한다. 이후 ROS 그래프에서도 데이터 선뿐 아니라 실행 선을 확인한다.

## 15단계 — 공식 로봇 에셋을 장면에 배치하기

[로봇 가져오기와 설정](03-core/05-robot-import-and-setup.md)을 따라 먼저 공식 에셋 하나를 사용한다. 단순한 바닥 위에 놓고 충돌체 표시를 켠다. 로봇 바닥이 지면에 파묻히지 않도록 초기 위치를 확인한다.

**완료 기준:** 아무 명령을 주지 않아도 로봇 링크가 흩어지거나 지면 아래로 떨어지지 않는다. 이상이 있으면 제어 코드를 추가하기 전에 고친다.

## 16단계 — 관절과 제어기 초기화하기

[Articulation과 제어기](03-core/04-articulation-joints-controllers.md)에서 DOF 이름과 limit을 출력한다. `world.reset()`으로 물리 핸들을 준비한 뒤 작은 목표값부터 적용한다. 위치를 강제로 덮어쓰는 함수와 모터 목표를 보내는 함수를 구별한다.

**완료 기준:** 의도한 관절만 움직이고 limit을 넘지 않는다. 로봇이 무너지면 root·관절 연결·관성·초기 관통부터 검사한다.

## 17단계 — 이동 로봇을 저속으로 제어하기

[이동 로봇 실습](03-core/06-mobile-and-manipulator.md)에서 정지→저속 직진→정지 순서로 실행한다. 바퀴 반지름과 좌우 간격의 단위는 미터다. 좌우 바퀴 관절 이름과 회전 부호를 실제 에셋에서 확인한다.

**완료 기준:** 명령 전에는 정지하고, 명령 후 예상 방향으로 이동한다. [프로젝트 2](07-projects/02-custom-mobile-robot.md)에서 자신의 모델로 바꿔 같은 검사를 반복한다.

## 18단계 — 로봇 팔과 목표 자세 다루기

[모션 생성](03-core/07-motion-generation.md)에서 공식 팔 예제를 사용한다. 먼저 관절 제어, 다음으로 end-effector 목표 이동을 실행한다. 도달할 수 있는 가까운 목표부터 시험하고 자기 충돌과 장애물 충돌을 구별한다.

**완료 기준:** 팔이 초기 자세를 유지하고 목표에 접근한다. 빠른 제어나 집기 동작은 이 검사를 통과한 뒤 추가한다.

## 19단계 — RGB 카메라에서 한 프레임 읽기

[카메라 실습](03-core/03-physics-material-light-sensors.md)을 따라 조명이 있는 장면에서 카메라 한 개만 만든다. 대상 상자가 화면 중앙에 오도록 놓고 낮은 해상도에서 시작한다. headless여도 카메라에는 렌더링이 필요하다.

**완료 기준:** 배열 크기가 예상 해상도와 맞고 빈 배열이나 전부 검은 영상이 아니다. 준비 프레임을 기다린 뒤에도 실패하면 방향·clipping range·조명부터 확인한다.

## 20단계 — Depth와 좌표계 확인하기

같은 카메라에 depth 출력을 추가한다. [커스텀 센서](05-customization/03-custom-sensors.md)에서 광학 축과 거리 정의를 확인한다. `distance_to_image_plane`과 카메라 중심까지의 거리를 혼동하지 않는다. 배경의 무효 depth는 물체 영역과 나누어 본다.

**완료 기준:** 알려진 위치에 둔 상자까지의 깊이를 확인하고, RGB·depth가 같은 카메라 자세와 시간에서 나왔는지 기록한다.

## 21단계 — IMU와 접촉 센서 읽기

[센서 물리와 읽기 순서](05-customization/03-custom-sensors.md)에 따라 강체에 IMU를 붙인다. 먼저 정지 구간의 각속도를 확인하고, 이후 작은 움직임을 준다. 중력을 포함한 가속도와 제거한 가속도의 기대값은 다르다.

**완료 기준:** 센서 값과 timestamp가 갱신되고 NaN·Inf가 없다. 정지 시 가속도가 반드시 0이라는 잘못된 기준으로 판정하지 않는다.

## 22단계 — RTX LiDAR 데이터 확인하기

[RTX 센서 실습](03-core/03-physics-material-light-sensors.md)의 최소 장면을 사용한다. 센서 앞에 불투명한 표적을 놓고 충분한 프레임 동안 렌더링한다. 5.0과 5.1의 annotator 차이는 [변경사항](appendices/release-notes-4x-to-5-1.md)을 확인한다.

**완료 기준:** 점 수가 0보다 크고 좌표가 유한하다. 점이 없다는 이유로 무조건 노이즈를 추가하지 않는다. 프로파일·빔 방향·범위와 표적부터 살펴본다.

## 23단계 — 외부 ROS 2 Jazzy 설치하기

[ROS 설치](02-getting-started/03-ros2-jazzy-setup.md)를 따른다. SIM과 ROS 터미널을 나누고 `ROS_DOMAIN_ID`를 맞춘다. 공식 실습 workspace는 `IsaacSim-5.1.0` 태그로 받는다.

**완료 기준:** ROS 터미널에서 `ros2 --help`가 실행되며, SIM 로그에는 시스템 Python 3.12용 `rclpy` 로드 오류가 없다.

## 24단계 — Bridge와 `/clock` 연결하기

[Bridge·workspace](04-ros2/01-install-bridge-workspace.md)의 Clock 그래프를 만든다. Play하고 외부 터미널에서 아래 명령을 실행한다.

```bash
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

**완료 기준:** 시간 메시지가 도착하고 값이 진행한다. `/clock` publisher는 하나만 둔다. 빈 장면에서 토픽 목록이 비어 있는 것만으로 Bridge 실패라고 판단하지 않는다.

## 25단계 — TF와 Odometry 연결하기

[시간·TF·이동](04-ros2/02-time-tf-and-motion.md)에서 `odom`, `base_link`, 센서 frame 관계를 만든다. RViz의 Fixed Frame을 실제 TF 루트와 맞춘다. 동일한 transform을 두 publisher가 중복 발행하지 않는다.

**완료 기준:** 정지한 로봇의 TF가 튀지 않고 센서가 올바른 위치에 보인다. frame 이름의 오타와 좌표축 오류를 먼저 해결한다.

## 26단계 — ROS 명령으로 이동하기

[제어 실습](04-ros2/10-control-cookbook.md)을 따라 `/cmd_vel`의 작은 선속도부터 보낸다. 시뮬레이터 내부 제어 예제와 ROS 구독 제어기를 동시에 켜지 않는다. 종료할 때는 0 속도를 보낸다.

**완료 기준:** ROS 메시지→바퀴 제어→odometry 변화가 이어진다. 속도 명령 단절 시 멈추는지도 별도로 확인한다.

## 27단계 — ROS 센서 토픽과 QoS 확인하기

[센서 토픽 실습](04-ros2/11-sensor-topic-cookbook.md)에서 RGB, CameraInfo, depth, scan/point cloud를 하나씩 연결한다. `ros2 topic info -v`로 QoS를 보고 RViz 구독 설정을 맞춘다.

**완료 기준:** 메시지 크기·frame_id·timestamp가 맞고 RViz에서 위치가 일치한다. 화면에 점이 보이는 것과 거리값이 맞는 것을 각각 검사한다.

## 28단계 — Nav2로 첫 목표점 이동하기

[Nav2 실습](04-ros2/12-nav2-workshop.md)에서 공식 Nova Carter 장면과 그에 맞는 map·params를 쓴다. 초기 위치를 설정한 후 가까운 목표 한 개부터 보낸다. 이 샘플의 토픽 이름을 앞선 임의 로봇 이름으로 바꾸지 않는다.

**완료 기준:** localization·TF·센서가 준비된 상태에서 goal 결과가 성공이고 충돌이 없다. 단순히 launch가 켜진 것을 성공으로 기록하지 않는다.

## 29단계 — MoveIt 2로 팔의 계획과 실행 비교하기

[MoveIt 2 실습](04-ros2/13-moveit2-workshop.md)을 따라 먼저 Plan, 다음으로 Execute를 실행한다. RViz 계획 궤적과 실제 Isaac Sim 관절 상태를 함께 본다.

**완료 기준:** 계획만 성공하고 실제 팔은 멈춘 상황을 구별한다. joint 이름, 상태 토픽, command 토픽과 컨트롤러 연결을 확인한다.

## 30단계 — 환경과 센서를 자신의 구성으로 바꾸기

[환경 만들기](05-customization/02-custom-environment.md)에서 단순한 벽과 통로를 만든다. 검증된 로봇을 reference로 배치하고 센서 위치를 하나씩 변경한다. 바닥·벽의 collider와 통로 폭을 로봇 크기와 비교한다.

**완료 기준:** 환경만 바꾼 상태에서 기존 정지·저속 주행·센서 검사를 다시 통과한다. 변경 원인을 찾을 수 있도록 여러 파라미터를 한꺼번에 바꾸지 않는다.

## 31단계 — Replicator로 작은 데이터셋 만들기

[합성 데이터](06-developer/03-replicator-and-sdg.md)에서 출력 폴더와 프레임 수를 지정한다. 먼저 고정 조명·고정 자세에서 RGB와 라벨을 저장하고, 그다음 한 종류의 무작위 변화를 추가한다.

**완료 기준:** 파일 수뿐 아니라 RGB와 라벨이 같은 물체를 가리키는지 샘플을 열어 확인한다. 검은 이미지나 빈 라벨도 파일 개수에는 포함될 수 있다.

## 32단계 — 성능과 회귀 검사를 기록하기

[검증·성능](05-customization/04-validation-performance.md)과 [검증 기록](appendices/validation-report.md)을 읽는다. 단일 센서, 복수 센서 순서로 VRAM·프레임 시간·물리 안정성을 측정한다. GUI 없이 돌려도 RTX GPU는 필요하다.

**완료 기준:** 실행 명령, GPU·드라이버, 로그, 결과 이미지와 수치가 남는다. 실제 GPU가 없는 환경의 정적 검사 결과는 ‘실행 미검증’으로 표시한다.

## 33단계 — 창고 자율주행 프로젝트 완성하기

[프로젝트 3](07-projects/03-warehouse-navigation.md)에서 지도·로봇·센서·Nav2를 묶는다. 단일 목표를 통과한 뒤 여러 목표를 순서대로 실행한다. 출발점, 목적지, 성공 횟수와 충돌 여부를 기록한다.

**완료 기준:** 저장한 장면과 명령만으로 다른 실행 세션에서도 결과를 재현한다. 샘플의 collision monitor 설정이 실제 정지 안전성을 보장하는지도 따로 살펴본다.

## 34단계 — 비전 기반 집기 프로젝트 완성하기

[프로젝트 4](07-projects/04-vision-pick-place.md)에서 카메라 관측, 대상 위치, 팔 목표를 연결한다. 먼저 알려진 물체 위치로 제어를 검증하고 그다음 추정값을 사용한다. 인식 성공, 접근 성공, 실제 집기 성공을 따로 기록한다.

**완료 기준:** 한 장의 성공 화면에 그치지 않고 초기화 후 반복한 결과와 실패 원인을 남긴다.

## 35단계 — Isaac Lab 정책 적용하기

[Isaac Lab](06-developer/04-isaac-lab.md)과 [프로젝트 5](07-projects/05-isaac-lab-policy.md)를 따른다. Isaac Sim 5.1과 맞는 Lab 버전, 관측 순서, action scale, 제어 주기를 확인한다. 먼저 공식 체크포인트로 추론을 재현한 뒤 학습이나 다른 로봇 적용을 시도한다.

**완료 기준:** 체크포인트·환경 설정·초기 seed·실행 버전을 기록하고 정책 출력이 유한한지, 로봇 자세가 안정적인지 확인했다.

## 36단계 — 최종 프로젝트를 다시 실행할 수 있게 정리하기

33~35단계 중 하나를 골라 [프로젝트 제출 기준](07-projects/00-overview.md)을 적용한다. 장면, 코드, 파라미터, 버전, 실행 명령, 기대 결과와 실패 사례를 함께 정리한다. 앱을 종료하고 새 터미널에서 다시 실행하는 것을 마지막 검사로 삼는다.

**완료 기준:** 준비→실행→결과 확인→종료 순서가 문서에 있으며, GPU에서 통과한 항목과 아직 실행하지 못한 항목이 분명하다. 더 큰 환경·센서 수·제어 속도로 확장하려면 그 조건에서 다시 검증한다.

## 출처

- [Isaac Sim 5.1.0 Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Isaac Sim 5.1.0 Tutorial Reference Table](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/tutorial_list.html)
- [Core API Tutorial Series](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/index.html)
- [ROS 2 Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/index.html)
- [Isaac Sim Conventions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_conventions.html)

위 순서와 단계별 완료 기준은 이 저장소의 학습 과정으로 구성했다. 공식 페이지의 메뉴 순서를 그대로 옮긴 것이 아니며, 각 세부 장에 해당 기능의 원문을 연결했다.
