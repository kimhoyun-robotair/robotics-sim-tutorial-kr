# 24. 큐브를 옮기는 작업과 로봇 제어를 나누기

## 이번에 배우는 것

**Franka의 집기·놓기를 실행하고, 장면을 관리하는 Task와 움직임을 계산하는 Controller의 역할을 구분합니다.**

로봇 팔을 움직이려면 관절 목표가 필요하지만, 그 목표를 계산하기 전에 알아야 할 것이 있습니다. 집을 물체가 어디에 있는지, 어디에 놓을지, 새 실습을 시작할 때 무엇을 초기화할지입니다. 이번에는 이 정보를 `LocalPickTask`에 모으고, `PickPlaceController`가 관찰값을 받아 동작을 계산하게 합니다.

| 구성 | 이 실습에서 맡은 일 |
|---|---|
| `pick_task.py` | Franka·큐브·바닥 생성, 현재 위치와 목표 공개, 색과 그리퍼 초기화 |
| `run.py` | Task 등록, 관찰값을 제어기에 전달, 물리 진행과 결과 저장 |
| `--task custom` | 직접 만든 `LocalPickTask` 사용, 기본 모드 |
| `--task builtin` | Isaac Sim에 포함된 `PickPlace` Task 사용 |

기본 큐브는 한 변이 0.0515 m입니다. 목표 중심 높이 0.02575 m는 그 절반으로, 큐브를 바닥 위에 놓는 위치를 뜻합니다.

## 1. 직접 만든 Task로 집기·놓기 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. Franka 에셋 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`와 설치에 포함된 Franka 예제·Lula/RMPflow 확장을 읽을 수 있어야 합니다. 저장소 루트에서 실행하세요. 설치 경로가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/24_core_core_adding_manipulator/run.py --task custom --steps 1800
```

큐브는 `(0.3, 0.3, 0.3)` m에서 시작해 바닥으로 떨어지고, 로봇은 이를 `(-0.3, -0.3, 0.02575)` m로 옮기려고 합니다. 제어기가 완료되면 최대 실행 길이 안에서 120단계를 더 진행한 뒤 결과를 저장하고 종료합니다. 1800단계가 먼저 끝나면 그때의 부분 결과를 저장합니다.

창을 계속 열어 두려면 `--steps 1800`을 빼세요. 이때 결과를 저장한 뒤에도 물리는 진행되며 창은 남습니다. `--headless`를 추가하면 창 없이 실행하고, 단계 수를 생략한 headless 실행의 상한은 1800단계입니다.

### 코드에서 볼 부분

`run.py`는 Task를 추가하고 `world.reset()`으로 장면과 물리 핸들을 준비합니다. 이후에는 매 반복에서 다음 정보를 연결합니다.

```python
observations = world.get_observations()
robot.apply_action(controller.forward(
    picking_position=observations[cube.name]["position"],
    placing_position=observations[cube.name]["target_position"],
    current_joint_positions=observations[robot.name]["joint_positions"]))
```

`picking_position`은 큐브의 **현재** 위치입니다. 시작 위치를 그대로 넣으면 큐브가 떨어진 뒤에도 공중의 옛 위치를 집으려고 할 수 있습니다. `placing_position`은 Task가 공개한 목표이고, `current_joint_positions`는 현재 팔 자세입니다. 제어기는 이 정보를 받아 관절 동작을 만들며 `world.step()`이 그 명령에 따른 물리를 진행합니다.

### 실행 결과 확인하기

결과는 이 폴더의 `output/<고유번호>/result.json`에 저장됩니다. `--output`으로 경로를 정할 수도 있으며, 이미 있는 폴더는 덮어쓰지 않습니다.

| 필드 또는 화면 | 읽는 방법 |
|---|---|
| `controller_done` | 집기·놓기 제어기의 동작 단계가 끝났는지 확인 |
| `cube_position_m`, `target_m` | 실제 큐브 중심과 목표 중심, 단위 m |
| `cube_target_error_m` | 두 중심 사이의 3차원 거리 |
| `within_3cm` | 최종 거리 `< 0.03` m인지 판정 |
| 파란 큐브가 초록색으로 바뀜 | custom Task에서 목표 3 cm 안에 한 번 들어왔다는 표시 |

**제어기가 끝난 것과 큐브가 목표에 놓인 것은 따로 확인합니다.** 그리퍼가 큐브를 놓쳤어도 동작 단계는 끝날 수 있습니다. 초록색도 달성 이력을 유지하므로, 이후 큐브가 움직였다면 마지막 위치는 JSON으로 판단하세요.

## 2. Task를 바꿔도 같은 제어 흐름을 쓰기

앞 실행이 끝난 뒤 내장 Task로 실행해 보세요.

```bash
~/isaacsim/python.sh src/24_core_core_adding_manipulator/run.py --task builtin --steps 1800
```

두 실행은 같은 객체 조회와 제어 코드를 사용합니다. `get_params()`로 로봇과 큐브의 이름을 얻고, 그 이름으로 Scene 객체와 관찰값을 찾습니다. 따라서 Task 구현이 달라도 필요한 정보의 구조가 맞으면 같은 제어 루프를 쓸 수 있습니다.

### 코드에서 볼 부분

직접 만든 Task의 관찰값은 다음처럼 구성됩니다.

```python
def get_observations(self):
    return {self.cube.name: {"position": self.cube.get_world_pose()[0], "target_position": self.target},
            self.robot.name: {"joint_positions": self.robot.get_joint_positions()}}
