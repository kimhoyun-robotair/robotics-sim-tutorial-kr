# 11–22단계: 자산, 로봇, 센서를 하나씩 확인하다

이 장은 `v3.0.0-beta2.patch1`의 PhysX 물리 엔진, Isaac RTX 렌더러, Kit 화면을 기준으로 한다. 1–10단계에서 설치와 빈 장면 실행을 마쳤다고 가정한다. 실습은 **물체 한 개 → 로봇 한 대 → 센서 → 환경 복제** 순서로 진행한다. 처음부터 로봇 수와 카메라 해상도를 높이면 물리 문제와 메모리 문제를 구분하기 어렵다.

본문의 짧은 Python 블록은 해당 개념을 설명하는 발췌 또는 지정된 위치에 넣는 코드이다. 바로 실행할 전체 프로그램은 [`p02_stable_rigid.py`](../examples/p02_stable_rigid.py), [`p03_hold_franka.py`](../examples/p03_hold_franka.py), [`p04_camera_check.py`](../examples/p04_camera_check.py)와 명시한 공식 스크립트를 사용한다.

새 터미널에서는 설치 단계의 가상환경을 활성화하고 다음 변수를 설정한다.

```bash
export ISAACLAB_ROOT="$HOME/IsaacLab"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
mkdir -p "$TUTORIAL_ROOT/isaaclab_tutorial/outputs"
cd "$ISAACLAB_ROOT"
git describe --tags --exact-match
```

태그는 `v3.0.0-beta2.patch1`이어야 한다. 다른 버전에서 코드가 돌아간다는 사실만으로 이 장과 같은 API라고 판단하지 않는다. 특히 2.x 예제의 quaternion과 데이터 쓰기 함수를 그대로 섞지 않는다.

<a id="step-11"></a>

## 11단계. USD와 Prim으로 자산 구조 읽기

USD는 장면을 구성하는 데이터 형식이다. 로봇의 겉모양뿐 아니라 링크의 배치, 재질, 충돌 형상, 관절, 다른 USD 파일 참조를 한 장면에 표현한다. **Prim**은 USD 장면의 한 항목이고, `/World/Franka` 같은 문자열은 파일 경로가 아니라 장면 내부의 경로이다.

다음 세 가지를 먼저 구분한다.

| 항목 | 역할 | 실습에서 확인할 곳 |
|---|---|---|
| `Xform` | 다른 항목을 묶고 위치·회전을 지정하다 | Stage 트리의 상위 노드 |
| `Mesh`, `Cube` 등 | 화면에 보이는 형상을 표현하다 | Viewport와 Geometry 속성 |
| 물리 schema | 질량·충돌·관절 등의 물리 정보를 추가하다 | Physics 속성, 충돌 표시 |

화면에 로봇이 보이는 것만으로 제어 가능한 articulation이 완성된 것은 아니다. 시각 형상만 있는 USD라면 중력도 관절 제어도 동작하지 않을 수 있다. 반대로 시각 형상을 감추어도 충돌 형상이 남아 있으면 다른 물체와 부딪힌다.

1. 13단계 또는 16단계 프로그램을 `--viz kit`으로 실행한다.
2. Stage 트리에서 `/World`를 펼친다.
3. `Box` 또는 `Franka`를 선택하고 자식 노드를 펼친다.
4. 위치와 회전 항목, 물리 관련 항목이 어느 노드에 붙어 있는지 확인한다.
5. 실행 중인 로봇의 링크를 마우스로 옮기며 원본 자산을 수정하지 않는다. 장면을 다시 실행해서 같은 상태를 재현하는 쪽으로 실습한다.

USD를 코드로 읽는 경우에는 이미 실행된 Kit 안에서 아래처럼 확인한다. 예를 들어 복사한 p03 프로그램의 `sim.reset()` 다음에 넣을 수 있다.

```python
from isaaclab.sim.utils.stage import get_current_stage
from pxr import UsdPhysics

stage = get_current_stage()
for prim in stage.Traverse():
    if str(prim.GetPath()).startswith("/World/Franka"):
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            print("articulation root:", prim.GetPath())
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            print("rigid link:", prim.GetPath())
```

`UsdFileCfg`는 기존 USD를 참조해서 불러오는 설정이다. `RigidObjectCfg`는 강체 상태를 읽고 쓰기 위한 설정이고, `ArticulationCfg`는 관절로 연결된 로봇과 actuator를 다루기 위한 설정이다. `UsdFileCfg` 하나가 이 세 역할을 모두 대신하지는 않는다.

```python
# 설명용: 이미 AppLauncher를 실행한 프로그램 안에서 사용하다.
from isaaclab.assets import Articulation
from isaaclab_assets import FRANKA_PANDA_HIGH_PD_CFG

robot_cfg = FRANKA_PANDA_HIGH_PD_CFG.replace(prim_path="/World/Franka")
print(robot_cfg.spawn.usd_path)  # 참조하는 공식 자산 주소
robot = Articulation(robot_cfg)
```

처음에는 공식 로봇 설정을 복사해서 경로만 바꾼다. 다른 USD 파일로 교체할 때는 관절 이름, articulation root, 고정 베이스 여부, 충돌 형상과 관성까지 다시 확인해야 한다.

확인할 공식 자료는 [새 로봇 추가 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/add_new_robot.py)와 [Franka 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_assets/isaaclab_assets/robots/franka.py)이다.

<a id="step-12"></a>

## 12단계. 좌표계·단위·XYZW quaternion 확인

이 튜토리얼의 길이는 m, 시간은 s, 회전 관절 위치는 rad를 사용한다. 손가락처럼 직선으로 움직이는 관절 위치는 m이다. 같은 `joint_pos` 배열 안에도 회전 관절과 직선 관절이 함께 들어갈 수 있다.

