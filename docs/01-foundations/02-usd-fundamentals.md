# USD 핵심 개념과 로봇 포맷 비교

이 장에서는 USD를 파일 형식이 아니라 장면을 조립하는 시스템으로 이해한다. 마지막에는 Stage, Layer, Prim, Schema, Composition, Xform, Variant, Reference, Payload, Instancing을 설명하고, URDF·Xacro·MJCF와 언제 무엇을 기준 원본으로 삼아야 하는지 판단할 수 있어야 한다.

## USD는 무엇인가

USD는 Universal Scene Description의 약자다. 계층적으로 구성된 정적 데이터와 시간 샘플 데이터를 기록하고, 여러 파일과 수정 사항을 하나의 장면으로 합성하는 데이터 모델·파일 형식·런타임이다.

로봇 시뮬레이션에서 USD는 다음을 함께 표현할 수 있다.

- 로봇과 환경의 계층, 기하, 변환, 재질, 조명
- 강체, 충돌체, 질량, Joint, Articulation 같은 물리 속성
- Camera, LiDAR, IMU 같은 센서 Prim과 설정
- 애니메이션 및 시간에 따른 속성 값
- 외부 자산 참조, 지연 로딩, 선택 가능한 구성
- 여러 사용자의 비파괴적 수정 레이어

URDF가 로봇 한 대의 링크·조인트 트리를 전달하는 데 집중한다면 USD는 로봇, 창고, 조명, 센서, 재질, 애니메이션을 포함하는 전체 디지털 월드를 합성하는 데 초점을 둔다.

## USDA, USDC, USD, USDZ

| 확장자 | 의미 | 권장 용도 |
|---|---|---|
| .usda | 사람이 읽을 수 있는 텍스트 인코딩 | 학습, 코드 리뷰, 디버깅, 작은 오버레이 |
| .usdc | Crate라고 부르는 바이너리 인코딩 | 큰 메시, 대규모 장면, 빠른 로딩 |
| .usd | 내부가 USDA 또는 USDC일 수 있는 중립 확장자 | 파이프라인이 인코딩보다 자산 의미를 강조할 때 |
| .usdz | USD와 의존 자산을 규칙에 맞게 묶은 비압축 ZIP 패키지 | 전송과 배포. 내부를 직접 수정하는 용도는 아니다 |

USDA와 USDC는 같은 USD 데이터 모델을 무손실로 양방향 변환할 수 있다. .usd는 확장자만 보고 텍스트인지 바이너리인지 단정할 수 없다. .usdz는 일반 ZIP과 비슷하지만 파일 정렬과 패키지 규칙이 있으며 읽기 전용으로 취급해야 한다.

~~~bash
# 텍스트로 확인한다.
usdcat robot.usdc | less

# 텍스트와 바이너리 사이를 변환한다.
usdcat robot.usdc -o robot.usda
usdcat robot.usda -o robot.usdc

# .usd의 내부 인코딩을 명시한다.
usdcat robot.usda -o robot.usd --usdFormat usdc
~~~

## 가장 중요한 객체: Stage, Layer, Prim

### Stage

Stage는 조합이 끝난 장면을 보여 주는 최상위 컨테이너다. 사용자는 Stage에서 /World/Robot/base_link 같은 경로로 Prim을 조회한다. Stage 자체가 반드시 파일 하나와 같지는 않다. Root Layer, Session Layer, Sublayer, Reference, Payload 등 여러 Layer의 의견을 합성한 결과다.

~~~python
from pxr import Usd

stage = Usd.Stage.Open("warehouse.usd")
prim = stage.GetPrimAtPath("/World/Robot")
print(prim.GetPath(), prim.GetTypeName())

for prim in stage.Traverse():
    print(prim.GetPath())
~~~

### Layer

Layer는 저작된 장면 설명을 보관하는 컨테이너다. 대개 .usda, .usdc, .usd 파일 하나가 Layer 하나에 대응하지만, 메모리 전용 익명 Layer도 만들 수 있다.

Stage와 Layer의 차이는 다음과 같다.

- Layer는 그 파일에 직접 기록된 Prim Spec과 opinion을 보여 준다.
- Stage는 여러 Layer와 composition arc를 평가한 최종 Prim을 보여 준다.
- 같은 /World/Robot Prim에 여러 Layer가 서로 다른 속성 값을 저작할 수 있다.
- 더 강한 opinion이 약한 opinion을 덮지만 약한 Layer의 데이터가 삭제되는 것은 아니다.

