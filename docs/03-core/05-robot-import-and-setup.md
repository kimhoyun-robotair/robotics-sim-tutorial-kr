# 로봇 가져오기와 설정

Importer가 오류 없이 끝났다고 시뮬레이션 가능한 로봇이 완성된 것은 아니다. 가져온 뒤 링크 계층, scale, collider, 질량·관성, joint 축·limit, drive, articulation root와 센서 frame을 검증해야 한다. 이 튜토리얼은 URDF/MJCF 입력을 재사용 가능한 USD 로봇 자산으로 만드는 전체 절차를 다룬다.

## 1. 권장 파이프라인

```text
원본 CAD/URDF/Xacro/MJCF
        ↓ 입력 정리·lint
Importer로 USD 생성
        ↓
시각/충돌/물리 계층 정리
        ↓
Articulation·joint·drive 검증
        ↓
센서·gripper·end-effector frame 추가
        ↓
gain·마찰·solver 조정
        ↓
motion generation XRDF/robot description 생성
        ↓
Asset Validation + 독립 smoke test
        ↓
장면에서는 reference로 사용
```

원본 description과 생성 USD를 모두 버전 관리한다. Importer 설정과 후처리 스크립트도 함께 기록해야 원본이 바뀌었을 때 재생성할 수 있다.

## 2. 가져오기 전 점검

### 이름과 경로

- link, joint, mesh와 파일 이름에는 USD prim 이름에 부적합한 특수문자를 피한다. Importer가 `_`로 바꾸면 ROS joint 이름과 USD 이름의 대응이 깨질 수 있다.
- `package://`, 상대 경로와 texture URI가 실제로 resolve되는지 확인한다.
- 대소문자를 구분하는 Linux에서 파일 이름이 정확한지 확인한다.
- Xacro macro는 먼저 펼쳐 실제 URDF를 보관하거나 ROS 2 node importer를 사용한다.

```bash
# ROS 2 Jazzy 환경에서 Xacro를 명시적으로 URDF로 펼치는 예
source /opt/ros/jazzy/setup.bash
xacro robot.urdf.xacro use_fake_hardware:=true > robot.generated.urdf
check_urdf robot.generated.urdf
```

### geometry와 단위

- 길이가 meter 기준인지 확인한다. CAD가 millimeter인데 scale 1로 가져오면 1000배 로봇이 된다.
- visual mesh는 보기 위한 것이며 collision mesh는 단순하고 닫힌 형상으로 별도 준비한다.
- link 원점, inertial origin, visual/collision origin과 joint origin을 구분한다.
- Z-up Stage로 변환된 뒤 joint axis가 의도대로인지 확인한다.

### 관성과 joint

- 움직이는 모든 link에 양의 mass가 있는지 확인한다.
- inertia matrix가 대칭이고 물리적으로 가능한 양의 값인지 확인한다.
- joint limit의 lower < upper, velocity > 0, effort > 0인지 확인한다.
- continuous joint와 limited revolute joint를 잘못 바꾸지 않는다.
- mimic joint, fixed joint 병합과 transmission 의미가 실제 제어 방식과 맞는지 확인한다.

## 3. URDF를 GUI로 가져오기

1. `Window > Extensions`에서 `isaacsim.asset.importer.urdf`가 활성화되었는지 확인한다.
2. `File > Import`에서 `.urdf`를 선택한다.
3. **USD Output**을 프로젝트의 쓰기 가능한 폴더로 지정한다.
4. 고정형 arm은 **Static Base**, AMR·legged robot은 **Moveable Base**를 선택한다.
5. mass가 없는 link에만 적용될 Default Density를 결정한다. 0이면 물리 엔진 기본 계산을 사용한다.
6. drive target을 joint별로 Position, Velocity 또는 None으로 설정한다.
7. collision source와 approximation을 정한다.
8. self collision은 collider가 서로 겹치지 않는 것을 확인하기 전에는 끈다.
9. Import를 누르고 Output Log의 warning을 읽는다.

