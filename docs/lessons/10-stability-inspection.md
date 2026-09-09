# 10. 물리 안정성을 점검하고 Robot Inspector를 사용하다

## 목표와 준비

로봇이 무너지거나 심하게 떨릴 때 렌더링 문제와 물리 문제를 구분한다. 09단계의 실험실을 검사한 뒤 작은 두 링크 모델로 Robot Inspector의 계층 보기를 연습한다. 고급 제어기를 추가하기 전에 질량·충돌·관절 연결을 읽는 습관을 만든다.

`lab.usda`를 열고 `File > Save As`로 `artifacts/scenes/inspection.usda`에 사본을 만든다. 이 단계는 사본에서 수행한다. 타임라인은 Stop 상태로 둔다. 디버그 시각화를 켜고 끄는 과정과 실제 재생을 구분한다.

## 1. 충돌 모양을 눈으로 확인하다

Viewport의 눈 아이콘에서 `Show by Type > Physics > Colliders > All`을 선택한다. 바닥, 벽, 장애물, TestBox에 물리 형상이 표시되는지 확인한다. 시각 메시와 Collider가 다를 수 있으므로 겉모양만 보고 접촉 상태를 판단하지 않는다.

TestBox가 정지 상태에서 바닥 안에 들어가 있으면 시작부터 큰 접촉 보정이 발생할 수 있다. 물체가 바닥 위에 있는지뿐 아니라, 벽이나 다른 상자의 Collider와 겹치는지도 확인한다. 중복 생성된 바닥은 Stage에서 찾아 삭제한다. 원인을 찾기 전에 solver 반복 횟수를 크게 올리는 방식으로 문제를 가리지 않는다.

```python
import omni.usd
import omni.timeline
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
assert omni.timeline.get_timeline_interface().is_stopped()
for prim in stage.Traverse():
    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        body = UsdPhysics.RigidBodyAPI(prim)
        mass = UsdPhysics.MassAPI(prim).GetMassAttr().Get() if prim.HasAPI(UsdPhysics.MassAPI) else None
        print(prim.GetPath(), "enabled=", body.GetRigidBodyEnabledAttr().Get(), "mass=", mass)
```

Mass가 `None`인 경우는 “질량 0”이 아니라 명시적 MassAPI가 없다는 뜻이다. Collider와 밀도를 통해 계산하는 모델도 있으므로 실제 계산된 질량을 Inspector에서 확인한다. 반대로 의도적으로 입력한 질량이 음수·NaN이거나 형상에 비해 지나치게 작으면 원본 데이터를 수정한다.

## 2. Robot Inspector용 작은 모델을 만들다

09단계의 상자는 로봇 스키마가 없는 단일 강체이므로 Robot Inspector의 로봇 목록에 나타나지 않을 수 있다. 아래 코드는 그 차이를 확인할 수 있도록 두 링크와 두 고정 관절을 갖는 모델을 만든다. 먼저 `Window > Extensions`에서 `isaacsim.robot.schema.ui`를 검색해 활성화한다.

모델은 `(0,-1.5,0.6)` 부근에 배치하므로 기존 중앙 상자와 겹치지 않는다. 원시 USD 스키마로 물리 연결을 먼저 만들고, 마지막에 Robot Schema 정보를 생성한다. **Script Editor에서 Stop 상태로 실행**한다.

