# 85. Load와 Run 사이에는 어떤 준비가 필요한가?

## 이번에 배우는 것

**확장 템플릿의 버튼을 따라가며 물리 객체 초기화, 반복 콜백, 순차 스크립트의 실행 시점을 구분합니다.**

로봇 prim이 Stage에 보인다고 관절을 바로 제어할 수 있는 것은 아닙니다. USD는 장면의 구성을 담고, 물리 엔진은 초기화 과정에서 움직임을 계산할 객체를 준비합니다. 템플릿의 Load와 Reset은 이 순서를 UI에 연결합니다.

| 살펴볼 대상 | 담당하는 일 | 관찰 지점 |
|---|---|---|
| Loaded Scenario의 Load/Reset | 장면과 물리 객체 준비 | post-load/post-reset의 위치 |
| Run/Stop StateButton | 시나리오 갱신 구독과 해제 | 반복 콜백 출력 |
| Scripting의 generator | 여러 동작을 순서대로 진행 | `yield` 사이의 실제 관절 이동 |
| `bounded_wait.py` | 목표 도착을 제한 횟수 안에 검사 | 허용 오차와 `TimeoutError` |
| `kr.lifecycle.starter` | 간단한 창의 시작과 종료 | 버튼 클릭과 창 정리 |

여기서는 **언제 사용할 수 있는 상태가 되었는지**를 중심으로 읽습니다. 같은 콜백이라도 창을 열 때 한 번 부르는 함수와 물리 단계마다 부르는 함수의 역할은 다릅니다.

## 1. 생성한 템플릿의 버튼과 콜백 연결하기

Isaac Sim 5.1 GUI, 지원 NVIDIA GPU, 기본 로봇 자산에 접근할 수 있는 환경이 필요합니다. 저장소 루트에서 실행하세요.

```bash
mkdir -p src/85_tools_extension_templates_tutorial/output/extensions
realpath src/85_tools_extension_templates_tutorial/output/extensions
~/isaacsim/isaac-sim.sh
```

1. `isaacsim.examples.extension`을 켜고 **Utilities > Generate Extension Templates**를 엽니다.
2. **Loaded Scenario**를 선택합니다. 위 절대 경로를 부모로 하여 Extension Path를 `<출력 경로>/kr.lifecycle.loaded`, 이름을 `kr.lifecycle.loaded`로 정하고 생성합니다.
3. **Scripting**은 같은 부모 아래 `kr.lifecycle.scripted`로 생성합니다. 이어 **Configuration Tooling**은 `kr.lifecycle.configuration`, **UI Component Library**는 `kr.lifecycle.components`로 각각 다른 폴더에 생성합니다.
4. **Window > Extensions > Settings > Extension Search Paths**에 부모 `<출력 경로>`를 추가합니다.
5. 먼저 `kr.lifecycle.loaded`만 켜고 생성된 창을 엽니다. Load가 새 Stage를 만들므로 보관할 작업은 미리 저장하세요.

### 코드에서 볼 부분

생성된 `output/extensions/kr.lifecycle.loaded/kr_lifecycle_loaded_python/ui_builder.py`에서 다음 연결을 찾으세요. 로컬 5.1 생성기는 확장 이름의 점을 밑줄로 바꾸고 `_python`을 붙인 폴더에 코드를 넣습니다.

```python
LoadButton(
    "Load Button", "LOAD",
    setup_scene_fn=self._setup_scene,
    setup_post_load_fn=self._setup_scenario,
)
```

`_setup_scene`은 로봇과 물체를 만들고 `world.scene.add(...)`로 World에 등록합니다. 초기화가 끝난 뒤 `_setup_scenario`가 실행됩니다. 후자의 시점에는 초기화된 물리 객체를 사용할 수 있고 타임라인은 시작 시점에서 일시정지되어 있습니다.

생성한 파일의 `_setup_scene`, `_setup_scenario`, `_on_post_reset_btn` 함수 본문에 각각 함수명 출력 한 줄을 추가해 보세요. 설치 원본 대신 **output에 생성한 파일**을 수정합니다. 이어 `_update_scenario`에는 `print("scenario step", step)`을 넣으세요.

Run 버튼은 다음 세 연결을 사용합니다.

```python
on_a_click_fn=self._on_run_scenario_a_text,
on_b_click_fn=self._on_run_scenario_b_text,
physics_callback_fn=self._update_scenario,
```

Run을 누르면 타임라인을 재생하고 물리 단계별 갱신을 구독합니다. Stop을 누르면 구독을 해제하고 이 템플릿에서는 타임라인도 Pause합니다. `step`은 이번 물리 단계의 시간 간격이며 초 단위입니다.

### 실행 결과 확인하기

| 누른 버튼 | 출력과 화면에서 볼 내용 |
|---|---|
| Load | scene 준비 → scenario 준비 순서, 로봇과 물체가 나타남 |
| Run | `scenario step`이 반복되고 관절과 큐브가 움직임 |
| Stop | 시나리오 콜백 출력과 움직임이 멈춤 |
| Reset | post-reset 출력 후 시나리오를 다시 시작할 준비가 됨 |

