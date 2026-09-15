# 47. H1의 학습 설정을 USD 관절 값으로 옮기기

## 이번에 배우는 것

**H1의 19개 관절에 초기 자세와 drive 값을 적용하고, rad 기반 입력이 USD의 degree 기반 값과 같은 의미인지 확인합니다.**

학습된 보행 정책은 특정 초기 자세와 actuator 설정을 전제로 합니다. 로봇 외형이 같아도 관절 이름·초기 각도·gain이 다르면 정책이 예상한 시스템과 달라집니다. 이번에는 정책 실행 전에 필요한 설정 일치를 다룹니다.

| 파일 | 담는 정보 | 사용하는 단위 |
|---|---|---|
| `h1_policy.json` | 관절 이름 패턴, 초기 각도, actuator 값 | rad 기반 |
| `run.py`의 출력 USD | Joint State, Drive, 속도·effort 한도 | USD의 degree 기반 각도·gain |
| `joint_configuration.json` | 입력과 작성값의 비교 기록 | rad와 degree를 함께 표시 |
| `inspect_runtime.py` | 실제 articulation의 위치·속성 출력 | 런타임 API의 rad 기반 값 |

이번 프로그램은 정책을 추론하거나 학습하지 않습니다. 설정을 작성한 후 창을 유지하며, Play도 자동 시작하지 않습니다.

## 1. 기본 설정을 USD에 작성하기

Isaac Sim 5.1.0, RTX GPU와 `/Isaac/Robots/Unitree/H1/h1.usd`에 접근할 수 있는 assets root가 필요합니다. Isaac Lab 설치나 이전 튜토리얼 결과는 필요하지 않습니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/47_robot_setup_rig_legged_robot/run.py \
  --output src/47_robot_setup_rig_legged_robot/output/baseline
