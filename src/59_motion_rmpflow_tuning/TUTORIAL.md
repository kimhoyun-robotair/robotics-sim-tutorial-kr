# 59. RMPflow의 반응을 하나씩 켜며 조정하기

## 이번에 배우는 것

**RMPflow의 기본 자세, 위치 추종, 회피, 방향, 제한, 감쇠를 단계적으로 복구하고 어떤 반응이 움직임을 바꾸는지 확인합니다.**

로봇이 목표 앞에서 느려졌을 때 위치로 끌어당기는 반응이 약한 것일 수도 있고, 장애물을 피하려는 반응과 경쟁하는 것일 수도 있습니다. 여러 값을 동시에 바꾸면 원인을 알기 어렵습니다. 이번에는 한 실행에 하나의 **phase**, 즉 활성화 단계만 선택해 결과를 비교합니다.

| 출력·설정 | 의미 |
|---|---|
| `--phase baseline` | 설치된 Franka 설정을 복사해 사용 |
| `--phase cspace`부터 `damping` | 반응을 끈 상태에서 정해진 순서로 복구 |
| `rmpflow.yaml` | 해당 실행이 실제로 사용한 정책 설정 |
| `tuning_trace.json` | 선택 phase와 실제 위치 오차·관절 속도 기록 |
| `--target-gain` | `target_rmp.accel_p_gain` 한 값만 덮어쓰기 |

이 실습에서 **metric은 반응 사이의 상대 영향**, **gain은 개별 반응의 세기나 감쇠**를 조정합니다. 물리 관절의 drive stiffness/damping과는 다른 계층의 값입니다.

## 1. 먼저 기준 설정과 기본 자세 반응 비교하기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. 설정은 설치된 motion generation 확장에서 읽고, 수정본은 결과 폴더에 저장합니다.

아래 두 명령을 **저장소 루트**에서 하나씩 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/59_motion_rmpflow_tuning/run.py \
  --phase baseline --steps 600 \
  --output src/59_motion_rmpflow_tuning/output/baseline

~/isaacsim/python.sh src/59_motion_rmpflow_tuning/run.py \
  --phase cspace --steps 600 \
  --output src/59_motion_rmpflow_tuning/output/cspace
```

각 실행은 물리 시간 10초 후 저장하고 종료합니다. `--headless`를 추가할 수 있으며, GUI에서 `--steps`를 생략하면 창을 닫을 때까지 같은 phase를 실행합니다. 출력 폴더는 새 경로여야 합니다. 한 실행 중 다음 phase로 자동 전환하지는 않습니다.

기본 목표는 `(0.5, 0, 0.7)` m입니다. 파란 고정 박스의 중심은 `(0.4, 0.15, 0.4)` m이고, 모든 phase에서 같은 물리 충돌체가 남아 있습니다.

### 코드에서 볼 부분

원본을 읽고 복사본의 `rmp_params`를 수정합니다. baseline 이외의 phase에서는 metric이나 inertia 등 선택한 가중치 키들을 먼저 0으로 만든 뒤 필요한 항목을 복구합니다.

```python
active = ['cspace_target_rmp']
if level >= 1:
    active.append('target_rmp')
if level >= 2:
    active.append('collision_rmp')
