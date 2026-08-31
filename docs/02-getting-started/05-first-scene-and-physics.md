# 첫 Stage 만들기: 물리, 저장과 Python 재현

이 장에서는 빈 Stage에서 낙하하는 상자를 만들고 저장하다. 같은 장면을 GUI와 standalone Python으로 각각 만들어 보며, 눈에 보이는 Mesh와 물리 API가 별개라는 점을 익히다.

## 학습 목표

- USD Stage, prim 경로와 Physics Scene을 구분하다.
- Collider, Rigid Body와 Ground Plane의 역할을 확인하다.
- Timeline에서 Play/Stop을 사용하고 authored 초기 상태를 저장하다.
- GUI 장면을 standalone Python으로 재현하고 headless로 검증하다.

## 실습 A: GUI에서 낙하 상자 만들기

### 1단계: 새 Stage와 저장 위치 준비

터미널에서 프로젝트 디렉터리를 먼저 만들다.

```bash
mkdir -p ~/isaacsim-projects/first-scene
```

Isaac Sim에서 `File > New`를 선택하다. 곧바로 `File > Save As`를 실행해 다음 경로로 저장하다.

```text
~/isaacsim-projects/first-scene/falling_cube.usda
```

`.usda`는 사람이 읽을 수 있는 USD ASCII 형식이라 첫 실습에서 구조를 살피기 좋다. 대형 에셋에서는 `.usd`/`.usdc`가 더 작고 빠를 수 있다.

### 2단계: Physics Scene과 바닥 만들기

1. `Create > Physics > Simulation Scene`을 선택하다.
2. Stage에서 생성된 Physics Scene prim을 선택하다.
3. Property에서 중력 방향이 아래쪽이고 `Simulation Steps per Second`가 60인지 확인하다. 항목명은 레이아웃에 따라 접혀 있을 수 있다.
4. `Create > Physics > Ground Plane`을 선택하다.

Physics Scene을 만들지 않아도 기본값 60 steps/s가 적용될 수 있지만, 튜토리얼에서는 중력과 timestep을 명시적으로 저장하기 위해 prim을 만들다.

### 3단계: Cube 만들기

1. `Create > Shape > Cube` 또는 현재 메뉴의 동등한 Cube 생성 항목을 선택하다.
2. Stage에서 Cube를 `FallingCube`로 바꾸다.
3. Property의 Transform에서 `Translate Z = 1.0`으로 설정하다.
4. Scale을 `[0.5, 0.5, 0.5]`로 설정하다. 생성된 Cube의 기본 size에 따라 실제 경계 크기는 달라질 수 있으므로 Viewport에서 확인하다.

아직은 시각 형상만 있을 뿐, 자동으로 동적 물체가 된 것은 아니다.

### 4단계: 물리 API 추가

`FallingCube`를 선택하고 Property의 `+ Add`에서 다음 API를 추가하다.

1. `Physics > Rigid Body`
2. `Physics > Collider`

Rigid Body는 중력과 힘에 의해 자세가 변하게 하다. Collider는 접촉 형상을 물리 엔진에 제공하다. 둘 중 하나만 빠져도 기대한 낙하·충돌이 나오지 않는다.

선택 사항으로 `Physics > Mass`를 추가해 질량을 `1.0 kg`으로 설정하다. 질량을 명시하지 않으면 PhysX가 밀도와 형상으로 계산할 수 있다. 단위와 관성 계산 방식을 확인하지 않고 임의 값을 넣지 않다.

### 5단계: 조명 추가

바닥과 Cube가 너무 어둡다면 `Create > Light > Distant Light`를 추가하고 Intensity를 조절하다. 조명은 물리 결과에 영향을 주지 않지만 카메라·합성 데이터 품질에는 영향을 주다.

## 첫 실행과 관찰

저장한 뒤 툴바에서 Play를 누르다. 다음을 관찰하다.

- `FallingCube`의 Z 위치가 감소하다.
- 바닥에 닿으면 통과하지 않고 정지하거나 약간 튀다.
- Collider 표시를 켜면 시각 Mesh 주위에 충돌 형상이 보이다.

