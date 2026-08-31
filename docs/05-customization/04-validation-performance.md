# 커스텀 자산 검증, 성능 최적화와 회귀시험

커스텀 로봇·환경·센서가 화면에 보인다는 사실만으로는 SimReady 자산이라 할 수 없다. 이 장에서는 Isaac Sim 5.1.0과 Ubuntu 24.04 LTS를 기준으로 자산을 정적으로 검사하고, 물리와 센서의 정답 장면을 실행하며, 성능 예산과 회귀시험까지 연결한다.

검증은 다음 순서를 지킨다.

```text
USD 정적 검사
  → Asset Validator
  → Physics Inspector와 시각 검사
  → 단일 기능 수치 시험
  → 통합 시나리오 시험
  → 성능 기준선
  → 자동 회귀시험
```

성능 최적화는 마지막 단계이다. 잘못된 collider를 없애서 빨라진 결과나 카메라 출력을 끄고 얻은 높은 FPS는 개선이 아니다. 모든 최적화 전후에 동일한 물리·센서 정확성 시험을 다시 통과해야 한다.

## 1. 먼저 합격 조건을 수치로 정하다

`좋아 보이다`, `대체로 안정적이다` 같은 표현은 자동 시험에 사용할 수 없다. 요구사항을 측정값과 허용오차로 바꾼다. 다음 값은 학습용 출발점이며 NVIDIA가 보증하는 공통 정답이 아니다. 실제 로봇 사양과 프로젝트 목적에 맞게 조정한다.

| 대상 | 측정값 | 예시 합격 조건 | 실패가 의미하는 것 |
|---|---|---:|---|
| USD | stage 단위와 up axis | `1 m/unit`, `Z-up` | scale 또는 축 변환 오류 |
| 로봇 | 정지 자세 5초 후 base drift | `< 0.01 m` | 관통, mass, gain 또는 마찰 오류 |
| 관절 | step 입력 최종 오차 | `< 0.02 rad` | drive, effort limit 또는 joint axis 오류 |
| 환경 | grid drop의 바닥 높이 오차 | `< 0.002 m` | collider 누락·offset·seam 오류 |
| 카메라 | 기준점 reprojection RMSE | `< 1 px` | intrinsic, extrinsic 또는 축 convention 오류 |
| LiDAR | 기준 평면 point-to-plane RMSE | `< 0.02 m` | pose, range, material 또는 단위 오류 |
| IMU | 정지 상태 angular speed 평균 | `< 0.01 rad/s` | 부착 frame, filter 또는 초기화 오류 |
| 접촉 센서 | 정적 하중 평균 오차 | `< 5%` | threshold, mass, 중력 또는 sampling 오류 |
| 실행 성능 | real-time factor | 실시간 응용이면 `>= 1.0` | wall time보다 simulation time이 느림 |
| 지연 | physics step p95 | 기준선 대비 `<= 110%` | tail latency 회귀 |

검증 결과에는 이진 합격 여부뿐 아니라 실제 측정값, 단위, 허용오차를 함께 남긴다. 그래야 임계값 바로 아래에서 계속 악화되는 경향을 찾을 수 있다.

## 2. 재현 가능한 시험 환경을 고정하다

동일 USD라도 GPU, driver, renderer, physics step, sensor 해상도와 launch 설정이 다르면 결과가 달라진다. 시험 시작 전에 다음 정보를 기록한다.

```bash
# [HOST] Ubuntu와 kernel
lsb_release -ds
uname -a

# [HOST] CPU, RAM과 GPU driver 상태
lscpu
free -h
nvidia-smi

# [SIM] Isaac Sim에 포함된 Python과 package 경로
cd "$ISAACSIM_PATH"
./python.sh -c 'import sys; print(sys.version); import isaacsim; print(isaacsim.__file__)'

# [ASSET] 실제 시험한 입력의 checksum
sha256sum /abs/assets/robot.usd /abs/assets/environment.usd
```

ROS 2 경계까지 시험한다면 새 terminal마다 Jazzy를 source하고 domain도 기록한다.

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
printenv ROS_DISTRO ROS_DOMAIN_ID RMW_IMPLEMENTATION
```

다음 항목을 `run_manifest.json` 같은 manifest에 저장한다.

```json
{
  "isaac_sim": "5.1.0",
  "os": "Ubuntu 24.04 LTS",
  "physics_dt_s": 0.0083333333,
  "rendering_dt_s": 0.0166666667,
  "renderer": "RTX - Real-Time",
  "headless": true,
  "warmup_steps": 120,
  "measurement_steps": 600,
  "seed": 42,
  "robot_sha256": "기록한 checksum",
  "environment_sha256": "기록한 checksum"
}
```

성능 비교에서 다음 조건은 같은 값으로 유지한다.

- Isaac Sim은 정확히 5.1.0으로 고정한다.
- GPU model, driver, power mode와 CPU governor를 기록한다.
- physics/rendering dt와 substep, solver 설정을 고정한다.
- renderer, DLSS mode, 해상도, light, camera와 annotator 수를 고정한다.
- GPU dynamics, Motion BVH, asynchronous rendering과 Replicator `rt_subframes` 설정을 기록한다.
- 같은 시작 pose, command sequence와 random seed를 사용한다.
- shader와 asset streaming warm-up은 측정 구간에서 제외한다.
- 다른 사용자의 GPU job과 화면 녹화를 끄고 같은 부하 조건에서 반복한다.

## 3. 1단계: USD를 열기 전에 정적으로 검사하다

### 3.1 파일과 composition을 검사하다

다음 항목이 하나라도 틀리면 물리 시험을 시작하지 않는다.

- root layer와 모든 reference, payload, texture가 해석된다.
- asset의 default prim이 설정되어 있다.
- stage 단위와 up axis가 프로젝트 convention과 같다.
- source layer, optimized layer, physics layer와 sensor layer의 책임이 섞이지 않는다.
- 로봇 articulation root가 정확히 한 군데에 있다.
- 움직이는 rigid body에는 mass와 collider가 있다.
- joint의 body 관계, limit와 drive target이 원본 설명 파일과 일치한다.
- 센서 prim 경로와 parent rigid body가 배포 계약과 일치한다.
- 절대 경로와 개인의 Nucleus 주소가 배포 USD에 남지 않는다.

`.usda`로 export한 사본은 composition과 authored value를 리뷰하기 편하다. 원본 binary USD를 텍스트 파일로 이름만 바꾸지 말고 OpenUSD 도구로 변환한다.

```bash
# [SIM] usdcat 실행 파일이 PATH에 노출된 Isaac Sim terminal에서 실행한다.
usdcat /abs/assets/robot.usd -o /tmp/robot_review.usda
usdchecker /abs/assets/robot.usd
```

설치 형태에 따라 OpenUSD CLI가 PATH에 없을 수 있다. 이때 억지로 system Python의 다른 OpenUSD 버전을 섞지 말고 Isaac Sim의 `./python.sh`와 `pxr`를 사용한다.

### 3.2 최소 정적 검사 script를 만들다

다음 `validate_usd_static.py`는 표준 USD Physics schema만 사용하므로 GUI 없이 실행할 수 있다. Asset Validator를 대체하지 않고, pull request마다 빠르게 잘못된 단위·root·mass·collider를 거르는 첫 gate로 사용한다.

```python
#!/usr/bin/env python3
import argparse
import math
import sys

