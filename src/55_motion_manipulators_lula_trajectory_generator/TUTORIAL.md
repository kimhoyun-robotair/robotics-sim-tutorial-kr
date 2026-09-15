# 55. 지나갈 점에 시간을 붙여 궤적으로 만들기

## 이번에 배우는 것

**UR10의 관절 경유점과 말단 경로를 시간에 따른 목표열로 바꾸고, 실제 관절이 그 목표를 따라가는지 확인합니다.**

도착 자세 하나만 정하는 것과 여러 점을 순서대로 지나가는 것은 다른 문제입니다. 경유점을 어떤 선으로 연결할지, 각 구간을 얼마나 빨리 통과할지 정해야 합니다. Lula Trajectory Generator는 이 경로에 시간을 부여하고 로봇이 받을 관절 목표를 만듭니다.

| `--trajectory` | 입력 | 비교할 특징 |
|---|---|---|
| `cspace` | UR10 6축 관절값 네 점 | 관절 공간에서 연결, 시간이 계산됨 |
| `timestamped` | 같은 네 점과 `[0, 5, 10, 13]`초 | 지정한 시각에 맞춰 통과 |
| `taskspace` | 말단 위치 다섯 점과 방향 | `ee_link`의 직사각형 경로 |
| `composite` | 이동·회전·원호와 관절 경로 | 서로 다른 경로 표현을 연결 |

여기서 c-space는 **관절값을 좌표로 하는 공간**, task-space는 **말단의 위치와 방향을 표현하는 공간**입니다.

## 1. 먼저 관절 경유점 궤적 재생하기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/UniversalRobots/ur10/ur10.usd`가 필요합니다. 설정은 설치된 motion generation 확장의 `motion_policy_configs/universal_robots/ur10/`에서 읽습니다.

**저장소 루트**에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/55_motion_manipulators_lula_trajectory_generator/run.py \
  --trajectory cspace --steps 600
```

600번의 물리 계산, 즉 시뮬레이션 시간 10초가 지나면 결과를 저장하고 종료합니다. `--headless`를 추가하면 창 없이 실행합니다. GUI에서 `--steps`를 생략하면 경로를 재생한 뒤 **마지막 목표를 유지하면서** 창을 계속 열어 둡니다. 처음부터 반복 재생하는 코드는 아닙니다.

바닥이 로봇 원점보다 2 m 아래에 있습니다. 주어진 관절 경로가 원점 아래로도 내려가므로 작업 공간을 확보한 구성입니다. 이 실습에서 UR10은 고정 base를 사용하며 실제 설치대는 모델링하지 않습니다.

### 코드에서 볼 부분

`points`의 각 행은 여섯 관절 위치(rad)입니다. 기본 분기에서는 이 점들을 다음 호출로 연결합니다.

```python
trajectory = generator.compute_c_space_trajectory(points)
actions = ArticulationTrajectory(
    robot, trajectory, physics_dt=1./60.).get_action_sequence()
```

첫 줄은 연속적인 시간 궤적을 만들고, 두 번째 줄은 그 궤적을 **1/60초 간격의 ArticulationAction 목록**으로 바꿉니다. `World`의 물리 간격도 1/60초로 맞춥니다. 목록을 적용하는 간격과 생성할 때 가정한 간격이 같아야 의도한 속도로 재생됩니다.

시작 상태는 첫 action의 관절값으로 한 번 맞춥니다. 이후에는 다음처럼 물리 drive에 목표를 전달합니다.

```python
action = actions[min(step, len(actions)-1)]
robot.apply_action(action)
world.step(render=not args.headless)
```

`min(...)` 덕분에 마지막 점을 지난 뒤에도 마지막 action을 계속 사용합니다. 매번 실제 관절 상태를 강제로 바꾸는 것이 아니므로 측정값과 목표값을 비교할 수 있습니다.

### 실행 결과 확인하기

결과는 이 폴더의 새 `output/run_*/trajectory.json`입니다.

| 항목 | 의미 |
|---|---|
| `action_count` | 생성한 목표 표본 수 |
| `duration_s` | `(action_count - 1) / 60`으로 기록한 목표열의 시간 길이 |
| `completed_sequence` | 모든 action을 적용할 만큼 물리 단계를 진행했는지 |
| `ground_plane_z_m` | 이번 장면의 바닥 높이, −2 m |
| `trace` | 15단계마다 기록한 관절 목표와 실제 위치 |

`trace`의 `target_positions`와 `measured_positions`를 관절별로 빼 보세요. 두 배열의 차이가 추종 오차입니다. `completed_sequence=true`는 목표열을 끝까지 적용했다는 뜻이며, 실제 관절이 모두 정확히 도착했다는 판정은 아닙니다.

화면의 빨간 경유점은 관절 waypoint를 FK로 계산한 말단 위치입니다. 관절 공간에서 점들을 연결했으므로 **말단이 빨간 점 사이를 직선으로 움직일 필요는 없습니다.**

## 2. 같은 점에 통과 시각을 지정하기

이번에는 목표 자세는 그대로 두고 각 점을 지날 시각을 지정합니다.

```bash
~/isaacsim/python.sh src/55_motion_manipulators_lula_trajectory_generator/run.py \
  --trajectory timestamped --steps 900