Stop을 누르고 초기 위치로 돌아오는지 확인하다. Pause는 현재 동적 상태를 유지한 채 시간을 멈추고, Stop은 재생 세션을 끝내다.

### 의도적인 실패 실험

원인을 몸으로 익히기 위해 한 번씩 시험하다.

1. **Collider 제거:** Cube가 바닥을 통과하는지 확인하다.
2. **Rigid Body 제거:** Cube가 공중에 고정되는지 확인하다.
3. **Ground Plane 제거:** 동적 Cube가 계속 낙하하는지 확인하다.
4. **중력 0:** Cube가 정지하는지 확인하다.

매 실험 후 Stop하고 원래 설정으로 되돌리다. 실패 결과가 다르면 적용한 API가 부모 Xform이나 다른 prim에 있는지 Stage를 확인하다.

## 시간 설정 이해하기

렌더 프레임률과 물리 스텝률은 서로 다르다.

- Layer 패널에서 Root Layer의 `Timecodes per second`는 Stage의 시간 코드/렌더 갱신 기준과 관련되다.
- Physics Scene의 `Simulation Steps per Second`는 물리 적분 간격을 결정하다.

예를 들어 물리 120 Hz면 `dt = 1/120 s`이다. 빠른 충돌은 작은 dt가 유리하지만 계산량이 늘다. 매우 빠른 물체가 얇은 collider를 건너뛰면 무조건 timestep만 크게 올리지 말고 Physics Scene과 Rigid Body의 CCD(Continuous Collision Detection)도 검토하다.

## 안전하게 저장하기

1. Stop 상태로 돌아오다.
2. Layer 패널에서 의도한 root layer가 Edit Target인지 확인하다.
3. `Ctrl+S`로 저장하다.
4. `File > New` 후 저장한 `falling_cube.usda`를 다시 열다.
5. Play하여 같은 결과가 나오는지 확인하다.

Stage 파일만 복사했는데 reference 에셋이 사라지면 참조 경로가 절대 경로이거나 함께 옮겨야 할 파일을 누락한 것이다. 이 장의 기본 도형은 외부 에셋이 없어 단일 USDA로 재현되어야 하다.

터미널에서도 파일과 prim 이름을 빠르게 확인할 수 있다.

```bash
ls -lh ~/isaacsim-projects/first-scene/falling_cube.usda
grep -nE 'PhysicsScene|GroundPlane|FallingCube' \
  ~/isaacsim-projects/first-scene/falling_cube.usda
```

`.usdc`나 바이너리 인코딩 `.usd`에는 `grep`을 사용하지 않다. USD 도구 또는 Python API로 열다.

## 실습 B: standalone Python으로 같은 개념 재현

다음 코드를 `~/isaacsim-projects/first-scene/first_scene.py`로 저장하다.

```python
from pathlib import Path
import os
import sys

import numpy as np
from isaacsim import SimulationApp


HEADLESS = "--headless" in sys.argv
simulation_app = SimulationApp({"headless": HEADLESS})

# SimulationApp을 만든 뒤에 Isaac Sim 모듈을 import하다.
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
import omni.usd


world = World(
    stage_units_in_meters=1.0,
    physics_dt=1.0 / 60.0,
    rendering_dt=1.0 / 60.0,
)
world.scene.add_default_ground_plane()

cube = world.scene.add(
    DynamicCuboid(
        prim_path="/World/FallingCube",
        name="falling_cube",
        position=np.array([0.0, 0.0, 1.0]),
        scale=np.array([0.5, 0.5, 0.5]),
        color=np.array([0.1, 0.4, 0.9]),
    )
)

# 물리 핸들을 초기화한 뒤 초기 상태를 저장하다.
world.reset()

output_path = Path(
    os.environ.get(
        "ISAAC_TUTORIAL_OUTPUT",
        "~/isaacsim-projects/first-scene/falling_cube_python.usda",
    )
).expanduser()
output_path.parent.mkdir(parents=True, exist_ok=True)

stage = omni.usd.get_context().get_stage()
if not stage.GetRootLayer().Export(str(output_path)):
    raise RuntimeError(f"USD 저장 실패: {output_path}")

for step in range(240):
    if not simulation_app.is_running():
        break
    world.step(render=not HEADLESS)
    if step % 60 == 0:
        position, orientation = cube.get_world_pose()
        print(f"step={step:03d}, z={position[2]:.4f}")

final_position, _ = cube.get_world_pose()
print(f"final_z={final_position[2]:.4f}")
print(f"saved={output_path}")

simulation_app.close()
```

