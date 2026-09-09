# URDF, Xacro와 MJCF에서 커스텀 로봇 완성하기

이 튜토리얼에서는 가져온 USD를 제어 가능한 SimReady 로봇으로 다듬는다. 파일이 열리고 메시가 보이는 것만으로 성공이라 판단하지 않고 articulation, 드라이브, 관성, 충돌과 ROS 이름을 시험으로 확인한다.

## 1. 기준 원본 정하기

| 원본 | 적합한 경우 | 유지 전략 |
|---|---|---|
| Xacro/URDF | ROS 패키지, TF, MoveIt/Nav2와 함께 관리 | Xacro를 원본으로 유지하고 USD를 재생성한다. |
| MJCF | MuJoCo의 actuator·default class 설정이 중심 | MJCF를 원본으로 유지하고 USD 전용 수정 사항을 별도 레이어에 둔다. |
| USD | 복잡한 재질, 센서, variant, PhysX 속성 편집이 중심 | USD를 원본으로 하고 필요할 때 지원 범위 안에서 URDF로 내보낸다. |

가져오기 도구가 만든 USD를 직접 대폭 수정한 뒤 다시 가져오면 변경을 잃게 된다. 반복 가능한 구조는 다음과 같다.

```text
source description → generated robot_base.usd → robot_physics_override.usda
                                      └────────→ robot_sensors.usda
```

## 2. 가져오기 전 원본 검사

### Xacro를 URDF로 펼치기

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
xacro "$ISAACSIM_COURSE/assets/demo_bot/robot.urdf.xacro" \
  use_sim:=true \
  -o "$ISAACSIM_COURSE/assets/demo_bot/robot.expanded.urdf"

check_urdf "$ISAACSIM_COURSE/assets/demo_bot/robot.expanded.urdf"
```

Xacro를 펼친 URDF와 실행 인자를 함께 보관하면 같은 자산을 다시 만들고 변경 전후를 비교할 수 있다. `robot_state_publisher` 노드를 통한 ROS 2 URDF 가져오기도 Xacro를 간접 지원하지만 여러 자산을 자동으로 변환할 때는 URDF 파일로 먼저 저장하는 편이 문제를 추적하기 쉽다.

### 메시와 단위 검사

- 메시의 길이 단위를 확인한다. 밀리미터로 만든 CAD 파일을 미터 단위로 읽으면 크기가 1000배가 된다.
- 각 링크의 시각 원점, 충돌 원점과 관성 원점을 비교한다.
- 메시 파일의 상대 경로와 `package://` URI가 실제로 해석되는지 확인한다.
- 링크/관절/메시 이름에 특수문자를 피하고 숫자·밑줄로 시작하지 않는다.
- 관절 축이 로컬 프레임에서 단위 벡터인지 확인한다.
- mimic 관계에서 기준 관절이 실제로 존재하고, 관절들이 서로를 순환 참조하지 않는지 확인한다.

링크별 질량과 총질량부터 확인한다.

```bash
# [ROS]
python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse("robot.expanded.urdf").getroot()
total = 0.0
for link in root.findall("link"):
    mass = link.find("inertial/mass")
    if mass is not None:
        value = float(mass.attrib["value"])
        print(f"{link.attrib['name']:<30} {value:9.4f} kg")
        total += value
print("total:", total, "kg")
PY
```

## 3. GUI 가져오기 도구로 기준 자산 만들기

### URDF

1. `File > Import`에서 `.urdf`를 선택한다.
2. USD를 저장할 쓰기 가능한 절대 경로를 지정한다.
3. 이동·보행 로봇은 Moveable Base를 고른다. 바닥에 고정할 로봇 팔은 Static Base를 고른다.
4. `Import Inertia Tensor`, mimic 관계 처리, 고정 관절 병합, 충돌 형상 근사와 드라이브를 설정한다.
5. 가져오기 후 Output Log의 경고·오류를 저장한다.

### MJCF

1. `File > Import`에서 `.xml`을 선택한다.
2. `fix_base`, `import_inertia_tensor`, `import_sites`, `self_collision`을 목적에 맞게 정한다.
3. 같은 메시를 반복 사용한다면 인스턴스로 공유하는 instanceable 자산을 검토한다.

`Collision From Visuals`는 충돌 원본이 없을 때만 임시로 사용한다. 복잡한 렌더링용 메시를 그대로 충돌로 쓰는 것을 최종 상태로 두지 않는다.

## 4. 명령행에서 반복 가능한 변환 구성하기

Isaac Lab 2.3.0이 Isaac Sim 5.1과 함께 설치된 경우 변환 스크립트가 여러 자산을 한꺼번에 변환할 때 편리하다.

