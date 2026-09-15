# Isaac Sim 5.1 공식 튜토리얼 실습 안내

현재 학습 안내는 이 파일입니다. `src/`에는 **공식 Isaac Sim 5.1 실습 페이지 180개에 대응하는 독립 패키지**가 있습니다. 이전 다섯 미니 프로젝트와 `tutorial_common`은 이 구조로 대체했습니다. 루트 `README.md`, `asset/`, `docs/`는 변경하지 않았습니다.

- **[권장 학습 순서 색인](src/INDEX.md)**: `00`–`179` 번호, 패키지 이름, 한국어 실습 안내, 공식 제목·원문 링크
- **[공식 목차 대응표](src/official_tutorials.json)**: 304개 목차 페이지의 포함/참조 분류와 180개 패키지 경로
- **[실행 검증 기록](src/VALIDATION.md)**: 실제로 실행한 범위와 미확인 환경
- **[Isaac Sim 5.1 Python API 사전](api/INDEX.md)**: 공식 API의 이름·문법·인자·한국어 설명·예제·출처. 실행 환경과 문법을 읽는 방법은 [API 안내](api/GUIDE.md)에 있습니다.

## 포함 범위

공식 [Tutorial Reference Table](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/tutorial_list.html)의 9개 시리즈에 더해 Quick Start, Cortex, Action/Event 하위 실습, NuRec, USD/Python 실습, 확장 개발과 디버깅을 포함했습니다. 제목에 `Tutorial`이 없는 센서·제어·도구 실습도 포함합니다. 같은 페이지가 여러 목차에 등장하면 한 패키지로 연결합니다. 한 페이지 안의 GUI·Python·OmniGraph 방식은 해당 패키지에서 다룹니다.

범위는 **5.1 문서 사이트 안의 실습 본문**입니다. 설치·클라우드 배포·릴리스 노트·API 참조·자산 목록은 전제조건 및 참조 자료로 분류합니다. 외부 Isaac Lab, Isaac ROS, Kit, Cosmos 등의 전체 문서까지 재귀적으로 복제하지 않습니다. 외부 도구를 사용하는 실습은 해당 패키지 안에 설치 조건과 실행 절차를 포함합니다. 공식 문서의 Deprecated 합성 데이터 실습도 포함하고 상태를 표시합니다. 목차 확인일은 **2026-09-14**입니다.

## 권장 학습 단계

180개 폴더를 다음 순서로 배치했습니다. 단계 안의 전체 패키지 이름과 실행 방식은 [색인](src/INDEX.md)에 있습니다.

