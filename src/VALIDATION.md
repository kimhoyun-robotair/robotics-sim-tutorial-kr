# 검증 기록 — Isaac Sim 5.1

## 2026-09-15 GUI 종료 동작 수정

GUI 실행에서 `--steps`를 생략하면 사용자가 창을 닫을 때까지 유지하도록 실행기를 수정했습니다. 명시한 양수는 제한 실행에 사용하고, headless 기본 실행은 유한하게 유지합니다. 데이터 생성량과 GUI 수명은 별개입니다.

- `python3 -m unittest discover -s tests -v`: **27개 테스트 통과**. 새 종료 동작 회귀 테스트 12개는 실제 Python 진입점을 실행하며 Isaac/Kit 경계만 모형으로 대체합니다. 기본 GUI 지속, 명시적 제한, 사용자 종료, headless 기본값, 오류 전파와 변환 작업 취소를 확인합니다. 수정 전 소스에서는 해당 회귀 테스트가 실패하는 것도 확인했습니다.
- `python3 src/catalog.py check`: 180개 패키지의 출처·경로·파일 연결 통과. 패키지 간 공통 실행 모듈을 추가하지 않았습니다.
- Python 242개 구문 검사, `--steps`를 제공하는 CLI 138개의 도움말, 안내서의 로컬 링크 검사를 통과했습니다. 보호 대상 `asset/`, `docs/`, 루트 `README.md`의 12개 파일은 이번 작업 시작 시점의 내용·경로 목록과 동일합니다.
- 아래는 실제 Isaac Sim 5.1 GUI와 GPU로 다시 실행한 범위입니다. 창 종료는 해당 테스트 프로세스의 창에 `WM_DELETE_WINDOW` 이벤트를 보내 확인했습니다.

| 실행 | 관찰 결과 |
|---|---|
| 01 Hello World, `--steps` 생략 | 기존 300스텝을 넘어 5,597개 물리 샘플 기록. 큐브가 바닥에 놓인 GUI를 확인한 뒤 창을 닫아 결과 저장·종료 코드 0 확인 |
| 01 Hello World, `--steps 120` | 정확히 120개 샘플 저장 후 자동 종료, 코드 0 |
| 01 Hello World, `--headless`, 스텝 생략 | 기존 기본값인 300개 샘플 저장 후 자동 종료, 코드 0 |
| 62 Camera, `--steps` 생략 | 640×480 RGBA와 측정 파일 저장 후에도 GUI 유지. 창 닫기 후 코드 0 |
| 132 Replicator, `--frames 1`, 스텝 생략 | RGB 1장·세그멘테이션·USD 저장 후 GUI 유지. 추가 RGB가 생성되지 않으며 창 닫기 후 코드 0 |
| 132 Replicator, `--frames 1 --steps 2` | 같은 유한 데이터 생성 후 화면 갱신 한도를 적용해 자동 종료, 코드 0 |

추가로 06의 로컬 URDF 보충 실행기는 실제 Carter를 가져와 articulation 초기화 후 `--headless --steps 5`로 종료했고, 63의 깊이 카메라 보충 실행기는 실제 카메라 USD를 저장하고 headless 기본 한도로 종료했습니다. 169의 native 실행 어댑터도 작은 실제 Kit 검증 장면으로 작업 완료 후 창 유지·창 닫기·정리를 확인했습니다. 이 어댑터 검사는 Infinigen 전체 생성 파이프라인을 실행한 것은 아닙니다.

실행 명령·입력 해시·출력 경로는 [validation_results.json](validation_results.json)의 `gui_lifetime_update`에 기록합니다. 나머지 패키지의 모든 GPU·ROS·외부 서비스 시나리오를 이번 수정 후 재실행한 것은 아닙니다.

**아래는 이전 소스의 검증 기록입니다.** 기존 36개 패키지의 측정값과 입력 해시는 이력을 보존하며, 종료 루프가 변경된 현재 소스 전체를 검증했다는 뜻은 아닙니다. 각 `RUNTIME_CHECK.md`와 manifest의 `partial_runtime_verified`도 해당 날짜·인자의 실행 범위를 뜻합니다.