```python
from pxr import Gf, UsdGeom, UsdPhysics
import usd.schema.isaac.robot_schema as robot_schema

root_path = "/World/DiagnosticRobot"
assert not stage.GetPrimAtPath(root_path).IsValid(), "이미 만든 모델은 다시 생성하지 않는다."
robot = UsdGeom.Xform.Define(stage, root_path)

def make_link(name, xyz, mass):
    link = UsdGeom.Cube.Define(stage, root_path + "/" + name)
    link.CreateSizeAttr(0.2)
    UsdGeom.XformCommonAPI(link).SetTranslate(Gf.Vec3d(*xyz))
    link.CreateDisplayColorAttr([Gf.Vec3f(0.1, 0.65, 0.3)])
    UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
    UsdPhysics.CollisionAPI.Apply(link.GetPrim())
    UsdPhysics.MassAPI.Apply(link.GetPrim()).CreateMassAttr(mass)
    return link

base = make_link("Base", (0, -1.5, 0.6), 1.0)
tip = make_link("Tip", (0.4, -1.5, 0.6), 0.2)

# body0를 지정하지 않은 고정 관절은 월드와 Base를 연결하다.
anchor = UsdPhysics.FixedJoint.Define(stage, root_path + "/Joints/RootAnchor")
anchor.CreateBody1Rel().SetTargets([base.GetPath()])
anchor.CreateLocalPos0Attr(Gf.Vec3f(0, -1.5, 0.6))
anchor.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
UsdPhysics.ArticulationRootAPI.Apply(anchor.GetPrim())

# 두 링크의 로컬 관절 위치는 같은 월드 지점 (0.2,-1.5,0.6)을 가리키다.
joint = UsdPhysics.FixedJoint.Define(stage, root_path + "/Joints/BaseToTip")
joint.CreateBody0Rel().SetTargets([base.GetPath()])
joint.CreateBody1Rel().SetTargets([tip.GetPath()])
joint.CreateLocalPos0Attr(Gf.Vec3f(0.2, 0, 0))
joint.CreateLocalPos1Attr(Gf.Vec3f(-0.2, 0, 0))

robot_schema.ApplyRobotAPI(robot.GetPrim())
print("진단 모델:", robot.GetPath())
```

이 모델은 관절 계층을 읽는 연습용이다. 움직일 자유도가 없는 Fixed Joint를 사용하므로 위치 제어 명령을 보내는 예제로 사용하지 않는다. 관절이 두 링크 사이의 빈 공간에 있어도 고정 연결이 가능하다. 실제 로봇의 기계 구조를 표현할 때는 시각 메시와 관절 위치를 설계 자료에 맞춰야 한다. 여기서 `Ctrl+S`로 **inspection.usda 사본**을 저장한다.

## 3. Robot Inspector에서 연결을 읽다

1. `Window > Robot Inspector`를 연다.
2. 로봇 목록에서 `DiagnosticRobot`을 선택한다.
3. `Tree` 모드에서 Base → BaseToTip → Tip 연결을 찾는다. 월드에 고정하는 RootAnchor도 관절 목록에서 확인한다.
4. `Flat`으로 바꾸어 링크와 관절을 각각 확인한다. `MuJoCo` 표시는 계층을 보여 주는 방식이며, 이 옵션만 누른다고 물리 백엔드가 전환되지 않는다.
5. 눈 아이콘의 `Show by Type > Physics > Joints`를 켜서 관절 위치와 연결선을 확인한다. 재생 중에는 관절 오버레이가 숨겨질 수 있다.

Robot Inspector는 `IsaacRobotAPI`가 있는 Prim을 기반으로 계층을 구성한다. 빈 목록을 보고 로봇의 시각 메시를 다시 가져오기 전에 Extension과 로봇 스키마를 확인한다. [Robot Inspector](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/robot_inspector.html), [Robot Schema](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/robot_schema.html)

계층을 Python으로 확인할 수도 있다.

```python
from usd.schema.isaac import robot_schema

tree = robot_schema.utils.GenerateRobotLinkTree(stage, stage.GetPrimAtPath("/World/DiagnosticRobot"))
robot_schema.utils.PrintRobotTree(tree)
```

## 4. 임시 진단과 영구 수정을 구분하다

Robot Inspector의 `Deactivate`, `Bypass`, `Anchor`는 원인을 좁히기 위한 임시 조작이다. Deactivate는 해당 요소를 비활성화하고, Bypass는 주변 연결을 이어 주며, Anchor는 링크를 월드에 고정한다. 이 변경은 전용 session sublayer에 저장되며 USD 파일에 영구 저장되지 않는다.

Stop 상태에서 Tip에 Deactivate를 한 번 적용해 표시 변화와 아이콘을 확인한 뒤 같은 조작으로 해제한다. 이번 모델은 이미 RootAnchor로 고정되어 있으므로 Anchor를 추가해 중복 구속을 만들지 않는다. 각 아이콘의 상태를 한꺼번에 바꾸지 않는다.