```bash
# [SIM/Isaac Lab]
./isaaclab.sh -p scripts/tools/convert_urdf.py \
  /abs/robot.expanded.urdf /abs/robot.usd \
  --joint-stiffness 0.0 \
  --joint-damping 0.0 \
  --joint-target-type none \
  --headless

./isaaclab.sh -p scripts/tools/convert_mjcf.py \
  /abs/robot.xml /abs/robot.usd \
  --import-sites \
  --make-instanceable \
  --headless
```

힘·토크 제어기를 붙일 로봇에 가져오기 도구의 위치 드라이브를 무조건 남기지 않는다. 반대로 위치 제어 로봇 팔에 강성과 감쇠를 모두 0으로 두면 목표를 추종하지 않는다.

Isaac Sim 5.1 Standalone Python은 기존 Kit 명령을 사용한다.

```python
from isaacsim import SimulationApp
app = SimulationApp({"headless": True})

import omni.kit.commands
from isaacsim.asset.importer.urdf import _urdf

cfg = _urdf.ImportConfig()
cfg.set_fix_base(False)
cfg.set_merge_fixed_joints(False)
cfg.set_import_inertia_tensor(True)
cfg.set_self_collision(False)

ok, prim_path = omni.kit.commands.execute(
    "URDFParseAndImportFile",
    urdf_path="/abs/robot.expanded.urdf",
    import_config=cfg,
    dest_path="/abs/generated/robot.usd",
)
if not ok:
    raise RuntimeError("URDF import failed")
app.update()
app.close()
```

5.1 코드에 최신 버전이나 6.0 문서의 `URDFImporter` 클래스 예제를 섞지 않는다. MJCF는 `MJCFCreateImportConfig`와 `MJCFCreateAsset` 명령을 사용한다.

## 5. 생성된 Stage 계층 읽기

권장 개념 구조는 다음과 같다.

```text
/Robot                       default prim, articulation root
  /base_link                 rigid body
    /visuals                 render geometry
    /collisions              collider geometry
  /link_1                    rigid body
  /Joints
    /joint_1                 revolute/prismatic/fixed joint
  /Sensors
```

실제 가져오기 도구 출력 경로는 다를 수 있다. 중요한 조건은 다음과 같다.

- 로봇 자산의 최상위 Prim을 defaultPrim으로 지정한다.
- 각 동적 링크에 강체 API가 적용되어 있고 충돌 형상이 링크에 속한다.
- articulation 루트가 로봇 전체에 정확히 한 번 적용된다.
- 이 튜토리얼에서는 관절의 Body0을 부모 링크, Body1을 자식 링크로 연결한다.
- 동적 강체를 또 다른 동적 강체 아래 잘못 중첩하지 않는다.
- 장면의 `/World/Robot`은 자산 참조이고 물리 수정 사항은 자산 레이어에 기록한다.

Script Editor에서 빠르게 검사한다.

```python
import omni.usd
from pxr import UsdPhysics

stage = omni.usd.get_context().get_stage()
for prim in stage.Traverse():
    tags = []
    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        tags.append("rigid")
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        tags.append("collider")
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        tags.append("articulation-root")
    if tags:
        print(prim.GetPath(), ",".join(tags))
```

## 6. Articulation과 관절 검증

### 루트와 베이스

- 고정 로봇 팔은 월드에 고정하는 관절 또는 베이스 고정 설정이 의도대로 적용되었는지 확인한다.
- 이동형 로봇은 베이스가 자유롭게 움직이는 강체이며 시작 자세가 바닥과 겹치지 않게 한다.
- Articulation Root API가 말단 메시가 아닌, 해당 로봇의 운동학 구조에 맞는 루트에 적용되었는지 확인한다.
- 폐루프 기구는 링크와 관절이 나무처럼 뻗는 일반 URDF 구조와 설정 방법이 다르다. NVIDIA의 폐루프 구조 실습에 따라 루프를 닫는 관절과 articulation 설정을 검증한다.

### 관절 표

각 자유도(DOF)의 관절 종류, 축과 제어 방식을 표로 기록한다.

| 관절 | 종류 | 부모→자식 | 축 | 제한 | 제어 방식 |
|---|---|---|---|---|---|
| `wheel_left_joint` | continuous/회전 | 베이스→바퀴 | 로컬 Y축 | 속도 | 속도 |
| `arm_joint_1` | 회전 | 베이스→link1 | 로컬 Z축 | `[-2.9, 2.9] rad` | 위치 |

Physics Inspector와 관절 조작 핸들을 사용해 물체 프레임과 축을 눈으로 확인한다. 양의 작은 명령을 한 관절씩 보내 실제 방향을 기록한다.

```python
# Script Editor의 async context 또는 Extension reset 이후에 실행하다.
import numpy as np
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction

robot = SingleArticulation("/World/Robot")
robot.initialize()
print(robot.dof_names)

target = np.zeros(robot.num_dof)
target[0] = 0.2
robot.apply_action(ArticulationAction(joint_positions=target))
```

