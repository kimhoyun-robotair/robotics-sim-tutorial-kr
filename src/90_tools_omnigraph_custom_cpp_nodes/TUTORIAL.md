# 90. Custom C++ Nodes

권장 학습 순서 **90** · OmniGraph와 확장 개발 · 출처 ID `t108`

Python과 같은 `.ogn` 선언을 C++ compute에 연결하는 native build 실습이다. 제공 두 파일은 외부 template의 ExampleNode를 작고 읽기 쉬운 비교 노드로 바꾼다. 전체 Kit 빌드 시스템을 이 폴더에 위장 구현하지 않는다.

## 이 실습의 의도

입력 숫자가 양수인지 판단하는 최소 계산으로 `.ogn`의 타입 선언, 생성된 Database header, C++ `compute()`와 노드 등록이 연결되는 과정을 배운다. 비교 연산을 단순하게 둔 이유는 계산 알고리즘보다 native 노드의 빌드·등록·평가 경로를 확인하기 위해서다. 이 폴더에는 노드 소스 두 개만 있으므로 외부 template에서 빌드한 뒤 Kit 앱과 Isaac Sim에 직접 로드해야 한다.

## 실행 후 확인할 것

- **생성·빌드:** template 빌드가 `OgnExampleNodeDatabase.h`와 plugin을 생성하는지 확인한다. 제공 `.cpp`를 단독 실행하거나 소스 파일을 복사한 것만으로 노드가 등록되지는 않는다.
- **등록:** extension을 켠 앱의 Action Graph에서 `Korean Positive Cpp`를 찾고 `value` 입력이 double, `positive` 출력이 bool인지 본다.
- **비교 결과:** 아래 Script Editor 평가 예제 또는 consumer가 연결된 graph에서 `value=-1, 0, 2`를 각각 평가하면 `positive=false, false, true`여야 한다. 노드만 배치하고 평가하지 않은 출력은 비교 근거가 아니다.
- **false의 의미:** 입력 0의 `positive=false`는 의도된 경계 결과다. `compute()`의 `return true`는 계산 완료를 뜻하므로 출력 false와 모순되지 않는다.
- **호스트 통합:** template 앱 확인 뒤 Isaac Sim 5.1에서도 같은 노드를 로드하고 비교 결과를 확인한다. template 빌드 성공과 Isaac Sim에서의 binary 로드 성공은 각각 확인한다.

## 고정한 외부 build 환경

원문이 연결하는 C++ template 저장소는 현재 최신 Kit로 바뀔 수 있다. 여기서는 **Kit 107.3.0 업데이트 커밋 `e8b660c96183f4a35f12f5ff75e37756ae6aee3b`**를 고정한다. Linux x86_64에서 Git, C++ build 도구, template dependency 다운로드를 위한 인터넷과 디스크 공간이 필요하다. Windows는 대응 `build.bat`와 Visual Studio C++ toolchain을 사용한다. C++ binary의 Isaac Sim 5.1 호환성은 실제 로드로 최종 확인해야 한다.

```bash
git clone https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp.git /absolute/path/to/this-package/output/cpp-template
cd /absolute/path/to/this-package/output/cpp-template
git checkout e8b660c96183f4a35f12f5ff75e37756ae6aee3b
./build.sh package
```

이 명령은 사용자가 실습 때 수행하며 본 패키지는 의존성을 자동 설치하지 않는다. `_build/linux-x86_64/release/omni.app.example.extension_browser.sh`는 template의 Kit 앱을 연다. Viewport가 필요하면 `omni.app.example.viewport.sh`를 사용한다. `Window > Extensions`에서 `omni.example.cpp`를 검색해 예제를 켠다.

- [고정 template source](https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp/tree/e8b660c96183f4a35f12f5ff75e37756ae6aee3b).
- [원문이 연결하는 C++ template 설명](https://docs.omniverse.nvidia.com/kit/docs/kit-extension-template-cpp/latest/index.html). 최신 문서의 SDK 숫자는 고정한 source와 다를 수 있다.

## 파일 적용과 빌드

1. 위 template의 `source/extensions/omni.example.cpp.omnigraph_node/plugins/nodes/`에 있는 원본 `OgnExampleNode.cpp/.ogn`를 output 아래 별도 backup 폴더에 보관한다.
2. 이 패키지의 같은 이름 파일 두 개를 해당 nodes 디렉터리에 복사한다. 기존 extension.toml/premake5.lua/플러그인 등록 구조를 사용하므로 이름을 임의로 바꾸지 않는다.
3. template 루트에서 `./build.sh`를 다시 실행한다. 빌드가 `.ogn`으로 `OgnExampleNodeDatabase.h`를 생성하고 C++ plugin을 컴파일한다. 생성 header를 수동 작성하지 않는다.
4. template Viewport 앱을 열고 `omni.example.cpp.omnigraph_node`를 Enabled로 한다. Action Graph를 만들어 **Korean Positive Cpp**를 추가한다. 노드 입력 `value`를 -1, 0, 2로 바꾸며 evaluation 후 `positive`가 false,false,true인지 확인한다. 이 노드는 데이터 계산 노드라 consumer 연결/graph 평가가 있어야 계산된다.
5. Python으로 명시적 평가할 때는 Script Editor에서 아래를 실행한다.

```python
import omni.graph.core as og
graph, _, _, _ = og.Controller.edit(
    {"graph_path": "/CppCheck", "evaluator_name": "push"},
    {og.Controller.Keys.CREATE_NODES: [("positive", "omni.example.cpp.omnigraph_node.ExampleNode")],
     og.Controller.Keys.SET_VALUES: [("positive.inputs:value", 2.0)]})
og.Controller.evaluate_sync(graph)
print(og.Controller.attribute("/CppCheck/positive.outputs:positive").get())
```

6. template 앱을 종료한 뒤 Isaac Sim 5.1을 `--ext-folder /absolute/path/to/this-package/output/cpp-template/_build/linux-x86_64/release/exts --enable omni.example.cpp.omnigraph_node`로 시작하여 같은 노드 등록을 확인한다. binary ABI/extension dependency 오류가 나면 성공으로 처리하지 않는다.

## C++/USD 개념

`db.inputs.value()`와 `db.outputs.positive()`는 생성 Database의 typed accessors다. `compute` 반환 true는 계산 완료, 출력 false는 비교 결과다. `REGISTER_OGN_NODE()`는 컴파일된 node type 등록/해제 정보를 연결한다. `.ogn`의 타입을 바꾸면 generated header가 달라지므로 다시 빌드해야 한다. C++ 노드는 USD prim 자체를 만드는 코드가 아니라 graph 평가에 참여하는 계산 코드다.

한 변수 실험: 비교식만 `> 0.0`에서 `>= 0.0`으로 바꾸고 재빌드하여 경계 입력 0을 검사한다. graph에 노드가 없으면 extension Enabled/빌드 target/Console을 확인한다. 이 패키지는 C++ build와 GPU 로드를 실행하지 않았다.

## 검증 범위

제공 `.ogn`과 C++ 비교 구현을 대조했다. 외부 template 빌드와 Kit/Isaac Sim에서의 실제 로드는 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_cpp_nodes.html).