```

### 코드에서 볼 부분

```python
trajectory = generator.compute_timestamped_c_space_trajectory(
    points, np.array([0., 5., 10., 13.]))
```

네 행의 관절 waypoint가 각각 0, 5, 10, 13초에 대응합니다. 처음과 마지막 관절 자세는 같으므로 한 바퀴의 자세 변화를 거쳐 처음 자세로 돌아옵니다. 13초를 재생하려면 60 Hz에서 약 780개의 시간 간격이 필요합니다. 첫 표본까지 포함한 실제 `action_count`를 기준으로 실행 길이를 확인하세요. 위 명령은 900단계로 여유를 둡니다.

### 실행 결과 확인하기

두 실행의 `mode`, `action_count`, `duration_s`, `completed_sequence`를 비교하세요. 같은 경유점을 쓰더라도 통과 시간 조건 때문에 목표열과 길이가 달라집니다. 특히 headless 기본값 600단계는 10초이므로 timestamped의 전체 13초 구간을 재생하기에 부족합니다.

말단 경로를 직접 지정하는 두 모드도 있습니다.

- **`taskspace`**: x=0.3 m 평면의 직사각형 다섯 점과 quaternion `[0, 1, 0, 0]`을 사용합니다. 위치와 방향을 지정한 `ee_link` 경로가 관절 목표로 변환됩니다.
- **`composite`**: 위로 이동, 회전, 세 점으로 정한 원호에 관절 경로를 이어 붙입니다. 코드의 `TransitionMode.FREE`는 연결 구간을 말단 직선으로 제한하지 않습니다.

이 두 모드는 위 명령의 `--trajectory` 값을 바꿔 실행할 수 있습니다. 생성 결과가 `None`이면 코드가 오류를 내며, 가능한 궤적을 만들지 못한 상태를 빈 재생으로 넘기지 않습니다. 경로 표현은 [공식 Lula Trajectory Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_trajectory_generator.html)에서 이어서 볼 수 있습니다.

## 3. 경로, 시간 궤적, 실제 추종 정리

```text
경유점: 어디를 지나갈까?
    → 경로: 점들을 어떻게 이을까?
    → 시간 궤적: 언제 어디에 있을까?
    → 60 Hz action: 이번 단계의 관절 목표는?
    → 물리 drive: 실제 관절이 얼마나 따라왔을까?
```

바닥을 낮춘 것도 이 구분과 연결됩니다. 궤적 생성에 성공해도 장면에 추가한 바닥이 경로를 막으면 실제 관절은 목표를 따라갈 수 없습니다. 이 프로그램의 generator는 외부 장애물의 충돌 없는 경로를 탐색하지 않습니다. 실제 작업대나 장애물을 추가할 때는 경로와 물리 접촉을 함께 확인해야 합니다.

## 4. 간단한 확인 실험

2절의 timestamped 실행에서 **`--steps`만 900에서 600으로** 줄이세요. 같은 궤적을 생성하지만 중간에 실행을 마칩니다.

`action_count`와 `duration_s`는 같은 설정의 궤적을 설명하고, `completed_sequence`는 `false`가 되어야 합니다. trace도 앞부분만 남습니다. **궤적을 만드는 데 성공한 것과 끝까지 재생한 것은 다른 결과**임을 확인해 보세요.

## 실행할 때 막히면

- **궤적을 만들지 못했다는 오류**: 바꾼 waypoint의 관절 한도, 말단 도달 가능성, 통과 시각을 확인하세요.
- **로봇이 바닥에 걸려 일부 관절이 멈춤**: 바닥을 z=0으로 바꾸지 않았는지 확인하세요. 제공 경로는 base 아래로 내려갑니다.
- **마지막 점까지 못 감**: `--steps`와 `action_count`를 비교하세요. GUI에서는 종료 한도를 생략하고 전체 재생을 관찰할 수 있습니다.
- **끝에서 멈춘 채 창이 계속 열려 있음**: 전체 재생 뒤 마지막 목표를 유지하는 정상 동작입니다. 창을 닫으면 JSON을 저장합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Lula Trajectory Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_trajectory_generator.html)에 대응합니다. 네 경로 모드를 명령행으로 선택하고 실제 관절 추종을 기록하도록 구성했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 기본 cspace를 headless 600단계 실행해 **349개 action을 전부 적용**하고 기록된 최대 관절 오차가 약 **7.25×10⁻⁶ rad**였다는 관찰이 있습니다. 과거 기본 모드의 기록이며 현재 코드 재실행이나 다른 세 모드·GUI 동작의 결과는 아닙니다. 각 실행의 목표열 길이, 재생 완료, 실제 추종 오차를 구분해 확인하세요.