모든 임시 진단 상태를 한 번에 되돌리려면 Stop 상태에서 `File > New`를 선택한 뒤 저장해 둔 `inspection.usda`를 다시 연다. 새 Stage를 열 때 masking session layer가 지워진다. 저장된 두 링크와 영구 관절은 남고 임시 조작만 사라지는지 확인한다.

이름만 보고 임시 Anchor가 저장되었다고 생각하면 파일을 다시 열었을 때 로봇이 떨어질 수 있다. 필요한 영구 고정은 원본 또는 별도 편집 레이어의 Fixed Joint 설정으로 명시하고 재열기로 확인한다.

## 5. 질량·관성·관절 값을 읽다

`Tools > Robotics > Joint Inspector`에서는 선택한 로봇의 관절 속성을 표로 확인할 수 있다. 이 예제는 Fixed Joint이므로 회전 제한이나 drive 항목이 비어 있을 수 있다. 빈 칸은 “0으로 설정했다”와 다르다. 이후 회전 관절 로봇에서 Position Min/Max, Max Force, Stiffness, Damping을 확인한다. 여러 행을 선택한 상태에서 값을 편집하면 여러 관절에 같은 변경이 적용될 수 있으므로 선택 범위를 먼저 확인한다. [Joint Inspector](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/joint_inspector.html)

질량 분포는 `Tools > Physics Toolbar`의 Rigid Body 선택과 Mass Distribution Manipulator로 확인할 수 있다. Physics Debugger를 사용할 때는 해당 도구의 Step/Run 흐름을 따른다. 공식 자산 검사 튜토리얼에는 디버그 상태에서 일반 Play를 누르면 충돌할 수 있다는 주의가 있으므로, 처음에는 Stop 상태의 형상 검사와 도구의 단일 Step을 사용한다. [공식 자산 검사 실습](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/openusd_tuning_tutorials/tutorial_03_inspect_asset.html)

## 예상 결과와 실패 시 확인

Robot Inspector에 두 링크가 연결된 모델이 표시되어야 한다. BaseToTip의 body 관계가 올바르고, 양쪽 관절 프레임이 같은 월드 지점에 있어야 한다. 시뮬레이션 실행 검사는 디버그 도구와 임시 masking을 해제한 사본에서 별도로 수행하고, 본 단계의 정적 구조 확인만으로 물리 안정성 통과를 선언하지 않는다.

| 문제 | 원인을 좁히는 순서 |
| --- | --- |
| 로봇이 조각처럼 분리됨 | jointEnabled, body0/body1 경로, articulation 구조 |
| 관절 근처에서 심한 떨림 | 로컬 관절 프레임, 초기 Collider 겹침, drive 이득 |
| 로봇 전체가 예상과 다르게 떨어짐 | 고정 베이스 의도, 영구 Fixed Joint, 임시 Anchor 여부 |
| 화면만 깜빡임 | 중복 시각 면, 조명, 렌더 모드; 실제 물리 위치와 비교 |
| 카메라 화면만 검음 | 센서 방향, clipping, 조명, warm-up; 로봇 붕괴와 구분 |

## 작은 과제

BaseToTip의 두 로컬 위치를 월드 좌표로 직접 계산한다. 둘이 같아야 하는 이유를 설명한다. 이어 “파일을 다시 열면 고정이 풀린다”는 문제가 임시 Anchor 때문인지 확인하는 절차를 세 문장으로 적는다.

## 공식 6.0.1 자료

- [Robot Inspector Window](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/robot_inspector.html)
- [Robot Schema](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omniverse_usd/robot_schema.html)
- [Joint Inspector](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/joint_inspector.html)
- [Tutorial 3: Inspect Asset](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/openusd_tuning_tutorials/tutorial_03_inspect_asset.html)

이전: [09. 중간 프로젝트 1](09-project-lab.md) · 다음 단계는 저장소의 학습 순서 표를 따른다.