## 2026-09-14 최초 검증

확인일: **2026-09-14**. Ubuntu 24.04, Isaac Sim **5.1.0-rc.19+release.26219.9c81211b.gl**, NVIDIA RTX 5070 Ti 16 GiB, ROS 2 Jazzy를 사용했습니다.

## 전체 패키지 검사

- 공식 5.1 목차 304개 페이지를 가져와 실습/참조를 분류하고, 180개 실습 페이지와 180개 패키지를 일대일로 대조했습니다. 검색·경로·출처 연결은 `python3 src/catalog.py check`로 다시 확인할 수 있습니다.
- `python3 -m unittest discover -s tests -v`: **11개 테스트 통과**. 이 안에 180개 패키지 대응표 검사, 모든 패키지 Python 구문/공유 import 검사, **89개 Standalone 진입점을 독립 폴더에 복사한 뒤 일반 Python으로 --help 실행**이 포함됩니다.
- Python 236개, JSON/OGN, YAML, XML/URDF, TOML 및 notebook 코드의 구문을 검사했습니다. 정적 검사는 외부 API의 실제 동작을 보증하지 않습니다.
- 저장소에 포함된 USD/USDA **12개 모두 실제 OpenUSD Sdf 파서로 로드**했습니다. 외부 자산의 전체 composition이나 GUI 상호작용 검증은 아닙니다.
- 독립 검토에서 공식 원문 범위, 설치된 API/노드 스키마, ROS 빌드 조건과 패키지 밖 파일 의존성을 확인했습니다.
- 보호 대상 `asset/`, `docs/`, 루트 `README.md`의 파일 11개는 시작 전후 SHA-256 및 경로 목록이 동일합니다.

## 실제 실행

**36개 패키지**에서 아래에 기록된 모드·인자로 실제 Isaac Sim/네이티브 확장을 실행하고 출력 데이터를 확인했습니다. 종료 코드만으로 통과를 판정하지 않았습니다. 상세 인자·측정값·입력 파일 해시는 [validation_results.json](validation_results.json)과 해당 패키지의 `RUNTIME_CHECK.md`에 있습니다.

각 manifest의 `partial_runtime_verified`는 그 기록의 시나리오만 확인했다는 뜻입니다. 나머지 패키지의 `not_run`은 실제 simulator 실행을 확인하지 않았다는 뜻이며, 구현 유무를 표시하는 필드가 아닙니다.

| 실습 | 실제 관찰 |
|---|---|
| Hello World | 120개 물리 샘플; 한 변 0.5 m 큐브의 최종 중심 높이 0.249998 m |
| Hello Robot | Jetbot 두 바퀴 관절을 제어해 x 방향 0.268741 m 이동 |
| Franka pick/place | 상태기 종료와 별도로 실제 큐브 목표 오차 0.002614 m 확인 |
| ROS Clock | 별도 Jazzy 수신 노드에서 증가하는 `/clock` 메시지 100개 수신 |
| Camera | 640×480 RGBA 저장; 렌더링된 두 색 큐브와 투영 픽셀 일치 확인 |
| Contact / IMU | 정착 후 각각 약 9.81 N, 9.81 m/s². IMU의 자유낙하 구간도 확인 |
| RTX Lidar / PhysX | 마지막 RTX 점군 41,315×3; generic depth 약 4.975 m; lightbeam은 2.75 m 물체 검출 후 통과 시 검출 해제 |
| Lula IK / RMPflow | 실제 관절 상태에서 마지막 말단 오차 각각 약 1.04 mm / 2.24 mm |
| UR10e IK / UR10 trajectory | IK 말단 오차 약 0.95 mm; 궤적 349 actions 전체 재생, 기록된 최대 관절 추종 오차 0.000008 rad 미만 |
| USD | session layer와 저장 layer 값 차이, 두 references, 잘못된 자산 경로 복구와 variant 선택 확인 |
| Replicator | RGB·분할·bbox 출력, 실제 채널 교환·깊이 잡음, 커스텀 구면 샘플, behavior, 조명 randomizer, 서로 다른 크기의 카메라 3개 출력 |
| Object SDG | Setting/Macro/Harmonizer에서 실제 JPG·라벨·description 생성. Setting은 depth/normal도 확인 |
| Import / Merge / Validate | 로컬 URDF/MJCF/OBJ 변환, 두 cube의 12 faces·2 material subsets, 실제 validation issues 4개 → 0개 |