from pxr import Usd, UsdGeom, UsdPhysics


def fail(errors, message):
    errors.append(message)
    print(f"ERROR: {message}")


def has_owned_collider(body_prim):
    """다른 nested rigid body 아래로 넘어가지 않고 collider를 찾는다."""
    stack = list(body_prim.GetChildren())
    while stack:
        child = stack.pop()
        if child.HasAPI(UsdPhysics.CollisionAPI):
            return True
        if child.HasAPI(UsdPhysics.RigidBodyAPI):
            continue
        stack.extend(child.GetChildren())
    return False


parser = argparse.ArgumentParser()
parser.add_argument("usd")
parser.add_argument("--robot", action="store_true")
parser.add_argument("--required-prim", action="append", default=[])
args = parser.parse_args()

stage = Usd.Stage.Open(args.usd)
if stage is None:
    raise SystemExit(f"USD를 열 수 없다: {args.usd}")

errors = []
default_prim = stage.GetDefaultPrim()
if not default_prim.IsValid():
    fail(errors, "default prim이 없다")

meters = UsdGeom.GetStageMetersPerUnit(stage)
axis = UsdGeom.GetStageUpAxis(stage)
print(f"metersPerUnit={meters} upAxis={axis}")
if not math.isclose(meters, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
    fail(errors, f"meter 단위 stage가 아니다: {meters}")
if axis != UsdGeom.Tokens.z:
    fail(errors, f"Z-up stage가 아니다: {axis}")

for path in args.required_prim:
    if not stage.GetPrimAtPath(path).IsValid():
        fail(errors, f"필수 prim이 없다: {path}")

articulation_roots = []
rigid_count = 0
collider_count = 0
joint_count = 0

for prim in stage.Traverse():
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        articulation_roots.append(str(prim.GetPath()))
    if prim.IsA(UsdPhysics.Joint):
        joint_count += 1
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        collider_count += 1
    if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
        continue

    rigid_count += 1
    if not has_owned_collider(prim):
        fail(errors, f"rigid body 아래 collider가 없다: {prim.GetPath()}")

    if not prim.HasAPI(UsdPhysics.MassAPI):
        fail(errors, f"MassAPI가 없다: {prim.GetPath()}")
        continue

    mass_api = UsdPhysics.MassAPI(prim)
    mass = mass_api.GetMassAttr().Get()
    inertia = mass_api.GetDiagonalInertiaAttr().Get()
    if mass is None or not math.isfinite(float(mass)) or mass <= 0:
        fail(errors, f"유효하지 않은 mass: {prim.GetPath()} value={mass}")
    if inertia is None:
        fail(errors, f"diagonal inertia가 없다: {prim.GetPath()}")
    else:
        values = [float(x) for x in inertia]
        if any((not math.isfinite(x) or x <= 0) for x in values):
            fail(errors, f"유효하지 않은 diagonal inertia: {prim.GetPath()} {values}")
        elif any(
            values[i] > values[(i + 1) % 3] + values[(i + 2) % 3] + 1e-9
            for i in range(3)
        ):
            fail(errors, f"inertia triangle inequality 위반: {prim.GetPath()} {values}")

print(
    f"rigid={rigid_count} collider={collider_count} "
    f"joint={joint_count} articulationRoots={articulation_roots}"
)

if args.robot:
    if len(articulation_roots) != 1:
        fail(errors, f"robot articulation root 수가 1이 아니다: {articulation_roots}")
    if joint_count == 0:
        fail(errors, "robot joint가 없다")

sys.exit(1 if errors else 0)
```

Isaac Sim에 포함된 Python으로 실행한다.

```bash
cd "$ISAACSIM_PATH"
./python.sh /abs/tests/validate_usd_static.py \
  /abs/assets/robot.usd \
  --robot \
  --required-prim /Robot/Sensors/Camera \
  --required-prim /Robot/Sensors/Lidar
```

이 script가 찾지 못하는 항목도 많다. 예를 들어 non-adjacent collider 교차, joint와 body transform의 일관성, Robot API 관계, physics layer 위치는 Isaac Sim Asset Validator로 검사한다.

## 4. 2단계: Asset Validator를 실행하다

Isaac Sim 5.1의 `isaacsim.asset.validation` extension은 기본으로 활성화된다. 꺼져 있다면 `Window > Extensions`에서 해당 extension을 찾는다. `Window > Asset Validator`를 열고 최소한 다음 세 category를 실행한다.

| category | 주요 검사 |
|---|---|
| `IsaacSim.PhysicsRules` | drive/mimic, max velocity, joint state, mass/inertia, collider, articulation root, collider clash |
| `IsaacSim.RobotRules` | naming, Robot API, links/joints 관계, physics source layer, thumbnail |
| `IsaacSim.SimReadyAssetRules` | material hierarchy와 top-level Looks 배치 |

특히 다음 오류는 simulation을 실행하기 전에 해결한다.

- non-fixed joint에 drive 또는 mimic이 없다.
- drive max force가 0이거나 유한한 양수로 authoring되지 않았다.
- rigid body에 Mass API, 양의 mass/inertia 또는 collider가 없다.
- non-adjacent collision mesh가 시작 자세에서 겹친다.
- articulation root가 없다.
- joint state와 drive target이 시작 pose와 모순된다.

`RobotNaming`, thumbnail과 folder cleanliness는 물리 계산을 바로 깨뜨리지는 않지만, 배포 규약과 asset browser 사용성에 영향을 준다. tutorial용 임시 asset이라서 의도적으로 예외 처리했다면 결과를 삭제하지 말고 waiver와 이유를 manifest에 기록한다.

자동 수정 제안은 diff를 확인한 뒤 적용한다. referenced source에 override가 생기거나 physics 속성이 잘못된 layer에 기록되지 않았는지 Layers panel에서 확인한다. 검증 결과 화면과 Output Log를 release artifact로 보관한다.

## 5. 3단계: Physics Inspector와 시각화 도구를 사용하다

### 5.1 Physics Inspector

`Tools > Physics > Physics Inspector`를 연다. Isaac Sim의 경로는 일반 Omniverse 문서와 다를 수 있으므로 이 메뉴 경로를 사용한다. Physics Authoring Toolbar는 `Tools > Physics Toolbar`에 있다.

Physics Inspector에서 다음 절차로 로봇을 검사한다.

1. articulation root와 link를 선택한다.
2. joint 목록, 축, lower/upper limit와 drive mode를 원본 URDF/MJCF 표와 대조한다.
3. timeline을 멈춘 상태에서 한 joint의 target slider만 작은 양수로 움직인다.
4. parent와 child가 올바른 축과 방향으로 움직이는지 확인한다.
5. limit 직전에서 collider가 관통하거나 mimic chain이 반대로 움직이지 않는지 확인한다.
6. 모든 joint를 시작 상태로 복원한 뒤 다음 joint를 검사한다.

Physics Inspector는 `omni.physx`를 부분적으로 초기화한다. 창이 열린 뒤 일반 simulation이 비정상적으로 보일 수 있다는 5.1 공식 경고가 있다. Inspector 검사가 끝나면 창을 닫고 stage를 다시 열거나 reset한 새 실행에서 수치 시험을 수행한다. Inspector를 연 세션의 성능 수치를 기준선으로 저장하지 않는다.

### 5.2 collider, mass와 runtime 상태를 보이다

- Viewport의 눈 아이콘에서 `Show by Type > Physics > Colliders > All`을 켜 visual mesh와 collider를 비교한다.
- Physics Toolbar의 mass distribution 도구로 COM과 질량 분포가 기구적으로 타당한지 확인한다.
- `Show by Type > Physics > Simulation Data Visualizer`에서 position, linear/angular velocity, acceleration, mass와 inertia를 본다.
- Physics Scene, articulation root 또는 joint에 `Add > Physics > Residual Reporting`을 적용하고 Simulation Data Visualizer에서 residual을 본다.
- residual이 발산하거나 지속적으로 큰 spike를 보이면 dt, mass ratio, 관통, joint constraint와 solver iteration을 조사한다.

residual의 절대 합격값은 모든 장면에 공통인 상수가 아니다. 정상 기준 장면과 같은 설정에서 시간 변화와 최적화 전후 추세를 비교한다.

## 6. 4단계: 커스텀 로봇을 수치로 검증하다

### 6.1 로봇 acceptance test 순서

1. ground 위 안전한 높이에 robot만 배치한다.
2. command 없이 3~5초 settle하고 base pose, link velocity와 NaN을 검사한다.
3. joint를 하나씩 작은 step으로 구동해 축, 부호, limit, drive를 검사한다.
4. position, velocity와 effort mode를 각각 의도한 controller와 시험한다.
5. self-collision on/off가 설계와 일치하는지 확인한다.
6. payload를 0%, 50%, 100%로 바꾸고 안정성과 torque margin을 측정한다.
7. mobile robot이면 직진·제자리 회전·braking distance·lateral slip을 측정한다.
8. manipulator이면 joint space와 Cartesian pose 오차, collision과 singular 근처 동작을 측정한다.

### 6.2 관절 step response를 자동 측정하다

다음 standalone 예제는 custom USD를 reference하고 한 관절에 position step을 준다. `ROBOT_USD`, `ROBOT_PRIM`, `JOINT_NAME`과 허용오차를 프로젝트 값으로 바꾼다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import json
import time
import numpy as np

from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.types import ArticulationAction

ROBOT_USD = "/abs/assets/robot.usd"
ROBOT_PRIM = "/World/Robot"
JOINT_NAME = "joint_1"
STEP_RAD = 0.20
FINAL_ERROR_LIMIT_RAD = 0.02
PHYSICS_DT = 1.0 / 120.0


def first_settled_time(t, error, tolerance):
    for i in range(len(error)):
        if np.all(error[i:] <= tolerance):
            return float(t[i])
    return None


try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=PHYSICS_DT,
        rendering_dt=1.0 / 60.0,
    )
    world.scene.add_default_ground_plane()
    add_reference_to_stage(ROBOT_USD, ROBOT_PRIM)
    robot = world.scene.add(
        SingleArticulation(prim_path=ROBOT_PRIM, name="robot_under_test")
    )
    world.reset()

    names = list(robot.dof_names)
    if JOINT_NAME not in names:
        raise RuntimeError(f"{JOINT_NAME}이 없다. DOF={names}")
    index = names.index(JOINT_NAME)

    # 시작 접촉과 shader/handle 초기화를 측정에서 제외한다.
    for _ in range(120):
        world.step(render=False)

    q0 = np.asarray(robot.get_joint_positions(), dtype=np.float64)
    target = q0.copy()
    target[index] += STEP_RAD
    robot.apply_action(ArticulationAction(joint_positions=target))

    samples = []
    wall_start = time.perf_counter()
    sim_start = world.current_time
    for _ in range(360):
        world.step(render=False)
        q = np.asarray(robot.get_joint_positions(), dtype=np.float64)
        dq = np.asarray(robot.get_joint_velocities(), dtype=np.float64)
        if not np.all(np.isfinite(q)) or not np.all(np.isfinite(dq)):
            raise AssertionError("joint state에 NaN/Inf가 발생했다")
        samples.append((world.current_time - sim_start, q[index], dq[index]))

    wall_elapsed = time.perf_counter() - wall_start
    data = np.asarray(samples)
    t = data[:, 0]
    q = data[:, 1]
    error = np.abs(target[index] - q)
    normalized = (q - q0[index]) / STEP_RAD

    metrics = {
        "joint": JOINT_NAME,
        "target_rad": float(target[index]),
        "final_error_rad": float(error[-1]),
        "overshoot_ratio": float(max(0.0, np.max(normalized) - 1.0)),
        "settling_time_s": first_settled_time(t, error, FINAL_ERROR_LIMIT_RAD),
        "max_abs_velocity_rad_s": float(np.max(np.abs(data[:, 2]))),
        "rtf_during_test": float((world.current_time - sim_start) / wall_elapsed),
    }
    print(json.dumps(metrics, indent=2))
    np.savetxt(
        "joint_step.csv",
        data,
        delimiter=",",
        header="sim_time_s,position_rad,velocity_rad_s",
        comments="",
    )

    assert metrics["final_error_rad"] <= FINAL_ERROR_LIMIT_RAD, metrics
    assert metrics["settling_time_s"] is not None, metrics
finally:
    simulation_app.close()
```

```bash
cd "$ISAACSIM_PATH"
./python.sh /abs/tests/test_joint_step.py 2>&1 | tee /abs/results/joint_step.log
```

position target을 full DOF vector로 보낸 이유는 관절 index와 target shape의 모호함을 없애기 위해서이다. continuous joint, mimic joint와 직접 effort-controlled joint에는 이 시험을 그대로 적용하지 않는다. 각 제어 mode에 맞는 입력과 metric을 정의한다.

### 6.3 mass, inertia와 collision을 검증하다

- 총 mass를 BOM 또는 실측과 비교한다.
- COM을 suspension/contact polygon과 비교하고, arm pose에 따른 이동이 타당한지 확인한다.
- diagonal inertia는 양수이고 물리적으로 가능한 범위인지 확인한다.
- visual과 collider의 gap·관통을 top/front/side에서 검사한다.
- non-adjacent link가 시작 자세에서 접촉하지 않는지 확인한다.
- wheel collider는 가능한 한 cylinder 또는 sphere 같은 단순 형상을 사용하고 회전축을 검증한다.
- self collision을 끌 때 실제로 필요한 gripper/finger 충돌까지 사라지지 않는지 확인한다.

접촉 안정성은 서로 다른 높이에서 drop, 경사면 정지, 낮은 턱 통과와 최대 command 정지 시험으로 나눈다. 매우 큰 friction이나 damping으로 잘못된 mass와 controller를 숨기지 않는다.

## 7. 5단계: 커스텀 환경의 collider를 검증하다

### 7.1 환경 정적 검사

| 항목 | 검사 방법 |
|---|---|
| 단위/축 | stage metadata와 알려진 문·pallet 크기를 재다. |
| ground | collider 표시 후 render floor와 높이·normal을 비교하다. |
| wall/door | robot footprint보다 작은 proxy를 통로에 이동하다. |
| stair/ramp | step 높이, slope, seam과 collision approximation을 재다. |
| movable prop | Rigid Body, Mass API, collider와 시작 관통을 검사하다. |
| material | render material과 physics material binding을 따로 확인하다. |
| semantics | class taxonomy와 annotator의 id-to-label mapping을 비교하다. |
| dependency | 다른 directory로 복사한 뒤 reference와 texture를 다시 load하다. |

invisible collider는 Viewport에서 항상 한 번 모두 표시한다. 보이지 않는 벽이 navigation 경로를 막거나 visual wall에 collider가 없는 경우가 흔하다.

### 7.2 grid drop 시험을 실행하다

알려진 floor 높이 위 여러 위치에서 작은 cube를 떨어뜨린다. 이 시험은 collider 누락, 잘못된 offset, 바닥 seam과 일부 경사 문제를 빠르게 찾는다. default ground plane을 추가하면 환경의 collider 누락을 가리므로 이 시험에서는 추가하지 않는다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.utils.stage import add_reference_to_stage

ENV_USD = "/abs/assets/warehouse.usd"
ENV_PRIM = "/World/Environment"
FLOOR_Z = 0.0
CUBE_SIZE = 0.10
Z_TOLERANCE = 0.002
SPEED_TOLERANCE = 0.02
XY = [(-4.0, -2.0), (0.0, 0.0), (3.0, 1.5), (4.0, -3.0)]

try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=1.0 / 120.0,
        rendering_dt=1.0 / 60.0,
    )
    add_reference_to_stage(ENV_USD, ENV_PRIM)

    probes = []
    for i, (x, y) in enumerate(XY):
        probes.append(
            world.scene.add(
                DynamicCuboid(
                    prim_path=f"/World/Validation/Probe_{i}",
                    name=f"probe_{i}",
                    position=np.array([x, y, FLOOR_Z + 1.0]),
                    size=CUBE_SIZE,
                    mass=0.2,
                    color=np.array([1.0, 0.0, 0.0]),
                )
            )
        )

    world.reset()
    for _ in range(600):
        world.step(render=False)

    expected_z = FLOOR_Z + CUBE_SIZE / 2.0
    failures = []
    for (x, y), probe in zip(XY, probes):
        position, _ = probe.get_world_pose()
        speed = np.linalg.norm(probe.get_linear_velocity())
        z_error = abs(float(position[2]) - expected_z)
        print((x, y), "z=", position[2], "z_error=", z_error, "speed=", speed)
        if z_error > Z_TOLERANCE or speed > SPEED_TOLERANCE:
            failures.append({"xy": (x, y), "z_error": z_error, "speed": speed})
    assert not failures, failures
