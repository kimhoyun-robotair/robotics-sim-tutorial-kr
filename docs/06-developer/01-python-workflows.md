# GUI, Script Editor, Extension, standalone Python의 차이

이 장에서는 같은 낙하 실험을 네 가지 방식으로 만들고, **누가 앱과 시뮬레이션의 실행 순서를 관리하는지** 비교한다. 실행 기준은 Ubuntu 24.04 LTS, Isaac Sim 5.1.0이다.

## 1. 왜 실행 방식을 나누는가

GUI, Extension, Python은 서로 다른 시뮬레이터가 아니다. GUI는 화면에서 작업하는 방식이고, Extension은 Isaac Sim을 구성하는 기능 단위이며, Python은 기능을 구현하거나 호출하는 언어이다. Stage 창, 속성 편집기, 센서 도구도 여러 Extension으로 구성되어 있다.

예를 들어 GUI에서 로봇을 배치하고 USD로 저장한 뒤, Python으로 그 USD를 불러와 센서 위치를 20번 바꿔 실험할 수 있다. 반복해서 쓰는 설정 창은 Extension으로 묶고, 밤새 실행할 실험은 standalone 프로그램으로 옮길 수 있다. NVIDIA도 세 방식을 조합하는 과정을 설명한다. [공식 Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)

| 비교 항목 | GUI | Script Editor | Extension | standalone Python |
| --- | --- | --- | --- | --- |
| 시작 방법 | `isaac-sim.sh` 실행 | 실행 중인 앱에서 편집기 열기 | Extension Manager에서 활성화 | `python.sh 프로그램.py` 실행 |
| 앱 생성 주체 | Isaac Sim 실행 파일 | 이미 실행 중인 앱 | 이미 실행 중인 Kit 앱 | 코드의 `SimulationApp` |
| 장면 편집 | 메뉴, 마우스, 속성 패널 | Python 명령 | 버튼, 메뉴, Python/C++ 기능 | Python 명령 |
| 물리 실행 | 사용자가 Play/Stop 조작 | 앱의 Play 상태에 따름 | 앱의 Play 상태와 콜백에 따름 | 코드에서 `world.step()` 호출 |
| 반복 실행 | 사람이 같은 조작 반복 | 짧은 코드 또는 비동기 작업 | 이벤트와 콜백 | 횟수가 정해진 루프 |
| 관리할 파일 | USD | USD + `.py` | USD + 소스/설정 | USD + 프로그램 + 실험 설정 |
| 알맞은 작업 | 배치, 관절 축, 시야 확인 | 속성 조사, 짧은 자동화 | 재사용할 도구와 조작 화면 | 일괄 검증, 데이터 생성, 학습 |

Script Editor를 별도 열로 나눈 이유는 초보자가 가장 먼저 Python을 실행하는 곳이기 때문이다. 공식 분류에서는 이미 실행 중인 앱 안에서 Python을 사용하는 Extension 방식에 가깝다.

## 2. 모든 방식에서 맞출 실험 조건

Prim 이름이나 바닥을 만드는 API가 달라도 다음 물리 조건을 맞춘다.

| 항목 | 값 | 확인할 의미 |
| --- | --- | --- |
| 길이 단위 / 위쪽 축 | m / Z | `z=1`은 지면 위 1 m |
| 바닥 윗면 | `z=0` | 정착 높이의 기준 |
| 큐브 한 변 | 0.2 m | 중심이 약 `z=0.1`에 정착 |
| 큐브 중심의 시작 위치 | `[0,0,1]` m | 바닥과 겹치지 않는 위치 |
| 질량 / 중력 | 1 kg / 9.81 m/s², -Z | 기본적인 강체 낙하 조건 |
| 물리 주기 | 60 Hz | 240 step은 시뮬레이션 시간 4초 |
| 조명 | 명시적으로 추가 | 화면의 임시 조명과 구분 |

접촉 여유 거리와 수치 계산 때문에 최종 높이가 정확히 `0.100000`일 필요는 없다. 반면 물체가 지면을 통과하거나, 계속 가속하거나, 위치가 NaN이 되면 정상으로 보지 않는다.

## 3. GUI로 만들기

