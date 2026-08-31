# Articulation, Joint와 Controller

로봇은 rigid link들을 joint로 연결한 시스템이다. Isaac Sim에서는 이를 PhysX **articulation**으로 묶어 일반 강체 집합보다 효율적이고 안정적으로 푼다. 이 튜토리얼에서는 joint를 구성하고, drive를 조정하고, `ArticulationAction`으로 제어한다.

## 1. 로봇의 물리 계층

일반적인 articulation은 다음 의미를 갖는다.

```text
Articulation root
  base_link (rigid body)
    joint_1 ── link_1 (rigid body)
                 joint_2 ── link_2 (rigid body)
                              ...
```

- 각 link는 질량·관성·collider를 가진 rigid body이다.
- joint는 parent body와 child body, 각 body 쪽 local frame과 운동 축을 정의한다.
- articulation root API는 PhysX가 전체 연결계를 하나의 articulation으로 다루게 한다.
- 고정형 매니퓰레이터는 base를 world에 고정하는 fixed/root joint가 필요하다.
- 모바일 로봇은 base가 움직일 수 있어야 하므로 root를 world에 고정하지 않는다.

Articulation은 기본적으로 tree topology에 적합하다. 4절 링크처럼 닫힌 고리는 공식 closed-loop rigging 절차에 따라 loop-closing joint를 articulation 계산에서 제외하는 등 별도 구성이 필요하다. 단순히 joint를 하나 더 연결하면 과구속과 solver 불안정이 생길 수 있다.

## 2. Joint 종류와 속성

| joint | 자유도 | 예 |
|---|---:|---|
| Fixed | 0 | 센서 브래킷, base 고정 |
| Revolute | 회전 1 | 로봇 팔, 바퀴 |
| Prismatic | 직선 1 | 리니어 액추에이터, 승강축 |
| Spherical | 회전 3 | 구면 연결 구조 |
| Distance | 거리 제약 | 특수 기구 |

Revolute와 prismatic joint는 일반적으로 lower/upper limit, axis, local pose, drive를 가진다. joint frame이 시각 mesh 원점과 같다고 가정하지 않는다. joint를 선택하고 Physics visualization으로 parent/child frame과 축을 확인한다.

### GUI에서 두 링크 연결하기

1. 두 Cube를 만들고 각각 `Rigid Body with Colliders Preset`을 적용한다.
2. 첫 body를 world에 고정하거나 static base로 정한다.
3. 두 prim을 선택하고 Physics Authoring 도구 또는 `Create > Physics > Joints > Revolute Joint`로 joint를 만든다.
4. Body 0/Body 1 relationship이 올바른지 확인한다.
5. local pose를 joint 축 위치에 맞춘다.
6. lower/upper limit를 지정한다.
7. joint에 Drive API를 추가하고 target, stiffness, damping, max force를 설정한다.
8. 상위 로봇 prim에 Articulation Root API를 적용한다.
9. Play한 뒤 Physics Inspector에서 drive target을 천천히 바꾼다.

## 3. Drive와 제어 모드

joint drive는 목표와 실제 상태 차이를 force/torque로 바꾼다. 개념적으로 position drive는 다음 PD 형태이다.

\[
\tau = K_p(q_{target}-q) + K_d(\dot q_{target}-\dot q)
\]

| 목표 | 권장 drive 설정 | 설명 |
|---|---|---|
| 위치 제어 | `Kp > 0`, `Kd >= 0` | 목표 각도/변위로 수렴한다. |
| 속도 제어 | `Kp = 0`, `Kd > 0` | 목표 속도를 추종한다. |
| effort 제어 | `Kp = 0`, `Kd = 0` 또는 drive 제거 | 별도 drive가 effort 명령과 싸우지 않게 한다. |

한 joint에 position과 effort 같은 서로 다른 제어 방식을 동시에 적용하지 않는다. `maxEffort`가 너무 작으면 목표에 못 가고, 너무 크고 gain도 높으면 접촉 시 불안정해질 수 있다.

### natural frequency 방식으로 gain 생각하기

Importer와 Gain Tuner는 natural frequency와 damping ratio를 이용할 수 있다.

\[
K_p=m_{eq}\omega_n^2, \qquad
K_d=2m_{eq}\zeta\omega_n
\]

여기서 \(m_{eq}\)는 joint에서 본 등가 관성, \(\omega_n\)은 natural frequency, \(\zeta\)는 damping ratio이다. \(\zeta=1\)은 임계 감쇠의 기준이다. 같은 Kp를 모든 joint에 복사하기보다 각 축의 등가 관성과 목표 bandwidth를 반영한다.

## 4. 단위 함정

- `ArticulationController`의 angular position과 velocity는 radian, rad/s를 사용한다.
- raw USD의 angular joint/drive target 속성은 degree 계열로 authoring되는 경우가 있으며 Core controller가 변환을 처리한다.
- prismatic joint는 Stage 길이 단위를 따른다. `stage_units_in_meters=1.0`을 권장한다.
- quaternion 배열은 사용 API가 기대하는 순서가 무엇인지 확인한다. Core API는 흔히 `(w, x, y, z)`를 사용한다.

