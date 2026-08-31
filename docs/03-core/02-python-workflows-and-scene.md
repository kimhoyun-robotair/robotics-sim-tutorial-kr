# Python 워크플로와 Scene API

같은 Isaac Sim Python API라도 **누가 애플리케이션을 시작했는가**에 따라 초기화와 반복문이 달라진다. 이 구분을 놓치면 import 오류, 멈춘 GUI, 초기화되지 않은 articulation 같은 문제가 생긴다.

## 1. Application, Simulation, World, Scene, Stage

서로 비슷하게 들리는 객체를 먼저 구분한다.

| 개념 | 소유하는 것 | 주 용도 |
|---|---|---|
| Application/Kit | 창, renderer, extension, 이벤트 루프 | Isaac Sim 프로세스 전체를 실행한다. |
| Simulation context | physics timestep, play/pause, backend | 시간과 PhysX 계산을 관리한다. |
| `World` | simulation context, `Scene`, task, callback, logger | 로봇 실습의 상위 orchestration wrapper이다. |
| `Scene` | 이름으로 찾는 Core API 객체 registry | 객체 추가, 조회, reset 시 기본 상태 복원을 돕는다. |
| USD `Stage` | prim과 layer를 합성한 장면 | 실제 장면 데이터의 출처이다. |

모든 Stage prim이 자동으로 `Scene` registry에 들어가는 것은 아니다. `world.scene.add(obj)`로 등록한 wrapper만 `world.scene.get_object(name)`로 찾는다. 반대로 Stage에서 prim이 삭제되었는데 Python wrapper만 들고 있으면 wrapper가 더 이상 유효하지 않을 수 있다.

## 2. 세 가지 Python 실행 방식

| 항목 | Standalone Python | Script Editor | Kit Extension |
|---|---|---|---|
| 앱 시작 주체 | 현재 스크립트 | 이미 실행 중인 Isaac Sim | 이미 실행 중인 Isaac Sim |
| `SimulationApp` 생성 | **반드시 생성한다.** | **절대 생성하지 않는다.** | **절대 생성하지 않는다.** |
| 반복문 | 스크립트가 `world.step()` 호출 | Kit 이벤트 루프에 양보 | update/physics callback 또는 async task |
| 긴 작업 | 동기 반복문 가능 | 동기 반복문 금지 | callback을 짧게 유지 |
| 재실행 | 프로세스를 새로 시작 | 같은 Stage와 singleton이 남을 수 있음 | hot reload와 `on_shutdown` 정리가 중요 |
| 적합한 일 | batch, 테스트, headless, 데이터 생성 | API 탐색, 짧은 실험 | 재사용 UI·도구·지속 실행 기능 |

### 가장 중요한 초기화 규칙

Standalone에서는 Omniverse 플러그인이 로드되기 전에 `omni`, `pxr`, 대부분의 `isaacsim.*` 런타임 모듈을 import하면 안 된다. 다음 순서를 지킨다.

```python
# 1. 표준 라이브러리와 SimulationApp만 먼저 import한다.
from isaacsim import SimulationApp

# 2. Kit을 실제로 시작한다.
simulation_app = SimulationApp({"headless": False})

# 3. 그 다음에야 omni, pxr, Core API와 센서 모듈을 import한다.
import omni.usd
from pxr import UsdGeom
from isaacsim.core.api import World

# 4. 장면을 만들고 명시적으로 step한다.
# ...

# 5. 항상 종료한다.
simulation_app.close()
```

`from isaacsim.simulation_app import SimulationApp`도 5.1에서 사용할 수 있다. 공식 예제에는 `from isaacsim import SimulationApp` 표기도 함께 나온다. 중요한 것은 import 철자가 아니라 **인스턴스를 만든 뒤 런타임 모듈을 late import하는 순서**이다.

## 3. Standalone 완전 예제

다음을 `standalone_falling_cube.py`로 저장하고 Isaac Sim 설치 루트에서 실행한다.

```python
from isaacsim import SimulationApp

# GUI를 보려면 False, 서버에서 렌더 창 없이 실행하려면 True로 한다.
simulation_app = SimulationApp(
    {"headless": False, "renderer": "RayTracedLighting"}
)

# 반드시 SimulationApp 생성 뒤에 불러온다.
import numpy as np

from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid

try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=1.0 / 60.0,
        rendering_dt=1.0 / 60.0,
    )
    world.scene.add_default_ground_plane()
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Cube",
            name="falling_cube",
            position=np.array([0.0, 0.0, 1.0]),
            scale=np.array([0.25, 0.25, 0.25]),
            color=np.array([0.9, 0.2, 0.1]),
            mass=1.0,
        )
    )

    # Scene wrapper와 physics handle은 reset 뒤에 사용할 준비가 된다.
    world.reset()

    for step in range(240):
        world.step(render=True)
        if step % 60 == 0:
            position, orientation = cube.get_world_pose()
            print(f"step={step:03d}, z={position[2]:.4f}")

    position, _ = cube.get_world_pose()
    assert 0.10 < position[2] < 0.20, position
    print("PASS: cube settled on the ground")
finally:
    simulation_app.close()
```

