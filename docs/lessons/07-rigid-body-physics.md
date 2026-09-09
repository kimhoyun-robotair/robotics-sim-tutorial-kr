# 07. 강체, 충돌체, 시간 간격을 설정하다

## 목표와 준비

06단계의 바닥과 상자에 물리를 추가한다. Play를 눌렀을 때 상자가 떨어져 바닥 위에 머무는지 확인한다. 이 단계의 기준은 “눈에 보인다”보다 엄격하다. 상자에 양의 질량이 있고, 바닥과 상자가 모두 충돌 계산에 참여하며, 초기 위치가 겹치지 않아야 한다.

장면에는 `/World/Floor`, `/World/TestBox`와 두 조명이 있어야 한다. `Stop`을 누른 상태에서 편집한다. 6.0.1에서 제공하는 여러 물리 백엔드를 이 실습 중간에 바꾸지 않고 PhysX 경로를 사용한다.

## 1. 화면과 물리의 역할을 구분하다

| 추가한 요소 | 중력에 따라 움직이는가 | 다른 물체와 충돌하는가 | 이번 용도 |
| --- | --- | --- | --- |
| 모양만 존재 | 아니오 | 아니오 | 표식이나 장식 |
| 모양 + Collider | 스스로는 움직이지 않음 | 예 | 고정 바닥과 벽 |
| 모양 + Rigid Body | 예 | Collider 없으면 아니오 | 단독 사용을 피하다 |
| 모양 + Rigid Body + Collider | 예 | 예 | 떨어지는 시험 상자 |

GUI에서 Floor를 선택하고 Property의 `Add > Physics > Collider`를 추가한다. 바닥에는 Rigid Body를 추가하지 않는다. TestBox를 선택하고 `Add > Physics > Rigid Body with Colliders Preset`을 추가한다. 이어 Mass 속성을 추가하거나 해당 물리 속성에서 질량을 `1 kg`으로 입력한다. 메뉴가 보이지 않으면 아래 코드를 사용해 정확한 스키마를 적용한다.

```python
import omni.usd
import omni.timeline
from pxr import Gf, UsdPhysics

assert omni.timeline.get_timeline_interface().is_stopped(), "Stop 후 물리 구성을 수정한다."
stage = omni.usd.get_context().get_stage()
floor_prim = stage.GetPrimAtPath("/World/Floor")
box_prim = stage.GetPrimAtPath("/World/TestBox")
assert floor_prim.IsValid() and box_prim.IsValid(), "06단계의 장면을 먼저 만든다."

UsdPhysics.CollisionAPI.Apply(floor_prim)
UsdPhysics.CollisionAPI.Apply(box_prim)
UsdPhysics.RigidBodyAPI.Apply(box_prim)
UsdPhysics.MassAPI.Apply(box_prim).CreateMassAttr(1.0)
```

## 2. 중력과 물리 시간 간격을 명시하다

`Create > Physics > Simulation Scene`을 추가하고 경로를 `/World/PhysicsScene`으로 정한다. 중력 방향은 `(0,0,-1)`, 크기는 `9.81`로 설정한다. `Simulation Steps per Second`는 `60`으로 둔다.

```python
from pxr import PhysxSchema

physics_scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
physics_scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
physics_scene.CreateGravityMagnitudeAttr(9.81)
PhysxSchema.PhysxSceneAPI.Apply(physics_scene.GetPrim()).CreateTimeStepsPerSecondAttr(60)
stage.SetTimeCodesPerSecond(60)
```

60 Hz 물리는 시뮬레이션 시간 약 `0.0167 s`씩 상태를 계산한다. 이 값과 실제 화면의 FPS는 서로 다르다. 렌더링이 느리면 실제 1초 동안 시뮬레이션 1초를 진행하지 못할 수 있다. 물리 속도를 올릴 목적으로 Scene의 Hz 하나만 바꾸지 않는다. 이후 센서와 ROS를 연결할 때는 물리·타임라인·렌더·발행 주기를 함께 조정한다. [물리 시간과 설정](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html)