```

딕셔너리의 바깥쪽 키는 **누구의 정보인지**, 안쪽 키는 **어떤 정보인지** 나타냅니다. 제어기는 큐브를 어떻게 만들었는지 몰라도 이 값을 읽을 수 있습니다.

`post_reset()`은 그리퍼를 열고, 큐브를 파란색으로 바꾸며, `achieved=False`로 되돌립니다. 새 실습에서 성공 표시가 남지 않도록 물리 상태와 작업 상태를 함께 초기화하는 것입니다. `pre_step()`은 물리 단계 전에 실제 위치 오차를 검사합니다. 이 색 변화 로직은 로컬 custom Task에 있으므로 builtin에서도 같은 색을 성공 기준으로 사용하지 마세요.

## 3. Task와 Controller의 연결 정리

```text
Task: 물체 생성 → 관찰값 제공 → 목표 달성 관찰
                         ↓
Controller: 관찰값 → 집기·놓기 단계 → 관절 동작
                         ↓
World: 물리 진행 → 실제 로봇과 큐브 상태 갱신
```

Task를 바꾸는 일은 작업의 장면과 정보를 바꾸는 일이고, Controller를 바꾸는 일은 그 정보로 움직임을 계산하는 방법을 바꾸는 일입니다. 최종 배치 성공은 **실제 큐브 위치**로 판정합니다.

## 4. 간단한 확인 실험

custom 모드에서 목표의 x좌표만 `-0.3`에서 `-0.25` m로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/24_core_core_adding_manipulator/run.py --task custom --steps 1800 --target -0.25 -0.3 0.02575
```

놓는 위치가 x 방향으로 5 cm 이동해야 합니다. z좌표는 큐브 반높이로 유지했으므로 여전히 바닥 위 목표입니다. 새 `result.json`의 `target_m`이 바뀌었는지 먼저 확인하고, `cube_target_error_m`가 그 새 목표를 기준으로 작은지 비교하세요.

## 실행할 때 막히면

- **Franka가 나타나지 않거나 RMPflow 초기화 오류**: Franka USD와 종속 에셋을 읽을 수 있는지, 5.1의 manipulator 예제·Lula 확장이 로드되는지 콘솔에서 확인하세요.
- **`controller_done=true`인데 큐브가 멀리 있음**: 시간에 따라 진행한 동작이 끝난 상태입니다. 큐브 위치와 그리퍼 접촉을 살펴보고 배치 성공과 구분하세요.
- **결과 파일이 없음**: 완료 전에 창을 닫으면 저장 전에 반환할 수 있습니다. `--steps 1800`으로 끝까지 실행해 보세요.
- **재시작 후 색이나 제어 단계가 이상함**: 이 실행 루프는 GUI Stop/Play로 제어기를 재시작하는 흐름을 제공하지 않습니다. 앱을 종료하고 명령을 다시 실행하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Adding a Manipulator Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html)에 대응합니다. 원문의 Scene·Task·PickPlaceController 연결을 독립 Python 실행으로 구성했고, 두 Task 선택과 최종 오차 기록을 추가했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 2026-09-14의 custom headless 1800단계 실행에서 제어기 완료와 큐브 오차 약 0.00261 m를 확인한 기록이 있습니다. builtin과 변경한 목표까지 검증한 기록은 아닙니다. 이 수치는 당시 실행의 참고값이며 현재 코드의 재검증 결과는 아닙니다.
