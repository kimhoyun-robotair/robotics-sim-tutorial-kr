# 커스텀 환경: USD, mesh, material, collider와 semantics

이 튜토리얼에서는 CAD/mesh를 보기 좋은 장면이 아니라 robot과 sensor가 신뢰할 수 있는 environment asset으로 만들다. geometry, render material, physics material, collider, semantics와 lighting을 별도 책임으로 다루다.

## 1. environment 계층과 layer를 설계하다

```text
warehouse/
├── warehouse.usd                 # 배포 entry point
├── geometry/warehouse_geom.usd   # mesh와 transform
├── physics/warehouse_physics.usda# collider와 physics material
├── looks/warehouse_looks.usda    # render material binding
├── semantics/warehouse_sem.usda  # semantic label
└── textures/                     # albedo, normal, roughness 등
```

entry file은 여러 layer/reference를 조립하다. geometry source를 다시 변환해도 physics/semantics layer를 재적용할 수 있어야 하다. 작업 Stage에는 environment를 `/World/Environment`에 reference하고 robot/scenario는 별도 prim에 두다.

## 2. source 파일을 준비하다

### 지원 형식을 USD로 변환하다

`File > Import` 또는 CAD Converter로 OBJ/FBX/GLTF/CAD source를 USD로 변환하다. 변환 전에 다음을 정하다.

- world length unit은 meter이다.
- Z-up을 기본으로 하다.
- pivot/origin은 배치에 쓸 수 있는 위치에 두다.
- 정적 architecture, 이동 가능한 prop과 door를 분리하다.
- texture는 임시 absolute path가 아니라 asset 폴더 상대 경로로 묶다.
- 이름 없는 수천 mesh를 공간/기능 단위 Xform 아래 정리하다.

변환 후 Stage metadata를 확인하다.

```python
# Isaac Sim Script Editor
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
print("up axis:", UsdGeom.GetStageUpAxis(stage))
print("meters/unit:", UsdGeom.GetStageMetersPerUnit(stage))
print("default prim:", stage.GetDefaultPrim().GetPath())
```

`metersPerUnit` metadata를 바꾸는 것과 geometry transform을 실제로 scale하는 것은 다르다. 잘못된 unit asset은 root에 임시 scale override를 남기지 말고 변환 pipeline에서 정규화하다.

## 3. composition으로 환경을 배치하다

새 Stage에 reference를 추가하는 최소 standalone 예시이다.

```python
from isaacsim import SimulationApp
app = SimulationApp({"headless": False})

import omni.usd
from pxr import UsdGeom

context = omni.usd.get_context()
context.new_stage()
stage = context.get_stage()

UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
stage.SetDefaultPrim(world)

env = stage.DefinePrim("/World/Environment", "Xform")
env.GetReferences().AddReference("/abs/warehouse/warehouse.usd")

stage.GetRootLayer().Export("/abs/stages/warehouse_scene.usda")
app.update()
app.close()
```

대형 environment는 payload로 선택적 load를 검토하고, 반복 pallet/rack/light fixture는 instanceable reference를 사용하다. instance 내부를 개별 수정해야 하면 prototype/source asset에서 수정하거나 instance 밖에 override prim을 두다.

## 4. render material을 구성하다

render material은 보이는 색·거칠기·금속성·normal을 정의하다. physics friction과 같은 값이 아니다.

| 목적 | 선택 |
|---|---|
| 다른 USD 도구와 교환 | `UsdPreviewSurface` |
| Omniverse에서 높은 시각 품질 | MDL/OmniPBR |
| 투명 유리 | 전용 glass material, sensor 영향 별도 검증 |

간단한 `UsdPreviewSurface` material을 authoring하다.

```python
import omni.usd
from pxr import Gf, Sdf, UsdShade

stage = omni.usd.get_context().get_stage()
material = UsdShade.Material.Define(stage, "/World/Looks/Floor")
shader = UsdShade.Shader.Define(stage, "/World/Looks/Floor/Shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
    Gf.Vec3f(0.18, 0.20, 0.22)
)
shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.75)
shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
material.CreateSurfaceOutput().ConnectToSource(
    shader.ConnectableAPI(), "surface"
)

floor = stage.GetPrimAtPath("/World/Environment/Floor/mesh")
UsdShade.MaterialBindingAPI.Apply(floor).Bind(material)
```

texture file은 USD asset path로 authoring하고 상대 경로 이동 시험을 하다. normal map의 color space, UV scale, tangent와 flipped normal을 여러 광원에서 확인하다.

## 5. collider를 별도로 authoring하다

