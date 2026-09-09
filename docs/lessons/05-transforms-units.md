# 05. Prim 계층, 좌표계, 단위를 이해하다

## 목표와 준비

04단계에서 익힌 Property 조작을 바탕으로 부모 좌표와 월드 좌표를 구분한다. 로봇의 카메라가 엉뚱한 방향을 보거나 바퀴가 차체에서 떨어져 보이는 문제는 좌표를 잘못 해석할 때도 발생한다. 이 단계에서는 물리를 켜지 않고 단순한 상자 두 개로 좌표 관계를 확인한다.

`File > New`로 연습 장면을 만들고 `Window > Script Editor`를 연다. 이하 Python 코드는 모두 **GUI의 Script Editor**에서 실행한다.

## 1. 미터와 Z-up을 명시하다

이 튜토리얼은 길이를 미터, 질량을 킬로그램으로 다루며 월드의 위쪽은 +Z로 둔다. 크기가 `0.4`인 상자는 한 변이 40 cm이다. 로봇의 전진 방향과 카메라의 광학 축은 이후 별도로 정의한다. “Z-up”만으로 모든 센서의 앞쪽 방향까지 결정되는 것은 아니다.

```python
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
print("한 단위의 길이[m]:", UsdGeom.GetStageMetersPerUnit(stage))
print("위쪽 축:", UsdGeom.GetStageUpAxis(stage))
```

이 설정은 앞으로 입력할 숫자의 의미를 선언한다. 이미 센티미터로 만든 물체가 들어 있는 장면의 메타데이터만 `1.0`으로 바꾸면 물체가 자동으로 1/100로 축소되지 않는다. 모델 변환 시 크기·관성·관절 위치를 함께 확인해야 한다. [Isaac Sim 단위와 좌표 관례](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/reference_material/reference_conventions.html)

## 2. 부모와 자식의 위치를 비교하다

다음은 로봇 전체를 나타내는 빈 Xform과 그 아래의 상자를 만든다. Xform은 여러 객체를 함께 움직이는 기준점으로 사용할 수 있다.

```python
from pxr import Gf, Usd, UsdGeom

rig = UsdGeom.Xform.Define(stage, "/World/Rig")
UsdGeom.XformCommonAPI(rig).SetTranslate(Gf.Vec3d(1.0, 0.0, 0.0))
box = UsdGeom.Cube.Define(stage, "/World/Rig/Marker")
box.CreateSizeAttr(0.2)
UsdGeom.XformCommonAPI(box).SetTranslate(Gf.Vec3d(0.5, 0.0, 0.4))

cache = UsdGeom.XformCache(Usd.TimeCode.Default())
world_matrix = cache.GetLocalToWorldTransform(box.GetPrim())
print("자식의 월드 위치:", world_matrix.ExtractTranslation())
```

Stage에서 `/World/Rig/Marker`를 선택하고 `F`로 화면을 맞춘다. Marker의 Property에는 부모 기준 위치 `(0.5, 0, 0.4)`가 표시된다. 부모는 X 방향으로 1 m 이동했으므로 출력되는 월드 위치는 `(1.5, 0, 0.4)`이다. 지금은 부모 회전과 스케일이 없어서 좌표를 단순히 더할 수 있다.

## 3. 부모를 회전하다

```python
UsdGeom.XformCommonAPI(rig).SetRotate(Gf.Vec3f(0.0, 0.0, 90.0))
cache.Clear()
print("부모 회전 후 월드 위치:", cache.GetLocalToWorldTransform(box.GetPrim()).ExtractTranslation())
```

이번에는 대략 `(1.0, 0.5, 0.4)`가 출력된다. 소수점 끝의 아주 작은 오차는 부동소수점 계산에서 나타날 수 있다. 부모가 회전했기 때문에 자식의 로컬 +X가 월드 +Y를 가리킨다. 자식의 Translate를 바꾸지 않아도 월드 위치는 바뀐다.

`cache.Clear()`는 이전 변환 계산 결과를 버린다. 장면을 수정한 뒤 같은 캐시를 재사용하면 이전 위치를 읽을 수 있으므로 정적 장면 점검에서도 갱신 시점을 의식한다. 재생 중 로봇 상태는 물리 엔진과 Fabric 쪽에서 갱신될 수 있어 USD 속성 조회만으로 실제 위치를 검증하지 않는다. 이 예는 **정지 상태의 장면 구성**을 확인하는 코드이다.

## 4. 회전 단위를 구별하다

USD의 `rotateXYZ`와 GUI의 회전 입력은 도 단위이다. ROS 메시지와 일반적인 로봇 제어식의 각도는 라디안을 사용하는 경우가 많다. 쿼터니언은 배열 순서까지 확인해야 한다. `pxr.Gf.Quatd`는 실수부를 먼저 받고, ROS `geometry_msgs/Quaternion`은 필드 이름 `x,y,z,w`로 표현한다.

```python
import math
from pxr import Gf

yaw_deg = 90.0
yaw_rad = math.radians(yaw_deg)
usd_quat = Gf.Quatd(math.cos(yaw_rad / 2), Gf.Vec3d(0, 0, math.sin(yaw_rad / 2)))
print("도:", yaw_deg, "라디안:", yaw_rad)
print("USD 쿼터니언의 실수부:", usd_quat.GetReal())
print("USD 쿼터니언의 허수부:", usd_quat.GetImaginary())
```

## 예상 결과와 실패 시 확인

부모 회전 전후에 예상한 월드 좌표가 출력되어야 한다. 좌표가 100배 다르면 모델 원본 단위를 확인한다. 회전 방향이 다르면 로컬 축과 월드 축을 혼동했는지 확인한다. 물체가 찌그러지면 부모나 자식에 비균일 Scale이 남아 있는지 확인한다. 관절이 있는 로봇은 GUI로 무작정 전체 Scale을 조절하기보다 원본 단위와 가져오기 설정을 먼저 수정한다.

## 작은 과제

부모의 위치를 `(2, -1, 0)`으로 바꾸고 회전을 0도로 되돌린다. Marker의 월드 위치를 계산한 뒤 출력과 비교한다. 이어 부모를 180도 회전했을 때의 위치를 먼저 종이에 적고 검증한다.

## 공식 6.0.1 자료

- [Isaac Sim Conventions](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/reference_material/reference_conventions.html)
- [OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/open_usd.html)
- [Physics Data Flow and Engine Integration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/new_physics_engine.html)

이전: [04. GUI 첫 조작](04-gui-basics.md) · 다음: [06. 바닥·조명·재질](06-ground-light-material.md)
