# 13. 색 변경을 실행하고 Undo로 되돌리기

## 이번에 배우는 것

**큐브를 파랗게 만드는 Action을 호출하고, 그 안의 Command가 색을 어떻게 되돌리는지 확인합니다.**

버튼을 누르는 것처럼 이름으로 기능을 실행하고 싶을 때는 **Action**을 등록할 수 있습니다. 편집을 취소하고 다시 적용하려면 **Command**의 Undo·Redo 동작이 필요합니다. 이 예제에서는 `make_blue` Action 안에서 `ChangeProperty` Command를 실행해 두 역할을 연결합니다.

| 구성 | 이번 실습에서 하는 일 |
|---|---|
| `CreateMeshPrimCommand` | 큐브를 만들고 실제 생성 경로 반환 |
| `make_blue` Action | 이름으로 호출할 색 변경 함수 |
| `ChangeProperty` Command | 이전 색을 보관하면서 새 색 적용 |
| `command_history.json` | 빨강 → 파랑 → 빨강 → 파랑의 실제 속성 기록 |
| `commands.usda` | 마지막 파란 큐브가 담긴 장면 |

등록된 Action은 실행 중인 Python 앱의 기능입니다. USD 파일에는 큐브의 최종 상태가 저장되며, Action 등록까지 함께 저장되지는 않습니다.

## 1. 먼저 자동 Undo·Redo 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음 명령을 실행하세요. 설치 경로가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/13_python_usd_omniverse_tools/run.py --steps 120
```

네 번의 색 읽기와 결과 저장을 먼저 수행한 뒤 앱 업데이트 120회를 진행하고 종료합니다. 창을 열어 둘 때는 `--steps 120`을 빼세요. `--headless`를 추가하면 창 없이 실행하며, 단계 수를 생략한 Headless 실행은 120회 후 종료합니다.

결과는 이 폴더의 `output/날짜-시간/`에 저장됩니다. `--output`을 사용하면 존재하지 않는 새 폴더를 지정해야 합니다.

### 코드에서 볼 부분

Action이 호출하는 함수는 다음과 같습니다.

```python
def make_blue():
    success, _ = omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=color.GetPath(),
        value=[Gf.Vec3f(0, 0, 1)],
        prev=color.Get(),
    )
```

- `prop_path`: 생성된 큐브의 `primvars:displayColor` 속성 경로입니다.
- `value`: 적용할 파랑 RGB입니다. 색 성분은 0~1 범위를 사용합니다.
- `prev`: 호출하는 순간 읽은 이전 색입니다. Undo에서 복원할 값입니다.

`prev`에 빨강 상수를 넣는 대신 `color.Get()`을 사용하므로, 호출 전에 다른 색을 설정해도 그 색으로 돌아갈 수 있습니다. 최초 빨강은 직접 USD 속성에 작성하고, 이후 색 변경은 Command로 수행합니다.

### 실행 결과 확인하기

`command_history.json`에서 다음 네 항목을 읽어보세요.

| 항목 | 확인할 RGB | 의미 |
|---|---|---|
| `before` | `[1, 0, 0]` | Action 호출 전 빨강 |
| `after_action` | `[0, 0, 1]` | Action이 적용한 파랑 |
| `after_undo` | `[1, 0, 0]` | Command가 이전 색 복원 |
| `after_redo` | `[0, 0, 1]` | 같은 변경을 다시 적용 |

코드는 매 단계에서 USD 속성을 다시 읽으며, 이 순서와 다르면 오류를 냅니다. 화면 갱신 반복문은 이 과정 뒤에 시작하므로 **화면에는 최종 파란 큐브만 보일 수 있습니다.** 중간 변화는 JSON으로 확인하세요.

`prim_path`에는 생성 명령이 실제로 반환한 경로가 기록됩니다. 항상 `/World/Cube`라고 가정하지 말고 이 값으로 Stage에서 큐브를 찾으세요.

## 2. 실행 중인 앱에서 Action 찾아보기

앞의 실행이 끝났다면 `--steps` 없이 다시 실행합니다.

```bash
~/isaacsim/python.sh src/13_python_usd_omniverse_tools/run.py
```

1. 해당 앱 창에서 **Window > Commands**를 엽니다.
2. **Search Commands**로 `CreateMeshPrimCommand`와 `ChangeProperty`를 찾아 매개변수를 살펴봅니다.
3. **Utilities > Registered Actions**에서 `tutorial.commands.local`의 `make_blue`를 찾습니다.
4. 이름과 설명을 읽은 뒤 Action 이름을 더블클릭해 실행합니다. 이미 파란 상태이므로 바로 눈에 띄는 변화가 없을 수 있습니다.

메뉴가 보이지 않으면 **Window > Extensions**에서 Commands 창은 `omni.kit.window.commands`, Action 목록은 `omni.kit.actions.window`를 활성화하세요. 현재 `run.py`가 실행 중인 창에서 켜야 등록된 `make_blue`를 찾을 수 있습니다.

### 코드에서 볼 부분

```python
registry.register_action(extension_id, action_id, make_blue)
omni.kit.actions.core.execute_action(extension_id, action_id)
omni.kit.undo.undo()
omni.kit.undo.redo()
```

`extension_id`는 `tutorial.commands.local`, `action_id`는 `make_blue`입니다. 두 식별자가 어떤 기능을 호출할지 정합니다. Action이 호출되면 Python 함수가 실행되고, 그 함수가 Command를 실행합니다.

앱 관찰을 마치면 `finally`에서 다음 정리를 수행합니다.

```python
registry.deregister_action(extension_id, action_id)
```

등록한 기능의 사용 기간이 끝났기 때문에 해제합니다. 저장한 `commands.usda`를 다른 Isaac Sim 창에서 여는 것만으로 Action이 다시 나타나지는 않습니다.

### 실행 결과 확인하기

Registered Actions 목록은 **지금 `run.py`가 실행 중인 앱 창**에서 확인하세요. 별도로 켠 다른 Isaac Sim 창은 별도 등록 목록을 가집니다.

자동 실행 후에 GUI에서 추가로 색을 바꾸거나 Action을 호출해도 이미 저장된 JSON은 갱신되지 않습니다. 수동 변경 결과를 남기려면 화면과 Property 값을 확인하고 장면을 새 이름으로 저장합니다.

## 3. Action과 Command의 역할 정리

```text
make_blue라는 이름으로 호출
    → 등록된 Python 함수 실행
    → ChangeProperty가 현재 색을 보관하고 파랑 적용
    → Undo는 보관한 색, Redo는 파랑 복원
