# 84. 버튼 하나에서 시작하는 확장 만들기

## 이번에 배우는 것

**작은 큐브 생성 확장을 실행한 뒤, 공식 생성기의 네 템플릿이 장면과 사용자 입력을 어떻게 나누어 맡는지 비교합니다.**

Script Editor에서 코드를 매번 붙여 넣는 대신 버튼으로 반복해서 실행하고 싶을 때 확장을 만들 수 있습니다. 확장은 앱이 켜고 끌 수 있는 기능 묶음입니다. 파일을 생성하는 단계, 앱이 확장을 찾는 단계, 사용자가 버튼을 누르는 단계는 각각 별도로 진행됩니다.

| 구성 | 이 실습에서 맡는 역할 | 확인할 결과 |
|---|---|---|
| `kr.template.starter` | 제공된 최소 UI 확장 | 버튼으로 큐브 생성 |
| `config/extension.toml` | 의존성과 불러올 Python 모듈 선언 | 확장 활성화 |
| `kr_template_starter/__init__.py` | 창 생성, 클릭 처리, 창 정리 | 창과 Stage의 서로 다른 수명 |
| 공식 Template Generator | 목적에 맞는 확장 소스 생성 | 네 확장 폴더와 각 실습 창 |

**Stage**는 현재 USD 장면이고, **prim**은 `/World/ExtensionCube`처럼 경로로 식별하는 장면 요소입니다. 확장 창을 닫는 일과 Stage에서 prim을 지우는 일은 서로 다릅니다.

## 1. 제공된 큐브 확장 실행하기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음 명령을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/84_tools_extension_template_generator/exts" \
  --enable kr.template.starter