물리를 초기화한 뒤 articulation view를 사용한다. 타임라인을 재생하거나 `World.reset_async()`를 완료한 뒤 `initialize()`를 호출한다.

## 7. 제어 방식에 맞는 관절 드라이브 설정

| 목표 | 드라이브 목표 | 일반 설정 |
|---|---|---|
| 위치 제어 | Position | 강성과 감쇠를 목표 응답에 맞게 설정 |
| 속도 제어 | Velocity | 강성 0, 감쇠와 힘·토크 제한 설정 |
| 힘·토크 직접 제어 | None | 관절 드라이브가 외부 제어기의 명령을 방해하지 않도록 설정 |

고유진동수와 감쇠비로 게인을 정할 때는 다음 근사 관계를 사용한다.

\[
K_p=m_{eq}\omega_n^2,\qquad
K_d=2m_{eq}\zeta\omega_n
\]

`m_eq`는 해당 DOF의 등가 질량/관성이고 `ζ=1`은 임계 감쇠이다. 단순히 모든 관절에 같은 수치를 복사하지 않는다. Gain Tuner로 계단 입력 응답을 보고 오버슈트, 정착 시간과 정상 상태 오차를 기록한다.

### Mimic 관절

URDF 가져오기 도구에서 mimic 관계 해석을 켜면 PhysX의 mimic API로 관절 간 연동을 표현할 수 있다. `Ignore Mimic`을 선택했다면 별도 제어기가 종속 관절을 명령해야 한다.

다음을 검사한다.

- 기준 관절 이름, 배율(multiplier), 오프셋이 원본과 일치한다.
- 기준 관절을 따라가는 종속 관절에 별도의 드라이브 명령을 동시에 보내지 않는다.
- 그리퍼가 닫힐 때 양쪽 손가락이 의도한 방향으로 움직인다.
- 연동 연결이 순환을 만들지 않는다.

### transmission과 ros2_control

URDF `<transmission>`/`<ros2_control>`은 하드웨어/제어기 설정 기준이지 PhysX 관절 자체가 아니다. 가져오기 도구가 관절 물리와 ROS 제어기를 자동 구성한다고 가정하지 않는다. 가져오기 경고를 확인하고 다음을 별도 구성한다.

1. USD 관절의 드라이브 또는 힘·토크 제어 방식
2. Isaac Sim의 ROS 2 Action Graph 또는 궤적 명령 변환 코드
3. 외부 `ros2_control` 제어기와 명령·상태 토픽과 액션

## 8. 질량·질량중심·관성 검증

물리적으로 유효한 관성 텐서는 대칭이고 양의 정부호여야 한다. 대각 값이 양수여도 삼각 부등식이 심하게 어긋난 값은 의심한다.

```text
Ixx > 0, Iyy > 0, Izz > 0
Ixx ≤ Iyy + Izz, Iyy ≤ Ixx + Izz, Izz ≤ Ixx + Iyy
```

검사 순서는 다음과 같다.

1. 링크 질량이 실측값이나 부품 명세서(BOM)에서 계산한 값과 비슷한지 확인한다.
2. 관성 원점이 시각 원점이 아니라 실제 COM인지 확인한다.
3. 관성이 COM 프레임 기준인지 확인한다.
4. 메시 크기를 바꿨다면 질량과 관성도 크기 변화에 맞게 다시 계산했는지 확인한다.
5. 밀도 `0` 기본 처리에 의존한 링크를 목록화한다.

길이를 `s`배로 바꾸고 같은 밀도를 유지하면 질량은 대략 `s³`, 관성은 `s⁵`배가 된다. 형상만 0.001배 하고 관성을 그대로 두는 오류를 피한다.

실습에서는 로봇을 공중에 고정해 관절 하나의 중력에 대한 반응을 보고, 바닥에 놓아 10초간 NaN·폭발·지속 떨림이 없는지 확인한다. Simulation Data Visualizer로 COM과 관성 주축을 켠다.

## 9. 충돌 형상과 외형 분리

Viewport의 `Show by Type > Physics > Colliders > All`로 충돌 형상만 보이게 한다.

| 형상 | 권장 충돌 |
|---|---|
| 단순한 바퀴·링크 | 상자·구·캡슐·원통 또는 볼록 껍질(convex hull) |
| 복잡한 동적 링크 | 여러 볼록 껍질 또는 볼록 분해 |
| 정적 환경 | 삼각형 메시 사용 가능, 성능과 접촉 품질 검증 |
| 고해상도 렌더링용 메시 | 직접 동적 충돌 형상으로 쓰지 않는다. |

다음을 확인한다.