```

**Action에 이름을 붙였다고 Undo가 자동으로 생기지는 않습니다.** 이 실습에서 되돌리기가 가능한 이유는 함수 안에서 이전 값을 전달하는 Command를 사용했기 때문입니다. 직접 `color.Set(...)`으로 값을 쓴 모든 작업이 같은 편집 이력을 남긴다고 생각하면 안 됩니다.

## 4. 간단한 확인 실험

창이 열린 상태에서 **Action 호출 전의 색만** 초록으로 바꿔보세요.

1. JSON의 `prim_path`에 해당하는 큐브를 선택하고 Property에서 Display Color를 초록으로 바꿉니다.
2. Registered Actions에서 `make_blue`를 실행합니다. 큐브가 파랗게 바뀌는지 봅니다.
3. Undo를 한 번 실행합니다. 이번에는 빨강이 아니라 **호출 직전의 초록**으로 돌아오는지 확인합니다.

이 실험은 `prev=color.Get()`이 고정된 기본색이 아닌 현재 값을 저장한다는 점을 확인합니다. 자동 검사 코드를 바꿀 필요는 없습니다.

## 실행할 때 막히면

- **`CreateMeshPrimCommand failed`**: **Window > Extensions**에서 mesh primitive 관련 확장이 활성화되어 있는지 확인하세요. 큐브 생성이 실패하면 뒤의 색 변경도 진행할 수 없습니다.
- **Action 목록에 `make_blue`가 없음**: `--steps`로 이미 종료했거나 다른 앱 창을 보고 있는지 확인하세요.
- **Action을 실행해도 색이 그대로임**: 현재 색이 이미 파랑이면 정상입니다. 확인 실험처럼 시작 색을 바꾸어 보세요.
- **Undo가 생각한 작업을 되돌리지 않음**: 그사이에 실행한 GUI 편집도 이력에 들어갈 수 있습니다. 색 변경 직후 다른 편집 없이 Undo를 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Commands](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/omniverse_tools.html)에 대응합니다. 등록된 Action에서 색 변경 Command를 실행하는 작은 장면으로 실행·Undo·Redo를 비교합니다.

현재 `tutorial.json`의 검증 상태는 `not_run`입니다. 이번 개정에서는 등록·해제 흐름, 속성 검사와 출력 항목을 코드로 대조했습니다. JSON 기대값과 GUI 관찰은 실제 실행에서 확인할 기준이며, 실행 성공 기록을 뜻하지 않습니다.
