# 12단계. Script Editor에서 장면을 만들다

**목표:** 현재 Stage를 Python으로 읽고, 비동기 작업을 예약해 UI를 멈추지 않고 큐브와 조명을 생성한다. 실행 파일은 [02_script_editor_scene.py](../../examples/02_script_editor_scene.py)이다.

## 어디에서 실행하는지 먼저 확인하기

1. Isaac Sim GUI를 실행한다.
2. 앞 단계의 결과를 저장한 뒤 `File > New`로 새 Stage를 만든다.
3. Timeline에서 Stop을 누른다. Pause는 시뮬레이션 도중 잠시 멈춘 상태이므로 이 실습의 편집 시작점으로 사용하지 않는다.
4. `Window > Script Editor`를 연다. 메뉴가 보이지 않으면 Extension Manager에서 Script Editor 관련 확장이 활성화되어 있는지 확인한다.
5. 빈 탭에 아래 코드를 입력하고 Run을 누른다.

```python
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
print("현재 Stage:", stage.GetRootLayer().identifier)
print("위쪽 축:", UsdGeom.GetStageUpAxis(stage))
print("1단위의 길이(m):", UsdGeom.GetStageMetersPerUnit(stage))
```

이 과정은 Isaac Sim에 내장된 Python을 사용한다. 시스템 터미널의 `python3`나 ROS 2 노드가 실행되는 Python과 같은 환경이라고 가정하지 않는다. [공식 6.0.1 Script Editor](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/development_tools/omniverse_script_editor.html)

## 새 Stage의 단위를 맞추다

앞 단계에서 만든 빈 Stage에 한해 아래를 실행한다. 물체가 이미 배치된 Stage의 단위를 바꾸면 좌표 숫자의 의미가 바뀌므로 새 Stage인지 먼저 확인한다.

```python
from pxr import UsdGeom
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
```

이제 Script Editor의 열기 버튼으로 `examples/02_script_editor_scene.py`를 열고 Run을 누른다. 파일 열기가 어려우면 파일 전체 내용을 새 탭에 붙여 넣고 실행한다. 이 파일은 standalone 프로그램이 아니므로 `python.sh`로 직접 실행하지 않는다.

예제의 핵심은 아래와 같다. 아래 조각만 실행하는 대신 전체 파일을 실행하면 Stage 검사와 중복 실행 처리가 함께 적용된다.

```python
async def build_scene():
    context = omni.usd.get_context()
    stage = context.get_stage()
    # 앞에서 Stage, Timeline, 단위, 소유 경로를 검사한다.
    await omni.kit.app.get_app().next_update_async()
    # 대기 중 사용자가 다른 Stage를 열었는지도 다시 검사한다.
    cube = UsdGeom.Cube.Define(stage, "/World/ScriptEditorDemo/Cube")
    cube.CreateSizeAttr(0.4)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.5))
```

## 비동기가 필요한 이유

Script Editor와 창의 버튼은 Kit의 실행 흐름 안에서 동작한다. 그 안에서 `while True`나 긴 `time.sleep()`을 실행하면 다음 화면과 버튼 입력을 처리하지 못한다. `await next_update_async()`는 다음 앱 갱신까지 실행을 양보한다. 이 함수가 물리 시뮬레이션을 정확히 한 번 실행한다는 뜻은 아니다.

```python
import asyncio
import omni.kit.app

async def show_three_updates():
    for index in range(3):
        await omni.kit.app.get_app().next_update_async()
        print("앱 갱신", index + 1)

task = asyncio.ensure_future(show_three_updates())
```

위 코드는 이미 실행 중인 Kit 이벤트 루프에 작업을 예약한다. Script Editor에서 `asyncio.run()`으로 또 다른 이벤트 루프를 시작하지 않는다. 반복 Run도 고려해야 하므로 전체 예제는 `_scene_task`를 보관하고 이전 작업이 대기 중이면 취소한다. 예외는 완료 콜백에서 꺼내 출력하므로 실패를 성공처럼 놓치지 않는다.

## 만든 결과를 검사하기

1. Stage에서 `/World/ScriptEditorDemo`를 펼친다. `Cube`와 `Light`가 있어야 한다.
2. Cube를 선택하고 Viewport 위에서 `F`를 누른다.
3. Size `0.4`, Translate Z `0.5`를 확인한다.
4. Run을 다시 누른다. Root가 하나이고 자식도 Cube와 Light 두 개인지 확인한다.
5. 다음 코드를 실행해 Prim 경로와 종류를 직접 확인한다.

```python
import omni.usd
from pxr import Usd

root = omni.usd.get_context().get_stage().GetPrimAtPath("/World/ScriptEditorDemo")
for prim in Usd.PrimRange(root):
    print(prim.GetPath(), prim.GetTypeName())
```

큐브는 **시각용 물체**이다. Rigid Body와 Collision을 적용하지 않았으므로 Play를 눌러도 떨어지지 않는 것이 정상이다. 렌더링용 도형과 물리 물체를 구분하는 연습이다.

## 실패했을 때

| 증상 | 확인 순서 |
|---|---|
| “Stop을 누른 뒤 실행한다” | Stop을 누르고 다시 Run |
| 다른 장면이 경로를 사용한다는 오류 | 해당 Root의 내용을 확인하고 새 Stage에서 재실행 |
| `xformOp` 중복 오류 | 전체 예제를 사용했는지, 조각만 기존 Prim에 반복 실행했는지 확인 |
| 화면이 어두움 | Light 활성 상태와 Viewport 노출·렌더러 준비 상태 확인 |
| 스크립트가 실행되어도 아무 결과 없음 | 콘솔의 “장면 생성 실패” 및 Python traceback 확인 |

**완료 기준:** 반복 Run 후 Root가 하나이며, 속성과 색상을 확인하고 큐브가 떨어지지 않는 이유를 설명한다.

**과제:** 전체 파일에서 크기를 `0.6`으로 바꾸고 다시 실행한다. 변경 전후의 Cube 하단 높이가 각각 `0.3 m`, `0.2 m`인지 계산한다.

[이전](11-workflows.md) · [다음: Standalone](13-standalone.md) · [학습 목차](../../README.md)
