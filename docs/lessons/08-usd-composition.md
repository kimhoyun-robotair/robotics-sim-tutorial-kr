# 08. USD 레이어·참조와 URDF·Xacro·MJCF를 구분하다

## 목표와 준비

USD가 단순한 3D 메시 파일보다 많은 정보를 저장한다는 점을 이해하고, 하나의 상자 자산을 두 곳에서 참조한다. 로봇 파일 변환에서 유지되는 정보와 별도 검증이 필요한 정보를 구분한다.

07단계의 장면은 필요하면 다른 이름으로 저장한다. 다음 코드는 파일 구성 실습이며 GUI의 현재 장면을 직접 바꾸지 않는다. Isaac Sim을 실행한 터미널에서 `TUTORIAL_ROOT`를 export했는지 확인한다.

## 1. 파일 형식의 역할을 비교하다

| 형식 | 주로 표현하는 것 | 사용하는 도구와 주의점 |
| --- | --- | --- |
| USD / USDA / USDC | 장면 계층·변환·재질·참조·물리 등 | OpenUSD의 `pxr`로 읽고 쓰며, 실제 지원 스키마를 확인하다 |
| URDF | 로봇의 링크·관절·관성·시각·충돌 형상 | ROS에서 널리 사용하며, 가져온 뒤 drive와 충돌을 점검하다 |
| Xacro | 반복·변수·매크로를 포함한 XML 생성 규칙 | 먼저 URDF로 전개한 뒤 importer에 전달하다 |
| MJCF | MuJoCo 모델의 body·joint·geom·actuator 등 | 가져오기 지원 범위와 물리 엔진 차이를 점검하다 |

`.usda`는 사람이 읽기 쉬운 텍스트 표현이고 `.usdc`는 바이너리 표현이다. `.usd` 확장자는 두 표현 중 하나를 담을 수 있다. USD 파일에 물리 속성을 저장해도 모든 프로그램이 같은 물리 모델을 구현하는 것은 아니다. URDF를 USD로 가져왔다는 사실만으로 센서 렌더링, 관절 이득, ROS 연결이 모두 완성되는 것도 아니다. [OpenUSD 기초](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/open_usd.html)

## 2. 작은 USD 자산을 저장하다

Script Editor에서 실행한다. `crate.usda`는 한 변 0.4 m의 시각 상자이며 이 단계에서는 물리를 넣지 않는다.

```python
import os
from pathlib import Path
from pxr import Gf, Usd, UsdGeom

root = Path(os.environ["TUTORIAL_ROOT"])
scene_dir = root / "artifacts" / "scenes"
scene_dir.mkdir(parents=True, exist_ok=True)
asset_path = scene_dir / "crate.usda"

asset = Usd.Stage.CreateInMemory()
UsdGeom.SetStageMetersPerUnit(asset, 1.0)
UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
crate = UsdGeom.Xform.Define(asset, "/Crate")
asset.SetDefaultPrim(crate.GetPrim())
body = UsdGeom.Cube.Define(asset, "/Crate/Body")
body.CreateSizeAttr(0.4)
asset.GetRootLayer().Export(str(asset_path))
print("자산 저장:", asset_path)
```

`defaultPrim`은 외부 파일에서 이 자산을 가져올 때 기본 진입점을 알려 준다. `/Crate/Body`의 절대 경로를 참조 쪽에서 매번 지정하지 않아도 `/Crate` 아래의 구조를 가져올 수 있다.

## 3. 같은 자산을 두 번 참조하다

다음은 새 `composition.usda`를 작성한다. 동일 이름의 이전 실습 결과가 있으면 이 예제로 덮어쓰므로, 보존할 결과는 다른 이름으로 저장한다. 현재 GUI에서 편집 중인 장면은 건드리지 않는다.

```python
layout_path = scene_dir / "composition.usda"
layout = Usd.Stage.CreateInMemory()
UsdGeom.SetStageMetersPerUnit(layout, 1.0)
UsdGeom.SetStageUpAxis(layout, UsdGeom.Tokens.z)
world = UsdGeom.Xform.Define(layout, "/World")
layout.SetDefaultPrim(world.GetPrim())
layout.GetRootLayer().Export(str(layout_path))

# 저장 경로가 생긴 레이어를 열어 상대 참조의 기준 디렉터리를 정하다.
layout = Usd.Stage.Open(str(layout_path))
for name, x in (("CrateA", -0.6), ("CrateB", 0.6)):
    placement = UsdGeom.Xform.Define(layout, "/World/" + name)
    placement.GetPrim().GetReferences().AddReference("./crate.usda")
    UsdGeom.XformCommonAPI(placement).SetTranslate(Gf.Vec3d(x, 0, 0.2))
layout.GetRootLayer().Save()
print("배치 파일:", layout_path)
```

`File > Open`으로 출력된 `composition.usda`를 열고 Stage에서 CrateA와 CrateB 아래에 각각 Body가 있는지 확인한다. 조명과 바닥은 이 파일에 없으므로 필요하면 06단계 방식으로 추가한다. 참조 검증은 Stage 구조와 아래 숫자 조회로도 수행할 수 있다.

## 4. 원본을 유지하면서 한 배치만 수정하다

