# 25. Jetbot과 Franka 사이의 작업 인계

권장 학습 순서 **25** · 물리 기초와 Core API 확장 · 출처 ID `t102`

공식 원문: **Adding Multiple Robots** · Isaac Sim **5.1.0** · 인덱스 **t102**

## 만들 결과와 실행 방식

Jetbot이 큐브를 Franka 쪽으로 밀어 운반하고 후퇴한 뒤 Franka가 큐브를 집어 놓습니다. 로봇 두 대를 추가하는 것에 더해 상태 전환과 두 제어기의 책임을 구현합니다.

이 패키지는 `Adding Multiple Robots` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac 5.1 Jetbot `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`와 Franka `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. Jetbot만 `--asset /절대경로/jetbot.usd`로 대체 경로를 지정할 수 있습니다. Franka와 Lula/RMPflow는 5.1 기본 확장/에셋 설정을 사용합니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --steps 2400 --retreat-steps 150
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 2400단계를 사용합니다. 작업 인계와 집기·놓기가 끝나고 120단계 안정화한 뒤 결과를 저장하며, 이후에도 물리 시뮬레이션과 GUI를 유지합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `handover_task.py`
- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `handover_task.py`를 엽니다. `PickPlace`가 큐브와 Franka를 생성한 후 Jetbot을 추가합니다. 큐브는 (0.1,0.3,0.05), Jetbot은 (0,0.3,0), Franka의 base는 (1,0,0) m에 둡니다.
2. `set_world_pose`와 `set_default_state`가 Franka에 함께 적용되는 이유를 읽습니다. 현재 위치만 옮기면 reset 때 원래 자리로 돌아갑니다.
3. 실행 후 터미널의 event를 관찰합니다. `0`에서 Jetbot은 (1.3,0.3) m를 향합니다. 큐브의 이동은 Jetbot과의 실제 물리 접촉으로 일어나며 코드가 큐브를 순간이동시키지 않습니다.
4. Jetbot 목표 오차가 0.04 m보다 작으면 `1 RETREAT`가 됩니다. -8 rad/s를 200단계 적용해 Franka의 작업 영역을 비웁니다.
5. `2 PICK`에 들어가면 Jetbot에 명시적으로 0 속도를 보냅니다. 동시에 실제 큐브 위치를 PickPlaceController의 picking_position에 전달합니다.
6. 결과 파일에서 마지막 event, controller_done, cube_target_error_m를 확인합니다. 인계 동작이 모두 완료되었는지 화면의 큐브 위치와 함께 판정합니다.

## API와 Omniverse/USD 개념

| 상태 | 조건/명령 | 관찰할 내용 |
|---|---|---|
| 0 DRIVE | WheelBasePoseController → DifferentialController | 현재 Jetbot pose를 사용해 목표로 이동 |
| 1 RETREAT | 좌우 -8 rad/s, 기본 200 물리 단계 | 큐브를 남겨두고 뒤로 이동 |
| 2 PICK | 좌우 0 rad/s + Franka PickPlaceController | 멈춘 Jetbot과 움직이는 Franka |

`BaseTask`가 작업 상태를 소유하고 `get_observations()`가 이동 로봇과 내장 PickPlace 관찰을 하나로 합칩니다. `run.py`의 제어 루프는 그 관찰을 읽어 각 로봇에 action을 보냅니다. `pre_step`은 물리 단계 직전에 상태를 갱신하므로 제어 루프에서 새 상태를 보는 시점에는 한 단계 차이가 있을 수 있습니다.

USD Prim 주소는 `/World/Jetbot`처럼 Stage에서 유일해야 하고 Scene의 이름도 유일해야 합니다. 여기서는 공식 `find_unique_string_name`을 사용합니다. 관절 속도 목표는 다음 action까지 남으므로 PICK 상태의 0 명령을 생략하면 Jetbot이 계속 후퇴합니다. `post_reset`은 그리퍼와 event를 함께 복구합니다.

## 관찰과 성공 판정

터미널에 DRIVE→RETREAT→PICK 전환이 실제로 나타나고, Jetbot은 최종 상태에서 멈춰야 합니다. controller_done과 실제 큐브 목표 오차를 별도로 확인합니다. 큐브가 밀리지 않았거나 흘러나간 경우에도 이벤트 진행은 가능하므로 event=2만으로 운반 성공이라 하지 않습니다.

## 한 변수만 바꾸는 실험

`--retreat-steps`만 200에서 150으로 바꿉니다. 후퇴 거리가 줄고 Franka 접근 시 Jetbot과의 간섭 가능성이 달라지는 것을 확인합니다.

## 문제 해결

event=0에 머물면 Jetbot 위치/목표 오차를 확인하고 충분한 단계를 실행합니다. 큐브가 넘어지거나 멀리 밀리면 원문의 간단한 접촉 운반 방식의 한계입니다. `events_dt`는 성공 센서가 아니라 시간 기반 상태 진행 값입니다. 실험 결과를 성공으로 가정하지 말고 cube_target_error_m를 확인합니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Adding Multiple Robots](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html)
- [공식 5.1: creating-the-scene](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html#creating-the-scene)
- [공식 5.1: integrating-a-second-robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html#integrating-a-second-robot)
- [공식 5.1: adding-task-logic](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html#adding-task-logic)
- [공식 5.1: robot-handover](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html#robot-handover)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.