| 번호 | 단계 |
|---|---|
| 00–03 | [첫 실행과 로봇 만나기](src/INDEX.md#first_steps) |
| 04–17 | [Python 실행 환경과 USD 기초](src/INDEX.md#python_usd) |
| 18–28 | [물리 기초와 Core API 확장](src/INDEX.md#physics_core) |
| 29–50 | [로봇 자산 가져오기와 제작](src/INDEX.md#robot_authoring) |
| 51–61 | [로봇 제어와 동작 계획](src/INDEX.md#motion_control) |
| 62–79 | [센서와 측정 데이터](src/INDEX.md#sensors) |
| 80–93 | [OmniGraph와 확장 개발](src/INDEX.md#omnigraph_extensions) |
| 94–103 | [환경 구축과 로봇 행동](src/INDEX.md#environments_behaviors) |
| 104–121 | [ROS 2 연결과 기본 통신](src/INDEX.md#ros2_basics) |
| 122–131 | [ROS 2 응용과 사용자 인터페이스](src/INDEX.md#ros2_applications) |
| 132–143 | [Replicator 합성 데이터 기초와 확장](src/INDEX.md#replicator) |
| 144–155 | [물체 시뮬레이션과 YAML 무작위화](src/INDEX.md#object_sdg) |
| 156–161 | [액터와 공간 이벤트 데이터](src/INDEX.md#actor_events) |
| 162–167 | [병렬 환경과 학습 정책 활용](src/INDEX.md#policies_scaling) |
| 168–174 | [고급 데이터 생성과 외부 시스템 통합](src/INDEX.md#advanced_integrations) |
| 175–179 | [사용 중단 문서와 레거시 참고](src/INDEX.md#legacy_reference) |

번호는 최소 두 자리(`00`–`99`, `100`–`179`)입니다. `catalog.py list`는 숫자 순서로 표시하며, 폴더 목록은 `ls -v src/`로 볼 수 있습니다.

## 한 패키지만 골라 시작하기

패키지는 폴더 단위로 복사해서 공부할 수 있습니다. 다른 튜토리얼 코드나 공통 학습 모듈을 import하지 않습니다. Isaac Sim 자체, 공식 자산, ROS 2, 외부 모델처럼 실습에 필요한 제품 의존성은 각 `TUTORIAL.md`에서 설명합니다.

1. [색인](src/INDEX.md)에서 관심 주제를 선택합니다. 처음에는 `core`의 **Isaac Sim Basic Usage Tutorial** 또는 **Hello World**로 시작해 보세요.
2. 그 폴더의 `TUTORIAL.md`를 읽습니다. 목표, 준비, 실행, API/개념, 결과 확인, 바꿔볼 실험을 담았습니다.
3. **실행 방식**을 확인합니다. GUI 실습에서는 안내된 메뉴·Property를 직접 조작합니다.
4. 해당 안내의 명령을 실행하고 관찰 기준과 실제 출력을 비교합니다. 출력 위치와 덮어쓰기 규칙은 각 실행기의 도움말을 따릅니다.

폴더 앞 `00`–`179`는 **권장 학습 순서**입니다. 처음에는 `00_core_quickstart_isaacsim` → `01_core_core_hello_world` → `02_core_core_hello_robot` 순으로 진행하세요. 기존 `t001` 같은 ID는 **공식 출처 식별자**로 유지합니다. 예를 들어 Hello World는 학습 번호 `01`, 출처 ID `t098`입니다. 순서가 실행 의존성을 만들지는 않으며 각 패키지 안에 필요한 준비와 설명이 있습니다.

## 설치와 실행

대상 환경은 **Isaac Sim 5.1.0, Ubuntu 24.04, ROS 2 Jazzy**입니다. ROS 안내에는 공식 지원 조합인 Ubuntu 22.04/Humble도 명시할 수 있습니다. ROS가 필요하지 않은 실습은 ROS 터미널 없이 실행합니다. Windows에서는 `python.bat`와 Windows 경로를 사용하되 Linux 전용 빌드·셸 실습은 각 안내의 플랫폼 제한을 따르세요.

```bash
cd /path/to/robotics-sim-tutorial-kr
export ISAAC_SIM_PATH="$HOME/isaacsim"  # 자신의 5.1 설치 디렉터리
cat "$ISAAC_SIM_PATH/VERSION"
python3 src/catalog.py list --search "Hello World"
python3 src/01_core_core_hello_world/run.py --help
"$ISAAC_SIM_PATH/python.sh" src/01_core_core_hello_world/run.py
```

GUI 실행에서 `--steps`를 생략하면 **사용자가 창을 닫을 때까지 유지**됩니다. 시뮬레이션·제어 실습은 계속 진행하고, 자산 변환이나 데이터 생성처럼 끝이 있는 작업은 결과를 저장한 뒤 GUI에서 확인할 수 있습니다. 오류가 발생하면 정상적으로 오류를 보고하고 종료합니다.

자동으로 종료하려면 `--steps`에 양수를 지정합니다. 다음은 제한 실행 예시입니다.

```bash
"$ISAAC_SIM_PATH/python.sh" src/01_core_core_hello_world/run.py --steps 180
"$ISAAC_SIM_PATH/python.sh" src/01_core_core_hello_world/run.py --headless --steps 180
```

`--headless`는 GUI가 없으므로 `--steps`를 생략해도 기존의 유한 실행 기본값을 사용합니다. 원래 명시적인 실행 한도를 요구하던 도구는 그 조건을 유지합니다. `--frames` 같은 데이터 수량 옵션은 생성할 데이터의 양을 정하며, GUI 종료 여부는 `--steps`로 정합니다. 스텝이 물리 계산, 앱 업데이트, 생성 후 화면 확인 중 무엇을 세는지는 각 패키지의 `--help`와 `TUTORIAL.md`에서 설명합니다. ROS 서비스 요청이나 외부 학습 명령의 동명 인자는 해당 작업의 의미를 유지합니다.

Standalone 실습은 **Isaac Sim에 포함된 Python**으로 실행합니다. 일반 `python3`에는 `isaacsim`, `omni`, `pxr`가 없을 수 있습니다. 실행기는 `SimulationApp`으로 Kit를 시작한 뒤 시뮬레이터 모듈을 import합니다. `--help`는 시뮬레이터를 시작하지 않습니다.

GUI 실습은 `"$ISAAC_SIM_PATH/isaac-sim.sh"`로 앱을 열고 해당 패키지의 절차를 수행합니다. **Script Editor 코드에서는 `SimulationApp`을 다시 만들지 않습니다.** 이미 실행 중인 Kit의 Stage를 사용하기 때문입니다. 안내에서 `run.py`, `inspect_stage.py`, 확장 폴더 등의 역할을 구분합니다.

공식 자산 실습은 5.1 자산 서버 접근 또는 로컬 자산 경로가 필요합니다. 설치의 예제·확장을 사용하는 실습은 해당 의존성을 명시합니다. 설치 디렉터리의 예제를 직접 수정하지 말고 패키지의 로컬 코드·설정과 안내된 복사본을 사용하세요.

출처: [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html), [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html), [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html).

## 실행 방식

| 표시 | 시작 방법 | 실행 대상 |
|---|---|---|
| `standalone` | Isaac Sim `python.sh`로 로컬 진입점 실행 | 앱·장면 생성, 시뮬레이션/렌더링 루프 |
| `gui` | GUI에서 안내의 메뉴·필드 조작 | 장면 편집, 센서 배치, 네이티브 도구 |
| `script_editor` | 실행 중인 앱의 Script Editor | 현재 Stage 검사·변경, 비동기 작업 |
| `extension` | 안내된 로컬 확장 등록·활성화 | Kit 수명주기, UI, OmniGraph 노드 |
| `ros2` | 시뮬레이터와 ROS 터미널을 각각 실행 | 실제 토픽·서비스·TF·제어 |
| `external` | 외부 프로그램/워크스페이스 준비 | 학습·변환·계획 서비스 통합 |

Standalone은 **다른 학습 패키지에 의존하지 않는다**는 의미와 Isaac Sim의 **Standalone Python 실행 방식**이라는 의미로 쓰입니다. 모든 패키지는 전자의 의미로 독립적이며, 후자의 실행 방식은 위 표로 구분합니다. GUI 원문을 Python으로 변환한 경우에는 해당 안내에서 변환 범위와 원래 GUI 절차를 설명합니다.

## 분야별 찾기

| 분야 키 | 수 | 주제 |
|---|---:|---|
| `core` | 10 | Quick Start, World/Scene, 로봇, Task, 기록 |
| `python_usd` | 11 | Python 환경·스니펫, USD Stage/Prim/Layer/Schema |
| `ros2` | 29 | 시계, 센서, TF, QoS, Nav2, MoveIt, 메시지·서비스·노드 |
| `importers` | 8 | URDF/MJCF/ShapeNet, 조립·검증·도구 |
| `robot_setup` | 14 | Robot Wizard와 로봇 구성 13개 실습 |
| `motion` | 16 | 제어기, Lula, RMPflow, grasp, policy, Cloner |
| `sensors` | 19 | 카메라, RTX/PhysX/물리 센서, Motion BVH, 물리 도구 |
| `replicator` | 18 | 데이터 생성·랜덤화·증강·학습 연계 |
| `events` | 22 | Actor/Object SDG, 캡션·이벤트, 배치·보정 |
| `sdg_extra` | 2 | Grasping SDG, MobilityGen |
| `digital_twin` | 12 | 창고, conveyor, cuOpt, Cortex, mapping, NuRec |
| `tools` | 19 | OmniGraph, 개발 환경, 확장, 디버깅·프로파일링 |

```bash
python3 src/catalog.py list --category sensors
python3 src/catalog.py list --mode standalone
python3 src/catalog.py list --search camera
python3 src/catalog.py show 00
python3 src/catalog.py list --stage first_steps
python3 src/catalog.py check
```

`catalog.py`는 검색·색인 검사 도구입니다. 실습 코드가 import하지 않으며 한 패키지를 복사할 때 가져갈 필요도 없습니다.

## 검증

```bash
python3 -m unittest discover -s tests -v
python3 src/catalog.py check
```

이 검사는 공식 출처와 파일 연결, 중복·누락, 패키지 밖 경로, Python 구문, 다른 학습 패키지 import, 복사된 Standalone 진입점의 도움말을 확인합니다. 물리 결과·GPU 렌더링·ROS 통신·학습 성공은 [실행 검증 기록](src/VALIDATION.md)에 따로 기록합니다. `tutorial.json`의 `verification`이 `not_run`이면 실제 실행을 확인하지 않은 상태입니다. 안내서의 성공 기준은 사용자가 자신의 환경에서 확인할 실습 기준입니다.

공식 코드를 포함한 패키지는 원래 라이선스와 출처를 보존합니다. NVIDIA 자산·모델·서비스는 패키지 소스와 별개 의존성이며 해당 공급자의 다운로드·사용 조건을 따릅니다.