```

1. **Korean Extension Starter** 창에서 **Create Cube**를 누릅니다.
2. Stage에서 `/World/ExtensionCube`를 선택하고 `F`로 화면 중심에 맞춥니다.
3. Property에서 크기와 Translate Z를 확인합니다.
4. **Window > Extensions**에서 `kr.template.starter`를 끕니다. 창과 큐브 중 무엇이 사라지는지 보세요.

이 실습은 자동으로 앱을 종료하지 않습니다. 확인을 마치면 앱 창을 닫으세요.

### 코드에서 볼 부분

확장 폴더의 `config/extension.toml`에는 다음 연결이 있습니다.

```toml
[[python.module]]
name = "kr_template_starter"
```

앱이 이 모듈을 불러오면 `StarterExtension.on_startup()`이 창을 만들고 버튼의 클릭 함수를 연결합니다.

```python
ui.Button("Create Cube", clicked_fn=self.create_cube)
```

여기서 `self.create_cube` 뒤에 괄호가 없는 이유는 **지금 함수를 실행하는 것이 아니라 클릭할 때 실행할 함수를 전달하기 때문**입니다. 클릭 후에는 다음 코드가 현재 Stage에 값을 씁니다.

```python
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.3)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
```

기본 미터 장면에서는 한 변이 0.3 m이고 중심 높이가 0.5 m인 큐브입니다. 이 코드에는 강체나 충돌 설정이 없어서 Play해도 중력으로 떨어지지 않습니다.

### 실행 결과 확인하기

터미널이나 Console의 `created /World/ExtensionCube` 출력과 Stage의 실제 경로를 함께 확인하세요. 확장을 끄면 `on_shutdown()`에서 `window.destroy()`가 실행되어 창이 사라집니다. 큐브 삭제 코드는 없으므로 큐브는 남습니다. USD 파일도 자동 저장하지 않습니다.

같은 Stage에서 버튼을 두 번 누르면 기존 경로가 있다는 오류가 납니다. 한 번의 클릭이 이미 만든 객체를 덮어쓰지 않도록 한 동작입니다.

## 2. 공식 생성기로 네 가지 확장 만들기

이제 작은 확장에 장면 로드와 실행 제어를 더하려면 어떤 출발점이 필요한지 살펴봅니다. 저장소 루트에서 출력 폴더와 절대 경로를 준비하세요.

```bash
mkdir -p src/84_tools_extension_template_generator/output/extensions
realpath src/84_tools_extension_template_generator/output/extensions
```

Isaac Sim에서 `isaacsim.examples.extension`을 활성화하고 **Utilities > Generate Extension Templates**를 엽니다. 위 명령이 출력한 경로를 아래의 `<출력 경로>` 자리에 사용하세요.

| 펼칠 템플릿 | Extension Name | Extension Path |
|---|---|---|
| Loaded Scenario | `kr.loaded` | `<출력 경로>/kr.loaded` |
| Scripting | `kr.scripted` | `<출력 경로>/kr.scripted` |
| Configuration Tooling | `kr.configuration` | `<출력 경로>/kr.configuration` |
| UI Component Library | `kr.components` | `<출력 경로>/kr.components` |

각 Description을 적고 **Generate Extension**을 누르세요. 확장 관리자의 메뉴에서 **Settings > Extension Search Paths**에 `<출력 경로>`를 추가합니다. 네 폴더를 담은 **부모 경로**를 등록해야 합니다. Third Party에서 각 확장을 찾아 하나씩 켜고 생성된 메뉴를 여세요.

### 설정에서 볼 부분

로컬 5.1 생성기는 확장 이름의 점을 밑줄로 바꾸고 `_python`을 붙인 Python 폴더를 만듭니다. 예를 들어 `kr.loaded`의 코드는 `kr_loaded_python/` 아래에 있습니다. 이 폴더의 `global_variables.py`에는 제목과 설명이, `extension.py`에는 메뉴와 이벤트 연결이, `ui_builder.py`에는 사용자 UI와 동작이 들어 있습니다. 생성된 README를 먼저 읽고 `ui_builder.py`에서 버튼과 콜백을 찾아보세요. 공식 웹 설명의 `scripts/` 표기와 달리 실제 생성물의 모듈 경로를 사용합니다.

제공 starter는 클릭 즉시 USD만 수정하지만 Loaded Scenario의 Load는 물리 객체 초기화까지 준비합니다. Configuration은 사용자가 이미 준비한 장면을 다루므로 로봇을 스스로 넣어야 합니다. 이 차이를 알고 템플릿을 선택하면 필요한 초기화 단계를 빠뜨리지 않을 수 있습니다.

### 실행 결과 확인하기

- **Loaded Scenario:** 보관할 장면을 저장한 뒤 Load → Run → Stop → Reset을 누릅니다. 기본 생성물에서는 UR10e의 관절이 차례로 움직이고 `/Scenario/cuboid`가 원을 그립니다. Stop 뒤 움직임이 멈추고 Reset 뒤 다시 시작할 수 있는지 확인하세요.
- **Scripting:** Load → Run 후 Franka가 목표로 이동하고 gripper를 여닫는 동안 창이 응답하는지 봅니다. 로봇 자산을 읽을 수 있는 5.1 자산 경로가 필요합니다.
- **Configuration:** 새 Stage에 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 추가하고 Play한 뒤 로봇 dropdown을 선택합니다. 관절 필드 하나를 바꾸어 실제 관절의 반응을 보세요.
- **UI Component Library:** 숫자 필드와 체크박스를 바꾸고 버튼을 눌러 생성 코드의 콜백에 전달되는 값과 타입을 확인합니다.

starter의 큐브 버튼을 눌렀다고 이 네 생성물이 실행되는 것은 아닙니다. `output/extensions`의 파일 생성과 각 확장의 실제 실행을 차례로 확인하세요.

## 3. 파일 생성부터 사용자 동작까지 정리

```text
Generate → 확장 소스가 디스크에 생김
Search Path 등록 → 앱이 확장 폴더를 발견함
Enabled → 모듈을 읽고 메뉴·창을 준비함
사용자 클릭 → 연결한 콜백이 USD나 물리를 변경함
Disabled → 확장이 소유한 UI·이벤트를 정리함
```

**템플릿은 시작 구조를 마련합니다. 어떤 버튼에서 장면을 만들고 어떤 시점에 물리를 실행할지는 생성된 코드의 연결을 통해 결정됩니다.**

## 4. 간단한 확인 실험

제공 starter의 `cube.CreateSizeAttr(0.3)`에서 **0.3만 0.6으로** 바꾸세요. 저장 후 확장을 껐다 켜고 **File > New**로 새 Stage를 준비한 다음 Create Cube를 누릅니다.

한 변 길이는 두 배가 되지만 중심 높이는 0.5로 유지됩니다. 기본 미터 장면에서 아래 면 높이는 `0.5 - 0.6/2 = 0.2 m`입니다. 화면 크기와 Property의 Size를 함께 확인하면 새 코드가 실제로 불러와졌는지 알 수 있습니다.

## 실행할 때 막히면

- **확장이 검색되지 않음:** `--ext-folder`나 Search Paths가 `exts/kr.template.starter`가 아닌 `exts`를 가리키는지 확인하세요.
- **두 번째 클릭에서 ExtensionCube exists 오류:** **File > New**로 새 장면을 준비하세요. 확장을 껐다 켜도 기존 큐브는 남습니다.
- **생성물 Load에서 로봇이 보이지 않음:** Console의 USD 자산 경로 오류를 확인하고 5.1 로봇 자산 연결을 준비하세요. starter는 외부 로봇 자산을 사용하지 않습니다.
- **Configuration의 관절 UI가 비활성화됨:** 로봇을 추가한 뒤 Play하고 articulation을 선택하세요. 장면 로드까지 맡는 템플릿이 아닙니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Extension Template Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html)에 대응합니다. 생성물의 이벤트 구조는 [Extension Template Generator Explained](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_templates_tutorial.html)와 로컬 5.1 템플릿 소스로 대조했습니다.

큐브 starter는 이 폴더의 작은 보조 예제입니다. 네 공식 템플릿은 사용자가 GUI로 생성합니다. 문서와 코드·설정의 연결을 검토했으며 GUI 활성화, 로봇 동작과 출력 파일 생성은 이번 개정에서 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
