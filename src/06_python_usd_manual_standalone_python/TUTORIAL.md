# 06. 독립 Python 실행은 어떤 환경과 시간을 사용할까요?

## 이번에 배우는 것

**Isaac Sim의 Python 실행 환경을 읽고, 앱 업데이트 횟수와 물리 단계 수를 구분합니다.**

05번에서는 물리를 누가 진행하는지 비교했습니다. 이번에는 같은 `world.step()` 호출도 물리 간격·렌더 간격·`render` 설정에 따라 무엇을 진행하는지 살펴봅니다. 기본 장면은 높이 2 m에서 떨어지는 큐브이며, 실행 환경과 물리 콜백 수를 JSON으로 남깁니다.

| 설정·파일 | 이 실습에서의 의미 |
|---|---|
| `python.sh` | 설치에 필요한 Python·라이브러리 경로를 준비합니다. |
| `SimulationApp` | 준비된 환경에서 앱을 시작하고 종료합니다. |
| `physics_dt=1/60` | 물리 계산 한 단계의 시간 간격입니다. |
| `rendering_dt=1/30` | 렌더링 시간 간격입니다. |
| `environment.json` | 요청 옵션, 실제 콜백 수와 물리 시간을 기록합니다. |
| `scene.usda` | 실행 후 루트 레이어를 내보낸 장면입니다. |
| `urdf_import.py` | 설치에 포함된 Carter URDF를 가져오는 별도 실습입니다. |

## 1. 설치 환경과 물리 횟수 확인하기

Isaac Sim 5.1과 지원 NVIDIA GPU·드라이버가 필요합니다. 기본 큐브 실행에는 외부 자산이 필요하지 않습니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/06_python_usd_manual_standalone_python/run.py --steps 120
```

반복문을 120번 완료하면 앱이 종료됩니다. `--steps`를 생략한 GUI는 창을 닫을 때까지 계속 실행합니다. `--headless`를 추가하면 창 없이 실행하고, 이때 단계 수를 생략하면 120번입니다. Windows에서는 설치의 `python.bat`을 사용하세요.

### 코드에서 볼 부분

```python
from isaacsim import SimulationApp
app = SimulationApp(
    {"headless": args.headless, "width": args.width, "height": args.height}
)
```

시작 해상도는 `--width 960 --height 640`처럼 지정할 수 있습니다. 이 값은 앱 생성 시 전달되며, 실행 중 해상도를 바꾸는 명령은 아닙니다.

`python.sh`는 설치의 `setup_python_env.sh`를 불러온 뒤 번들 Python으로 파일을 실행합니다. `ISAAC_PATH`는 Isaac Sim 설치 위치, `EXP_PATH`는 앱 설정이 있는 위치, `CARB_APP_PATH`는 Kit 위치를 가리킵니다. 환경이 준비된 다음 `SimulationApp`을 생성해야 확장 기반의 `omni`·Core API를 가져올 수 있습니다.

아래 두 줄의 시간 간격은 다르게 설정되어 있습니다.

```python
world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 30)
world.step(render=not args.headless)
```

`world.step()`은 반복문 안에 있습니다. GUI 경로에서는 앱 업데이트를 통해 렌더링과 물리가 진행되고, `render=False` 경로에서는 물리 단계만 진행합니다. **이 코드의 `--steps`는 바깥 반복문의 제한입니다. 실제 물리 단계 수는 콜백으로 따로 셉니다.**

```python
def count_physics(dt):
    counts["physics_callbacks"] += 1