Reset은 World에 등록한 객체의 기본 상태 복원과 시나리오 내부 상태 초기화를 연결합니다. 버튼 글자가 Run으로 돌아온 것만 보지 말고 실제 물체 위치와 재실행을 함께 확인하세요. 타임라인 왼쪽의 Stop을 직접 누르는 경우에는 물리 상태가 해제될 수 있어 템플릿이 Run을 비활성화합니다. 다시 Load/Reset으로 필요한 상태를 준비하세요.

### 창·Stage·확장 종료에서 구독 정리 확인하기

같은 생성 파일의 `on_timeline_event`, `on_stage_event`, `cleanup`에도 함수명 출력 한 줄을 넣고 확장을 다시 불러오세요. `extension.py`가 Stage와 타임라인의 이벤트를 받아 이 함수들로 전달합니다. `cleanup()`은 감싼 UI 요소의 `cleanup()`을 호출하여 StateButton 등의 구독을 정리합니다.

1. Load → Run 뒤 창을 닫아 반복한 `scenario step` 출력이 멈추는지 봅니다. 창을 닫을 때도 UI 정리가 필요합니다.
2. 창을 다시 열고 Load → Run한 뒤 File > New로 Stage를 바꿉니다. 새 Stage에는 이전 로봇의 handle을 쓸 수 없으므로 템플릿이 실행 버튼을 비활성화하는지 확인하세요.
3. 다시 준비해 Run한 뒤 확장을 끕니다. `cleanup` 출력과 반복 콜백 중단을 함께 확인합니다. 물체가 Stage에 남는 것과 콜백 구독이 남는 것은 서로 다른 문제입니다.

이 진단 출력은 호출 순서를 확인하기 위한 임시 편집입니다. 관찰을 마치면 생성한 파일에서 추가한 출력만 제거하세요.

## 2. 기다리는 동안에도 로봇이 움직이게 하기

Loaded Scenario를 끄고 `kr.lifecycle.scripted`를 켭니다. Load → Run으로 기본 시퀀스를 먼저 관찰한 뒤 생성된 `output/extensions/kr.lifecycle.scripted/kr_lifecycle_scripted_python/scenario.py`를 여세요.

### 코드에서 볼 부분

시나리오는 generator를 만들고 물리 단계마다 다음 위치까지 진행합니다.

```python
self._script_generator = self.my_script()
```

```python
result = next(self._script_generator)
```

`my_script()` 안의 `yield from`은 하위 동작이 끝날 때까지 기다렸다가 다음 줄로 이어집니다. 하위 함수의 `yield`는 실행 위치를 기억한 채 Kit에 제어권을 돌려줍니다. 그 사이 앱이 물리를 진행하므로 다음 검사에서 관절 위치가 달라질 수 있습니다.

제공 `bounded_wait.py`는 이 대기를 다음처럼 제한합니다.

```python
for _ in range(max_steps):
    actual = articulation.get_joint_positions()[indices]
    if np.allclose(actual, target, atol=tolerance, rtol=0):
        return True
    yield
raise TimeoutError("Articulation did not reach the target within max_steps")
```

`rtol=0`이므로 각 관절의 `|현재값 - 목표값|`이 `tolerance` 이내인지 검사합니다. 함수는 명령을 보내지 않습니다. 목표를 지정한 뒤 호출해야 합니다.

실제로 연결하려면 `bounded_wait.py`의 함수 전체를 생성된 `scenario.py`의 클래스 바깥에 복사하세요. `open_gripper_franka`의 **관절 명령 전송 부분은 유지**하고, 기존 `while` 대기와 마지막 반환을 다음으로 교체합니다.

```python
return (yield from wait_for_target(
    articulation, [7, 8], [0.04, 0.04],
    tolerance=0.001, max_steps=300,
))
```

이 인덱스는 기본 Franka의 두 손가락 관절에 맞춘 값입니다. 다른 로봇에서는 관절 이름과 인덱스를 다시 확인해야 합니다. 손가락 이동이 미터 단위인 이 예제에서 0.001은 1 mm의 허용 오차입니다.

### 실행 결과 확인하기

저장 후 확장을 다시 불러오고 Load → Run을 수행하세요. 손가락이 목표에 도착하면 다음 동작으로 이어지며, 대기 중에도 GUI가 응답해야 합니다.

300은 **위치 검사 횟수**입니다. 호출자가 물리 단계마다 한 번 진행하고 간격이 1/60초라면 약 5초의 시뮬레이션 진행에 해당하지만 실제 시계로 잰 제한 시간은 아닙니다. 도착하지 못하면 오류가 발생합니다. 이 예외를 생성 템플릿이 자동 복구하는 코드는 제공하지 않으므로 Stop 후 목표와 상태를 확인하세요.

