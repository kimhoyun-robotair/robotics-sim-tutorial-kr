# 48. 관절이 목표를 잘 따라가게 하려면?

## 이번에 배우는 것

**같은 관절에 위치 목표를 보내고, stiffness와 damping을 바꿨을 때 실제 움직임이 어떻게 달라지는지 읽습니다.**

로봇에 0.5 rad라는 목표를 보냈다고 관절이 즉시 그 각도에 도달하지는 않습니다. 관절 drive가 힘을 가하고, 링크의 질량과 관성에 따라 움직임이 달라집니다. 목표를 지나쳤다가 돌아올 수도 있고, 목표 근처에서 오래 흔들릴 수도 있습니다. 이번에는 작은 팔 하나로 이 차이를 관찰합니다.

| 실습 요소 | 이 폴더에서 사용하는 값과 역할 |
|---|---|
| `arm.urdf` | 고정 base와 길이 0.4 m인 팔을 연결한 로봇 |
| `shoulder` | Y축으로 회전하는 관절 하나, 범위 −1.2~1.2 rad |
| `--kp` | 위치 오차에 반응하는 stiffness, 기본 20 |
| `--kd` | 속도 오차에 반응하는 damping, 기본 1 |
| `response.csv` | 명령과 물리 계산으로 얻은 관절 상태를 나란히 기록 |
| `--interactive` | 같은 로봇을 Gain Tuner 창에서 직접 시험하는 방식 |

## 1. 먼저 계단 모양 목표를 보내기

Isaac Sim 5.1의 `python.sh`로 실행합니다. 아래 명령은 **저장소 루트** 기준이며, 설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 로봇은 로컬 URDF에서 가져오므로 외부 로봇 자산은 필요하지 않습니다.

```bash
~/isaacsim/python.sh src/48_importers_robot_setup_gain_tuner/run.py \
  --headless --kp 20 --kd 1 --wave step --steps 600 \
  --output src/48_importers_robot_setup_gain_tuner/output/kd1
```

위 명령은 창 없이 물리 계산을 600번 진행한 뒤 종료합니다. 물리 간격은 1/120초이므로 시뮬레이션에서는 5초입니다. 출력 경로는 매번 **아직 없는 폴더**를 사용하세요.

**CSV로 gain을 비교할 때는 두 실행 모두 `--headless`를 유지하세요.** 이 코드의 물리는 120 Hz, 렌더링은 60 Hz입니다. GUI의 `world.step(render=True)` 한 번은 앱 업데이트를 진행하므로 통상 물리 두 단계가 포함되지만, CSV 시각은 여전히 반복문 번호를 120으로 나눕니다. 따라서 GUI의 600회 반복을 물리 5초라고 읽거나 headless CSV와 같은 시간축으로 비교할 수 없습니다. 화면에서 자동 움직임만 보려면 `--headless`를 빼고, 직접 gain을 시험하려면 2절의 GUI 방식을 사용하세요.

### 코드에서 볼 부분

URDF를 가져오기 전에 `shoulder`의 drive에 두 값을 넣습니다.

```python
model.joints['shoulder'].drive.strength = args.kp
model.joints['shoulder'].drive.damping = args.kd
```

`world.reset()` 후에는 다음 순서로 목표와 상태를 비교합니다.

```text
명령 시각 t 계산 → 위치 목표 전달 → world.step()
    → 실제 각도와 속도 읽기 → 목표 − 실제 각도를 CSV에 기록
```

위 headless 실행의 step 입력은 처음 0.5초 동안 0 rad를 유지한 뒤 0.5 rad로 바뀝니다. 코드의 위치 목표와 속도 목표를 함께 보세요.

```python
robot.apply_action(ArticulationAction(
    joint_positions=np.array([target]),
    joint_velocities=np.array([0.0])))
```

목표 속도가 0이므로 움직이는 동안 damping은 속도를 줄이는 쪽으로 작용합니다. 목표 위치로 끌어당기는 반응과 움직임을 가라앉히는 반응의 균형을 보는 실험입니다.

### 실행 결과 확인하기

