# 26. 같은 작업을 여러 벌 배치하려면 무엇을 나눠야 할까?

## 이번에 배우는 것

**Jetbot–Franka 작업을 세 벌 만들고, 좌표·이름·제어 상태를 작업마다 분리하는 방법을 익힙니다.**

25번의 이동·후퇴·집기 흐름을 여러 번 생성하면 로봇 수도 늘어납니다. 하지만 객체 이름이 같으면 관찰값이 덮어써지고, 같은 제어기를 공유하면 한 로봇의 완료 상태가 다른 로봇에도 영향을 줄 수 있습니다. 이번에는 같은 `HandoverTask` 클래스로 서로 구별되는 작업을 만듭니다.

| 나눠야 할 것 | 이 실습의 구성 |
|---|---|
| 공간 | 작업별 y방향 `offset`, 기본 간격 2 m |
| 이름 | `lane_0`·`lane_1`·`lane_2`, 고유한 로봇·큐브 이름 |
| 관찰 | 작업 이름이 포함된 event 키와 객체별 상태 |
| 제어 진행 | lane마다 별도 이동 제어기와 집기 제어기 |
| 결과 | `result.json`에 작업마다 한 항목 |

여기서 lane은 같은 Stage 안에 나란히 배치한 작업 구역입니다. 각각 별도의 물리 세계가 생기는 것은 아닙니다.

## 1. 세 작업을 한 번에 실행하기

Isaac Sim 5.1, 지원 NVIDIA GPU, Jetbot·Franka 에셋과 내장 Lula/RMPflow가 필요합니다. 로봇은 각각 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`, `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 사용합니다.

저장소 루트에서 아래 명령을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/26_core_core_multiple_tasks/run.py --tasks 3 --spacing 2 --seed 7 --steps 2400
```

Franka·Jetbot·큐브가 세 벌 생성됩니다. 각 작업은 Jetbot 이동, 기본 200단계 후퇴, Franka 집기 순서로 진행합니다. 물리 2400단계 후 그때의 상태를 저장하고 종료하므로 아직 진행 중인 작업이 있을 수도 있습니다. 창 없이 실행하려면 `--headless`를 추가하세요. headless의 기본 상한도 2400단계입니다.

### 코드에서 볼 부분

작업 구역의 중심 y좌표는 다음 식으로 만듭니다.

```python
offset=np.array([0.0, (index - (args.tasks-1)/2) * args.spacing, 0.0])
```

세 작업일 때 `index`가 0·1·2이고 중심을 가운데에 맞추므로 offset은 -2·0·2 m입니다. Jetbot과 큐브의 로컬 시작 y는 0.3 m이므로 실제 시작 y는 다음과 같습니다.

| 작업 | y offset | Jetbot·큐브의 시작 y | Franka base의 y |
|---|---:|---:|---:|
| `lane_0` | -2 m | -1.7 m | -2 m |
| `lane_1` | 0 m | 0.3 m | 0 m |
| `lane_2` | 2 m | 2.3 m | 2 m |

위치는 달라도 로봇 사이의 상대 배치는 같은 방식으로 유지됩니다. 각 Jetbot의 목표 x는 `default_rng(seed)`로 1.2~1.6 m에서 뽑습니다. 같은 seed는 같은 목표값을 만들지만, 물리 궤적 전체가 항상 완전히 같다는 뜻은 아닙니다.

### 실행 결과 확인하기

시작 콘솔의 `parameters`에서 lane별 로봇·큐브·Jetbot 이름이 서로 다른지 확인하세요. 이후 출력되는 event 딕셔너리는 각 작업이 `0 DRIVE`, `1 RETREAT`, `2 PICK` 중 어디에 있는지 보여줍니다. 목표 거리가 다르므로 모든 lane이 동시에 전환될 필요는 없습니다.

이 폴더의 `output/<고유번호>/result.json`에는 지정한 작업 수만큼 항목이 생깁니다. 각 항목에서 `task`, `event`, `controller_done`, `cube_target_error_m`, `within_3cm`를 함께 읽으세요. `within_3cm`는 **그 lane의 최종 큐브 중심이 자기 목표에서 3 cm 안에 있는지** 나타냅니다. 한 항목의 성공을 전체 작업의 성공으로 읽지 않습니다.

## 2. 좌표와 제어 상태가 섞이지 않는 이유

`handover_task.py`는 내장 `PickPlace`를 사용해 Franka와 큐브를 만들고 Jetbot을 추가합니다. offset을 적용할 때는 누가 이미 위치를 옮겼는지 구분해야 합니다.

### 코드에서 볼 부분

내장 Task에 offset을 전달하는 부분과, 바깥 Task에 Jetbot을 등록하는 부분을 연결해 읽어 보세요.

```python
self.pick = PickPlace(name=name + "_pick", cube_initial_position=np.array([0.1, 0.3, 0.05]),
                      target_position=np.array([0.7, -0.3, 0.02575]), offset=self._offset)
