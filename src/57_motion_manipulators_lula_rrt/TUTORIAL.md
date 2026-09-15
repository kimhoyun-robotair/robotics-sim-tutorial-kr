# 57. 장애물 사이에서 갈 수 있는 경로 찾기

## 이번에 배우는 것

**Franka의 시작 관절 상태에서 목표까지 RRT 경로를 찾고, 계획 목록과 실제 재생을 구분해서 확인합니다.**

목표 쪽으로 조금씩 움직이는 것만으로는 장애물 뒤편까지 가기 어려울 수 있습니다. RRT는 여러 관절 자세를 후보로 살펴보며 시작점과 목표를 잇는 경로를 찾습니다. 이 예제에서는 찾은 경로를 촘촘한 관절 목표로 바꾸어 화면에서 재생합니다.

| 요소 | 이 실습에서의 역할 |
|---|---|
| `/World/panda` | 경로를 재생할 Franka |
| `/World/target` | 기본 `(0.45, 0.5, 0.7)` m의 목표 표시 |
| `/World/wall` | planner에 등록한 계획용 장애물 |
| `--max-iterations` | 한 번의 탐색에 허용하는 반복 수, 기본 5000 |
| `--max-cspace-dist` | 계획을 재생용 관절 목표로 보간하는 간격, 기본 0.01 |
| `plans.json` | 계획 성공 여부와 전체 관절 목표 목록 |

**wall은 `VisualCuboid`입니다.** 계획기에는 장애물로 등록하지만 PhysX 충돌체는 아니므로, 로봇이 벽에서 물리적으로 밀려나는 것을 회피 성공의 기준으로 삼지 않습니다.

## 1. 먼저 기본 목표로 경로 계획하기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. RRT는 설치된 motion generation 확장의 Franka URDF, robot description과 planner 설정을 읽습니다.

다음은 **저장소 루트**에서 실행하는 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/57_motion_manipulators_lula_rrt/run.py \
  --max-iterations 5000 --steps 600
```

시작 상태에서 경로를 계산한 뒤 한 물리 단계에 action 하나씩 적용합니다. 600단계 후 저장하고 종료하며, `--headless`를 추가하면 창 없이 실행할 수 있습니다. GUI에서 `--steps`를 생략하면 창을 닫을 때까지 재생과 목표 변경 확인을 계속합니다.

### 코드에서 볼 부분

```python
planner.set_max_iterations(args.max_iterations)
planner.add_obstacle(obstacle)
visualizer = PathPlannerVisualizer(robot, planner)
```

planner는 탐색을 수행하고, visualizer는 얻은 관절 경로를 실제 articulation에 보낼 action 목록으로 만듭니다. 벽의 크기는 `(0.1, 0.4, 0.4)` m, 중심은 `(0.3, 0.6, 0.6)` m이며 `add_obstacle()`로 계획 모델에 포함합니다.

계획할 때는 다음 순서를 사용합니다.

```python
planner.set_robot_base_pose(*robot.get_world_pose())
planner.set_end_effector_target(current)
planner.update_world()
actions = visualizer.compute_plan_as_articulation_actions(
    max_cspace_dist=args.max_cspace_dist)
```

현재 base와 목표를 같은 월드 좌표로 맞추고 장애물 위치를 갱신합니다. 계획의 시작 관절 상태는 연결된 articulation에서 가져옵니다. 설치된 Franka 로더 설정은 `right_gripper`를 말단 frame으로 넘깁니다. RRT 내부 YAML에 다른 `task_space_frame_name`이 적혀 있어도 생성자가 이 값으로 덮어쓰므로 로더가 넘기는 설정까지 확인해야 합니다. 다른 그리퍼를 조립했다면 그 제어 기준점도 함께 맞추세요.

### 실행 결과 확인하기

터미널의 `RRT plan: ... interpolated actions; success: ...`와 이 튜토리얼 폴더의 새 `output/run_*/plans.json`을 확인하세요.

| 각 계획의 항목 | 의미 |
|---|---|
| `step`, `target_m` | 언제 어떤 목표로 계획했는지 |
| `success` | action 목록이 비어 있지 않은지 |
| `joint_indices` | 각 관절값이 적용될 articulation 인덱스 |
| `joint_positions` | 보간된 전체 관절 목표 목록 |

`success=true`는 경로를 찾았다는 뜻입니다. 이 파일에는 실제 관절값, 말단 오차, 재생 완료 여부가 없습니다. 예를 들어 800개 action을 찾고 600단계 뒤 종료했다면 JSON에는 800개가 남아도 실제 적용은 앞부분에서 끝납니다. 계획 목록 길이와 실행 길이를 함께 확인하세요.

## 2. 목표를 옮겼을 때 다시 계획하는 조건 보기

아래 명령으로 창을 유지하세요.

```bash
~/isaacsim/python.sh src/57_motion_manipulators_lula_rrt/run.py
```

1. 첫 경로가 생성되면 로봇의 이동을 관찰하세요.
2. Stage에서 `/World/target`을 선택해 도달 가능한 곳으로 **1 cm보다 크게** 옮기세요.
3. 새 `RRT plan:` 출력이 나타나는지 확인하고, 창을 닫은 뒤 JSON에 새 계획이 추가됐는지 봅니다.

### 코드에서 볼 부분

```python
if step % 60 == 0 and (
    last_target is None or np.linalg.norm(current-last_target) > 0.01):
    planner.set_robot_base_pose(*robot.get_world_pose())
    planner.set_end_effector_target(current)
    planner.update_world()
    actions = visualizer.compute_plan_as_articulation_actions(
        max_cspace_dist=args.max_cspace_dist)