```

실행기는 원본 H1을 sublayer로 넣은 `h1_policy.usda`와 `joint_configuration.json`을 생성합니다. 출력은 새 폴더만 허용합니다. 창 없이 설정 파일만 만들려면 `--headless --steps 120`을 추가하세요. 여기서 120은 **앱 갱신 횟수**이며 보행의 물리 단계 수가 아닙니다. GUI는 단계 수를 생략하거나 0이면 직접 닫을 때까지 유지됩니다.

### 코드에서 볼 부분

입력에서는 좌우 관절에 같은 값을 적용하기 위해 이름 패턴을 사용합니다.

```json
".*_hip_pitch": -0.28,
".*_knee": 0.79,
".*_ankle": -0.52
```

`.*_knee`는 `left_knee`, `right_knee` 같은 이름에 대응합니다. `matching_value()`는 정규식 `fullmatch`로 관절 이름 전체를 검사하며, 일치하는 설정이 **정확히 하나**여야 값을 사용합니다. 누락이나 중복을 임의로 추측하지 않습니다.

팔의 shoulder_pitch는 0.28 rad, elbow는 0.52 rad이며 hip yaw/roll, torso, shoulder roll/yaw는 0입니다. Base 위치는 `(0, 0, 1.05)` m, orientation은 identity로 작성합니다.

### 실행 결과 확인하기

보고서는 실제 찾은 RevoluteJoint 19개에 대해 다음을 기록합니다.

| 항목 | 읽는 방법 |
|---|---|
| `joint` | 설정한 관절 이름 |
| `initial_position_rad`, `usd_position_deg` | 같은 초기 각도의 두 표현 |
| `stiffness_rad`, `usd_stiffness_per_deg` | 같은 힘 반응의 두 표현 |
| `damping_rad`, `usd_damping_per_deg` | 같은 감쇠 반응의 두 표현 |
| `max_effort_nm`, `max_velocity_rad_s` | 입력 effort·속도 한도 |

목록 길이가 19가 아니면 실행기가 오류를 냅니다. USD Property에서는 knee의 **Joint State Position과 Drive Target Position 모두 약 45.26°**인지 확인하세요. 초기 상태와 목표를 같은 값으로 작성하여 처음부터 서로 다른 자세를 요구하지 않도록 합니다.

## 2. 각도와 gain의 변환 방향 비교하기

### 코드에서 볼 부분

각도와 각속도는 rad에서 degree로 다음과 같이 옮깁니다.

```python
drive.CreateTargetPositionAttr(math.degrees(position))
state.CreatePositionAttr(math.degrees(position))
joint.CreateMaxJointVelocityAttr(math.degrees(group["velocity_limit"]))
```

반면 stiffness와 damping은 반대 배율입니다.

```python
drive.CreateStiffnessAttr(stiffness * math.pi / 180)
drive.CreateDampingAttr(damping * math.pi / 180)
```

왜 반대인지 작은 예로 생각해 보세요. 1 rad의 오차는 약 57.3°입니다. 같은 오차에서 같은 토크를 내려면 **1°당 gain은 1 rad당 gain보다 약 57.3배 작아야** 합니다. 각도 숫자가 커졌다고 gain까지 같은 비율로 키우면 훨씬 큰 토크를 요구하게 됩니다.

### 설정에서 볼 부분

`h1_policy.json`의 actuator 값은 다음과 같습니다.

| 관절 그룹 | Stiffness (N·m/rad) | Damping (N·m·s/rad) | Effort 한도 (N·m) | 속도 한도 (rad/s) |
|---|---:|---:|---:|---:|
| hip yaw/roll | 150 | 5 | 300 | 100 |
| hip pitch/knee/torso | 200 | 5 | 300 | 100 |
| ankle | 20 | 4 | 100 | 100 |
| shoulder/elbow | 40 | 10 | 300 | 100 |

예를 들어 left_hip_yaw의 USD 값은 stiffness 약 **2.61799**, damping 약 **0.0872665**, 최대 각속도 약 **5729.58 deg/s**입니다. Max Force는 300이며 각도 단위 변환 때문에 57.3배 바꾸지 않습니다. 코드는 force drive를 명시하고, 입력에 없는 armature·friction을 임의로 덮어쓰지 않습니다.

### 실행 결과 확인하기

작성된 Property를 확인했다면 직접 Play하고 **Window > Script Editor**에서 `inspect_runtime.py` 전체를 실행하세요.

```python
robot = SingleArticulation(prim_path="/h1", name="h1_policy_inspection")
robot.initialize()
print("DOF order:", robot.dof_names)
print("Runtime positions (rad):", robot.get_joint_positions())
print("Runtime properties (rad-based gains/velocities):", robot.dof_properties)
```

먼저 `DOF order`에서 이름을 찾고 그 인덱스의 속성을 읽습니다. `left_hip_yaw`의 런타임 stiffness≈150, damping≈5, maxVelocity≈100, maxEffort≈300을 USD 값과 대조하세요. 반환 순서가 JSON이나 원문 표의 순서와 같다고 가정하지 않습니다. 이 도구는 콘솔에 출력하며 파일을 자동 저장하지 않습니다.

Play 중 실제 관절 위치는 중력과 drive 때문에 초기값에서 달라질 수 있습니다. 또한 균형 정책이 없으므로 서 있기나 보행 안정성을 이번 설정 검사의 성공 기준으로 삼지 마세요. 초기 자세와 drive를 작성했다는 사실과 자유로운 로봇이 균형을 유지한다는 사실은 별개입니다.

### GUI에서 초기 자세를 저장하는 다른 방법

API로 Joint State를 직접 작성하는 방식과 원문의 GUI 방식을 비교하려면 별도 작업 사본에서 진행하세요.

1. 각 관절의 Drive Target Position을 원하는 degree 값으로 설정합니다.
2. `/h1/torso_link`를 선택하고 **Create > Physics > Joint > Fixed Joint**로 world와 임시 고정합니다. 균형 정책 없이 자세를 관찰하기 위한 지지대입니다.
3. **Edit > Preferences > Physics > Reset Simulation on Stop**을 잠시 끄고 Play하여 목표 자세에 접근시킨 뒤 Stop합니다. 정지 후 실제 관절 상태가 남는지 확인하세요.
4. 임시 Fixed Joint를 제거하고 로컬 사본을 저장한 뒤 **Reset Simulation on Stop을 다시 켭니다.**

이 경로는 물리를 거쳐 얻은 상태를 저장하므로 명령 목표와 정확히 같다고 가정하지 않습니다. 기본 `run.py`는 이 과정을 거치지 않고 입력 각도를 Joint State와 Drive Target에 각각 작성합니다.

## 3. 같은 물리 값을 다른 단위로 읽는 법 정리

```text
각도:       q_deg = q_rad × 180/π
각속도:     v_deg = v_rad × 180/π
stiffness:  k_deg = k_rad × π/180
damping:    d_deg = d_rad × π/180
```

예를 들어 hip yaw에 0.1 rad 오차가 있다고 가정하면 입력 gain 150은 15 N·m를 요구합니다. 같은 오차 약 5.73°에 USD gain 약 2.618을 곱해도 약 15 N·m입니다. 이렇게 **같은 물리 결과가 나오는지** 생각하면 변환 방향을 기억하기 쉽습니다. 실제 drive에서는 effort 한도 등 다른 조건도 적용됩니다.

## 4. 간단한 확인 실험

`h1_policy.json`을 같은 폴더의 `h1_policy_low_arm.json`으로 복사한 뒤, **arms 그룹의 stiffness 값들만 40에서 20으로** 바꿔보세요. Damping, 초기 자세, 다른 그룹은 그대로 둡니다.

```bash
~/isaacsim/python.sh src/47_robot_setup_rig_legged_robot/run.py \
  --config src/47_robot_setup_rig_legged_robot/h1_policy_low_arm.json \
  --output src/47_robot_setup_rig_legged_robot/output/low_arm
