# 88. VS Code에서 필요한 구성 요소를 골라 확장 만들기

## 이번에 배우는 것

**같은 생성기에서 Python 확장과 빌드가 필요한 확장을 만들고, 선택한 기능마다 확인해야 할 결과를 연결합니다.**

확장에 UI가 있다고 반드시 C++ 코드가 필요한 것은 아닙니다. 반대로 API나 계산 노드만 있는 확장은 별도 창이 없어도 정상입니다. VS Code 생성기는 이런 구성 요소를 골라 출발 코드를 만듭니다.

| 구성 요소 | Python | C++ | 사용자가 확인할 동작 |
|---|---|---|---|
| Extension / API | 가능 | 가능 | 활성화와 공개 함수 호출 |
| OmniGraph | 가능 | 가능 | 노드의 실제 입력 → 출력 |
| Pybind | 해당 없음 | 가능 | C++ 기능을 Python에서 호출 |
| UI | 가능 | 생성 대상 아님 | 메뉴에서 창 열기와 버튼 동작 |
| Tests | 가능 | 가능 | 생성된 테스트의 수집과 실행 |

**Ready-to-use**는 생성한 Python 확장을 별도 native 빌드 없이 불러오는 경로입니다. C++를 포함하면 소스가 실행 바이너리가 되도록 Kit 빌드 환경을 거쳐야 합니다.

## 1. Python 확장을 생성하고 불러오기

Isaac Sim 5.1 GUI, 지원 NVIDIA GPU, VS Code와 **Isaac Sim VS Code Edition** 확장(`NVIDIA.isaacsim-vscode-edition`)이 필요합니다. 저장소 루트에서 출력 폴더를 준비하세요.

```bash
mkdir -p src/88_tools_vscode_extension_template_generator/output/extensions
realpath src/88_tools_vscode_extension_template_generator/output/extensions
~/isaacsim/isaac-sim.sh
```

1. VS Code의 Isaac Sim 아이콘에서 **Templates > Extension**을 엽니다.
2. Ext. name은 `kr.advanced.lesson`, Ext. path는 위 출력 폴더의 절대 경로로 정합니다.
3. **Ready-to-use extension**을 켜고 Python의 Extension, API, OmniGraph, UI, Tests를 선택한 뒤 Create합니다.
4. 생성된 폴더의 `config/extension.toml`과 Python 모듈·테스트를 엽니다.
5. Isaac Sim의 **Window > Extensions > Settings > Extension Search Paths**에 부모 `output/extensions` 절대 경로를 추가합니다.
6. `kr.advanced.lesson`을 활성화하고 생성된 Window 메뉴의 창을 엽니다.

### 설정에서 볼 부분

Ext. path에는 확장들을 담을 부모 폴더를 입력합니다. 생성 후에는 그 아래의 `kr.advanced.lesson`이 확장 하나입니다. `extension.toml`의 `[[python.module]]`은 앱이 불러올 Python 모듈을 가리킵니다.

이 저장소에 포함된 `kr.advanced.starter`를 열어보면 이 연결을 작게 확인할 수 있습니다.

```toml
[[python.module]]
name = "kr_advanced_starter"
```

`kr_advanced_starter/__init__.py`에서는 시작 시 UI를 만들고 클릭 함수를 연결합니다.

```python
ui.Button("Create Cube", clicked_fn=self.create_cube)
```

이 starter는 `kr.advanced.lesson`과 다른 확장입니다. 생성물의 복잡한 구성을 읽기 전에 모듈과 UI 연결만 실행해 보려면 별도의 앱에서 다음을 사용하세요.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/88_tools_vscode_extension_template_generator/exts" \
  --enable kr.advanced.starter
