# USD 도구와 pxr 프로그래밍

이 장에서는 USD 파일을 명령행에서 검사하고, Python과 C++로 생성·수정·분석하는 방법을 익힌다. 예제는 OpenUSD 자체와 Isaac Sim 5.1의 Kit 런타임을 구분한다.

## 실행 환경을 먼저 구분한다

USD 코드를 실행하는 환경은 크게 세 가지다.

| 환경 | 사용 가능한 것 | 적합한 작업 |
|---|---|---|
| 독립 OpenUSD 설치 | pxr과 `usdcat`·`usdview` 등 빌드에 포함한 도구 | 파일 검사, 변환, 범용 USD 파이프라인 |
| Isaac Sim Script Editor·Extension | pxr, omni.*, Isaac Sim Extension과 현재 GUI Stage | 대화형 장면 편집, 메뉴·센서·물리 기능 호출 |
| Isaac Sim 독립 Python | pxr, omni.*, Isaac Sim API. SimulationApp 초기화 필요 | Headless 배치, 자동화, 데이터 생성 |

Isaac Sim의 Python이 아닌 일반 시스템 Python에서 `omni` 모듈을 import하면 실패하는 것이 정상이다. 반대로 순수 pxr 코드에 GUI가 필요 없다면 Kit를 띄우지 않는 편이 더 빠르고 단순하다.

Isaac Sim 압축 패키지 설치에서는 일반적으로 설치 루트의 python.sh로 스크립트를 실행한다.

~~~bash
cd /path/to/isaac-sim
./python.sh /absolute/path/to/script.py
~~~

Pip 설치를 사용한다면 Isaac Sim을 설치한 동일한 가상환경의 python을 사용한다. 정확한 실행 방법은 설치 방식별 5.1 문서를 따른다.

## 버전을 기록한다

Isaac Sim 5.1은 Kit 107.3.3 계열을 사용한다. 인터넷의 최신 OpenUSD 예제가 설치본의 API와 다를 수 있으므로 버전과 명령 도움말을 먼저 기록한다.

~~~python
from pxr import Usd

print("OpenUSD:", Usd.GetVersion())
~~~

~~~bash
usdcat --help
usdview --help
usdchecker --help
~~~

이 장의 옵션은 OpenUSD 공식 Toolset을 기준으로 한다. Isaac Sim 또는 별도 OpenUSD 빌드에 포함된 도구의 실제 플래그가 다르면 설치본의 --help가 우선한다.

## 주요 명령행 도구 한눈에 보기

| 도구 | 목적 | 자주 쓰는 예 |
|---|---|---|
| usdcat | 내용을 텍스트로 출력하고 인코딩·flatten 결과를 저장한다 | usdc→usda, Stage flatten |
| usdview | Hydra 뷰포트와 장면 그래프로 대화형 검사한다 | Prim 선택, Payload 미로딩 검사 |
| usdchecker | USD·USDZ 규칙과 교환 적합성을 검증한다 | CI 유효성 검사 |
| usddiff | 두 USD-readable 파일을 텍스트화해 비교한다 | 변경 전후, 합성 결과 비교 |
| usdtree | Prim 트리를 터미널에 표시한다 | Headless 구조 확인 |
| usdresolve | Asset Resolver가 경로를 어떻게 해석하는지 확인한다 | Reference·Texture 경로 진단 |
| usdzip | USDZ를 생성하고 목록·내용을 검사한다 | 의존 자산 패키징 |
| usdedit | 바이너리 USD도 임시 USDA로 열어 편집한다 | 작은 긴급 수정. 원본 덮어쓰기 주의 |

## usdcat

### 내용을 읽는다

~~~bash
usdcat robot.usd
usdcat robot.usd | less

# 파일이 로드 가능한지만 빠르게 확인한다.
usdcat -l robot.usd
~~~

.usdc나 바이너리 .usd를 strings나 일반 텍스트 편집기로 검사하지 않는다. usdcat은 플러그인과 파일 형식을 통해 올바르게 역직렬화한다.

### USDA와 USDC를 변환한다

~~~bash
usdcat robot.usda -o robot.usdc
usdcat robot.usdc -o robot.usda

# .usd 확장자의 내부 인코딩을 명시한다.
usdcat robot.usda -o robot_binary.usd --usdFormat usdc
usdcat robot_binary.usd -o robot_text.usd --usdFormat usda
~~~

변환 전후의 USD 의미가 같은지 확인한다.

~~~bash
usddiff robot.usda robot.usdc
~~~

