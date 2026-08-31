# 모바일 로봇과 매니퓰레이터

이 튜토리얼에서는 articulation이라는 공통 기반 위에서 모바일 로봇과 매니퓰레이터가 어떻게 다른 command를 사용하는지 익힌다. 모바일 로봇은 base 속도를 wheel joint 속도로 바꾸고, 매니퓰레이터는 task-space 목표를 joint action과 gripper 상태로 바꾼다.

## 1. 모바일 로봇의 kinematic 계약

차동 구동에서 원하는 선속도 \(V\), yaw 각속도 \(\omega\), 바퀴 반지름 \(r\), 좌우 바퀴 간 거리 \(l\)가 주어지면 다음 wheel angular velocity를 사용한다.

\[
\omega_R=\frac{2V+\omega l}{2r},\qquad
\omega_L=\frac{2V-\omega l}{2r}
\]

입력은 `m/s`, `rad/s`, 출력 wheel 속도는 `rad/s`이다. wheel radius와 wheel distance를 visual mesh가 아니라 실제 contact collider와 joint 위치에서 측정한다.

## 2. Jetbot 차동 구동 Standalone 예제

다음을 `drive_jetbot.py`로 저장한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np

from isaacsim.core.api import World
from isaacsim.robot.wheeled_robots.controllers.differential_controller import (
    DifferentialController,
)
from isaacsim.robot.wheeled_robots.robots import WheeledRobot
from isaacsim.storage.native import get_assets_root_path

try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=1.0 / 60.0,
        rendering_dt=1.0 / 60.0,
    )
    world.scene.add_default_ground_plane()

    root = get_assets_root_path()
    if root is None:
        raise RuntimeError("Isaac Sim asset root를 찾지 못했다")

    robot = world.scene.add(
        WheeledRobot(
            prim_path="/World/Robots/Jetbot",
            name="jetbot",
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
            create_robot=True,
            usd_path=root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
            position=np.array([0.0, 0.0, 0.0]),
        )
    )
    world.reset()

    print("DOFs:", list(robot.dof_names))
    controller = DifferentialController(
        name="jetbot_diff",
        wheel_radius=0.03,
        wheel_base=0.1125,
    )

    start, _ = robot.get_world_pose()

    # 2초 직진, 2초 좌회전, 1초 정지한다.
    for step in range(300):
        if step < 120:
            command = [0.25, 0.0]
        elif step < 240:
            command = [0.15, 0.8]
        else:
            command = [0.0, 0.0]

        robot.apply_wheel_actions(controller.forward(command))
        world.step(render=True)

    end, _ = robot.get_world_pose()
    displacement = np.linalg.norm(end[:2] - start[:2])
    print("start:", start, "end:", end, "xy displacement:", displacement)
    assert np.isfinite(displacement) and displacement > 0.1
finally:
    simulation_app.close()
```

```bash
cd ~/isaacsim
./python.sh /절대/경로/drive_jetbot.py
```

wheel command는 매 physics step 다시 적용하는 패턴이 명확하다. controller에 acceleration limit와 `dt`를 설정했다면 step마다 업데이트해야 ramp가 의도대로 동작한다.

### 검증 포인트

- 양의 선속도에서 좌우 바퀴가 같은 방향으로 도는가?
- 양의 yaw 명령에서 기대한 방향으로 회전하는가?
- 정지 명령 뒤 wheel velocity가 0으로 수렴하는가?
- 바닥 마찰을 바꾸면 slip과 odometry 오차가 예상대로 변하는가?

좌우가 바뀌거나 한 바퀴가 반대로 돌면 controller 수식을 바꾸기 전에 joint axis와 `wheel_dof_names` 순서를 확인한다.

## 3. 목표 pose로 이동하기

`DifferentialController`는 순간 base velocity를 wheel action으로 변환할 뿐 목표 위치까지의 feedback은 제공하지 않는다. `WheelBasePoseController`는 현재 pose와 goal pose를 받아 forward/yaw command를 만든 뒤 differential controller에 연결한다.

```python
from isaacsim.robot.wheeled_robots.controllers.wheel_base_pose_controller import (
    WheelBasePoseController,
)

pose_controller = WheelBasePoseController(
    name="go_to_pose",
    open_loop_wheel_controller=controller,
    is_holonomic=False,
)

position, orientation = robot.get_world_pose()
action = pose_controller.forward(
    start_position=position,
    start_orientation=orientation,
    goal_position=np.array([1.0, 0.5]),
)
robot.apply_wheel_actions(action)
```

API signature와 stop tolerance는 사용하는 5.1 controller 문서에서 확인한다. 실제 navigation에는 장애물 지도, global planner, localization, recovery가 더 필요하다. 이 controller 하나를 Nav2 대체물로 보지 않는다.

## 4. Holonomic과 Ackermann

### Holonomic

Mecanum/omni-wheel 로봇은 `[forward, lateral, yaw]` 속도를 명령할 수 있다. `HolonomicController`는 wheel position, orientation, radius와 roller angle로 joint drive command를 계산한다. 로봇 USD의 wheel joint에 mecanum radius와 angle 속성이 필요하며 `HolonomicRobotUsdSetup`으로 authoring을 자동화할 수 있다.

```python
from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import (
    HolonomicController,
)