world.add_physics_callback("environment_count", count_physics)
```

### 실행 결과 확인하기

종료 후 이 폴더의 `output/날짜-시간/environment.json`을 엽니다.

| 항목 | 읽는 방법 |
|---|---|
| `requested_steps` | 요청한 반복 횟수입니다. 중간에 창을 닫으면 실제 완료 횟수와 다를 수 있습니다. |
| `physics_callbacks` | 실행 중 실제 호출된 물리 콜백 수입니다. |
| `physics_time_s` | `world.current_time`에서 읽은 시뮬레이션 시간입니다. |
| `environment` | 세 경로 변수가 자신이 사용한 설치와 연결되는지 확인합니다. |
| `requested_resolution` | 기본값 `[800, 600]`인 시작 해상도 요청입니다. |
| `enabled_extensions` | 명령행에서 요청한 확장 ID 목록입니다. |

물리 단계 수와 1/60초를 연결해 `physics_time_s`를 해석하세요. 기본 GUI 설정에서는 렌더 간격 하나에 **(1/30) ÷ (1/60) = 물리 2단계**가 들어갑니다. 중간에 Pause/Stop하지 않고 정상 재생했다면 120번의 GUI 반복에서 약 240개 콜백과 4초를 기대할 수 있습니다. 실제 완료 범위는 JSON의 관찰값으로 확인합니다. 화면에서는 `/World/Cube`가 떨어지는지 보고, 요청 해상도와 실제 창·Viewport 크기도 구분해 살펴봅니다.

`scene.usda`에는 시간별 이동 기록이 없습니다. 장면 저장 결과와 콜백 수 보고서는 서로 다른 자료입니다.

## 2. 장면·확장·URDF를 선택해 실행하기

### 코드에서 볼 부분: 기존 Stage 열기

`--stage`를 지정하면 기본 큐브와 지면 대신 그 파일을 사용합니다. 앞서 생성한 `scene.usda`의 실제 경로를 넣어 실행하세요.

```bash
~/isaacsim/python.sh src/06_python_usd_manual_standalone_python/run.py --steps 120 --stage /실제/출력/경로/scene.usda
```

코드는 로컬 파일의 존재를 확인한 뒤 `open_stage()`로 엽니다. 이 옵션은 `Path`로 처리하므로 네트워크 URL을 직접 받는 옵션이 아닙니다. 로봇 장면을 넣는 경우에는 참조하는 하위 자산도 필요합니다.

확장은 `--extension`을 반복해 요청합니다.

```bash
~/isaacsim/python.sh src/06_python_usd_manual_standalone_python/run.py --steps 120 --extension omni.kit.widget.layers --extension omni.kit.window.stage
```

각 ID에 `enable_extension()`을 호출한 뒤 앱을 갱신합니다. 요청 목록이 JSON에 저장됐다는 사실과 확장이 실제로 활성화됐다는 사실은 구분하세요. **Window > Extensions**에서 해당 확장의 상태를 확인합니다. 앱의 확장 구성을 담는 `.kit`와 장면 데이터를 담는 `.usd`도 서로 다른 파일입니다.

### 코드에서 볼 부분: Carter URDF 가져오기

기본 실행을 종료한 뒤 다음 보조 파일을 실행할 수 있습니다.

```bash
~/isaacsim/python.sh src/06_python_usd_manual_standalone_python/urdf_import.py --steps 1000
```

이 파일은 `isaacsim.asset.importer.urdf` 확장 안의 `data/urdf/robots/carter/urdf/carter.urdf`를 사용합니다. `URDFCreateImportConfig`로 설정을 만들고 `URDFParseAndImportFile`로 링크·관절을 현재 Stage로 가져옵니다.

```python
config.fix_base = args.fix_base
config.self_collision = args.self_collision
```

`--fix-base`는 베이스를 월드에 고정하고, `--self-collision`은 로봇 링크 사이의 충돌을 켭니다. 기본값은 둘 다 꺼져 있습니다. 가져온 `/carter/joints/left_wheel`, `right_wheel`에는 다음 USD drive 값을 작성합니다.

```python
drive.GetTargetVelocityAttr().Set(150.0)
drive.GetDampingAttr().Set(15000.0)
drive.GetStiffnessAttr().Set(0.0)
```

여기는 USD의 angular drive 속성이므로 목표 단위는 **도/초**입니다. 02번 Core API의 rad/s와 구분하세요. Stiffness를 0으로 두고 damping을 사용해 속도 목표를 따르게 합니다. 타임라인을 재생한 뒤 `app.update()`를 반복하므로 보조 파일의 `--steps`는 앱 업데이트 제한입니다.

### 실행 결과 확인하기

기본 보조 실행에서는 Carter와 바퀴 움직임을 보고, 출력의 `wheel_target_degrees_per_second`가 150.0인지 확인하세요. `--fix-base`를 사용했다면 바퀴 목표가 있어도 베이스가 주행하지 않는 설정입니다. 이 파일은 `environment.json`이나 USD를 자동 저장하지 않습니다.

원문에 있는 다른 주제를 더 보고 싶으면 설치의 다음 예제를 열어 입력과 옵션을 확인할 수 있습니다.

| 주제 | `~/isaacsim/` 아래 파일 |
|---|---|
| 물리·렌더 시간 비교 | `standalone_examples/api/isaacsim.core.api/time_stepping.py` |
| USD 장면 로드 | `standalone_examples/api/isaacsim.simulation_app/load_stage.py` |
| 실행 중 해상도 변경 | `standalone_examples/api/isaacsim.simulation_app/change_resolution.py` |
| 자산 변환 | `standalone_examples/api/omni.kit.asset_converter/asset_usd_converter.py` |
| WebRTC 스트리밍 | `standalone_examples/api/isaacsim.simulation_app/livestream.py` |

이 파일들은 설치 예제이며 이 폴더의 기본 실행에 포함되지 않습니다. 시간 비교 예제는 `~/isaacsim/python.sh ~/isaacsim/standalone_examples/api/isaacsim.core.api/time_stepping.py`로 실행합니다. 해상도 예제도 같은 방식으로 `change_resolution.py`를 지정하세요. 해상도 예제는 Headless에서 `resolution set to: ...`를 출력하므로 눈에 보이는 창 크기 변경을 기대하지 않습니다.

자산 변환에는 입력 폴더가 필요합니다. 저장소 루트에서 아래처럼 설치 예제의 입력을 복사한 뒤 변환할 수 있습니다. `cube_input`, `torus_input`이 이미 있으면 새 폴더 이름으로 바꿔 이전 결과와 구분하세요.

```bash
mkdir -p src/06_python_usd_manual_standalone_python/output
cp -r ~/isaacsim/standalone_examples/data/cube src/06_python_usd_manual_standalone_python/output/cube_input
cp -r ~/isaacsim/standalone_examples/data/torus src/06_python_usd_manual_standalone_python/output/torus_input
~/isaacsim/python.sh ~/isaacsim/standalone_examples/api/omni.kit.asset_converter/asset_usd_converter.py \
  --folders "$PWD/src/06_python_usd_manual_standalone_python/output/cube_input" \
            "$PWD/src/06_python_usd_manual_standalone_python/output/torus_input"