1. 기존 작업을 저장하고 **File > New**로 새 장면을 만든다. 타임라인이 Stop 상태인지 확인한다.
2. **Create > Physics > Ground Plane**으로 바닥을 만든다. Translate Z가 0인지 확인한다.
3. **Create > Lights > Dome Light**로 조명을 만들고 Intensity를 700으로 지정한다.
4. **Create > Shape > Cube**로 큐브를 만든다. Stage에서 해당 Cube를 선택한다.
5. Property에서 큐브 한 변을 0.2 m로 맞추고 Translate를 `[0,0,1]`로 설정한다. `Cube` 타입에 Size 항목이 있으면 Size를 0.2, Scale을 `[1,1,1]`로 지정한다. `Mesh` 타입으로 만들어졌다면 Size 항목이 없으므로 기본 한 변이 1 m인지 확인하고 Scale을 `[0.2,0.2,0.2]`로 지정한다. Size와 Scale을 동시에 줄이지 않는다.
6. 큐브의 **Add > Physics > Rigid Body with Colliders Preset**을 적용한다. 강체 속성과 충돌 형상이 모두 필요하다.
7. **Add > Physics > Mass**에서 Mass를 1로 설정한다. 큐브의 상위 Xform까지 또 강체로 만들지 않는다.
8. **Create > Physics > Simulation Scene**을 추가한다. 이미 Physics Scene이 있으면 기존 것을 사용한다. 중력 방향과 크기, Simulation Steps per Second를 표의 값과 맞춘다.
9. Cube를 선택하고 Viewport에 마우스를 올려 `F`를 눌러 화면을 맞춘다. Play를 누르면 큐브가 바닥으로 떨어져 멈춰야 한다.
10. 정착한 모습을 확인한 다음 Stop으로 초기 상태로 돌아온다. `workflow_gui.usd`로 저장한다.

이 순서는 공식 Basic Usage와 Physics Fundamentals의 장면 작성 절차를 이 과정의 수치로 구성한 것이다. [Basic Usage](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html), [Physics Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)

## 4. Script Editor로 같은 장면 만들기

1. GUI 실습을 저장하고 **File > New**를 선택한다.
2. **Window > Script Editor**를 연다.
3. [falling_cube.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/script_editor/falling_cube.py)의 전체 내용을 붙여 넣고 실행한다. 일반 터미널의 `python3`로 실행하는 파일이 아니다.
4. Stage의 `/World/WorkflowDemo/Cube`를 선택하고 `F`, Play 순서로 조작한다.
5. 이미 장면이 있다는 오류가 뜨면 코드를 반복 실행하지 말고 Stop, File > New 순서로 다시 시작한다.

파일에서 다음 부분을 먼저 읽는다.

```python
stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, "/World/WorkflowDemo/Cube")
cube.CreateSizeAttr(0.2)
cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 1.0))
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1.0)
```

`get_stage()`는 현재 열려 있는 문서를 가져온다. `Define()`은 그 문서에 Prim을 만들고, `Apply()`는 충돌·강체·질량 같은 속성 묶음을 부착한다. `SimulationApp()`은 없다. 앱은 이미 실행 중이며 Script Editor는 그 앱의 Python 환경을 사용하기 때문이다.

제공 파일은 빈 익명 Stage인지 검사한 후에만 단위와 위쪽 축을 설정한다. 저장된 로봇 장면의 단위를 임의로 바꾸거나 `World.clear_instance()`로 다른 실습의 상태를 지우지 않는다.

### 속성 조사도 Python으로 할 수 있다

Stop 상태에서 다음 전체 코드를 별도로 실행한다.

```python
import omni.usd
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/WorkflowDemo/Cube")
assert prim.IsValid(), "먼저 falling_cube.py를 실행한다."
print("type:", prim.GetTypeName())
print("size:", UsdGeom.Cube(prim).GetSizeAttr().Get())
print("mass:", UsdPhysics.MassAPI(prim).GetMassAttr().Get())
print("rigid body:", prim.HasAPI(UsdPhysics.RigidBodyAPI))
print("collider:", prim.HasAPI(UsdPhysics.CollisionAPI))
```

이는 **USD에 작성한 속성**을 읽는다. 실행 중인 물리 상태가 항상 같은 속성에 기록된다고 가정해서는 안 된다. Fabric이나 물리 설정에 따라 런타임 상태는 Core API의 물리 핸들로 읽어야 한다.

## 5. GUI에서 긴 루프를 실행하면 왜 멈추는가

Python이 UI 스레드를 계속 차지하면 창 갱신, Stop 버튼, 렌더링, 일부 초기화가 진행되지 못한다. GUI에서 `while True`로 제어 코드를 계속 호출하거나 `time.sleep()`으로 기다리는 패턴은 피한다. 짧은 작업을 나누고 앱에 제어권을 돌려주어야 한다.

다음은 장면을 바꾸지 않고 앱 업데이트 10회를 기다리는 완전한 예제이다.

```python
import asyncio
import omni.kit.app

async def observe_updates():
    for index in range(10):
        await omni.kit.app.get_app().next_update_async()
        print("app update:", index + 1)

old_task = globals().get("course_observer_task")
if old_task is not None and not old_task.done():
    old_task.cancel()
course_observer_task = asyncio.ensure_future(observe_updates())
```