- 충돌 형상이 외형보다 지나치게 크거나 작지 않다.
- 인접 링크 충돌 형상이 정지 자세에서 깊게 겹치지 않는다.
- 바퀴 충돌 형상의 회전축과 차축이 일치한다.
- 자기 충돌을 켜기 전에 인접 링크 쌍을 검토한다.
- 접촉 오프셋/정지 오프셋이 로봇 크기에 맞다.
- 로봇과 바닥 재질의 마찰계수·반발계수 조합이 의도한 움직임을 만드는지 확인한다.

볼록 껍질은 빠르지만 오목한 공간을 메운다. 볼록 분해는 세밀하지만 충돌 형상 수와 접촉 비용이 늘어난다. 제어에 필요한 정확도를 만족하면서 계산 부담이 적은 충돌 형상을 선택한다.

## 10. ROS·MoveIt 이름과 센서 장착 위치 준비

- `/joint_states`의 name이 URDF/SRDF와 일치하는지 검사한다.
- USD 이름을 바꾸지 않고 ROS 이름만 바꾸려면 `isaac:nameOverride`를 사용한다.
- `base_link`, `odom`, 센서 프레임과 optical 프레임의 TF 발행 책임을 정한다.
- 센서는 링크의 자식 Xform 아래에 참조로 배치하고 보정 변환을 별도 레이어에 기록한다.
- 여러 로봇을 복제할 경우 그래프 안 절대 prim 경로와 토픽 이름을 매개변수로 관리한다.

## 11. 검증 시험 자동화

| 시험 | 조건 | 예시 합격 기준 |
|---|---|---|
| 불러오기 | 창 없이 열고 다시 불러오기 | 오류 0, 누락 자산 0 |
| 정지 | 바닥에서 10초 | NaN 0, 베이스 위치 변화가 허용 범위 이내 |
| 관절 계단 입력 | 각 자유도에 작은 목표값 변화 | 방향/제한 일치, 오버슈트 기준 이내 |
| 속도 | 바퀴 1 rad/s | 회전 방향과 정상상태 속도 일치 |
| 충돌 | 낮은 높이에서 낙하 | 관통 없음, 비정상 반발 없음 |
| 자기 충돌 | 전체 관절 가동 범위 검사 | 허용 쌍 외 접촉 없음 |
| ROS | 관절 상태/TF | 이름·타임스탬프·프레임 일치 |
| 초기화 | Stop→Play 20회 | 상태/콜백 누적 없음 |

가져오기 로그, 로봇 총질량, 자유도별 이름·제한, 10초간 자세 기록과 제어기 게인을 결과 파일로 남긴다.

## 12. 흔한 실패와 원인

| 증상 | 주된 원인 |
|---|---|
| Play 즉시 폭발 | 겹친 충돌 형상, 잘못된 크기/관성, 관절 프레임 오류 |
| 로봇 관절이 자세를 유지하지 못하고 처짐 | 드라이브 없음/너무 낮은 게인, 베이스 고정 누락 |
| 토크 명령이 먹지 않음 | 기존 위치 드라이브가 동시에 작동 |
| 바퀴가 회전해도 이동 안 함 | 축·관절 순서 오류, 마찰 부족, 충돌 방향 오류 |
| 그리퍼 손가락이 반대로 움직임 | mimic 배율·축 오류 |
| ROS 관절이 누락 | 고정·병합된 관절 또는 이름 불일치 |
| 가져오기를 다시 하면 수정 소실 | 생성된 레이어를 직접 수정 |

## 완료 체크포인트

- [ ] 원본 로봇 설명 파일과 생성된 USD/override 레이어를 분리했다.
- [ ] articulation 루트, Body0/Body1, 축과 제한을 각 DOF에서 검사했다.
- [ ] 드라이브 목표와 외부 제어 방식이 충돌하지 않는다.
- [ ] mimic 관계와 transmission 설정이 그대로 변환되었다고 가정하지 않고 검증했다.
- [ ] 질량/COM/관성과 충돌 형상을 시각화하고 수치로 기록했다.
- [ ] 창 없이 불러오기, 10초 정지, 관절 계단 입력, 충돌, ROS와 초기화 시험을 통과했다.

## 출처

- [Isaac Sim 5.1 — Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [Isaac Sim 5.1 — URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [Isaac Sim 5.1 — Import MJCF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_mjcf.html)
- [Isaac Sim 5.1 — MJCF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_mjcf.html)
- [Isaac Sim 5.1 — Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Isaac Sim 5.1 — Articulate a Basic Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_simple_robot.html)
- [Isaac Sim 5.1 — Rig a Mobile Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html)
- [Isaac Sim 5.1 — Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Isaac Sim 5.1 — Tuning Joint Drive Gains](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)
- [Isaac Sim 5.1 — Asset Optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html)
- [Isaac Sim 5.1 — Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Isaac Sim 5.1 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
