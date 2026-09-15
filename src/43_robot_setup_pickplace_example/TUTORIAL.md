# 43. 그리퍼 제어에서 실제 물체 옮기기까지

## 이번에 배우는 것

**같은 UR10e와 Robotiq를 네 가지 방식으로 제어하고, 명령 완료와 실제 도달 결과를 구분합니다.**

손가락을 닫는 명령, 손끝을 목표에 보내는 계산, 물체를 집어 옮기는 작업은 서로 다른 단계입니다. 이번 실행기는 `--exercise`로 단계를 나누어 시험합니다. 각 단계에서 무엇을 명령하고 무엇을 측정하는지 먼저 구분해 보세요.

| 모드 | 보내는 명령 | 주로 확인할 결과 |
|---|---|---|
| `gripper` | finger_joint 열기·닫기 | 실제 `finger_rad` 변화 |
| `ik` | 목표 위치·방향에 맞는 관절 자세 | `ik_failures`, `target_error_m` |
| `rmpflow` | 목표를 따라가는 연속 운동 | 손끝 궤적과 `target_error_m` |
| `pick` | 접근·집기·이동·놓기 순서 | 큐브 이동과 `cube_target_error_m` |

**IK**는 목표 손끝 자세에 해당하는 관절 각도를 구하는 역기구학입니다. **RMPflow**는 목표와 로봇 상태를 바탕으로 다음 운동을 계속 계산하는 방식입니다. 집기 모드는 RMPflow와 그리퍼 명령을 순서대로 묶습니다.

## 1. 그리퍼와 목표 추종부터 실행하기

Isaac Sim 5.1.0, 지원 GPU, Lula/RMPflow와 `isaacsim.robot.manipulators`가 필요합니다. 공식 `/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd`를 사용하며, 운동 설정은 이 폴더의 `config/`에 포함되어 있습니다.

저장소 루트에서 각 명령을 따로 실행하세요.

```bash
~/isaacsim/python.sh src/43_robot_setup_pickplace_example/run.py \
  --exercise gripper --steps 800

~/isaacsim/python.sh src/43_robot_setup_pickplace_example/run.py \
  --exercise ik --target 0.5 0 0.5 --steps 120

~/isaacsim/python.sh src/43_robot_setup_pickplace_example/run.py \
  --exercise rmpflow --target 0.5 0 0.5 --steps 600
```

`--steps`를 생략하거나 GUI에서 0으로 지정하면 창을 닫을 때까지 제어와 물리가 계속됩니다. Headless는 `--headless`를 추가하며, 단계 수 생략 시 6000단계입니다. 세 모드의 물리 간격은 **1/60초**입니다. Gripper 800단계는 시뮬레이션 시간 약 13.3초로 한 번 닫고 여는 주기를 관찰하는 길이입니다.

### 코드에서 볼 부분

그리퍼는 직접 구동하는 joint 하나만 명령합니다.

```python
joint_prim_names=["finger_joint"]
joint_opened_positions=np.array([0.0])
joint_closed_positions=np.array([0.7])
use_mimic_joints=True
```

다른 손가락과 knuckle 관절은 mimic 관계를 따라 움직입니다. 이때 Python articulation 명령의 각도는 **rad**입니다. 닫힘 0.7 rad는 약 40.1°이며, 설정 파일 `ur10e_kinematics.urdf`의 finger_joint 상한과 맞춘 값입니다.

팔의 여섯 관절은 이름으로 실제 DOF 인덱스를 찾아 초기화합니다.

```python
arm_indices = np.array([robot.get_dof_index(name) for name in description["cspace"]])
robot.set_joint_positions(np.array(description["default_q"]), joint_indices=arm_indices)
```

USD의 관절 순서가 YAML의 순서와 같다고 가정하지 않는 이유입니다. IK와 RMPflow가 사용하는 end-effector 이름은 URDF의 `ee_link_robotiq_arg2f_base_link`이고, 화면의 USD 경로는 `/ur/ee_link/robotiq_arg2f_base_link`입니다. 두 주소는 표기 체계가 다릅니다.

IK에서는 다음 조건으로 해를 적용합니다.

```python
action, success = solver.compute_inverse_kinematics(
    target_position=position, target_orientation=orientation)
if success:
    robot.apply_action(action)
```

해를 찾지 못하면 `ik_failures`가 늘고 그 단계의 새 action을 적용하지 않습니다. 계산 성공과 물리 로봇의 실제 도달은 다르므로 실행 후 위치를 다시 읽습니다.

