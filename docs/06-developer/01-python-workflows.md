# Python 실행 방식과 Core API

Isaac Sim의 Python은 같은 언어라도 실행 주체가 다르다. 작은 자동화는 Script Editor, 반복 가능한 프로그램은 standalone, 제품 기능은 Extension으로 만든다.

## 세 워크플로를 고르다

| 방식 | lifecycle 소유자 | 장점 | 주의점 |
| --- | --- | --- | --- |
| Script Editor | 이미 실행 중인 Isaac Sim | stage를 보며 빠르게 실험하다. | 동기 코드로 UI thread를 오래 막지 않다. |
| standalone | 스크립트가 `SimulationApp`을 생성하다. | headless, batch, CI에 적합하다. | `SimulationApp`을 다른 Isaac/Omniverse import보다 먼저 만들다. |
| Extension | Kit가 `on_startup`/`on_shutdown`을 호출하다. | UI, 메뉴, service를 재사용·배포하다. | subscription과 callback을 종료 때 해제하다. |

Jupyter는 실행 중 application scope에 붙는 대화형 방식과 `jupyter_notebook.sh`로 kernel을 여는 방식을 구분하다. notebook의 중첩 event loop는 Isaac Sim이 처리하지만, cell 순서를 바꾸어 lifecycle을 깨지 않게 하다.

## 최소 standalone 프로그램

다음 파일을 `examples/standalone/hello_stage.py`로 저장하고 Isaac Sim의 Python wrapper로 실행하다.

```python
from isaacsim import SimulationApp

# 반드시 대부분의 isaacsim/omni/pxr import보다 먼저 실행하다.
simulation_app = SimulationApp(
    {
        "headless": True,
        "width": 640,
        "height": 480,
        "disable_viewport_updates": True,
    }
)

from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
import numpy as np

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()
cube = world.scene.add(
    DynamicCuboid(
        prim_path="/World/Cube",
        name="falling_cube",
        position=np.array([0.0, 0.0, 1.0]),
        size=0.2,
        color=np.array([0.2, 0.7, 1.0]),
    )
)

world.reset()
for _ in range(240):
    world.step(render=False)

position, _ = cube.get_world_pose()
print(f"final_z={position[2]:.4f}")
simulation_app.close()
```

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py
```

`final_z`가 지면 위 cube 중심 높이에 가까우면 physics step이 실행된 것이다. `close()`를 `finally`에서 보장하면 예외가 난 batch도 resource를 정리하기 쉽다.

```python
from isaacsim import SimulationApp

app = SimulationApp({"headless": True})
try:
    # app 생성 이후에 Isaac Sim 모듈을 import하고 작업하다.
    ...
finally:
    app.close()
```

## stage와 simulation lifecycle을 분리하다

`World`는 scene object, physics context, task, callback을 묶은 고수준 API이다. `pxr.Usd`는 USD opinion을 직접 편집하는 저수준 API이다. stage에 prim이 존재한다고 physics handle이 즉시 준비된 것은 아니다. asset을 추가하거나 articulation 구성을 바꾼 뒤에는 `world.reset()` 또는 비동기 환경의 `reset_async()`로 handle을 초기화하다.

```python
world.reset()
for _ in range(10):
    world.step(render=False)
```

GUI Extension에서는 UI thread를 막는 긴 loop 대신 async 또는 physics callback을 사용하다.

```python
def on_physics_step(step_size: float) -> None:
    # 짧고 결정적인 작업만 수행하다.
    controller_step(step_size)

world.add_physics_callback("course_controller", on_physics_step)
# 종료할 때 world.remove_physics_callback("course_controller")를 호출하다.
```

## 설정을 명령줄에서 덮어쓰다

Kit setting은 `--/경로=값` 형식으로 전달하다.

```bash
"$ISAACSIM_PATH/python.sh" my_script.py \
  --/log/level=info \
  --/app/window/width=1280
```

설정 이름과 기본값은 버전마다 달라질 수 있다. UI에서 값을 바꾸기 전에 현재 값을 기록하고, 5.1.0 API 문서 또는 `carb.settings`로 확인하다.

## 출처

- [Python Scripting Concepts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html)
- [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
