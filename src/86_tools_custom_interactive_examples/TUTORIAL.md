# 86. 나만의 낙하 실험을 Examples Browser에 등록하기

## 이번에 배우는 것

**큐브 낙하 장면을 Examples Browser 항목으로 만들고, 등록·Load·Play·Reset이 각각 언제 실행되는지 확인합니다.**

한 번 만든 실험을 다시 찾고 초기화하기 쉽게 만들려면 장면 코드와 실행 UI를 연결해야 합니다. 여기서는 `BaseSample`이 장면을 맡고 `BaseSampleUITemplate`이 Load와 Reset UI를 제공합니다. 확장을 활성화하면 브라우저에 항목이 생기고, 그 항목에서 Load를 눌러야 장면이 만들어집니다.

| 구성 | 역할 | 이 실습의 이름 |
|---|---|---|
| 확장 | 예제 등록과 해제 | `kr.browser.example` |
| Browser 항목 | 사용자가 여는 진입점 | Korean Examples > Korean Falling Cube |
| `FallingCubeSample` | 바닥과 동적 큐브 생성 | `/World/LearningCube` |
| `BaseSampleUITemplate` | 비동기 Load/Reset 처리 | 예제 패널의 버튼 |
| 출력 | 초기화 직후 위치 확인 | `loaded pose:`, `reset pose:` |

초록 큐브는 한 변이 0.25 m이고 중심 높이 1.5 m에서 시작합니다. `DynamicCuboid`가 강체와 충돌 설정을 포함하므로 Play하면 바닥으로 떨어집니다.

## 1. Examples Browser에서 실험 열기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 외부 로봇 USD 없이 기본 도형만 사용합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/86_tools_custom_interactive_examples/exts" \
  --enable kr.browser.example
```

1. **Window > Examples > Robotics Examples**를 엽니다.
2. **Korean Examples > Korean Falling Cube**를 선택합니다.
3. **Load**를 누릅니다. 보관할 장면은 Load 전에 저장하세요.
4. Stage에서 `/World/LearningCube`를 선택하고 `F`로 화면에 맞춥니다.
5. 왼쪽 타임라인의 **Play**를 누른 뒤 큐브 낙하를 관찰합니다.
6. 예제 패널의 **Reset**을 눌러 시작 상태로 돌아오는지 확인합니다.

앱은 관찰이 끝나도 계속 열려 있습니다. 다음 절의 등록 해제를 확인한 뒤 창을 닫으세요.

### 실행 결과 확인하기

| 시점 | 화면 또는 출력의 기대값 |
|---|---|
| 확장 활성화 직후 | Browser 항목이 나타남 |
| Load 완료 | 바닥과 초록 큐브, `loaded pose:` 뒤 위치 `[0, 0, 1.5]` |
| Play 후 | 큐브가 떨어져 바닥에 머묾 |
| 충분히 안정된 뒤 | 중심 높이가 약 0.125 m |
| Reset 후 | `reset pose:` 뒤 시작 위치, 큐브 높이 약 1.5 m |

바닥에 놓인 중심 높이 0.125 m는 `0.25/2`에서 나온 값입니다. 접촉 여유나 물리 계산 때문에 마지막 숫자가 정확히 같지는 않을 수 있습니다. 이 예제는 CSV를 기록하지 않으므로 화면과 Console의 초기화 출력을 나누어 읽으세요.

## 2. 장면 코드와 Browser 등록 따라가기

`exts/kr.browser.example/kr_browser_example/__init__.py`에 장면과 확장 코드가 함께 들어 있습니다.

### 코드에서 볼 부분

장면은 `setup_scene()`에서 World에 추가합니다.

```python
world.scene.add(DynamicCuboid(
    prim_path="/World/LearningCube",
    name="learning_cube",
    position=np.array([0.0, 0.0, 1.5]),
    size=0.25,
    color=np.array([0.2, 0.7, 0.3]),
))
```

`prim_path`는 USD 장면 경로이고 `name`은 World의 scene에서 객체를 찾는 이름입니다. 둘을 같은 문자열로 생각하면 나중에 조회 위치를 혼동할 수 있습니다. 초기화 뒤에는 scene 이름으로 객체를 가져옵니다.

```python
async def setup_post_load(self):
    self.cube = self.get_world().scene.get_object("learning_cube")
    print("loaded pose:", self.cube.get_world_pose()[0])