RMPflow에서는 `ArticulationMotionPolicy(robot, rmp, physics_dt)`가 운동 정책을 실제 로봇과 물리 간격에 연결합니다. 반복문은 다음 action을 받아 적용한 뒤 물리를 진행합니다.

```python
robot.apply_action(motion.forward(
    target_end_effector_position=position,
    target_end_effector_orientation=orientation))
```

같은 위치 목표라도 매 단계의 운동을 계속 계산하므로, 최종 자세뿐 아니라 목표까지 이어지는 움직임을 살펴보세요.

### 실행 결과 확인하기

Gripper에서는 0~400단계 동안 닫히고 400~800단계 동안 열리는 방향을 봅니다. 실제 관절 값이 목표에 완벽히 일치한다고 미리 가정하지 마세요.

IK와 RMPflow에서는 빨간 `/World/Target`이 기본 `(0.5, 0, 0.5)` m에 있습니다. 목표 방향은 Euler `(-π, 0, π)`를 쿼터니언으로 바꾼 값입니다. 실행 중 목표 prim을 조금 옮기면 매번 읽은 위치·방향을 따라 제어합니다.

결과는 종료 시 이 폴더의 `output/<고유번호>/result.json`에 저장됩니다. `--output`으로 지정할 때는 존재하지 않는 새 폴더를 사용하세요.

| 항목 | 의미 |
|---|---|
| `samples[].step` | 100단계마다 기록하는 0 기반 루프 번호 |
| `samples[].end_effector_m` | 물리 단계 후 측정한 그리퍼 base 위치 |
| `samples[].finger_rad` | 실제 finger_joint 각도 |
| `target_error_m` | 마지막 그리퍼 base와 빨간 목표의 위치 거리 |
| `ik_failures` | IK 계산이 실패한 횟수 |

표본은 물리 단계 뒤에 기록하므로 `step=0`도 첫 물리 진행 후 값입니다. `target_error_m`는 방향 오차를 포함하지 않습니다. Pick 이외의 모드에서는 `controller_done`과 `cube_target_error_m`가 `null`인 것이 정상입니다.

## 2. 물리 기반 집기와 놓기 실행하기

```bash
~/isaacsim/python.sh src/43_robot_setup_pickplace_example/run.py \
  --exercise pick --steps 6000
```

기본 모드도 `pick`입니다. 파란 큐브는 중심 `(0.3, 0.3, 0.3)` m에서 시작하며 크기는 `(0.1, 0.0515, 0.1)` m입니다. 빨간 목표는 놓기 위치 `(-0.3, 0.6, 0.05)` m로 바뀝니다. 높이 0.1 m인 물체가 바닥에 놓이면 중심은 약 0.05 m라는 점을 연결해 보세요.

### 코드에서 볼 부분

집기 모드에서는 물리 간격을 **1/200초**로 줄입니다. 따라서 6000단계는 시뮬레이션 시간 30초입니다. 다른 모드의 6000단계와 같은 시간이 아닙니다.

```python
pick.forward(
    picking_position=cube.get_world_pose()[0],
    placing_position=place_goal,
    current_joint_positions=robot.get_joint_positions(),
    end_effector_offset=np.array([0.0, 0.0, 0.20]))
```

`picking_position`은 시뮬레이터에서 읽은 실제 큐브 위치입니다. 카메라로 물체를 검출하는 과정은 없습니다. `end_effector_offset`은 그리퍼 base와 실제 집는 지점 사이를 고려하는 0.20 m 보정입니다. 이 보정이 맞지 않으면 손끝 대신 그리퍼의 다른 부분을 목표에 가져갈 수 있습니다.

PickPlaceController는 접근, 하강, 닫기, 상승, 운반, 놓기 등을 순서대로 진행합니다. `events_dt`의 열 개 값은 각 단계의 내부 진행 속도를 정하며 “물체가 잡혔음을 감지했다”는 센서 판정이 아닙니다.

운동 계산에 사용하는 파일도 구분해 보세요.

| 설정 파일 | 담당하는 정보 |
|---|---|
| `ur10e_kinematics.urdf` | 링크·관절·관성 구조; visual/collision mesh 요소는 제거됨 |
| `robot_descriptor.yaml` | 팔 cspace, 초기 각도, 고정 그리퍼 값, 충돌 구 |
| `ur10e_rmpflow_common.yaml` | 목표·관절 제한·충돌 반응 등의 RMPflow 값 |

렌더링과 물리 접촉은 공식 USD가 담당합니다. 로컬 코드에는 외부 장애물을 RMPflow에 등록하는 과정이 없으므로 장면에 장애물을 추가하는 것만으로 회피까지 설정되지는 않습니다.