### 주요 옵션을 결정하는 법

| 옵션 | 선택 기준 |
|---|---|
| Static/Moveable base | world에 고정된 arm인가, base가 움직이는 로봇인가? |
| Natural Frequency/Stiffness | 초기 gain을 물리적인 bandwidth로 줄 것인가, Kp/Kd를 직접 줄 것인가? |
| Acceleration/Force drive | inertia에 독립적인 이상적 감쇠형인가, 실제 spring-damper force인가? |
| Position/Velocity/None | 해당 joint를 어떤 controller가 구동하는가? torque 제어면 None을 고려한다. |
| Ignore Mimic | 원본 mimic을 PhysX Mimic API로 유지할 것인가? |
| Collision From Visuals | collision geometry가 없을 때만 임시 방편으로 쓴다. |
| Convex Hull/Decomposition | 단순·볼록인가, 오목한 동적 형상인가? |
| Replace Cylinders with Capsules | 더 안정적이고 단순한 바퀴/링크 collider가 필요한가? |
| Self Collision | 필요한 link pair만 충돌해야 하는가, 초기 overlap이 없는가? |

Importer의 natural frequency 설정은 결과 USD에는 stiffness로 저장된다. 공식 문서의 관계는 다음과 같다.

\[
K_p=m_{eq}\omega_n^2,\qquad K_d=2m_{eq}\zeta\omega_n
\]

## 4. URDF를 Python으로 가져오기

다음 코드는 실행 중인 Isaac Sim의 Script Editor 또는 Extension 안에서 사용할 수 있다. Standalone 파일이라면 앞에서 설명한 대로 이 import들보다 먼저 `SimulationApp`을 생성해야 한다.

```python
from pathlib import Path

import omni.kit.commands
from isaacsim.asset.importer.urdf import _urdf

urdf_path = Path("/absolute/path/to/robot.generated.urdf")
if not urdf_path.is_file():
    raise FileNotFoundError(urdf_path)

config = _urdf.ImportConfig()
config.convex_decomp = False
config.fix_base = False              # 모바일 로봇 예시
config.make_default_prim = True
config.self_collision = False
config.distance_scale = 1.0
config.density = 0.0

parsed, robot_model = omni.kit.commands.execute(
    "URDFParseFile",
    urdf_path=str(urdf_path),
    import_config=config,
)
if not parsed:
    raise RuntimeError(f"URDF parse 실패: {urdf_path}")

# 필요하면 parsed model의 joint drive를 여기서 로봇별로 조정한다.
for joint_name in robot_model.joints:
    joint = robot_model.joints[joint_name]
    print("parsed joint:", joint_name, joint)

imported, prim_path = omni.kit.commands.execute(
    "URDFImportRobot",
    urdf_robot=robot_model,
    import_config=config,
)
if not imported:
    raise RuntimeError("URDF import 실패")
print("robot prim:", prim_path)
```

별도 USD 파일로 생성해 현재 장면에서 reference하려면 `URDFParseAndImportFile` command에 `dest_path`를 지정하는 방식이 좋다. texture가 포함된 자산과 재사용 로봇은 in-memory Stage import보다 파일 자산으로 만든 뒤 reference하는 편이 낫다.

> Importer의 Python API와 command 인자는 버전 민감도가 높다. 5.1 프로젝트에서는 5.1 API 문서와 함께 고정하고, 다른 버전으로 옮길 때 import smoke test를 먼저 실행한다.

## 5. Xacro와 ROS 2 description

Xacro는 macro 언어이므로 Isaac Sim의 일반 URDF file importer가 직접 해석하는 입력으로 기대하지 않는다. 두 방법이 있다.

### 방법 A: 빌드 단계에서 펼치기

```bash
xacro my_robot.urdf.xacro prefix:=sim_ > build/my_robot.urdf
```

이 방법은 생성 URDF가 명시적으로 남고 CI에서 diff/lint하기 쉽다.

