# 41. 관절 계산·모터 힘·손가락 마찰을 따로 조정하기

## 이번에 배우는 것

**조립된 UR10e와 Robotiq에 물리 설정을 적용하고, 저장한 값과 실제 목표 추종을 나누어 확인합니다.**

로봇이 물체를 잘 잡으려면 손가락이 목표대로 움직이고 접촉도 유지되어야 합니다. 이때 solver 반복 횟수, 모터 effort 한도, 마찰은 서로 다른 곳에 작용합니다. 하나의 숫자만 크게 만든다고 모든 문제가 해결되지는 않습니다.

| 조정 대상 | 기본값 | 영향을 주는 부분 |
|---|---|---|
| Solver Position/Velocity Iterations | 64 / 4 | 관절·접촉 제약을 푸는 반복 계산 |
| finger_joint Max Force | 200 | 회전 drive가 낼 수 있는 effort 한도 |
| 손가락 Static/Dynamic Friction | 1.0 / 1.0 | 접촉면의 미끄러짐 저항 |
| Sleep / Stabilization Threshold | 0.00005 / 0.00001 | 작은 운동을 다루는 물리 설정 |

`run.py`가 이 값을 로컬 USD에 작성합니다. 목표 추종 곡선은 별도로 Physics Inspector와 Gain Tuner에서 관찰합니다.

## 1. 설정한 USD와 보고서 만들기

Isaac Sim 5.1.0, 지원 GPU와 공식 UR10e+Robotiq 에셋 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/41_robot_setup_configure_manipulator/run.py \
  --output src/41_robot_setup_configure_manipulator/output/baseline
```

기본 입력은 `/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd`입니다. 이전 튜토리얼 결과 없이 실행할 수 있고, 자신의 조립 결과는 `--asset`으로 지정합니다.

창은 직접 닫을 때까지 유지됩니다. 스크립트는 자동 Play하지 않으며 `--steps`는 앱 갱신 횟수입니다. 설정 파일만 만들고 종료하려면 `--headless --steps 10`을 추가하세요. Headless에서 `--steps`를 생략하면 `--frames` 값인 기본 1200회가 적용됩니다.

### 코드에서 볼 부분

실행기는 articulation root를 찾아 정확히 하나인지 확인한 뒤 설정합니다.

```python
articulation.CreateSolverPositionIterationCountAttr(64)
articulation.CreateSolverVelocityIterationCountAttr(4)
articulation.CreateSleepThresholdAttr(0.00005)
articulation.CreateStabilizationThresholdAttr(0.00001)
```

반복 횟수는 관절이나 접촉 제약을 더 반복해서 풀도록 하는 값입니다. 모터가 따라갈 목표 위치나 stiffness를 대신하지는 않습니다. 이 예제는 원본 에셋을 직접 수정하지 않고 그 위에 현재 장면의 설정을 작성합니다.

### 실행 결과 확인하기

`output/baseline`에 `configured.usda`와 `configuration_report.json`이 생성됩니다.

| 보고서 항목 | 기대할 내용 |
|---|---|
| `articulation` | 실제 설정한 root 경로 |
| `solver_position_iterations`, `solver_velocity_iterations` | 64, 4 |
| `finger_joint`, `max_force` | 직접 구동 joint 경로, 200 |
| `friction` | 1.0 |
| `material_bound_colliders` | 좌우 inner finger의 Collider 경로 |

`configured.usda`는 원본을 참조하는 파일이므로 원본 에셋 접근도 계속 필요합니다. 현재 앱의 장면은 메모리상의 stage이며 파일은 Export로 만들어집니다. GUI 편집까지 저장하려면 **File > Open으로 `configured.usda`를 다시 열고** 그 파일을 작업 대상으로 삼으세요.

## 2. 손가락의 힘과 접촉을 관찰하기

### 코드에서 볼 부분

모터 한도와 물리 재질은 따로 작성합니다.

```python
drive.CreateMaxForceAttr(args.max_force)
physics.CreateStaticFrictionAttr(args.friction)
physics.CreateDynamicFrictionAttr(args.friction)
```

여기서 `drive`는 `finger_joint`의 angular drive입니다. 회전 관절의 effort 한도이므로 물리적으로 토크에 해당합니다. 이 한도를 200으로 설정하는 것만으로 손가락이 닫히지는 않습니다. 위치나 속도 목표도 있어야 합니다.

재질은 `/ur/Looks/FingerPhysics`에 만들고, 이름에 `left_inner_finger` 또는 `right_inner_finger`가 포함된 실제 Collider를 찾아 연결합니다.

```python
UsdShade.MaterialBindingAPI.Apply(collider).Bind(material, materialPurpose="physics")
```

`physics` 목적의 바인딩은 손가락 색을 바꾸는 외관 재질과 구분됩니다. 보고서의 Collider 목록을 선택하여 Property에서도 같은 재질을 가리키는지 확인하세요. 코드는 편집할 수 있도록 찾은 instance prim의 Instanceable을 해제하지만, 별도 구조의 사용자 에셋까지 모두 처리한다고 가정하지 않습니다.

### 설정에서 볼 부분: 목표 추종

1. `configured.usda`를 열고 **Tools > Physics > Physics Inspector**를 선택합니다.
2. `/ur`를 선택한 뒤 Inspector의 Refresh를 누릅니다.
3. `finger_joint`의 목표 슬라이더를 작은 범위에서 움직이고 실제 DOF 위치가 따라오는지 봅니다.
4. 다음 일반 시뮬레이션으로 넘어가기 전에 Inspector를 닫습니다. 시험 값을 저장할지 묻는다면 유지할 값만 선택합니다.
5. **Tools > Robotics > Asset Editors > Gain Tuner**를 열고 로봇 `ur`를 선택합니다.
6. Tune Gains에서 Natural Frequency=0.5, Damping Ratio=1.0을 시작점으로 두고, Test Gains Settings에서 작은 관절 묶음을 선택해 시험합니다.

Natural Frequency는 목표에 반응하는 빠르기와 관련되고, Damping Ratio는 진동을 얼마나 억제할지 조정하는 기준입니다. 이 값은 공식 수업의 출발점이지 모든 관절의 최적값은 아닙니다. 먼저 목표와 실제 위치 곡선이 어느 구간에서 벌어지는지 읽으세요.

### 실행 결과 확인하기

Inspector에서는 실제 위치가 목표 방향으로 움직이는지, Gain Tuner에서는 응답이 목표를 지나쳤다가 반복해서 돌아오는지 확인합니다. 목표에 도달하지 못하는 현상과 목표를 지나치는 현상은 다른 원인을 가질 수 있습니다.

설정 보고서에는 추종 오차나 물체 잡기 기록이 없습니다. **보고서의 friction=1.0은 적용한 값의 증거이며 grasp 성공의 증거는 아닙니다.** 접촉 물체와 집기 시퀀스가 있어야 마찰의 실제 효과를 비교할 수 있습니다.

## 3. 조정 위치에 따른 역할 정리

```text
목표·drive gain → 어떤 운동을 얼마나 강하게 요구하는가
Max Force      → drive가 낼 수 있는 effort를 어디까지 허용하는가
마찰           → 물체와 닿았을 때 미끄러짐에 어떻게 저항하는가
solver 반복    → 관절·접촉 조건을 얼마나 반복해서 계산하는가
```

값을 저장하는 단계와 물리를 실행하는 단계를 구분하면, 설정 오류를 동작 문제로 오해하거나 그 반대로 판단하는 일을 줄일 수 있습니다.

## 4. 간단한 확인 실험

**`--friction`만 1.0에서 0.5로** 바꿔 새 결과를 만드세요.

```bash
~/isaacsim/python.sh src/41_robot_setup_configure_manipulator/run.py \
  --headless --steps 10 --friction 0.5 \
  --output src/41_robot_setup_configure_manipulator/output/friction_05
