# 09. 중간 프로젝트 1 — GUI로 작은 실험실을 만들다

## 목표와 준비

바닥, 벽 두 개, 장애물, 낙하 상자가 있는 6 m × 6 m 실험실을 GUI로 제작한다. 만든 장면을 `artifacts/scenes/lab.usda`에 저장하고 앱에서 다시 열어 같은 물리 실험을 반복한다. 이 프로젝트의 핵심은 **구성 → 실행 → 저장 → 재개 → 재검사**를 한 번 끝까지 수행하는 것이다.

02~08단계를 마쳤고 Isaac Sim을 실행하기 전에 `TUTORIAL_ROOT`를 export한 상태라고 가정한다. 기존 장면은 필요한 이름으로 저장한 뒤 `File > New`를 선택한다. 타임라인은 Stop 상태로 둔다.

## 1. 장면의 규격을 정하다

다섯 물체를 모두 `Create > Shape > Cube`로 만들고 Size는 **모두 1**로 둔다. 그 뒤 아래 표에 맞춰 이름, Translate, Scale을 입력한다. Rotate는 전부 `(0,0,0)`이다. Stage의 부모가 `/World`인지 확인한다.

| Prim 경로 | Translate `(x,y,z)` [m] | Scale `(x,y,z)` | 물리 역할 |
| --- | --- | --- | --- |
| `/World/Floor` | `(0,0,-0.1)` | `(6,6,0.2)` | 고정 바닥 |
| `/World/NorthWall` | `(0,2.9,0.5)` | `(5.6,0.2,1)` | 북쪽 고정 벽 |
| `/World/EastWall` | `(2.9,0,0.5)` | `(0.2,6,1)` | 동쪽 고정 벽 |
| `/World/Obstacle` | `(-1.5,1,0.4)` | `(0.6,0.6,0.8)` | 고정 장애물 |
| `/World/TestBox` | `(0,0,1)` | `(0.4,0.4,0.4)` | 질량 1 kg인 동적 상자 |

이번에는 Size=1에 Scale을 곱해서 치수를 만들었다. 07단계의 TestBox는 Size=0.4, Scale=1이었으므로 실제 크기는 같지만 저장된 속성은 다르다. Size와 Scale을 둘 다 0.4로 입력하면 상자 한 변이 0.16 m가 되므로 주의한다.

지면 윗면은 Z=0이고 장애물 아랫면도 Z=0이다. 동적 상자는 시작 시 지면에서 떨어져 있다. 바닥과 별도의 Ground Plane을 동시에 생성하지 않는다. 겹치는 바닥을 두는 실수를 처음부터 피한다.

## 2. 빛과 색을 넣다

06단계와 같은 방식으로 `/World/FillLight`에 Dome Light를 만들고 intensity를 300으로 설정한다. `/World/KeyLight`에 Distant Light를 만들고 intensity를 1500, Rotate를 `(-35,25,0)`으로 둔다. Dome의 외부 텍스처는 비워 둔다.

색은 다음 코드로 구분한다. 물체 생성은 GUI에서 끝낸 뒤 실행한다. 크기나 위치를 대신 고치는 코드가 아니므로 잘못 배치한 물체는 Property에서 다시 수정한다.

```python
import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdShade

stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
palette = {
    "Floor": (0.32, 0.35, 0.4),
    "NorthWall": (0.6, 0.65, 0.7),
    "EastWall": (0.6, 0.65, 0.7),
    "Obstacle": (0.1, 0.3, 0.7),
    "TestBox": (0.9, 0.25, 0.05),
}
for name, color in palette.items():
    prim = stage.GetPrimAtPath("/World/" + name)
    assert prim.IsValid(), f"GUI에서 {name}을 먼저 만든다."
    path = "/World/Looks/" + name + "Material"
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
```

## 3. 물리를 적용하다

