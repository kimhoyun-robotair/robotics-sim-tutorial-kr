# 55. Lula Trajectory Generator: 점을 시간 궤적으로

권장 학습 순서 **55** · 로봇 제어와 동작 계획 · 출처 ID `t139`

UR10으로 c-space 최적 시간 궤적, timestamped 궤적, task-space 직선 경로, 복합 path spec을 각각 생성합니다. 공식 예제의 핵심 모드를 독립 실행 옵션으로 제공하고 실제 관절 추종 상태를 기록합니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

5.1 Assets의 `Isaac/Robots/UniversalRobots/ur10/ur10.usd`와 종속 파일이 필요합니다. 설정은 설치된 `isaacsim.robot_motion.motion_generation/motion_policy_configs/universal_robots/ur10/ur10_robot.urdf`와 `rmpflow/ur10_robot_description.yaml`에서 읽습니다. 별도 학습 모델은 필요 없습니다.

터미널에서 이 패키지 폴더(`55_motion_manipulators_lula_trajectory_generator`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --trajectory cspace
"$ISAAC_SIM_ROOT/python.sh" run.py --trajectory timestamped
"$ISAAC_SIM_ROOT/python.sh" run.py --trajectory taskspace
"$ISAAC_SIM_ROOT/python.sh" run.py --trajectory composite
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 작업공간과 바닥

UR10의 고정 base는 월드 원점에 두고, 참조용 바닥은 **z=−2 m**에 둡니다. 원문의 관절 waypoint를 그대로 유지하면 로봇의 일부 링크가 base보다 아래로 내려갑니다. 예를 들어 첫 waypoint의 shoulder lift 0.5 rad에서는 elbow frame의 높이가 URDF 기준 `0.1273 − 0.612·sin(0.5) ≈ −0.166 m`입니다. 여기에 z=0의 물리 바닥을 추가하면 관절 구동이 바닥 충돌에 막혀 trajectory target을 따라가지 못합니다.

이 장면은 고정된 로봇을 열린 작업공간에서 움직이는 궤적 실습입니다. 바닥을 낮추어 원문의 경로를 위한 공간을 확보하며, 로봇의 collision과 물리 drive는 유지합니다. base mount가 실제 어떤 구조에 고정되는지는 이 실습에서 모델링하지 않습니다. 결과의 `ground_plane_z_m`에 사용한 바닥 높이를 기록합니다. 실제 작업대·장애물을 추가하려면 먼저 전체 링크 경로의 충돌 여유를 확인해야 합니다.

## 단계별 실습

1. cspace 실행에서 빨간 waypoint marker를 확인합니다. 6개 값으로 된 UR10 관절 waypoint를 FK로 변환하여 표시합니다. joint 공간에서 부드럽게 이어도 end-effector가 task-space 직선으로 움직인다는 뜻은 아닙니다.
2. timestamped 모드는 같은 waypoint를 `[0,5,10,13]`초에 통과하도록 요구합니다. 총 재생이 끝나려면 적어도 13×60 스텝이 필요하며 종료 뒤 마지막 target을 유지합니다.
3. taskspace 모드는 `[0.3,−0.3,0.1]`에서 시작하는 직사각형의 다섯 점과 고정 quaternion `[0,1,0,0]`을 전달합니다. `ee_link` frame의 위치/orientation을 task space에서 연결합니다.
4. composite 모드는 task-space의 translation, rotation, three-point arc에 c-space 경로를 연결합니다. 초기 configuration과 path 사이에는 `TransitionMode.FREE`를 사용합니다. 이 연결 구간은 직선 task-space 이동으로 제한되지 않습니다.
5. `trajectory.json`의 action_count와 duration_s를 확인합니다. completed_sequence가 false라면 창을 더 오래 열어 두거나, 제한 실행에서 `--steps`를 늘려 전체 궤적을 재생합니다. GUI는 궤적 재생 뒤에도 마지막 목표를 유지하며 물리를 계속 갱신합니다. trace의 target_positions와 measured_positions 차이는 물리 drive의 추종 오차입니다.

## API와 시간간격

`LulaCSpaceTrajectoryGenerator.compute_c_space_trajectory()`는 위치 waypoint를 joint velocity/acceleration/jerk 제한 안에서 spline으로 잇고 시간을 선택합니다. `compute_timestamped_c_space_trajectory()`는 지정한 통과 시각도 사용합니다. 제한에 맞는 해를 못 찾으면 None을 반환하므로 이 코드는 명시적인 오류를 내며 멈춥니다.

`LulaTaskSpaceTrajectoryGenerator.compute_task_space_trajectory_from_points()`는 위치와 w,x,y,z quaternion을 각 점에 요구합니다. `compute_task_space_trajectory_from_path_spec()`는 여러 방식으로 정의된 경로를 받습니다. `ArticulationTrajectory(..., physics_dt=1/60)`는 그 연속 궤적을 로봇이 사용할 ArticulationAction 열로 샘플링합니다. 실제 World의 dt도 1/60로 맞춥니다.

첫 action의 joint_positions로 시작 상태를 한 번 설정합니다. 이는 예제 시작을 맞추기 위한 teleport이며 재생 중에는 `apply_action()`으로 drive target을 전달합니다. 반대 순서로 매 스텝 `set_joint_positions()`를 호출하면 실제 물리 추종을 측정하지 못합니다.

## 고급 path spec 실험

코드의 composite 분기에서 `lula.create_task_space_path_spec(Pose3(rotation, translation))` 이후 다음 중 한 동작만 교체하여 실행합니다.

- `add_linear_path(Pose3(...))`: 위치와 회전을 함께 보간합니다.
- `add_translation(...)`, `add_rotation(...)`: 나머지 pose 성분을 고정합니다.
- `add_three_point_arc(target, midpoint, constant_orientation=True)`: 중간점을 통과하는 원호에 고정 방향을 사용합니다. false면 접선 방향을 사용합니다.
- `add_three_point_arc_with_orientation_target(Pose3(...), midpoint)`: 끝 orientation도 요구합니다.
- `add_tangent_arc(target, constant_orientation=True/False)` 또는 `add_tangent_arc_with_orientation_target(Pose3(...))`: 이전 경로 접선에 맞는 원호를 연결합니다.

`create_c_space_path_spec(q)`와 `add_c_space_waypoint(q_next)`는 관절 경로를 정의합니다. composite에 추가할 때 FREE는 연결 방법을 자유롭게, LINEAR_TASK_SPACE는 새 task path까지 말단 직선으로, SKIP은 새 path의 첫 점을 건너뛰어 연결합니다. geometry가 성립하지 않는 arc나 한계 근처 waypoint는 생성 실패가 될 수 있습니다. 원문 고급 예제의 모든 arc 종류를 위 실험에서 독립적으로 바꿔 볼 수 있게 설명합니다.

## 관찰 기준과 한 변수 실험

동일 cspace waypoint에서 `--trajectory`만 cspace와 timestamped로 바꾸어 duration과 관절 추종을 비교합니다. marker를 통과하는 것과 collision-free라는 것은 다릅니다. trajectory generator는 이 예제에서 장애물 검사나 전역 계획을 수행하지 않습니다.

## 문제 해결

UR10 대신 다른 robot USD를 쓰면 descriptor/URDF/frame/6개 waypoint가 모두 맞아야 합니다. None 반환 시 joint limit에 너무 가까운 점, 도달 불가능한 pose, 불가능한 통과 시간을 확인합니다. 일부 관절의 측정값만 목표와 크게 벌어진 채 고정되면 바닥·작업대와의 접촉을 먼저 확인합니다. 특히 shoulder lift가 약 0.109 rad에 막히는 현상은 원점 높이의 바닥을 추가했을 때 관찰된 증상입니다. 그래픽이 느려도 simulation dt는 설정값이므로 벽시계 시간으로 trajectory duration을 판단하지 않습니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Lula Trajectory Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_trajectory_generator.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