### Flatten의 차이를 이해한다

~~~bash
# Reference, Payload, Variant 등 모든 composition 결과를 굽는다.
usdcat root.usd --flatten -o flattened.usda

# Sublayer stack만 합치고 Reference 같은 arc는 보존한다.
usdcat root.usd --flattenLayerStack -o layer_stack.usda
~~~

--flatten은 배포용 스냅샷과 디버깅에는 유용하지만 원래의 composition arc, Variant 선택 구조, Layer 편집 경계를 잃게 한다. 원본 자산을 flattened 파일로 덮어쓰지 않는다.

여러 입력 파일을 usdcat에 전달해도 하나로 merge되지 않는다. 각 파일의 텍스트가 순서대로 출력될 뿐이다. 시간 샘플을 합치는 usdstitch나 Layer 설계를 별도로 검토한다.

## usdview

usdview는 Hydra 기반 대화형 뷰어이자 scenegraph 검사기다. Prim, Property, Layer, composition 정보를 살피고 내장 Python interpreter도 사용할 수 있다.

~~~bash
usdview warehouse.usd
usdview warehouse.usd --select /World/Robot
usdview warehouse.usd --unloaded
usdview warehouse.usd --mask /World/Robot
~~~

--unloaded는 Payload를 불러오지 않은 상태를 검사할 때 유용하다. --mask는 지정 Prim과 조상·자손만 population해 대형 장면의 문제 범위를 줄인다.

다음 항목을 확인한다.

1. 예상한 defaultPrim과 Prim 경로가 있는가?
2. Payload를 로드하지 않아도 자산 인터페이스가 보이는가?
3. 선택한 Attribute의 값이 어느 Layer에서 왔는가?
4. Xform stack과 world transform이 예상과 같은가?
5. Reference와 Texture의 resolved path가 유효한가?

usdview는 범용 OpenUSD 뷰어이므로 Isaac Sim의 RTX, MDL, PhysX 전용 기능이 동일하게 보이거나 실행된다고 가정하지 않는다. 로보틱스 실행 검증은 Isaac Sim에서도 다시 한다.

## usdchecker

usdchecker는 USD Stage 또는 USDZ 패키지를 규칙과 메트릭으로 검증한다.

~~~bash
usdchecker robot.usd
usdchecker -v robot.usd

# warning도 실패 코드로 처리해 CI를 엄격하게 만든다.
usdchecker -t robot.usd

# 현재 선택된 Variant만 검사해 시간을 줄인다.
usdchecker -s robot.usd

# 사용 가능한 규칙을 확인한다.
usdchecker -d robot.usd
~~~

기본 동작은 가능한 Variant 조합까지 검사할 수 있다. VariantSet이 많으면 검사 시간이 크게 늘 수 있다. -s로 줄였다면 CI에서 전체 조합을 검사하는 별도 작업을 두는 것이 좋다.

usdchecker 통과는 Isaac Sim 물리가 안정적이라는 뜻이 아니다. 이것은 USD 교환·렌더링 적합성 검사이며, Articulation, 관성, 접촉 안정성은 별도 시뮬레이션 테스트가 필요하다.

## usddiff

usddiff는 각 입력을 usdcat으로 텍스트화한 뒤 외부 diff 프로그램으로 비교한다.

~~~bash
usddiff before.usd after.usd
usddiff -q before.usd after.usd

# 두 파일을 각각 합성·flatten한 결과로 비교한다.
usddiff -f before.usd after.usd
~~~

기본 비교와 -f 비교는 질문이 다르다.

- 기본 비교는 Layer에 실제로 저작된 구조의 차이를 찾는다.
- -f 비교는 composition을 평가한 최종 장면의 차이를 찾는다.

usddiff는 부동소수점 허용오차를 적용하지 않는다. 1.0과 1.0000001도 차이로 보고한다. 물리 수치 회귀 테스트는 pxr로 값을 읽어 numpy tolerance를 적용하는 별도 테스트를 작성한다.

~~~python
import numpy as np
from pxr import Usd

def read_mass(path):
    stage = Usd.Stage.Open(path)
    attr = stage.GetPrimAtPath("/Robot/base_link").GetAttribute("physics:mass")
    return float(attr.Get())

assert np.isclose(read_mass("a.usd"), read_mass("b.usd"), rtol=1e-6)
~~~

## usdtree와 usdresolve

GUI가 없는 서버에서는 usdtree로 구조를 빠르게 확인한다.