Isaac Lab 3.0의 quaternion 순서는 **`(x, y, z, w)`**이다. 회전하지 않은 상태는 `(0, 0, 0, 1)`이다. 예전 Isaac Lab 2.x의 `(1, 0, 0, 0)`을 그대로 넣으면 같은 자세가 아니다. [공식 3.0 마이그레이션 안내](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/migration/migrating_to_isaaclab_3-0.rst)

| 의미 | Isaac Lab 3.0 값 |
|---|---|
| 항등 회전 | `(0.0, 0.0, 0.0, 1.0)` |
| Z축으로 90도 회전 | `(0.0, 0.0, 0.70710678, 0.70710678)` |
| root pose 배열 | `[x, y, z, qx, qy, qz, qw]` |
| root velocity 배열 | `[vx, vy, vz, wx, wy, wz]` |

다음은 초기화 후 상태를 검사하는 발췌이다. `.torch`는 Isaac Lab의 `ProxyArray`를 PyTorch에서 읽도록 명시하는 접근자이다.

```python
pose = robot.data.root_pose_w.torch
position = pose[:, :3]
quaternion = pose[:, 3:7]

print("position:", position)
print("quaternion xyzw:", quaternion)
norm = torch.linalg.vector_norm(quaternion, dim=-1)
if not torch.all(torch.abs(norm - 1.0) < 0.01):
    raise RuntimeError("단위 quaternion인지 확인하다.")
```

`_w`는 world 좌표계에서 표현한 값이라는 뜻이다. 부모 노드가 이동해도 world 좌표와 부모 기준 좌표를 혼동해서는 안 된다. 환경을 여러 개 복제했을 때 중요한 차이는 17단계에서 다시 다룬다.

카메라는 회전 성분의 순서와 광학 축 방향을 별도로 확인한다.

| 카메라 `convention` | 앞 방향 | 위 방향 |
|---|---|---|
| `"ros"` | +Z | -Y |
| `"opengl"` | -Z | +Y |
| `"world"` | +X | +Z |

여기서 `"ros"`는 카메라 좌표계 표기 방식이며 ROS 설치를 요구하는 옵션이 아니다. 로봇의 앞 방향을 카메라의 +Z라고 막연히 가정하지 않는다. 카메라가 바닥만 보거나 로봇 내부를 볼 때는 조명보다 먼저 위치·방향을 확인한다. [CameraCfg의 좌표계 정의](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/camera_cfg.py)

<a id="step-13"></a>

## 13단계. 미니 프로젝트 2: 상자 낙하와 정착

**목표:** 20 cm 상자 하나를 50 cm 높이에서 떨어뜨리고, 바닥 위에 정착하는지 수치로 확인한다. 같은 프로그램 안에서 초기화를 두 번 수행한다.

이 예제의 바닥은 두께가 있는 정적 상자이며, 윗면이 `z=0`이다. 바닥에는 충돌 속성을 넣고 동적 강체 속성을 넣지 않아 제자리에 고정한다. 외부 ground USD를 내려받지 않으므로 첫 물리 실습에서 자산 다운로드 문제를 줄일 수 있다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p02_stable_rigid.py" \
  --device cuda:0 --viz kit --steps 600 \
  --output "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/p02.json"
```

1. 창이 열리고 장면 로딩이 끝날 때까지 기다린다.
2. 초록색 상자가 내려와 바닥 위에 멈추는지 확인한다.
3. 중간에 다시 위로 올라가는 것은 의도한 reset이다.
4. 프로그램이 600개 물리 스텝을 완료한 뒤 종료되는지 확인한다.
5. 터미널의 `[SETTLED]` 두 줄과 마지막 `[PASS]`를 확인한다.

`dt=1/120`에서 600스텝은 시뮬레이션 시간 5초이다. 최초 실행에서는 셰이더 준비 등에 시간이 들 수 있으므로 실제 대기 시간이 5초일 필요는 없다.

다음은 전체 파일에서 상자를 만드는 핵심 부분이다.

```python
from isaaclab.assets import RigidObjectCfg
from isaaclab_physx.sim.schemas import (
    PhysxCollisionPropertiesCfg,
    PhysxRigidBodyPropertiesCfg,
)

