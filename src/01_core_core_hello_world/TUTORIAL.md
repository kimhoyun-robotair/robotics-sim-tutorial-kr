# 01. 처음 만드는 물리 세계: 큐브의 낙하를 읽기

권장 학습 순서 **01** · 첫 실행과 로봇 만나기 · 출처 ID `t098`

공식 원문: **Hello World** · Isaac Sim **5.1.0** · 인덱스 **t098**

## 만들 결과와 실행 방식

0.5 m 큐브가 높이 1 m에서 떨어져 바닥 위에 멈춥니다. 물리 단계마다 실제 위치와 속도를 CSV에 기록합니다.

이 패키지는 `Hello World` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- 외부 USD 에셋이 필요 없습니다. 큐브와 지면을 코드로 만듭니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --steps 300 --height 2.0
```

`run.py`는 `--steps`를 생략하면 사용자가 창을 닫을 때까지 물리와 제어를 계속 실행합니다. 양수 `--steps N`을 지정하면 N단계 후 종료합니다. `--headless`에서 `--steps`를 생략하면 300단계 후 종료합니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. `run.py`의 `World(...)`를 찾습니다. 길이 단위는 미터, 물리 시간 간격은 1/60초입니다. `--steps 300`은 약 5초의 시뮬레이션이며 컴퓨터의 실제 실행 시간과 다릅니다.
2. `DynamicCuboid`의 `prim_path="/World/FallingCube"`와 `name="falling_cube"`를 비교합니다. 전자는 Stage의 주소, 후자는 Scene에서 객체를 찾는 이름입니다. Stage 창에서 `/World/FallingCube`를 선택하고 `F`로 화면 중심에 맞춥니다.
3. 첫 실행 중 터미널의 `position_m`과 `velocity_mps`를 봅니다. 낙하 중 z 속도는 음수가 되고 접촉 후 0 근처로 줄어듭니다.
4. `world.reset()` 다음에 콜백을 등록하는 이유를 확인합니다. USD의 물체 정의를 PhysX에서 다룰 준비가 된 뒤 상태를 읽어야 합니다. `observe(step_size)`는 매 물리 단계의 직전에 호출됩니다.
5. 종료 후 출력된 `output/<번호>/fall.csv`를 텍스트 편집기로 엽니다. 헤더의 단위, 최초 행, 낙하 중 행, 마지막 행을 비교합니다. `result.json`의 최종 높이는 0.25 m 근처인지 확인합니다.

## API와 Omniverse/USD 개념

| 코드/API | 이 실습에서의 역할 |
|---|---|
| `SimulationApp` | Omniverse Kit와 확장을 먼저 시작합니다. 이 호출 전에 `omni`/`pxr`를 가져오지 않습니다. |
| `World` / `World.instance()` | 물리 시간, Scene, callback을 관리합니다. 현재 프로세스의 World 싱글턴을 돌려줍니다. |
| `world.scene.add` | Python 객체를 이름으로 등록하고 reset 시 물리 핸들을 초기화합니다. |
| `DynamicCuboid` | 보이는 큐브, 강체, 충돌체를 함께 정의하는 Core API 편의 클래스입니다. |
| `get_world_pose` | 세계 좌표의 위치와 `[w,x,y,z]` 쿼터니언을 읽습니다. |
| `get_linear_velocity` | 강체 중심의 실제 속도를 m/s로 읽습니다. |
| `add_physics_callback` | `step_size` 인자를 받는 함수를 각 물리 단계 직전에 실행합니다. |

USD Stage는 장면 데이터베이스, Prim은 그 안의 항목입니다. 화면에 보이는 기하와 질량/충돌 같은 물리 정보는 서로 다른 속성이지만 DynamicCuboid가 입문에 필요한 것을 한 번에 붙입니다. `world.step(render=False)`도 물리는 진행합니다. 렌더링 빈도와 물리 빈도를 혼동하지 마세요.

## 관찰과 성공 판정

`--steps 300`으로 제한한 실행에서 CSV에 300개의 물리 관찰 행이 있고 마지막 큐브 중심 z가 약 0.25 m, 속도가 거의 0이면 기본 관찰을 만족합니다. 기본 GUI 실행의 행 수는 창을 닫은 시점에 따라 달라집니다. 콜백은 단계 직전 값이므로 `result.json` 마지막 상태와 CSV 끝값에는 한 단계 차이가 있을 수 있습니다.

## 한 변수만 바꾸는 실험

`--height`만 1.0에서 2.0으로 바꿉니다. 더 늦게 바닥에 닿지만 정지 높이는 같아야 합니다. 큐브 크기를 함께 바꾸지 않습니다.

## 문제 해결

`No module named isaacsim`이면 일반 Python 대신 Isaac Sim 5.1의 `python.sh`로 실행합니다. 큐브가 화면 밖이면 Stage에서 선택하고 F를 누릅니다. `--steps 10`처럼 짧으면 바닥까지 도달하지 않습니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
- [공식 5.1: singleton-world](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html#singleton-world)
- [공식 5.1: continuously-inspecting-the-object-properties-during-simulation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html#continuously-inspecting-the-object-properties-during-simulation)
- [공식 5.1: converting-the-example-to-a-standalone-application](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html#converting-the-example-to-a-standalone-application)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
