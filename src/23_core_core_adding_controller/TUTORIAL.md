# 23. 바퀴 속도 계산에서 목표 위치 제어까지

## 이번에 배우는 것

**전진·회전 명령을 좌우 바퀴 속도로 바꾸고, 현재 위치를 읽어 목표에서 멈추는 제어로 확장합니다.**

차동구동 로봇은 왼쪽과 오른쪽 바퀴를 다르게 돌려 방향을 바꿉니다. 원하는 전진 속도와 회전 속도를 바퀴 속도로 환산하는 계산은 현재 로봇이 어디에 있는지 몰라도 할 수 있습니다. 그러나 목적지에서 멈추려면 실제 위치와 방향을 계속 읽어야 합니다.

| `--controller` | 입력 | 현재 상태를 사용하나요? |
|---|---|---|
| `custom` | 전진 속도·회전 속도 | 사용하지 않음 |
| `differential` | 같은 속도 입력 | 사용하지 않음 |
| `pose` | 현재 위치·방향과 목표 위치 | 매 단계 사용 |

직접 만든 `UnicycleController`와 공식 `DifferentialController`는 같은 차동구동 식을 비교합니다. `WheelBasePoseController`는 내부에 DifferentialController를 넣고 **방향 맞추기 → 전진 → 도착 시 정지**를 계산합니다.

## 1. 먼저 목표 위치로 이동하기

Isaac Sim 5.1, 지원 NVIDIA GPU와 공식 Jetbot 에셋이 필요합니다. 기본 에셋은 Isaac 에셋 루트의 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`입니다.

다음은 저장소 루트 기준 Linux 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/23_core_core_adding_controller/run.py --controller pose --goal 0.8 0.8 --steps 900
```

로컬 에셋을 사용하려면 `--asset /절대경로/jetbot.usd`를 추가합니다. 이후의 Custom/Differential 비교와 목표 변경 명령에도 같은 `--asset`을 유지하세요. 바퀴 관절 `left_wheel_joint`, `right_wheel_joint`가 있는 공식 에셋과 그 주변 참조 파일이 필요합니다.

목표는 월드 XY 좌표 `(0.8, 0.8)` m입니다. 목표 마커는 따로 만들지 않습니다. 로봇 움직임과 출력 위치 오차를 함께 확인하세요. 1/60초 간격으로 900단계, 약 15초를 진행한 뒤 결과를 저장하고 종료합니다.

`--steps 900`을 빼면 최초 900단계 뒤 저장하고도 창을 닫을 때까지 제어를 계속합니다. 이후 경로는 JSON에 추가하지 않습니다. `--headless`는 창 없이 실행하며 단계 수 생략 시 900단계 후 종료합니다. 기본 출력은 이 폴더의 `output/고유번호/`이고, `--output`에는 새 폴더를 지정합니다.

### 코드에서 볼 부분

매 단계의 제어 흐름입니다.

```python
position, orientation = robot.get_world_pose()
action = pose.forward(
    start_position=position,
    start_orientation=orientation,
    goal_position=goal,
    lateral_velocity=abs(args.linear),
    position_tol=0.04,
)
robot.apply_wheel_actions(action)
world.step(render=not args.headless)
```

현재 위치와 쿼터니언 방향을 읽어 목표와 비교하고, 계산한 바퀴 명령을 적용한 뒤 물리를 진행합니다. `position_tol=0.04`는 목표 XY 위치와의 거리가 4 cm 미만이면 정지 명령을 내리는 기준입니다.

기본 `--linear 0.2`는 전진할 때의 속도입니다. Pose 모드에서는 현재 방향으로 회전 방향을 계산하므로 `--angular`를 매 단계 회전 명령으로 사용하지 않습니다. 별도로 넘기지 않은 `yaw_velocity`와 `heading_tol`은 설치 API의 기본값인 0.5 rad/s와 0.05 rad를 사용합니다. 목표 방향과의 차이가 약 2.86°보다 크면 전진을 멈추고 회전부터 수행합니다.

### 실행 결과 확인하기

`result.json`을 다음 순서로 읽어보세요.

| 항목 | 의미 |
|---|---|
| `controller` | 이번에 실행한 모드 |
| `goal_m` | 목표 `[x, y, z]`, 이 실습은 XY 평면 거리 사용 |
| `samples[].position_m` | 60단계 간격으로 읽은 로봇 위치 |
| `samples[].goal_error_m` | 해당 위치에서 목표까지의 평면 거리 |
| `final_goal_error_m` | 마지막 물리 단계 뒤 읽은 거리 |

충분히 진행한 Pose 실행에서는 오차가 0.04 m 부근 이하로 줄고 로봇이 정지하는지 확인합니다. 초기에는 제자리에서 방향을 맞추므로 오차가 매 행마다 감소할 필요는 없습니다.

`step`은 0부터 시작하는 반복문 인덱스입니다. 물리를 진행한 뒤 기록하므로 `step: 0`도 이미 한 단계 진행한 상태입니다. 기본 샘플은 0, 60, …, 840의 15개이며, 마지막 샘플과 900단계 후의 `final_goal_error_m`은 측정 시점이 다릅니다.

## 2. 같은 바퀴 속도를 직접 계산하기

이번에는 현재 위치를 사용하지 않는 두 모드를 같은 조건으로 실행합니다.

```bash
~/isaacsim/python.sh src/23_core_core_adding_controller/run.py --controller custom --linear 0.2 --angular 0.785398 --steps 900
~/isaacsim/python.sh src/23_core_core_adding_controller/run.py --controller differential --linear 0.2 --angular 0.785398 --steps 900
```