> `SimulationApp`은 Kit 런타임과 확장을 초기화하다. 따라서 `isaacsim.core...`처럼 Kit에 의존하는 모듈은 `SimulationApp` 생성 뒤 import하는 패턴을 따르다.

GUI로 실행하다.

```bash
cd ~/isaacsim
./python.sh ~/isaacsim-projects/first-scene/first_scene.py
```

창 없이 실행하다.

```bash
cd ~/isaacsim
./python.sh ~/isaacsim-projects/first-scene/first_scene.py --headless
```

출력 위치를 바꿀 때는 환경 변수를 사용하다.

```bash
ISAAC_TUTORIAL_OUTPUT=/tmp/falling_cube.usda \
  ./python.sh ~/isaacsim-projects/first-scene/first_scene.py --headless
```

성공하면 약 1초 간격으로 Z 좌표가 출력되고, 마지막에는 저장 경로가 나오다. 바닥과 Cube의 실제 접촉 높이는 기본 Ground Plane과 Cube size/scale 정의에 따라 결정되므로 `final_z`를 특정 숫자로 하드코딩해 합격 판정하지 않다. 대신 다음 조건을 확인하다.

- 초기 Z보다 최종 Z가 낮다.
- 최종 값이 유한수이다.
- 240 step 안에 계속 큰 음수로 발산하지 않다.
- 저장된 USD를 GUI에서 다시 열 수 있다.

```bash
test -s ~/isaacsim-projects/first-scene/falling_cube_python.usda \
  && echo "USD export: OK"
```

## GUI와 Python 결과가 다를 때

| 증상 | 확인할 것 |
|---|---|
| Cube가 움직이지 않음 | Timeline/`world.step`, Rigid Body 적용 prim, 중력 |
| 바닥을 통과함 | Collider, Ground Plane, scale, physics dt |
| GUI에는 보이지만 headless 실패 | 렌더 의존 코드, 에셋 경로, 실행 로그 |
| 저장 파일에 동적 최종 위치가 없음 | 코드는 초기 authored 상태를 Export했다. 런타임 물리 상태와 USD 저작 상태를 구분하다 |
| 재실행할 때 prim 중복 | 새 Stage/새 World를 만들었는지, 같은 경로를 중복 정의했는지 확인하다 |

## 확장 실습

1. 마찰이 다른 Physics Material 두 개를 만들고 경사면에서 비교하다.
2. Cube를 세 개로 복제하고 질량·restitution을 바꾸다.
3. Physics Scene을 60 Hz와 120 Hz로 실행해 4초 동안의 step 수와 결과를 기록하다.
4. Contact Sensor를 Cube에 붙이고 Console 또는 Python에서 접촉 시점을 기록하다.
5. root layer에는 환경, sublayer에는 실험 파라미터만 저장해 보다.

## 완료 체크포인트

- [ ] GUI에서 Collider와 Rigid Body의 차이를 실패 실험으로 확인했다.
- [ ] Stop 상태의 초기 장면을 USDA로 저장하고 다시 열었다.
- [ ] standalone Python을 GUI와 headless 두 모드로 실행했다.
- [ ] USD authored 상태와 런타임 PhysX 상태가 다를 수 있음을 이해했다.
- [ ] prim 경로 `/World/FallingCube`를 Stage와 코드에서 찾았다.

## 출처

- [Isaac Sim 5.1.0 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Isaac Sim 5.1.0 — Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Isaac Sim 5.1.0 — Core API Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
- [Isaac Sim 5.1.0 — Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [Isaac Sim 5.1.0 — Scene Setup Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html)