Floor, NorthWall, EastWall, Obstacle에는 GUI의 `Add > Physics > Collider`만 추가한다. TestBox에는 `Rigid Body with Colliders Preset`을 추가하고 질량을 1 kg으로 설정한다. `Create > Physics > Simulation Scene`을 만들어 `/World/PhysicsScene`으로 정한다. 중력은 `(0,0,-1)` 방향으로 9.81, 물리는 60 Hz로 설정한다.

07단계에서 배운 물리 재질을 만들고 다섯 물체에 적용한다. 다음 코드는 물리 재질과 타임라인 시간 단위를 정확히 맞추는 보조 코드이다.

```python
from pxr import UsdPhysics

stage.SetTimeCodesPerSecond(60)
mat = UsdShade.Material.Define(stage, "/World/Looks/ContactMaterial")
physics_material = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
physics_material.CreateStaticFrictionAttr(0.7)
physics_material.CreateDynamicFrictionAttr(0.6)
physics_material.CreateRestitutionAttr(0.0)
for name in palette:
    prim = stage.GetPrimAtPath("/World/" + name)
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat, materialPurpose="physics")
```

## 4. 재생 전에 구성 오류를 찾다

아래 코드는 만든 장면을 검사한다. 실패한 assert가 있으면 해당 Prim을 GUI에서 고친 뒤 다시 실행한다. 검사에 통과했다고 실제 물리와 렌더링이 검증된 것은 아니다.

```python
import math
import omni.timeline
from pxr import PhysxSchema, Usd, UsdLux

assert omni.timeline.get_timeline_interface().is_stopped(), "Stop 상태에서 검사한다."
expected = {
    "Floor": ((0, 0, -0.1), (6, 6, 0.2)),
    "NorthWall": ((0, 2.9, 0.5), (5.6, 0.2, 1)),
    "EastWall": ((2.9, 0, 0.5), (0.2, 6, 1)),
    "Obstacle": ((-1.5, 1, 0.4), (0.6, 0.6, 0.8)),
    "TestBox": ((0, 0, 1), (0.4, 0.4, 0.4)),
}
for name, (target_position, target_scale) in expected.items():
    prim = stage.GetPrimAtPath("/World/" + name)
    cube = UsdGeom.Cube(prim)
    assert cube, f"{name}: Shape의 Cube인지 확인한다."
    assert math.isclose(cube.GetSizeAttr().Get(), 1.0), f"{name}: Size를 1로 맞춘다."
    t, r, s, pivot, order = UsdGeom.XformCommonAPI(prim).GetXformVectors(Usd.TimeCode.Default())
    assert all(abs(a-b) < 1e-5 for a, b in zip(t, target_position)), f"{name}: 위치 오류"
    assert all(abs(a-b) < 1e-5 for a, b in zip(s, target_scale)), f"{name}: Scale 오류"
    assert all(abs(v) < 1e-5 for v in r), f"{name}: 회전을 0으로 맞춘다."
    assert prim.HasAPI(UsdPhysics.CollisionAPI), f"{name}: Collider 누락"
    assert UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get(), f"{name}: 충돌 비활성"
    assert prim.HasAPI(UsdPhysics.RigidBodyAPI) == (name == "TestBox"), f"{name}: Rigid Body 확인"

box = stage.GetPrimAtPath("/World/TestBox")
assert UsdPhysics.RigidBodyAPI(box).GetRigidBodyEnabledAttr().Get()
assert not UsdPhysics.RigidBodyAPI(box).GetKinematicEnabledAttr().Get()
assert box.HasAPI(UsdPhysics.MassAPI), "TestBox에 Mass를 명시한다."
assert math.isclose(UsdPhysics.MassAPI(box).GetMassAttr().Get(), 1.0)
scenes = [p for p in stage.Traverse() if p.IsA(UsdPhysics.Scene)]
assert len(scenes) == 1, "Physics Scene을 정확히 하나 둔다."
physics_scene = UsdPhysics.Scene(scenes[0])
assert tuple(physics_scene.GetGravityDirectionAttr().Get()) == (0.0, 0.0, -1.0)
assert math.isclose(physics_scene.GetGravityMagnitudeAttr().Get(), 9.81, rel_tol=1e-5)
assert PhysxSchema.PhysxSceneAPI(scenes[0]).GetTimeStepsPerSecondAttr().Get() == 60
for light_name in ("FillLight", "KeyLight"):
    light = UsdLux.LightAPI(stage.GetPrimAtPath("/World/" + light_name))
    assert light and light.GetIntensityAttr().Get() > 0, f"{light_name}: 조명 확인"
print("작성 속성 검사 통과. 다음은 실제 재생과 재열기 검사이다.")
```