```

cspace 단계의 중심 반응은 description의 기본 관절 자세로 향하는 편향입니다. 빨간 target에 도착하지 않아도 이상하지 않습니다. 위치 목표에 반응하는 `target_rmp`가 아직 복구되지 않았기 때문입니다.

실제 사용하는 파일 경로도 복사본으로 바꿉니다.

```python
local_config = output / 'rmpflow.yaml'
local_config.write_text(yaml.safe_dump(tuning, sort_keys=False))
config['rmpflow_config_path'] = str(local_config)
policy = RmpFlow(**config)
```

따라서 설치 파일을 편집하지 않고 실행별 설정을 나란히 비교할 수 있습니다.

### 실행 결과 확인하기

두 결과 폴더의 YAML을 먼저 비교하고 JSON을 읽으세요.

| `tuning_trace.json` 항목 | 해석 |
|---|---|
| `phase` | 이 실행에 선택한 단계 |
| `trace[].step` | 0부터 15단계 간격의 표본 |
| `end_effector_m` | 실제 관절 상태로 계산한 `right_gripper` 위치 |
| `error_m` | 그때의 목표와 말단 사이 거리 |
| `joint_velocities_rad_s` | 실제 articulation 전체의 관절 속도 배열 |

속도 배열의 키 이름에는 `rad_s`가 있지만 코드는 관절을 걸러내지 않고 전부 읽습니다. **팔의 회전 관절은 rad/s, 손가락의 직선 관절은 m/s**로 해석해야 합니다. 배열에 관절 이름도 저장하지 않으므로 인덱스 대응을 확인한 뒤 비교하세요.

cspace 실행의 큰 `error_m`는 비활성화한 위치 반응의 결과일 수 있습니다. “오차가 작은 phase가 항상 더 좋은 설정”이라고 순위를 매기지 말고, 해당 단계에서 무엇을 켰는지 함께 읽습니다.

## 2. 나머지 반응을 단계적으로 복구하기

1절 명령의 `--phase`를 아래 순서로 바꾸어 별도 실행하세요. 목표·600단계·로봇 drive는 그대로 두고 출력 경로만 phase별 새 폴더로 지정합니다.

| phase | 앞 단계에서 추가되거나 달라지는 내용 | 관찰 지점 |
|---|---|---|
| `target` | 위치 추종 반응, 단순화한 metric | 말단이 빨간 목표에 접근하는지 |
| `collision` | 장애물 회피 반응 | 박스 근처에서 경로·접근 속도가 달라지는지 |
| `directional` | 목표 방향별 metric과 근접 boost 복구 | 먼 곳과 목표 근처의 반응 차이 |
| `orientation` | `axis_target_rmp` 복구 | 손의 방향까지 맞추려는 움직임 |
| `limits` | 관절 위치 한도·속도 cap 반응 | 큰 관절 움직임의 제한 방식 |
| `damping` | 전역 감쇠와 cspace inertia 복구 | 급격한 움직임과 잔류 진동 |

### 설정에서 볼 부분

target과 collision 단계에서는 위치 반응을 읽기 쉽게 세 값을 고정합니다.

```text
min_metric_alpha = 0
metric_alpha_length_scale = 100000
proximity_metric_boost_scalar = 1
```

방향에 따른 차이와 목표 근처 가중 증가를 줄인 상태에서 위치 접근부터 살펴보려는 설정입니다. directional에서는 이 값들을 원본으로 되돌립니다. 5.1 설치 YAML의 키는 `cspace_target_rmp`와 `proximity_metric_boost_scalar`입니다. 비슷한 이름의 새 키를 임의로 추가하지 마세요.

각 단계의 구성과 순서는 [공식 RMPflow Tuning Guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow_tuning_guide.html)의 점진적 활성화 절차를 로컬 실행에 옮긴 것입니다. 다만 코드가 처음 0으로 만든 보조 항목 중 다시 복구하지 않는 키도 있으므로 damping 파일이 baseline과 완전히 같다고 가정하지 말고 YAML을 직접 대조하세요.

### 실행 결과 확인하기

코드는 모든 단계에서 위치와 quaternion `[0, 0, 1, 0]`을 목표로 전달합니다. cspace~directional 단계에서는 방향 반응의 가중치가 꺼져 있으므로 목표를 전달했다는 사실만으로 방향을 따라가는 것은 아닙니다. baseline과 orientation 이후 단계에서는 방향 반응이 켜져 있습니다. JSON에는 회전 오차가 없으므로 실제 손의 방향도 화면에서 비교해야 합니다.

target 단계에서 회피 반응이 꺼져 있어도 파란 박스의 PhysX collision은 유지됩니다. 팔이 박스에 걸리는 현상을 단순히 target gain 부족으로 판단하지 마세요. collision phase에서 경로가 바뀌는지 비교하면 정책 반응과 물리 접촉을 구분하는 데 도움이 됩니다.

## 3. 가중치, 반응 gain, 물리 drive 정리

```text
metric: 여러 반응 중 무엇을 얼마나 반영할까?
gain: 각 반응이 얼마나 강하게 움직임을 요구할까?
    → RMPflow의 관절 목표
    → USD drive와 물리 계산
    → 실제 관절 속도와 말단 오차
```

목표 반응을 키우면 접근이 빨라질 수도 있지만 장애물 회피나 기본 자세 반응과의 균형도 달라집니다. 실제 drive가 목표를 따라가지 못하면 정책 gain만 조절해 해결되지 않을 수 있습니다.

trace는 15단계, 약 0.25초 간격입니다. 짧은 속도 급증은 표본 사이에서 빠질 수 있습니다. 또한 목표 위치 자체를 JSON에 저장하지 않으므로 비교 실험에서는 CLI 목표를 유지하고 GUI로 target을 움직이지 않는 편이 결과를 읽기 쉽습니다.

## 4. 간단한 확인 실험

아래처럼 **target phase에서 `--target-gain`만 20과 40으로** 비교하세요.

```bash
~/isaacsim/python.sh src/59_motion_rmpflow_tuning/run.py \
  --phase target --target-gain 20 --steps 600 \
  --output src/59_motion_rmpflow_tuning/output/target_gain20

~/isaacsim/python.sh src/59_motion_rmpflow_tuning/run.py \
  --phase target --target-gain 40 --steps 600 \
  --output src/59_motion_rmpflow_tuning/output/target_gain40
```

YAML에서 `target_rmp.accel_p_gain`만 달라지는지 확인하세요. 같은 step의 `error_m`와 팔 관절 속도를 비교해 접근 속도, 마지막 오차, 급격한 움직임을 함께 살펴봅니다. gain을 두 배로 했다고 오차가 절반이 되거나 항상 더 좋아지는 것은 아닙니다.

## 실행할 때 막히면

- **cspace에서 target을 무시함**: 위치 반응을 아직 켜지 않은 단계입니다. `rmpflow.yaml`의 활성 가중치를 확인하세요.
- **초기 phase에서 박스에 걸림**: 회피가 꺼져 있어도 실제 collider는 남습니다. target과 collision 결과를 비교하세요.
- **gain을 바꿔도 차이가 거의 없음**: target 반응이 켜진 phase인지 먼저 확인하세요. cspace에서는 위치 반응 gain을 바꿔도 기여가 꺼져 있습니다.
- **위치 오차는 작은데 손 방향이 다름**: JSON은 방향 오차를 기록하지 않습니다. orientation 활성 여부와 화면의 방향을 확인하세요.
- **설정이 발산하거나 지나치게 느림**: baseline으로 돌아가 같은 목표에서 비교하고 한 번에 한 값만 바꾸세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RMPflow Tuning Guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow_tuning_guide.html)에 대응합니다. 단계별 정책 복사본과 실제 FK 위치 오차를 함께 남기는 조정 실습입니다.

`tutorial.json`은 `not_run` 상태입니다. 이번 개정에서는 로컬 phase 분기와 설치 YAML을 대조했으며 각 단계의 실제 움직임, 충돌 회피, 방향 추종을 새로 실행해 검증하지 않았습니다.