finally:
    simulation_app.close()
```

cube가 무한히 떨어지면 collider가 없거나 위치가 틀렸을 가능성이 높다. 기대 높이보다 위에 멈추면 invisible collider 또는 이중 collider를 의심한다. 계속 흔들리면 seam, restitution, mass scale, solver 또는 시작 관통을 확인한다.

grid drop 하나로 통로와 벽을 검증할 수는 없다. 이어서 robot 크기의 capsule/box proxy로 주행 경로를 sweep하고 다음을 기록한다.

- 문과 aisle의 최소 collision 폭
- wheel이 걸리는 바닥 seam 위치
- 계단·경사·threshold의 통과/거부 경계
- navigation map obstacle과 실제 collider의 차이
- 움직이는 door/prop의 joint limit와 contact 안정성

## 8. 6단계: 센서를 ground truth 장면으로 검증하다

센서 검증에서 “Viewport와 비슷하다”는 합격 조건이 아니다. 정답을 계산할 수 있는 단순 장면을 먼저 만든 뒤 복잡한 환경으로 이동한다.

### 8.1 공통 센서 계약

모든 센서에 다음 표를 만든다.

| 계약 | 확인할 값 |
|---|---|
| parent/pose | sensor prim path, rigid-body parent, local translation/quaternion |
| frame | Isaac Sim 축과 ROS optical/sensor frame 변환 |
| rate | requested period, physics/render rate, 실제 timestamp 간격 |
| unit | m, rad/s, m/s², N, N·m 등 |
| range | minimum/maximum, clipping, invalid value 표현 |
| latency | simulation timestamp와 consumer 수신 시각 |
| noise | seed, 분포, bias, drift와 correlation |
| reset | 첫 valid sample 시점, timestamp reset 정책 |

요청 frequency가 physics frequency보다 높아도 IMU가 더 많은 새 physics sample을 만들지는 않는다. render 기반 센서 역시 render product update보다 빠른 독립 ground truth를 보장하지 않는다.

### 8.2 카메라 intrinsic·extrinsic과 영상 출력을 검증하다

카메라 앞에 위치를 정확히 아는 marker를 놓고 기대 pixel을 저장한다. 다음 핵심 코드는 5.1 `Camera` wrapper의 공식 world-to-image API를 사용한다.

```python
import numpy as np

