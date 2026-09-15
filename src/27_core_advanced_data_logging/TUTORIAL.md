# 27. 실제 관절 상태와 목표를 기록하고 재생하기

권장 학습 순서 **27** · 물리 기초와 Core API 확장 · 출처 ID `t105`

공식 원문: **Data Logging** · Isaac Sim **5.1.0** · 인덱스 **t105**

## 이 실습의 의도

Franka의 목표 추종 중 실제 관절 상태와 적용한 관절 목표를 따로 기록해, 센서처럼 읽은 값과 제어 명령의 차이를 익힙니다. 기본 `record` 모드는 y축 사인파로 움직이는 목표를 600단계 기록하며, 재생 모드는 그 로그가 있어야 실행할 수 있습니다. `trajectory`는 관절 action만, `scene`은 action과 목표 물체 pose를 복원하므로 재생 범위를 화면과 기록 필드로 비교할 수 있습니다.

## 실행 후 확인할 것

- record 실행에서 목표 물체의 x,z는 0.45 m이고 y는 기본 진폭 0.1 m로 움직이며 Franka가 따라가는지 봅니다. `trajectory.json`의 `Isaac Sim Data` 아래에 실제 프레임이 저장되어야 합니다.
- `python3 inspect_log.py <기록 경로>`가 실제 로그를 끝까지 읽는지 확인합니다. 각 프레임의 시간은 증가하고 `joint_positions`/`applied_joint_positions`는 각각 9개, `target_position`은 3개, `target_orientation`은 4개의 유한한 숫자여야 합니다. 이 검사는 파일 구조를 검증하며 추종 정확도를 판정하지는 않습니다.
- 같은 프레임에서 측정 `joint_positions`와 명령 `applied_joint_positions`를 비교합니다. drive 응답이 있으므로 두 배열의 완전 일치를 성공 조건으로 삼지 않습니다. record의 `result.json`에서 `replayed_frames=0`, `mean_joint_state_L2_error=null`인 것은 아직 재생하지 않은 정상 결과입니다.
- 같은 입력 로그를 trajectory와 scene으로 각각 재생합니다. 두 모드 모두 관절 목표를 적용하지만, 목표 시각 물체는 trajectory에서 기본 위치에 남고 scene에서 기록된 pose를 따라야 합니다. scene도 전체 물리 세계나 모든 센서를 복원하지는 않습니다.
- 재생 `result.json`의 `data_frames`는 입력 전체 길이이고 `replayed_frames`는 이번에 실제 재생한 길이입니다. `--steps` 또는 headless 기본 600단계 제한으로 둘이 다를 수 있습니다. `mean_joint_state_L2_error`는 실제 재생 상태 차이로 해석하고 0을 강제하지 않습니다.

## 실행 방식