```bash
cd ~/isaacsim
./python.sh /절대/경로/standalone_falling_cube.py
```

큐브 scale이 한 변 0.25 m이므로 중심 Z가 약 0.125 m 부근에서 멈추면 정상이다. contact offset과 solver 상태에 따라 마지막 소수점은 달라질 수 있으므로 지나치게 엄격한 비교를 하지 않는다.

### 재현 가능한 step

- batch 실험은 고정된 `physics_dt`와 명시적인 step 수를 사용한다.
- 제어기는 callback에 전달된 `step_size` 또는 설정한 physics dt를 사용한다.
- 가능한 한 wall-clock `sleep()`으로 물리 시간을 만들지 않는다. `sleep(1)`은 컴퓨터를 쉬게 할 뿐 “정확히 1초의 시뮬레이션”을 보장하지 않는다.
- renderer가 필요 없는 물리 batch에서는 `world.step(render=False)`를 사용하되 센서가 렌더를 요구하는지 확인한다.

## 4. Script Editor 비동기 예제

`Window > Script Editor`에서 다음 코드를 실행한다. 실행 중인 Kit의 메인 스레드를 `while` 루프로 점유하지 않고 매 프레임 이벤트 루프에 제어권을 돌려준다.

```python
import asyncio
import numpy as np

from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.utils.stage import create_new_stage_async
import omni.kit.app


async def build_and_run():
    # Script Editor를 여러 번 실행할 때 이전 singleton과 Stage를 정리한다.
    if World.instance() is not None:
        World.instance().clear_instance()
    await create_new_stage_async()

    world = World(stage_units_in_meters=1.0)
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane()
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Cube",
            name="cube",
            position=np.array([0.0, 0.0, 1.0]),
            size=0.25,
            color=np.array([0.2, 0.6, 1.0]),
        )
    )

    await world.reset_async()
    await world.play_async()

    # Kit이 GUI와 physics를 갱신하도록 매번 양보한다.
    app = omni.kit.app.get_app()
    for _ in range(180):
        await app.next_update_async()

    await world.pause_async()
    position, _ = cube.get_world_pose()
    print("final position:", position)


asyncio.ensure_future(build_and_run())
```

### 잘못된 Script Editor 패턴

```python
# 잘못된 예: GUI 이벤트 루프를 막는다.
while True:
    world.step(render=True)
```

이 코드는 UI가 멈추고 Stop 버튼도 누를 수 없게 만들 수 있다. Script Editor에서는 async API, physics callback 또는 update subscription을 사용한다.

## 5. Extension 수명 주기

반복해서 쓸 도구는 Extension으로 만든다. 최소 구조는 다음과 같다.

```text
my.core.demo/
  config/extension.toml
  my/core/demo/__init__.py
  my/core/demo/extension.py
```

`config/extension.toml`의 핵심은 Python module 등록이다.

```toml
[core]
reloadable = true

[package]
title = "Core Demo"
version = "0.1.0"

[[python.module]]
name = "my.core.demo"
```

`extension.py`에서는 시작 시 장면 작업을 예약하고 종료 시 callback과 task를 해제한다.

```python
import asyncio
import omni.ext


class CoreDemoExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._task = asyncio.ensure_future(self._setup_async())
        self._physics_callback_name = "my.core.demo.control"

    async def _setup_async(self):
        from isaacsim.core.api import World
        from isaacsim.core.utils.prims import is_prim_path_valid

        world = World.instance() or World()
        await world.initialize_simulation_context_async()
        # 기존 Stage를 존중할지 새 Stage를 만들지는 도구의 계약으로 정한다.
        if not is_prim_path_valid("/World/defaultGroundPlane"):
            world.scene.add_default_ground_plane()
        await world.reset_async()
        world.add_physics_callback(
            self._physics_callback_name, self._on_physics_step
        )

    def _on_physics_step(self, step_size):
        # 짧고 결정적인 제어 계산만 수행한다.
        pass

    def on_shutdown(self):
        from isaacsim.core.api import World

        world = World.instance()
        if world is not None:
            try:
                world.remove_physics_callback(self._physics_callback_name)
            except Exception:
                pass
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None
```

