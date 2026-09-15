# 45. 같은 목표에도 관절이 다르게 움직이는 이유

## 이번에 배우는 것

**1 kg 슬라이더의 위치·속도 응답을 기록하고, stiffness와 damping이 목표 도달 과정에 미치는 영향을 비교합니다.**

관절에 목표 위치 0.5 m를 준다고 즉시 그 위치에 놓이는 것은 아닙니다. Drive가 힘을 만들고 물리 계산이 진행되면서 실제 위치가 바뀝니다. 이번에는 다른 접촉의 영향을 줄인 한 축 시험 장치로 그 과정을 관찰합니다.

| 시험 조건 | 기본값 | 의미 |
|---|---:|---|
| Slider 질량 | 1 kg | 움직일 물체의 질량 |
| 관절 | X축 Prismatic, 0~1 m | 직선 자유도 하나 |
| 위치 목표 | 0.5 m | 도달할 관절 변위 |
| Stiffness | 100 N/m | 위치 오차에 대한 힘의 크기 |
| Damping | 20 N·s/m | 속도 오차에 대한 힘의 크기 |
| Max Force | 200 N | drive 힘의 상한 |

이 코드는 실제 PhysX articulation을 진행한 뒤 값을 읽습니다. CSV는 이론식으로 만든 응답 곡선이 아닙니다.

## 1. 기본 응답을 3초 동안 기록하기

Isaac Sim 5.1.0과 지원 GPU, 설치에 포함된 `usd.schema.isaac`가 필요합니다. 외부 로봇 에셋은 사용하지 않습니다. GUI에서 gain을 조절할 때는 Gain Tuner 확장도 사용합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/45_robot_setup_joint_tuning/run.py \
  --headless --output src/45_robot_setup_joint_tuning/output/baseline
```

Headless 기본값은 720단계입니다. 렌더링 없이 `world.step()`으로 물리를 한 단계씩 진행하므로 물리 간격 **1/240초**에서 시뮬레이션 시간은 `720 / 240 = 3초`입니다. **정량적인 응답 비교에는 이 headless 명령을 사용하세요.**

화면으로도 보고 싶다면 `--headless`를 빼고 `--steps 720`을 넣을 수 있습니다. 다만 GUI는 렌더 간격 1/60초의 앱 업데이트를 통해 물리를 진행하며 한 번의 갱신에 여러 물리 단계가 들어갈 수 있습니다. 이 경우 720은 측정 반복의 한도이고 3초짜리 기록이라고 단정할 수 없습니다. GUI에서 단계 수를 생략하거나 0으로 지정하면 창을 닫을 때까지 실행합니다.

### 코드에서 볼 부분

장치는 world에 고정한 base와 X축으로 움직이는 slider로 구성됩니다.

```text
world ─ Fixed Joint ─ base ─ slider_joint(X) ─ slider
```

강체의 시각용 큐브에는 Collider를 추가하지 않습니다. 바닥과 부딪히는 효과 대신 관절 drive의 응답을 분리해서 보기 위해서입니다. `/GainRig/base`와 `/GainRig/slider`의 큐브를 환경 접촉 시험용 물체로 해석하지 마세요.

Drive에는 다음 값을 넣습니다.

```python
drive.CreateStiffnessAttr(args.stiffness)
drive.CreateDampingAttr(args.damping)
drive.CreateMaxForceAttr(200.0)
drive.CreateTargetPositionAttr(args.target)
drive.CreateTargetVelocityAttr(args.velocity)
```

`world.reset()` 후 위치와 속도 목표를 articulation action으로 적용합니다. 반복문에서는 **`world.step()` 다음에** 실제 관절 위치와 속도를 읽습니다.

### 실행 결과 확인하기

출력 폴더에는 `gain_rig.usda`, `response.csv`, `metrics.json`이 생깁니다. 기존 폴더는 덮어쓰지 않습니다.

| CSV 열 | 의미 |
|---|---|
| `time_s` | `(표본 번호 + 1) / 240`으로 계산한 시간; 위 headless 실행에서 물리 경과 시간과 대응 |
| `position_m` | 실제 관절 변위 |
| `velocity_m_s` | 실제 관절 속도 |
| `target_position_m` | 최초 CLI 위치 목표 |
| `target_velocity_m_s` | 최초 CLI 속도 목표 |

위 headless 실행의 첫 시간은 0이 아니라 **1/240초**이고, 720단계를 마치면 마지막 시간은 3초입니다. 이 열은 시뮬레이터 clock을 읽은 값이 아니므로 GUI나 물리 간격을 바꾼 실험의 실제 경과 시간을 증명하지 않습니다. 스프레드시트에서 `time_s`를 가로축, `position_m`를 세로축으로 그려 0.5 m 목표선과 비교하세요.

`metrics.json`의 `final_position_error_m`는 `목표 - 마지막 위치`이므로 부호가 있습니다. `overshoot_m`는 전체 기록의 최대 위치가 목표를 넘은 거리이며, 넘지 않았다면 0입니다. 마지막 오차가 작아도 중간에 크게 넘었다 돌아왔을 수 있습니다.

## 2. 위치 제어와 속도 제어 비교하기

### 코드에서 볼 부분

선형 drive의 힘을 이해하는 출발점은 다음 관계입니다.

```text
힘 ≈ stiffness × (목표 위치 - 실제 위치)
   + damping   × (목표 속도 - 실제 속도)
