# 06. Python 환경: python.sh, 앱 수명, 확장, 스텝

권장 학습 순서 **06** · Python 실행 환경과 USD 기초 · 출처 ID `t094`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 예상 결과

설치 Python이 준비하는 환경과 `SimulationApp`의 역할을 실제 실행으로 확인한다. 이 패키지는 옵션으로 창 해상도·확장·로컬 Stage를 선택하고, 물리 콜백 횟수와 시뮬레이션 시간을 `environment.json`에 기록한다. 기본 실행은 떨어지는 큐브와 `scene.usda`를 만든다.

## 순서대로 실습

1. `python3 run.py --help`로 옵션을 확인하고 `~/isaacsim/python.sh run.py --width 960 --height 640`으로 실행한다.
2. `environment.json`에서 `ISAAC_PATH`, `EXP_PATH`, `CARB_APP_PATH`를 확인한다. `python.sh`는 설치 위치를 기준으로 앱 설정, Python 확장 경로, 네이티브 라이브러리 경로를 준비하고 번들 Python을 시작한다.
3. 코드의 import 순서를 본다. `SimulationApp`을 만든 다음 `omni.usd`를 가져오는 이유는 확장 플러그인이 앱 시작 시 로드되기 때문이다. 마지막 `finally`는 오류에도 `close()`를 실행한다.
4. `~/isaacsim/python.sh run.py --extension omni.kit.widget.layers --extension omni.kit.window.stage`으로 실행한다. 해당 확장은 5.1 설치본에서 제공되어야 한다. 패키지 옵션은 명시된 확장만 활성화하며 시스템 설정 파일을 바꾸지 않는다.
5. 이전 출력의 `scene.usda` 절대 경로를 `--stage /실제/경로/scene.usda`로 지정해 다시 실행한다. 임의 로봇 Stage에는 그 자산의 종속 파일도 필요하다.
6. `physics_dt=1/60`, `rendering_dt=1/30`을 읽고 `environment.json`의 실제 `physics_callbacks`, `physics_time_s`를 관찰한다. 렌더 한 프레임과 물리 한 스텝이 같은 단위라고 가정하지 않는다. headless의 `render=False`와 GUI 실행의 결과를 비교한다.

## 원문에 나오는 설치 예제 실습

아래 표는 원문의 소주제를 실습하는 경로다. URDF Import는 이 패키지의 `urdf_import.py`로 실행한다. 나머지 설치 예제는 **5.1 설치본의 네이티브 예제**이며 설치 루트에서 명령을 실행한다. 각 파일을 열어 옵션과 대상 경로를 확인한다.

| 원문 소주제 | 설치 파일/실습 |
|---|---|
| Time Stepping | `./python.sh standalone_examples/api/isaacsim.core.api/time_stepping.py` 실행 후 물리·렌더 콜백과 시간 간격을 비교한다. |
| Load USD Stage | 로컬 `run.py --stage`를 사용하거나 `standalone_examples/api/isaacsim.simulation_app/load_stage.py --usd_path /Isaac/Environments/Simple_Room/simple_room.usd`를 번들 Python으로 실행한다. 후자는 NVIDIA 자산 접근이 필요하다. |
| URDF Import | 이 패키지 폴더에서 `~/isaacsim/python.sh urdf_import.py`를 실행한다. `--fix-base` 또는 `--self-collision` 한 옵션만 추가해 비교한다. `--steps`를 생략하면 창을 닫을 때까지 유지하며, 양수를 지정하면 해당 앱 업데이트 수 후 종료한다. `--headless`에서 생략하면 1000번으로 제한한다. |
| Change Resolution | `./python.sh standalone_examples/api/isaacsim.simulation_app/change_resolution.py`; 초기 해상도와 런타임 변경 시점을 확인한다. 로컬 `--width/--height`는 시작 해상도다. |
| Convert Assets | `./python.sh standalone_examples/api/omni.kit.asset_converter/asset_usd_converter.py --folders standalone_examples/data/cube standalone_examples/data/torus`; 예제 입력의 복사본으로 진행하고 생성된 `_converted` 디렉터리에서 USD를 검사한다. |
| Livestream | `./python.sh standalone_examples/api/isaacsim.simulation_app/livestream.py`; WebRTC 클라이언트와 접근 가능한 네트워크가 별도로 필요하다. 이 패키지 기본 실행은 스트리밍 서버를 시작하지 않는다. |

URDF 보조 실습은 설치에 포함된 Carter URDF와 메시를 읽어 현재 Stage로 가져온다. `URDFCreateImportConfig`는 변환 옵션을 만들고 `URDFParseAndImportFile`은 URDF의 링크·관절을 USD로 변환한다. `fix_base`는 바닥에 베이스를 고정하고 `self_collision`은 로봇 링크 사이 충돌을 켠다. 바퀴의 `UsdPhysics.DriveAPI` 속도 목표는 도/초 단위이며, stiffness=0과 damping은 속도 제어를 설정한다. 로컬 보조 파일은 설치 예제의 자동 종료 반복문을 대체하며 설치 파일을 수정하지 않는다.

## API와 개념 해설

`enable_extension`은 런타임 확장을 켠다. 다른 방법으로는 별도 `.kit` 경험 파일의 `[dependencies]`에 확장 ID를 등록할 수 있다. 경험 파일은 앱에 어떤 확장을 로드할지 정하며 USD 파일은 장면을 정한다. `.kit`와 `.usd`를 서로 대체할 수 없다. `app.update()`는 앱 업데이트이고 `world.step()`은 Core의 물리/렌더 시간 관리까지 포함한다.

`--headless`는 창을 숨기는 옵션이며 GPU를 사용하지 않는다는 뜻이 아니다. 이 패키지는 필요한 세 경로 변수만 보고서에 쓰며 전체 환경변수를 덤프하지 않는다.

## 한 가지 변수 실험과 문제 해결

`--width`만 800에서 1200으로 바꿔 창 폭을 비교한다. 출력의 requested_resolution은 요청값이므로 실제 화면 크기 검증을 대신하지 않는다. `--stage`가 실패하면 로컬 파일 여부와 참조 자산을 확인한다. 확장 import 오류에는 해당 ID가 설치되어 있는지 **Window > Extensions**에서 확인한다. Windows에서는 설치의 `python.bat`을 사용한다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- URDF 보조 실습의 API와 Carter 경로는 설치본 `standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py` 및 `isaacsim.asset.importer.urdf`의 `impl/commands.py`와 대조했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