box_cfg = RigidObjectCfg(
    prim_path="/World/Box",
    spawn=sim_utils.CuboidCfg(
        size=(0.2, 0.2, 0.2),
        rigid_props=PhysxRigidBodyPropertiesCfg(disable_gravity=False),
        collision_props=PhysxCollisionPropertiesCfg(),
        mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
    ),
    init_state=RigidObjectCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.5),
        rot=(0.0, 0.0, 0.0, 1.0),
    ),
)
```

상자 중심 높이가 0.5 m이고 높이가 0.2 m이므로 시작할 때 바닥과 겹치지 않는다. 정착한 뒤 중심 높이는 약 0.1 m이어야 한다. 중심을 `z=0`에 놓으면 상자의 절반이 바닥 속에 들어간 상태로 시작하므로 접촉 보정 과정에서 튀는 원인이 된다.

전체 프로그램은 다음 조건을 검사한다. 아래 수치는 이 단순 장면을 위한 검사 기준이지 모든 로봇의 공통 기준은 아니다.

| 검사 | 기준 |
|---|---|
| 위치·자세·속도 | NaN과 inf가 없어야 하다 |
| 시뮬레이션 중 상자 높이 | `0.07 < z < 0.65` m |
| 정착 높이 | `abs(z - 0.1) < 0.015` m |
| 정착 선속도 크기 | `0.1 m/s` 미만 |
| 정착 각속도 크기 | `0.2 rad/s` 미만 |
| quaternion 크기 | 1과의 차이가 0.01 미만 |

정착 높이·선속도·각속도는 두 낙하 구간 각각의 마지막 30스텝 전체에서 확인한다. 한 시점에서만 속도가 우연히 작아진 상태와 계속 정착해 있는 상태를 구분하기 위한 조건이다. JSON에는 각 검사 구간의 최대 높이 오차와 최대 선속도·각속도를 기록한다. 이 기준은 예제를 위해 정한 시운전 기준이며 GPU 실측으로 보정한 허용치나 모든 진동을 검출하는 보증은 아니다.

실행 결과 JSON은 성공했을 때만 기록한다. 이전 실행의 JSON이 이미 있다면 수정 시각과 터미널 종료 코드를 함께 확인한다. JSON 파일이 존재한다는 사실만으로 이번 실행이 성공한 것은 아니다.

문제가 생기면 바닥 충돌, 초기 겹침, 길이 단위 순서로 확인한다. 질량을 0으로 바꾸거나 감쇠를 지나치게 높여서 문제를 감추지 않는다. 원본 예제는 [공식 강체 튜토리얼](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/run_rigid_object.py)이고, 이 저장소 예제는 무작위 원뿔 대신 정착 높이를 검사하기 쉬운 상자로 범위를 줄였다.

<a id="step-14"></a>

## 14단계. 물리 스텝·reset·버퍼 갱신 순서

Isaac Lab에서 Python 변수에 목표값을 넣었다고 로봇이 즉시 움직이는 것은 아니다. 기본적인 한 주기는 다음과 같다.

1. 관절 목표나 힘을 내부 버퍼에 기록한다.
2. `write_data_to_sim()`으로 시뮬레이터에 보낸다.
3. `sim.step()`으로 물리를 한 번 진행한다.
4. `update(dt)`로 새 상태를 읽을 수 있도록 자산 또는 장면 버퍼를 갱신한다.

```python
robot.set_joint_position_target_index(target=q_target)
robot.write_data_to_sim()
sim.step()
robot.update(sim_dt)

q_measured = robot.data.joint_pos.torch
```

`set_joint_position_target_index()`의 이름에 `target`이 들어가는 이유는 물리 상태 자체를 순간이동시키는 함수가 아니기 때문이다. 반면 `write_joint_position_to_sim_index(position=...)`는 관절 상태를 직접 설정하는 함수이므로 주로 reset에 사용한다. 매 스텝 상태를 강제로 덮어쓰면 제어 성능을 확인할 수 없다.

3.0에서는 위치·속도 쓰기와 대상 선택을 명시한다. 2.x 코드를 찾았을 때 다음처럼 읽는다.

| 작업 | 이 장에서 사용하는 3.0 호출 |
|---|---|
| root 위치·자세 초기화 | `write_root_pose_to_sim_index(root_pose=pose)` |
| root 속도 초기화 | `write_root_velocity_to_sim_index(root_velocity=vel)` |
| 관절 위치 초기화 | `write_joint_position_to_sim_index(position=q)` |
| 관절 속도 초기화 | `write_joint_velocity_to_sim_index(velocity=qd)` |
| 관절 위치 목표 지정 | `set_joint_position_target_index(target=q_target)` |

`_index` 함수는 환경·관절 인덱스로 대상을 고르고, `_mask` 함수는 전체 환경 데이터와 boolean mask를 사용한다. 처음에는 모든 환경을 대상으로 하는 `_index` 호출부터 익힌다. 부분 reset은 선택한 데이터의 행 수와 `env_ids` 길이를 맞춘 뒤 확장한다. [공식 데이터 쓰기 API 변경](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/migration/migrating_to_isaaclab_3-0.rst)

초기값을 직접 수정하지 않도록 `.clone()`을 사용한다.

```python
q = robot.data.default_joint_pos.torch.clone()
qd = robot.data.default_joint_vel.torch.clone()
robot.write_joint_position_to_sim_index(position=q)
robot.write_joint_velocity_to_sim_index(velocity=qd)
robot.reset()
```

`.reset()`만 호출했다고 관절이 원하는 초기 위치로 순간 이동한다고 가정하지 않는다. 위 예제에서는 물리 상태를 먼저 쓰고 내부 버퍼를 초기화한다. 센서 이력도 사용한다면 `scene.reset()` 또는 해당 센서의 `reset()`을 함께 처리한다.

속도는 위치 차분으로 계산하는 경우가 있으므로 위치만 바꾸고 속도·이력을 남기면 reset 직후 큰 값이 나타날 수 있다. 실습에서는 위치와 속도를 한 쌍으로 초기화하고 첫 센서 프레임을 정상 프레임과 구분한다.

<a id="step-15"></a>

## 15단계. Articulation과 actuator 설정 읽기

Articulation은 관절로 연결된 링크를 하나의 시스템으로 다루는 방식이다. 로봇 팔에서는 베이스, 여러 링크, 관절, 그리퍼가 이에 해당한다. 관절은 움직일 수 있는 방향과 범위를 정하고 actuator는 그 관절을 어떻게 구동할지 정한다.

공식 Franka 설정은 관절 이름 패턴으로 actuator 그룹을 나눈다.

```python
from isaaclab.actuators import ImplicitActuatorCfg

