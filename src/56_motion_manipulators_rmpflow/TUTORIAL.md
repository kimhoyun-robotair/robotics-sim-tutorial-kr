# 56. 움직이는 목표를 따라가며 장애물에 반응하기

## 이번에 배우는 것

**목표로 접근하는 반응과 장애물을 피하는 반응을 RMPflow로 연결하고, 정책의 계산과 실제 로봇 움직임을 비교합니다.**

미리 만든 궤적을 재생하는 동안 목표가 옮겨지면 어떻게 해야 할까요? 이번 실습은 현재 목표와 장애물 위치를 읽어 매 단계 새 관절 목표를 만듭니다. RMPflow는 이런 반응을 조합하는 모션 정책입니다.

| 장면 요소 | 경로·기본 설정 | 역할 |
|---|---|---|
| Franka | `/World/panda` | 정책 명령을 실제 물리로 실행 |
| 빨간 목표 | `/World/target`, `(0.5, 0, 0.7)` m | 말단이 접근할 위치 표시 |
| 파란 박스 | `/World/obstacle`, `(0.4, 0.15, 0.4)` m | 정책에 등록한 장애물이자 물리 충돌체 |
| 충돌 구 | `--debug-spheres` | 정책이 보는 로봇 근사 형상 |
| 추종 기록 | `tracking.json` | 실제 관절 상태로 계산한 말단 위치와 오차 |

빨간 목표는 잡을 물체가 아닙니다. 이번 코드는 위치만 지정하므로 손의 방향이나 그리퍼 개폐는 별도 목표가 없습니다.

## 1. 먼저 정지한 목표에 접근하기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. RMPflow 설정은 설치된 motion generation 확장의 Franka 구성을 사용합니다.

아래 명령은 **저장소 루트** 기준입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/56_motion_manipulators_rmpflow/run.py \
  --debug-spheres --steps 180
```

180단계, 물리 시간 3초 동안 실행한 뒤 종료합니다. 로봇을 둘러싼 구와 빨간 목표, 파란 박스를 함께 살펴보세요. 창 없이 기록만 만들려면 `--headless`를 추가합니다. 결과는 이 폴더의 새 `output/run_*/tracking.json`입니다.

### 코드에서 볼 부분

```python
config = interface_config_loader.load_supported_motion_policy_config('Franka', 'RMPflow')
policy = RmpFlow(**config)
policy.add_obstacle(obstacle)
```

설정에는 로봇의 운동학 URDF, 제어 관절과 충돌 구를 담은 description, 반응의 강도 등을 담은 RMPflow YAML이 연결됩니다. 보이는 박스를 만드는 코드와 `add_obstacle()` 호출은 역할이 다릅니다. **장면에 물체를 추가하는 것만으로 정책이 그 물체를 아는 것은 아닙니다.**

```python
policy.set_robot_base_pose(*robot.get_world_pose())
policy.set_end_effector_target(position)
policy.update_world()
robot.apply_action(motion.get_next_articulation_action())
world.step(render=not args.headless)
```

base pose와 목표를 월드 좌표로 맞추고, 등록된 장애물의 최신 위치를 읽은 뒤 다음 action을 만듭니다. `ArticulationMotionPolicy`가 정책의 결과를 로봇 관절 순서에 맞는 action으로 바꿉니다. 바깥 물리 간격은 1/60초이며, 정책 내부 계산의 작은 적분 간격과는 구분합니다.

### 실행 결과 확인하기

`tracking.json`은 배열이며 각 행에 다음 값이 들어 있습니다.

| 항목 | 의미 |
|---|---|
| `step` | 반복문 인덱스, 0부터 30단계 간격 |
| `target_m` | 그때 읽은 목표의 월드 위치 |
| `end_effector_m` | 실제 관절값으로 계산한 `right_gripper` 위치 |
| `position_error_m` | 목표와 실제 말단의 거리(m) |

정지한 도달 가능 목표에서 오차가 전반적으로 줄어드는지 확인하세요. 각 표본은 물리 계산 뒤 기록되므로 `step=0`도 첫 단계 이후 상태입니다. 180단계 실행의 마지막 기록은 `step=150`이며 종료 직전 측정값은 아닙니다.

작은 위치 오차는 목표 추종의 근거입니다. 이 JSON에는 접촉 수나 최소 충돌 거리가 없으므로 충돌 회피 성공까지 숫자 하나로 판단할 수는 없습니다. 구와 링크가 파란 박스 주변에서 어떻게 지나가는지도 관찰하세요.

## 2. 목표를 옮기고 정책의 내부 상태 보기

이번에는 종료 한도를 생략해 창을 유지합니다.

```bash
~/isaacsim/python.sh src/56_motion_manipulators_rmpflow/run.py --debug-spheres
```

1. Stage에서 `/World/target`을 선택하고 Move 도구로 도달 가능한 범위 안에서 조금씩 옮기세요.
2. 로봇이 새 위치를 향해 방향을 바꾸는지 봅니다. 목표가 바뀌는 순간 거리 오차가 다시 커지는 것은 자연스럽습니다.
3. `/World/obstacle`을 조금 옮겨 접근 경로가 어떻게 달라지는지 살펴보세요. 코드가 매 단계 `update_world()`를 호출해 등록된 장애물 위치를 반영합니다.
4. 창을 닫고 저장된 `target_m`의 변화를 확인하세요. 목표가 계속 움직인 실행과 정지 목표 실행을 같은 수렴 조건으로 비교하지 않습니다.

### 코드에서 볼 부분

정책의 이상적인 움직임과 실제 로봇을 비교하는 옵션도 있습니다.

```bash
~/isaacsim/python.sh src/56_motion_manipulators_rmpflow/run.py \
  --debug-spheres --ignore-state
