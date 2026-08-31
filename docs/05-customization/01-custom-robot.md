# URDF, Xacro와 MJCF에서 커스텀 로봇 완성하기

이 튜토리얼에서는 import된 USD를 제어 가능한 SimReady robot으로 다듬다. 파일이 열리고 mesh가 보이는 것만으로 성공이라 판단하지 않고 articulation, drive, inertia, collision과 ROS 이름을 acceptance test로 검증하다.

## 1. source-of-truth를 정하다

| source | 적합한 경우 | 유지 전략 |
|---|---|---|
| Xacro/URDF | ROS package, TF, MoveIt/Nav2와 함께 관리 | Xacro를 원본으로 유지하고 USD를 재생성하다. |
| MJCF | MuJoCo actuator/default/class 모델이 중심 | MJCF를 원본으로 유지하고 USD-only override를 별도 layer에 두다. |
| USD | 복잡한 material, sensor, variant, PhysX authoring이 중심 | USD를 원본으로 하고 필요할 때 제한적으로 URDF export하다. |

importer가 만든 USD를 직접 대폭 수정한 뒤 다시 import하면 변경을 잃다. 반복 가능한 구조는 다음과 같다.

```text
source description → generated robot_base.usd → robot_physics_override.usda
                                      └────────→ robot_sensors.usda
```

## 2. import 전에 source를 검사하다

### Xacro를 전개하다

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
xacro "$ISAACSIM_COURSE/assets/demo_bot/robot.urdf.xacro" \
  use_sim:=true \
  -o "$ISAACSIM_COURSE/assets/demo_bot/robot.expanded.urdf"

check_urdf "$ISAACSIM_COURSE/assets/demo_bot/robot.expanded.urdf"
```

Xacro 매크로 자체를 importer에 주지 않고 전개 결과를 고정해 diff와 재현성을 남기다. `robot_state_publisher` node를 통한 ROS 2 URDF import도 Xacro를 간접 지원하지만 batch asset build에는 명시적 전개가 읽기 쉽다.

### mesh와 단위를 검사하다

- length가 meter인지 확인하다. mm CAD를 meter로 오해하면 크기가 1000배가 되다.
- 각 link의 visual origin, collision origin과 inertial origin을 비교하다.
- mesh 파일의 상대 경로와 `package://` URI가 실제로 해석되는지 확인하다.
- link/joint/mesh 이름에 특수문자를 피하고 숫자·underscore로 시작하지 않다.
- joint axis가 local frame에서 단위 vector인지 확인하다.
- mimic master가 먼저 존재하고 dependency cycle이 없는지 확인하다.

간단한 질량 sanity check를 남기다.

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

## 3. GUI importer로 첫 기준 asset을 만들다

### URDF

1. `File > Import`에서 `.urdf`를 선택하다.
2. 쓰기 가능한 absolute USD output을 지정하다.
3. mobile/legged robot은 Moveable Base, 고정 manipulator는 의도에 따라 Static Base를 고르다.
4. `Import Inertia Tensor`, mimic 처리, merge fixed joints, collision approximation과 drive를 설정하다.
5. import 후 Output Log의 warning/error를 저장하다.

### MJCF

1. `File > Import`에서 `.xml`을 선택하다.
2. `fix_base`, `import_inertia_tensor`, `import_sites`, `self_collision`을 목적에 맞게 정하다.
3. 반복 mesh가 많으면 instanceable output을 검토하다.

`Collision From Visuals`는 collision source가 없을 때만 임시로 사용하다. 복잡한 render mesh를 그대로 collision으로 쓰는 것을 최종 상태로 두지 않다.

## 4. 반복 가능한 CLI 변환을 만들다

Isaac Lab 2.3.0이 Isaac Sim 5.1과 함께 설치된 경우 변환 script가 실용적인 batch CLI이다.

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

force/effort controller를 붙일 robot에 importer의 position drive를 무조건 남기지 않다. 반대로 position-controlled arm에 stiffness/damping을 모두 0으로 두면 목표를 추종하지 않다.

Isaac Sim 5.1 standalone Python은 legacy Kit command를 사용하다.

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

5.1에서 최신/6.0의 `URDFImporter` class 예제를 섞지 않다. MJCF는 `MJCFCreateImportConfig`와 `MJCFCreateAsset` command를 사용하다.

## 5. 생성된 Stage hierarchy를 읽다

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

실제 importer 출력 경로는 다를 수 있다. 중요한 조건은 다음과 같다.

