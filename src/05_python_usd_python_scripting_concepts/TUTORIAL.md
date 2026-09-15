# 05. 시뮬레이션은 누가 진행시키는가?

## 이번에 배우는 것

**같은 큐브 낙하를 두 가지 방식으로 실행하고, 물리 계산을 진행시키는 주체가 누구인지 비교합니다.**

01번에서는 `World`에 콜백을 등록해 큐브의 상태를 관찰했습니다. 이번에는 그 콜백이 실행되도록 **누가 시뮬레이션을 진행하는지** 살펴봅니다.

| 구분 | 독립 Python 실행 | Isaac Sim의 Script Editor 실행 |
|---|---|---|
| 실습 파일 | `run.py` | `script_editor.py` |
| 시작 장소 | 터미널 | 이미 열린 Isaac Sim 창 |
| 앱 실행 | 코드에서 `SimulationApp` 생성 | 이미 앱이 실행 중 |
| 물리 진행 | 내 반복문에서 `world.step()` 호출 | 재생 중인 앱이 진행 |
| 내 코드의 역할 | 물리를 진행하고 결과 기록 | 앱을 기다리며 콜백으로 결과 관찰 |
| 실습 완료 후 | 코드에서 앱 종료 | 물리 재생만 일시정지하고 창 유지 |

두 방식 모두 한 변이 0.4 m인 큐브를 중심 높이 2 m에서 떨어뜨립니다. 바닥에 놓이면 중심 높이는 약 0.2 m가 됩니다.

## 1. 먼저 `run.py` 실행하기

Isaac Sim 5.1이 설치된 환경에서 실행합니다. 아래는 저장소 루트에서 실행하는 Linux 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/05_python_usd_python_scripting_concepts/run.py --steps 120
```

큐브가 떨어지고, 물리 계산 120 step이 끝나면 앱이 종료됩니다. 화면을 계속 열어 두고 싶으면 `--steps 120`을 빼세요. 창 없이 실행하려면 `--headless`를 추가합니다.

### 코드에서 볼 부분

실행 흐름은 다음과 같습니다.

```text
SimulationApp으로 앱 시작
    → World와 큐브 생성
    → world.reset()으로 초기화
    → 물리 콜백 등록
    → 반복문에서 world.step() 호출
    → 콜백 제거 및 앱 종료
```

이 예제의 콜백은 두 값을 셉니다.

```python
callback_count = 0
elapsed_time = 0.0

def on_physics(dt):
    nonlocal callback_count, elapsed_time
    callback_count += 1
    elapsed_time += float(dt)

world.add_physics_callback("count_physics", on_physics)
```

- `callback_count`: 물리 콜백이 실행된 횟수
- `dt`: 이번 물리 단계의 시간 간격(초)
- `elapsed_time`: `dt`를 더해 구한 시뮬레이션 경과 시간
- `nonlocal`: 함수 바깥에서 만든 두 변수를 함수 안에서 수정한다는 뜻

**콜백 등록만으로 물리가 계속 진행되지는 않습니다.** 이 파일에서는 반복문 안의 다음 호출이 물리를 진행시킵니다.

```python
world.step(render=not args.headless)
```

물리 단계 직전에 `on_physics(dt)`가 호출됩니다. `world.step()`이 끝나면 반복문에서 콜백 횟수, 누적 시간, 큐브 높이를 CSV 한 행으로 기록합니다.

### 실행 결과 확인하기

결과는 이 튜토리얼 폴더의 `output/날짜-시간/timeline.csv`에 저장됩니다.

| CSV 열 | 의미 | 120단계를 끝낸 마지막 행의 기대값 |
|---|---|---|
| `loop_iteration` | 반복문 실행 횟수 | `120` |
| `physics_callbacks` | 물리 콜백 실행 횟수 | `120` |
| `simulated_time_s` | 누적 물리 시간 | 약 `2.0`초 |
| `cube_height_m` | 큐브 중심의 높이 | 약 `0.2` m |

코드에서 물리 간격을 `1/60초`로 설정했으므로 **120 × 1/60 = 2초**입니다.

여기서 2초는 **시뮬레이션 속 시간**입니다. 앱을 켜거나 화면을 그리는 데 시간이 더 걸리면, 실제 시계로 잰 실행 시간은 더 길 수 있습니다.

## 2. 같은 장면을 Script Editor에서 실행하기

이번에는 Isaac Sim 앱을 먼저 켜고, 그 안에서 코드를 실행합니다.

1. 앞의 `run.py` 실행을 종료합니다.
2. `~/isaacsim/isaac-sim.sh`로 **새 Isaac Sim 창**을 엽니다.
3. **File > New**로 빈 장면을 준비합니다.
4. **Window > Script Editor**를 엽니다.
5. 이 폴더의 `script_editor.py` 전체를 붙여 넣고 실행합니다.

`run.py`가 아니라 **`script_editor.py`를 붙여 넣으세요.** 이미 실행 중인 앱 안에서는 `SimulationApp`을 다시 생성하지 않습니다.

### 코드에서 볼 부분

장면을 만들고 `await world.reset_async()`로 초기화한 뒤, 다음 콜백을 등록합니다.

```python
samples = []