### 방법 B: ROS 2 node에서 가져오기

1. ROS 2 Jazzy workspace를 source한다.
2. `robot_state_publisher`가 `robot_description`을 제공하도록 launch한다.
3. 같은 환경에서 Isaac Sim을 시작하고 ROS 2 Bridge를 켠다.
4. `isaacsim.ros2.urdf` extension을 활성화한다.
5. `File > Import from ROS 2 URDF Node`에서 node 이름과 output directory를 지정한다.

ROS node importer는 description이 동적으로 생성되는 패키지에 편리하지만, 최종 생성 USD와 사용한 launch argument를 반드시 기록한다.

## 6. MJCF 가져오기

GUI에서는 `File > Import`에서 MJCF XML을 선택한다. Extension ID는 `isaacsim.asset.importer.mjcf`이다. 다음은 공식 5.1 command 흐름을 단순화한 예이다.

```python
from pathlib import Path
import omni.kit.commands

mjcf_path = Path("/absolute/path/to/robot.xml")
if not mjcf_path.is_file():
    raise FileNotFoundError(mjcf_path)

ok, config = omni.kit.commands.execute("MJCFCreateImportConfig")
if not ok:
    raise RuntimeError("MJCF import config 생성 실패")

config.set_fix_base(False)
config.set_import_inertia_tensor(True)
config.set_self_collision(False)
config.set_convex_decomp(False)
config.set_make_default_prim(True)

ok, _ = omni.kit.commands.execute(
    "MJCFCreateAsset",
    mjcf_path=str(mjcf_path),
    import_config=config,
    prim_path="/World/Robot",
)
if not ok:
    raise RuntimeError("MJCF import 실패")
```

MJCF의 body/site/actuator/default 상속 의미가 USD로 어떻게 매핑되었는지 점검한다. `merge_fixed_joints`, `import_sites`, `override_com`, `override_inertia` 같은 옵션은 topology와 동역학을 바꾸므로 기본값을 무심코 쓰지 않는다.

## 7. 가져온 직후 10분 검사

### 1단계: 눈으로 보기

1. Stage에서 로봇 root와 모든 link/joint가 예상한 계층에 있는지 확인한다.
2. `F`로 초점을 맞추고 크기를 확인한다.
3. Viewport의 Physics visualization에서 Colliders를 모두 표시한다.
4. collider가 visual에서 크게 벗어나거나 서로 파고들지 않는지 확인한다.
5. center of mass와 joint frame visualization을 켠다.

### 2단계: Play하기

1. fixed robot은 base가 떨어지지 않아야 한다.
2. moveable robot은 바닥 위에서 자연스럽게 지지되어야 한다.
3. 아무 명령 없이 joint가 폭발하거나 limit 밖으로 가지 않아야 한다.
4. self collision을 켤 필요가 있다면 link pair별로 천천히 검증한다.

### 3단계: metadata 출력하기

Script Editor에서 robot prim path를 맞추어 실행한다.

```python
import asyncio
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation


async def inspect_robot():
    world = World.instance() or World()
    await world.initialize_simulation_context_async()

    robot = SingleArticulation(
        prim_path="/World/Robot",
        name="imported_robot",
    )
    await world.reset_async()
    robot.initialize()

    print("num_dof:", robot.num_dof)
    print("dof_names:", list(robot.dof_names))
    print("dof_properties:\n", robot.dof_properties)
    print("q:", robot.get_joint_positions())


asyncio.ensure_future(inspect_robot())
```

DOF 개수·이름·순서가 controller와 ROS joint list의 기대와 같은지 확인한다. `dof_properties`의 limit, max velocity, max effort, stiffness와 damping을 원본과 비교한다.

## 8. Robot Setup 공식 학습 흐름을 실제 자산에 적용하기

Isaac Sim 5.1 Robot Setup 튜토리얼 13개는 다음 작업 흐름으로 이해하면 된다.