`await next_update_async()`는 **앱 업데이트**를 기다린다. 물리 1 step 또는 센서 프레임 1장을 보장하지 않는다. 정지 상태에서도 앱은 화면을 그릴 수 있고, 앱 업데이트 한 번 사이에 물리가 여러 step 진행될 수도 있다. 물리 주기마다 제어할 코드는 physics callback에 연결한다.

`World`를 사용하는 비동기 예제에서는 `await world.reset_async()`로 초기화를 기다린 뒤 로봇 핸들을 사용한다. 초기화 전에 관절 위치를 읽거나 명령을 보내면 화면에 로봇이 보이더라도 핸들이 준비되지 않았을 수 있다. [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)

## 6. Extension으로 재사용하기

코드를 매번 붙여 넣기 번거롭거나 다른 사람이 버튼으로 실습을 시작해야 한다면 Extension으로 묶는다. [다음 장](02-extension-and-omnigraph.md)에서 설치 가능한 [course.falling_cube](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/extensions/course.falling_cube/config/extension.toml)를 실행한다.

| 파일 | 책임 |
| --- | --- |
| `config/extension.toml` | 이름, 버전, 의존성, Python 모듈 지정 |
| `course/falling_cube/__init__.py` | Kit가 클래스를 찾도록 모듈에서 내보내기 |
| `scene.py` | USD 장면 생성과 빈 장면 검사 |
| `extension.py` | UI, 비동기 작업, 물리/Stage 이벤트 구독, 종료 처리 |

버튼을 누르는 시점에 장면 생성 함수를 호출한다. Extension을 켰다는 이유만으로 사용자의 장면을 교체하지 않는다. 창을 만들고 장면 생성은 사용자의 조작으로 시작하는 구조를 익히는 것이 핵심이다.

## 7. standalone으로 자동 실행하기

저장소 루트에서 다음 명령을 실행한다.

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py
```

같은 검사를 창에서 관찰하려면 명령 끝에 `--gui`를 추가한다. 완료 후 프로그램은 자동으로 종료한다.

전체 프로그램은 [hello_stage.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/hello_stage.py)에 있다. 다음은 실행 순서를 이해하기 위한 독립적인 물리 전용 예제이다.

```python
from isaacsim import SimulationApp

app = SimulationApp({"headless": True})
try:
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid
    import numpy as np

    world = World(stage_units_in_meters=1.0, physics_dt=1.0 / 60.0)
    world.scene.add_default_ground_plane()
    cube = world.scene.add(DynamicCuboid(
        prim_path="/World/Cube", name="cube",
        position=np.array([0.0, 0.0, 1.0]), size=0.2, mass=1.0,
    ))
    world.reset()
    for _ in range(240):
        world.step(render=False)
    position, _ = cube.get_world_pose()
    print("center z:", float(position[2]))
finally:
    app.close()
```

이 코드는 렌더링하지 않으므로 센서 영상을 검증하지 않는다. `headless=True`는 창을 열지 않는다는 뜻이고, `render=False`는 이 step에서 렌더링하지 않는다는 뜻이다. 카메라와 RTX LiDAR는 창이 없는 실행에서도 렌더링이 필요하다.

`SimulationApp`을 생성한 뒤 Isaac Sim 모듈을 import한다. 시스템 Python에 `pxr`만 설치한다고 Isaac Sim의 Extension과 런타임까지 초기화되는 것은 아니다. 설치본의 `python.sh`를 사용하는 이유도 여기에 있다. [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html), [SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)

## 8. 무엇을 USD에 저장할 수 있는가

큐브 위치, 충돌 속성, 카메라, 재질, OmniGraph처럼 Stage에 작성한 내용은 USD에 저장할 수 있다. Python 지역 변수, 실행 중인 콜백, 비동기 task, UI 창까지 자동으로 USD에 저장되지는 않는다. 다른 컴퓨터에서 재현하려면 **USD 파일 + 필요한 Extension + Python 프로그램 + 실행 설정**을 함께 관리한다.

실습을 마치면 다음을 설명할 수 있어야 한다.

- 같은 낙하 장면을 GUI와 Python 양쪽에서 만들 수 있다.
- Script Editor에서 `SimulationApp`을 새로 만들지 않는 이유를 안다.
- 앱 업데이트, 물리 step, 센서 프레임을 구분한다.
- Extension 종료 때 콜백과 비동기 작업을 정리할 수 있다.
- 240 physics step과 240번 화면 갱신을 같은 것으로 취급하지 않는다.

이 저장소의 정적 검사는 Python 문법과 파일 구성을 검사한다. 실제 GUI 표시, PhysX 동작, 그래픽 드라이버별 렌더링 결과는 Isaac Sim 5.1.0과 RTX GPU가 있는 환경에서 위 절차로 확인해야 한다.

## 출처

- [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)
- [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