- robot entry prim이 default prim이다.
- 각 동적 link에 Rigid Body API가 있고 collider가 link에 속하다.
- articulation root가 robot 전체에 정확히 한 번 적용되다.
- joint의 Body0은 parent, Body1은 child이다.
- dynamic rigid body를 또 다른 dynamic rigid body 아래 잘못 중첩하지 않다.
- scene의 `/World/Robot`은 asset reference이고 physics correction은 asset layer에 기록하다.

Script Editor에서 빠르게 검사하다.

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

## 6. articulation과 joint를 검증하다

### root와 base

- 고정 arm은 world fixed joint 또는 fixed-base import가 의도대로 적용되었는지 확인하다.
- mobile robot은 base가 free body이며 시작 pose가 ground와 겹치지 않게 하다.
- articulation root가 mesh leaf가 아니라 kinematic tree의 올바른 root에 적용되었는지 확인하다.
- closed loop는 일반 tree URDF와 다르게 별도 rigging이 필요하다. loop joint와 articulation 설정을 공식 closed-loop 절차로 검증하다.

### joint 표

각 DOF를 표로 남기다.

| joint | type | parent→child | axis | limits | command mode |
|---|---|---|---|---|---|
| `wheel_left_joint` | continuous/revolute | base→wheel | local Y | velocity | velocity |
| `arm_joint_1` | revolute | base→link1 | local Z | `[-2.9, 2.9] rad` | position |

Physics Inspector와 joint gizmo를 사용해 body frame과 axis를 눈으로 확인하다. 양의 작은 command를 한 관절씩 보내 실제 방향을 기록하다.

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

physics가 초기화되기 전에 articulation view를 사용하지 않다. Timeline Play 또는 `World.reset_async()` 뒤 `initialize()`하다.

## 7. drive를 control 방식과 일치시키다

| 목표 | Drive target | 일반 설정 |
|---|---|---|
| 위치 servo | Position | 유한 stiffness와 damping |
| 속도 servo | Velocity | stiffness 0, 적절한 damping/force limit |
| 직접 effort/torque | None | drive가 외부 torque와 싸우지 않게 하다. |

natural frequency 설정은 대략 다음 관계를 사용하다.

\[
K_p=m_{eq}\omega_n^2,\qquad
K_d=2m_{eq}\zeta\omega_n
\]

`m_eq`는 해당 DOF의 equivalent mass/inertia이고 `ζ=1`은 critical damping이다. 단순히 모든 joint에 같은 수치를 복사하지 않다. Gain Tuner로 step response를 보고 overshoot, settling time과 steady-state error를 기록하다.

### mimic joint

URDF importer에서 mimic parsing을 켜면 PhysX Mimic API로 표현할 수 있다. `Ignore Mimic`을 선택했다면 별도 controller가 slave joint를 명령해야 하다.

다음을 검사하다.

- master joint 이름, multiplier와 offset이 원본과 일치하다.
- mimic slave에 독립 drive command를 동시에 보내지 않다.
- gripper가 닫힐 때 양 finger 방향이 의도대로 움직이다.
- mimic chain이 cycle을 만들지 않다.

### transmission과 ros2_control

URDF `<transmission>`/`<ros2_control>`은 hardware/controller contract이지 PhysX joint 자체가 아니다. importer가 joint physics와 ROS controller를 자동 구성한다고 가정하지 않다. import warning을 확인하고 다음을 별도 구성하다.

1. USD joint drive/effort mode
2. Isaac ROS Action Graph 또는 trajectory adapter
3. 외부 `ros2_control` controller와 command/state topic/action

## 8. mass, center of mass와 inertia를 검증하다

물리적으로 유효한 inertia tensor는 대칭이고 양의 definite여야 하다. diagonal 값이 양수여도 triangle inequality가 심하게 어긋난 값은 의심하다.

```text
Ixx > 0, Iyy > 0, Izz > 0
Ixx ≤ Iyy + Izz, Iyy ≤ Ixx + Izz, Izz ≤ Ixx + Iyy
```

검사 순서는 다음과 같다.

1. link mass가 실측/BOM과 같은 order인지 확인하다.
2. inertial origin이 visual origin이 아니라 실제 COM인지 확인하다.
3. inertia가 COM frame 기준인지 확인하다.
4. mesh scale을 바꿨다면 mass/inertia도 올바르게 scale되었는지 확인하다.
5. density `0` fallback에 의존한 link를 목록화하다.