위 표 외의 Cloner, props, data logging, RRT 등도 아래 패키지별 기록을 확인하세요. RRT는 경로 생성과 기록, data logging은 record 모드를 확인했으며 모든 후속 재생·제어 모드를 검증하지 않았습니다.

| ID | 확인한 패키지 |
|---|---|
| t005 | [Getting Started with Cloner](163_motion_cloner/RUNTIME_CHECK.md) |
| t009 | [ROS 2 Clock](106_ros2_ros2_clock/RUNTIME_CHECK.md) |
| t037 | [Getting Started Scripts](134_replicator_replicator_getting_started/RUNTIME_CHECK.md) |
| t044 | [Data Augmentation](139_replicator_replicator_augmentation/RUNTIME_CHECK.md) |
| t045 | [Custom Replicator Randomization Nodes](140_replicator_replicator_custom_og_randomizer/RUNTIME_CHECK.md) |
| t046 | [Modular Behavior Scripting](141_replicator_replicator_modular_scripting/RUNTIME_CHECK.md) |
| t047 | [Randomization Snippets](135_replicator_replicator_isaac_randomizers/RUNTIME_CHECK.md) |
| t048 | [Useful Snippets](136_replicator_replicator_isaac_snippets/RUNTIME_CHECK.md) |
| t059 | [Setting](145_events_ext_replicator_object_setting/RUNTIME_CHECK.md) |
| t066 | [Harmonizer](152_events_ext_replicator_object_harmonizer/RUNTIME_CHECK.md) |
| t067 | [Macro](153_events_ext_replicator_object_macro/RUNTIME_CHECK.md) |
| t098 | [Hello World](01_core_core_hello_world/RUNTIME_CHECK.md) |
| t099 | [Hello Robot](02_core_core_hello_robot/RUNTIME_CHECK.md) |
| t101 | [Adding a Manipulator Robot](24_core_core_adding_manipulator/RUNTIME_CHECK.md) |
| t104 | [Adding Props](19_core_core_adding_props/RUNTIME_CHECK.md) |
| t105 | [Data Logging](27_core_advanced_data_logging/RUNTIME_CHECK.md) |
| t111 | [Tutorial: Import URDF](30_importers_import_urdf/RUNTIME_CHECK.md) |
| t113 | [Tutorial: Import MJCF](31_importers_import_mjcf/RUNTIME_CHECK.md) |
| t114 | [Tutorial: ShapeNet Importer](175_importers_shapenet_importer/RUNTIME_CHECK.md) |
| t116 | [Merge Mesh Utility](33_importers_util_merge_mesh/RUNTIME_CHECK.md) |
| t127 | [Tutorial 9: Pick and Place Example](43_robot_setup_pickplace_example/RUNTIME_CHECK.md) |
| t132 | [Asset Validation](50_importers_asset_validation/RUNTIME_CHECK.md) |
| t136 | [Lula RMPflow](56_motion_manipulators_rmpflow/RUNTIME_CHECK.md) |
| t137 | [Lula RRT](57_motion_manipulators_lula_rrt/RUNTIME_CHECK.md) |
| t138 | [Lula Kinematics Solver](54_motion_manipulators_lula_kinematics/RUNTIME_CHECK.md) |
| t139 | [Lula Trajectory Generator](55_motion_manipulators_lula_trajectory_generator/RUNTIME_CHECK.md) |
| t145 | [Camera Sensors](62_sensors_sensors_camera/RUNTIME_CHECK.md) |
| t147 | [RTX Lidar Sensor](72_sensors_sensors_rtx_lidar/RUNTIME_CHECK.md) |
| t152 | [Contact Sensor](65_sensors_sensors_physics_contact/RUNTIME_CHECK.md) |
| t153 | [Effort Sensor](66_sensors_sensors_physics_effort/RUNTIME_CHECK.md) |
| t154 | [IMU Sensor](67_sensors_sensors_physics_imu/RUNTIME_CHECK.md) |
| t156 | [PhysX SDK Generic Sensor](69_sensors_sensors_physx_generic/RUNTIME_CHECK.md) |
| t158 | [PhysX SDK Lightbeam Sensor](71_sensors_sensors_physx_lightbeam/RUNTIME_CHECK.md) |
| t173 | [OpenUSD Fundamentals](10_python_usd_open_usd/RUNTIME_CHECK.md) |
| t174 | [Working with USD](11_python_usd_intro_to_usd/RUNTIME_CHECK.md) |
| t175 | [USD Tools](12_python_usd_usd_tools/RUNTIME_CHECK.md) |