위 명령의 결과는 이 튜토리얼 폴더의 `output/kd1/response.csv`입니다.

| CSV 열 | 읽는 방법 |
|---|---|
| `time_s` | 코드가 `step / 120`으로 만든 명령 시각; 위 headless 조건에서 물리 시간과 대응 |
| `target_rad` | 0.5초부터 0.5 rad로 바뀌는 목표 |
| `actual_rad` | 그 목표를 적용하고 물리 한 단계를 진행한 뒤의 각도 |
| `velocity_rad_s` | 같은 단계 뒤의 실제 각속도 |
| `error_rad` | `target_rad - actual_rad` |

스프레드시트에서 `time_s`를 가로축으로 두고 목표와 실제 각도를 겹쳐 그려 보세요. 실제 각도가 목표를 넘는 부분이 **오버슈트**, 목표 부근에서 오르내리는 부분이 **진동**입니다. 각도 차이가 작아져도 속도가 크면 아직 멈춘 상태가 아닙니다.

첫 행의 시각은 0이고 마지막은 약 4.9917초입니다. `time_s`는 **명령 직전 시각**, 상태는 **물리 계산 직후 값**이기 때문입니다. 600단계를 진행했다는 사실과 마지막 행의 시각 표기가 어긋난 오류는 아닙니다.

## 2. 같은 관절을 Gain Tuner에서 시험하기

앞선 자동 측정이 끝나면 다음 명령으로 새 창을 여세요.

```bash
~/isaacsim/python.sh src/48_importers_robot_setup_gain_tuner/run.py \
  --interactive --output src/48_importers_robot_setup_gain_tuner/output/gui
```

1. **Tools > Robotics > Gain Tuner**를 열고 가져온 articulation을 선택하세요. 재생이 멈춰 있으면 Play하세요.
2. **Tuning Gains / Tuning Options**에서 Stiffness 방식을 선택하고 `shoulder`를 Position 모드, stiffness 20, damping 1로 두세요.
3. **Gains Test**에서 Step Function을 선택하세요. 해당 관절의 Test를 켜고 Step Minimum 0, Step Maximum 0.5, Period 2초, Phase 0으로 설정합니다.
4. 시험을 실행하고 **Test Results**의 command/actual position과 velocity를 비교하세요. 목표를 넘은 뒤 속도 부호가 바뀌는 지점을 찾아보세요.

### 설정에서 볼 부분

