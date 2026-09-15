# 02. Jetbot을 불러오고 바퀴 관절을 직접 움직이기

권장 학습 순서 **02** · 첫 실행과 로봇 만나기 · 출처 ID `t099`

공식 원문: **Hello Robot** · Isaac Sim **5.1.0** · 인덱스 **t099**

## 만들 결과와 실행 방식

NVIDIA Jetbot USD를 참조로 불러오고 두 바퀴에 rad/s 명령을 보냅니다. Robot 래퍼와 바퀴 전용 WheeledRobot 래퍼를 같은 조건으로 비교합니다.

이 패키지는 `Hello Robot` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac Sim 5.1 에셋 루트의 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`가 필요합니다. 기본 asset root가 네트워크 주소면 접근이 필요합니다. 에셋 팩을 로컬에 둔 경우 `--asset /절대경로/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`로 지정할 수 있습니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --api robot
"$ISAAC_SIM_ROOT/python.sh" run.py --api wheeled --wheel-speeds 2 4
```

`run.py`는 `--steps`를 생략하면 사용자가 창을 닫을 때까지 물리와 제어를 계속 실행합니다. 양수 `--steps N`을 지정하면 N단계 후 종료합니다. `--headless`에서 `--steps`를 생략하면 600단계 후 종료합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `--api robot`으로 실행합니다. `add_reference_to_stage`가 Stage의 `/World/Jetbot` 아래에 에셋을 합성하는 줄과 `Robot(...)`이 그 Prim을 감싸는 줄을 따로 확인합니다. Robot 생성만으로 Jetbot 모델이 생기는 것은 아닙니다.
2. 터미널의 reset 전/후 DOF 값을 비교합니다. reset 전에는 핸들이 준비되지 않았고 reset 후에는 관절 이름과 인덱스를 읽을 수 있습니다.
3. Stage에서 Jetbot을 선택하고 F를 눌러 봅니다. 좌우 4 rad/s 명령에서는 전진하는지, 출력되는 실제 바퀴 속도가 명령을 따라가는지 봅니다.
4. 두 번째 명령으로 실행해 WheeledRobot의 `wheel_dof_names`와 `apply_wheel_actions`를 확인합니다. 좌우 속도를 2와 4로 다르게 주면 곡선으로 움직입니다.
5. 각 실행의 `result.json`에서 `wheel_indices`, `command_rad_s`, `displacement_m`, `orientation_wxyz`를 비교합니다. 첫 위치를 뺀 이동량을 계산하므로 USD의 초기 위치와 혼동하지 않습니다.

## API와 Omniverse/USD 개념

| API/개념 | 설명 |
|---|---|
| USD reference | 원본 USD를 복사하지 않고 현재 Stage의 특정 주소에서 구성하는 합성 방식입니다. |
| `Robot` | 관절로 연결된 강체 묶음인 articulation을 조작하는 일반 래퍼입니다. |
| `world.reset()` | USD 정의를 물리 엔진에 준비시키고 초기 상태로 되돌립니다. 관절 조회는 이 다음입니다. |
| `get_dof_index(name)` | 이름으로 관절 인덱스를 찾습니다. 모델 파일의 내부 순서를 외우지 않아도 됩니다. |
| `ArticulationAction` | 위치/속도/힘 목표와 대상 관절 인덱스를 담습니다. 명령 자체가 물리 결과는 아닙니다. |
| `apply_action` | articulation controller에 목표를 전달합니다. 여기서는 바퀴 관절 속도를 제어합니다. |
| `WheeledRobot` | 바퀴 이름을 기억하고 바퀴 배열을 전체 articulation의 올바른 인덱스로 변환합니다. |

회전 관절 속도 단위는 rad/s입니다. 로봇의 전진 속도 m/s와 같지 않습니다. 바퀴 접촉, 마찰, 모터 drive가 명령을 실제 이동으로 바꿉니다. 쿼터니언은 Euler 각도가 아니며 Core API의 배열 순서는 w,x,y,z입니다.

## 관찰과 성공 판정

reset 뒤 Jetbot에 두 바퀴 DOF가 보이고 바퀴 목표를 보낸 뒤 실제 위치 또는 자세가 변해야 합니다. 출력된 이동량이 0 근처이면 목표 숫자만 바뀌었을 가능성을 조사합니다.

## 한 변수만 바꾸는 실험

같은 `--api robot`에서 `--wheel-speeds 4 4`를 `--wheel-speeds -4 -4`로만 바꿉니다. 전진/후진 방향이 뒤집히는지 봅니다.

## 문제 해결

에셋을 읽을 수 없으면 지정한 파일과 그 USD가 참조하는 하위 리소스를 함께 설치해야 합니다. 관절 이름 오류는 다른 로봇 USD를 넣었을 때 생깁니다. 이 실습의 두 이름은 Jetbot 전용입니다. 실행 중 GUI Stop/Play 대신 프로그램을 다시 실행하면 초기 상태가 확실히 복구됩니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)
- [공식 5.1: adding-a-robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html#adding-a-robot)
- [공식 5.1: move-the-robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html#move-the-robot)
- [공식 5.1: using-the-wheeledrobot-class](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html#using-the-wheeledrobot-class)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