```

Create Cube는 `/World/ExtensionCube`에 Size 0.3, Translate Z 0.5를 작성합니다. 강체 설정이 없어 Play해도 그대로 떠 있습니다. disable하면 창만 사라지고 prim은 남습니다.

### 실행 결과 확인하기

생성한 `kr.advanced.lesson`에서는 다음을 각각 확인하세요.

- UI 메뉴를 열고 버튼의 callback이 실제 호출되는지 봅니다.
- Action Graph에서 생성된 Python 노드를 검색합니다. 정확한 이름과 포트는 생성된 `.ogn`에 있습니다. 구현의 계산식을 읽은 뒤 입력을 바꾸고 필요한 실행 신호를 연결해 출력을 비교하세요.
- API만 선택해 별도 생성했다면 창이 없는 것이 정상입니다. 생성된 모듈의 공개 함수를 확인해야 합니다.

Python tests는 생성 코드를 읽어 어떤 동작과 값을 검사하는지 먼저 확인한 후, 저장소 루트에서 다음으로 실행합니다.

```bash
~/isaacsim/kit/kit --empty --enable omni.kit.test \
  --/exts/omni.kit.test/runTestsAndQuit=true \
  --/exts/omni.kit.test/testExts/0=kr.advanced.lesson \
  --ext-folder "$PWD/src/88_tools_vscode_extension_template_generator/output/extensions" \
  --no-window
```

테스트 출력에서 **해당 확장의 테스트 이름, 실행 개수와 실패 여부**를 확인하세요. 테스트가 하나도 수집되지 않은 종료는 선택한 기능을 검사한 결과가 아닙니다.

## 2. C++ 구성 요소를 생성하고 빌드하기

이 경로에는 x86_64 Linux 또는 Windows의 C++ 도구와 의존성 다운로드 환경이 추가로 필요합니다. 아래는 Linux 명령입니다. 별도 출력 폴더에 [Isaac Sim App Template v5.1.0](https://github.com/isaac-sim/isaacsim-app-template/tree/6c344c155b823ce3f5797fd21bc24fb8d90f5e11)을 준비합니다.

```bash
git clone --branch v5.1.0 \
  https://github.com/isaac-sim/isaacsim-app-template.git \
  src/88_tools_vscode_extension_template_generator/output/app-template
cd src/88_tools_vscode_extension_template_generator/output/app-template
./repo.sh build
./_build/linux-x86_64/release/isaacsim.exp.full.kit.sh
```

기본 앱이 열리는지 확인하고 닫으세요. 이후 이 절의 빌드 명령은 **app-template 루트**에서 실행합니다. 같은 터미널에서 생성 소스의 부모 폴더를 준비하고 절대 경로를 확인하세요.

```bash
mkdir -p source/extensions
realpath source/extensions
```

1. wizard에서 이름을 `kr.native.lesson`, 경로를 방금 준비한 `app-template/source/extensions` 절대 경로로 정합니다.
2. Ready-to-use를 끕니다. C++ Extension/API/OmniGraph/Pybind/Tests와 Python UI를 선택합니다.
3. 생성한 파일을 확인한 뒤 다음 의존성을 추가합니다.

### 설정에서 볼 부분

`tools/deps/kit-sdk-deps.packman.xml`의 기존 all-deps `<import>` 안에 다음 필터를 추가합니다. 이미 있으면 중복 작성하지 마세요.

```xml
<filter include="usd-${config}"/>
<filter include="doctest"/>
```

같은 파일의 import 바깥에는 다음 dependency가 필요합니다.

```xml
<dependency name="usd-${config}" linkPath="../../_build/target-deps/usd/${config}"/>
<dependency name="doctest" linkPath="../../_build/target-deps/doctest"/>
```

고정한 v5.1.0 template에는 doctest 필터와 버전을 지정한 dependency가 이미 들어 있습니다. 기존 doctest 블록과 package 버전은 유지하고, 누락된 USD 항목만 추가하세요. 위 예시는 필요한 연결을 보여주며 기존 파일 전체를 대체하는 내용이 아닙니다.

USD 의존성은 OmniGraph 구성의 빌드에, doctest는 C++ 테스트에 사용됩니다. 파일을 생성했다고 컴파일러가 해당 헤더와 라이브러리를 자동으로 찾는 것은 아니므로 빌드 의존성을 연결합니다.

```bash
./repo.sh build
./_build/linux-x86_64/release/isaacsim.exp.full.kit.sh
```

빌드한 앱에서 `kr.native.lesson`을 켜세요. 별도 Isaac Sim 설치에 연결할 때에는 생성 소스 폴더가 아닌 **빌드 결과의 확장 폴더를 담은 경로**를 Search Paths로 지정합니다.

### 실행 결과 확인하기

생성된 Python 모듈이 `kr.native.lesson`이고 공개 API 이름이 아래와 같다면 Script Editor에서 다음을 실행합니다. 실제 생성 파일에서 이름을 먼저 확인하세요.

```python
import kr.native.lesson as lesson

