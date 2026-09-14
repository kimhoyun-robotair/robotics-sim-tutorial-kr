# 03 — Manipulator Pick & Place Cell

## Goal / Architecture / Execution Context

**Isaac Sim 5.1.0 · Standalone Python.** Franka Panda, 작은 cube, 정적 장애물, 놓을 위치를 생성합니다. 동일한 scene에서 IK, RRT, RMPflow 기반 pick & place를 각각 실행합니다.

```text
pick-place: 접근 → 하강 → gripper 닫기 → lift → 이동 → 내려놓기 → 열기
                   ↓ 실제 cube contact / 높이 / 최종 위치를 측정
ik: target → Lula IK → joint positions
rrt: target + obstacle → Lula RRT → waypoint actions
```

RMPflow는 reactive motion policy, RRT는 path planner입니다. 기본 pick & place는 RMPflow controller를 이용하는 상태 기계이고, `--mode rrt`는 별도의 경로 계획 실험입니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [RMPflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow.html)
- NVIDIA Isaac Sim 5.1 — [Lula RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html)

## Dependencies / How to Run

Isaac Sim 설치와 Franka USD 접근이 필요합니다. 별도 ROS 또는 pip 설치는 필요 없습니다. 저장소 루트에서:

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" src/03_manipulator_pick_place/run.py --mode ik --steps 240
"$ISAAC_SIM_PATH/python.sh" src/03_manipulator_pick_place/run.py --mode rrt
"$ISAAC_SIM_PATH/python.sh" src/03_manipulator_pick_place/run.py --headless --mode pick-place
```

pick & place는 controller 완료 후 추가 120 step을 관측합니다. 짧은 `--steps`로 task를 중간에 끝내면 완료 판정 실패로 종료할 수 있습니다. `summary.json`의 `success`를 함께 확인하세요.

## USD Assets / Robot Model / Physics Configuration / APIs Used

| 항목 | 설정 |
|---|---|
| Franka reference | `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd` |
| Prim | `/World/Franka`, `/World/Cube`, `/World/Obstacle`, `/World/Target` |
| Cube | 한 변 0.0515m, mass 0.05kg, `DynamicCuboid` |
| Obstacle | 0.10×0.10×0.24m, `FixedCuboid`; RMPflow/RRT에도 등록 |
| Target | visual marker, collider 없음 |
| Physics dt | 1/60초 |
| Robot physics | 원본 USD의 articulation·joint drive·mass·inertia |
| Kinematics | `KinematicsSolver`, end-effector frame `right_gripper` |
| Control | `RMPFlowController` + `PickPlaceController` / `PathPlannerVisualizer` |
| Contact / effort | `ContactSensor` raw body pair + `get_measured_joint_efforts()` |

contact sensor는 cube 아래에 두어 접촉 상대 body가 손가락인지 확인합니다. 바닥에 닿은 것만으로 grasp라 판정하지 않습니다. 양의 force만이 아니라 **finger contact와 cube의 5cm 이상 상승이 같은 step에서 관측되는지**를 확인합니다. 이는 교육용 판정이며 force closure의 증명은 아닙니다.

### Sources

- NVIDIA 공식 v5.1.0 소스 — [Franka pick up](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/standalone_examples/api/isaacsim.robot.manipulators/franka_pick_up.py)
- NVIDIA Isaac Sim 5.1 — [Lula Kinematics Solver](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_kinematics.html)
- NVIDIA Isaac Sim 5.1 — [Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)
- NVIDIA Isaac Sim 5.1 — [Articulation Joint Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html)

## 결과 / 공부 순서

[run.py](run.py)를 scene 생성 → controller 생성 → 각 mode의 action 생성 → 관측 → 판정 순서로 읽으세요.

`manipulation.csv`는 cube pose, 접촉 force, finger 접촉 여부, grasp 판정, joint 7 effort를 기록합니다. `summary.json`은 controller 완료와 실제 task 성공을 따로 기록합니다. pick & place 성공에는 grasp 관측·controller 완료·최종 3D 위치 오차 8cm 미만을 모두 요구합니다.

실제 headless 검증에서 cube 최대 높이는 약 0.396m, 최종 위치 오차는 약 6.6mm였고 grasp contact와 성공 판정을 확인했습니다. 이 값은 하나의 실행 결과이며 모든 asset·설정에서의 보장은 아닙니다.

- cube mass만 0.2kg으로 바꾸고 contact/effort가 어떻게 달라지는지 봅니다.
- obstacle 높이를 올리고 RMPflow가 멈추는 상황과 RRT가 경로를 찾는 상황을 비교합니다.
- IK가 해를 찾았어도 경로 전체가 collision-free인 것은 아닌 이유를 설명해봅니다.
- state machine 완료를 실제 grasp 성공으로 간주하면 생기는 오류를 로그로 찾아봅니다.

## Known Limitations / Relevant Documentation

RRT waypoint는 일정 step씩 유지하며 엄밀한 속도·가속도 제한을 보장하는 trajectory retiming을 하지 않습니다. RMPflow/RRT의 장애물 모델에 **손에 잡힌 cube의 형상까지 자동 등록하지 않습니다**. 복잡한 운반 경로를 만들 때는 이를 추가해야 합니다. contact raw data는 이 5.1 설치에서 deprecated 경고가 발생하므로 이후 버전으로 옮길 때 재검토하세요. 여기서는 상대 body를 확인하기 위해 유지했습니다. effort는 별도 `EffortSensor` Prim을 생성하는 방식 대신 Core articulation joint 측정 API를 실습합니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Lula RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html)
- NVIDIA 공식 v5.1.0 소스 — [ContactSensor 구현](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/extensions/isaacsim.sensors.physics/python/impl/contact_sensor.py)