shoulder = ImplicitActuatorCfg(
    joint_names_expr=["panda_joint[1-4]"],
    effort_limit_sim=87.0,
    stiffness=400.0,
    damping=80.0,
    armature=1e-3,
)
```

이는 설명용으로 구성한 high-PD 어깨 그룹이며, 전체 실습은 공식 `FRANKA_PANDA_HIGH_PD_CFG`를 사용한다. 상완과 전완의 토크 한계를 같은 값으로 바꾸지 않는다. 공식 설정은 `panda_joint[5-7]` 그룹의 `effort_limit_sim`을 12로 두고 있다. 손가락은 직선 관절이므로 팔 회전 관절과 단위도 다르다. [공식 Franka actuator 정의](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_assets/isaaclab_assets/robots/franka.py)

PD 제어를 이해할 때는 다음 식을 출발점으로 삼는다.

```text
구동 힘/토크 ≈ stiffness × (목표 위치 - 현재 위치)
             + damping × (목표 속도 - 현재 속도)
```

`ImplicitActuatorCfg`에서는 시뮬레이터의 관절 구동기가 이를 처리한다. 위 식은 개념 설명이며, 실제 솔버의 이산화와 한계 처리까지 모두 표현한 식은 아니다.

| 설정 | 의미 | 잘못 바꿨을 때 확인할 현상 |
|---|---|---|
| `stiffness` | 위치 오차에 대한 반응 | 너무 낮으면 처짐, 너무 높으면 스텝 크기와 함께 진동 확인 |
| `damping` | 속도 차이에 대한 반응 | 감쇠 부족으로 진동하거나 움직임이 지나치게 느려질 수 있다 |
| `effort_limit_sim` | 시뮬레이터가 허용하는 힘·토크 한계 | 너무 낮으면 목표를 따라가지 못하다 |
| `joint_names_expr` | 적용할 관절 이름 패턴 | 일부 관절을 놓치거나 잘못된 관절을 제어하다 |
| `fix_root_link` | 베이스를 월드에 고정하는 설정 | 탁상용 팔의 베이스까지 움직이다 |

로봇이 무너지면 stiffness만 높이지 않는다. articulation root가 맞는지, 고정 베이스가 필요한지, 관절 이름이 실제 USD와 맞는지, 초기 자세가 충돌하지 않는지부터 확인한다. 팔의 관절을 모두 0으로 초기화하는 방법은 이 Franka 예제의 초기 자세를 대신할 수 없다.

3.0은 공통 자산 API와 backend별 물리 속성 설정을 나누었다. 이 장의 새 코드는 PhysX 전용 설정을 다음 경로에서 가져온다.

```python
from isaaclab.assets import Articulation, RigidObject
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.sim.schemas import (
    PhysxArticulationRootPropertiesCfg,
    PhysxCollisionPropertiesCfg,
    PhysxRigidBodyPropertiesCfg,
)
```

공식 예제 일부에 `sim_utils.RigidBodyPropertiesCfg` 같은 이전 이름이 남아 있어도 새 코드의 기준은 위 경로로 삼는다. 호환용 별칭이 존재하는 것과 앞으로 권장되는 이름은 구분한다. 다른 물리 backend로 바꿀 때 PhysX 전용 필드가 그대로 동작한다고 가정하지 않는다.

<a id="step-16"></a>

## 16단계. 미니 프로젝트 3: Franka 초기 자세 유지

**목표:** Franka 한 대의 베이스를 고정하고 공식 초기 관절 자세를 유지한다. root 이동과 관절 오차를 기록하고 두 번의 reset을 통과한다.

이 실습은 공식 `FRANKA_PANDA_HIGH_PD_CFG`에 맞춰 **로봇 링크의 중력을 비활성화**한다. 이를 명시하는 이유는 자산 로딩, 관절 매칭, 목표 전송, 고정 베이스를 먼저 확인하기 위해서이다. 이 결과가 실제 하중을 들어 올리는 성능이나 중력 보상 성능을 의미하지는 않는다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p03_hold_franka.py" \
  --device cuda:0 --viz kit --steps 600 \
  --output "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/p03.json"
```

1. 최초 실행에서는 공식 Franka USD와 관련 자산의 로딩을 기다린다.
2. 로봇 베이스가 바닥에 있고 링크가 분리되어 날아가지 않는지 확인한다.
3. 손가락이 열린 초기 자세에서 팔이 가만히 있는지 확인한다.
4. 터미널에서 실제 `joints=` 목록을 읽는다.
5. `fixed_base=True`, `gravity_on_robot=False`를 확인한다.
6. `[HOLD]`에 표시되는 관절 오차와 root 이동이 허용 범위 안인지 확인한다.

전체 파일은 고정 베이스를 아래처럼 명시한다.

```python
robot_cfg.spawn.articulation_props = PhysxArticulationRootPropertiesCfg(
    fix_root_link=True,
    enabled_self_collisions=True,
    solver_position_iteration_count=8,
    solver_velocity_iteration_count=2,
)
robot_cfg.spawn.rigid_props = PhysxRigidBodyPropertiesCfg(
    disable_gravity=True,
    max_depenetration_velocity=1.0,
)
```

고정 베이스는 베이스가 움직이지 않는다는 의미이고, 중력 비활성화는 링크에 중력을 가하지 않는다는 의미이다. 둘은 별개의 설정이다. 고정 베이스 로봇이라도 링크에는 중력이 작용할 수 있다.

프로그램은 `robot.is_fixed_base`가 참인지 확인하고, 관절 위치·속도·root 자세의 유한성, 초기 목표와의 관절 오차, root 이동을 매 스텝 검사한다. 관절은 이름으로 팔 7개와 손가락 2개를 찾고, 수가 맞지 않으면 중단한다. 회전과 직선 관절의 단위를 섞어 하나의 최대 오차로 보고하지 않는다.

| 항목 | 이 실습의 시운전 기준 |
|---|---|
| 팔 관절 위치 오차 | `0.05 rad` 미만 |
| 손가락 관절 위치 오차 | `0.005 m` 미만 |
| root 이동 | `0.005 m` 미만 |
| reset 후 60스텝이 지난 뒤 팔 관절 속도 | `0.5 rad/s` 미만 |
| reset 후 60스텝이 지난 뒤 손가락 관절 속도 | `0.05 m/s` 미만 |

