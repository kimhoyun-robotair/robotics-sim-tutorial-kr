# 23. 차동구동 식에서 목표 위치 제어까지

권장 학습 순서 **23** · 물리 기초와 Core API 확장 · 출처 ID `t100`

공식 원문: **Adding a Controller** · Isaac Sim **5.1.0** · 인덱스 **t100**

## 만들 결과와 실행 방식

직접 작성한 UnicycleController와 공식 DifferentialController가 같은 바퀴 목표를 만드는 것을 읽고, WheelBasePoseController가 실제 로봇 위치를 피드백해 목표에 정지하는 과정을 관찰합니다.

이 패키지는 `Adding a Controller` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac 5.1 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`가 필요합니다. 로컬 에셋은 `--asset /절대경로/jetbot.usd`로 넘깁니다. 주변 참조 파일도 보존합니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --controller custom --linear 0.2 --angular 0.785398
"$ISAAC_SIM_ROOT/python.sh" run.py --controller differential --linear 0.2 --angular 0.785398
"$ISAAC_SIM_ROOT/python.sh" run.py --controller pose --goal 0.8 0.8
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 900단계를 사용합니다. 기본 900단계의 위치·경로를 결과 파일에 저장한 뒤에도 창을 닫을 때까지 매 스텝 제어 명령을 계속 계산합니다. 이후 관찰 구간의 샘플은 메모리에 추가하지 않습니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `run.py` 안의 `UnicycleController`를 읽습니다. 바퀴 반지름 r=0.03 m, 좌우 간격 b=0.1125 m이며 입력은 전진 속도 v와 yaw 속도 ω입니다.
2. 첫 실행 직후 custom과 built-in의 바퀴 목표 출력값을 비교합니다. `left=(v-ωb/2)/r`, `right=(v+ωb/2)/r`이 어떻게 좌우 차이를 만드는지 손으로 계산합니다.
3. custom과 differential 모드에서는 현재 위치를 목표 계산에 넣지 않습니다. 일정한 속도로 회전하는 열린 고리 제어임을 관찰합니다.
4. pose 모드에서는 매번 `get_world_pose()`를 읽어 `forward(start_position, start_orientation, goal_position)`에 넣습니다. 로봇이 방향을 맞춘 뒤 전진하고 목표 반경 0.04 m 안에서 정지하는지 봅니다.
5. `result.json`의 60단계 간격 위치와 목표 오차를 비교합니다. 열린 고리 모드의 목표 오차는 참고 측정값이며 도달 의무가 있는 제어가 아닙니다.

## API와 Omniverse/USD 개념

`BaseController.forward()`는 명령 계산의 인터페이스이며 출력은 `ArticulationAction`입니다. 클래스 이름만 Controller로 바꿔도 물리가 진행되지는 않습니다. 매 단계 `robot.apply_wheel_actions(action)`과 `world.step()`이 필요합니다.

| 계층 | 입력 → 출력 | 현재 상태 사용 |
|---|---|---|
| 직접 UnicycleController | [m/s, rad/s] → [왼쪽 rad/s, 오른쪽 rad/s] | 없음 |
| DifferentialController | 같은 차동구동 입력 → 바퀴 action | 없음 |
| WheelBasePoseController | 현재 pose와 세계 목표 → 내부 DifferentialController action | 위치와 방향 |

세계 좌표 목표는 `[x,y,z]`이며 이 제어기는 평면 x,y 거리와 yaw를 사용합니다. USD에서 Jetbot의 Prim 주소와 Scene 이름은 별개의 식별자입니다. 관절 속도 목표는 다음 명령까지 유지될 수 있으므로 도착 후 0 속도를 명시하는 것이 필요합니다.

## 관찰과 성공 판정

custom과 differential의 초기 바퀴 계산 출력이 같아야 합니다. pose 실행은 `final_goal_error_m`가 0.04 m 근처 이하로 내려가고 정지하는 것을 확인합니다. 짧은 실행에서는 아직 이동 중일 수 있습니다.

## 한 변수만 바꾸는 실험

pose 모드에서 `--goal`의 x만 0.8에서 0.4로 바꾸고 같은 900단계를 사용합니다. 도착 방향과 이동 시간을 비교합니다.

## 문제 해결

로봇이 회전만 하면 현재 쿼터니언과 목표 좌표가 올바른지 확인합니다. 사용자 에셋의 바퀴 반지름과 간격이 다르면 식의 상수도 달라집니다. 네트워크 asset root가 닿지 않으면 로컬 `--asset`을 사용합니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)
- [공식 5.1: creating-a-custom-controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html#creating-a-custom-controller)
- [공식 5.1: using-the-available-controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html#using-the-available-controllers)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.
