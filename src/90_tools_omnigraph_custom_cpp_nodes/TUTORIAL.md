# 90. C++ 계산 노드를 빌드하고 그래프에서 평가하기

## 이번에 배우는 것

**양수 판정 노드를 C++로 빌드하고, 노드 선언에서 생성된 접근 함수가 그래프의 실제 입출력으로 이어지는지 확인합니다.**

계산은 `value > 0`으로 단순하지만, C++에서는 `.ogn` 선언을 읽어 만든 Database 헤더와 native plugin이 추가로 필요합니다. 소스 파일을 확장 폴더에 두는 단계만으로 실행 준비가 끝나지 않습니다.

| 구성 | 역할 | 이 실습의 이름 |
|---|---|---|
| `OgnExampleNode.ogn` | 입력·출력 타입과 노드 선언 | `ExampleNode` |
| `OgnExampleNode.cpp` | 비교 계산 구현 | `compute` |
| 생성 헤더 | 선언한 포트의 C++ 접근 함수 제공 | `OgnExampleNodeDatabase.h` |
| template 확장 | 빌드 결과 로드와 등록 | `omni.example.cpp.omnigraph_node` |
| 그래프 출력 | 비교 결과 확인 | `positive` |

이 노드에는 `execIn` 포트가 없습니다. 이번에는 **Push Graph를 명시적으로 평가**하여 계산이 실행된 다음 결과를 읽습니다.

## 1. 노드 소스를 template에 적용하기

Linux x86_64의 C++ 도구, Git과 SDK 의존성 다운로드 환경이 필요합니다. Isaac Sim에 불러오려면 지원 GPU와 5.1 GUI도 준비하세요. 아래는 저장소 루트에서 시작하는 명령입니다.

```bash
lesson_dir="$PWD/src/90_tools_omnigraph_custom_cpp_nodes"
mkdir -p "$lesson_dir/output"
git clone https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp.git \
  "$lesson_dir/output/cpp-template"
cd "$lesson_dir/output/cpp-template"
git checkout e8b660c96183f4a35f12f5ff75e37756ae6aee3b
./build.sh package
```

[고정 template](https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp/tree/e8b660c96183f4a35f12f5ff75e37756ae6aee3b)의 초기 빌드가 끝나면 제공된 두 파일을 적용합니다. 같은 터미널에서 이어서 실행하세요.

```bash
nodes_dir="source/extensions/omni.example.cpp.omnigraph_node/plugins/nodes"
mkdir -p "$lesson_dir/output/original_nodes"
cp "$nodes_dir/OgnExampleNode.cpp" "$nodes_dir/OgnExampleNode.ogn" \
  "$lesson_dir/output/original_nodes/"
cp "$lesson_dir/OgnExampleNode.cpp" "$lesson_dir/OgnExampleNode.ogn" "$nodes_dir/"
./build.sh
./_build/linux-x86_64/release/omni.app.example.viewport.sh
```

새 출력 폴더에서 시작하고, 반복할 때에는 원본 백업을 보존하세요. Windows에서는 대응 `build.bat`와 `_build/windows-x86_64` 경로를 사용합니다.

### 코드에서 볼 부분

선언의 입력은 `double`, 출력은 `bool`입니다.

```json
"inputs": {
  "value": {
    "type": "double",
    "default": 0.0,
    "description": "Number to compare"
  }
}
```

출력 이름 `positive`는 다음 C++ 계산에 그대로 연결됩니다.

```cpp
static bool compute(OgnExampleNodeDatabase& db) {
    db.outputs.positive() = db.inputs.value() > 0.0;
    return true;
}
```

Python의 속성 접근과 달리 C++에서는 `value()`와 `positive()` 같은 **생성된 접근 함수**를 사용합니다. `.ogn`을 바꾸면 이 함수가 들어 있는 헤더도 달라지므로 다시 빌드해야 합니다. `OgnExampleNodeDatabase.h`를 손으로 작성하거나 수정하지 마세요.

### 설정에서 볼 부분

template의 `premake5.lua`는 OGN 생성 작업을 C++ 컴파일보다 앞에 둡니다. `project_ext_ogn(...)`이 노드 선언을 처리하고, plugin target에 `plugins/nodes`와 OGN 의존성을 연결합니다. `REGISTER_OGN_NODE()`는 빌드한 노드 타입의 등록·해제 정보를 제공합니다.

빌드 로그에서 OGN 처리와 C++ 컴파일·링크를 구분해 보세요. 헤더가 없다는 오류가 나면 C++ 문법보다 먼저 `.ogn` 처리 단계가 성공했는지 확인해야 합니다.

## 2. 입력을 바꾸고 평가한 다음 출력 읽기

template 앱의 **Window > Extensions**에서 `omni.example.cpp.omnigraph_node`를 켭니다. Graph 편집기에서는 **Korean Positive Cpp**라는 표시 이름으로 찾을 수 있습니다. 아래 절차는 **Window > Script Editor**에서 실행합니다. 최소 template 앱에 이 메뉴가 없다면 확장 관리자에서 `omni.kit.window.script_editor`를 켜세요. Graph 편집기 없이도 아래 코드로 그래프를 만들고 평가할 수 있습니다.