### 실행 결과 확인하기

큐브가 바닥으로 내려온 뒤 손가락 사이에서 실제로 들리고, 운반 후 목표 근처에 놓이는지 관찰하세요. 결과 JSON에서는 다음을 함께 읽습니다.

- `samples[].cube_m`: 큐브의 실제 위치 표본입니다. 높이가 올라갔다 내려오는 과정을 확인합니다.
- `controller_done`: 정해진 제어 순서를 마쳤는지 나타냅니다.
- `cube_target_error_m`: 최종 큐브 중심과 놓기 목표의 거리입니다.

**제어 순서를 끝냈어도 물체를 놓쳤을 수 있습니다.** 관찰 기준으로 목표 3 cm 이내에 놓이는지 보고, 마지막 순간뿐 아니라 바닥에 안정적으로 남는지도 확인하세요. 실행기가 3 cm 기준으로 자동 합격 판정을 하지는 않습니다.

Pick의 `target_error_m`는 여전히 **그리퍼 base**의 거리입니다. 이를 큐브의 놓기 오차로 읽으면 안 됩니다. 또한 `--target` 값은 pick의 고정 놓기 목표를 바꾸지 않습니다. 작업 완료 후에도 물리는 계속 진행하며 다음 집기를 자동 재시작하지 않습니다.

## 3. 계산·제어·물체 결과 정리

```text
IK 성공             → 목표 자세에 맞는 관절 해를 구함
손끝 위치 오차 감소  → 실제 로봇이 위치 목표에 접근함
controller_done     → 집기 제어 순서를 마침
큐브 위치·안정성    → 실제 물체가 원하는 곳에 놓임
```

각 결과는 앞 단계의 성공만으로 보장되지 않습니다. 자신이 시험한 모드와 그 모드의 실제 측정값을 연결해 읽는 것이 이번 실습의 핵심입니다.

## 4. 간단한 확인 실험

IK 모드에서 **목표의 X만 0.5에서 0.6 m로** 바꿔 120단계를 실행하세요. Y, Z, 목표 방향과 단계 수는 그대로 둡니다.

```bash
~/isaacsim/python.sh src/43_robot_setup_pickplace_example/run.py \
  --exercise ik --target 0.6 0 0.5 --steps 120
```

빨간 목표가 0.1 m 옮겨지는지, 다른 관절 자세로 접근하는지 확인합니다. `ik_failures`와 최종 오차를 기본 목표 결과와 비교하세요. 도달 가능성과 같은 시간 안의 수렴 정도는 별개이므로 오차가 커졌다고 즉시 IK 실패로 해석하지 않습니다.

## 실행할 때 막히면

- **그리퍼가 없거나 joint를 찾지 못합니다**: 구성된 UR10e+Robotiq USD와 활성 그리퍼 variant를 확인하세요. 로컬 에셋은 `--asset`으로 지정합니다.
- **IK가 반복해서 실패합니다**: 기본 목표로 돌아가고 URDF의 end-effector 이름과 YAML cspace를 확인하세요.
- **RMPflow 초기화가 실패합니다**: `config/` 파일을 함께 보존하고 sphere link 이름이 URDF와 맞는지 확인하세요.
- **`controller_done=true`인데 물체가 옮겨지지 않았습니다**: 큐브 표본, 손가락 실제 각도, 접촉 마찰, 0.20 m offset과 단계 시간을 각각 조사하세요.
- **실행 중 `result.json`이 없습니다**: 파일은 종료 시 기록됩니다. 창을 닫거나 양수 `--steps`로 실행을 마치세요. 강제 중단은 결과 저장을 보장하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 9: Pick and Place Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html)에 대응합니다. 포함 설정의 출처와 변경은 [NOTICE.md](NOTICE.md)에 있습니다. Finger 닫힘을 0.7 rad로 설정하고, descriptor의 일곱 link 이름을 제공 URDF와 맞추며, 놓기 중심 높이를 0.05 m로 정한 것은 로컬 구현의 조정입니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 **2026-09-14, `--exercise ik --headless --steps 120`** 조건에서 `ik_failures=0`, `target_error_m≈0.000952` m를 기록합니다. 이는 약 0.95 mm의 위치 오차이며 해당 실행의 측정값입니다. Gripper·RMPflow·pick, GUI 조작, 다른 목표의 검증을 뜻하지 않습니다. `tutorial.json`도 이 범위를 `partial_runtime_verified`로 구분합니다.

위 수치는 당시 입력 버전의 참고 기록이며 현재 실행기를 다시 검증한 결과는 아닙니다.