예를 들어 base.usda가 로봇의 기본 위치를 (0, 0, 0)으로 정의하고, shot.usda가 같은 경로에 (2, 0, 0)이라는 더 강한 override를 저작하면 Stage에서는 (2, 0, 0)이 보인다. base.usda는 바뀌지 않는다.

~~~usda
# base.usda
#usda 1.0
def Xform "World" {
    def Xform "Robot" {
        double3 xformOp:translate = (0, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }
}
~~~

~~~usda
# shot.usda
#usda 1.0
(
    subLayers = [@base.usda@]
)
over "World" {
    over "Robot" {
        double3 xformOp:translate = (2, 0, 0)
    }
}
~~~

Root Layer의 직접 opinion은 일반적으로 그 Root Layer가 포함한 Sublayer보다 강하다. Sublayer 목록 안에서도 순서가 강도에 영향을 준다. 복잡한 장면에서는 추측하지 말고 Isaac Sim의 Layer 패널이나 usdview의 composition 정보를 확인하는 습관을 들인다.

### Session Layer와 Edit Target

Session Layer는 Stage 위에 존재하는 가장 강한 임시 Layer다. 사용자별 임시 선택이나 실험에 적합하지만 보통 Root Layer를 저장해도 함께 저장되지 않는다.

Edit Target은 새 opinion을 어느 Layer에 쓸지 정한다. 보이는 값이 맞아도 잘못된 Layer에 저작하면 자산 재사용성이 무너진다.

~~~python
from pxr import Sdf, Usd, UsdGeom

stage = Usd.Stage.Open("shot.usda")
overlay = Sdf.Layer.CreateNew("robot_pose_override.usda")
stage.GetRootLayer().subLayerPaths.insert(0, overlay.identifier)

with Usd.EditContext(stage, overlay):
    robot = UsdGeom.Xform.Get(stage, "/World/Robot")
    robot.AddTranslateOp(opSuffix="lesson").Set((1.0, 0.0, 0.0))

overlay.Save()
stage.GetRootLayer().Save()
~~~

> 실무 원칙: 원본 로봇 Layer에 환경별 위치와 튜닝을 직접 굽지 않는다. 로봇 자산은 Reference하고 환경 또는 실험용 Layer에서 override한다.

### Prim

Prim은 Stage 장면 그래프의 지속적인 객체다. 파일 시스템의 디렉터리처럼 자식 Prim을 가질 수 있지만, 타입과 속성, 관계, 메타데이터도 가진다.

~~~text
/World                       Xform
/World/Robot                 Xform + ArticulationRootAPI
/World/Robot/base_link       Xform + RigidBodyAPI + MassAPI
/World/Robot/base_link/mesh  Mesh + CollisionAPI
/World/Robot/camera          Camera
~~~

Prim 경로는 /로 시작하는 절대 경로다. Prim 이름에는 USD 식별자 규칙이 적용되므로 숫자로 시작하거나 특수 문자를 포함한 URDF 이름은 Importer가 바꿀 수 있다.

Prim Specifier에는 def, over, class가 있다.

- def는 Prim을 정의한다.
- over는 이미 다른 Layer나 Reference에서 정의된 Prim에 override를 더한다.
- class는 주로 inherits에 사용할 추상 Prim을 만든다.

### Property: Attribute와 Relationship

Prim의 Property는 크게 두 종류다.

- Attribute는 숫자, 문자열, 배열, 토큰, 자산 경로 같은 값을 보관하며 시간 샘플을 가질 수 있다.
- Relationship은 다른 Prim이나 Property 경로를 대상으로 가리킨다. 예를 들어 Joint의 body0/body1 관계나 Material Binding에 사용한다.

~~~python
prim = stage.GetPrimAtPath("/World/Robot/base_link")

for attr in prim.GetAttributes():
    print("ATTR", attr.GetName(), attr.Get())

for rel in prim.GetRelationships():
    print("REL", rel.GetName(), rel.GetTargets())
~~~

메타데이터는 Attribute 값과 다르다. active, kind, instanceable, documentation, customData 같은 Prim·Layer의 해석 정보를 기록한다.

## Schema는 Prim에 의미를 부여한다

Schema는 어떤 속성과 관계가 어떤 의미를 가지는지 정의한 계약이다. 단순히 이름이 radius인 Attribute를 만들었다고 Sphere가 되는 것이 아니라 UsdGeomSphere Schema를 통해 표준 의미를 부여한다.

Schema는 두 범주를 구분하면 이해하기 쉽다.

### Typed Schema

Prim이 하나의 주 타입을 가진다. Xform, Mesh, Camera, Sphere, PhysicsScene 등이 예다.

~~~python
from pxr import UsdGeom

mesh_prim = stage.GetPrimAtPath("/World/Table/top")
if mesh_prim.IsA(UsdGeom.Mesh):
    mesh = UsdGeom.Mesh(mesh_prim)
    print(mesh.GetPointsAttr().Get())
~~~

### API Schema

기존 Prim에 행동이나 속성 묶음을 추가한다. 하나의 Mesh Prim에 CollisionAPI와 MassAPI를 적용하는 식으로 여러 의미를 조합할 수 있다.

~~~python
from pxr import UsdPhysics

prim = stage.GetPrimAtPath("/World/Box")
UsdPhysics.RigidBodyAPI.Apply(prim)
UsdPhysics.CollisionAPI.Apply(prim)
mass_api = UsdPhysics.MassAPI.Apply(prim)
mass_api.CreateMassAttr(2.0)
~~~

Isaac Sim에서는 표준 UsdPhysics Schema 외에도 PhysX와 Isaac 전용 Schema를 만난다. 다른 OpenUSD 도구가 Prim 자체는 읽더라도 해당 전용 Schema의 실행 의미를 모를 수 있다.

## Composition: 여러 의견을 하나의 장면으로 합치기

Composition은 여러 Layer의 Prim Spec과 composition arc를 하나의 Stage로 합성하는 과정이다. 주요 arc는 다음과 같다.

| Arc | 핵심 목적 | 로봇 예시 |
|---|---|---|
| Sublayer | 같은 namespace를 가진 Layer를 쌓는다 | base, physics, experiment override를 순서대로 쌓는다 |
| Reference | 외부 자산을 특정 Prim 아래에 조립한다 | `robot.usd`를 `/World/Robot`에 배치한다 |
| Payload | Reference처럼 조립하되 필요할 때만 로드한다 | 대형 공장 구역이나 고해상도 로봇을 지연 로드한다 |
| VariantSet | 이름 있는 대안 중 하나를 선택한다 | `gripper=parallel/suction`, `color=red/blue`를 선택한다 |
| Inherits | class Prim의 opinion을 상속한다 | 여러 자산에 공통 설정을 배포한다 |
| Specializes | 기본 모델을 전문화한 강한 기본값 관계를 만든다 | 자산 템플릿 파이프라인에서 드물게 사용한다 |

Composition은 파일을 복사·붙여넣는 작업이 아니다. Stage는 arc를 유지한 채 계산된 결과를 보여 준다. Flatten하면 계산 결과를 한 Layer에 굽고 많은 arc를 제거하므로 원본 파이프라인의 편집 구조를 잃을 수 있다.

## Reference

Reference는 다른 Layer의 Prim을 현재 namespace에 합성한다. 여러 환경에서 같은 로봇 자산을 중복 저장하지 않고 재사용할 수 있다.

~~~usda
# warehouse.usda
#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World" {
    def Xform "Robot" (
        prepend references = @./assets/mobile_robot.usd@
    ) {
        double3 xformOp:translate = (3, 1, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }
}
~~~

Python에서는 다음처럼 저작한다.

~~~python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("warehouse.usda")
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
world = UsdGeom.Xform.Define(stage, "/World")
robot = UsdGeom.Xform.Define(stage, "/World/Robot")
robot.GetPrim().GetReferences().AddReference("./assets/mobile_robot.usd")
stage.SetDefaultPrim(world.GetPrim())
stage.GetRootLayer().Save()
~~~

Reference 대상 자산에는 defaultPrim을 올바르게 지정하는 것이 좋다. 그렇지 않으면 어떤 Prim을 가져올지 명시해야 한다.

## Payload

Payload는 선택적으로 로드할 수 있는 지연 Reference다. Stage를 열 때 Payload를 로드하지 않으면 장면의 가벼운 인터페이스만 구성하고 무거운 기하와 재질은 생략할 수 있다.

~~~python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("factory.usda")
zone = UsdGeom.Xform.Define(stage, "/World/ZoneA").GetPrim()
zone.GetPayloads().AddPayload("./zones/zone_a.usd")
stage.GetRootLayer().Save()

# Payload를 로드하지 않고 연다.
light_stage = Usd.Stage.Open(
    "factory.usda", load=Usd.Stage.LoadNone
)
light_stage.Load("/World/ZoneA")
light_stage.Unload("/World/ZoneA")
~~~

Reference와 Payload의 데이터 표현 능력이 본질적으로 다른 것은 아니다. 작업 세트를 선택적으로 로드해야 하는지가 선택 기준이다. 로봇 한 대의 필수 충돌·관절 데이터까지 Payload로 숨기면 물리 설정 코드가 해당 Prim을 찾지 못할 수 있으므로 로딩 시점을 명시한다.

## VariantSet

VariantSet은 같은 자산에 여러 대안을 보관하고 선택을 기록한다. 파일을 robot_red.usd, robot_blue.usd처럼 복제하는 대신 하나의 자산에 color Variant를 만들 수 있다.

~~~python
from pxr import Gf, Usd, UsdGeom

stage = Usd.Stage.CreateNew("variant_robot.usda")
robot = UsdGeom.Xform.Define(stage, "/Robot").GetPrim()
body = UsdGeom.Cube.Define(stage, "/Robot/Body")

variants = robot.GetVariantSets().AddVariantSet("color")
for name, rgb in {
    "red": Gf.Vec3f(0.8, 0.1, 0.1),
    "blue": Gf.Vec3f(0.1, 0.2, 0.8),
}.items():
    variants.AddVariant(name)
    variants.SetVariantSelection(name)
    with variants.GetVariantEditContext():
        body.CreateDisplayColorAttr([rgb])

variants.SetVariantSelection("blue")
stage.GetRootLayer().Save()
~~~

Variant는 단순 가시성 토글보다 강력하다. 각 Variant 내부에서 Reference, 재질, Prim, 속성 값을 다르게 저작할 수 있다. 다만 가능한 Variant 조합이 폭발적으로 늘어날 수 있으므로 독립적인 선택 축만 별도 VariantSet으로 만든다.

## Xform과 좌표 변환

UsdGeomXformable은 이동, 회전, 스케일, 행렬 연산을 독립 Attribute로 표현하고 xformOpOrder가 적용 순서를 정한다. 단일 translate/rotate/scale 값으로 단정하면 안 된다.

~~~python
from pxr import Gf, UsdGeom

xform = UsdGeom.Xform.Define(stage, "/World/SensorMount")
xform.AddTranslateOp().Set(Gf.Vec3d(0.30, 0.0, 1.20))
xform.AddRotateXYZOp().Set(Gf.Vec3f(0.0, -15.0, 90.0))
xform.AddScaleOp().Set(Gf.Vec3f(1.0, 1.0, 1.0))

cache = UsdGeom.XformCache()
world_matrix = cache.GetLocalToWorldTransform(xform.GetPrim())
print(world_matrix)
~~~

주의할 점은 다음과 같다.

- USD 회전 값은 기본적으로 degree를 사용한다. ROS와 물리 계산의 radian과 혼동하지 않는다.
- Stage 메타데이터 metersPerUnit와 upAxis를 확인한다. Isaac Sim의 기본은 meter와 Z-up이다.
- 부모와 자식의 변환이 합성된다. 센서의 world pose만 보고 local pose를 잘못 수정하지 않는다.
- xformOpOrder에 없는 xformOp Attribute는 적용되지 않는다.
- resetXformStack가 설정되면 조상 변환의 상속을 끊는다.

## Instancing

Instancing은 동일한 구성의 중복 메모리와 처리 비용을 줄인다. 로봇 학습 환경이나 반복되는 창고 랙에 특히 중요하다.

### Native Instancing

같은 Reference를 가진 Prim을 instanceable로 표시하면 USD가 공통 Prototype을 공유한다.

~~~python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("fleet.usda")
UsdGeom.Xform.Define(stage, "/World")

for index in range(4):
    prim = UsdGeom.Xform.Define(stage, f"/World/Robot_{index}").GetPrim()
    prim.GetReferences().AddReference("./robot.usd")
    prim.SetInstanceable(True)

stage.GetRootLayer().Save()
~~~

Instance Proxy 내부에는 일반적인 방식으로 개별 opinion을 저작할 수 없다. 인스턴스별 색상이나 센서 구성이 필요하면 인스턴스 루트 바깥에 데이터를 두거나 Variant/primvar/비인스턴스 구조를 설계한다.

### PointInstancer

UsdGeomPointInstancer는 매우 많은 단순 Prototype을 position, orientation, scale 배열로 배치한다. 볼트, 상자, 식생처럼 수가 많은 기하에 적합하지만 독립 Articulation 로봇의 일반적인 대체 수단은 아니다.

### Isaac Sim의 Instanceable Asset

Isaac Sim 로봇 자산은 visual과 collision mesh를 별도 파일로 분리해 instanceable하게 만드는 구조를 자주 사용한다. 편집하려면 인스턴스 가능 상태를 임시 해제해야 하는 도구도 있다. 성능을 위해 무조건 켜기 전에 편집 가능성, 센서 경로, 물리 복제 방식을 함께 검증한다.

## USD와 URDF·Xacro·MJCF 비교

| 관점 | USD | URDF | Xacro | MJCF |
|---|---|---|---|---|
| 주 목적 | 일반 3D 장면의 비파괴 합성·교환 | ROS 로봇의 링크·조인트·기하 기술 | 매크로로 URDF XML을 생성 | MuJoCo 모델과 시뮬레이션 설정 기술 |
| 범위 | 로봇, 환경, 조명, 재질, 애니메이션, 물리, 센서 | 주로 로봇 한 대의 트리 | 최종 결과는 URDF 범위 | 로봇·환경·접촉·액추에이터·센서 |
| 구조 | 임의의 Prim 계층과 composition arc | 단일 루트의 Link/Joint 트리 | include, macro, property, 조건식 | body 트리와 asset/default/tendon/actuator 등 |
| 비파괴 합성 | Layer, Reference, Payload, Variant, Inherits | 없음 | 소스 생성 단계의 include·macro | include와 default class가 있으나 USD composition과 다름 |
| 시간 샘플 | 표준 기능 | 없음 | 없음 | 실행 상태는 모델 XML과 별도 |
| 렌더링 표현 | 고급 재질·조명·카메라·대형 장면 | visual geometry와 단순 material | URDF와 같음 | geom, material, texture 등 MuJoCo 중심 |
| 물리 표현 | UsdPhysics와 벤더 Schema로 확장 | inertial, collision, joint limit 등 제한된 공통 부분 | URDF와 같음 | tendon, actuator, equality, contact 등 MuJoCo 고유 기능이 풍부함 |
| 코드 API | OpenUSD C++와 pxr Python | urdfdom 등 파서 | xacro 프로세서가 URDF 생성 | MuJoCo C/C++와 Python API |
| Isaac Sim 5.1 | 기본 장면 형식 | 공식 Importer와 Preview Exporter | 먼저 URDF로 펼치거나 ROS 2 노드에서 간접 import | 공식 Importer 제공, 공식 Exporter 없음 |

### URDF

URDF는 XML로 로봇의 링크와 조인트, visual, collision, inertial을 기술한다. ROS의 robot_state_publisher, RViz, MoveIt 등과 교환하기 좋다. 그러나 일반 URDF는 닫힌 루프, 여러 부모를 가진 링크, 풍부한 장면 구성, USD Layer 같은 비파괴 합성을 직접 표현하지 못한다.

~~~xml
<robot name="two_link">
  <link name="base_link"/>
  <link name="arm_link">
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.01" ixy="0" ixz="0"
               iyy="0.01" iyz="0" izz="0.01"/>
    </inertial>
  </link>
  <joint name="shoulder" type="revolute">
    <parent link="base_link"/>
    <child link="arm_link"/>
    <axis xyz="0 0 1"/>
    <limit lower="-1.57" upper="1.57" effort="20" velocity="2"/>
  </joint>
</robot>
~~~

### Xacro

Xacro는 독립적인 런타임 로봇 포맷이 아니라 URDF/XML 생성기다. macro, property, 수식, 조건, include로 반복을 줄이고 최종적으로 URDF XML을 출력한다.

~~~xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="demo">
  <xacro:property name="wheel_radius" value="0.08"/>
  <xacro:macro name="wheel" params="side y">
    <link name="${side}_wheel">
      <visual>
        <geometry><cylinder radius="${wheel_radius}" length="0.03"/></geometry>
      </visual>
    </link>
  </xacro:macro>
  <xacro:wheel side="left" y="0.15"/>
</robot>
~~~

USD에서 URDF를 만들 수 있어도 원래의 macro 이름, 수식, include 경계는 이미 펼쳐진 결과에 존재하지 않는다. 그러므로 USD→Xacro 자동 역변환을 기대하면 안 된다.

### MJCF

MJCF는 MuJoCo Modeling XML File이다. MuJoCo 컴파일러가 실행용 mjModel로 만드는 고수준 모델 설명이며, default class, actuator, tendon, equality constraint, contact 설정, sensor, site 등 MuJoCo의 기능을 풍부하게 표현한다.

~~~xml
<mujoco model="pendulum">
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <default>
    <joint damping="0.1"/>
    <geom density="500" friction="0.8 0.1 0.01"/>
  </default>
  <worldbody>
    <body name="link" pos="0 0 1">
      <joint name="hinge" type="hinge" axis="0 1 0"/>
      <geom type="capsule" fromto="0 0 0 0 0 -0.5" size="0.04"/>
      <site name="tip" pos="0 0 -0.5"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="motor" joint="hinge" gear="10"/>
  </actuator>
</mujoco>
~~~

Isaac Sim Importer가 MJCF를 USD/PhysX 구조로 매핑할 때 MuJoCo 전용 Solver·Actuator·Tendon 의미가 일대일로 보존된다고 가정하면 안 된다. 변환 뒤에는 질량, 관성, 축, 제한, 구동, 충돌을 다시 검증한다.

## 어떤 포맷을 기준 원본으로 둘 것인가

### ROS 중심 로봇 패키지

Xacro를 사람이 편집하는 기준 원본으로 두고 CI에서 URDF를 생성·검증한 뒤 Isaac Sim용 USD를 생성한다. Isaac Sim에서 추가한 재질, 센서, 물리 튜닝은 별도 USD Layer에 보관한다.

### Isaac Sim 중심 디지털 트윈

모듈형 USD 자산을 기준 원본으로 두고 ROS 도구가 요구할 때만 USD→URDF Exporter를 사용한다. Exporter가 지원하지 않는 USD 기능은 별도 ROS 설정 파일이나 수작업 패치로 관리한다.

### MuJoCo 연구 자산

MJCF를 기준 원본으로 유지하고 Isaac Sim 검증용 USD를 생성한다. 양쪽 엔진의 접촉과 액추에이터 모델이 다르므로 수치적으로 같은 결과를 약속하지 않는다.

### 피해야 할 흐름

URDF→USD→URDF→USD를 반복하며 매번 새 결과를 기준 원본으로 삼지 않는다. 각 변환은 표현력이 다른 데이터 모델 사이의 매핑이며 이름, 계층, 재질, 충돌, 관성, 전용 기능이 달라질 수 있다.

## 다음 장을 위한 체크리스트

- Stage와 Layer를 같은 것으로 설명하지 않는다.
- 현재 Edit Target을 확인하고 수정한다.
- Reference는 재사용, Payload는 선택적 로딩이라는 기준으로 선택한다.
- Variant는 복제 파일을 줄이지만 조합 수를 관리한다.
- Xform의 op 순서, 단위, up axis를 확인한다.
- Instancing은 성능과 편집 가능성의 절충이다.
- URDF/Xacro/MJCF와 USD 사이의 변환은 일반적으로 무손실 왕복이 아니다.

## 출처

- [NVIDIA Isaac Sim 5.1 — OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html)
- [NVIDIA Isaac Sim 5.1 — Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html)
- [OpenUSD — Introduction to USD](https://openusd.org/release/intro.html)
- [OpenUSD — USD Terms and Concepts](https://openusd.org/release/glossary.html)
- [OpenUSD — Referencing Layers](https://openusd.org/release/tut_referencing_layers.html)
- [OpenUSD — Transformations, Animation, and Layer Offsets](https://openusd.org/release/tut_xforms.html)
- [OpenUSD — Scenegraph Instancing](https://openusd.org/release/api/_usd__page__scenegraph_instancing.html)
- [OpenUSD — UsdGeomXformable](https://openusd.org/release/api/class_usd_geom_xformable.html)
- [OpenUSD — USDZ File Format Specification](https://openusd.org/release/spec_usdz.html)
- [ROS 2 Jazzy — URDF](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html)
- [ROS 2 Jazzy — Using Xacro to Clean Up a URDF File](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Using-Xacro-to-Clean-Up-a-URDF-File.html)
- [MuJoCo — Modeling](https://mujoco.readthedocs.io/en/stable/modeling.html)
- [MuJoCo — XML Reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
