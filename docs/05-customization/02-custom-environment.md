# 커스텀 환경: USD, 메시, 재질, 충돌 형상과 의미 정보

이 장에서는 CAD와 메시로 로봇 주행과 센서 검증에 사용할 환경을 만든다. 외형, 렌더링 재질, 물리 재질, 충돌 형상, 의미 정보와 조명이 각각 어떤 역할을 하는지 구분하고 함께 검증한다.

## 1. 환경 계층과 레이어 설계

```text
warehouse/
├── warehouse.usd                 # 배포 entry point
├── geometry/warehouse_geom.usd   # mesh와 transform
├── physics/warehouse_physics.usda# collider와 physics material
├── looks/warehouse_looks.usda    # render material binding
├── semantics/warehouse_sem.usda  # semantic label
└── textures/                     # albedo, normal, roughness 등
```

사용자가 여는 대표 USD 파일은 여러 레이어와 참조를 조합한다. 형상 원본을 다시 변환해도 물리/의미 정보 레이어를 재적용할 수 있어야 한다. 작업 Stage에는 환경을 `/World/Environment`에 참조하고 로봇/시험 상황은 별도 prim에 둔다.

## 2. 원본 파일 준비

### 지원 형식을 USD로 변환하기

`File > Import` 또는 CAD Converter로 OBJ/FBX/GLTF/CAD 원본을 USD로 변환한다. 변환 전에 다음을 정한다.

- 월드의 길이 단위는 미터로 정한다.
- Z축이 위를 향하는 Z-up 좌표계를 사용한다.
- 회전 중심(pivot)과 원점은 장면에 배치하기 편한 위치에 둔다.
- 고정된 건축물과 이동 가능한 소품·문을 분리한다.
- 텍스처는 임시 절대 경로가 아니라 자산 디렉터리를 기준으로 한 상대 경로로 관리한다.
- 메시가 많으면 공간이나 기능별 Xform 아래에 묶고 이름을 붙인다.

변환 후 Stage 메타데이터를 확인한다.

```python
# Isaac Sim Script Editor
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
print("up axis:", UsdGeom.GetStageUpAxis(stage))
print("meters/unit:", UsdGeom.GetStageMetersPerUnit(stage))
print("default prim:", stage.GetDefaultPrim().GetPath())
```

`metersPerUnit`은 좌표 값의 단위를 지정한다. 이 메타데이터를 바꾸는 것과 형상 자체의 좌표·크기를 바꾸는 것은 다르다. 단위를 잘못 적용했다면 원본을 변환하는 단계에서 배율을 바로잡는다.

## 3. USD 참조로 환경 배치

새 Stage에 참조를 추가하는 최소 Standalone 예시이다.

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

대형 환경은 필요한 구역만 불러올 수 있도록 Payload를 검토한다. 반복되는 팔레트·선반·조명기구는 instanceable 참조로 공유한다. 인스턴스 내부 형상을 바꾸려면 원본 자산을 수정하거나, 인스턴스별로 달라질 요소를 인스턴스 바깥에 별도로 둔다.

## 4. 렌더링 재질 구성

시각 재질은 보이는 색·거칠기·금속성·법선을 정의한다. 물리 마찰계수와는 별도로 설정한다.

| 목적 | 선택 |
|---|---|
| 다른 USD 도구와 교환 | `UsdPreviewSurface` |
| Omniverse에서 높은 시각 품질 | MDL/OmniPBR |
| 투명 유리 | 전용 유리 재질, 센서 영향 별도 검증 |

간단한 `UsdPreviewSurface` 재질을 작성한다.

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

텍스처는 USD 자산 경로로 연결하고 디렉터리를 옮긴 뒤에도 열리는지 확인한다. 노멀 맵의 색 공간, UV 배율, 접선 방향과 뒤집힌 법선이 없는지 여러 조명 조건에서 확인한다.

## 5. 충돌 형상 구성

움직이지 않는 환경에는 충돌 형상을 추가한다. 강체 API를 적용하지 않은 충돌체는 정적으로 취급한다. 움직이는 문이나 팔레트에는 강체·질량을 추가하고 필요에 따라 관절도 설정한다.