# camera.initialize()와 충분한 render warm-up 뒤 실행한다.
world_points = np.array(
    [
        [2.0, -0.25, 1.0],
        [2.0,  0.00, 1.0],
        [2.0,  0.25, 1.0],
    ],
    dtype=np.float64,
)
expected_pixels = np.loadtxt("expected_pixels.csv", delimiter=",")
actual_pixels = camera.get_image_coords_from_world_points(world_points)

error = np.linalg.norm(actual_pixels - expected_pixels, axis=1)
rmse = float(np.sqrt(np.mean(error ** 2)))
print("reprojection px:", error, "RMSE:", rmse)
assert np.all(np.isfinite(actual_pixels))
assert rmse < 1.0

rgba = camera.get_rgba()
assert rgba is not None
assert rgba.shape[:2] == (480, 640)
assert np.all(np.isfinite(rgba))
assert np.ptp(rgba[..., :3].astype(np.float32)) > 1.0
```

`expected_pixels.csv`는 시험 장면과 calibration contract에서 계산한 독립 기준값이어야 한다. 같은 API로 기대값을 만들고 같은 API를 검사하면 순환 검증이 된다.

추가로 다음을 검사한다.

- OpenCV pinhole/fisheye coefficient와 `OmniLensDistortion` schema가 의도대로 적용된다.
- RGB, depth, point cloud, segmentation이 같은 camera pose와 timestamp를 사용한다.
- depth의 의미가 optical-axis depth인지 Euclidean distance인지 consumer 계약과 일치한다.
- clipping plane 근처와 먼 거리에서 invalid pixel 규칙이 일관된다.
- semantic label과 instance id mapping이 frame마다 해석 가능하다.
- 밝은 낮, 어두운 실내, 역광에서 histogram과 saturation 비율을 기록한다.
- 첫 render frame과 shader warm-up frame은 정답 비교에서 제외한다.

pixel 단위 exact match는 renderer와 GPU 변화에 취약하다. geometry mask는 IoU, depth는 RMSE/invalid ratio, RGB는 영역별 평균·histogram 또는 perceptual metric처럼 목적에 맞는 허용오차를 사용한다.

### 8.3 RTX LiDAR를 평면과 모서리로 검증하다

센서 frame 앞에 normal과 거리를 아는 큰 평면을 배치한다. point cloud를 sensor frame으로 변환한 뒤 plane residual을 계산한다.

```python
import numpy as np