```python
body_a = UsdGeom.Cube(layout.GetPrimAtPath("/World/CrateA/Body"))
body_a.GetSizeAttr().Set(0.6)
layout.GetRootLayer().Save()

source = Usd.Stage.Open(str(asset_path))
print("자산 원본:", UsdGeom.Cube(source.GetPrimAtPath("/Crate/Body")).GetSizeAttr().Get())
print("배치 A:", body_a.GetSizeAttr().Get())
print("배치 B:", UsdGeom.Cube(layout.GetPrimAtPath("/World/CrateB/Body")).GetSizeAttr().Get())
print("A 속성에 관여한 레이어:")
for spec in body_a.GetSizeAttr().GetPropertyStack():
    print(spec.layer.identifier, spec.path)
```

원본은 0.4, A는 0.6, B는 0.4여야 한다. A의 크기 변경은 배치 레이어에 기록한 override이다. GUI의 Layers 창과 Edit Target은 지금 어느 레이어에 수정 내용을 기록할지 결정한다. 원본 로봇과 실험별 설정을 나누면 실험 도중 원본 관절을 바꾸는 실수를 줄일 수 있다.

Layer는 의견을 저장하는 단위, Reference는 다른 자산의 구조를 가져오는 연결이다. Sublayer는 여러 레이어의 의견을 같은 장면에 합성하는 방법이다. `Save`와 flatten을 혼동하지 않는다. Flatten은 합성 결과를 한 레이어로 풀어 쓰므로 원래의 재사용 구조를 유지하려면 일반 저장과 필요한 파일 묶음을 우선 사용한다. [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/intro_to_usd.html)

## 5. 같은 상자를 로봇 파일에서 읽다

다음 URDF는 구조를 비교하기 위한 완전한 단일 링크 예이다. 한 변 0.4 m, 질량 1 kg인 균일 상자의 관성은 각 축에서 약 `0.0266667 kg·m²`이다. `visual`과 `collision`을 별도로 둔 점을 확인한다.

```xml
<?xml version="1.0"?>
<robot name="one_box">
  <link name="base_link">
    <visual><geometry><box size="0.4 0.4 0.4"/></geometry></visual>
    <collision><geometry><box size="0.4 0.4 0.4"/></geometry></collision>
    <inertial>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <mass value="1.0"/>
      <inertia ixx="0.0266667" ixy="0" ixz="0" iyy="0.0266667" iyz="0" izz="0.0266667"/>
    </inertial>
  </link>
</robot>
```

Xacro 파일은 위 값들을 변수로 계산할 수 있다. 아래는 `artifacts/one_box.urdf.xacro`에 저장해 전개할 수 있는 예이다.

```xml
<?xml version="1.0"?>
<robot name="one_box" xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:property name="a" value="0.4"/>
  <xacro:property name="m" value="1.0"/>
  <link name="base_link">
    <visual><geometry><box size="${a} ${a} ${a}"/></geometry></visual>
    <collision><geometry><box size="${a} ${a} ${a}"/></geometry></collision>
    <inertial>
      <mass value="${m}"/>
      <inertia ixx="${m*a*a/6}" ixy="0" ixz="0" iyy="${m*a*a/6}" iyz="0" izz="${m*a*a/6}"/>
    </inertial>
  </link>
</robot>
```

Ubuntu 터미널에서 변환한다.

```bash
source /opt/ros/jazzy/setup.bash
xacro "$TUTORIAL_ROOT/artifacts/one_box.urdf.xacro" \
  -o "$TUTORIAL_ROOT/artifacts/one_box.urdf"
```

MJCF는 다음처럼 표현할 수 있다. MJCF box의 `size`는 각 축의 **반길이**이므로 0.4 m 상자는 `0.2 0.2 0.2`이다. [MuJoCo 공식 geom 설명](https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-geom)

```xml
<mujoco model="one_box">
  <worldbody>
    <body name="base_link" pos="0 0 1">
      <freejoint/>
      <geom name="box" type="box" size="0.2 0.2 0.2" mass="1"/>
    </body>
  </worldbody>
</mujoco>
```

URDF와 MJCF는 각각의 importer를 사용한다. USD에서 URDF로 내보내는 공식 exporter도 있지만 조명, 복잡한 재질, 레이어 구조 등은 URDF로 그대로 보존되지 않는다. USD에서 Xacro로 되돌린다고 원래 매크로나 변수명이 복구되는 것도 아니다. 파일 변환 후에는 링크 수, 관절 축, 제한, 질량, Collider, 고정 베이스 여부를 다시 검사한다.

## 예상 결과와 실패 시 확인

crate 원본을 바꾸지 않고 A만 커져야 한다. Reference 오류가 나면 `crate.usda`와 `composition.usda`가 같은 폴더에 있는지 확인한다. 한 파일만 다른 곳으로 옮기면 상대 참조가 끊길 수 있다. 변환한 로봇이 너무 크면 URDF의 미터, MJCF의 반길이, USD의 metersPerUnit을 함께 확인한다.

## 작은 과제

CrateB의 크기만 0.3으로 바꾸고 원본 파일의 크기가 0.4인지 다시 읽는다. 동료에게 장면을 전달할 때 어느 파일을 함께 전달해야 하는지 적는다.

## 공식 6.0.1 자료

- [OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/open_usd.html)
- [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/intro_to_usd.html)
- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [MJCF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_isaacsim_asset_importer_mjcf.html)
- [USD to URDF Exporter Extension](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_omni_exporter_urdf.html)

이전: [07. 강체와 충돌](07-rigid-body-physics.md) · 다음: [09. 중간 프로젝트 1](09-project-lab.md)