| 환경 형상 | 충돌 표현 |
|---|---|
| 평평한 바닥·벽 | 상자 또는 단순 메시 |
| 복잡한 정적 건축물 | 삼각형 메시, 공간별 분할 |
| 이동 가능한 소품 | 볼록 껍질 또는 볼록 분해 |
| 얇은 판 | 실제 두께가 있는 상자 형상 권장 |
| 계단 | 계단별 상자 형상 또는 목적에 맞춘 단순 경사면 |

GUI에서 메시를 선택하고 `Add > Physics > Collider`를 적용한다. 동적 메시의 충돌 근사(Approximation)는 `convexHull` 또는 `convexDecomposition`으로 한다. 다음은 Python으로 기본 도형을 충돌체로 만드는 예다.

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

보이지 않게 설정한 충돌체를 렌더링 메시의 자식으로 묶을 때 변환이 두 번 적용되지 않는지 확인한다. Viewport에서 `Show by Type > Physics > Colliders > All`로 충돌 형상만 표시한다.

### 충돌 형상 검증 시험

1. 작은 상자를 바닥의 여러 지점 위 1 m 높이에서 떨어뜨린다.
2. 로봇 크기의 캡슐 형상을 벽 주변, 출입문과 선반 아래로 움직여 충돌 여부를 확인한다.
3. Nav2가 사용할 경로에서 좁은 통로의 폭을 충돌 형상 기준으로 측정한다.
4. 바닥 이음매에서 바퀴가 걸리거나 바닥을 관통하지 않는지 확인한다.
5. 보이지 않는 벽이 의도치 않게 통로를 막지 않는지 검사한다.

## 6. 물리 재질과 렌더링 재질 구분

`Create > Physics > Physics Material > Rigid Body Material`로 재질을 만들고 충돌 형상에 적용한다.

| 표면 | 정지 마찰계수 | 운동 마찰계수 | 반발계수 | 시작값 예시 |
|---|---:|---:|---:|---|
| 마른 콘크리트 | 높음 | 중간~높음 | 낮음 | `0.9 / 0.8 / 0.05` |
| 매끄러운 금속 | 중간 | 낮음~중간 | 낮음 | `0.5 / 0.35 / 0.05` |
| 고무 바퀴 접촉 | 조합 검증 | 조합 검증 | 낮음 | 로봇과 바닥을 함께 조정 |

수치는 정답이 아니라 초기값 예시이다. 실제 타이어와 바닥 조합에서 가속도, 제동 거리, 옆 방향 미끄러짐을 측정해 값을 맞춘다. 제어기나 질량 설정이 잘못된 문제를 높은 마찰계수로 덮지 않는다.

물리 재질은 충돌체에 직접 적용하거나 상위 Prim에서 지정할 수 있다. 부모와 자식에 서로 다른 재질을 지정했다면 Property에서 실제로 어느 재질이 적용되는지 확인한다.

## 7. 의미 정보 작성

의미 정보 레이블은 인지 데이터의 정답에 사용할 클래스나 인스턴스를 나타낸다. 렌더링 재질이나 물리 재질과는 별도로 지정한다.

GUI에서 `Tools > Replicator > Semantics Schema Editor`를 열어 prim을 선택하고 레이블을 추가·수정·삭제한다. 먼저 어떤 클래스 이름을 사용할지 정리한다.

```yaml
taxonomy:
  floor: traversable floor
  wall: permanent wall
  rack: storage rack
  pallet: movable pallet
  forklift: vehicle
  person: human
```

5.1의 Python 유틸리티를 사용하면 다음처럼 레이블을 추가할 수 있다.

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

부모 Prim과 자식 메시에 서로 모순되는 클래스를 지정하지 않는다. Replicator의 의미 분할(semantic segmentation)과 경계 상자(bounding box) annotator 출력에서 각 물체의 레이블이 맞는지 확인한다. 이름에 `pallet`이 포함되었다는 사실은 의미 정보 레이블이 아니다.

## 8. RTX 센서의 비시각 재질 설정