# RTX annotator 또는 ROS bag에서 추출해 sensor frame의 xyz로 저장한다.
points = np.load("lidar_points_sensor_frame.npy")[:, :3]
points = points[np.all(np.isfinite(points), axis=1)]

# 알려진 시험 평면 n·p=d. n은 단위 vector이다.
n = np.array([1.0, 0.0, 0.0])
d = 5.0

# 벽의 유한한 y/z 범위 안 hit만 평가한다.
mask = (
    (np.abs(points[:, 1]) < 1.0)
    & (np.abs(points[:, 2]) < 1.0)
    & (points[:, 0] > 0.0)
)
wall_hits = points[mask]
if len(wall_hits) < 100:
    raise AssertionError(f"평면 hit가 너무 적다: {len(wall_hits)}")

residual = wall_hits @ n - d
rmse = float(np.sqrt(np.mean(residual ** 2)))
p95 = float(np.percentile(np.abs(residual), 95))
print({"count": len(wall_hits), "plane_rmse_m": rmse, "p95_m": p95})
assert rmse < 0.02
```

이 시험을 여러 거리, incidence angle과 material에서 반복한다. glass, retroreflective surface와 non-visual material은 RGB material만으로 판단하지 않는다. 다음도 기록한다.

- 한 rotation/frame의 point 수와 invalid 비율
- min/max range 경계
- horizontal/vertical field of view와 channel/ray pattern
- rotation/update rate와 timestamp monotonicity
- point cloud frame과 sensor extrinsic
- 움직이는 target에서 motion distortion 요구 여부
- RTX non-visual material을 바꿨을 때 intensity/return 변화

### 8.4 IMU를 정지·등속·회전 시험으로 검증하다

IMU는 rigid body에 붙이고 filter가 채워질 때까지 warm-up한다. `read_gravity=True`와 `False`는 서로 다른 계약이므로 명시한다. 5.1 저수준 interface에서 gravity를 포함한 최신 physics sample을 읽는 핵심은 다음과 같다.

```python
import numpy as np
from isaacsim.sensors.physics import _sensor

imu_interface = _sensor.acquire_imu_sensor_interface()
reading = imu_interface.get_sensor_reading(
    "/World/Robot/base_link/Imu_Sensor",
    use_latest_data=True,
    read_gravity=True,
)
if not reading.is_valid:
    raise RuntimeError("valid IMU sample이 아직 없다")

linear_acceleration = np.array(
    [reading.lin_acc_x, reading.lin_acc_y, reading.lin_acc_z], dtype=float
)
angular_velocity = np.array(
    [reading.ang_vel_x, reading.ang_vel_y, reading.ang_vel_z], dtype=float
)
print("|a|=", np.linalg.norm(linear_acceleration))
print("|w|=", np.linalg.norm(angular_velocity))
assert np.all(np.isfinite(linear_acceleration))
assert np.all(np.isfinite(angular_velocity))
```

정지 시험에서는 `read_gravity=True`일 때 local frame으로 회전한 중력 vector와 비교한다. 방향을 외워서 고정하지 말고 sensor extrinsic으로 world gravity를 변환해 기대값을 계산한다. 이어서 다음을 시험한다.

- gravity를 제외한 정지 출력의 bias와 표준편차
- 알려진 일정 angular velocity에서 axis·부호·scale
- 등속 이동 중 불필요한 linear acceleration 여부
- step acceleration의 filter delay와 overshoot
- reset 직후 invalid/초기 sample 처리
- sensor period와 실제 timestamp 간격

### 8.5 contact와 effort sensor를 하중으로 검증하다

질량 `m`인 box를 수평 floor 위에 정지시키면 장시간 평균 normal force는 대략 `m g`가 된다. 접촉 직후 impulse 구간을 버리고 평균과 변동을 계산한다.

```python
import numpy as np

mass_kg = 2.0
gravity_m_s2 = 9.81
force_n = np.loadtxt("contact_force_after_warmup.csv", delimiter=",")

