# 88. Advanced Extension Template Generator from VS Code

권장 학습 순서 **88** · OmniGraph와 확장 개발 · 출처 ID `t167`

VS Code의 생성 wizard에서 Python ready-to-use 확장과 Kit build가 필요한 C++/Python 확장을 각각 만든다. 즉시 열어볼 수 있는 독립 UI starter도 포함한다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 준비와 ready-to-use 생성

1. VS Code Extensions에서 **Isaac Sim VS Code Edition**(`NVIDIA.isaacsim-vscode-edition`)을 설치하고 Activity Bar의 Isaac Sim 아이콘→**Templates > Extension**을 연다.
2. Ext. name=`kr.advanced.lesson`, Ext. path=`/absolute/path/to/this-package/output/extensions`, **Ready-to-use extension=On**, components는 **Extension, API, OmniGraph, UI, Tests**를 선택해 Create한다.
3. Isaac Sim `Window > Extensions` 메뉴→Settings→Extension Search Paths에 위 **부모 output/extensions**를 추가한다. Third Party에서 생성한 확장을 Enabled로 한다.
4. `Window > ...`의 생성 UI를 열고 버튼을 조작한다. Action Graph에서 생성된 Python OGN 노드를 이름으로 검색해 넣고 schema 입력/출력을 바꾸어 확인한다. API만 생성한 경우 창이 없는 것이 정상이다.
5. 테스트는 생성된 Python tests를 읽어 기대값을 확인한 뒤 다음처럼 실행한다. 실제 확장명과 경로를 맞춘다.

```bash
"$ISAAC_SIM_PATH/kit/kit" --empty --enable omni.kit.test --/exts/omni.kit.test/runTestsAndQuit=true --/exts/omni.kit.test/testExts/0=kr.advanced.lesson --ext-folder /absolute/path/to/this-package/output/extensions --no-window
```

## build가 필요한 생성물

1. [Isaac Sim App Template v5.1.0](https://github.com/isaac-sim/isaacsim-app-template/tree/6c344c155b823ce3f5797fd21bc24fb8d90f5e11)을 별도 폴더에 고정 버전으로 준비한다. 이 template은 x86_64 Linux/Windows용이며 빌드 의존성을 다운로드한다.

```bash
git clone --branch v5.1.0 https://github.com/isaac-sim/isaacsim-app-template.git /absolute/path/to/this-package/output/app-template
cd /absolute/path/to/this-package/output/app-template
./repo.sh build
./_build/linux-x86_64/release/isaacsim.exp.full.kit.sh
```

확인된 v5.1.0 커밋은 `6c344c155b823ce3f5797fd21bc24fb8d90f5e11`이다. 첫 기본 app 실행을 확인하고 종료한 뒤 생성기를 사용한다.
2. VS Code wizard에서 Ext. name=`kr.native.lesson`, Ext. path=`.../output/app-template/source/extensions`, **Ready-to-use=Off**로 한다. C++ Extension/API/OmniGraph/Pybind/Tests와 필요한 Python UI를 선택한다. C++ UI 생성은 지원 표에 없으므로 Python UI를 사용한다.
3. `tools/deps/kit-sdk-deps.packman.xml`의 기존 all-deps import에 OmniGraph용 `<filter include="usd-${config}"/>`, Tests용 `<filter include="doctest"/>`를 추가한다. import 밖에 대응 dependency를 추가한다.

```xml
<dependency name="usd-${config}" linkPath="../../_build/target-deps/usd/${config}"/>
<dependency name="doctest" linkPath="../../_build/target-deps/doctest"/>
```

4. app template 루트에서 `./repo.sh build`(Windows `repo.bat build`)로 컴파일한다. 빌드 결과의 extension 폴더를 Isaac Sim search path에 추가하고 켠다.
5. C++/Python OGN을 Action Graph에 넣고 Pybind API를 Script Editor에서 호출한다. 생성 API의 실제 모듈에서 `acquire_extension_interface()`, `set_default_status("local lesson")`, `interface.register_object(10)`을 수행하고 `release_extension_interface()`로 해제한다. 생성 이름이 다르면 파일에 정의된 이름을 사용한다.
6. `./_build/linux-x86_64/release/tests-kr.native.lesson.sh`로 생성 tests를 실행한다. 컴파일/테스트 출력과 host 로드 성공은 별도로 기록한다.

## 제공 starter와 개념

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.advanced.starter
```

Create Cube를 누르면 `/World/ExtensionCube`가 생성된다. extension.toml의 module은 Python import, plugin은 native binary 로드 단위다. Pybind는 C++ API를 Python으로 노출하고 OGN은 graph의 typed port/compute를 정의한다. UI/Tests는 추가 component이며 API와 동일한 뜻이 아니다.

한 변수 실험: starter 버튼 callback의 Cube 크기만 바꾸어 reload 결과를 확인한다. 성공은 wizard 생성 파일, 확장 활성화, 실제 UI/OGN/Pybind 호출과 tests 결과다. build prerequisite가 없으면 C++ 파트를 미실행으로 남기며 ready-to-use 실행만으로 C++ 성공을 주장하지 않는다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/vscode_extension_template_generator.html).
