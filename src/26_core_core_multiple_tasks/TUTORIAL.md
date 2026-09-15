# 26. 좌표 offset과 고유 이름으로 여러 Task 확장하기

권장 학습 순서 **26** · 물리 기초와 Core API 확장 · 출처 ID `t103`

공식 원문: **Multiple Tasks** · Isaac Sim **5.1.0** · 인덱스 **t103**

## 만들 결과와 실행 방식

한 Stage 안에 독립적인 Jetbot–Franka 인계 작업 세 개를 배치합니다. 각 작업의 좌표, 이벤트, 로봇 이름, 제어기 상태가 서로 섞이지 않도록 구성합니다.

이 패키지는 `Multiple Tasks` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac Sim 5.1과 Jetbot `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`, Franka `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`, 내장 RMPflow 확장이 필요합니다. `--asset`은 Jetbot USD만 지정하며 Franka는 기본 5.1 asset root를 사용합니다. 작업 수가 증가하면 GPU 메모리/CPU 물리 비용도 늘어납니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --tasks 3 --spacing 2 --seed 7
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --tasks 1 --seed 7 --steps 2400
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 2400단계를 사용합니다. 모든 작업의 집기·놓기가 끝나고 120단계 안정화한 뒤 결과를 저장하며, 이후에도 물리 시뮬레이션과 GUI를 유지합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `handover_task.py`
- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `run.py`의 `tasks` 생성식을 봅니다. 기본 세 작업의 y offset은 -2,0,2 m이며 각 작업에는 고유한 `lane_0`, `lane_1`, `lane_2` 이름이 주어집니다.
2. `handover_task.py`에서 PickPlace에 offset을 넘기는 부분과 `_move_task_objects_to_their_frame()`을 비교합니다. PickPlace가 큐브와 Franka에 offset을 이미 적용했으므로 외부 Task의 `_task_objects`에는 Jetbot만 등록합니다.
3. 실행 후 출력된 각 작업의 params에서 Jetbot, Franka, cube의 이름을 비교합니다. 같은 Stage 안의 Prim 경로와 Scene 이름 충돌이 없어야 합니다.
4. 각 lane의 Jetbot 목표 x가 1.2~1.6 m에서 달라지는 것을 확인합니다. `default_rng(seed)`를 사용하므로 같은 seed는 같은 목표를 생성합니다.
5. 터미널 event 딕셔너리를 봅니다. 관찰 키가 `lane_0_event`, `lane_1_event`처럼 구별되므로 한 작업의 도착이 다른 작업을 후퇴시키지 않아야 합니다.
6. `result.json` 배열에서 lane별 controller_done과 실제 큐브 오차를 비교합니다. 모든 로봇이 같은 순간에 완료한다고 가정하지 않습니다.

## API와 Omniverse/USD 개념

각 lane은 자체 `HandoverTask`, `WheelBasePoseController`, `DifferentialController`, `PickPlaceController`를 가집니다. 제어기의 상태 머신을 여러 로봇이 공유하면 한 로봇의 진행 단계가 다른 로봇에 영향을 주므로 인스턴스를 각각 만듭니다.

| 확장 문제 | 코드의 해결 방법 |
|---|---|
| 물체가 겹침 | 모든 해당 물체와 목표를 같은 offset으로 평행이동 |
| 두 번 이동됨 | 내장 PickPlace가 적용한 offset을 외부에서 다시 적용하지 않음 |
| USD Prim 경로 충돌 | `find_unique_string_name` + `is_prim_path_valid` |
| Scene 객체 이름 충돌 | `find_unique_string_name` + `scene.object_exists` |
| 관찰 딕셔너리가 덮어써짐 | 작업 이름이 포함된 event 키와 고유 객체 이름 |
| 제어 단계 혼동 | 작업마다 별도 controller 인스턴스와 reset |

USD Stage는 하나지만 논리적 Task가 여러 개일 수 있습니다. offset은 새 세계를 만드는 것이 아니라 같은 세계 안에서 좌표를 이동하는 것입니다. 이 실습은 물리 격리나 병렬 학습 환경을 보장하지 않습니다. lane 간격을 너무 줄이면 다른 작업 물체와도 충돌할 수 있습니다.

## 관찰과 성공 판정

세 lane이 각자 DRIVE→RETREAT→PICK을 진행하고 결과 배열에 서로 다른 task 이름이 있어야 합니다. 실제 cube_target_error_m로 lane별 성공을 판단합니다. 무작위 운반 거리 때문에 시간 기반 집기 controller가 놓칠 수 있으며 이를 결과에 그대로 남깁니다.

## 한 변수만 바꾸는 실험

`--tasks 3`을 `--tasks 2`로만 바꿔 이름 충돌 없이 필요한 두 쌍만 생성되는지 확인합니다. 다른 실험에서는 `--seed`만 바꿔 운반 거리 변화가 집기 성능에 미치는 영향을 비교합니다.

## 문제 해결

GPU 메모리가 부족하면 --tasks 1로 동일 흐름부터 확인합니다. lane이 겹치면 offset이 두 번 적용되었거나 spacing을 줄였는지 확인합니다. 프로그램은 spacing 1.5 m 미만을 거부합니다. 한 lane 완료가 전체 성공을 의미하지 않으므로 결과 배열의 모든 항목을 봅니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Multiple Tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html)
- [공식 5.1: parameterizing-tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html#parameterizing-tasks)
- [공식 5.1: scaling-to-many-tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html#scaling-to-many-tasks)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.