```

보고서에서 팔 관절의 `usd_stiffness_per_deg`가 약 0.69813에서 0.34907로 반감되고 다리 값은 유지되는지 확인하세요. 런타임에서는 해당 팔 관절 stiffness가 20으로 읽히는지 대조합니다. 이 실험은 설정 전달을 확인하며 학습 정책의 보행 성능을 시험하지 않습니다.

## 실행할 때 막히면

- **설정이 없거나 여러 개라는 오류가 납니다**: 관절 이름과 JSON 정규식의 전체 일치를 확인하세요. 넓은 패턴을 추가하면 기존 패턴과 겹칠 수 있습니다.
- **관절 수가 19가 아닙니다**: H1 에셋 버전과 RevoluteJoint 구조를 조사하세요. 다른 로봇의 설정을 자동으로 추측하는 실행기는 아닙니다.
- **초기 각도가 약 57배 다릅니다**: JSON 입력은 rad, USD Property는 degree인지 확인하세요. Gain은 반대 배율입니다.
- **런타임 핸들 또는 속성을 읽지 못합니다**: `/h1` 경로와 Play 상태를 확인한 뒤 검사 스크립트를 실행하세요.
- **H1이 넘어지거나 움직이지 않습니다**: 정책 추론은 포함하지 않습니다. 작성한 Property와 런타임 속성을 먼저 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 13: Rigging a Legged Robot for Locomotion Policy](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html)에 대응합니다. 입력 숫자는 공식 [5.1 H1 environment 설정](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Policies/H1_Policies/h1_env.yaml)의 초기 자세와 actuator 항목을 로컬 JSON에 옮긴 것입니다.

로컬 코드는 초기 Joint State를 직접 작성합니다. 원문의 GUI 재생·자세 저장 절차와 수행 방식이 다릅니다. `tutorial.json`의 상태는 `not_run`이며 실제 RTX 로드, 런타임 tensor 값, 정책 추론과 보행 안정성은 검증 완료 범위가 아닙니다.