## 실행 중 발견하여 수정한 문제

- Object SDG의 출력명 매크로를 실제 5.1 writer 문법으로 수정하고 재생성했습니다.
- 카메라 기본 렌더와 수학적 투영의 불일치를 zero-distortion OpenCV 모델로 수정해 실제 이미지와 대조했습니다.
- 원문 궤적에 추가한 z=0 바닥이 UR10과 충돌하던 문제를 고쳤습니다. waypoint와 물리 drive는 유지하고 바닥을 z=−2 m로 옮긴 뒤 전체 궤적을 다시 실행했습니다.
- GUI 실습용 USD 5개의 light 선언 문법을 고쳐 실제 Sdf 파싱을 통과했습니다.
- Mesh Merge의 명령 등록과 선택된 Mesh의 중복 순회를 수정하고, 실제 topology·material subsets를 검사했습니다.
- ROS workspace 태그, 사용자 OmniGraph 노드의 등록 이름, importer의 실제 5.1 UI 절차를 설치본과 대조해 수정했습니다. 이 수정만으로 ROS custom workspace 빌드까지 검증한 것은 아닙니다.

## 확인하지 않은 범위

모든 GUI 클릭·확장 UI·ROS Nav2/MoveIt 전체 시나리오·사용자 메시지/C++ 링크·정책 추론·모델 학습·NIM/cuOpt/Cosmos/Infinigen 서비스·외부 대규모 자산/recording까지 실행한 검증은 아닙니다. 해당 준비 조건과 네이티브 실행 순서는 각 패키지에 있습니다. GPU/센서의 성능 수치나 다른 하드웨어에서의 재현성도 보장하는 기록이 아닙니다.

원시 실행 로그는 로컬 `.omo/work/isaac51-catalog/evidence/`에 보관했습니다. 저장소에 남는 패키지별 기록에는 측정값과 입력 파일 해시를 포함했습니다.

## 2026-09-15 학습 순서 번호 적용

180개 폴더에 `00`–`179` 접두사를 붙이고 안내·색인·메타데이터의 현재 경로를 갱신했습니다. `t001` 등의 출처 ID와 기존 실행 검증 상태는 유지합니다. Python 실습 코드와 입력 설정은 바꾸지 않았으므로 위 GPU 실행 증거를 재사용합니다.

`validation_results.json`의 `command`와 `metrics`는 2026-09-14 실행 당시 기록입니다. 새 경로에서 같은 실습을 실행하는 명령은 `replay_command`이며, 해당 폴더의 실행 안내도 새 이름을 사용합니다. 개별 `RUNTIME_CHECK.md`의 측정 데이터에 남은 이전 경로도 당시 기록입니다.

번호 적용 후 테스트 **15개**가 통과했습니다. 180개 번호의 연속성·중복·폴더명·메타데이터·학습 단계 대응, 숫자 순서의 검색 결과, 학습 번호와 기존 출처 ID 조회를 확인했습니다. 89개 Standalone 진입점은 변경된 폴더를 따로 복사한 뒤 `--help`로 검사했습니다. 로컬 문서 링크 314개와 기존 실행 입력 해시도 확인했으며, 실습 코드·설정·데이터 391개 파일과 보호 대상 11개 파일은 내용이 동일합니다. GPU 시뮬레이션은 이번 이름 변경에서 재실행하지 않았습니다.