| 단계 | 적용할 작업 | 산출물/검증 |
|---:|---|---|
| 1. Stage Setup | Z-up, meter 단위, default prim, layer 구조를 정한다. | 빈 로봇 자산 골격 |
| 2. Assemble Simple Robot | visual, collider, rigid body, mass, physics material을 구성한다. | 물리 link 자산 |
| 3. Articulate Basic Robot | joint, drive와 articulation root를 구성한다. | 제어 가능한 articulation |
| 4. Add Camera and Sensors | 센서 prim과 fixed frame을 link 아래 배치한다. | 센서 포함 로봇 |
| 5. Rig Mobile Robot | moveable base, wheel axes, velocity drives와 마찰을 맞춘다. | AMR base |
| 6. Setup Manipulator | arm과 gripper 자산을 Robot Assembler 등으로 결합한다. | 조립된 manipulator |
| 7. Configure Manipulator | solver, gripper friction, effort limit, mimic, gain을 조정한다. | 안정적인 manipulation physics |
| 8. Generate Robot Config | Lula robot description/XRDF의 c-space, collision sphere, EE frame을 만든다. | motion generation config |
| 9. Pick and Place | target, controller와 gripper를 통합한다. | end-to-end grasp test |
| 10. Closed Loop | 닫힌 기구의 loop-closing constraint를 올바르게 분리한다. | 안정적인 폐루프 기구 |
| 11. Tune Joint Gains | step response로 Kp/Kd와 effort를 조정한다. | 검증된 drive parameter |
| 12. Asset Optimization | mesh, collider, layer와 instanceability를 최적화한다. | 배포 가능한 경량 자산 |
| 13. Legged Robot | moveable articulation, contact, joint order와 정책 actuator 계약을 맞춘다. | policy-ready legged asset |

각 튜토리얼의 숫자를 그대로 복사하기보다 자신의 로봇 mass, gear ratio, payload와 접촉 재질에 맞춰 측정하고 조정한다.

## 9. Robot Setup 도구 선택

| 도구 | 역할 | 사용할 때 |
|---|---|---|
| Robot Wizard (Beta) | 로봇 설정 흐름을 안내한다. | 처음 rigging할 때 누락을 줄인다. |
| Robot Assembler | 독립 articulation/asset을 고정 관계로 조립한다. | arm+gripper, base+sensor mast |
| Merge Mesh Utility | 많은 mesh를 병합한다. | draw call과 구조를 줄이되 편집성 손실을 감수할 때 |
| Gain Tuner | joint step response와 gain을 조정한다. | import 직후 또는 payload 변경 후 |
| Grasp Editor | gripper grasp pose를 authoring한다. | grasp pipeline 구성 |
| Lula Robot Description/XRDF Editor | collision sphere와 motion config를 만든다. | RMPflow, RRT, IK를 custom robot에 쓸 때 |
| Asset Validation | schema와 자산 구조 문제를 검사한다. | 배포/commit 전 |

Robot Assembler로 결합한 arm+gripper를 motion generation에서 쓸 때는 알고리즘이 읽는 URDF/XRDF에도 같은 kinematic chain과 EE offset이 있어야 한다. Stage만 조립하고 Lula description은 arm 단독으로 남기면 목표 pose와 collision sphere가 어긋난다.

## 10. Manipulator 설정 핵심

1. base 고정과 articulation root를 확인한다.
2. arm joint effort·velocity limit를 제조사 또는 actuator 모델에 맞춘다.
3. gripper fingertip에 별도 physics material을 적용한다.
4. mimic joint의 주 joint와 배율·offset을 확인한다.
5. arm과 gripper의 collider가 home pose에서 겹치지 않게 한다.
6. end-effector frame을 실제 TCP에 둔다.
7. 대표 payload와 최악 pose에서 gain을 시험한다.
8. 필요한 경우 solver position/velocity iteration을 올리되 성능을 측정한다.

공식 UR10e+2F-140 예제의 solver 수치나 마찰 1.0은 해당 실습의 시작점이지 모든 로봇의 정답이 아니다.