로컬 `kr.lifecycle.starter`의 창 수명만 따로 비교하고 싶다면 앞의 앱을 종료하고 다음을 실행할 수 있습니다.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/85_tools_extension_templates_tutorial/exts" \
  --enable kr.lifecycle.starter
```

이 starter의 Create Cube는 `/World/ExtensionCube`를 만들고 disable은 창만 지웁니다. 위 로봇 대기 함수는 starter에 연결되어 있지 않습니다.

### Configuration과 UI Component의 값 전달 비교하기

Scripting을 끄고 새 Stage에서 `kr.lifecycle.configuration`을 켜세요. Content의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 추가하고 Play한 뒤 **Select Articulation**에서 로봇을 고릅니다. 생성된 `kr_lifecycle_configuration_python/ui_builder.py`에서 다음 연결을 찾으세요.

```python
lambda value, index=i: self._on_set_joint_position_target(index, value)
```

`index=i`는 필드를 만들 당시의 관절 번호를 보관합니다. 관절 목표 필드 하나를 허용 범위 안에서 조금 바꾸고, 그 번호의 관절이 움직이는지 확인하세요. 타임라인 Stop 후 제어 UI가 비활성화되고 Play·재선택으로 다시 준비되는지도 봅니다. Configuration은 장면을 직접 만드는 Load 대신 현재 장면의 선택과 물리 초기화 상태에 의존합니다.

이어서 `kr.lifecycle.components`의 창을 열고 Float Field와 Check Box를 각각 바꿉니다. 생성된 `kr_lifecycle_components_python/ui_builder.py`의 `_on_float_field_value_changed_fn(new_value: float)`와 `_on_checkbox_click_fn(value: bool)`는 받은 값을 상태 표시 필드에 씁니다. **필드 표시 변경 → 콜백 인수 → 상태 메시지 갱신**을 대조하세요. 이 UI 예제는 관절 명령을 보내지 않으므로 숫자를 바꿨다고 로봇이 움직이지는 않습니다.

## 3. 상태와 실행 시점 정리

```text
Load → 장면 작성 → 물리 초기화 → Pause → post-load
Run  → Play → 물리 콜백 → generator의 다음 yield까지 진행
Stop → 시나리오 구독 해제 → Pause
Reset → 기본 물리 상태 복원 → 시나리오 상태 초기화
```

**초기화 콜백은 사용할 수 있는 상태를 마련하고, 물리 콜백은 시간이 흐를 때 할 일을 정합니다.** 도착을 기다리는 루프에도 `yield`가 있어야 물리가 진행되어 기다리는 조건 자체가 바뀔 수 있습니다.

Configuration은 준비된 장면의 관절에 값을 전달하고, Component Library는 상태 메시지로 입력값을 보여 줍니다. 같은 숫자 필드라도 연결한 콜백의 내용에 따라 결과가 달라집니다.

## 4. 간단한 확인 실험

Configuration/UI 비교를 끝냈다면 두 확장을 끄고 Scripting을 다시 켜 Load하여 같은 로봇 시나리오로 돌아오세요. 앞에서 연결한 `wait_for_target` 호출의 **`tolerance=0.001`만 `0.01`로** 바꾸세요. 같은 시작 상태에서 다시 Load → Run하고 손가락 다음 동작으로 넘어가는 시점을 비교합니다.

허용 오차가 1 mm에서 10 mm로 넓어져 목표에 덜 가까워도 완료로 판단할 수 있습니다. 목표 위치 0.04와 검사 한도 300은 유지하세요. 눈으로 차이가 작다면 두 실행에서 대기 종료 직전의 실제 관절 위치를 출력해 비교하면 됩니다.

## 실행할 때 막히면

- **`bounded_wait.py`만 실행했는데 아무 일도 없음:** 함수 정의만 있는 파일입니다. 생성 시나리오에서 명령을 보낸 뒤 `yield from`으로 호출하세요.
- **Run 출력이 너무 많음:** `_update_scenario`는 매 물리 단계 호출됩니다. 호출 순서를 확인한 뒤 추가한 진단 출력을 제거하세요.
- **대기 중 화면까지 멈춤:** 위치 검사 루프에 `yield`가 있는지 확인하세요. 이벤트 루프를 점유하면 관절도 목표로 이동하지 못합니다.
- **`TimeoutError` 발생:** 타임라인 재생 상태, 실제 관절 인덱스, 도달 가능한 목표와 접촉 방해 여부를 확인하세요. 대기 시간을 늘리기 전에 실제 위치가 변하는지 보세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Extension Template Generator Explained](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_templates_tutorial.html)에 대응합니다. 버튼 이름과 callback 연결은 로컬 5.1의 Loaded Scenario·Scripting 템플릿 소스와 대조했습니다.

`bounded_wait.py`는 제한 횟수가 있는 도착 검사를 익히는 로컬 보조 함수입니다. 자동 연결이나 예외 복구까지 구현하지 않습니다. 이번 개정은 소스·설정 검토이며 GUI 로봇 동작과 도착 검사는 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