def record(dt):
    samples.append((float(dt), float(cube.get_world_pose()[0][2])))

world.add_physics_callback("interactive_record", record)
```

앱이 물리를 진행할 때마다 `record()`가 호출되어 **시간 간격과 큐브 높이**를 저장합니다. 내 코드는 다음 반복문에서 관찰값이 충분히 모이기를 기다립니다.

```python
while len(samples) < 120:
    await omni.kit.app.get_app().next_update_async()
```

여기서 `await`는 **“내 작업은 잠시 기다릴 테니, 앱이 화면 갱신과 물리 계산 등 다른 작업을 처리하게 하자”**는 뜻입니다. 이 반복문에는 `world.step()`이 없습니다. 물리는 재생 중인 앱이 진행합니다.

앱이 이런 작업을 반복해서 처리하는 흐름을 **이벤트 루프**라고 부릅니다. `await` 없이 기다리는 반복문만 계속 돌리면 앱이 다른 작업을 처리하지 못해 화면이 멈출 수 있습니다.

파일 마지막의 `asyncio.ensure_future(run_interactive())`는 이 비동기 작업을 앱의 루프에서 실행하도록 예약합니다.

### 실행 결과 확인하기

- 큐브가 떨어집니다.
- 물리 관찰값이 **120개 이상** 모이면 콜백을 제거하고 재생을 일시정지합니다.
- 출력 영역에 `Interactive callback samples:`와 `(dt, 높이)` 목록이 나타납니다.
- Isaac Sim 창은 그대로 남습니다. 이 방식은 CSV를 저장하지 않습니다.

앱 업데이트 한 번과 물리 단계 한 번은 항상 같지는 않으므로, 이 코드는 앱 업데이트 횟수 대신 **실제 콜백으로 모은 관찰값 수**를 확인합니다.

## 3. 두 방식의 차이 정리

```text
run.py
내 반복문 → world.step() → 물리 콜백 실행 및 물리 계산 → 결과 기록

script_editor.py
앱의 재생 흐름 → 물리 콜백 실행 및 물리 계산
내 비동기 작업 → await로 기다림 → 관찰값이 충분한지 확인
```

**두 방식 모두 콜백을 사용합니다. 차이는 독립 실행에서는 내가 물리 진행을 호출하고, Script Editor에서는 앱의 진행 흐름에 맞춰 내 코드를 실행한다는 점입니다.**

## 4. 간단한 확인 실험

`run.py`를 `--steps 60`으로 실행해 보세요.

- 반복 횟수와 콜백 횟수: 60회
- 누적 물리 시간: 약 1초

큐브는 1초와 2초 모두 바닥에 놓여 있을 수 있습니다. **시간 차이는 마지막 큐브 모습보다 CSV의 `simulated_time_s`로 확인**하세요.

## 실행할 때 막히면

- **`No module named isaacsim`**: 일반 Python 대신 Isaac Sim의 `python.sh`로 실행하세요. Windows에서는 `python.bat`을 사용합니다.
- **Script Editor에서 기존 World 관련 오류**: 새 Isaac Sim 창에서 실습하세요. 이 코드는 이미 World가 있으면 실행을 중단합니다.
- **Script Editor에서 결과 출력이 안 나옴**: 수동으로 Pause했다면 Play를 재개하세요. 물리가 멈추면 콜백 관찰값도 늘어나지 않습니다.
- **`run.py`가 계속 실행됨**: `--steps`를 생략한 GUI 실행의 정상 동작입니다. 창을 닫거나 단계 수를 지정하세요. Headless 실행은 생략 시 120단계입니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Python Scripting Concepts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html)에 대응하는 한국어 실습입니다. 앱 시작과 독립 Python 실행은 [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html), 물리 콜백은 [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)를 함께 참고하세요.

큐브 설정, CSV 기록, 120개 관찰값 수집은 개념을 비교하기 위해 이 폴더에 구성한 실습 코드입니다. 위 기대값은 실행 시 확인할 기준이며, 실행 검증 상태는 `tutorial.json`을 참고하세요.
