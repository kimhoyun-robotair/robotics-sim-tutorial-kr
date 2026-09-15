# 22. 팔의 움직임을 관절 기록과 화면 그래프로 읽기

## 이번에 배우는 것

**한 관절 팔의 각도·속도를 기록하고, Simulation Data Visualizer의 강체 상태와 단위를 비교합니다.**

움직임이 자연스러워 보여도 실제 각도나 속도를 알아야 제어 응답을 설명할 수 있습니다. 이번에는 월드에 고정된 Base와 길이 1.5 m의 Link를 사용합니다. 관절 drive는 0°를 목표로 하고 중력은 Link를 아래로 당깁니다. 이 둘이 만드는 초기 변화와 이후 상태를 관찰합니다.

| 관찰 대상 | 어디서 읽는지 | 이번 실습의 단위 |
|---|---|---|
| 관절 각도·속도 | `joint_motion.json` | rad, rad/s |
| Link 위치·회전 | Simulation Data Visualizer | m, degree |
| Link 선속도·각속도 | Simulation Data Visualizer | m/s, degree/s |
| 물리 제약의 residual | Physics Scene의 Visualizer 표시 | 해당 residual의 표시 단위 |

관절 각도는 두 몸체 사이의 상대 회전이고, Link의 위치는 월드에서 본 몸체 중심입니다. 화면에 숫자가 나온다는 이유로 같은 물리량처럼 직접 비교하지 않습니다.

## 1. 먼저 관절 상태 기록하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/22_sensors_inspect_physics/run.py
```

처음 240단계의 관절 상태를 기록한 뒤에도 창을 닫을 때까지 물리를 계속 진행합니다. 물리 간격은 1/60초이므로 최초 기록 구간은 약 4초입니다. GUI에서 나중에 관찰한 움직임은 기존 JSON에 추가되지 않습니다.

이 팔은 Link Scale X=`1.5`인데 관절 localPos1 X를 `-0.75`로 작성합니다. 시작 중심 X=`0.75`를 함께 적용하면 Link 쪽 연결점 X는 `-0.375`가 되어 Base 쪽 0과 일치하지 않습니다. 따라서 초기 응답에는 관절 조립 상태의 정렬 영향도 있을 수 있습니다. 이를 완벽히 정렬된 팔의 중력·drive 응답으로 단정하지 말고, 아래 상태와 residual을 함께 읽으세요. 코드가 이 불일치를 자동으로 고치는 것은 아닙니다.

파일 기록만 먼저 확인하려면 `--headless --steps 240`을 추가할 수 있습니다. `--steps N`을 지정한 실행은 N단계 후 저장하고 종료합니다. 기본 출력은 이 폴더의 `output/날짜_시간/`이며 `--output`은 새 폴더를 받아들입니다.

### 코드에서 볼 부분

팔을 구성한 뒤 residual 기록을 활성화하고 World를 초기화합니다.

```python
world.get_physics_context().enable_residual_reporting(True)
world.reset()
```

이어서 각 물리 단계가 끝난 뒤 상태를 읽습니다.

```python
world.step(render=True)
rows.append({
    'time_s': float(world.current_time),
    'joint_angle_rad': robot.get_joint_positions().tolist(),
    'joint_velocity_rad_s': robot.get_joint_velocities().tolist(),
})
```

설정한 목표각을 다시 쓰는 것이 아니라, 물리 계산 뒤 articulation에서 **실제 관절 상태**를 읽습니다. 이 팔의 자유도는 하나지만 API는 배열을 반환하므로 각도와 속도는 각각 원소 한 개의 목록으로 저장됩니다.

### 실행 결과 확인하기

`joint_motion.json`의 처음·중간·마지막 행을 비교합니다.

| 항목 | 읽을 내용 |
|---|---|
| `time_s` | 행마다 증가하는 물리 경과 시간 |
| `joint_angle_rad[0]` | 하나뿐인 회전 관절의 실제 각도 |
| `joint_velocity_rad_s[0]` | 같은 관절의 실제 회전 속도 |

초기에는 중력·drive와 조립 상태에 반응해 값이 변하고, 이후 속도가 줄거나 일정 상태에 가까워지는지 봅니다. 이 코드에는 주기적으로 목표를 바꾸는 명령이 없습니다. 일정 주기로 계속 왕복하거나, 정확히 0 rad에 정지하는 모습을 필수 결과로 삼지 마세요.

`arm.usda`도 함께 내보내지만, 시간에 따른 관절 측정값은 JSON에서 읽습니다. 기록 시작 직전 `world.reset()`이 있으며 첫 행은 첫 물리 단계 이후입니다.

## 2. 같은 팔을 Visualizer로 관찰하기

창이 열린 실행에서 다음을 진행합니다.

1. 뷰포트의 눈 아이콘에서 **Show By Type > Physics > Simulation Data Visualizer**를 켭니다.
2. Stage에서 `/World/Arm/Link`를 선택합니다.
3. 위치·회전·선속도·각속도, 질량·관성 표시를 살펴봅니다.
4. 부모 `/World/Arm`을 선택해 표시 가능한 항목이 어떻게 달라지는지 비교합니다.

### 설정에서 볼 부분

Link는 강체이므로 물리 속도를 읽을 수 있습니다. 부모 Arm은 묶음용 Xform이어서 같은 물리 항목을 모두 제공하지 않습니다. 먼저 선택한 Prim이 내가 관찰하려는 몸체인지 확인하세요.

Visualizer의 각도는 degree, Python의 관절 각도는 rad입니다. 같은 회전을 비교할 때는 다음처럼 환산합니다.

```text
각도(degree) = 각도(rad) × 180 / π
속도(degree/s) = 속도(rad/s) × 180 / π
예: 0.1 rad ≈ 5.73°
```

이 장면은 고정된 Base에 Y축 회전 관절 하나가 있으므로 Link의 Y 회전 변화와 관절 변화를 연결하기 쉽습니다. 그래도 각속도 벡터의 X·Y·Z 성분과 관절 스칼라 속도를 구분하고, 단위를 맞춘 뒤 비교하세요. 속도 그래프의 `M`은 벡터 크기이며 추가 관절을 뜻하지 않습니다.

### 실행 결과 확인하기

기록 구간을 놓쳤다면 JSON으로 최초 4초의 응답을 읽고, 현재 GUI는 그 이후 상태로 구분하세요. 이 두 시점의 숫자가 정확히 같아야 한다고 요구하지 않습니다. 초기 상태부터 비교하려면 같은 명령으로 프로그램을 다시 실행합니다.

다음으로 Stage의 Physics Scene을 선택합니다. Property에서 Residual Reporting과 Advanced의 **Enable Residual Reporting**이 켜졌는지 확인한 뒤 Visualizer의 RMS·Max를 살펴보세요. 코드는 이미 Physics Context를 통해 기록을 활성화합니다. 직접 변경했다면 재초기화 후 관찰해야 할 수 있습니다.

Residual은 물리 엔진이 관절·접촉 같은 제약을 얼마나 잘 만족했는지 살펴보는 지표입니다. RMS는 전체적인 크기를, Max는 큰 오차를 찾는 데 사용합니다. **작은 residual이 실제 로봇 모델이나 센서가 정확하다는 뜻은 아닙니다.** 또한 `joint_motion.json`에는 residual 열이 없으므로 이 값은 GUI에서 별도로 관찰합니다.

### 공식 Cortex 예제에서도 같은 표시 읽기

로컬 팔과 공식 예제를 비교하려면 `run.py`를 종료하고 `~/isaacsim/isaac-sim.sh`로 새 GUI를 시작합니다. **Window > Examples > Robotics Examples**에서 **Cortex > Franka Cortex Examples**를 열고 **Load Robot**을 누릅니다. 이 단계에는 NVIDIA Franka 에셋 접근이 필요합니다.

`/World/Franka/panda_hand`를 선택하고 **START**를 누른 뒤 Visualizer의 강체 상태를 읽어 보세요. residual은 Physics Scene에 **Add > Physics > Residual Reporting**을 적용하고 Advanced의 **Enable Residual Reporting**을 켠 뒤 예제의 **Reset → Start**로 확인합니다. 선택한 로봇은 달라져도 위치·각도·속도의 단위를 먼저 구분하는 방법은 같습니다. 이 예제의 움직임은 로컬 `joint_motion.json`에 기록되지 않습니다.

## 3. 목표·상태·오차 지표 정리

```text
drive 목표 0° + 중력
    → 물리 계산
    → 관절 각도·속도               → JSON
    → 선택한 Link의 위치·속도      → Visualizer
    → 제약 계산의 residual         → Scene의 표시