위 기준은 중력이 비활성화된 정지 목표 실습을 위해 작성한 값이며 GPU 실측으로 보정한 성능 규격은 아니다. 속도 검사를 두어 목표 근처에서 계속 흔들리는 경우도 확인한다. JSON에는 팔·손가락의 최대 위치 오차, 준비 구간 이후 최대 속도, 최대 root 이동을 단위별로 기록한다. 정밀 조작 작업에서는 허용 오차와 관측 시간도 그 작업에 맞게 다시 정해야 한다.

다음처럼 기본 목표를 **복사**해서 사용한다.

```python
q_target = robot.data.default_joint_pos.torch.clone()
qd_zero = torch.zeros_like(robot.data.default_joint_vel.torch)

robot.set_joint_position_target_index(target=q_target)
robot.set_joint_velocity_target_index(target=qd_zero)
robot.write_data_to_sim()
sim.step()
robot.update(sim_dt)
```

창이 열렸지만 팔이 보이지 않으면 USD 참조 로딩 오류가 있는지 로그부터 확인한다. `robot.is_fixed_base` 검사에서 멈추면 렌더링 옵션을 바꾸기보다 USD의 articulation과 고정 관절을 확인한다. 팔이 진동하면 이 예제의 초기 자세·시간 간격·actuator 설정으로 되돌린 뒤 변경한 항목을 하나씩 다시 적용한다.

심화 과제에서는 공식 `FRANKA_PANDA_CFG`와 중력 활성화 상태를 따로 실험하고 목표 오차를 비교한다. 그때는 중력 보상과 제어기 설정에 맞는 새로운 판정 기준을 정한다. 여기의 `[PASS]` 기준을 설명 없이 복사해서 쓰지 않는다.

<a id="step-17"></a>

## 17단계. 환경 복제와 `env_origins`

강화학습에서는 같은 작업 공간을 여러 개 만들어 한 번에 경험을 수집한다. `InteractiveScene`은 이런 환경을 배치하고 자산·센서 업데이트를 묶어서 처리한다.

먼저 공식 장면 예제를 환경 두 개로 실행한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/tutorials/02_scene/create_scene.py \
  --num_envs 2 --device cuda:0 --viz kit
```

이 예제는 Cartpole에 무작위 힘을 가하는 제어 인터페이스 실습이다. 막대가 서 있지 못하는 현상 자체를 고장으로 판단하지 않는다. 16단계의 Franka 자세 유지 실습과 목표가 다르다. [공식 장면 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/02_scene/create_scene.py)

장면 설정에서 `{ENV_REGEX_NS}`는 복제한 환경 경로에 맞는 패턴으로 바뀐다.

```python
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab_assets import FRANKA_PANDA_HIGH_PD_CFG

@configclass
class TwoArmSceneCfg(InteractiveSceneCfg):
    robot = FRANKA_PANDA_HIGH_PD_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )

# 실제 scene을 생성할 때의 설정 예이다.
scene_cfg = TwoArmSceneCfg(num_envs=2, env_spacing=3.0)
```

핵심은 reset할 때 world 좌표를 올바르게 만드는 것이다. 두 환경에서 같은 로컬 초기 위치를 사용해도 world 위치는 달라야 한다.

```python
root_pose = scene["robot"].data.default_root_pose.torch.clone()
root_pose[:, :3] += scene.env_origins
scene["robot"].write_root_pose_to_sim_index(root_pose=root_pose)

root_velocity = scene["robot"].data.default_root_vel.torch.clone()
scene["robot"].write_root_velocity_to_sim_index(root_velocity=root_velocity)
```

`env_origins`를 빼먹으면 reset 뒤 모든 로봇이 world 원점에 겹칠 수 있다. 반대로 기본 데이터를 복사하지 않고 원점 이동을 반복해서 더하면 reset할 때마다 멀리 이동하는 문제가 생길 수 있다.

완료 확인은 화면만 보지 않고 아래 값으로도 한다.

```python
world_position = scene["robot"].data.root_pos_w.torch
local_position = world_position - scene.env_origins
print("world:", world_position)
print("local:", local_position)
```

환경들의 world 위치는 서로 떨어져 있고, 동일한 초기화 직후의 local 위치는 거의 같아야 한다. 환경 간 충돌 필터 설정도 별도로 확인한다. 단순히 `env_spacing`을 크게 만드는 것만으로 모든 충돌 분리가 보장되는 것은 아니다.

<a id="step-18"></a>

## 18단계. 미니 프로젝트 4 준비: 센서와 렌더러 구분

**목표:** RGB·깊이 카메라, 접촉 센서, 높이 스캐너가 무엇을 측정하는지 구분하고 각각의 출력을 검사한다. 19–22단계를 묶어 하나의 센서 실습으로 진행한다.

| 장치 | 결과 | 이 장의 계산 경로 | 조명이 필요한가 |
|---|---|---|---|
| Viewport | 사람이 보는 장면 | Kit 화면과 렌더링 | 장면을 볼 때 필요하다 |
| `Camera` | RGB, 깊이 등 영상 배열 | Isaac RTX 렌더러 | RGB에 필요하다 |
| `ContactSensor` | 물체가 받는 접촉 힘 | 물리 엔진 | 필요하지 않다 |
| `RayCaster` | 지정 mesh와 광선의 교차 위치 | Warp ray casting | 필요하지 않다 |

Viewport가 멀쩡하다고 센서 카메라도 올바른 방향을 본다는 뜻은 아니다. 반대로 GUI를 끈 상태에서도 카메라 센서의 렌더링은 실행할 수 있다.

3.0의 카메라 설정은 센서와 렌더러를 분리한다.

```python
from isaaclab.sensors import CameraCfg
from isaaclab_physx.renderers import IsaacRtxRendererCfg