```

같은 offset을 내장 Task에도 전달하므로 큐브의 시작 위치와 목표가 해당 lane의 좌표로 해석됩니다. 바깥 Task가 직접 옮길 객체는 다음처럼 따로 등록합니다.

```python
self._task_objects[self.jetbot.name] = self.jetbot
self._move_task_objects_to_their_frame()
```

PickPlace가 Franka와 큐브를 이미 자기 작업 좌표로 옮겼으므로, 바깥 Task에서는 Jetbot만 옮깁니다. 같은 물체를 양쪽에 등록하면 offset을 두 번 적용할 수 있습니다. 좌표를 더할 때는 물체 위치뿐 아니라 Jetbot 목표와 큐브 목표에도 같은 기준을 사용합니다.

이름도 두 종류를 나눠 확인합니다. `/World/Jetbot` 같은 Prim 경로는 USD Stage에서 유일해야 하고, `jetbot` 같은 Scene 이름은 관찰값과 객체 검색에 사용됩니다. `find_unique_string_name()`은 각 공간에서 이미 사용 중인 이름을 피합니다.

`run.py`에서는 작업마다 제어기를 새로 만들고 묶어서 저장합니다.

```python
controllers.append((drive, pick))
```

이후 `zip(tasks, controllers)`로 같은 순서의 작업과 제어기를 연결합니다. 매 단계 `observations[task.name + "_event"]`를 읽기 때문에 `lane_0_event`가 바뀌어도 다른 lane의 상태는 그대로입니다.

### 실행 결과 확인하기

GUI를 계속 관찰하려면 앞 명령에서 `--steps 2400`을 빼세요. 모든 집기 제어기가 끝난 뒤 120단계를 더 진행하고 결과를 저장하며, 창과 물리는 계속 유지됩니다. 한 lane이 DRIVE에 머무르면 이 완료 조건도 기다리게 됩니다. 유한 실행 결과는 정해진 길이에서의 측정이라는 차이를 기억하세요.

## 3. 여러 Task를 확장하는 기준 정리

```text
같은 작업 클래스
    ├─ lane_0: offset_0 + 고유 객체 + controller_0 → 결과_0
    ├─ lane_1: offset_1 + 고유 객체 + controller_1 → 결과_1
    └─ lane_2: offset_2 + 고유 객체 + controller_2 → 결과_2
                         ↓
                 하나의 World에서 물리 진행
```

공간 배치는 offset으로, 데이터 구별은 이름으로, 동작 진행은 별도 인스턴스로 관리했습니다. 작업 수를 늘리는 것은 이 세 가지를 함께 늘리는 일입니다. 같은 World를 쓰므로 가까이 놓은 작업끼리는 물리적으로 간섭할 수 있습니다.

## 4. 간단한 확인 실험

`--tasks`만 3에서 2로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/26_core_core_multiple_tasks/run.py --tasks 2 --spacing 2 --seed 7 --steps 2400
```

로봇 쌍과 결과 항목이 둘로 줄어야 합니다. 중심을 맞추는 식 때문에 y offset도 -1·1 m로 바뀝니다. 세 작업 중 하나가 단순히 사라져 -2·0 m에 남는 구성이 아닙니다. 객체 이름의 중복이 없는지, 결과의 `task`가 두 개인지, 각 큐브가 자기 목표와 비교되는지 확인하세요.

## 실행할 때 막히면

- **GPU 메모리가 부족하거나 로딩이 매우 느림**: `--tasks 1`로 한 작업을 먼저 확인하세요. 같은 에셋을 쓰더라도 로봇 수에 따라 물리·렌더링 비용이 증가합니다.
- **`--spacing` 오류**: 코드는 1.5 m 미만을 거부합니다. 기본 2 m로 돌아가 배치부터 확인하세요.
- **한 lane만 끝나지 않음**: 그 lane의 event와 큐브 위치를 확인하세요. Jetbot이 도착했더라도 큐브가 충분히 밀리지 않았을 수 있습니다.
- **로컬 Jetbot을 사용하려는데 Franka 로딩이 실패함**: `--asset`은 Jetbot USD만 지정합니다. Franka와 RMPflow는 기본 5.1 자산·확장 설정을 사용합니다.
- **GUI Stop/Play 후 진행이 맞지 않음**: 이 루프는 제어기까지 재설정하는 GUI 재시작을 구현하지 않습니다. 프로그램을 다시 실행해 동일한 초기 조건으로 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Multiple Tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html)에 대응합니다. Task의 매개변수와 offset을 여러 작업으로 확장하는 개념을 유지하고, 작업 수·간격·난수 seed와 lane별 최종 오차를 로컬 실행 옵션으로 구성했습니다.

`tutorial.json`은 `not_run`입니다. 위 설명은 코드의 생성식과 관찰·결과 구조에 따른 확인 기준입니다. 여러 로봇의 실제 운반·집기 성공과 GUI 배치는 아직 실행 검증하지 않았습니다.