holonomic = HolonomicController(
    name="omni_base",
    wheel_radius=[0.04, 0.04, 0.04],
    wheel_positions=[
        [-0.098, 0.001, -0.051],
        [0.049, -0.085, -0.051],
        [0.050, 0.086, -0.051],
    ],
    wheel_orientations=[
        [0.0, 0.0, 0.0, 1.0],
        [0.866, 0.0, 0.0, -0.5],
        [0.866, 0.0, 0.0, 0.5],
    ],
    mecanum_angles=[90.0, 90.0, 90.0],
)
wheel_action = holonomic.forward([0.3, 0.1, 0.2])
```

orientation quaternion의 순서는 해당 controller 예제 계약을 그대로 따른다. custom robot 값은 CAD/joint frame에서 산출해 검증한다.

### Ackermann

Ackermann 차량은 steering joint position과 wheel joint velocity를 별도로 제어한다. wheelbase, track width, turning radius와 steering angle 관계가 중요하다. `AckermannController` 결과를 steering joint indices와 drive wheel indices에 나누어 적용한다.

```python
from isaacsim.robot.wheeled_robots.controllers.ackermann_controller import (
    AckermannController,
)

ackermann = AckermannController(
    "car_controller",
    wheel_base=1.65,
    track_width=1.25,
    front_wheel_radius=0.25,
    back_wheel_radius=0.25,
)
action = ackermann.forward(
    [
        0.1,  # desired steering angle
        0.0,  # steering velocity
        1.1,  # desired forward velocity
        0.0,  # acceleration
        0.0,  # dt: acceleration limit을 쓰지 않는 예제
    ]
)
```

5.1 controller의 입력 순서는 `[steering_angle, steering_velocity, forward_velocity, acceleration, dt]`이다. acceleration limit을 사용하면 실제 physics dt를 마지막 원소에 넣는다. controller 출력에서 steering target과 wheel velocity를 어느 joint에 보낼지 이름 기반으로 매핑한다.

## 5. 모바일 로봇 튜닝 순서

1. wheel collider radius와 joint axis를 확정한다.
2. base mass, center of mass와 inertia를 확인한다.
3. wheel/ground physics material을 설정한다.
4. 공중에서 wheel velocity command를 시험해 부호와 순서를 확인한다.
5. 평면에서 직진·제자리 회전을 시험한다.
6. commanded velocity와 실제 base velocity를 기록한다.
7. acceleration/deceleration과 max wheel speed limit를 적용한다.
8. 경사, 턱, payload에서 slip과 접촉 안정성을 시험한다.

시각적으로 경로가 비슷한지만 보지 말고 다음 지표를 남긴다.

```python
position, _ = robot.get_world_pose()
linear_velocity = robot.get_linear_velocity()
wheel_velocity = robot.get_joint_velocities()
```

## 6. 매니퓰레이터 wrapper의 역할

일반 `SingleArticulation`도 arm joint를 제어할 수 있지만 robot-specific manipulator wrapper는 다음 정보를 함께 제공한다.

- `end_effector` prim wrapper
- parallel 또는 suction `gripper`
- open/closed joint position
- robot-specific controller와 task
- 기본 USD와 joint name 계약

Franka 예제의 `Franka` wrapper와 `PickPlaceController`를 사용해 전체 파이프라인을 확인한다.

## 7. Franka pick-and-place Standalone 예제

다음을 `franka_pick_place.py`로 저장한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np

from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.robot.manipulators.examples.franka import Franka
from isaacsim.robot.manipulators.examples.franka.controllers import (
    PickPlaceController,
)

try:
    world = World(
        stage_units_in_meters=1.0,
        physics_dt=1.0 / 60.0,
        rendering_dt=1.0 / 60.0,
    )
    world.scene.add_default_ground_plane()

    franka = world.scene.add(
        Franka(prim_path="/World/Robots/Franka", name="franka")
    )
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Props/Cube",
            name="cube",
            position=np.array([0.30, 0.30, 0.30]),
            scale=np.array([0.0515, 0.0515, 0.0515]),
            color=np.array([0.0, 0.2, 1.0]),
        )
    )

    world.reset()
    franka.gripper.set_joint_positions(
        franka.gripper.joint_opened_positions
    )

    controller = PickPlaceController(
        name="pick_place",
        gripper=franka.gripper,
        robot_articulation=franka,
    )
    goal = np.array([-0.30, -0.30, 0.0515 / 2.0])

    done = False
    for step in range(12000):
        cube_position, _ = cube.get_world_pose()
        action = controller.forward(
            picking_position=cube_position,
            placing_position=goal,
            current_joint_positions=franka.get_joint_positions(),
        )
        franka.apply_action(action)
        world.step(render=True)

        if controller.is_done():
            done = True
            print("controller completed at step", step)
            break

    final_position, _ = cube.get_world_pose()
    print("cube final:", final_position, "goal:", goal)
    assert np.all(np.isfinite(final_position))
    if not done:
        print("WARN: allotted steps 안에 state machine이 끝나지 않았다")
finally:
    simulation_app.close()
```