정적 환경에 collider만 적용하고 Rigid Body API를 적용하지 않으면 static collision이 되다. 움직여야 하는 door/pallet에는 rigid body, mass와 joint를 별도 설정하다.

| environment geometry | collision 표현 |
|---|---|
| 평평한 floor/wall | box 또는 단순 mesh |
| 복잡한 정적 건축물 | triangle mesh, 공간별 분할 |
| 이동 가능한 prop | convex hull/decomposition |
| 얇은 sheet | 실제 두께를 가진 box 권장 |
| 계단 | 각 step box 또는 목적에 맞춘 단순 ramp |

GUI에서 mesh를 선택하고 `Add > Physics > Collider`를 적용하다. dynamic mesh는 approximation을 `convexHull` 또는 `convexDecomposition`으로 하다. Python으로 primitive collider를 만드는 예시이다.

```python
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
wall = UsdGeom.Cube.Define(stage, "/World/Environment/Colliders/Wall_A")
wall.CreateSizeAttr(1.0)
wall.AddTranslateOp().Set(Gf.Vec3d(0.0, 3.0, 1.0))
wall.AddScaleOp().Set(Gf.Vec3f(5.0, 0.1, 2.0))
UsdPhysics.CollisionAPI.Apply(wall.GetPrim())
wall.GetVisibilityAttr().Set(UsdGeom.Tokens.invisible)
```

invisible collider를 render mesh의 child로 묶을 때 transform이 두 번 적용되지 않는지 확인하다. Viewport에서 `Show by Type > Physics > Colliders > All`로 collider만 표시하다.

### collider acceptance test

1. 작은 cube를 여러 floor 위치에서 1 m 높이에서 떨어뜨리다.
2. wall/door/under-rack을 robot-sized capsule로 sweep하다.
3. Nav2 경로의 좁은 passage 폭을 collider 기준으로 측정하다.
4. seam에서 wheel이 걸리거나 바닥을 관통하지 않는지 확인하다.
5. invisible wall이 의도치 않게 통로를 막지 않는지 검사하다.

## 6. physics material을 render material과 분리하다

`Create > Physics > Physics Material > Rigid Body Material`로 material을 만들고 collider에 bind하다.

| 표면 | static friction | dynamic friction | restitution | 시작값 예시 |
|---|---:|---:|---:|---|
| dry concrete | 높음 | 중간~높음 | 낮음 | `0.9 / 0.8 / 0.05` |
| smooth metal | 중간 | 낮음~중간 | 낮음 | `0.5 / 0.35 / 0.05` |
| rubber wheel contact | 조합 검증 | 조합 검증 | 낮음 | robot+floor 함께 튜닝 |

수치는 정답이 아니라 초기값 예시이다. 실제 tire/floor 조합의 acceleration, braking distance와 lateral slip을 측정해 맞추다. friction을 매우 높여 controller/weight 오류를 숨기지 않다.

physics material은 collider geometry에 직접 bind하거나 rigid body 상위에 override할 수 있다. 자식 binding과 상위 binding의 resolution을 Property에서 확인하다.

## 7. semantics를 authoring하다

semantic label은 perception ground truth의 class/instance 의미이고 render material이나 physics material이 아니다.

GUI에서 `Tools > Replicator > Semantics Schema Editor`를 열어 prim을 선택하고 label을 추가·수정·삭제하다. label taxonomy를 먼저 문서화하다.

```yaml
taxonomy:
  floor: traversable floor
  wall: permanent wall
  rack: storage rack
  pallet: movable pallet
  forklift: vehicle
  person: human
```

Python utility를 사용하는 5.1 pattern이다.

```python
import omni.usd
from isaacsim.core.utils.semantics import add_update_semantics

stage = omni.usd.get_context().get_stage()
for path, label in {
    "/World/Environment/Floor": "floor",
    "/World/Environment/Rack_A": "rack",
    "/World/Environment/Pallet_A": "pallet",
}.items():
    prim = stage.GetPrimAtPath(path)
    if not prim.IsValid():
        raise RuntimeError(f"missing prim: {path}")
    add_update_semantics(prim, label, type_label="class")
```

상위 prim과 모든 mesh child에 모순되는 class를 중복 authoring하지 않다. Replicator semantic segmentation/bounding-box annotator로 실제 출력 mapping을 확인하다. 이름에 `pallet`이 포함되었다는 사실은 semantic label이 아니다.

## 8. RTX sensor의 non-visual material을 구분하다

LiDAR/Radar 반사 특성은 RGB material만으로 완전히 결정되지 않다. Isaac Sim 5.1은 Material prim의 USD attribute로 RTX non-visual material을 지정하는 방식을 지원하다. 이전 CSV 기반 mapping은 5.1에서 deprecated이다.