```

실제 힘에는 Max Force 제한과 물리 solver의 처리가 더해집니다. 위치 목표가 멀면 첫 항이 당기고, 속도 목표가 0이면 두 번째 항이 운동을 줄이는 방향으로 작용합니다.

속도만 추종하려면 위치 오차의 영향을 없애도록 stiffness를 0으로 둡니다.

```bash
~/isaacsim/python.sh src/45_robot_setup_joint_tuning/run.py \
  --headless --stiffness 0 --damping 20 --target 0 --velocity 0.2 --steps 480 \
  --output src/45_robot_setup_joint_tuning/output/velocity
```

이 실행은 2초 동안 0.2 m/s 속도 목표를 줍니다. 위치가 0에 머물지 않고 증가하는 것이 자연스럽습니다. 목표 위치 0은 stiffness가 0인 동안 위치 복원력을 만들지 않습니다. 움직임이 1 m 관절 한도에 닿으면 속도 응답도 달라질 수 있으므로 위치와 속도를 함께 보세요.

### 설정에서 볼 부분: Gain Tuner

GUI에서 응답을 비교하려면 새 출력 폴더로 실행합니다.

```bash
~/isaacsim/python.sh src/45_robot_setup_joint_tuning/run.py \
  --output src/45_robot_setup_joint_tuning/output/gui
```

1. **Tools > Robotics > Asset Editors > Gain Tuner**를 엽니다.
2. Robot=`GainRig`, Joint=`slider_joint`를 선택합니다.
3. Tune Gains에서 한 관절의 stiffness와 damping을 확인합니다.
4. Test Gains Settings에서 제한된 시험 범위를 지정하고 실행합니다.
5. 테스트가 끝난 뒤 command와 measured 곡선을 비교합니다.

코드의 RobotAPI, LinkAPI, JointAPI와 관계 정보는 도구가 이 장치를 로봇으로 찾도록 합니다. 실제 물리 연결을 만드는 `UsdPhysics.PrismaticJoint`와 관절을 로봇 목록에 표시하는 Robot Schema의 Joint API는 역할이 다릅니다.

### 실행 결과 확인하기

Headless CLI 고정 실험은 `response.csv`로 비교하고, GUI 시험은 Gain Tuner의 실제 command/measured 곡선을 사용하세요. GUI의 `time_s`는 앱 갱신과 물리 단계의 차이를 반영하지 않으므로 headless CSV와 같은 시간축으로 겹쳐 비교하지 않습니다. CSV의 target 열은 **GUI 변경을 추적하지 않고 최초 CLI 값을 유지**합니다. 따라서 GUI 시험의 실제 목표가 달라졌다면 그 열로 오차를 계산하면 안 됩니다.

`gain_rig.usda`도 실행 초기에 Export한 장면입니다. GUI에서 바꾼 gain을 보존하려면 자신의 로컬 파일로 Save As하세요. 실행 종료 시 저장하는 metrics와 USD 저장 시점은 다릅니다.

## 3. 응답 곡선으로 gain 읽기 정리

이상적인 질량–스프링–댐퍼의 임계 감쇠 기준은 다음과 같습니다.

```text
c = 2√(km)
k=100 N/m, m=1 kg → c=20 N·s/m
```

기본 damping 20은 이 값을 비교의 출발점으로 삼습니다. 실제 PhysX의 제한과 시간 간격 때문에 이론 곡선과 정확히 같다고 가정하지는 않습니다.

관절 응답에서는 목표에 얼마나 가까워졌는지와 **그곳에 도달하는 동안 어떻게 움직였는지**가 모두 중요합니다. 위치 곡선의 목표 초과량, 진동, 속도가 줄어드는 과정을 함께 살펴보세요.

## 4. 간단한 확인 실험

질량·목표·stiffness·단계 수를 유지하고 **damping만 20에서 5로** 바꿉니다.

```bash
~/isaacsim/python.sh src/45_robot_setup_joint_tuning/run.py \
  --headless --damping 5 \
  --output src/45_robot_setup_joint_tuning/output/low_damping
```

두 CSV를 같은 시간축에 놓고 비교해 보세요. 감쇠가 작아지면 운동을 줄이는 힘이 약해져 목표를 넘거나 진동할 가능성이 커집니다. 실제 `overshoot_m`와 곡선으로 확인하고, 마지막 위치만 보고 둘을 같다고 판단하지 마세요.

## 실행할 때 막히면

- **Gain Tuner에 장치가 없습니다**: `isaacsim.robot_setup.gain_tuner` 활성화와 `/GainRig`의 로봇 schema·link/joint 관계를 확인하세요.
- **속도 모드에서 위치 오차가 계속 커집니다**: stiffness=0인 속도 제어에서는 위치 목표가 성공 기준이 아닙니다. `velocity_m_s`를 비교하세요.
- **GUI를 Pause한 뒤 자동 종료하지 않습니다**: 코드는 재생 중 기록한 측정 반복만 셉니다. Play를 재개하거나 창을 닫으세요.
- **결과 폴더가 이미 있습니다**: 새 `--output` 경로로 실행하세요. Mass는 양수, gain은 음수가 아니어야 하며 위치 목표는 0~1 범위입니다.
- **응답이 발산하거나 큰 진동을 보입니다**: gain과 질량, 200 N 제한을 먼저 확인하고 기본값으로 돌아가 한 변수씩 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 11: Tuning Joint Drive Gains](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)의 원리를 로컬 1자유도 시험 장치에 적용합니다. GUI에서 장치를 찾는 구조는 [Robot Schema](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html)를 참고하세요.

`tutorial.json`은 `not_run`입니다. 응답 곡선과 Gain Tuner 화면은 실제 실행에서 확인할 항목이며, 이 문서의 이론적 비교를 측정 완료 결과로 사용하지 않습니다.