```

입력 폴더 옆의 `cube_input_converted`, `torus_input_converted`에 생성된 USD를 열어 형상을 확인하세요. 변환기는 STL·OBJ·FBX를 찾아 USD로 바꾸며, 완료 후 앱을 닫습니다. 파일이 생긴 것과 형상·재질이 올바르게 변환된 것은 따로 확인합니다.

스트리밍은 `~/isaacsim/python.sh ~/isaacsim/standalone_examples/api/isaacsim.simulation_app/livestream.py`로 시작합니다. WebRTC 클라이언트와 접속 가능한 네트워크를 별도로 준비해야 하며, 서버 프로세스가 살아 있다는 사실만으로 원격 화면 수신을 확인한 것은 아닙니다.

## 3. 실행 환경과 시간 단위 정리

```text
python.sh → 경로와 라이브러리 환경 준비 → SimulationApp 시작
          → 확장·장면 준비 → World 초기화 → 반복문에서 step
          → 실제 콜백 수·물리 시간 기록 → 앱 종료
```

반복문, 앱 업데이트, 물리 단계는 각각 세는 대상이 다릅니다. 값이 우연히 같을 때도 이름을 구분해 기록하면 렌더 속도나 실행 모드를 바꾼 뒤 결과를 해석하기 쉽습니다.

## 4. 간단한 확인 실험

첫 명령에 **`--headless` 하나만** 추가하세요.

```bash
~/isaacsim/python.sh src/06_python_usd_manual_standalone_python/run.py --steps 120 --headless
```

두 실행의 `requested_steps`는 120으로 같습니다. 코드에서는 `render=True`가 `False`로 바뀌므로 실제 물리 콜백 수와 경과 시간을 비교해야 합니다. Headless의 물리 진행에서는 120번의 1/60초 단계, 즉 약 2초를 기준으로 확인하세요. 기본 GUI의 약 240개·4초와 비교하면 창을 숨기는 옵션이 이 코드에서는 물리 진행 경로도 바꾼다는 사실을 볼 수 있습니다. 두 실행 모두 실제 JSON 값을 최종 기준으로 삼습니다.

## 실행할 때 막히면

- **일반 Python에서 모듈을 찾지 못함**: 설치의 `python.sh`를 사용하세요. `--headless`도 Isaac Sim 런타임과 GPU 준비가 필요합니다.
- **`--stage`에 파일이 없다는 오류**: 출력 예시의 자리표시자를 실제 로컬 USD 경로로 바꾸세요.
- **확장 이름이 보고서에 있지만 기능이 안 보임**: Extensions 창에서 설치 여부와 활성 상태를 확인하세요. 보고서는 요청 목록을 담습니다.
- **Carter URDF가 없다는 오류**: 5.1 URDF importer 확장과 그 `data` 폴더가 설치되어 있는지 확인하세요.
- **Carter가 움직이지 않음**: `--fix-base` 사용 여부와 바퀴 drive 속성을 확인합니다. 앱 업데이트 수를 물리 시간으로 바로 환산하지 마세요.
- **출력 폴더 중복 오류**: `--output`에 존재하지 않는 새 경로를 지정하거나 옵션을 생략합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)에 대응합니다. 설치 launcher, 앱 수명, 시간 진행, Stage 로드와 확장 활성화를 `run.py`로 연결하고, URDF 가져오기는 별도 파일로 제공합니다.

보고서의 요청값과 실제 관찰값을 구분하는 것이 이 실습의 확인 기준입니다. `tutorial.json`의 실행 검증 상태는 `not_run`이며 GUI·URDF·설치 예제 실행까지 검증됐다는 뜻은 아닙니다.