이 패키지는 `Data Logging` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac Sim 5.1의 Franka `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`, `isaacsim.robot.manipulators.examples`와 내장 Lula/RMPflow가 필요합니다. `inspect_log.py`만 실행할 때는 Python 3 표준 라이브러리로 충분합니다. 기록 파일은 이 폴더에서 직접 생성합니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --mode record --output output/record_a
python3 inspect_log.py output/record_a/trajectory.json
"$ISAAC_SIM_ROOT/python.sh" run.py --mode trajectory --input output/record_a/trajectory.json
"$ISAAC_SIM_ROOT/python.sh" run.py --mode scene --input output/record_a/trajectory.json
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 600단계를 사용합니다. record 모드는 기본 600단계만 기록·저장한 뒤에도 목표 추종을 계속하며 추가 기록은 쌓지 않습니다. GUI의 trajectory/scene 모드는 입력 기록 전체를 한 번 재생한 뒤 장면을 유지합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `inspect_log.py`
- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. record 모드로 실행합니다. `FollowTarget` Task가 Franka와 작은 목표 물체를 만듭니다. 목표의 x,z는 각각 0.45 m이고 y는 진폭 0.1 m의 sin 파형으로 움직입니다.
2. `run.py`의 `log_frame(tasks, scene)`를 읽습니다. 측정된 `joint_positions`와 명령인 `applied_joint_positions`를 분리해 저장합니다. 목표의 위치와 쿼터니언도 함께 저장합니다.
3. DataLogger의 `start()` 다음에 반복 물리 단계가 진행되고 `pause()`로 멈춘 후 `save()`가 실행되는 순서를 확인합니다. JSON 파일의 최상위 키는 `Isaac Sim Data`입니다.
4. `inspect_log.py`로 저장된 프레임 수, 시간 순서, 9개 관절 값, 목표 pose 형식을 확인합니다. 실제 파일을 읽는 검사이며 로봇 동작을 재실행하지는 않습니다.
5. trajectory 모드로 기록을 재생합니다. 매 프레임 저장된 joint target을 controller에 보내지만 목표 시각 물체는 기본 위치에 남아 있습니다.
6. scene 모드로 재생합니다. action 외에 목표 물체의 위치·자세도 기록값으로 복원되므로 화면에서 원래 목표 이동을 함께 볼 수 있습니다.
7. 각 재생 결과의 `mean_joint_state_L2_error`를 봅니다. 같은 action을 적용해도 reset 상태와 물리 수치해석 때문에 실제 상태가 기록과 완전히 같지 않을 수 있습니다.
8. 원문 기본 GUI 흐름은 Window > Examples > Robotics Examples → Manipulation > Follow Target Task → LOAD → FOLLOW TARGET → START LOGGING입니다. 목표를 이동하고 STOP LOGGING 후 Save Data로 JSON을 저장합니다. 이 패키지의 자동 목표 이동은 같은 DataLogger API를 독립 실행형으로 옮긴 실습입니다.

## API와 Omniverse/USD 개념

| 항목 | 의미 |
|---|---|
| `world.get_data_logger()` | World가 소유한 DataLogger를 가져옵니다. |
| `add_data_frame_logging_func` | 매 물리 단계에서 수집할 딕셔너리를 정의합니다. |
| `start` / `pause` | 수집을 시작/중단합니다. 이미 수집한 데이터는 유지됩니다. |
| `save` / `load` | 실제 JSON 데이터 저장/읽기입니다. |
| `get_data_frame(index)` | 저장 배열의 순서에 해당하는 프레임을 읽습니다. |
| `current_time` / `current_time_step` | 벽시계가 아닌 시뮬레이션 시간/단계입니다. |
| `ArticulationAction` | 기록된 관절 목표를 다시 controller에 전달합니다. |

USD Stage는 로봇과 목표 물체의 구조를 담습니다. JSON은 전체 USD 장면이 아니라 선택한 상태/명령의 시간 기록입니다. scene 모드도 임의의 모든 물체·센서·충돌 상태를 복원하는 기능은 아니며 이 실습에서 기록한 목표 pose와 관절 action을 복원합니다. 리스트로 바꾸는 `.tolist()`는 NumPy 배열을 JSON에 저장하기 위한 변환입니다.

재생 반복문의 index는 저장 프레임 배열의 0부터 시작합니다. 원문의 시뮬레이션 단계 인덱스와 배열 인덱스를 그대로 같다고 가정하면 중간에 시작한 로그에서 어긋날 수 있어 여기서는 분리했습니다. 프레임의 실제 기록 시간은 출력에 따로 표시합니다.

## 한 변수만 바꾸는 실험

record의 `--amplitude`만 0.1에서 0.05로 바꿔 새 output 폴더에 저장합니다. 목표 y 범위가 절반으로 줄어드는지 JSON과 화면에서 비교합니다.

## 문제 해결

output/record_a가 이미 있으면 덮어쓰기 방지를 위해 중단합니다. 새 이름을 사용합니다. 재생 입력은 이 패키지가 기록한 9관절 Franka 로그여야 합니다. 다른 로봇/이전 버전 파일은 구조와 단위를 별도로 검토해야 합니다. 기록을 너무 짧게 하면 추종이 안정화되기 전 동작만 포함됩니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Data Logging](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html)
- [공식 5.1: recording-data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html#recording-data)
- [공식 5.1: inspect-the-data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html#inspect-the-data)
- [공식 5.1: replaying-back-data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html#replaying-back-data)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