~~~bash
usdtree robot.usd
usdtree -a -m robot.usd
usdtree --unloaded robot.usd
usdtree --flatten robot.usd
~~~

경로 문제는 usdresolve로 Asset Resolver 관점에서 확인한다.

~~~bash
usdresolve ./assets/robot.usd
usdresolve --anchorPath /project/scenes/world.usd ../assets/robot.usd
~~~

셸의 realpath가 성공해도 USD의 Resolver context나 Nucleus URI가 다르면 결과가 달라질 수 있다. Reference를 저작한 Layer의 위치를 anchor로 생각한다.

## usdzip

명시한 파일을 USDZ로 묶는다.

~~~bash
usdzip package.usdz root.usda textures/albedo.png meshes/body.usdc
~~~

Root Layer가 참조하는 의존 자산을 수집하고 compliance도 검사하려면 --asset과 -c를 사용한다.

~~~bash
usdzip package.usdz --asset root.usd -c

# 패키지 목록과 내용을 검사한다.
usdzip -l - package.usdz
usdzip -d - package.usdz
usdchecker -t package.usdz
~~~

USDZ는 일반적으로 읽기 전용 배포물이다. 수정하려면 풀어서 원본 USD와 자산을 고친 뒤 다시 패키징한다. 단순 zip 명령으로 만들면 USDZ의 정렬 규칙을 만족하지 않을 수 있으므로 usdzip을 사용한다.

## 반복 가능한 CLI 검증 흐름

~~~bash
set -euo pipefail

ASSET="${1:?usage: validate_usd.sh ASSET.usd}"

usdcat -l "$ASSET"
usdchecker -t "$ASSET"
usdtree --unloaded "$ASSET" > "${ASSET}.tree.txt"
usdcat "$ASSET" --flatten -o "${ASSET}.flattened.usda"
~~~

Flatten 파일은 검사용 산출물로만 사용하고 소스 관리 대상에서 제외하는 편이 좋다.

## pxr 모듈 지도

OpenUSD 배포판과 pxr을 혼동하지 않는다. OpenUSD는 라이브러리·도구·플러그인 전체이고 pxr은 C++ namespace 및 Python import 최상위 이름이다.

| 모듈 | 역할 | 대표 타입 |
|---|---|---|
| Usd | 합성된 Stage와 Prim, Property, EditTarget | Usd.Stage, Usd.Prim, Usd.EditContext |
| Sdf | Layer와 Path, 저수준 Spec, ValueType | Sdf.Layer, Sdf.Path, Sdf.PrimSpec |
| UsdGeom | 기하, Xform, Camera, 공간 계산 | UsdGeom.Mesh, Xformable, XformCache |
| Gf | 벡터, 행렬, quaternion, 범위 수학 | Gf.Vec3d, Gf.Quatd, Gf.Matrix4d |
| Vt | USD 값과 타입 배열 | Vt.Vec3fArray, Vt.IntArray |
| Tf | Token, 타입, 진단, Notice 기반 시설 | Tf.Token 관련 기능 |
| Ar | Asset Resolution | Ar.Resolver |
| UsdShade | Material과 Shader graph | UsdShade.Material, Shader |
| UsdLux | Light Schema | DistantLight, DomeLight |
| UsdPhysics | 표준 물리 Schema | RigidBodyAPI, CollisionAPI, Joint |
| UsdSkel | Skeleton·Skinning | Skeleton, Animation |
| UsdUtils | 의존성, 패키징, Stage 유틸리티 | StageCache, dependency utilities |

PhysxSchema는 OpenUSD 코어가 아니라 NVIDIA가 제공하는 PhysX 확장 Schema다. 순수 OpenUSD만 설치한 환경에서 import되지 않을 수 있다.

## 실습 1: Stage 생성과 검사

다음 파일을 create_scene.py로 저장하고 OpenUSD Python 또는 Isaac Sim Python에서 실행한다.

~~~python
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

OUTPUT = "scene.usda"

stage = Usd.Stage.CreateNew(OUTPUT)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
stage.SetStartTimeCode(0)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(60)

world = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
stage.SetDefaultPrim(world.GetPrim())

cube = UsdGeom.Cube.Define(stage, Sdf.Path("/World/Cube"))
cube.CreateSizeAttr(0.20)
cube.CreateDisplayColorAttr([Gf.Vec3f(0.1, 0.5, 0.9)])

xformable = UsdGeom.Xformable(cube.GetPrim())
translate = xformable.AddTranslateOp()
translate.Set(Gf.Vec3d(0.0, 0.0, 0.10))

UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1.5)

for prim in stage.Traverse():
    print(prim.GetPath(), prim.GetTypeName(), prim.GetAppliedSchemas())

stage.GetRootLayer().Save()
print("saved:", stage.GetRootLayer().realPath)
~~~

~~~bash
python create_scene.py
usdcat scene.usda
usdchecker scene.usda
usdview scene.usda
~~~

Isaac Sim에서 실행할 때는 다음처럼 현재 Stage를 얻을 수도 있다.

~~~python
import omni.usd

stage = omni.usd.get_context().get_stage()
print(stage.GetRootLayer().identifier)
~~~

현재 GUI Stage를 새 파일로 여는 코드와 Usd.Stage.Open으로 별도 Stage를 여는 코드를 섞지 않는다.

## 실습 2: 조회와 안전한 타입 처리

~~~python
from pxr import Usd, UsdGeom, UsdPhysics

stage = Usd.Stage.Open("scene.usda")

for prim in stage.Traverse():
    path = prim.GetPath()

    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
        print("mesh", path, "points", len(mesh.GetPointsAttr().Get() or []))

    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        rigid = UsdPhysics.RigidBodyAPI(prim)
        enabled = rigid.GetRigidBodyEnabledAttr().Get()
        print("rigid", path, "enabled", enabled)

    if prim.IsA(UsdGeom.Xformable):
        xformable = UsdGeom.Xformable(prim)
        print("xform ops", path, [op.GetOpName() for op in xformable.GetOrderedXformOps()])
~~~

GetPrimAtPath가 반환한 Prim이 유효한지 항상 확인한다.

~~~python
prim = stage.GetPrimAtPath("/World/Missing")
if not prim.IsValid():
    raise KeyError("Prim not found: /World/Missing")
~~~

## 실습 3: Layer와 Edit Target

~~~python
from pxr import Gf, Sdf, Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")
root = stage.GetRootLayer()
session = stage.GetSessionLayer()
overlay = Sdf.Layer.CreateNew("scene_override.usda")

# Sublayer 목록의 앞쪽에 추가해 기존 Sublayer보다 강하게 둔다.
root.subLayerPaths.insert(0, overlay.identifier)

with Usd.EditContext(stage, overlay):
    cube = UsdGeom.Xformable.Get(stage, "/World/Cube")
    cube.AddTranslateOp(opSuffix="experiment").Set(Gf.Vec3d(1.0, 0.0, 0.0))

print("edit target:", stage.GetEditTarget().GetLayer().identifier)
print("root:", root.identifier)
print("session:", session.identifier)
print("used layers:")
for layer in stage.GetUsedLayers():
    print(" -", layer.identifier)

overlay.Save()
root.Save()
~~~

Layer가 저장되었어도 Root Layer의 subLayerPaths 변경을 저장하지 않으면 다음 실행에서 연결이 사라진다.

## 실습 4: Reference, Payload, Variant

먼저 재사용할 로봇 대체 자산을 만든다.

~~~python
from pxr import Gf, Usd, UsdGeom

asset = Usd.Stage.CreateNew("robot_asset.usda")
robot = UsdGeom.Xform.Define(asset, "/Robot")
asset.SetDefaultPrim(robot.GetPrim())
body = UsdGeom.Cube.Define(asset, "/Robot/Body")
body.CreateSizeAttr(0.4)
body.CreateDisplayColorAttr([Gf.Vec3f(0.3, 0.3, 0.3)])
asset.GetRootLayer().Save()
~~~

Reference와 Payload, Variant를 저작한다.

~~~python
from pxr import Gf, Usd, UsdGeom

stage = Usd.Stage.CreateNew("composed_scene.usda")
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

robot = UsdGeom.Xform.Define(stage, "/World/Robot").GetPrim()
robot.GetReferences().AddReference("./robot_asset.usda")

heavy = UsdGeom.Xform.Define(stage, "/World/HeavyZone").GetPrim()
heavy.GetPayloads().AddPayload("./heavy_zone.usd")

tool_set = robot.GetVariantSets().AddVariantSet("tool")
for name, length in {"short": 0.15, "long": 0.35}.items():
    tool_set.AddVariant(name)
    tool_set.SetVariantSelection(name)
    with tool_set.GetVariantEditContext():
        tool = UsdGeom.Cube.Define(stage, "/World/Robot/Tool")
        tool.CreateSizeAttr(length)
        tool.AddTranslateOp().Set(Gf.Vec3d(0.4, 0.0, 0.0))