## 11. Mobile/legged 설정 핵심

### Mobile

- wheel joint axis와 wheel radius를 실제 collider 기준으로 측정한다.
- wheel drive는 velocity mode라면 stiffness 0, damping > 0으로 시작한다.
- 좌우 wheel name과 controller 순서를 고정한다.
- caster collider와 마찰이 base를 끌지 않는지 확인한다.
- 차체 root를 world에 고정하지 않는다.

### Legged

- 학습/배포 policy가 기대하는 joint name 순서와 `dof_names`가 정확히 같아야 한다.
- actuator Kp/Kd, effort/velocity limit와 action scale을 policy 설정과 맞춘다.
- foot collider와 contact material을 검증한다.
- base와 link 질량·관성이 원본 모델과 같아야 한다.
- self collision filter를 정책 학습 환경과 일치시킨다.

## 12. 자산 계층과 layer 전략

한 파일에 모든 변경을 넣지 않는다. 예를 들어 다음처럼 분리할 수 있다.

```text
my_robot/
  my_robot.usd                    # 외부에서 reference할 진입점
  configuration/
    my_robot_base.usd             # 계층·reference
    my_robot_physics.usd          # rigid/joint/drive/material override
    my_robot_sensors.usd          # camera/IMU/LiDAR prim
  meshes/
    visual/
    collision/
  materials/
  config/
    robot_descriptor.yaml
    robot.xrdf
    motion_policy.yaml
  source/
    my_robot.urdf.xacro
    my_robot.generated.urdf
```

Importer가 생성한 base layer를 직접 손으로 대량 수정하면 재import 때 사라진다. 가능한 후처리 override를 강한 layer에 두거나 스크립트로 재현한다.

## 13. 자동 smoke test 설계

최소한 다음 조건을 자동으로 검사한다.

```python
q = robot.get_joint_positions()
qd = robot.get_joint_velocities()

assert robot.num_dof == EXPECTED_DOF
assert list(robot.dof_names) == EXPECTED_DOF_NAMES
assert np.all(np.isfinite(q))
assert np.all(np.isfinite(qd))
assert np.max(np.abs(qd)) < 100.0
```

여기에 다음 episode를 추가한다.

- reset을 10회 반복해 pose가 같은지 확인한다.
- 각 joint를 limit 중앙 근처에서 작은 step으로 왕복한다.
- mobile base를 1 m 직진·90° 회전해 오차를 측정한다.
- gripper가 알려진 크기·질량의 물체를 일정 시간 유지하는지 확인한다.
- camera/IMU/contact sensor가 예상 frequency와 shape로 값을 내는지 확인한다.
- headless에서도 동일한 physics 결과 범위에 드는지 확인한다.

## 14. 검증 체크포인트

- [ ] 원본 description과 생성 USD, importer 설정을 함께 보관한다.
- [ ] scale, collider, mass/inertia, joint axis/limit, drive 순서로 검사했다.
- [ ] 고정형과 이동형 base 옵션을 올바르게 골랐다.
- [ ] `dof_names`를 controller 및 ROS joint list와 비교했다.
- [ ] custom end-effector를 조립한 뒤 URDF/XRDF도 함께 갱신했다.
- [ ] 자산을 독립 Stage와 headless smoke test에서 검증했다.
- [ ] 장면에서는 로봇 자산을 복사하지 않고 reference한다.

## 출처

- [Importers and Exporters](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/importers_exporters.html)
- [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [MJCF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_mjcf.html)
- [Robot Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/index.html)
- [Robot Wizard](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/robot_wizard.html)
- [Robot Setup Tutorials Series](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/index.html)
- [Tutorial 2: Assemble a Simple Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_assemble_robot.html)
- [Tutorial 5: Rig a Mobile Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html)
- [Tutorial 7: Configure a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html)
- [Tutorial 10: Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Tutorial 13: Rigging a Legged Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html)
- [Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)
- [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