LiDAR/Radar 반사 특성은 RGB 재질만으로 완전히 결정되지는 않는다. Isaac Sim 5.1은 재질 prim의 USD 속성으로 RTX 비시각 재질을 지정하는 방식을 지원한다. 이전 CSV 기반 재질 매핑은 5.1에서 사용 중단 예정이다.

`isaacsim.sensors.rtx`의 공식 예제를 실행해 속성과 디버그 화면을 확인한다.

```bash
# [SIM]
cd ~/isaacsim
./python.sh \
  standalone_examples/api/isaacsim.sensors.rtx/specify_non_visual_materials.py
```

Viewport의 `RTX - Real-Time > Debug View > Non-Visual Material ID`로 표면별 ID를 확인한다. 재귀반사 표지판, 유리, 아스팔트와 금속을 실제 센서 요구에 맞게 구분한다.

## 9. 조명을 포함한 센서 시험

| 조명 | 역할 | 주의점 |
|---|---|---|
| Dome 조명 | HDRI 기반 전체 환경광 | 텍스처 라이선스, 방향, 노출 |
| Distant 조명 | 태양과 같은 평행광 | 그림자 방향과 광원의 각도 |
| Rect/Disk/Sphere 조명 | 실내 조명기구 | 면적, 광도, 색 온도 |

조명을 Python으로 만든다.

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

조명 강도와 렌더러·노출 설정을 함께 기록한다. 재질을 비교할 때는 카메라 자동 노출과 후처리 설정을 고정한다. 최소한 밝은 낮, 어두운 실내와 역광 세 조건에서 카메라 영상의 밝기 분포, 깊이, LiDAR/Radar 반사점을 검사한다.

## 10. 환경과 로봇 주행 검증

- 바닥과 경사로의 기울기가 로봇이 주행할 수 있는 범위인지 확인한다.
- 출입문의 폭을 렌더링용 메시가 아니라 충돌 형상 기준으로 측정한다.
- 점유 지도를 생성하는 Z축 높이 범위가 LiDAR 높이의 장애물을 포함하는지 확인한다.
- 유리와 얇은 물체가 점유 지도와 RTX 센서에 어떻게 보이는지 기록한다.
- 움직이는 소품은 정적 지도에 없더라도 센서와 costmap에서 검출되어야 한다.
- 지도 원점과 월드 원점 사이의 관계를 Stage 좌표 변환과 맞춘다.

## 11. 성능 측정과 최적화

1. 반복 형상을 instanceable 참조로 만든다.
2. 작은 메시가 수천 개라면 Merge Mesh 도구로 병합할 수 있는지 검토한다.
3. 당장 필요하지 않은 먼 구역은 Payload로 로딩을 조절하고, 화면 표시 여부는 visibility로 관리한다.
4. 충돌 형상은 렌더링 형상보다 단순하게 만든다.
5. 텍스처 해상도를 낮추고, 같은 설정의 재질은 공유해 재질 수를 줄인다.
6. RTX 센서가 필요 없는 프레임에는 렌더 출력(Render Product)/Helper를 끈다.

최적화 전후에 같은 카메라 자세에서 Stage 로딩 시간, Prim·메시·재질·충돌체 수, GPU 메모리, FPS와 실시간 계수(RTF)를 기록한다. 메시 병합으로 서로 다른 물체의 인스턴스 레이블이 합쳐지지 않았는지도 확인한다.

## 12. 환경 검증 체크리스트

- [ ] Z-up, 미터 단위, defaultPrim과 월드 원점이 맞다.
- [ ] 모든 참조/텍스처가 프로젝트 기준 상대 경로 또는 배포 가능한 URI이다.
- [ ] 시각 재질과 물리 재질을 구분했다.
- [ ] 충돌체 표시 모드에서 통로·바닥·벽이 의도대로 보인다.
- [ ] 낙하·충돌 범위·로봇 주행 시험을 통과했다.
- [ ] 클래스 분류표와 annotator 출력이 일치한다.
- [ ] RTX 비시각 재질 ID를 필요한 표면에 설정했다.
- [ ] 세 조명 조건에서 카메라와 RTX 센서를 검증했다.
- [ ] 장면을 다시 열거나 창 없이 실행해도 누락된 자산이 없다.

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
