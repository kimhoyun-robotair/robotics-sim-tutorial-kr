# 06. 바닥, 조명, 재질로 확인하기 쉬운 장면을 만들다

## 목표와 준비

물리 실습 전에 “무엇이 어디에 있는지 확실히 보이는 장면”을 만든다. 바닥은 회색, 시험 상자는 주황색으로 구분하고 조명을 명시한다. 외부 텍스처나 HDR 파일을 사용하지 않아 온라인 자산 누락과 물리 문제를 혼동하지 않도록 한다.

Isaac Sim에서 `File > New`를 선택한다. 타임라인은 Stop 상태로 둔다. `Window > Script Editor`를 열고 05단계처럼 미터·Z-up을 설정한다.

## 1. 바닥의 크기를 정하다

1. `Create > Shape > Cube`를 선택한다.
2. Stage에서 `/World/Floor`로 이름을 정한다.
3. Property에서 Size를 `1`, Scale을 `(6, 6, 0.2)`, Translate를 `(0, 0, -0.1)`로 입력한다.
4. Rotate를 `(0, 0, 0)`으로 둔다.

이 상자의 윗면은 `-0.1 + 0.2 / 2 = 0`이다. 따라서 이후 로봇이 서는 지면 높이를 Z=0으로 맞출 수 있다. 화면에 보이는 격자는 편집 보조 표시이므로 물리 바닥으로 간주하지 않는다. 이 단계의 Floor는 아직 **눈에만 보이는 바닥**이며, 다음 단계에서 Collider를 추가한다.

같은 형태를 코드로 만들거나 GUI 입력을 정확히 맞추려면 다음을 실행한다. 동일한 경로의 Cube를 찾거나 정의하므로 `/World/Floor_01` 같은 중복 물체를 만들지 않는다.

```python
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
floor = UsdGeom.Cube.Define(stage, "/World/Floor")
floor.CreateSizeAttr(1.0)
floor_pose = UsdGeom.XformCommonAPI(floor)
floor_pose.SetTranslate(Gf.Vec3d(0, 0, -0.1))
floor_pose.SetScale(Gf.Vec3f(6, 6, 0.2))
floor_pose.SetRotate(Gf.Vec3f(0, 0, 0))
```

## 2. 시험 상자와 조명을 배치하다

Cube를 하나 더 만들어 `/World/TestBox`로 이름을 정한다. Size는 `0.4`, Scale은 `(1,1,1)`, Translate는 `(0,0,1)`로 설정한다. 바닥과 상자가 겹치지 않는다.

`Create > Lights > Dome Light`로 전체 밝기를 확보하고 `/World/FillLight`로 이름을 정한다. Texture는 비워 두고 intensity를 `300`으로 설정한다. 이어 `Create > Lights > Distant Light`를 만들고 `/World/KeyLight`로 이름을 정한다. intensity는 `1500`, Rotate는 `(-35, 25, 0)`으로 둔다. 이 값은 본 실습에서 비교를 시작하기 위한 초기값이며, 모든 렌더 설정에서 같은 밝기를 보장하는 보정값은 아니다.

```python
from pxr import UsdLux

box = UsdGeom.Cube.Define(stage, "/World/TestBox")
box.CreateSizeAttr(0.4)
UsdGeom.XformCommonAPI(box).SetTranslate(Gf.Vec3d(0, 0, 1))
UsdGeom.XformCommonAPI(box).SetScale(Gf.Vec3f(1, 1, 1))
UsdGeom.XformCommonAPI(box).SetRotate(Gf.Vec3f(0, 0, 0))

fill = UsdLux.DomeLight.Define(stage, "/World/FillLight")
fill.CreateIntensityAttr(300.0)
key = UsdLux.DistantLight.Define(stage, "/World/KeyLight")
key.CreateIntensityAttr(1500.0)
UsdGeom.XformCommonAPI(key).SetRotate(Gf.Vec3f(-35, 25, 0))
```

## 3. 반사 특성이 단순한 재질을 적용하다

처음에는 금속이나 유리 재질을 사용하지 않는다. 밝은 부분이 흰색으로 포화되거나 거울 반사가 생기면 센서 방향을 확인하기 어려워질 수 있다. 다음 코드는 외부 파일이 필요 없는 `UsdPreviewSurface` 재질을 만들고 바닥과 상자에 연결한다.

```python
from pxr import Sdf, UsdShade

def matte_material(path, rgb):
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material

floor_mat = matte_material("/World/Looks/FloorMat", (0.35, 0.38, 0.42))
box_mat = matte_material("/World/Looks/BoxMat", (0.85, 0.25, 0.05))
UsdShade.MaterialBindingAPI.Apply(floor.GetPrim()).Bind(floor_mat)
UsdShade.MaterialBindingAPI.Apply(box.GetPrim()).Bind(box_mat)
```

여기서 `roughness`는 빛 반사의 거칠기이고 **접촉 마찰 계수는 아니다**. 로봇 바퀴가 바닥에서 미끄러질 때 이 값을 높여도 물리 마찰은 바뀌지 않는다. 물리 재질은 다음 단계에서 따로 만든다.

## 4. 물리 실행 전에 화면을 확인하다

Stage에서 Floor를 선택하고 `F`를 누른 뒤 조금 확대한다. 렌더 모드는 Viewport의 렌더 설정에서 실시간 RTX 모드를 선택한다. Path Tracing으로 연습하고 있었다면 실시간 모드로 돌아온다. 상자가 공중에 보이고, 바닥과 색이 구별되며, 상자의 세 면을 볼 수 있도록 시점을 조정한다.

## 예상 결과와 실패 시 확인

회색 바닥과 주황색 상자가 보여야 한다. 전체가 검으면 Stage에 Light Prim이 존재하고 visibility가 켜져 있는지, intensity가 0인지, 화면이 바닥 아래를 보고 있는지 확인한다. 한 면만 어두우면 전체 렌더링 실패와 구분해 조명 방향을 확인한다. 반짝임이 심하면 상자·바닥이 중복 생성되어 같은 면이 겹쳤는지 먼저 확인한다. 동일 평면의 중복은 깊이 판정 충돌로 깜빡임을 일으킬 수 있다.

## 작은 과제

KeyLight의 intensity만 1500에서 750으로 바꾸어 비교한다. 다음에는 원래 값으로 복구하고 BoxMat의 색만 바꾼다. 한 번에 한 설정을 바꾸면 결과의 원인을 어떻게 구분할 수 있는지 기록한다.

## 공식 6.0.1 자료

- [Create Menu](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/menu_create.html)
- [Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/quickstart_isaacsim.html)
- [OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/open_usd.html)

이전: [05. 좌표와 단위](05-transforms-units.md) · 다음: [07. 강체와 충돌](07-rigid-body-physics.md)