이 검사는 정해진 다섯 Prim의 구성 오류를 찾는다. 중복 Prim 전체, 실제 접촉, 화면 노출, 드라이버 상태까지 검사하는 코드는 아니다. Stage를 한 번 펼쳐 의도하지 않은 복사본이 있는지도 확인한다.

## 5. 낙하·저장·재개를 수행하다

1. Floor를 선택해 `F`를 누른 뒤 벽 두 개와 중앙 상자를 모두 볼 수 있게 시점을 조절한다.
2. Play 후 시뮬레이션 시간 약 5초 동안 관찰한다. 상자가 바닥에 도달한 뒤 계속 튀거나 바닥 아래로 사라지지 않아야 한다.
3. Stop 후 초기 위치로 돌아오는지 확인한다. 필요하면 TestBox의 Translate를 `(0,0,1)`로 복구한다.
4. `File > Save As`에서 저장소의 `artifacts/scenes/lab.usda`를 선택한다. 파일 선택 창은 `$TUTORIAL_ROOT`를 셸처럼 확장하지 않을 수 있으므로 터미널에 출력한 실제 절대 경로를 사용한다.
5. `File > New`로 장면을 비운 뒤 `File > Open`으로 `lab.usda`를 다시 연다.
6. 같은 시점에서 다시 Play하고 낙하를 관찰한다. 저장 전과 같은 환경·중력·크기인지 비교한다.

저장 경로를 정확하게 만들고 싶다면 3번과 4번 사이에 다음 코드를 사용할 수 있다. **Stop 상태의 초기 배치**를 저장한다.

```python
import os
from pathlib import Path

assert omni.timeline.get_timeline_interface().is_stopped()
scene_path = Path(os.environ["TUTORIAL_ROOT"]) / "artifacts" / "scenes" / "lab.usda"
scene_path.parent.mkdir(parents=True, exist_ok=True)
stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
assert stage.GetRootLayer().Export(str(scene_path))
print("다시 열 파일:", scene_path)
```

## 통과 기준과 실패 시 확인

| 검사 | 통과 기준 | 남길 근거 |
| --- | --- | --- |
| 작성 속성 | 위 assert를 모두 통과하다 | Script Editor 출력 |
| 렌더링 | 바닥·벽·상자 색을 구분하고 화면이 지속적으로 표시되다 | 재생 중 화면 캡처 |
| 물리 | 상자가 지면에 안착하고 눈에 띄는 계속된 진동·관통이 없다 | 약 5초 재생 관찰 기록 |
| 저장 재개 | 새 장면에서 저장 파일을 열어 같은 낙하를 재현하다 | 재열기 후 화면과 파일 경로 |

실제 관찰하지 않은 항목에 “통과”를 적지 않는다. 실패하면 모델을 한꺼번에 고치지 말고 조명 → 초기 겹침 → Collider → Rigid Body → 질량 → 물리 Scene 순서로 원인을 좁힌다. 기록은 `artifacts/logs/lab-check.md`에 남긴다.

## 작은 과제

장애물을 한 개 더 추가하되 중앙에 폭 1 m 이상의 통로를 남긴다. 원본 `lab.usda`는 유지하고 `lab-layout-b.usda`로 저장한다. 추가 장애물이 고정 물체이며 새 상자 낙하를 방해하지 않는지 다시 확인한다.

## 공식 6.0.1 자료

- [Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/quickstart_isaacsim.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html)
- [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/intro_to_usd.html)

이전: [08. USD 구성](08-usd-composition.md) · 다음: [10. 안정성과 진단](10-stability-inspection.md)