길이를 `s`배, 같은 density를 유지하면 mass는 대략 `s³`, inertia는 `s⁵`배가 되다. geometry만 0.001배 하고 inertia를 그대로 두는 오류를 피하다.

실습에서는 robot을 공중에 고정해 joint 하나의 gravity response를 보고, ground에 놓아 10초간 NaN·폭발·지속 jitter가 없는지 확인하다. simulation data visualizer로 COM과 inertia axes를 켜다.

## 9. collider를 visual과 분리하다

Viewport의 `Show by Type > Physics > Colliders > All`로 collider만 보이게 하다.

| 형상 | 권장 collision |
|---|---|
| wheel, link primitive | box/sphere/capsule/cylinder 또는 convex hull |
| 복잡한 dynamic link | 여러 convex hull 또는 convex decomposition |
| 정적 environment | triangle mesh 가능, 성능과 contact 품질 검증 |
| 고해상도 render mesh | 직접 dynamic collider로 쓰지 않다. |

다음을 확인하다.

- collider가 visual보다 지나치게 크거나 작지 않다.
- 인접 link collider가 rest pose에서 깊게 겹치지 않다.
- wheel collider와 axle axis가 맞다.
- self-collision을 켜기 전에 인접 link pair를 검토하다.
- contact offset/rest offset이 robot scale에 맞다.
- friction과 restitution이 floor material과 함께 의도한 거동을 만들다.

convex hull은 빠르지만 오목한 공간을 메우다. convex decomposition은 세밀하지만 collider 수와 contact 비용이 늘다. control 목적에 필요한 최소 정확도를 선택하다.

## 10. ROS/MoveIt 이름과 sensor mount를 준비하다

- `/joint_states`의 name이 URDF/SRDF와 일치하는지 검사하다.
- USD 이름을 바꾸지 않고 ROS 이름만 바꾸려면 `isaac:nameOverride`를 사용하다.
- `base_link`, `odom`, sensor frame과 optical frame의 TF ownership을 정하다.
- sensor는 link child Xform 아래 reference하고 calibration transform을 별도 layer에 기록하다.
- 여러 robot을 복제할 경우 graph 안 absolute prim path와 topic을 parameterize하다.

## 11. acceptance test를 자동화하다

| Test | 조건 | 예시 합격 기준 |
|---|---|---|
| Load | headless open/reopen | error 0, missing asset 0 |
| Rest | ground에서 10 s | NaN 0, base drift 제한 이내 |
| Joint step | 각 DOF 작은 step | 방향/limit 일치, overshoot 기준 이내 |
| Velocity | wheel 1 rad/s | 부호와 steady speed 일치 |
| Collision | 낮은 높이 drop | 관통 없음, 비정상 반발 없음 |
| Self collision | full range sweep | 허용 pair 외 contact 없음 |
| ROS | joint state/TF | 이름·timestamp·frame 일치 |
| Reset | Stop→Play 20회 | state/callback 누적 없음 |

import log, robot total mass, DOF 이름/limit, 10초 pose trace와 controller gain을 artifact로 남기다.

## 12. 흔한 실패와 원인

| 증상 | 주된 원인 |
|---|---|
| Play 즉시 폭발 | 겹친 collider, 잘못된 scale/inertia, joint frame 오류 |
| robot이 국수처럼 처짐 | drive 없음/너무 낮은 gain, fixed base 누락 |
| torque command가 먹지 않음 | 기존 position drive가 동시에 작동 |
| wheel이 회전해도 이동 안 함 | axis/order 오류, friction 부족, collision orientation 오류 |
| gripper finger가 반대로 움직임 | mimic multiplier/axis 오류 |
| ROS joint가 누락 | fixed/merged joint 또는 이름 mismatch |
| import를 다시 하면 수정 소실 | generated layer를 직접 수정 |

## 완료 체크포인트

- [ ] source description과 generated USD/override layer를 분리했다.
- [ ] articulation root, Body0/Body1, axis와 limits를 각 DOF에서 검사했다.
- [ ] drive target과 외부 controller mode가 충돌하지 않다.
- [ ] mimic/transmission을 자동 변환되었다고 가정하지 않고 검증했다.
- [ ] mass/COM/inertia와 collider를 시각화하고 수치로 기록했다.
- [ ] headless load, 10초 rest, joint step, collision, ROS와 reset test를 통과했다.

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
