# 25. Jetbot의 이동을 Franka의 집기로 연결하기

## 이번에 배우는 것

**Jetbot의 이동·후퇴·정지와 Franka의 집기·놓기를 세 상태로 연결하고, 작업 인계가 언제 일어나는지 살펴봅니다.**

두 로봇을 한 장면에 놓는 것만으로 협업이 이루어지지는 않습니다. 이동 로봇이 아직 접근 중인데 팔이 움직이거나, 큐브를 남긴 뒤에도 이동 로봇이 계속 후퇴하면 서로의 작업을 방해할 수 있습니다. 이번에는 `HandoverTask`가 현재 단계를 저장하고 `run.py`가 그 단계에 맞는 명령을 보냅니다.

| 상태 | Jetbot의 명령 | Franka의 명령 |
|---|---|---|
| `0 DRIVE` | 평면 목표로 이동 | 집기 명령을 아직 보내지 않음 |
| `1 RETREAT` | 두 바퀴에 -8 rad/s | 집기 명령을 아직 보내지 않음 |
| `2 PICK` | 두 바퀴에 0 rad/s | 실제 큐브 위치에서 집기·놓기 진행 |

큐브는 Jetbot 앞에 놓이며 접촉에 의해 밀립니다. 인계 상태는 Jetbot의 위치와 경과 단계로 바뀌므로, 상태가 끝까지 진행해도 실제 큐브 운반은 별도로 확인해야 합니다.

## 1. 두 로봇의 작업 인계 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU, Jetbot·Franka 에셋이 필요합니다. 사용 경로는 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`와 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`입니다. Franka 제어에는 설치에 포함된 Lula/RMPflow를 사용합니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 실제 설치 경로로 바꿀 수 있습니다.

```bash
~/isaacsim/python.sh src/25_core_core_adding_multiple_robots/run.py --steps 2400
```

Jetbot은 `(0, 0.3, 0)` m, 큐브는 `(0.1, 0.3, 0.05)` m에서 시작하고 Franka의 base는 `(1, 0, 0)` m로 이동시킵니다. Jetbot 목표는 평면상 `(1.3, 0.3)` m이며, 큐브의 최종 배치 목표는 `(0.7, -0.3, 0.02575)` m입니다.

물리 2400단계 후 결과를 저장하고 종료합니다. 이 횟수는 60 Hz에서 시뮬레이션 시간 약 40초에 해당하며, 그 안에 작업이 완료되리라는 보장은 아닙니다. `--headless`를 추가하면 창 없이 실행하고, headless에서 단계를 생략하면 2400단계입니다.

### 코드에서 볼 부분

`handover_task.py`의 상태 전환은 다음 두 조건에 달려 있습니다.

```python
if self.event == 0 and np.linalg.norm(self.jetbot.get_world_pose()[0][:2] - self.goal[:2]) < 0.04:
    self.event = 1
    self.arrival_step = control_index
elif self.event == 1 and control_index - self.arrival_step >= self.retreat_steps:
    self.event = 2
```

`[:2]`는 x·y만 골라 바닥 위 거리로 비교한다는 뜻입니다. 목표와의 거리가 4 cm보다 작아지면 도착 시점을 저장합니다. 그 뒤 기본 물리 200단계가 지나면 후퇴를 마치고 집기로 넘어갑니다. **큐브가 어디까지 밀렸는지는 이 조건에 들어 있지 않습니다.**

### 실행 결과 확인하기

터미널에서 `event=1 RETREAT`, `event=2 PICK`을 찾으세요. 120단계마다 현재 event도 출력합니다. 화면에서는 큐브가 Jetbot과 함께 이동하는지, 후퇴 뒤 Franka가 접근할 공간이 생기는지 관찰합니다.

이 폴더의 `output/<고유번호>/result.json`은 항목 하나를 가진 배열입니다.

| 필드 | 확인할 내용 |
|---|---|
| `event` | DRIVE·RETREAT·PICK 중 어디까지 진행했는지 |
| `controller_done` | Franka 제어기의 집기·놓기 단계가 끝났는지 |
| `jetbot_position_m` | 마지막 이동 로봇 위치 |
| `cube_position_m`, `target_m` | 실제 큐브 중심과 최종 배치 목표 |
| `cube_target_error_m`, `within_3cm` | 최종 3차원 거리와 `< 0.03` m 판정 |

`event=2`는 Franka에 작업을 넘겼다는 뜻입니다. 큐브를 잡았다는 뜻은 아닙니다. `controller_done`도 실제 물체 도착과 함께 해석하세요.

## 2. 상태마다 다른 제어기를 연결하기

`run.py`는 매 반복에서 `world.get_observations()`를 읽습니다. DRIVE에서는 `WheelBasePoseController`가 현재 위치·자세와 목표로부터 이동 명령을 만들고, 내부 `DifferentialController`가 두 바퀴 속도로 바꿉니다. 바퀴 반지름은 0.03 m, 바퀴 사이 거리는 0.1125 m로 설정되어 있습니다.