```

두 보고서에서 friction이 달라지고 Max Force와 solver 반복은 같은지 확인합니다. 새 USD의 재질에서는 Static과 Dynamic Friction이 모두 0.5여야 합니다. 이번 비교가 직접 보여주는 것은 **작성된 접촉 설정의 변화**입니다. 실제 미끄러짐까지 비교하려면 동일한 물체·자세·손가락 목표를 갖춘 별도 접촉 실험이 필요합니다.

## 실행할 때 막히면

- **`Expected one articulation` 오류가 납니다**: 조립 파일의 root가 둘로 남았거나 그리퍼 구성이 달라졌는지 확인하세요.
- **finger_joint 또는 양쪽 Collider를 못 찾습니다**: `--asset`이 UR10e+Robotiq 구성인지, gripper variant가 `None`인지, 실제 prim 이름이 기대 구조와 같은지 확인하세요.
- **손가락이 자동으로 닫히지 않습니다**: 실행기는 목표를 바꾸지 않습니다. Inspector에서 작은 목표를 주어 시험하세요.
- **진동이 커집니다**: Max Force만 올리지 말고 local frame, 초기 접촉 겹침, gain과 물리 간격을 나누어 확인하세요.
- **GUI에서 바꾼 값이 파일에 없습니다**: Export된 `configured.usda`를 다시 열어 편집하고 저장했는지 확인하세요. JSON은 최초 적용값만 기록합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 7: Configure a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html)에 대응합니다. 원문의 physics layer 편집값을 로컬 실행기는 참조 위의 override로 작성합니다.

`tutorial.json`의 상태는 `not_run`입니다. 설정 파일의 구조 대조와 실제 Inspector·Gain Tuner·접촉 동작은 다른 확인 범위이며, 본 문서의 관찰 설명은 GUI에서 수행할 실습 기준입니다.