Extension에서는 앱이 이미 시작되어 있으므로 `SimulationApp`을 생성하지 않는다. hot reload 때 이전 callback, event subscription, UI window와 async task를 해제하지 않으면 같은 제어가 두 번 실행되거나 이미 삭제된 prim을 참조한다.

## 6. Stage와 자산을 코드로 다루기

### 현재 Stage와 prim 검사

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/Cube")
if not prim.IsValid():
    raise RuntimeError("/World/Cube prim이 없다")

print("type:", prim.GetTypeName())
print("path:", prim.GetPath())
print("applied schemas:", prim.GetAppliedSchemas())
```

### USD reference로 자산 넣기

```python
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path

assets_root = get_assets_root_path()
if assets_root is None:
    raise RuntimeError("Isaac Sim asset root를 찾지 못했다")

robot_usd = assets_root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
add_reference_to_stage(robot_usd, "/World/Robots/Franka")
```

자산 root의 구체적인 위치를 문자열로 하드코딩하지 않고 resolver를 사용한다. 네트워크 자산 서버가 없거나 경로가 바뀔 수 있으므로 `None`과 파일 존재 여부를 검사한다.

### 조명 만들기

```python
import omni.usd
from pxr import Gf, UsdLux

stage = omni.usd.get_context().get_stage()
light = UsdLux.DistantLight.Define(stage, "/World/Lights/Key")
light.CreateIntensityAttr(800.0)
light.CreateAngleAttr(1.0)
light.CreateColorAttr(Gf.Vec3f(1.0, 0.95, 0.9))
```

## 7. Scene registry와 여러 객체

`name`과 `prim_path`는 다르다. `name`은 Python `Scene`에서 찾는 고유 key이고, `prim_path`는 USD Stage 주소이다.

```python
for i in range(3):
    world.scene.add(
        DynamicCuboid(
            prim_path=f"/World/Props/Cube_{i}",
            name=f"cube_{i}",
            position=np.array([0.0, i * 0.4, 0.5 + i * 0.3]),
            size=0.2,
        )
    )

world.reset()
cube_1 = world.scene.get_object("cube_1")
print(cube_1.get_world_pose()[0])
```

여러 로봇이나 여러 task를 다룰 때도 prim path와 name을 충돌 없이 설계한다. `/World/envs/env_0/robot`, `/World/envs/env_1/robot`처럼 환경 namespace를 두면 vectorized view의 expression도 단순해진다.

## 8. Physics callback과 관측 기록

제어 명령은 매 physics step 직전에 계산하는 편이 안정적이다.

```python
samples = []

def observe(step_size):
    position, orientation = cube.get_world_pose()
    linear_velocity = cube.get_linear_velocity()
    samples.append(
        {
            "dt": float(step_size),
            "z": float(position[2]),
            "vz": float(linear_velocity[2]),
        }
    )

world.add_physics_callback("record_cube", callback_fn=observe)
```

이름이 같은 callback을 다시 등록하지 않는다. 실험이 끝나면 `world.remove_physics_callback("record_cube")`로 정리한다. 무거운 파일 쓰기와 네트워크 통신은 callback 밖의 queue consumer로 넘긴다.

## 9. Core Experimental API를 언제 검토하는가

5.1 문서는 5.0부터 Core Experimental API를 도입했으며 앞으로 기존 Core API를 대체할 방향이라고 안내한다. 다만 이름 그대로 5.1 시점에는 실험 API이다.

- 공식 5.1 Core 튜토리얼을 그대로 따라가거나 기존 예제와 호환해야 하면 이 장의 기존 Core API를 사용한다.
- 장기 유지할 새 코드라면 동일 기능의 Experimental API 문서와 migration 상태를 확인하고 작은 proof-of-concept로 평가한다.
- 한 모듈 안에서 기존 wrapper와 experimental wrapper를 무계획하게 섞지 않는다. 초기화, backend와 데이터 shape 계약이 다를 수 있다.

## 10. 검증 체크포인트

- [ ] Standalone 예제를 `./python.sh`로 실행하고 `PASS`를 확인했다.
- [ ] `SimulationApp` 생성 전에는 `omni`, `pxr`, Core API를 import하지 않았다.
- [ ] Script Editor 예제가 UI를 멈추지 않고 실행된다.
- [ ] Extension 종료 시 callback과 async task를 해제하는 이유를 설명할 수 있다.
- [ ] `name`과 `prim_path`의 차이를 설명할 수 있다.
- [ ] Stage prim과 Scene registry 객체가 일대일로 자동 연결되는 것이 아님을 이해했다.

## 출처

- [Python Scripting Concepts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html)
- [SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- [Scene Setup Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html)
- [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
- [Adding Multiple Robots](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html)
- [Multiple Tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html)
- [Adding Props](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html)
- [Data Logging](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html)
- [Omniverse Script Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html)