raw `UsdPhysics.DriveAPI`와 Core `ArticulationController`를 섞어 값을 쓸 때 degree와 radian을 다시 확인한다.

## 5. `SingleArticulation`으로 Franka 제어하기

다음을 `control_franka.py`로 저장한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np

from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path

try:
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    assets_root = get_assets_root_path()
    if assets_root is None:
        raise RuntimeError("Isaac Sim asset root를 찾지 못했다")

    usd_path = (
        assets_root
        + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
    )
    robot_path = "/World/Robots/Franka"
    add_reference_to_stage(usd_path, robot_path)

    robot = world.scene.add(
        SingleArticulation(prim_path=robot_path, name="franka")
    )

    # physics handle, DOF metadata와 controller는 reset 뒤 유효하다.
    world.reset()

    print("DOF count:", robot.num_dof)
    print("DOF names:", list(robot.dof_names))
    q0 = robot.get_joint_positions()
    print("initial q:", q0)

    target = np.array(
        [0.0, -1.0, 0.0, -2.2, 0.0, 2.4, 0.8, 0.04, 0.04],
        dtype=np.float32,
    )
    if target.shape != q0.shape:
        raise RuntimeError(f"target {target.shape} != robot DOF {q0.shape}")

    robot.apply_action(ArticulationAction(joint_positions=target))
    for _ in range(300):
        world.step(render=True)

    q = robot.get_joint_positions()
    error = np.abs(target - q)
    print("final q:", q)
    print("absolute error:", error)
    assert np.all(np.isfinite(q))
finally:
    simulation_app.close()
```

```bash
cd ~/isaacsim
./python.sh /절대/경로/control_franka.py
```

모든 joint error가 완전히 0이 되는 것을 기대하지 않는다. gravity, gain, effort limit, 접촉과 simulation time이 영향을 준다. 먼저 NaN이 없고 joint가 limit 안에서 목표 방향으로 움직였는지 확인한다.

## 6. 일부 joint만 안전하게 명령하기

index를 숫자로 외우지 말고 이름에서 구한다.

```python
finger_indices = np.array(
    [
        robot.get_dof_index("panda_finger_joint1"),
        robot.get_dof_index("panda_finger_joint2"),
    ],
    dtype=np.int32,
)

close_gripper = ArticulationAction(
    joint_positions=np.array([0.0, 0.0], dtype=np.float32),
    joint_indices=finger_indices,
)
robot.apply_action(close_gripper)
```

`joint_indices` 길이와 각 command 배열 길이는 같아야 한다. `0.0`은 유효한 목표값이다. 제어하지 않을 축은 0을 넣어 표현하지 말고 해당 command 필드를 생략하거나 `joint_indices`로 subset을 명시한다.

### 상태 변경과 제어 명령의 차이

```python
# 상태를 즉시 바꾸는 teleport 계열이다. 초기화/복구 외에는 신중히 쓴다.
robot.set_joint_positions(target)

# drive가 물리적으로 목표를 추종하게 하는 제어 명령이다.
robot.apply_action(ArticulationAction(joint_positions=target))
```

학습 데이터나 성능 평가에서 매 step `set_joint_positions`를 사용하면 접촉·관성·actuator dynamics를 우회하므로 잘못된 결과가 된다.

## 7. `ArticulationController` 직접 사용하기

`SingleArticulation`은 내부 controller를 자동으로 만든다.

```python
controller = robot.get_articulation_controller()

controller.apply_action(
    ArticulationAction(
        joint_positions=np.array([0.2], dtype=np.float32),
        joint_indices=np.array([0], dtype=np.int32),
    )
)
```

여러 로봇을 vectorized 방식으로 다룰 때는 `Articulation` view를 만들고 physics가 시작된 뒤 controller를 그 view로 초기화할 수 있다.

```python
from isaacsim.core.prims import Articulation
from isaacsim.core.api.controllers.articulation_controller import ArticulationController

view = Articulation(
    prim_paths_expr="/World/envs/env_.*/Robot",
    name="robot_view",
)
world.scene.add(view)
world.reset()

controller = ArticulationController()
controller.initialize(view)
```

prim expression은 실제 Stage 경로와 view API가 지원하는 패턴에 맞춘다. `world.reset()` 전에 view 데이터를 읽지 않는다.

## 8. gain 읽기와 조정

```python
controller = robot.get_articulation_controller()
kps, kds = controller.get_gains()
print("Kp:", kps)
print("Kd:", kds)