tool_set.SetVariantSelection("short")
stage.GetRootLayer().Save()
~~~

Payload를 제외하고 열어 working set을 제어한다.

~~~python
from pxr import Usd

stage = Usd.Stage.Open("composed_scene.usda", load=Usd.Stage.LoadNone)
print("loaded:", stage.GetLoadSet())

stage.Load("/World/HeavyZone")
stage.Unload("/World/HeavyZone")
~~~

heavy_zone.usd가 아직 없으면 Load할 때 오류가 나는 것이 정상이다. 이 실습은 Payload arc 자체와 대상 로드 실패를 구분하는 연습이다.

## 실습 5: Instancing과 XformCache

~~~python
from pxr import Gf, Usd, UsdGeom

stage = Usd.Stage.CreateNew("fleet.usda")
UsdGeom.Xform.Define(stage, "/World")

for index in range(100):
    xform = UsdGeom.Xform.Define(stage, f"/World/Robot_{index}")
    xform.GetPrim().GetReferences().AddReference("./robot_asset.usda")
    xform.GetPrim().SetInstanceable(True)
    xform.AddTranslateOp().Set(Gf.Vec3d(index % 10, index // 10, 0.0))

cache = UsdGeom.XformCache(Usd.TimeCode.Default())
for index in (0, 9, 99):
    prim = stage.GetPrimAtPath(f"/World/Robot_{index}")
    matrix = cache.GetLocalToWorldTransform(prim)
    print(index, matrix.ExtractTranslation())

stage.GetRootLayer().Save()
~~~

반복문 안에서 매번 새 XformCache를 만들지 않는다. 시간 코드가 바뀌면 cache.SetTime()을 호출하거나 새 cache를 구성한다.

## 시간 샘플을 저작한다

~~~python
from pxr import Gf, Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")
cube = UsdGeom.Xformable.Get(stage, "/World/Cube")
op = cube.AddRotateZOp(opSuffix="spin")

for frame in range(0, 121):
    op.Set(frame * 3.0, Usd.TimeCode(frame))

stage.SetStartTimeCode(0)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(60)
stage.GetRootLayer().Save()
~~~

USD의 timeCode는 반드시 초와 같지 않다. timeCodesPerSecond 메타데이터로 시간 축의 의미를 정한다. Isaac Sim의 물리 시뮬레이션 상태를 매 프레임 USD에 저작하면 성능이 크게 저하될 수 있으므로 기록 목적과 빈도를 설계한다.

## C++ 최소 예제

Python과 C++ API는 이름이 거의 일대일로 대응한다.

| Python | C++ |
|---|---|
| pxr.Usd.Stage | pxr::UsdStage |
| pxr.Sdf.Layer | pxr::SdfLayer |
| pxr.Usd.Prim | pxr::UsdPrim |
| pxr.UsdGeom.Xformable | pxr::UsdGeomXformable |
| pxr.Gf.Vec3d | pxr::GfVec3d |

~~~cpp
#include "pxr/base/gf/vec3d.h"
#include "pxr/base/vt/value.h"
#include "pxr/usd/sdf/path.h"
#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usdGeom/cube.h"
#include "pxr/usd/usdGeom/xform.h"
#include "pxr/usd/usdGeom/xformable.h"

PXR_NAMESPACE_USING_DIRECTIVE

int main() {
    UsdStageRefPtr stage = UsdStage::CreateNew("scene_cpp.usda");
    if (!stage) {
        return 1;
    }

    UsdGeomXform world = UsdGeomXform::Define(stage, SdfPath("/World"));
    stage->SetDefaultPrim(world.GetPrim());

    UsdGeomCube cube = UsdGeomCube::Define(stage, SdfPath("/World/Cube"));
    cube.CreateSizeAttr(VtValue(0.2));
    UsdGeomXformable(cube.GetPrim())
        .AddTranslateOp()
        .Set(GfVec3d(0.0, 0.0, 0.1));

    return stage->GetRootLayer()->Save() ? 0 : 2;
}
~~~

OpenUSD 빌드 방식에 따라 CMake export와 library 이름이 달라질 수 있다. 일반적인 shared-library 빌드 예시는 다음과 같지만 설치본의 pxrConfig.cmake를 확인한다.

~~~cmake
cmake_minimum_required(VERSION 3.20)
project(usd_minimum LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
find_package(pxr REQUIRED CONFIG)

add_executable(usd_minimum main.cpp)
target_include_directories(usd_minimum PRIVATE ${PXR_INCLUDE_DIRS})
target_link_libraries(usd_minimum PRIVATE usd usdGeom sdf gf vt tf)
~~~

~~~bash
cmake -S . -B build -DCMAKE_PREFIX_PATH=/opt/openusd
cmake --build build -j
./build/usd_minimum
~~~

Isaac Sim Extension용 C++ 플러그인은 독립 OpenUSD 앱과 빌드·ABI 조건이 다르다. Isaac Sim에 임의 버전의 OpenUSD shared library를 함께 로드하지 말고, Kit Extension 템플릿과 Isaac Sim에 맞는 SDK를 사용한다.

## 자주 발생하는 문제

### ModuleNotFoundError: No module named pxr

OpenUSD Python 바인딩이 현재 interpreter에 설치·노출되지 않은 것이다. Isaac Sim 작업이면 python.sh 또는 같은 pip 가상환경을 사용한다. 독립 OpenUSD 빌드라면 Python 지원을 켰는지와 PYTHONPATH를 확인한다.

### ModuleNotFoundError: No module named omni

일반 OpenUSD Python에서 Kit 전용 모듈을 호출한 것이다. Isaac Sim Python으로 실행하고 독립 스크립트라면 SimulationApp을 다른 omni import보다 먼저 초기화한다.

~~~python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import omni.usd
from pxr import UsdGeom

# 작업을 수행한다.

simulation_app.close()
~~~

### 파일은 열리지만 Reference가 비어 있다

- Reference 경로가 이를 저작한 Layer 기준으로 해석되는지 확인한다.
- 대상 자산의 defaultPrim을 확인한다.
- usdresolve와 usdview composition 정보를 사용한다.
- Nucleus URI라면 연결과 인증을 확인한다.

### 수정한 값이 저장되지 않는다

- 현재 Edit Target이 Session Layer인지 확인한다.
- 실제 변경된 Layer에 Save를 호출한다.
- 익명 Layer라면 Export하거나 파일 기반 Layer로 옮긴다.
- instance proxy 내부에 저작하려고 하지 않았는지 확인한다.

### usdchecker는 통과하지만 Isaac Sim에서 이상하다

USD 문법·교환 검증과 PhysX 물리 검증은 다르다. Stage 단위, up axis, CollisionAPI, RigidBodyAPI, MassAPI, Articulation root, Joint body 관계를 Isaac Sim에서 확인한다.

## 권장 CI 단계

1. 모든 소스 USD에 usdcat -l을 실행한다.
2. usdchecker -t를 실행한다.
3. 허용한 Reference·Texture 루트 밖으로 나가는 경로를 pxr로 검사한다.
4. 핵심 Prim 경로와 Schema를 pxr 단위 테스트로 검사한다.
5. 이전 기준 자산과 usddiff를 실행한다.
6. Isaac Sim Headless로 Stage를 열고 몇 초간 물리를 실행한다.
7. 센서와 ROS 인터페이스가 필요하면 예상 토픽과 데이터 shape를 검사한다.

## 출처

- [OpenUSD — USD Toolset](https://openusd.org/release/toolset.html)
- [OpenUSD — Converting Between Layer Formats](https://openusd.org/release/tut_converting_between_layer_formats.html)
- [OpenUSD — Hello World: Creating Your First USD Stage](https://openusd.org/release/tut_helloworld.html)
- [OpenUSD — USD Tutorials](https://openusd.org/release/tut_usd_tutorials.html)
- [OpenUSD — C++ API Reference](https://openusd.org/release/api/index.html)
- [OpenUSD — UsdStage API](https://openusd.org/release/api/class_usd_stage.html)
- [OpenUSD — SdfLayer API](https://openusd.org/release/api/class_sdf_layer.html)
- [OpenUSD — UsdGeomXformable API](https://openusd.org/release/api/class_usd_geom_xformable.html)
- [NVIDIA Isaac Sim 5.1 — OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html)
- [NVIDIA Isaac Sim 5.1 — USD Tools](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/usd_tools.html)
- [NVIDIA Isaac Sim 5.1 — Standalone Python](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [NVIDIA Isaac Sim 5.1 — Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- [NVIDIA Isaac Sim 5.1 — Release Notes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)
- [NVIDIA Kit 107.3.1 — pxr USD Python API](https://docs.omniverse.nvidia.com/kit/docs/pxr-usd-api/107.3.1/index.html)