```

목표값은 코드가 원하는 상태이고, 측정값은 물리가 계산한 결과입니다. 중력에 맞서려면 drive가 힘을 내야 하므로 실제 자세가 목표에서 조금 벗어날 수 있습니다. 이때 목표 오차와 제약 residual은 다른 의미의 값입니다.

## 4. 간단한 확인 실험

Link의 질량만 1 kg에서 2 kg으로 바꾸어 같은 길이로 기록해 보세요.

```bash
~/isaacsim/python.sh src/22_sensors_inspect_physics/run.py --mass 1 --steps 240
~/isaacsim/python.sh src/22_sensors_inspect_physics/run.py --mass 2 --steps 240
```

막대 길이, 관절 한계 -80°~80°, drive의 stiffness 100과 damping 10은 그대로입니다. 질량을 늘리면 중력이 만드는 토크와 관성이 함께 달라집니다. 처음 흔들리는 속도, 각도 변화, 마지막 구간의 자세가 어떻게 달라지는지 `time_s`가 같은 행끼리 비교하세요.

“질량이 두 배니 각도도 정확히 두 배”라는 기준은 사용하지 않습니다. drive·중력·관절 한계가 함께 정하는 응답을 관찰하는 실험입니다.

## 실행할 때 막히면

- **물리 그래프가 비어 있음**: `/World/Arm/Link`를 선택했는지와 타임라인이 재생 중인지 확인하세요. 부모 Xform에는 같은 항목이 없습니다.
- **각도 값이 수십 배 차이 남**: JSON의 rad와 화면의 degree를 먼저 환산하세요.
- **Residual이 안 보임**: Physics Scene을 선택했는지, reporting과 enable 설정이 모두 있는지 확인하세요. JSON에는 저장하지 않는 값입니다.
- **Play가 이상하게 동작함**: 다른 실습에서 Physics Inspector를 열었다면 닫고 다시 실행하세요. 부분 초기화 상태가 일반 시뮬레이션에 영향을 줄 수 있습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Simulation Data Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/ext_isaacsim_inspect_physics.html)에 대응합니다. 공식 화면 경로·단위·residual 표시를 대조했습니다. 기본 실행은 로컬 한 관절 팔을 사용하며, 관절 JSON은 이 실습에 추가한 기록입니다. Cortex Franka는 별도 GUI 비교로 진행합니다.

현재 `tutorial.json`은 `not_run`입니다. 상태 읽기·단위·관절 좌표 파싱을 대조했으며 관절 운동·초기 정렬·GUI 그래프·residual은 실제 실행으로 검증하지 않았습니다. 위 비교는 실행 후 확인할 관찰 기준입니다.