# 예: 첫 arm joint만 소폭 낮춘다. 원본 배열을 복사해 변경한다.
new_kps = kps.copy()
new_kps[0] *= 0.8
controller.set_gains(kps=new_kps, kds=kds)
```

gain 튜닝 절차는 다음과 같다.

1. collider 겹침, mass와 inertia부터 바로잡는다.
2. payload와 대표 pose를 정한다.
3. 낮은 target 속도와 작은 step response로 시작한다.
4. Kp를 올려 필요한 tracking을 확보한다.
5. overshoot와 진동을 Kd로 감쇠한다.
6. max effort/velocity가 병목인지 확인한다.
7. free-space뿐 아니라 접촉과 singular pose에서도 시험한다.
8. Gain Tuner 결과를 자산 USD 또는 구성 파일에 명시적으로 저장한다.

## 9. 사용자 정의 controller

Isaac Sim controller는 고수준 command를 `ArticulationAction`으로 바꾸는 객체로 구성할 수 있다.

```python
import numpy as np
from isaacsim.core.api.controllers import BaseController
from isaacsim.core.utils.types import ArticulationAction


class DifferentialDriveController(BaseController):
    def __init__(self, wheel_radius, wheel_base):
        super().__init__(name="differential_drive")
        self._r = float(wheel_radius)
        self._l = float(wheel_base)

    def forward(self, command):
        linear, yaw_rate = map(float, command)
        left = (2.0 * linear - yaw_rate * self._l) / (2.0 * self._r)
        right = (2.0 * linear + yaw_rate * self._l) / (2.0 * self._r)
        return ArticulationAction(
            joint_velocities=np.array([left, right], dtype=np.float32)
        )
```

controller는 Stage를 직접 수정하기보다 action을 반환하게 만들면 테스트하기 쉽다.

```python
ctrl = DifferentialDriveController(wheel_radius=0.03, wheel_base=0.1125)
action = ctrl.forward([0.2, 0.5])
assert np.allclose(
    action.joint_velocities,
    [(0.4 - 0.5 * 0.1125) / 0.06,
     (0.4 + 0.5 * 0.1125) / 0.06],
)
```

## 10. 관절 힘 읽기

```python
commanded_effort = robot.get_applied_joint_efforts()
measured_effort = robot.get_measured_joint_efforts()
spatial_forces = robot.get_measured_joint_forces()

print(commanded_effort.shape, measured_effort.shape, spatial_forces.shape)
```

`get_measured_joint_forces()`는 base의 incoming joint를 포함해 `(num_joints + 1, 6)` 형태가 될 수 있다. 특정 DOF index와 행을 같은 것으로 단정하지 말고 API 문서의 joint metadata와 `joint_index + 1` 규칙을 확인한다. 첫 세 값은 force, 뒤 세 값은 torque이며 child joint frame 기준이다.

## 11. Reset 설계

초기 pose를 재현하려면 default state를 설정한다.

```python
robot.set_joints_default_state(
    positions=target,
    velocities=np.zeros(robot.num_dof, dtype=np.float32),
    efforts=np.zeros(robot.num_dof, dtype=np.float32),
)
world.reset()
```

Extension 예제에서는 Toolbar의 Stop→Play가 사용자 객체, controller 내부 상태와 task를 모두 초기화하지 않을 수 있다. 제공한 Reset 버튼에서 다음을 함께 수행한다.

- `world.reset_async()`
- controller의 integral/filter/path state 초기화
- RMPflow 또는 behavior state 초기화
- 관측 buffer와 logger episode 구분
- random seed 정책에 따른 scene randomization

## 12. 흔한 실패와 진단

| 증상 | 먼저 확인할 것 |
|---|---|
| `handlers are not initialized` | `world.reset()`/`reset_async()` 뒤 읽었는가? |
| 로봇이 폭발한다 | 초기 collider 겹침, 잘못된 mass/inertia, 과도한 gain |
| 위치 목표에 가지 않는다 | Kp, max effort, joint limit, 명령 joint 순서 |
| 속도 명령인데 위치로 복귀한다 | position stiffness가 0이 아닌가? |
| effort 명령이 이상하다 | drive stiffness/damping이 effort와 동시에 작동하는가? |
| base가 떨어진다 | 고정형 로봇의 root/fixed joint가 올바른가? |
| 바퀴가 돌지만 차가 안 간다 | collider·축·마찰·wheel radius와 joint velocity 단위 |
| 일부 joint가 반대로 돈다 | joint axis와 parent/child frame, URDF axis 변환 |

## 13. 검증 체크포인트

- [ ] articulation root, link, joint와 drive의 역할을 구분한다.
- [ ] `robot.dof_names`를 출력한 뒤 명령을 만들었다.
- [ ] 위치·속도·effort 모드를 한 joint에서 충돌시키지 않았다.
- [ ] `ArticulationAction` subset의 indices와 값 길이가 같다.
- [ ] 상태 teleport와 물리 drive 명령의 차이를 안다.
- [ ] reset 뒤 controller와 behavior 내부 상태도 초기화한다.

## 출처

- [Articulation Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)
- [Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)
- [Tutorial 3: Articulate a Basic Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_simple_robot.html)
- [Tutorial 10: Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Tutorial 11: Tuning Joint Drive Gains](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)
- [Articulation Joint Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html)