## 3. 마찰과 튕김을 설정하다

다음은 바닥과 상자에 같은 물리 재질을 적용한다. 초기 실습은 반발 계수 0으로 시작해 튕김을 줄인다. 이 값이 모든 종류의 진동을 없애는 것은 아니다.

```python
from pxr import UsdShade

surface = UsdShade.Material.Define(stage, "/World/Looks/ContactMaterial")
contact = UsdPhysics.MaterialAPI.Apply(surface.GetPrim())
contact.CreateStaticFrictionAttr(0.7)
contact.CreateDynamicFrictionAttr(0.6)
contact.CreateRestitutionAttr(0.0)
for prim in (floor_prim, box_prim):
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(surface, materialPurpose="physics")
```

시각 재질과 물리 재질을 `materialPurpose="physics"`로 구분하므로 상자의 주황색을 유지하면서 접촉 특성을 설정할 수 있다.

## 4. 재생하고, 멈추고, 다시 시작하다

1. Stage에서 TestBox를 선택해 시작 위치가 `(0,0,1)`인지 확인한다.
2. Play를 누르고 상자가 바닥에 도달하는 모습을 관찰한다.
3. 시뮬레이션 시간 기준으로 충분히 기다려 상자가 안정된 뒤 Pause로 관찰한다.
4. Stop을 눌러 편집 상태로 돌아간다. 초기 위치 복구 여부를 눈으로 확인한다.
5. 처음 위치가 달라졌다면 Stop 상태에서 TestBox를 `(0,0,1)`로 재설정한 뒤 반복한다.

한 변 0.4 m인 상자의 바닥 안착 중심 높이는 약 Z=0.2 m이다. 접촉 오프셋과 계산 오차 때문에 화면상 아주 작은 간격이 생길 수 있다. 공중에서 크게 떠 있거나 바닥 아래로 내려가면 성공으로 처리하지 않는다. 재생 중 실제 위치는 물리/Fabric 상태에서 읽어야 할 수 있으므로 이 단계에서는 USD 초기 Transform 값만 보고 안착했다고 판정하지 않는다.

## 예상 결과와 실패 시 확인

| 증상 | 먼저 확인할 항목 |
| --- | --- |
| 상자가 움직이지 않음 | Play 상태, Rigid Body enabled, kinematic 설정 |
| 상자가 바닥을 통과함 | 두 Prim의 Collider 존재, 바닥 높이와 두께 |
| 시작하자마자 튀어 오름 | 상자가 바닥·다른 Collider 안에 들어가 있는지 |
| 바닥까지 함께 떨어짐 | Floor에 Rigid Body를 잘못 추가했는지 |
| 미세 진동이 계속됨 | 중복 Collider, 과도한 스케일, 질량·접촉 설정 |

빠른 물체와 얇은 벽의 통과는 CCD가 필요한 경우가 있지만, 누락된 Collider를 CCD로 고칠 수는 없다. 먼저 이 작은 낙하 장면을 정상화한 뒤 고속 실험으로 확장한다. CCD는 PhysX Scene과 해당 Rigid Body 양쪽 설정이 필요하다는 점도 구별한다.

## 작은 과제

Stop 상태에서 상자의 X 위치를 0.8로 옮기고 같은 낙하를 반복한다. 바닥 위에 안착하는지 확인한다. 질량만 1 kg에서 2 kg으로 바꿨을 때 자유낙하 가속도가 두 배가 되어야 하는지 설명한다.

## 공식 6.0.1 자료

- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html)
- [Robot Simulation Tips](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_simulation/robot_simulation_tips.html)
- [Physics Data Flow and Engine Integration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/new_physics_engine.html)

이전: [06. 바닥·조명·재질](06-ground-light-material.md) · 다음: [08. USD 구성과 로봇 파일](08-usd-composition.md)
