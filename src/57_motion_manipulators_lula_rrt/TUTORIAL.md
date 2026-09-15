# 57. Lula RRT: 충돌을 피하는 경로 계획

권장 학습 순서 **57** · 로봇 제어와 동작 계획 · 출처 ID `t137`

Franka 시작 관절 상태에서 task-space 목표까지 실제 Lula RRT를 호출합니다. 경로가 나오면 선형 보간된 ArticulationAction으로 시각화하고 계획 결과를 저장합니다. 경로 실패는 성공으로 표시하지 않습니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

Isaac Sim 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. `get_assets_root_path()`가 반환하는 asset 서버 또는 로컬 asset 팩에서 읽습니다. 첫 로딩에는 네트워크가 필요할 수 있습니다. 이 로봇 USD와 해당 재질/mesh 참조를 함께 사용할 수 있어야 합니다.

터미널에서 이 패키지 폴더(`57_motion_manipulators_lula_rrt`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --max-iterations 5000 --target 0.45 0.5 0.7
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. `/World/wall`과 target의 위치를 살펴봅니다. wall은 이 예제에서 Lula world에 등록된 `VisualCuboid`로, 계획용 장애물입니다. 실제 PhysX 충돌체를 대신한다고 해석하지 않습니다.
2. `load_supported_path_planner_config('Franka','RRT')`가 반환하는 robot description, URDF, RRT YAML, end-effector frame을 확인합니다. RRT 설정은 설치의 `path_planner_configs/franka/rrt/` 아래에 있습니다.
3. `set_max_iterations(5000)`은 탐색 비용을 제한합니다. `set_end_effector_target()`과 `update_world()` 뒤 `compute_plan_as_articulation_actions(max_cspace_dist=0.01)`을 호출합니다.
4. GUI에서 target을 이동합니다. 60 physics frame 간격으로 목표가 1 cm 넘게 바뀌었는지 확인하고 재계획합니다. 실패한 동일 목표를 매 프레임 무제한 재시도하지 않습니다.
5. `plans.json`에서 각 계획의 target, success, joint_indices, 모든 interpolated joint_positions를 확인합니다. success=false인 계획은 action 목록이 비어 있습니다. 한 번도 경로를 찾지 못하면 결과 파일을 남기고 프로그램이 오류로 종료됩니다.
6. 목표를 도달할 수 없는 먼 곳으로 옮기거나 반복 제한을 아주 작게 해서 실패 처리도 관찰합니다. 프로그램이 계속 돌아가는 것과 경로를 찾는 것은 서로 다른 결과입니다.

## API와 알고리즘

RRT는 configuration space에서 샘플을 확장하여 시작과 목표를 잇는 경로를 찾습니다. 이 경로는 sparse waypoint이며, 시간에 대한 속도/가속 계획이 아닙니다. `PathPlannerVisualizer`는 active/watched joint를 로봇의 순서와 맞추고 관절 공간 보간을 통해 action 목록을 만듭니다. 한 물리 스텝에 한 action을 적용하는 방식은 공식 시각화 목적을 따르며 최적 속도·부드러운 실제 제어기라고 주장하지 않습니다.

`max_cspace_dist`를 줄이면 경로 샘플이 늘어납니다. 관절 한 번 이동량과 최종 재생 시간이 함께 달라질 수 있으므로 physics dt와 혼동하지 않습니다. 실제 적용에는 RRT 경로를 trajectory generator로 시간 매개화하고 로봇 drive 추종과 환경 변경을 검증해야 합니다.

RRT의 robot geometry는 URDF의 mesh와 동일하지 않을 수 있으며 robot description의 collision sphere 모델을 사용합니다. `planner.add_obstacle()`로 등록한 물체만 planner가 아는 장애물이 됩니다. 로봇 base pose도 world 좌표계에 맞춰 갱신합니다. 움직이는 장애물에 대한 오래된 경로의 안전을 보장하는 예제가 아닙니다.

## 관찰 기준과 한 변수 실험

성공 계획이 하나 이상 있고 nonempty action 목록을 로봇이 순서대로 실행하는지 확인합니다. 경로가 모델의 wall을 돌아가는지 화면으로 살펴봅니다. `--max-iterations`만 5000에서 100으로 낮추어 성공 여부와 계산 지연을 비교합니다. RRT는 확률적 계획기라 한 번의 실패가 목표가 불가능함을 증명하지 않습니다.

## 문제 해결

계획 실패 때 target 작업영역, 시작 상태의 collision, sphere 모델, 반복 제한을 확인합니다. target을 조금 옮기면 다시 계획합니다. 로봇이 경로를 따라가지 못하면 계획 성공 여부와 PD 추종 오류를 따로 봅니다. 양수 `--steps`로 제한한 경우 모든 action 적용 전에 종료될 수 있으므로 긴 경로는 값을 늘리거나 GUI 실행에서 옵션을 생략합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Lula RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