`isaacsim.sensors.rtx`의 공식 예제를 실행해 attribute와 debug view를 확인하다.

```bash
# [SIM]
cd ~/isaacsim
./python.sh \
  standalone_examples/api/isaacsim.sensors.rtx/specify_non_visual_materials.py
```

Viewport의 `RTX - Real-Time > Debug View > Non-Visual Material ID`로 표면별 ID를 확인하다. retroreflective sign, glass, asphalt와 metal을 실제 sensor 요구에 맞게 구분하다.

## 9. lighting을 sensor 시험의 일부로 만들다

| light | 역할 | 주의점 |
|---|---|---|
| Dome Light | HDRI 기반 전체 환경광 | texture license, orientation, exposure |
| Distant Light | 태양과 같은 평행광 | shadow 방향과 angle |
| Rect/Disk/Sphere Light | 실내 fixture | 면적, intensity, color temperature |

조명을 Python으로 만들다.

```python
import omni.usd
from pxr import Gf, UsdGeom, UsdLux

stage = omni.usd.get_context().get_stage()

sun = UsdLux.DistantLight.Define(stage, "/World/Lights/Sun")
sun.CreateIntensityAttr(1200.0)
sun.CreateAngleAttr(0.53)
sun.AddRotateXYZOp().Set(Gf.Vec3f(-35.0, 20.0, 25.0))

fill = UsdLux.DomeLight.Define(stage, "/World/Lights/Sky")
fill.CreateIntensityAttr(500.0)
fill.CreateExposureAttr(0.0)
```

intensity 단위와 renderer/exposure 조합을 기록하다. camera auto-exposure 또는 post-processing을 바꾸면서 material만 튜닝하지 않다. 최소한 밝은 낮, 어두운 실내와 역광 세 조건에서 camera histogram, depth, LiDAR/Radar return을 검사하다.

## 10. environment와 navigation을 함께 검증하다

- ground와 ramp의 slope가 robot capability 안에 있는지 확인하다.
- door width를 render mesh가 아니라 collider 기준으로 측정하다.
- occupancy map Z slice가 LiDAR 높이의 장애물을 포함하다.
- glass/얇은 물체가 occupancy와 RTX sensor에 어떻게 보이는지 기록하다.
- dynamic prop은 static map에는 없더라도 sensor/costmap에서 검출되게 하다.
- map origin, world origin과 Stage transform을 일치시키다.

## 11. 성능을 측정하고 최적화하다

1. 반복 geometry를 instanceable reference로 만들다.
2. 작은 mesh 수천 개는 Mesh Merge Tool을 검토하다.
3. invisible/먼 구역은 payload/visibility로 load와 render를 줄이다.
4. collision은 visual detail보다 훨씬 단순하게 하다.
5. texture resolution과 unique material 수를 줄이다.
6. RTX sensor가 필요 없는 frame에는 render product/helper를 끄다.

최적화 전후에 Stage load time, prim/mesh/material/collider 수, GPU memory, FPS와 real-time factor를 같은 camera pose에서 기록하다. merge한 뒤 semantic instance 경계가 사라지는 trade-off를 확인하다.

## 12. environment acceptance checklist

- [ ] Z-up, meter, default prim과 world origin이 맞다.
- [ ] 모든 reference/texture가 project-relative 또는 배포 가능한 URI이다.
- [ ] visual material과 physics material을 구분했다.
- [ ] collider-only view에서 통로·floor·wall이 의도대로 보이다.
- [ ] drop/sweep/navigation collision test를 통과했다.
- [ ] semantic taxonomy와 annotator output이 일치하다.
- [ ] RTX non-visual material ID를 필요한 표면에 설정했다.
- [ ] 세 lighting 조건에서 camera와 RTX sensor를 검증했다.
- [ ] reopen/headless 환경에서도 missing asset이 없다.

## 출처

- [Isaac Sim 5.1 — Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Omniverse — CAD Converter](https://docs.omniverse.nvidia.com/extensions/latest/ext_cad-converter.html)
- [Isaac Sim 5.1 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Isaac Sim 5.1 — Object-Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html)
- [Isaac Sim 5.1 — Scene-Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
- [Isaac Sim 5.1 — Replicator Overview and Semantics Schema Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html)
- [Isaac Sim 5.1 — RTX Sensor Non-Visual Materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html)
- [Isaac Sim 5.1 — Static Warehouse Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/tutorial_static_assets.html)
- [Isaac Sim 5.1 — Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