새 Stage를 준비한 뒤 다음 코드로 Push Graph와 노드 하나를 만듭니다.

```python
import omni.graph.core as og

graph, _, _, _ = og.Controller.edit(
    {"graph_path": "/CppCheck", "evaluator_name": "push"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("positive", "omni.example.cpp.omnigraph_node.ExampleNode")
        ],
        og.Controller.Keys.SET_VALUES: [
            ("positive.inputs:value", 2.0)
        ],
    },
)
```

표시 이름과 타입 이름은 다릅니다. 생성할 때 쓰는 전체 타입 이름은 확장 경로와 선언의 `ExampleNode`를 연결한 문자열입니다.

### 코드에서 볼 부분

생성한 그래프에서 값을 바꾸고 평가한 다음 읽습니다.

```python
input_attr = og.Controller.attribute("/CppCheck/positive.inputs:value")
output_attr = og.Controller.attribute("/CppCheck/positive.outputs:positive")

for value in (-1.0, 0.0, 2.0):
    og.Controller.set(input_attr, value)
    og.Controller.evaluate_sync(graph)
    print(value, output_attr.get())
```

`evaluate_sync` 다음에 출력을 읽는 순서를 확인하세요. 노드가 존재한다는 사실과 이번 입력으로 계산했다는 사실을 구분하기 위한 코드입니다. 같은 Stage에서 첫 그래프 생성 코드를 반복하지 말고 두 번째 값 변경 코드만 실행하세요.

### 실행 결과 확인하기

```text
-1.0 False
0.0 False
2.0 True
```

0은 양수가 아니므로 False입니다. 이때 C++ `compute`는 `true`를 반환합니다. 출력 `positive`는 수학적 판정이고 함수 반환값은 계산 성공 여부이므로 모순되지 않습니다.

template 앱을 닫은 다음 같은 터미널에서 Isaac Sim을 실행합니다.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$lesson_dir/output/cpp-template/_build/linux-x86_64/release/exts" \
  --enable omni.example.cpp.omnigraph_node
```

새 Stage에서 위 생성·평가 코드를 다시 실행하여 세 결과를 확인하세요. template 빌드와 Isaac Sim host의 native 로드는 각각 확인해야 합니다. Script Editor의 관찰이 끝나면 앱을 닫습니다.

## 3. 선언·빌드·평가의 연결 정리

```text
.ogn 포트 선언 → Database 헤더 생성 ─┐
                                    ├→ plugin 빌드 → 확장 로드
.cpp의 compute + REGISTER_OGN_NODE ─┘                 ↓
값 설정 → graph 평가 → compute 실행 → positive 출력 읽기
```

**입력과 출력의 이름은 선언에서 시작해 생성 헤더와 그래프 속성까지 이어집니다.** 이 이름을 일관되게 유지해야 C++ 계산이 기대한 포트를 읽고 쓸 수 있습니다.

이번 노드는 숫자만 계산합니다. 로봇이나 USD 도형을 만드는 기능은 없으므로 장면의 움직임 대신 출력 세 값이 확인 기준입니다.

## 4. 간단한 확인 실험

template에 복사한 `OgnExampleNode.cpp`의 **`> 0.0`을 `>= 0.0`으로** 바꾸세요. 앱을 종료하고 재빌드한 뒤 새 앱에서 세 입력을 평가합니다.

- -1: 계속 False
- 0: **True로 변경**
- 2: 계속 True

연산자 하나가 바뀌었는지 확인하는 데에는 0이 가장 유용한 입력입니다. 실험 후 원래 비교식으로 되돌리세요. 새 의미를 유지하려면 `.ogn`의 설명도 음이 아닌 수의 판정에 맞춰 변경해야 합니다.

## 실행할 때 막히면

- **`OgnExampleNodeDatabase.h`를 찾지 못함:** 두 파일을 같은 nodes 경로에 복사했는지와 OGN 생성 단계 오류를 확인하세요.
- **노드 타입을 찾지 못함:** 확장 Enabled 상태와 plugin 로드 로그를 확인하세요. 검색 표시 이름과 생성 코드의 전체 타입 이름도 구분합니다.
- **입력만 바꿨는데 결과가 그대로임:** `evaluate_sync(graph)`를 실행한 뒤 출력 속성을 읽으세요.
- **Isaac Sim에서만 plugin 로드 실패:** SDK·ABI·확장 의존성 오류를 확인하세요. template 앱의 성공으로 host 통합까지 확인된 것은 아닙니다.
- **기존 `/CppCheck` 관련 오류:** 새 Stage에서 생성 코드부터 시작하거나 이미 만든 그래프에는 값 변경 코드만 실행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Custom C++ Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_cpp_nodes.html)에 대응합니다. 빌드 연결은 [고정 template의 OmniGraph premake 파일](https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp/blob/e8b660c96183f4a35f12f5ff75e37756ae6aee3b/source/extensions/omni.example.cpp.omnigraph_node/premake5.lua)과 대조했습니다.

제공 파일은 원래 예제 노드를 작은 양수 판정으로 바꿉니다. 이번 개정에서는 선언·계산식·빌드 경로를 검토했으며 외부 빌드와 두 host에서의 그래프 실행은 하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
