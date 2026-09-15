# 24. Franka 집기·놓기를 Task로 정리하기

권장 학습 순서 **24** · 물리 기초와 Core API 확장 · 출처 ID `t101`

공식 원문: **Adding a Manipulator Robot** · Isaac Sim **5.1.0** · 인덱스 **t101**

## 만들 결과와 실행 방식

Franka가 5.15 cm 큐브를 집어 목표 위치에 놓습니다. 이 폴더의 LocalPickTask와 Isaac의 내장 PickPlace Task를 선택해 동일한 controller 입력 구조를 확인합니다.

이 패키지는 `Adding a Manipulator Robot` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac Sim 5.1 에셋 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`와 Isaac에 함께 설치된 `isaacsim.robot.manipulators.examples`, Lula/RMPflow 확장이 필요합니다. 기본 asset root 또는 5.1 로컬 에셋 설정에서 Franka를 읽을 수 있어야 합니다. 별도 로봇 모델이나 다른 로컬 튜토리얼은 필요 없습니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --task custom
"$ISAAC_SIM_ROOT/python.sh" run.py --task builtin
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 1800단계를 사용합니다. 집기·놓기가 완료되고 120단계 안정화한 뒤 결과를 저장하며, 이후에도 물리 시뮬레이션과 GUI를 유지합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `pick_task.py`
- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `pick_task.py`의 `set_up_scene`를 읽습니다. 지면, `Franka`, `DynamicCuboid`를 이 Task가 직접 생성합니다. 큐브 중심 시작점은 (0.3,0.3,0.3) m, 목표는 (-0.3,-0.3,0.02575) m입니다.
2. `post_reset()`에서 gripper를 열고 파란색을 복구하는 부분을 확인합니다. reset은 물체 위치뿐 아니라 실습의 성공 상태도 초기화해야 합니다.
3. custom 모드로 실행합니다. `run.py`는 `world.get_observations()`에서 큐브 위치, 목표 위치, Franka 관절 위치를 읽고 `PickPlaceController.forward()`에 넣습니다.
4. 큐브가 들어 올려져 목표에 놓이는지 봅니다. custom Task는 큐브 중심이 목표에서 3 cm 안에 들면 초록색으로 바꿉니다. 처음에는 파란색이어야 합니다.
5. `result.json`에서 `controller_done`과 `cube_target_error_m`를 함께 봅니다. controller의 상태 머신 종료와 실제 물체 도착은 서로 다른 측정입니다.
6. builtin 모드로 다시 실행합니다. `get_params()`가 반환한 `robot_name`/`cube_name`으로 객체를 찾아 동일한 controller를 사용할 수 있는지 코드를 비교합니다.

## API와 Omniverse/USD 개념

| 구성 | 책임 |
|---|---|
| `Franka` | articulation, end effector, parallel gripper 접근을 제공하는 로봇 클래스 |
| `PickPlaceController` | 접근→하강→잡기→상승→운반→해제 같은 단계의 동작을 생성 |
| `BaseTask.set_up_scene` | 해당 작업에 필요한 물체와 로봇을 Scene에 생성 |
| `get_observations` | 제어에 필요한 현재 상태를 이름별 딕셔너리로 공개 |
| `pre_step` | 매 물리 단계 전에 실제 목표 달성 여부를 검사 |
| `post_reset` | 그리퍼·색·성공 플래그를 초기 상태로 복구 |
| `get_params` | 작업이 생성한 로봇/물체 이름 등의 구성 정보를 공개 |

USD에는 로봇 link/joint의 물리 구조와 시각 mesh가 들어 있습니다. Franka 래퍼는 이 모델을 로딩하고 필요한 제어 핸들을 제공합니다. end effector 위치 제어는 곧바로 강체를 순간이동시키는 방식이 아니라 내부 운동 생성기가 관절 목표로 바꿔서 실행합니다.

원문은 직접 Scene 구성, 직접 만든 Task, 내장 PickPlace 순으로 발전합니다. 여기서는 직접 구성 코드를 `LocalPickTask.set_up_scene`에 모두 남기고 `--task`로 비교하게 했습니다. Task가 장면/관찰을, Controller가 동작 계산을 맡는 경계가 핵심입니다.

## 관찰과 성공 판정

집기 전 파란 큐브가 실제로 들리고 내려가야 합니다. `controller_done=true`만으로 성공을 판정하지 않습니다. 충분히 안정된 마지막 실제 큐브 위치가 목표 3 cm 이내인지 확인합니다. 코드는 controller 종료 뒤 120단계 더 안정화합니다.

## 한 변수만 바꾸는 실험

`--target -0.25 -0.3 0.02575`로 x만 변경합니다. z를 큐브 반높이로 유지해 지면 위 목표의 의미를 확인합니다.

## 문제 해결

1800단계 전에 창을 닫으면 결과는 부분 실행입니다. 큐브를 놓쳤는데 controller_done이 참일 수 있습니다. 이 controller는 이벤트 시간으로 진행하는 예제이므로 물리 성공을 별도로 확인해야 합니다. 로봇이 안 뜨면 Franka USD와 RMPflow 확장 로딩 오류를 먼저 확인합니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Adding a Manipulator Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html)
- [공식 5.1: creating-the-scene](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html#creating-the-scene)
- [공식 5.1: using-the-pickandplace-controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html#using-the-pickandplace-controller)
- [공식 5.1: what-is-a-task](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html#what-is-a-task)
- [공식 5.1: use-the-pick-and-place-task](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html#use-the-pick-and-place-task)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