```

`policy.set_ignore_state_updates(True)`를 사용하면 실제 관절 상태를 계속 반영하는 대신 내부에서 자신의 상태를 진행합니다. 이를 **내부 rollout**이라고 합니다. 계획한 대로 움직였다고 가정하며 다음 상태를 계산해 보는 것입니다.

### 실행 결과 확인하기

충돌 구 시각화가 실제 링크보다 앞서거나 다른 위치에 나타나는지 보세요. 내부 계산은 잘 진행되는데 실제 팔이 늦게 따라온다면 관절 drive와 물리 접촉을 살펴볼 단서가 됩니다. 기본 제어에서는 `--ignore-state`를 끕니다.

이 옵션을 켜도 `tracking.json`의 말단 위치는 실제 articulation의 FK에서 읽습니다. 화면의 정책 구가 목표에 도착했다는 사실과 실제 로봇이 도착했다는 사실을 나누어 보세요. 이 디버깅 방식은 [공식 Lula RMPflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_rmpflow.html)에서도 다룹니다.

## 3. 정책, 장애물 모델, 물리 추종 정리

```text
목표로 끌어당기는 반응 + 등록한 장애물을 피하는 반응
    → RMPflow 관절 목표 → 물리 drive → 실제 로봇
          ↑                                  │
          └──────── 실제 관절 상태 ──────────┘
```

기본 실행은 이 되먹임을 사용합니다. RMPflow는 현재 주변 조건에 반응하므로 매번 전체 우회 경로를 검색하는 계획기와 성격이 다릅니다. 좁거나 막힌 배치에서는 서로 다른 반응이 균형을 이뤄 멈출 수 있습니다.

또한 코드가 정책에 등록한 외부 장애물은 파란 박스입니다. 바닥 등 다른 장면 물체가 모두 자동 등록되지는 않습니다. 정책의 충돌 구와 PhysX collider도 서로 다른 형상이므로 로봇을 변경했다면 두 모델의 위치와 크기를 함께 맞춰야 합니다.

## 4. 간단한 확인 실험

1절의 명령에 **`--obstacle-y -0.15`**를 추가하세요. 목표와 실행 길이는 그대로 두고 박스의 y만 +0.15에서 −0.15 m로 옮깁니다.

두 실행에서 말단의 접근 경로와 `end_effector_m` 표본을 비교하세요. 박스가 반대편으로 옮겨졌다고 관절 경로가 완벽히 좌우 대칭이 될 필요는 없습니다. 초기 자세와 로봇 형상도 반응에 영향을 줍니다. 마지막 오차뿐 아니라 장애물 근처에서 접근이 느려지는 구간을 찾아보세요.

## 실행할 때 막히면

- **RMPflow 설정을 찾지 못함**: Isaac Sim 5.1의 motion generation 확장이 설치되어 있고 지원 Franka 설정을 읽는지 확인하세요.
- **목표에 가까이 가다 멈춤**: 목표가 도달 가능하며 장애물 근처에 놓이지 않았는지 확인하세요. 다른 배치에서 움직인다면 반응 간 경쟁을 살펴봅니다.
- **구는 움직이는데 실제 팔은 뒤처짐**: `--ignore-state` 여부를 확인하고 실제 drive gain, 접촉, 시간 간격을 살펴보세요.
- **새 물체를 추가했는데 피하지 않음**: USD 추가와 정책의 `add_obstacle()` 등록은 별개입니다. 등록과 `update_world()` 경로를 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Lula RMPflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_rmpflow.html)에 대응합니다. 위치 추종, 장애물 갱신, 충돌 구와 내부 상태 비교를 독립 실행으로 구성했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 기본 목표를 headless 180단계 실행했을 때 마지막 저장 위치 오차가 약 **0.00224 m**였던 관찰이 있습니다. 과거 기본 추종의 기록이며 현재 코드 재실행, 충돌 거리, GUI 이동·ignore-state 모드의 결과는 아닙니다. 작은 목표 오차와 장애물 주변의 실제 통과 상태를 함께 확인하세요.