interface = lesson.acquire_extension_interface()
try:
    lesson.set_default_status("local lesson")
    interface.register_object(10)
finally:
    lesson.release_extension_interface()
```

이 호출은 Python에서 native API로 들어가는 연결을 확인합니다. 이어 생성된 C++ 노드도 그래프에서 실제 평가하고, 앱을 닫은 뒤 다음으로 테스트합니다.

```bash
./_build/linux-x86_64/release/tests-kr.native.lesson.sh
```

컴파일 완료, 앱의 plugin 로드, Python API 호출, 그래프 계산, 테스트 통과는 서로 다른 관찰 결과입니다. 어느 단계까지 확인했는지 나누어 기록하세요.

## 3. 생성물과 실행 경로 정리

```text
Python Ready-to-use
wizard → Python 모듈·설정 → Search Path → Enabled → 기능 실행

C++ 포함
wizard → C++/OGN/Python 소스 → 의존성 구성 → 빌드
       → plugin과 생성 코드 → host에서 로드 → 기능·테스트 실행
```

**선택한 구성 요소가 확인 방법을 결정합니다.** UI는 창과 callback으로, OGN은 포트 계산으로, Pybind는 Python 호출로 확인합니다. 모두 선택했다면 확장 활성화 한 번으로 검사를 끝내지 마세요.

## 4. 간단한 확인 실험

제공 starter의 `config/extension.toml`에서 **package의 `title`만 `Korean Advanced Starter`로** 바꾸세요. 파일을 저장하고 확장을 다시 불러옵니다.

확장 관리자에 표시되는 제목은 달라지지만 생성된 창 제목은 계속 `Korean Extension Starter`입니다. 창 제목은 Python의 `ui.Window("Korean Extension Starter", ...)`에 별도로 쓰여 있기 때문입니다. 확장 ID `kr.advanced.starter`도 그대로 유지됩니다. 이 비교로 설정의 표시 이름, 활성화할 확장 ID, UI가 자체적으로 정한 창 제목을 구분할 수 있습니다.

## 실행할 때 막히면

- **wizard 결과가 검색되지 않음:** Ext. path로 사용한 부모 폴더가 Search Paths에 있는지 확인하세요.
- **C++ 파일은 있는데 native plugin이 없음:** Ready-to-use 설정과 빌드 로그를 확인하세요. native 경로는 `repo.sh build`가 필요합니다.
- **USD/doctest 헤더를 찾지 못함:** 기존 all-deps import 안의 필터와 바깥 dependency를 함께 확인하세요.
- **테스트가 0개로 끝남:** 생성 때 Tests를 선택했는지, 테스트 명령의 확장 이름과 경로가 맞는지 확인하세요.
- **starter 두 번째 클릭 오류:** 기존 `ExtensionCube`가 남아 있습니다. 새 Stage에서 반복하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Advanced Extension Template Generator from VS Code](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/vscode_extension_template_generator.html)에 대응합니다. wizard와 native 준비 순서를 다루며, 로컬 starter는 Python UI와 USD 작성만 제공합니다.

이번 개정에서는 로컬 설정·코드와 공식 생성 절차를 대조했습니다. VS Code wizard 실행, 외부 의존성 설치, C++ 빌드, Kit 로드와 생성 테스트는 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