### 코드에서 볼 부분

PICK 분기의 시작은 로봇 팔 명령이 아니라 Jetbot 정지입니다.

```python
task.jetbot.apply_wheel_actions(
    ArticulationAction(joint_velocities=np.zeros(2)))
```

후퇴 분기에서 보낸 바퀴 속도 목표를 0으로 갱신해야 Jetbot이 계속 뒤로 가지 않습니다. 이후 Franka의 `picking_position`에는 그 순간 관찰한 큐브 위치를 넣습니다. 큐브가 예상보다 덜 밀렸거나 옆으로 벗어났을 때도 제어 입력 자체는 현재 상태를 사용합니다.

장면 준비에서는 Franka에 `set_world_pose()`와 `set_default_state()`를 함께 사용합니다. 앞 호출은 지금의 위치를, 뒤 호출은 `world.reset()` 후 돌아갈 위치를 정합니다. 둘 중 현재 위치만 바꾸면 초기화할 때 원래 자리로 돌아갈 수 있습니다.

`pre_step()`은 `world.step()` 안에서 상태를 갱신하고, 제어 루프는 다음 반복에서 새 상태를 읽습니다. 따라서 전환 로그와 새 명령의 적용 사이에 한 반복 차이가 있을 수 있습니다.

창에서 충분히 관찰하려면 단계 수를 생략해 실행해 보세요.

```bash
~/isaacsim/python.sh src/25_core_core_adding_multiple_robots/run.py
```

이 GUI 실행은 Franka 제어기 완료 후 120단계를 더 진행해 결과를 저장한 다음 창과 물리를 유지합니다. 한편 앞의 유한 실행은 2400단계에 측정하므로, 둘의 결과 저장 시점이 같다고 가정하지 마세요.

## 3. 작업 인계 조건 정리

```text
Jetbot이 목표 4 cm 안에 도착
    → 후퇴 시작 시점 저장
    → 기본 200단계 동안 후퇴
    → Jetbot 정지 + Franka 집기 시작
    → 실제 큐브의 최종 위치로 배치 판정
```

앞부분은 **다음 동작을 시작할 조건**, 마지막은 **작업 결과의 측정**입니다. 접촉으로 큐브를 미는 방식에서는 이동 로봇의 도착만으로 물체 도착을 알 수 없습니다. 상태 로그와 큐브 오차를 함께 남기는 이유가 여기에 있습니다.

## 4. 간단한 확인 실험

후퇴 길이만 200단계에서 150단계로 줄여 보세요.

```bash
~/isaacsim/python.sh src/25_core_core_adding_multiple_robots/run.py --steps 2400 --retreat-steps 150
```

후퇴 상태의 시간은 약 3.33초에서 2.5초로 줄어듭니다. 같은 -8 rad/s 명령을 더 짧게 보내므로 후퇴 거리는 대체로 줄겠지만, 실제 거리는 접촉과 미끄러짐의 영향을 받습니다. PICK 시작 때의 Jetbot 위치, Franka와의 간섭, 최종 큐브 오차를 비교하세요. 시간을 줄인 것이 곧 작업 개선을 뜻하지는 않습니다.

## 실행할 때 막히면

- **계속 `event=0`임**: Jetbot 자체가 목표 4 cm 안에 들어와야 전환합니다. 바퀴 움직임과 목표 위치를 보고, 짧은 실행을 사용했다면 단계 수를 늘려 보세요.
- **PICK으로 넘어갔지만 큐브가 멀리 있음**: 접촉 운반 중 큐브가 벗어났을 수 있습니다. 제어기 단계 종료를 성공으로 읽지 말고 `cube_target_error_m`를 확인하세요.
- **Jetbot 자산 경로 오류**: `--asset /실제/경로/jetbot.usd`를 지정할 수 있습니다. 이 옵션은 Jetbot만 바꾸므로 Franka 에셋도 별도로 접근 가능해야 합니다.
- **GUI에서 결과가 아직 없음**: 무제한 GUI는 제어기 완료를 기다립니다. 창을 먼저 닫으면 결과가 저장되지 않을 수 있으므로, 부분 상태가 필요하면 양수 `--steps`로 실행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Adding Multiple Robots](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html)를 바탕으로 Task 상태와 두 제어기의 연결을 독립 Python 예제로 구성했습니다. 최종 큐브 오차와 실행 길이 선택은 로컬 실습에서 추가한 관찰 장치입니다.

`tutorial.json`의 검증 상태는 `not_run`입니다. 이 문서는 코드의 상태 조건·명령·출력 구조를 대조해 작성했으며, Jetbot 운반과 Franka 집기의 실제 성공을 확인한 실행 기록은 없습니다.