```

`setup_scene`에서 장면을 작성한 다음 물리 초기화가 진행되고, `setup_post_load`에서 준비된 큐브를 조회합니다. `get_world_pose()` 결과의 `[0]`은 위치 벡터입니다. Reset 뒤에도 같은 객체에서 위치를 읽어 초기 상태 복원을 확인합니다.

브라우저 연결은 다음 코드가 맡습니다.

```python
get_browser_instance().register_example(
    name=self.name, category=self.category,
    execute_entrypoint=self.ui.build_window,
    ui_hook=self.ui.build_ui,
)
```

`execute_entrypoint`와 `ui_hook`에는 UI를 만드는 함수를 전달합니다. **등록하면서 낙하 실험을 곧바로 실행하는 구조가 아닙니다.** 사용자의 예제 선택과 Load가 뒤따라야 합니다.

`config/extension.toml`의 `isaacsim.examples.interactive`, `isaacsim.examples.browser`, `isaacsim.core.api` 의존성은 이 UI와 장면 API를 불러올 수 있게 합니다.

### 실행 결과 확인하기

**Window > Extensions**에서 `kr.browser.example`을 끄세요. 다음 코드가 같은 이름과 카테고리의 Browser 항목을 해제합니다.

```python
get_browser_instance().deregister_example(
    name=self.name, category=self.category,
)
```

다시 켰을 때 항목이 하나만 생기는지 확인합니다. 확장 종료 코드에는 Stage의 큐브를 직접 삭제하는 동작이 없습니다. Browser 항목이 없어졌는지와 기존 장면에 큐브가 남았는지를 별도로 관찰하세요.

## 3. 예제의 수명 정리

```text
확장 켜기 → Browser에 이름 등록
예제 선택 → UI 만들기
Load → setup_scene → reset으로 객체 초기화 → Pause → setup_post_load
Play → 앱의 물리 진행 → 큐브 낙하
Reset → 초기 상태 복원 → setup_post_reset
확장 끄기 → Browser 등록 해제
```

**예제 등록은 실험으로 들어갈 입구를 만들고, Load와 Reset은 반복해서 실행할 상태를 준비합니다.** 이 구분을 유지하면 장면 코드에 메뉴 처리를 섞지 않고도 다른 물체나 로봇 실험을 추가할 수 있습니다.

## 4. 간단한 확인 실험

`position=np.array([0.0, 0.0, 1.5])`에서 **높이 1.5만 2.5로** 바꾸세요. 파일을 저장하고 확장을 껐다 켠 뒤 Load합니다.

- `loaded pose:`의 Z가 2.5인지 확인합니다.
- Play하면 더 높은 곳에서 낙하합니다.
- 바닥에 놓인 최종 중심 높이는 큐브 크기가 같으므로 여전히 약 0.125 m입니다.
- Reset 출력은 새 시작 높이 2.5를 가리켜야 합니다.

시작 높이가 바뀌었다고 최종 높이까지 달라지는 것은 아닙니다. **Load/Reset 출력은 초기 조건을, 착지 모습은 크기와 접촉을 확인하는 지점**입니다.

## 실행할 때 막히면

- **Browser에 항목이 없음:** `--ext-folder`가 이 튜토리얼의 `exts`를 가리키는지, 확장 의존성 로드 오류가 없는지 확인하세요.
- **항목은 있지만 큐브가 없음:** 예제 선택 뒤 Load를 눌렀는지 확인하세요. 활성화만으로 장면을 만들지 않습니다.
- **큐브가 떨어지지 않음:** 타임라인 Play 상태를 확인하세요. Load 뒤 정지된 화면은 낙하 실패의 증거가 아닙니다.
- **코드를 바꿨는데 Reset 높이가 예전 값임:** 모듈을 다시 불러오고 Load하여 장면을 새로 만드세요. 이미 만들어진 객체의 기본 위치는 소스 편집만으로 바뀌지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Custom Interactive Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html)에 대응합니다. 공식 문서의 BaseSample·Browser 연결을 사용하며, 설치된 `user_examples`를 수정하는 대신 로컬 확장 폴더에 낙하 예제를 구성했습니다.

이번 개정에서는 확장 설정과 장면·등록·초기화 코드를 대조했습니다. Browser 표시, 물리 낙하와 Reset의 GUI 결과는 실행하지 않았으며 `tutorial.json`의 검증 상태는 `not_run`입니다.