expected = mass_kg * gravity_m_s2
measured = float(np.mean(force_n))
relative_error = abs(measured - expected) / expected
print({"expected_N": expected, "mean_N": measured, "relative_error": relative_error})
assert np.all(np.isfinite(force_n))
assert relative_error < 0.05
```

Contact Sensor의 threshold, radius/region과 parent collider를 바꾸며 접촉 포함·제외 경계를 시험한다. 센서 prim을 simulation 중 이동하면 sensor가 invalid해질 수 있으므로 Stop 상태에서 hierarchy를 고치고 다시 Play한다.

Effort Sensor는 revolute joint에서 torque, prismatic joint에서 force를 측정한다. 알려진 lever arm과 payload로 정적 기대 torque를 계산하고 sign, magnitude, joint index를 비교한다. controller command나 drive target을 ground truth effort로 착각하지 않는다.

### 8.6 timestamp와 실제 rate를 검사하다

저장한 sensor timestamp에 다음 공통 검사를 적용한다.

```python
import numpy as np

timestamps = np.loadtxt("sensor_timestamps_s.csv")
dt = np.diff(timestamps)
assert len(dt) > 10
assert np.all(np.isfinite(dt))
assert np.all(dt > 0.0), "timestamp가 중복되거나 역행한다"

print(
    {
        "samples": len(timestamps),
        "median_period_s": float(np.median(dt)),
        "p95_period_s": float(np.percentile(dt, 95)),
        "effective_rate_hz": float(1.0 / np.mean(dt)),
    }
)
```

ROS 2 Jazzy까지 연결했다면 consumer가 보는 topic 계약도 별도로 검사한다.

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
ros2 topic info --verbose /camera/color/image_raw
ros2 topic hz /camera/color/image_raw
ros2 topic echo --once /camera/color/camera_info
ros2 topic hz /scan
ros2 topic hz /imu
```

`ros2 topic hz`는 consumer 관측 rate이며 simulation 내부 sensor 생성 rate와 다를 수 있다. QoS 불일치, DDS/serialization과 RTF 저하를 함께 진단한다.

## 9. 성능을 physics·render·sensor로 분리해 측정하다

### 9.1 측정해야 할 metric

- RTF: `simulated elapsed time / wall elapsed time`
- step latency p50, p95, p99와 maximum
- physics-only와 rendering-enabled 결과
- camera/RTX sensor별 실제 update rate
- CPU utilization, GPU utilization, RAM과 VRAM peak
- rigid body, articulation, collider, contact pair, mesh/prim 수
- ROS publish rate와 message bandwidth가 요구사항에 미치는 영향

RTF가 1보다 크면 wall time보다 simulation이 빠르고, 1보다 작으면 느리다. GUI FPS와 RTF는 같은 값이 아니다. physics가 여러 번 step된 뒤 한 번 render될 수 있다.

Isaac Sim 5.1은 `isaacsim.benchmark.services`와 standalone benchmark 예제를 제공한다. 공식 benchmark와 자체 acceptance test는 목적이 다르다. 공식 예제는 machine 간 표준 KPI 비교에 사용하고, 자체 benchmark는 실제 custom stage와 sensor 계약의 release gate로 사용한다.

```bash
cd "$ISAACSIM_PATH"
./python.sh standalone_examples/benchmarks/benchmark_robots_o3dyn.py \
  --num-robots 10 \
  --num-gpus 1
```

공식 benchmark 문서의 GPU KPI는 600 frame 평균을 사용한다. 평균 하나만으로 spike가 가려지므로 자체 시험에서는 p95와 p99도 함께 남긴다. multi-GPU는 camera/render workload에 이득이 날 수 있지만 GPU physics는 한 GPU에서 실행된다는 제한도 성능 계획에 반영한다.

### 9.2 reusable benchmark를 실행하다

다음 pattern은 warm-up 뒤 step latency와 RTF를 JSON으로 출력한다. 실제 sensor workload 시험에서는 sensor와 annotator가 stage에서 활성화된 상태로 `RENDER=True`를 사용한다.

```python
from isaacsim import SimulationApp

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("usd")
parser.add_argument("--render", action="store_true")
parser.add_argument("--output", default="metrics.json")
args = parser.parse_args()

simulation_app = SimulationApp(
    {
        "headless": True,
        # physics-only일 때만 viewport update를 끈다.
        "disable_viewport_updates": not args.render,
    }
)

import json
import time
import numpy as np

from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage

try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=1.0 / 120.0,
        rendering_dt=1.0 / 60.0,
    )
    add_reference_to_stage(args.usd, "/World/AssetUnderTest")
    world.reset()

    for _ in range(120):
        world.step(render=args.render)

    sim_start = world.current_time
    wall_start = time.perf_counter()
    latencies_ms = []
    for _ in range(600):
        t0 = time.perf_counter()
        world.step(render=args.render)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
    wall_elapsed = time.perf_counter() - wall_start
    sim_elapsed = world.current_time - sim_start

    a = np.asarray(latencies_ms)
    metrics = {
        "render": args.render,
        "steps": len(a),
        "sim_elapsed_s": float(sim_elapsed),
        "wall_elapsed_s": float(wall_elapsed),
        "rtf": float(sim_elapsed / wall_elapsed),
        "step_ms_p50": float(np.percentile(a, 50)),
        "step_ms_p95": float(np.percentile(a, 95)),
        "step_ms_p99": float(np.percentile(a, 99)),
        "step_ms_max": float(np.max(a)),
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
finally:
    simulation_app.close()
```

physics-only와 실제 render/sensor workload를 별도 process로 실행한다.

```bash
cd "$ISAACSIM_PATH"

./python.sh /abs/tests/benchmark_stage.py \
  /abs/scenes/regression_scene.usd \
  --output /abs/results/physics_only.json

./python.sh /abs/tests/benchmark_stage.py \
  /abs/scenes/regression_scene.usd \
  --render \
  --output /abs/results/render_sensor.json
```

`render=False`는 RTX camera/LiDAR workload를 대표하지 않는다. 반대로 render 시험에서 sensor 결과를 실제로 소비하지 않으면 readback, annotator와 serialization 비용을 놓칠 수 있다. 실제 application과 동일한 render product, annotator, writer 또는 ROS publisher를 켠 통합 benchmark도 실행한다.

별도 terminal에서 GPU 상태를 sampling한다.

```bash
# [HOST] Ctrl+C로 종료한다.
nvidia-smi \
  --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,power.draw \
  --format=csv \
  -l 1
```

짧은 spike의 원인은 Tracy로 찾는다.

```bash
cd "$ISAACSIM_PATH"
./python.sh /abs/tests/benchmark_stage.py /abs/scenes/regression_scene.usd \
  --render \
  --enable omni.kit.profiler.tracy
```

profiler는 overhead를 만든다. 원인 분석 capture와 최종 합격 수치는 분리하고, 최종 수치는 profiler를 끈 상태에서 다시 잰다.