camera_cfg = CameraCfg(
    prim_path="/World/Camera",
    height=120,
    width=160,
    update_period=0.0,
    data_types=["rgb", "distance_to_image_plane"],
    renderer_cfg=IsaacRtxRendererCfg(depth_clipping_behavior="none"),
    spawn=sim_utils.PinholeCameraCfg(clipping_range=(0.05, 20.0)),
)
```

`height`, `width`, 데이터 종류는 무엇을 측정할지 정하고, `renderer_cfg`는 어떤 렌더러로 영상을 만들지 정한다. `depth_clipping_behavior` 같은 RTX 전용 옵션은 렌더러 설정에 넣는다.

이 태그에서는 **`CameraCfg`가 tiled rendering 최적화를 포함**한다. 이전 자료의 `TiledCameraCfg`를 별도의 최신 고속 카메라라고 소개하지 않는다. 해당 클래스에는 `CameraCfg`를 사용하라는 deprecation 안내가 있다. [Camera 공식 개념 문서](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/overview/core-concepts/sensors/camera.rst), [TiledCameraCfg 원본](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/tiled_camera_cfg.py)

| 실행 목적 | 옵션 |
|---|---|
| 물리와 GUI 확인 | `--viz kit` |
| GUI 없이 물리 검사 | `--viz none` |
| GUI와 RTX 카메라 | `--viz kit --enable_cameras` |
| GUI 없이 RTX 카메라 저장 | `--viz none --enable_cameras` |

`--viz none`은 모든 visualizer를 끄는 옵션이다. `--enable_cameras`와 함께 사용하면 카메라 계산까지 끄는 뜻이 아니다. 이전 `--headless` 옵션은 호환용으로 남아 있지만 이 튜토리얼은 `--viz`를 사용한다. [AppLauncher 원본](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/app/app_launcher.py)

Newton Warp renderer와 Isaac RTX renderer는 지원하는 출력이 같지 않다. 이 장의 `distance_to_image_plane`와 RTX annotator 설명을 다른 렌더러에 그대로 적용하지 않는다. 처음에는 한 카메라·낮은 해상도로 확인한 뒤 수를 늘린다.

<a id="step-19"></a>

## 19단계. RGB·깊이 카메라 수집

먼저 이 저장소의 유한 스텝 카메라 검사 프로그램을 실행한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p04_camera_check.py" \
  --device cuda:0 --viz none --enable_cameras --steps 120 \
  --output-dir "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/camera"
```

결과 디렉터리에서 다음 파일을 확인한다.

| 파일 | 용도 |
|---|---|
| `rgb.png` | 사람이 직접 확인할 RGB 영상 |
| `rgb.npy` | RGB 배열을 다시 분석할 자료 |
| `depth.npy` | 단위를 보존한 깊이 자료 |
| `camera_report.json` | 카메라 검사 지표 |

`rgb.png`를 열어 물체가 예상 위치에 보이는지 확인한다. 깊이는 검은색·흰색으로만 보이는 그림보다 숫자로 확인하는 편이 정확하다. 깊이 `.npy`를 RGB 사진처럼 해석해서는 안 된다.

아래는 카메라 업데이트 후 배열을 읽는 발췌이다.

```python
sim.step()
camera.update(sim.get_physics_dt())

rgb = camera.data.output["rgb"].torch
depth = camera.data.output["distance_to_image_plane"].torch
print("rgb:", rgb.shape, rgb.dtype)
print("depth:", depth.shape, depth.dtype)

valid = torch.isfinite(depth) & (depth > 0)
print("valid depth ratio:", valid.float().mean().item())
if valid.any():
    print("valid range [m]:", depth[valid].min().item(), depth[valid].max().item())
```

RGB는 일반적으로 `(카메라 수, 높이, 너비, 3)`이고 깊이는 `(카메라 수, 높이, 너비, 1)` 배열이다. 실제 `shape`와 `dtype`는 실행해서 확인한다. `CameraData`의 각 출력도 `ProxyArray`이므로 명시적으로 `.torch`에 접근한다. [CameraData 정의](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/camera_data.py)

`distance_to_image_plane`은 카메라 영상면에 수직인 방향의 깊이이며, `distance_to_camera`처럼 카메라 중심에서의 유클리드 거리와 구분한다. 화면 가장자리에서는 같은 점이라도 두 값이 다를 수 있다.

하늘을 보는 픽셀이나 측정 범위 밖 픽셀에 `inf`가 있는 것은 정의된 무효 깊이일 수 있다. 이를 무조건 0으로 바꾼 뒤 정상이라고 보고하지 않는다. 원본 깊이를 저장하고, 유효 픽셀 비율과 유효 깊이 범위를 따로 기록한다. 정확한 판정은 카메라 앞에 놓인 기준 물체가 차지하는 영역과 예상 거리로 수행한다.

다양한 annotator를 더 보려면 공식 예제를 별도로 실행한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/tutorials/04_sensors/run_usd_camera.py \
  --device cuda:0 --viz kit --enable_cameras --camera_id 0 --save
