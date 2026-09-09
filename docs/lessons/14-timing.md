# 14단계. 물리 시간과 렌더링 시간을 구분하기

**목표:** FPS와 물리 주기를 구분하고, 물리 계산이 끝난 시점에 상태를 기록한다. 실행 예제는 [01_drop_cube.py](../../examples/01_drop_cube.py)이다.

## 세 가지 시간을 따로 기록하기

| 값 | 예 | 무엇을 의미하는가 |
|---|---|---|
| 물리 간격 `dt` | `1/120 s` | 힘과 속도로 다음 상태를 계산하는 시간 간격 |
| 렌더링·앱 갱신 | 약 `60회/s` | 화면, UI, 그래프 등의 갱신 빈도 |
| 실제 경과 시간 | 터미널 실행 후 `8초` | 사람이 기다린 시간 |

물리가 120 Hz이고 화면이 60 FPS라면 화면 한 장 사이에 물리가 두 번 진행할 수 있다. 무거운 렌더링 때문에 5초의 시뮬레이션을 계산하는 데 실제로는 20초가 걸릴 수도 있다. 따라서 “600번 `app.update()`를 실행했으니 5초”라는 계산은 성립하지 않는다. [공식 Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html#simulation-timeline)

## 주기를 설정하기

아래는 전체 예제에 들어 있는 설정이다. 이미 물리가 실행 중인 Stage에서 값만 바꾸지 말고 새 실행에서 적용한다.

```python
from isaacsim.core.simulation_manager import PhysxScene

physics = PhysxScene("/World/PhysicsScene")
physics.set_gravity((0.0, 0.0, -9.81))
physics.set_steps_per_second(120)
physics.set_enabled_gpu_dynamics(False)
physics.set_broadphase_type("MBP")
physics.set_solver_type("TGS")
```

이 프로젝트는 소형 강체 한 개를 CPU PhysX로 계산한다. CPU 물리와 GPU 렌더링은 동시에 사용할 수 있다. NVIDIA의 모든 물리 기능이 CPU에서 동작한다는 뜻은 아니다. Newton으로 엔진을 바꾸면 이 PhysX 설정을 그대로 적용하지 말고 해당 엔진의 설정·지원 기능을 다시 확인한다.

## 물리 스텝마다 상태를 기록하기

새 6.0.1 코드에는 `SimulationEvent.PHYSICS_POST_STEP`을 사용한다. API 문서에서 `IsaacEvents.POST_PHYSICS_STEP`은 deprecated로 표시된다. 공식 튜토리얼 일부에 이전 이름이 남아 있어도 새 코드에서는 현재 API를 기준으로 작성한다. [공식 SimulationManager API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.core.simulation_manager/docs/index.html)

```python
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager

samples = []

def record_state(dt, context):
    # cube는 Play 이전에 만들어 둔 RigidPrim이다.
    positions, orientations = cube.get_world_poses()
    samples.append({"dt": float(dt), "position": positions.numpy()[0].tolist()})

callback_id = SimulationManager.register_callback(
    record_state, event=SimulationEvent.PHYSICS_POST_STEP
)
# 시뮬레이션을 실행한 후 자신이 등록한 콜백만 해제한다.
SimulationManager.deregister_callback(callback_id)
```

이 조각은 등록 방법을 보여주는 설명용 코드이다. 전체 예제에서는 등록과 해제 사이에 Timeline을 Play하고 `app.update()`를 반복한다. 이벤트 핸들러 안에서 예외를 던졌을 때 Kit가 콘솔에만 기록할 수 있으므로, 전체 예제는 예외를 목록에 보관하고 바깥 반복문에서 실패 처리한다.

`SimulationManager.step(steps=N)`은 물리 스텝을 직접 제어하는 별도 API이다. 수동 stepping을 사용하는 프로그램은 물리 초기화와 렌더링 동기화도 함께 관리해야 한다. Timeline 자동 진행 중에 이 호출을 섞으면 의도하지 않은 추가 스텝이 생길 수 있다. 첫 프로젝트는 하나의 흐름만 사용한다. 즉 Timeline이 물리를 진행하고, 콜백은 관측만 한다.

## 같은 길이의 실험을 두 번 실행하기

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py \
  --headless --physics-hz 60 --steps 300 --output artifacts/drop_60hz.json
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py \
  --headless --physics-hz 120 --steps 600 --output artifacts/drop_120hz.json
```

300/60과 600/120은 모두 5초이다. 초기 조건은 같고 시간 간격만 다르다. 각 결과의 `simulation_duration_s`, `wall_duration_s`, `app_updates`, `physics_samples`를 비교한다.

```bash
python3 - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("artifacts").glob("drop_*hz.json")):
    data = json.loads(path.read_text())
    print(path.name, data.get("simulation_duration_s"), data.get("wall_duration_s"), data["passed"])
PY
```

여기서는 이미 저장한 JSON만 읽으므로 시스템 `python3`를 사용해도 된다.

**예상 결과:** 두 실행 모두 관측한 물리 시간이 약 5초이고 최종 중심 높이는 약 `0.2 m`이다. 실수 계산 오차가 있으므로 시간 문자열이 정확히 `5.0`일 필요는 없다. 해상도·드라이버·장비 차이까지 비트 단위 동일 결과를 보장하지 않는다.

**진단:** `physics_dt` 검사 실패는 설정 주기가 실제 콜백 간격에 반영되지 않았다는 뜻이다. `app_updates`를 고쳐 결과만 맞추지 말고 물리 Scene, 활성 엔진, 다른 콜백이나 외부 시뮬레이션 제어부터 확인한다.

**완료 기준:** FPS를 물리 주기로 착각하지 않고, 같은 길이의 두 실험 결과를 비교한다.

**과제:** 초기 높이 2 m에서 한 변 0.4 m인 큐브가 처음 바닥에 닿는 시간을 자유낙하 식 `sqrt(2 * (2 - 0.2) / 9.81)`로 계산한다. 수치 결과와 충돌 검출 시점이 정확히 같지 않은 이유를 `dt`와 접촉 허용 거리로 설명한다.

[이전](13-standalone.md) · [다음: 중간 프로젝트 2](15-project-drop-test.md) · [학습 목차](../../README.md)