## 10. 병목별로 안전하게 최적화하다

한 번에 한 항목만 바꾸고 같은 seed와 입력으로 전후를 비교한다.

### 10.1 로봇 자산

- 한 rigid body를 이루는 불필요하게 많은 visual mesh를 Mesh Merge Tool로 정리한다.
- 반복 wheel/link mesh는 reference와 scenegraph instancing을 검토한다.
- body는 box/capsule, wheel은 cylinder/sphere처럼 목적을 충족하는 가장 단순한 collider를 사용한다.
- 사용하지 않는 collider와 필요 없는 self collision을 끈다.
- mass ratio, solver iteration과 physics dt를 정확성 범위 안에서 조정한다.
- high-poly render mesh를 collision mesh로 그대로 사용하지 않는다.

instancing된 child에는 개별 attribute override 제한이 있다. sensor, material 또는 collision variant가 link마다 다르면 prototype 설계를 먼저 고친다.

### 10.2 환경

- 반복 rack, pallet와 fixture를 instanceable reference로 구성한다.
- 거대한 단일 triangle mesh collider를 공간 단위로 나누거나 단순 primitive로 대체한다.
- 보이지 않고 접촉하지 않는 prop은 payload, activation 또는 scenario variant로 load를 제어한다.
- render mesh count와 material 수를 줄이되 semantic instance 경계를 잃지 않는다.
- camera에 보이지 않는 고비용 light, reflection과 texture를 요구사항에 맞게 줄인다.
- navigation 정확도를 유지하는 범위에서 collider contact point 수를 줄인다.

### 10.3 센서와 rendering

- 필요한 resolution, FOV와 frequency만 사용한다.
- 같은 camera에서 중복 render product와 사용하지 않는 annotator를 제거한다.
- RGB를 사용하지 않으면서 매 frame CPU로 복사하지 않는다.
- sensor update와 ROS publish를 physics의 매 step에 무조건 연결하지 않는다.
- headless physics batch에서만 `disable_viewport_updates=True`를 사용한다.
- streaming workflow에는 viewport update 비활성화를 적용하지 않는다.
- DLSS와 renderer 설정을 바꾸면 camera 품질 회귀시험을 다시 실행한다.
- LiDAR motion compensation이나 Radar Doppler 정확도에 Motion BVH가 필요하다면 켠 상태를 기준 workload로 삼는다. 이 기능은 VRAM과 render 시간을 늘릴 수 있다.

Isaac Sim full GUI 구성에서는 정지·일시정지 중 asynchronous rendering이 활성화될 수 있다. 합성 데이터 회귀 캡처에서 frame skip이나 ghosting을 조사할 때는 해당 설정과 `rt_subframes`를 manifest에 남긴다. 검증 목적상 async를 끌 경우 launch argument도 결과에 기록한다.

```bash
cd "$ISAACSIM_PATH"
./isaac-sim.sh --exts."isaacsim.core.throttling".enable_async=false
```

Isaac Sim 5.1 문서는 texture streaming을 끄면 일부 workload가 빨라질 수 있지만 VRAM 증가, missing texture와 crash 위험이 있다고 경고한다. 기본 최적화로 일괄 적용하지 않고 workload별로 측정한다.

### 10.4 CPU와 physics

- per-step `Stage.Traverse()`, Python allocation과 과도한 `print()`를 없앤다.
- prim handle, joint index와 static transform을 setup에서 cache한다.
- physics dt를 키우면 빠르지만 collision, controller와 sensor accuracy가 낮아질 수 있다.
- GPU dynamics는 GPU 여유와 지원 collider에 따라 이득이 달라진다.
- thread 수가 많을수록 항상 빠르지 않다. 5.1 `SimulationApp`의 `limit_cpu_threads`를 여러 값으로 benchmark한다.

```python
simulation_app = SimulationApp(
    {
        "headless": True,
        "limit_cpu_threads": 16,
    }
)
```

Ubuntu CPU governor 변경에는 root 권한과 시스템 전체 영향이 따른다. 먼저 상태만 기록하고, 전용 benchmark machine에서 운영 정책에 맞게 변경한다.

```bash
cpupower frequency-info
```

## 11. 최적화 결과를 정확성-성능 표로 판단하다

다음처럼 한 축만 보지 않는다.

| variant | joint error | LiDAR RMSE | camera RMSE | RTF | step p95 | 판단 |
|---|---:|---:|---:|---:|---:|---|
| baseline | 0.012 rad | 0.009 m | 0.42 px | 0.82 | 13.1 ms | 정확, 느림 |
| simple collider | 0.013 rad | 0.009 m | 0.42 px | 1.08 | 9.7 ms | 합격 후보 |
| dt 2배 | 0.061 rad | 0.011 m | 0.42 px | 1.36 | 7.4 ms | 관절 정확성 실패 |
| sensor 1/2 rate | 0.013 rad | 0.010 m | 0.44 px | 1.22 | 8.5 ms | rate 요구 확인 |

최적화의 합격 조건은 다음 두 가지를 동시에 만족하는 것이다.

1. 모든 correctness hard limit를 통과한다.
2. 동일 workload에서 performance budget을 통과한다.

## 12. 결정성의 범위와 random seed를 이해하다

`seed=42`만 설정했다고 모든 pixel과 contact가 bitwise 동일해지는 것은 아니다. 다음 요소를 구분한다.

- Python `random`과 NumPy seed
- Replicator randomization seed
- physics initial state와 command 순서
- asynchronous task, ROS message arrival와 callback 순서
- GPU renderer와 annotator의 수치 차이
- asset streaming과 shader compile warm-up

일반 Python과 Replicator seed를 명시한다.

```python
import random
import numpy as np
import omni.replicator.core as rep

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rep.set_global_seed(SEED)
```

PhysX 5.1의 공식 limitation에는 접촉 중인 simulation state를 중간에 USD로 저장하고 재개할 때 내부 contact state를 완전히 직렬화할 수 없어 nondeterministic할 수 있다는 항목이 있다. 회귀시험은 중간 접촉 snapshot에서 재개하지 말고 초기 상태부터 새 process로 실행한다.

권장 정책은 다음과 같다.

- physics state 시험은 같은 초기 stage에서 step 0부터 시작한다.
- 한 test case마다 새 process 또는 완전한 stage reload를 사용한다.
- exact equality 대신 단위가 있는 tolerance를 사용한다.
- RGB는 pixel exact match보다 ROI 통계·mask IoU·허용오차를 사용한다.
- 성능은 5회 이상 반복한 median과 p95를 비교한다.
- run 간 분산이 크면 개선으로 결론 내리지 말고 환경 noise를 먼저 찾는다.