`PickPlaceController`는 접근, 하강, grasp, 상승, 이동, release 같은 phase를 가진 state machine이다. 완료되지 않으면 단순히 반복 수만 늘리지 말고 어느 phase에서 멈췄는지, cube가 실제로 잡혔는지, IK/drive가 목표를 추종하는지 확인한다.

## 8. Gripper를 이해하기

### Parallel gripper

- finger joint names와 open/closed position을 정의한다.
- mimic joint가 있으면 주 joint와 관계를 확인한다.
- fingertip collider와 마찰을 별도 튜닝한다.
- object 폭이 joint range 안에 있는지 확인한다.

### Surface gripper

Surface Gripper extension은 흡착형 end effector를 모델링한다. parent path, offset, grip threshold와 force/torque limit를 설정하고 접촉 조건에서 close/open한다. 강제로 물체를 순간 이동시키는 방식과 다르므로 gripper frame, collider와 접근 pose가 중요하다.

Grasp Editor는 grasp pose를 authoring하는 데 유용하다. 어떤 gripper든 “controller가 close를 호출했다”와 “물체가 실제 부착되었다”를 별도 상태로 검사한다.

## 9. Task로 장면과 평가 분리하기

Core `BaseTask`는 다음 책임을 나눈다.

```python
from isaacsim.core.api.tasks import BaseTask


class ReachTask(BaseTask):
    def set_up_scene(self, scene):
        super().set_up_scene(scene)
        # 로봇, 목표와 환경을 추가한다.

    def get_observations(self):
        # controller에 필요한 상태를 dict로 반환한다.
        return {}

    def pre_step(self, control_index, simulation_time):
        # 매 step metric/종료 조건을 갱신한다.
        pass

    def post_reset(self):
        # episode 상태와 gripper/controller를 초기화한다.
        pass

    def calculate_metrics(self):
        return {"position_error": 0.0}

    def is_done(self):
        return False
```

Task는 scene 생성, observation, metric과 종료 조건을 묶고 controller는 observation을 action으로 바꾼다. 이 둘을 분리하면 같은 task에 서로 다른 controller를 비교할 수 있다.

## 10. 여러 로봇과 여러 task

각 로봇과 task에 고유한 namespace와 `offset`을 둔다.

```text
/World/envs/env_0/Franka
/World/envs/env_0/Target
/World/envs/env_1/Jetbot
/World/envs/env_1/Goal
```

- name과 prim path를 모두 고유하게 만든다.
- physics callback 이름도 고유하게 만든다.
- observation dict의 key 계약을 문서화한다.
- 여러 task가 같은 joint에 동시에 action을 보내지 않게 arbitration한다.
- 다수 환경에서는 vectorized `Articulation`/`RigidPrim` view와 Cloner를 고려한다.

## 11. 실패를 계층별로 나누기

| 증상 | kinematics/controller | physics/asset |
|---|---|---|
| EE가 목표 반대편으로 감 | EE frame, joint order, quaternion | joint axis/import 변환 |
| 경로는 맞는데 크게 뒤처짐 | 목표 속도, control dt | gain, effort/velocity limit |
| 물체를 끼웠는데 빠짐 | close timing, grasp pose | fingertip friction, collider, effort |
| 모바일 로봇이 원을 그림 | wheel radius/order calibration | 좌우 마찰·질량 비대칭 |
| 정지 명령에도 움직임 | command persistence, controller reset | damping, slope, 접촉 |

## 12. 검증 체크포인트

- [ ] Jetbot이 0.1 m 이상 이동하고 유한한 pose를 반환했다.
- [ ] wheel radius, base와 DOF 순서를 자산에서 확인했다.
- [ ] differential, holonomic, Ackermann controller의 입력 차이를 안다.
- [ ] Franka wrapper의 gripper와 end-effector가 초기화되었다.
- [ ] pick-and-place controller의 phase와 `is_done()`을 검사했다.
- [ ] task, controller, robot asset의 책임을 분리했다.
- [ ] 여러 로봇이 같은 prim/name/callback을 공유하지 않는다.

## 출처

- [Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)
- [Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)
- [Mobile Robot Controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html)
- [Adding a Manipulator Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html)
- [Adding Multiple Robots](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html)
- [Multiple Tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html)
- [Surface Gripper Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html)
- [Grasp Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html)