### 코드에서 볼 부분

직접 만든 제어기의 `forward()`는 다음 식을 사용합니다.

```python
linear, angular = command
left = (linear - angular * self.track / 2) / self.radius
right = (linear + angular * self.track / 2) / self.radius
return ArticulationAction(joint_velocities=np.array([left, right]))
```

바퀴 반지름 `radius`는 0.03 m, 좌우 간격 `track`은 0.1125 m입니다. 전진 속도 `v`는 m/s, 회전 속도 `ω`는 rad/s로 받습니다.

```text
왼쪽 바퀴 각속도  = (v - ω × 바퀴 간격 / 2) / 반지름
오른쪽 바퀴 각속도 = (v + ω × 바퀴 간격 / 2) / 반지름
```

전진만 하면 두 바퀴가 같은 속도로 돌고, 양의 회전을 더하면 오른쪽이 더 빨라집니다. 반지름으로 나누는 이유는 바퀴 둘레의 선속도를 바퀴 자체의 각속도로 바꾸기 위해서입니다.

기본 입력을 넣으면 왼쪽은 약 5.194 rad/s, 오른쪽은 약 8.139 rad/s입니다. `ArticulationAction`은 이 목표값을 담는 자료이며, 실제 적용은 `apply_wheel_actions()`가 수행합니다. 제어 함수만 호출한다고 물리가 진행되지는 않습니다.

### 실행 결과 확인하기

터미널의 `Custom wheel targets rad/s`와 `Built-in wheel targets rad/s`를 비교하세요. 모든 모드에서 시작할 때 같은 입력으로 두 계산을 출력합니다. Pose 실행에서도 이 출력은 **초기 식 비교용**이며, Pose가 매 단계 내리는 명령의 전체 기록은 아닙니다.

Custom과 Differential 모드에서는 같은 전진·회전 속도를 계속 적용합니다. 실제 경로가 비슷한지 JSON 위치를 비교하되, 이 모드가 목표 `(0.8, 0.8)`에서 멈춰야 한다고 기대하지 마세요. 목표 오차는 참고로 계산할 뿐 제어 입력에 사용하지 않습니다.

## 3. 속도 환산과 위치 피드백 정리

```text
Custom / Differential
고정 [전진, 회전] → 바퀴 목표 → 물리 진행 → 위치는 기록만

Pose
현재 위치·방향 + 목표
    → 목표 허용 거리 안이면 정지
    → 아직 멀고 방향이 다르면 회전
    → 아직 멀고 방향이 맞으면 전진
    → 바퀴 목표 적용 → 물리 진행 → 새 상태로 반복
```

현재 상태를 다시 읽어 다음 명령을 바꾸는 연결이 **피드백**입니다. 바퀴 속도 환산은 Pose 안에서도 필요하지만, 어디로 향하고 언제 멈출지를 판단하는 계층이 그 위에 추가됩니다.

정지 역시 속도 0인 명령을 적용하는 동작입니다. 마지막 전진 명령을 보낸 뒤 계산을 그만두는 것만으로 로봇이 멈춘다고 가정하면 안 됩니다.

## 4. 간단한 확인 실험

Pose의 목표에서 **X 좌표만 0.8에서 0.4로** 바꿔 같은 900단계를 실행합니다.

```bash
~/isaacsim/python.sh src/23_core_core_adding_controller/run.py --controller pose --goal 0.4 0.8 --steps 900
```

새 `goal_m`과 초기 회전 방향·이동 경로를 비교하세요. 원점 근처에서 출발한다면 목표 방향은 대략 45°에서 63.4°로 바뀝니다. 목적지까지의 거리는 줄지만 처음 방향을 맞추는 양도 달라지므로, 도착 시간이 거리 비율대로만 줄어든다고 예상하지는 않습니다.

두 실행 모두 `final_goal_error_m`와 마지막 정지 동작으로 도착을 확인하세요. 마지막 로봇 모습만 보면 실제로 어느 목표에 접근했는지 구별하기 어렵습니다.

## 실행할 때 막히면

- **Jetbot을 불러오지 못함**: 에셋 루트 접근을 확인하거나 `--asset`으로 로컬 파일을 지정하세요. 내부 참조 파일도 필요합니다.
- **회전만 하고 전진하지 않음**: 현재 방향과 목표를 비교하세요. Pose는 방향 오차가 충분히 줄어야 전진합니다. 사용자 에셋이라면 바퀴 축·이름·반지름·간격도 확인합니다.
- **목표에 도달하지 못함**: 너무 짧은 `--steps`나 `--linear 0`으로 실행했는지 확인하세요. Custom/Differential은 목표 정지 모드가 아닙니다.
- **재생을 다시 시작한 결과가 섞임**: 이 코드에서는 실행 중 Stop/Play로 초기화하기보다 프로그램을 다시 실행해 같은 초기 조건을 만드세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)에 대응합니다. 직접 제어기와 공식 제어기, 목표 위치 제어의 관계를 독립 Python 실행으로 비교합니다. 모드 선택과 위치 JSON은 이 폴더의 학습용 구성입니다.

현재 `tutorial.json`은 `not_run`입니다. 이번 개정에서는 로컬 코드와 설치된 5.1 `WheelBasePoseController`의 회전·전진·정지 분기를 대조했습니다. 바퀴 목표 계산과 도착 기준은 실행 결과를 읽을 기준이며, Jetbot 주행을 새로 실행해 확인한 기록은 아닙니다.
