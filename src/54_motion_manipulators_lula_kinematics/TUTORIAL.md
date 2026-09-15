# 54. IK가 성공하면 로봇도 목표에 도착했을까?

## 이번에 배우는 것

**목표 위치에서 관절 해를 구하는 IK와 실제 관절값에서 말단 위치를 구하는 FK를 연결해, 계산 성공과 물리 추종을 구분합니다.**

손을 `(0.3, 0, 0.5)` m에 놓으려면 팔의 관절들을 얼마나 움직여야 할까요? 이 질문을 푸는 계산이 **역기구학, IK**입니다. 반대로 지금의 관절 각도에서 손이 어디에 있는지 계산하는 것은 **순기구학, FK**입니다.

| 이번 실습의 요소 | 의미 |
|---|---|
| `/World/panda` | 실제 물리 관절을 가진 Franka |
| `/World/target` | 원하는 월드 위치를 표시하는 빨간 cube |
| `right_gripper` | 위치를 맞출 Lula의 말단 frame |
| IK 결과 | 목표를 만족할 관절 목표와 성공 여부 |
| FK 결과 | 현재 관절 상태로 계산한 말단 위치·회전행렬 |
| `kinematics.json` | IK 성공 여부와 실제 FK 오차의 기록 |

## 1. 먼저 도달 가능한 위치를 지정하기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. Lula 설정은 설치된 motion generation 확장의 Franka 설정을 읽습니다.

다음은 **저장소 루트** 기준 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/54_motion_manipulators_lula_kinematics/run.py \
  --target 0.3 0 0.5 --steps 180
```

Franka가 빨간 목표에 접근하는 동안 180단계, 즉 물리 시간 3초를 진행하고 종료합니다. 물리 간격은 1/60초입니다. 창 없이 실행하려면 `--headless`를 추가하세요. GUI에서 `--steps`를 생략하면 목표를 계속 읽으며 창을 닫을 때까지 실행합니다.

### 코드에서 볼 부분

```python
config = interface_config_loader.load_supported_lula_kinematics_solver_config('Franka')
solver = LulaKinematicsSolver(**config)
kinematics = ArticulationKinematicsSolver(robot, solver, args.frame)
```

`LulaKinematicsSolver`는 URDF와 robot description으로 기구학을 계산합니다. `ArticulationKinematicsSolver`는 시뮬레이터의 실제 관절 상태를 읽고 Lula 관절 순서에 맞추는 연결 역할을 합니다. 그리퍼를 포함한 articulation의 배열을 무조건 그대로 IK 입력에 쓰지 않는 이유입니다.

반복문에서는 목표 위치와 로봇 base의 pose를 먼저 읽습니다.

```python
solver.set_robot_base_pose(*robot.get_world_pose())
action, success = kinematics.compute_inverse_kinematics(position)
if success:
    robot.apply_action(action)
