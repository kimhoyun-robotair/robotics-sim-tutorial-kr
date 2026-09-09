# 04. GUI에서 물체를 만들고 화면을 조작하다

## 목표와 준비

Isaac Sim 6.0.1을 실행한 상태에서 Viewport, Stage, Property의 역할을 구분한다. 물체를 이동하는 조작과 보는 위치를 옮기는 조작을 따로 연습한다. 이 단계에서는 물리 시뮬레이션을 켜지 않는다.

## 1. 작업 화면을 읽다

`File > New`로 빈 장면을 만든다. 이전 실습을 저장할지 묻는다면 필요한 장면은 다른 이름으로 저장한다.

| 화면 영역 | 보는 정보 | 이번 실습의 조작 |
| --- | --- | --- |
| Viewport | 장면을 렌더링한 화면 | 상자를 선택하고 시점을 움직이다 |
| Stage | Prim의 이름과 부모·자식 구조 | 화면 밖의 상자도 경로로 찾다 |
| Property | 선택한 Prim의 속성 | 위치를 정확한 숫자로 입력하다 |
| 왼쪽 도구 모음 | 이동·회전·크기와 재생 도구 | 화살표와 재생 버튼을 구별하다 |
| 상단 메뉴 | 생성·저장·도구·창 열기 | 잃어버린 패널을 다시 열다 |

오른쪽 패널이 없으면 `Window` 메뉴에서 `Stage`와 `Property`를 찾는다. 패널 제목을 드래그하면 도킹 위치를 바꿀 수 있다. 패널의 `×`는 해당 패널을 닫는 버튼이며 장면 안의 물체를 삭제하지 않는다. [공식 UI 설명](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_user_interface.html)

## 2. 상자를 만들고 이름을 붙이다

1. `Create > Shape > Cube`를 선택한다. UI에서 `Shapes`로 표시되면 그 아래 `Cube`를 사용한다.
2. Stage에서 생성된 Cube를 선택한다. 부모가 `/World`인지 경로를 확인한다.
3. 이름을 `PracticeCube`로 바꾼다. Stage의 이름을 편집하거나 우클릭 메뉴의 이름 변경 기능을 사용한다.
4. Property의 Transform에서 Translate를 `(0, 0, 0.5)`, Rotate를 `(0, 0, 0)`, Scale을 `(1, 1, 1)`로 입력한다.
5. `Cube`의 Size 속성이 있으면 `0.4`로 입력한다. Mesh Cube를 만든 경우에는 Size 속성이 없을 수 있으므로 `Shape`의 Cube를 다시 만든다.

## 3. 화면을 움직이다

먼저 Stage에서 상자를 선택한 뒤 마우스 포인터를 Viewport 위로 옮기고 `F`를 누른다. 선택한 물체를 중심으로 화면이 맞춰진다. 다음 조작은 **카메라 시점**을 바꾸며, 상자의 Translate 값을 바꾸지 않는다.

| 조작 | 결과 |
| --- | --- |
| 마우스 휠 | 화면을 확대하거나 축소하다 |
| 가운데 버튼을 누르고 드래그 | 보는 위치를 평행 이동하다 |
| 오른쪽 버튼을 누르고 드래그 | 시선 방향을 바꾸다 |
| 오른쪽 버튼을 누른 채 `W/A/S/D` | 앞으로·왼쪽으로·뒤로·오른쪽으로 이동하다 |
| 오른쪽 버튼을 누른 채 `Q/E` | 위·아래로 이동하다 |
| 물체 선택 후 `F` | 해당 물체가 잘 보이도록 맞추다 |

공식 단축키 표는 회전 관찰 조작을 `Opt + LMB`로도 표시한다. 키보드 레이아웃이나 창 관리자와 충돌한다면 우선 `F`, 휠, 가운데·오른쪽 버튼 조작을 익힌다. [공식 단축키 표](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_keyboard_shortcuts.html)

## 4. 물체를 움직이다

Viewport에 마우스를 놓고 **오른쪽 버튼에서 손을 뗀 뒤** `W`를 누른다. 이제 `W`는 카메라 전진이 아니라 물체 이동 도구를 뜻한다. 빨강·초록·파랑 화살표가 보이면 하나만 잡아 짧게 움직인다. 다시 Property를 보아 어떤 좌표가 바뀌었는지 확인한다.

`E`는 물체 회전, `R`은 크기 변경이다. 회전이나 크기를 시험한 뒤 Property에서 Rotate `(0, 0, 0)`, Scale `(1, 1, 1)`로 되돌린다. 숫자 입력 칸에 커서가 있는 동안 단축키를 누르면 글자가 입력될 수 있으므로 Viewport를 클릭한 뒤 사용한다.

## 5. GUI에서 바뀐 값을 코드로 확인하다

`Window > Script Editor`를 열고 다음을 실행한다. 부모가 `/World`가 아니라면 Stage의 실제 경로로 수정한다.

```python
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/PracticeCube")
assert prim.IsValid(), "Stage에서 PracticeCube의 전체 경로를 확인한다."
for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
    print(op.GetOpName(), op.Get())
```

GUI에 표시한 Translate/Rotate/Scale은 USD의 `xformOp`로 기록된다. 단, 파일마다 하나의 행렬로 저장하는 등 표현이 다를 수 있으므로 이 단계에서는 속성을 읽는 데 집중한다. 화면을 돌리는 것만으로 출력 값이 바뀌어서는 안 된다.

## 예상 결과와 실패 시 확인

상자가 화면 중앙에 있고, 마우스로 화면을 옮겨도 상자의 위치 값은 그대로여야 한다. 물체가 안 보이면 먼저 Stage에서 선택하고 `F`를 누른다. 그래도 안 보이면 눈 모양 표시의 visibility와 상자의 Scale이 0인지 확인한다. 모든 패널이 사라졌다면 `F7`로 UI 표시 상태를 확인하고, 전체 화면은 `F11`로 전환한다.

## 작은 과제

상자를 화면의 오른쪽에 보이게 하는 방법을 두 가지로 수행한다. 첫 번째는 카메라만 움직이고, 두 번째는 상자의 X 좌표를 바꾼다. 두 결과의 이미지가 비슷해도 장면 데이터는 어떻게 다른지 적는다.

## 공식 6.0.1 자료

- [User Interface Reference](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_user_interface.html)
- [Keyboard Shortcuts Reference](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_keyboard_shortcuts.html)
- [Create Menu](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/menu_create.html)

이전: [03. 설치와 첫 실행](03-installation.md) · 다음: [05. 좌표와 단위](05-transforms-units.md)
