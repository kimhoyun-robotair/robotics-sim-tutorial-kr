# 17단계. 중간 프로젝트 3 — 재사용 장면 생성 도구를 완성하기

**목표:** 다른 사용자가 Python 코드를 읽지 않고도 버튼으로 동일한 장면을 만들고 지울 수 있게 한다. 산출물은 `tutorial.scene` Extension, 저장한 USD, 반복 동작 확인 기록이다.

## 도구의 동작을 먼저 정하기

`Create / Reset Scene`은 `/World/TutorialScene` 아래에 파란 Cube와 Dome Light를 생성한다. 이미 이 도구가 만든 Root가 있으면 그 부분만 다시 만든다. `Remove Scene`은 같은 Root만 지운다. 다른 경로에 있는 Prim이나 다른 도구가 만든 Root는 수정하지 않는다.

이 프로젝트의 Cube는 시각용 물체이다. 버튼 구조, USD 작성, 중복 실행, 정리를 먼저 확인하기 위한 것이므로 낙하 실험의 동적 강체와 구분한다. 창을 끈다고 사용자가 만든 장면을 지우지 않으며, 삭제는 Remove 버튼으로 명시적으로 수행한다.

## 사용할 Stage를 준비하기

1. 앞 단계의 Extension을 활성화한다.
2. 현재 작업을 저장하고 `File > New`로 빈 Stage를 만든다.
3. Stop을 누르고 Script Editor에서 다음 코드를 실행한다.

```python
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
```

4. Create / Reset Scene을 누른다.
5. Cube가 선택되면 Viewport 위에서 `F`를 누른다.

## UI에서 장면 로직까지 따라가기

[전체 구현](../../extensions/tutorial.scene/tutorial/scene/extension.py)에서는 버튼이 `_create()`를 호출하고, `_create()`가 오류 처리 함수 `_run()`을 거쳐 `create_scene()`을 실행한다.

```python
ui.Button("Create / Reset Scene", clicked_fn=self._create)

def _create(self):
    self._run(create_scene)

def _run(self, action):
    try:
        self._status.text = action()
    except Exception as exc:
        self._status.text = f"실행하지 못했다: {exc}"
```

버튼의 역할은 호출과 상태 표시이다. USD 작성은 별도 함수에 둔다. 이렇게 작성하면 나중에 같은 로직을 테스트하거나 CLI 도구로 옮길 때 UI 코드를 함께 옮길 필요가 줄어든다. 공식 템플릿도 공통 구조와 각 기능 구현을 나누어 제공한다. [공식 6.0.1 Extension Template Generator Explained](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/utilities/extension_templates_tutorial.html)

## 중복 생성과 잘못된 삭제를 막다

도구가 관리하는 Root에는 소유 표식을 넣는다.

```python
ROOT_PATH = "/World/TutorialScene"
OWNER = "tutorial.scene"
root.GetPrim().SetCustomDataByKey("tutorialOwner", OWNER)
```

다시 생성하거나 삭제할 때는 이 표식을 검사한다.

```python
root = stage.GetPrimAtPath(ROOT_PATH)
if root and root.GetCustomDataByKey("tutorialOwner") != OWNER:
    raise RuntimeError("다른 장면이 사용하는 경로이다.")
```

같은 경로에 있다고 무조건 지우지 않는 이유는 Stage를 여러 도구가 함께 편집할 수 있기 때문이다. 이 예제의 Reset은 Root 아래 내용을 통째로 다시 만들므로, 그 아래에 사용자가 별도로 붙인 Prim도 함께 없어질 수 있다. 사용자 작업은 `/World/MyObjects`처럼 다른 Root에 배치한다.

추가로 `is_stopped()`를 검사한다. Pause 중에는 물리 엔진이 아직 실행 상태를 보관할 수 있으므로 강체·센서 편집 도구로 발전시킬 때도 Stop 후 구조를 수정하는 절차가 유용하다.

## 완료 검사를 실제로 수행하기

다음 표의 각 행을 직접 수행하고 결과를 기록한다. “예상” 칸은 작성 환경에서 실행 완료했다는 뜻이 아니다.

| 조작 | 예상 결과 |
|---|---|
| Create 1회 | Root 아래 Cube와 Light 생성 |
| Create 추가 3회 | Root 하나, Cube 하나, Light 하나 유지 |
| Cube 속성 확인 | Size 0.4, Translate `(0, 0, 0.5)` |
| Remove 1회 | `/World/TutorialScene` 삭제 |
| Remove 추가 1회 | 예외 없이 이미 없는 상태 유지 |
| 다시 Create | 같은 위치·크기·색상으로 생성 |
| Play 또는 Pause 상태에서 Create | 상태 문구로 Stop을 요청하고 장면 수정 중단 |
| Stop 후 Create | 정상 생성 |
| Extension 끄기 | 창만 제거하고 장면 유지 |
| Extension 다시 켜기 | 창 하나 생성, 기존 장면 사용 가능 |

다음 Script Editor 코드로 개수를 확인한다.

```python
import omni.usd
from pxr import Usd

stage = omni.usd.get_context().get_stage()
root = stage.GetPrimAtPath("/World/TutorialScene")
paths = [str(prim.GetPath()) for prim in Usd.PrimRange(root)]
print(paths)
assert paths == ["/World/TutorialScene", "/World/TutorialScene/Cube", "/World/TutorialScene/Light"]
```

마지막으로 `File > Save As`에서 저장소의 `artifacts/scene_tool.usda`로 저장한다. 새 Stage를 연 뒤 저장한 파일을 다시 열고 Cube와 Light가 남아 있는지 확인한다. USD는 장면 결과를 저장하고, 버튼을 제공하는 Extension 코드는 별도로 필요하다.

**진단:** 생성은 성공했지만 어두우면 Light 존재, intensity, Viewport 노출을 순서대로 확인한다. 다른 단위 Stage에서 거절되면 그 Stage의 단위를 덮어쓰지 말고 빈 Z-up·1 m Stage를 사용한다. 직접 `pxr`로 작성한 변경은 모든 경우에 GUI Undo 한 번으로 되돌아간다고 가정하지 말고 이 예제의 Reset/Remove를 사용한다.

**완료 기준:** 표의 모든 조작을 확인하고 저장한 USD를 다시 연다. Extension 비활성화와 장면 삭제가 다른 행동임을 설명한다.

**추가 과제:** Cube 색상 변경 버튼을 추가한다. 새 객체를 무제한으로 만들지 말고 같은 Prim의 `displayColor`만 변경하게 한다. 다음 프로젝트에서 센서 설정 버튼으로 확장할 수 있도록 함수 이름과 입력값을 정리한다.

[이전](16-extension-basics.md) · [다음: OmniGraph](18-omnigraph.md) · [학습 목차](../../README.md)