world.step(render=not args.headless)
```

목표는 월드 좌표입니다. solver에도 로봇 base가 월드의 어디에 있는지 알려야 두 위치를 같은 기준으로 계산할 수 있습니다. `success`가 참일 때만 새 관절 목표를 전달합니다.

이 호출은 **위치만 요구**합니다. 손의 방향까지 맞추도록 지정한 실습은 아니며, 빨간 cube도 집을 물체가 아닌 위치 표시입니다.

### 실행 결과 확인하기

결과는 이 폴더의 새 `output/run_*/kinematics.json`에 저장됩니다.

| 항목 | 해석 |
|---|---|
| `frame`, `available_frames` | 선택한 말단과 URDF에서 읽은 frame 목록 |
| `trace[].ik_success` | 해당 반복에서 IK 해를 찾았는지 |
| `fk_position_m`, `target_m` | 실제 관절로 계산한 위치와 목표 위치 |
| `position_error_m` | 두 위치 사이의 3차원 거리 |
| `fk_rotation_matrix` | 실제 FK의 3×3 회전행렬 |

`ik_success=true`인 첫 행에서도 위치 오차는 클 수 있습니다. IK는 가능한 관절값을 찾았지만 물리 drive는 이제 그 값으로 움직이기 시작했기 때문입니다. 뒤의 표본에서 오차가 어떻게 변하는지 읽어 보세요.

기록은 `step=0, 30, 60, ...`에서 물리 계산 후 남깁니다. 180단계 실행의 마지막 기록은 `step=150`이므로 종료 직전 값과 같다고 단정하지 않습니다. `step=0`도 초기 상태가 아니라 **첫 물리 단계 뒤**의 표본입니다.

## 2. frame과 FK를 기준으로 결과 다시 읽기

`right_gripper`는 USD prim 경로가 아니라 **Lula URDF에 정의된 frame 이름**입니다. 같은 팔 자세라도 손목, 손가락 끝, 집게 중심은 서로 다른 위치에 있습니다. 무엇을 목표에 맞췄는지 먼저 확인해야 합니다.

### 코드에서 볼 부분

```python
ee_position, rotation = kinematics.compute_end_effector_pose()
error = np.linalg.norm(position - ee_position)
```

두 번째 줄은 저장하는 거리 오차를 풀어 쓴 것입니다. 차이가 `(dx, dy, dz)`라면 거리는 `sqrt(dx² + dy² + dz²)`입니다. 예를 들어 높이만 0.01 m 어긋나면 오차는 1 cm입니다.

첫 번째 호출은 전달한 목표 관절값이 아니라 **실제 articulation 상태**로 FK를 계산합니다. 목표값으로만 FK를 계산하면 IK가 만든 해가 맞는지는 볼 수 있어도 실제 팔이 따라왔는지는 알 수 없습니다.

### 실행 결과 확인하기

1. JSON의 `frame`이 `right_gripper`인지 확인하세요.
2. 같은 행의 `target_m - fk_position_m`을 계산해 어느 축으로 오차가 남았는지 읽어 보세요.
3. `fk_rotation_matrix`가 3행 3열인지 확인하세요. 네 성분의 quaternion과는 다른 표현입니다.
4. GUI에서 target을 움직였다면 각 행의 `target_m`도 달라졌는지 확인하세요. 움직이는 목표의 오차와 정지 목표의 수렴을 같은 조건으로 비교하지 않습니다.

Franka처럼 7축 팔은 같은 위치에 도달하는 자세가 여러 개일 수 있습니다. 이 연결 객체는 현재 자세를 IK의 출발점으로 활용합니다. 그래도 해를 찾았다는 사실이 그 자세로 가는 모든 중간 경로의 충돌 부재를 뜻하지는 않습니다. 기구학 계산의 역할은 [공식 Lula Kinematics Solver](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_kinematics.html)에서 더 볼 수 있습니다.

실패한 입력을 읽는 방법도 확인하려면 별도 실행에서 `--target 3 0 3 --steps 180`을 사용하세요. 이 목표는 기본 Franka의 작업영역 밖입니다. 성공한 IK가 한 번도 없으면 프로그램은 `kinematics.json`을 저장한 뒤 오류로 종료합니다. 저장된 `ik_success=false`와 큰 위치 오차를 확인하세요. 실패를 종료 시 판정하므로 이 비교에서는 유한 `--steps`를 유지합니다.

## 3. 두 계산을 연결한 흐름 정리

```text
목표 위치 → IK → 관절 목표
                    ↓ drive와 물리 계산
실제 관절값 → FK → 실제 말단 위치 → 목표와 거리 비교
```

**IK 성공은 해의 존재를, FK 오차는 현재 추종 상태를 설명합니다.** 전자는 계산 문제이고 후자는 실제로 움직인 결과를 포함합니다. 두 값을 함께 봐야 “계산은 되지만 아직 움직이는 중”인 상태를 구분할 수 있습니다.

## 4. 간단한 확인 실험

1절의 명령에서 **목표 z만 0.5에서 0.6으로** 바꾸세요.

```bash
~/isaacsim/python.sh src/54_motion_manipulators_lula_kinematics/run.py \
  --target 0.3 0 0.6 --steps 180
```

목표 높이는 10 cm 올라갑니다. `target_m`의 z와 FK 위치의 z가 함께 달라지는지, IK 성공 뒤 오차가 줄어드는지 비교하세요. 바뀐 말단 위치를 만들기 위해 여러 관절의 회전 조합이 달라집니다.

## 실행할 때 막히면

- **알 수 없는 frame 오류**: 오류에 출력된 목록에서 이름을 고르세요. `/World/panda/...` 경로는 `--frame` 입력이 아닙니다.
- **IK가 한 번도 수렴하지 않았다는 오류**: 목표가 작업영역 밖인지 확인하세요. 코드는 실행 종료 후 JSON을 저장하고, 성공이 한 번도 없으면 오류로 끝냅니다.
- **성공 표시가 있는데 오차가 남음**: 실행 길이, 실제 관절 drive와 접촉을 살펴보세요. IK 플래그만으로 물리 추종을 판정하지 않습니다.
- **위치가 일정하게 어긋남**: base pose, 선택한 frame의 offset, m 단위를 순서대로 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Lula Kinematics Solver](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_kinematics.html)에 대응합니다. 로컬 실습은 위치 IK와 실제 상태 FK를 연결하고 30단계 간격으로 기록합니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 headless 180단계 기본 목표에서 마지막 저장 오차가 약 **0.00104 m**였던 관찰이 있습니다. 과거 실행의 참고값이며 현재 코드 재실행이나 다른 목표·frame·GUI 조작의 결과는 아닙니다. 목표별 성공 여부와 실제 FK 오차는 새 실행의 기록으로 확인하세요.