```

이 공식 예제는 카메라 두 개를 만들고 RGB·깊이·법선·분할 정보를 출력한다. `--camera_id`는 저장하거나 점군을 표시할 카메라를 고르는 옵션이며 카메라 생성 개수를 줄이는 옵션이 아니다. 출력은 공식 스크립트가 있는 디렉터리 아래 `output/camera`에 저장된다. 충분히 확인했으면 창을 닫거나 터미널에서 종료한다.

처음부터 `--draw`까지 켜지 않는다. RGB·깊이 수집을 먼저 확인한 뒤 점군 표시를 추가한다. 공식 코드에도 초기 몇 스텝 동안 점군이 비어 있을 수 있어 비어 있지 않을 때만 표시하는 처리가 있다. [공식 USD 카메라 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_usd_camera.py)

<a id="step-20"></a>

## 20단계. 접촉 센서 힘 읽기

접촉 센서는 카메라처럼 장면을 촬영하지 않는다. 강체가 다른 물체와 접촉할 때의 힘을 읽는다. 물체가 화면에서 바닥에 닿아 보여도 contact reporting이 활성화되지 않으면 센서가 올바르게 준비되지 않을 수 있다.

다음 두 설정을 한 쌍으로 생각한다.

```python
# 로봇을 생성하기 전에 해당 자산의 contact reporting을 활성화하다.
robot_cfg.spawn.activate_contact_sensors = True

# 실제 강체 링크 경로와 일치해야 하다.
from isaaclab.sensors import ContactSensorCfg
contact_cfg = ContactSensorCfg(
    prim_path="{ENV_REGEX_NS}/Robot/.*_FOOT",
    update_period=0.0,
    history_length=6,
    debug_vis=True,
)
```

`.*_FOOT`는 ANYmal의 발 링크를 대상으로 하는 공식 예제의 패턴이다. Franka에는 같은 이름이 없으므로 그대로 붙여 넣지 않는다. 센서가 감시하는 body 수가 예상과 맞는지 출력으로 확인한다.

통합 센서 예제는 무작위 초기 관절 노이즈를 추가한다. 안정된 시작 상태를 먼저 비교하기 위해 원본을 복사하고 그 한 줄을 제거한다. 해상도도 줄인다. 다음 코드는 수정할 문자열이 실제로 한 번 존재하는지 확인하고, 맞지 않으면 중단한다.

```bash
cp "$ISAACLAB_ROOT/scripts/tutorials/04_sensors/add_sensors_on_robot.py" \
  "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/sensors_no_noise.py"

python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["TUTORIAL_ROOT"]) / "isaaclab_tutorial/outputs/sensors_no_noise.py"
text = path.read_text(encoding="utf-8")
changes = {
    "            joint_pos += torch.rand_like(joint_pos) * 0.1\n": "",
    "        height=480,": "        height=120,",
    "        width=640,": "        width=160,",
}
for old, new in changes.items():
    if text.count(old) != 1:
        raise SystemExit(f"예상한 공식 소스와 다르다: {old!r}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
PY

cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/sensors_no_noise.py" \
  --num_envs 1 --device cuda:0 --viz kit --enable_cameras
```

이 수정은 시작 상태의 무작위 관절 오차만 제거한다. 실제 물리·제어·접촉 모델 전체의 노이즈가 사라진다고 주장하지 않는다. ANYmal의 기본 actuator와 초기 자세는 그대로 사용한다.

복사한 파일의 센서 정보 출력 부분에서 다음 계산을 추가하면 힘의 방향과 크기를 구분하기 쉽다.

```python
forces = scene["contact_forces"].data.net_forces_w.torch
magnitudes = torch.linalg.vector_norm(forces, dim=-1)
print("force vectors [N]:", forces)
print("force magnitudes [N]:", magnitudes)
print("finite:", torch.isfinite(forces).all().item())
```

`torch.max(forces)`는 모든 성분 중 가장 큰 성분이다. 힘 벡터의 크기를 보고 싶다면 위처럼 마지막 XYZ 축의 norm을 계산한다. 정착 이후 발의 접촉력이 유한하게 나오는지 보고, 충돌 순간의 peak와 정착한 뒤의 값을 분리해서 해석한다.

여러 접촉점·물체를 가진 로봇에서 모든 힘의 합을 무조건 `m × 9.81`과 동일하다고 판정하지 않는다. 관측 body, 부호, 합산 범위, 동적 상태가 맞아야 그런 비교가 의미가 있다. [공식 접촉 센서 개념](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/overview/core-concepts/sensors/contact_sensor.rst), [통합 센서 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/add_sensors_on_robot.py)

<a id="step-21"></a>

## 21단계. RayCaster로 바닥 높이 측정

20단계의 ANYmal 예제에는 바닥으로 광선을 보내는 `height_scanner`가 이미 들어 있다. 먼저 이 센서를 읽은 뒤 별도 rough terrain 예제로 넘어간다.

```python
from isaaclab.sensors import RayCasterCfg, patterns

height_scanner_cfg = RayCasterCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base",
    update_period=0.02,
    offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
    ray_alignment="yaw",
    pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=[1.6, 1.0]),
    mesh_prim_paths=["/World/defaultGroundPlane"],
    debug_vis=True,
)
```

위 설정은 공식 통합 예제의 구성이다. 로봇 위쪽에서 아래로 향하는 격자 광선으로 지정한 바닥 mesh의 높이를 읽는다. 20 m offset은 카메라를 20 m 위에 놓는 뜻이 아니며, 이 height scanner 광선의 출발 위치를 정하는 값이다.

`mesh_prim_paths`는 광선이 검사할 대상이다. 목록에 포함하지 않은 물체가 장면에 보이더라도 이 센서의 교차 대상으로 자동 포함된다고 가정하지 않는다. 또한 `GridPatternCfg`는 바닥 높이 관측용 격자 패턴이며 3D LiDAR의 회전·반사 강도·시간 왜곡을 모두 재현한 모델이 아니다.

```python
hits = scene["height_scanner"].data.ray_hits_w.torch
valid_rays = torch.isfinite(hits).all(dim=-1)
print("valid ray ratio:", valid_rays.float().mean().item())
if valid_rays.any():
    valid_heights = hits[..., 2][valid_rays]
    print("ground z range [m]:", valid_heights.min().item(), valid_heights.max().item())