```

계획 조건을 물리 60단계마다 확인합니다. 물리 간격 1/60초이므로 시뮬레이션 시간으로 약 1초 간격입니다. 처음이거나 마지막으로 계획한 목표에서 1 cm 넘게 움직였을 때 새 탐색을 수행합니다. 렌더링과 탐색에 걸리는 실제 시계 시간은 이 간격보다 길 수 있습니다.

새 계획을 만들면 `action_index=0`부터 그 목록을 재생합니다. 실패했다면 빈 목록으로 바뀌고 해당 계획도 `success=false`로 기록합니다.

### 실행 결과 확인하기

target을 그대로 두고 wall만 옮기면 **재계획 조건이 충족되지 않습니다.** `update_world()`도 계획 분기 안에서 호출합니다. 따라서 이 코드를 움직이는 장애물을 항상 감시하는 시스템으로 이해하면 안 됩니다.

실패한 목표도 `last_target`에 기록되므로 목표가 그대로면 다음 주기에 무조건 재시도하지 않습니다. 다른 위치로 target을 옮기거나 새 실행으로 조건을 바꿔 시험하세요. 성공이 한 번도 없으면 실행을 끝낼 때 JSON을 저장한 뒤 오류로 종료합니다.

## 3. 계획 경로와 시간 궤적의 차이 정리

```text
RRT: 장애물 모델 안에서 관절 자세들을 연결
    → 보간: 인접 자세 사이에 관절 목표 추가
    → 재생: 매 물리 단계에 다음 목표 적용
    → 실제 추종: drive가 그 목표를 따라 움직임
```

RRT가 찾는 경로 자체는 각 점을 몇 초에 지나야 하는지 정한 궤적이 아닙니다. 이 visualizer는 보간된 점을 한 단계씩 재생하는 학습용 연결입니다. 간격을 줄이면 목표 수와 재생 시간도 늘 수 있습니다. 부드러운 속도·가속도 조건까지 필요하면 경로에 시간을 부여하는 과정이 추가로 필요합니다. [공식 Lula RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html)는 계획과 보간의 역할을 설명합니다.

충돌 판단도 planner에 등록한 장애물과 로봇 근사 형상을 기준으로 합니다. 계획 성공, 실제 목표 도착, 전체 경로의 물리 충돌 부재를 서로 다른 확인 항목으로 읽으세요.

## 4. 간단한 확인 실험

1절에서 **`--max-iterations`만 5000에서 100으로** 줄여 실행하세요. 목표, 장애물, 보간 간격, 실행 길이는 그대로 둡니다.

터미널과 JSON에서 성공 여부와 action 수를 비교하세요. 한도가 작아져도 쉬운 경로는 찾을 수 있고, 실패했다면 탐색 기회가 부족했을 수 있습니다. RRT는 샘플링 기반 알고리즘이지만 설치 설정에는 seed도 있으므로 같은 입력의 반복이 같은 결과를 낼 수 있습니다. 한 번의 실패를 경로가 존재하지 않는다는 증명으로 해석하지 않습니다.

## 실행할 때 막히면

- **`RRT가 경로를 찾지 못했습니다`**: 저장된 실패 기록을 읽고 목표 작업영역, 시작 자세와 장애물, 반복 한도를 확인하세요.
- **실패 후 계속 기다려도 새 계획이 없음**: 동일 목표는 자동 재시도하지 않습니다. 1 cm 넘게 옮긴 뒤 다음 확인 주기를 기다리세요.
- **성공인데 끝까지 이동하지 못함**: `joint_positions` 목록 길이와 `--steps`를 비교하세요. JSON은 실행하지 못한 뒤쪽 action도 보관합니다.
- **벽을 움직였는데 예전 경로를 따라감**: 이 코드의 재계획 조건은 목표 변화입니다. wall 이동만 감시하는 기능은 없습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Lula RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html)에 대응합니다. 로컬 실습은 경로 생성, 관절 공간 보간, 목표 변경에 따른 재계획과 계획 기록을 다룹니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 headless 60단계에서 **계획 기록 1개 생성과 계획 성공**을 확인한 과거 기록입니다. 현재 코드 재실행, 전체 재생, 실제 말단 도달·충돌 여유를 측정한 결과는 아닙니다. 계획 목록을 만들었다는 사실과 로봇이 그 경로를 끝까지 따라왔다는 사실을 나누어 확인하세요.