자동 코드는 한 번 목표를 바꾸지만 GUI의 Step Function은 주기에 따라 시험을 반복합니다. 두 결과를 비교할 때는 동일한 한 번의 상승 구간을 골라 읽으세요. Sinusoidal의 Amplitude와 Offset 입력은 관절 범위에 대한 **백분율**이므로 0.3을 곧바로 0.3 rad로 해석하지 않습니다. [Gain Tuner 시험 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html#gains-tests)에 각 입력의 의미가 나옵니다.

`--interactive` 분기는 `app.update()`로 앱을 갱신하며 스크립트의 위치 목표를 보내지 않습니다. 이 모드에서는 **`response.csv`도 생성하지 않습니다.** 관찰 결과는 Gain Tuner의 그래프에서 확인하세요. `--steps`를 넣으면 GUI 시험 시간과 관계없이 앱 업데이트 횟수로 종료되므로 수동 실습에서는 생략합니다.

### 고유진동수와 감쇠비로 같은 gain 읽기

**Tuning Options > Natural Frequency**로 전환하면 stiffness와 damping을 직접 넣는 대신 고유진동수와 감쇠비로 조정할 수 있습니다. 고유진동수는 응답이 얼마나 빠르게 변하는지, 감쇠비는 진동을 얼마나 억제하는지 표현하는 출발점입니다. 설치된 5.1 GUI의 Natural Frequency 값은 Hz이며 각주파수 rad/s와는 `ω = 2πf` 관계입니다.

같은 Step Function과 표시된 고유진동수는 유지하고 **Damping Ratio만 1.0, 0.5, 2.0**으로 바꾸어 각각 시험하세요. 매 시험의 command/actual 곡선과 변환된 damping을 함께 확인합니다. 이상적인 단일축에서는 1이 임계 감쇠, 1보다 작으면 진동이 남기 쉬운 조건, 1보다 크면 과감쇠입니다. 실제 로봇은 자세에 따라 등가 관성이 달라질 수 있으므로 이 분류만으로 응답을 보장하지 않습니다. 이때 Drive Type도 Force 또는 Acceleration 중 무엇인지 유지하세요. 후자는 질량으로 정규화한 방식이므로 같은 숫자를 곧바로 힘 기반 gain과 비교하지 않습니다.

## 3. 목표, gain, 실제 응답의 관계 정리

관절 drive를 이해하는 출발점은 다음 관계입니다.

```text
위치 오차에 대한 반응: Kp × (목표 각도 − 실제 각도)
속도 오차에 대한 반응: Kd × (목표 속도 − 실제 속도)
두 반응과 힘 제한, 질량·관성, 중력 → 실제 움직임
```

이는 반응 방향을 이해하기 위한 설명입니다. PhysX drive는 현재 시간 단계의 제약을 푸는 방식이며, 실제 응답을 단순한 수식 하나로 보장할 수는 없습니다. 특히 URDF에는 effort 20, 속도 제한 2 rad/s와 팔의 질량 0.3 kg이 들어 있습니다. 목표를 크게 바꾸면 gain 이외의 조건도 응답에 영향을 줍니다.

`--wave sine`는 진폭 0.3 rad, 주파수 0.5 Hz의 목표를 만듭니다. 이때도 목표 속도는 0입니다. 따라서 실제 각도가 목표보다 늦게 움직이는 정도와 진폭 차이를 살피되, 목표 속도까지 함께 보내는 궤적 제어와는 입력 조건이 다르다는 점을 기억하세요.

## 4. 간단한 확인 실험

첫 명령에서 **`--kd`만 1에서 2로** 바꿔 실행하세요. `--output` 경로 끝의 `kd1`은 `kd2`로 바꿔 결과를 따로 저장합니다. `--headless`, `kp`, 목표 파형, 600단계는 그대로 둡니다.

두 CSV에서 최대 각도, 목표 부근의 진동, 마지막 오차와 속도를 비교하세요. damping을 늘렸을 때 진동은 줄지만 접근이 느려지는지 확인해 보세요. 어느 값이 더 좋은지는 “얼마나 빨리, 얼마나 덜 흔들리며 도달해야 하는가”에 따라 판단합니다.

## 실행할 때 막히면

- **CSV에서 목표가 계속 0임**: 60단계 이하로 끝냈는지 확인하세요. 목표 변화는 `t=0.5`인 61번째 명령부터 나타납니다.
- **새 출력 폴더를 요구하는 오류**: 이전 `output/kd1`이 남아 있습니다. 기존 결과를 보관하고 다른 `--output`을 지정하세요.
- **interactive인데 CSV가 없음**: 이 모드는 GUI 시험용입니다. 파일 측정에는 `--interactive`를 빼세요.
- **GUI와 headless의 반응 시간이 다름**: 자동 GUI의 반복문 시각은 실제 물리 경과 시간을 기록하지 않습니다. CSV 시간 비교는 1절처럼 headless로 통일하고 GUI에서는 Gain Tuner 그래프를 사용하세요.
- **진동이 심하거나 목표에 못 도달함**: `arm.urdf`의 관절 범위와 질량을 먼저 확인하고 작은 step 입력으로 돌아가세요. 한 번에 두 gain을 바꾸면 원인을 분리하기 어렵습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Gain Tuner Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html)에 대응합니다. 로컬 1관절 URDF와 CSV 측정은 gain과 응답의 관계를 읽기 위한 구성입니다.

`tutorial.json`의 실행 검증 상태는 `not_run`입니다. 설명한 곡선 해석은 실행 후 확인할 기준이며, 이번 문서 개정에서 물리 응답이나 GUI 그래프를 새로 측정한 결과는 아닙니다.