```

평평한 바닥만 검사하는 이 장면에서는 유효 교차점들의 Z가 바닥 높이 근처여야 한다. 광선이 대상에 닿지 않으면 무효 값이 있을 수 있으므로 모든 배열에 무조건 `max()`를 적용하지 않는다.

확장 실습으로 공식 rough terrain 예제를 실행한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/tutorials/04_sensors/run_ray_caster.py \
  --device cuda:0 --viz kit
```

이 공식 예제는 외부 rough terrain USD를 불러오고 공들의 위치를 무작위로 초기화한다. 평평한 바닥 실습과 높이 범위가 같을 필요는 없다. 첫 로딩 실패는 센서 알고리즘보다 자산 주소·다운로드 로그를 먼저 확인한다.

RayCaster의 대상 mesh 지원과 갱신 방식은 구현에 따라 제한이 있다. 움직이는 물체까지 감지하도록 확장하려면 해당 태그의 RayCaster와 multi-mesh sensor 문서를 읽고 작은 장면에서 교차점을 따로 확인한다. 일반 RGB 렌더러가 보고 있는 형상 전체와 ray-cast 대상이 항상 같다고 설명하지 않는다. [공식 RayCaster 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_ray_caster.py), [RayCaster 개념](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/overview/core-concepts/sensors/ray_caster.rst)

<a id="step-22"></a>

## 22단계. 센서 통합 검사와 이상 화면 진단

미니 프로젝트 4의 완료 조건은 카메라 사진 한 장이 생기는 데서 끝나지 않는다. 아래 기록을 남긴다.

| 검사 대상 | 남길 기록 | 통과 여부를 판단할 근거 |
|---|---|---|
| RGB·깊이 | `rgb.png`, 원본 `.npy`, JSON | 물체 방향, 픽셀 분포, 유효 깊이와 예상 거리 |
| 로봇 상태 | 위치·관절·속도 로그 | 유한한 값, reset 후 의도한 초기 자세 |
| 접촉 센서 | 힘 벡터와 norm | 대상 링크가 맞고 접촉 시 유효한 변화가 있는가 |
| RayCaster | 유효 광선 비율과 높이 범위 | 지정한 바닥 위치와 교차점이 일치하는가 |
| 재현 조건 | 태그, 명령, GPU·드라이버 | 같은 조건으로 다시 실행할 수 있는가 |

센서를 무작정 추가하면서 문제를 찾지 않는다. p02 물리, p03 로봇, p04 카메라, 공식 통합 센서 순서로 어느 단계에서 처음 문제가 생기는지 확인한다.

| 증상 | 먼저 확인할 것 | 다음 조치 |
|---|---|---|
| 창이 열리지 않다 | `--viz kit` 지정 여부 | GUI가 필요한 명령에 명시하다 |
| RGB가 계속 검다 | 카메라 방향, 물체가 시야 안에 있는지, 조명, `--enable_cameras` | p04의 기준 장면으로 다시 실행하다 |
| RGB는 정상, depth에 inf가 많다 | 하늘·측정 범위 밖 픽셀, clipping 범위 | 유효 픽셀을 분리하고 기준 물체 영역을 확인하다 |
| 시작 몇 프레임이 비다 | 자산·셰이더·render product 준비 | 준비 프레임 이후 결과를 검사하다 |
| 로봇이 무너지다 | root 고정, 관절 이름, actuator, 초기 겹침 | p03 설정으로 복구하고 변경을 하나씩 재적용하다 |
| reset 뒤 로봇들이 겹치다 | `env_origins`, 기본 데이터의 `.clone()` | world pose 계산을 고치다 |
| 접촉력이 계속 0이다 | contact reporting, 실제 강체 링크 경로, 실제 접촉 | 센서 body 수와 경로를 출력하다 |
| ray hit가 없다 | `mesh_prim_paths`, 광선 방향·출발 위치 | 평평한 공식 ground로 범위를 줄이다 |
| 해상도나 환경 수를 늘린 뒤 오류 | GPU 메모리와 오류 로그 | 직전에 통과한 수·해상도로 되돌리다 |
| 형상이 찢어지거나 일부만 나타나다 | USD 참조·재질 로딩 오류, 변환·단위 | 자산 로딩 완료 여부와 원본 설정을 확인하다 |

실시간 RTX 렌더링의 시간 누적이나 샘플링 변화와 센서에 의도적으로 추가한 측정 노이즈는 구분한다. 학습용 노이즈·domain randomization은 기준 장면의 정상 동작을 확인한 뒤 도입한다. RGB가 조금 달라졌다는 이유만으로 매 프레임 완전히 같은 픽셀을 요구하는 검사는 만들지 않는다.

이 저장소의 검사 코드는 실패를 자동으로 숨기지 않도록 설계했다. 다만 문법 검사와 공식 소스 대조만으로 GPU 렌더링, 모든 자산 로딩, 로봇의 실제 동역학까지 통과했다고 말할 수는 없다. 작성 환경에서 GPU로 실행하지 못한 항목은 검증 보고서에 미실행으로 구분한다. 사용자는 위 명령을 자신의 GPU 환경에서 실행하고, 발생한 출력과 화면으로 마지막 확인을 마친다.

다음 장에서는 정상 동작을 확인한 장면을 관측·행동·보상·종료 조건을 갖춘 학습 환경으로 구성한다. 상자의 낙하나 로봇의 자세 유지에 문제가 남아 있다면 학습 시간을 늘리기 전에 이 장의 기준 실습부터 해결한다.