## 13. 회귀시험 결과와 artifact를 구조화하다

권장 결과 구조는 다음과 같다.

```text
results/
└── 2026-08-31T120000Z/
    ├── manifest.json
    ├── asset_validator.txt
    ├── output.log
    ├── static_validation.json
    ├── joint_step.csv
    ├── camera_metrics.json
    ├── lidar_metrics.json
    ├── physics_only.json
    ├── render_sensor.json
    ├── gpu_samples.csv
    └── screenshots/
```

baseline과 current의 metric을 비교하는 최소 script는 다음과 같다.

```python
import json
import sys

baseline_path, current_path = sys.argv[1:3]
with open(baseline_path, encoding="utf-8") as f:
    baseline = json.load(f)
with open(current_path, encoding="utf-8") as f:
    current = json.load(f)

failures = []

# correctness는 absolute threshold를 사용한다.
hard_limits = {
    "joint_final_error_rad": ("max", 0.02),
    "camera_reprojection_rmse_px": ("max", 1.0),
    "lidar_plane_rmse_m": ("max", 0.02),
    "rtf": ("min", 1.0),
}
for key, (kind, limit) in hard_limits.items():
    value = current[key]
    if (kind == "max" and value > limit) or (kind == "min" and value < limit):
        failures.append(f"{key}={value} limit={kind} {limit}")

# tail latency는 같은 machine의 baseline 대비 허용 비율을 사용한다.
ratio = current["step_ms_p95"] / baseline["step_ms_p95"]
if ratio > 1.10:
    failures.append(f"step_ms_p95 ratio={ratio:.3f} > 1.10")

if failures:
    print("REGRESSION")
    print("\n".join(failures))
    raise SystemExit(1)
print("PASS")
```

CI가 Isaac Sim process의 실패를 놓치지 않도록 pipe 상태를 보존한다.

```bash
set -o pipefail
cd "$ISAACSIM_PATH"
./python.sh /abs/tests/run_regression.py \
  /abs/scenes/regression_scene.usd \
  2>&1 | tee /abs/results/output.log
```

Output Log에는 asset loading, PhysX, RTX와 extension error가 없는지 확인한다. 다만 log에 error가 없다는 사실만으로 합격시키지 않는다. 수치 assertion과 process exit code가 최종 gate이다.

## 14. 단계별 release gate를 운영하다

| gate | 실행 시점 | 반드시 통과할 항목 |
|---|---|---|
| G0 Source | URDF/MJCF/CAD 변경 | 단위, 이름, mesh path, source lint |
| G1 USD Static | import/authoring 직후 | default prim, dependency, schema, mass/collider |
| G2 Asset Validator | asset review | PhysicsRules, RobotRules, SimReadyAssetRules |
| G3 Component | sensor/controller 변경 | joint, drop, camera, LiDAR, IMU, contact 정답 시험 |
| G4 Integration | scene 조립 | navigation/manipulation 시나리오와 ROS contract |
| G5 Performance | release candidate | RTF, latency, RAM/VRAM과 품질 metric |
| G6 Reproducibility | 배포 직전 | clean machine/container에서 반복 실행 |

오류 severity도 정의한다.

- **P0**: stage load 실패, crash, NaN/Inf, 자산 손상이다. 즉시 release를 막는다.
- **P1**: joint 축, collider, sensor frame·unit·timestamp 계약 오류이다. release를 막는다.
- **P2**: 품질 metric 또는 성능 budget 실패이다. 요구사항에 따라 release를 막는다.
- **P3**: naming, thumbnail, 문서와 경고 정리 문제이다. 계획과 기한을 기록한다.

## 15. 최종 체크리스트

### custom robot

- [ ] Asset Validator의 PhysicsRules와 RobotRules 결과를 저장했다.
- [ ] articulation root가 정확히 하나이며 link/joint 관계가 맞다.
- [ ] mass, COM, inertia와 collider가 실물 scale에 맞다.
- [ ] 모든 joint의 축, 부호, limit, drive와 max force를 시험했다.
- [ ] command 없는 settle과 payload별 step response가 합격했다.
- [ ] self collision과 environment collision을 의도대로 시험했다.
- [ ] NaN, 관통, 발산 residual과 비정상 velocity가 없다.

### custom environment

- [ ] meter/Z-up, default prim, reference와 texture 이동성을 확인했다.
- [ ] invisible/visible collider를 겹쳐 보고 누락과 이중 collider를 찾았다.
- [ ] grid drop, wall/door proxy와 navigation corridor를 시험했다.
- [ ] physics material, semantics와 RTX non-visual material을 구분했다.
- [ ] movable prop의 rigid body, mass와 joint가 안정적이다.

### custom sensor

- [ ] parent, local pose, frame convention, unit와 range 계약이 있다.
- [ ] timestamp가 monotonic이고 실제 rate가 요구 범위에 있다.
- [ ] camera intrinsic/extrinsic, depth와 label mapping을 검사했다.
- [ ] LiDAR의 range/FOV/point pattern과 기준 평면 오차를 검사했다.
- [ ] IMU gravity 설정, axis, bias/filter와 동적 응답을 검사했다.
- [ ] contact/effort를 알려진 mass·lever arm과 비교했다.
- [ ] reset과 첫 valid frame을 consumer가 안전하게 처리한다.

### performance와 회귀시험

- [ ] physics-only, render-enabled, 실제 sensor/ROS workload를 따로 측정했다.
- [ ] warm-up을 제외하고 RTF와 p50/p95/p99를 저장했다.
- [ ] CPU/GPU/RAM/VRAM과 정확한 hardware 정보를 기록했다.
- [ ] 한 번에 한 변수만 최적화했다.
- [ ] 최적화 뒤 모든 correctness test를 다시 통과했다.
- [ ] 동일 초기 상태에서 여러 번 반복하고 분산을 확인했다.
- [ ] 접촉 중간 snapshot이 아니라 시작 상태부터 회귀시험을 실행했다.
- [ ] manifest, metric, log와 checksum을 함께 보관했다.

## 출처

- [Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)
- [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Simulation Data Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/ext_isaacsim_inspect_physics.html)
- [Omniverse Physics and PhysX SDK Limitations](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/physics_resources.html)
- [Tutorial 12: Asset Optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html)
- [Isaac Sim Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- [Profiling Performance Using Tracy](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)
- [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)
- [RTX Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx.html)
- [IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
- [Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)
- [Effort Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html)
- [ROS 2 Publish Real Time Factor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtf.html)
- [Isaac Sim Benchmarks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/benchmarks.html)
- [Replicator Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/troubleshooting.html)
