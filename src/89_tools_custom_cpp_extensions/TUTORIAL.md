# 89. C++ 확장의 시작과 종료를 직접 확인하기

## 이번에 배우는 것

**C++ 소스를 native plugin으로 빌드하고, 확장을 켜고 끌 때 실제 함수가 호출되는지 로그로 확인합니다.**

Python 확장은 모듈을 불러오지만 C++ 확장은 먼저 컴파일한 바이너리를 불러옵니다. 여기서는 장면이나 로봇 대신 시작·종료 메시지만 출력합니다. 덕분에 빌드 결과가 실제 앱까지 연결되었는지에 집중할 수 있습니다.

| 구성 | 어디에 있는가 | 역할 |
|---|---|---|
| `HelloWorldExtension.cpp` | 이 튜토리얼 폴더 | 시작·종료 동작 구현 |
| `premake5.lua` | 외부 C++ template의 예제 폴더 | 컴파일 대상과 소스 연결 |
| `config/extension.toml` | 같은 외부 예제 폴더 | 앱이 찾을 plugin 경로 선언 |
| `_build/.../release/exts` | template 빌드 결과 | 앱에 등록할 확장 묶음 |
| Console/터미널 | 실행 중인 앱 | `started`와 `stopped` 관찰 |

제공 C++ 파일은 단독 실행 프로그램이 아닙니다. `main()` 대신 Kit가 호출할 확장 인터페이스를 구현하며, 외부 template의 빌드 구조를 사용합니다.

## 1. 고정된 template에 소스를 넣고 빌드하기

Linux x86_64의 Git·C++ 빌드 도구와 의존성을 내려받을 인터넷·디스크 공간이 필요합니다. Isaac Sim에 통합하려면 지원 NVIDIA GPU와 5.1 설치도 준비하세요. Windows에서는 template의 `build.bat`와 해당 C++ 도구를 사용합니다.

아래는 **저장소 루트**에서 시작하는 Linux 명령입니다. 경로 변수가 다음 단계에도 쓰이므로 같은 터미널에서 이어서 실행하세요.

```bash
lesson_dir="$PWD/src/89_tools_custom_cpp_extensions"
mkdir -p "$lesson_dir/output"
git clone https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp.git \
  "$lesson_dir/output/cpp-template"
cd "$lesson_dir/output/cpp-template"
git checkout e8b660c96183f4a35f12f5ff75e37756ae6aee3b
./build.sh package
```

이 실습은 [고정한 template 커밋](https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp/tree/e8b660c96183f4a35f12f5ff75e37756ae6aee3b)의 파일 배치를 사용합니다. 최신 branch의 SDK나 파일 구조를 섞지 마세요.

최초 빌드는 원래 예제를 준비합니다. 이제 같은 터미널에서 로컬 구현을 적용하고 다시 빌드하세요.

```bash
cpp_target="source/extensions/omni.example.cpp.hello_world/plugins/omni.example.cpp.hello_world/HelloWorldExtension.cpp"
cp "$cpp_target" "$lesson_dir/output/HelloWorldExtension.original.cpp"
cp "$lesson_dir/HelloWorldExtension.cpp" "$cpp_target"
./build.sh
./_build/linux-x86_64/release/omni.app.example.extension_browser.sh
```

처음 수행할 때는 출력 폴더를 새로 사용하세요. 재실행할 때 원본 백업에 수정본을 덮어쓰지 않도록 확인합니다.

### 설정에서 볼 부분

외부 예제의 `premake5.lua`에는 plugin target과 C++ 소스 폴더의 연결이 있습니다.

```lua
project_ext_plugin(ext, "omni.example.cpp.hello_world.plugin")
```

`config/extension.toml`은 빌드한 plugin을 앱에 알려줍니다.

```toml
[[native.plugin]]
path = "bin/*.plugin"
```

따라서 확장 검색 경로에는 원본 C++ 파일만 있는 위치가 아니라, `config`와 `bin`을 포함한 **빌드 결과의 확장들**이 필요합니다.

### 실행 결과 확인하기

template 앱의 **Window > Extensions**에서 `omni.example.cpp.hello_world`를 찾아 켜세요.

```text
Korean C++ extension started: <실제 확장 ID>
```

끄면 다음 메시지가 나타나야 합니다.

```text
Korean C++ extension stopped
```

다시 켜서 startup 메시지가 한 번 더 나오는지 보세요. 이 예제는 USD prim이나 창을 만들지 않으므로 화면의 도형 대신 **Enabled 전환과 로그의 대응**을 관찰합니다.

## 2. 같은 plugin을 Isaac Sim에 연결하기

template 앱을 종료합니다. 앞의 터미널에서는 `lesson_dir`가 그대로 유지됩니다.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$lesson_dir/output/cpp-template/_build/linux-x86_64/release/exts" \
  --enable omni.example.cpp.hello_world
```

Isaac Sim의 확장 관리자에서 같은 enable/disable을 반복합니다. template 앱에서 동작해도 Isaac Sim의 라이브러리와 바이너리 인터페이스가 맞는지는 이 단계에서 확인해야 합니다.

### 코드에서 볼 부분

로컬 `HelloWorldExtension.cpp`의 핵심은 다음과 같습니다.

```cpp
class ExampleCppHelloWorldExtension : public omni::ext::IExt {
public:
    void onStartup(const char* extId) override {
        std::printf("Korean C++ extension started: %s\n", extId);
    }
    void onShutdown() override {
        std::printf("Korean C++ extension stopped\n");
    }
};
```

`override`는 기반 인터페이스의 함수를 구현한다는 표시입니다. `extId`는 앱이 전달하는 실제 확장 식별자이므로 파일 이름만 추측하는 대신 로그에서 어떤 확장이 시작되었는지 읽을 수 있습니다.

`carb::PluginImplDesc`에는 plugin 이름과 설명이 들어가고, `CARB_PLUGIN_IMPL(...)`이 이 구현을 Carbonite plugin으로 노출합니다. 로컬 파일의 plugin ID와 namespace를 template의 target에 맞춘 이유가 여기에 있습니다. 파일 한 곳의 이름만 바꾸면 설정이 찾는 대상과 구현이 제공하는 대상이 달라질 수 있습니다.

### 실행 결과 확인하기

다음 세 가지를 나누어 확인하세요.

| 단계 | 근거 |
|---|---|
| 컴파일·링크 | 로컬 C++ 적용 뒤의 빌드 로그와 결과 파일 |
| template 앱 로드 | 첫 앱의 startup/shutdown 메시지 |
| Isaac Sim 통합 | Isaac Sim에서의 startup/shutdown 메시지 |

이 예제는 시작 함수에서 반복 작업을 등록하지 않습니다. 이후 물리나 업데이트 callback을 추가한다면 종료 함수에서 해당 구독도 해제해야 합니다. 앱이 확장을 껐는데 코드가 계속 호출되는 상태를 만들지 않기 위한 연결입니다.

## 3. 소스에서 실행 함수까지 정리

```text
C++ 소스 → premake target → 컴파일·링크 → native plugin
                                          ↓
extension.toml → 앱의 확장 활성화 → onStartup(extId)
                            비활성화 → onShutdown()
```

**바이너리가 만들어졌다는 사실과 앱이 그 바이너리를 불러왔다는 사실은 다릅니다.** 이 실습의 로그는 후자를 확인하는 가장 작은 관찰 지점입니다.

자신의 새 확장으로 발전시킬 때에는 폴더 이름, 설정, premake target, plugin ID와 C++ namespace를 함께 정리하세요. 이 실습은 연결을 배우기 위해 원래 예제 이름을 유지합니다. 사용자 확장 이름은 `kr.cpp.lesson`처럼 고유한 접두사를 사용합니다.

## 4. 간단한 확인 실험

template에 복사한 C++ 파일의 startup 문자열에서 **`started`만 `started v2`로** 바꾸세요. 앱을 닫고 template 루트에서 `./build.sh`를 다시 실행한 뒤 같은 host를 재시작합니다.

새 startup 문자열이 보이고 shutdown 문자열은 그대로여야 합니다. 소스만 저장한 뒤 앱에서 이전 메시지가 나온다면 컴파일한 파일과 앱이 불러오는 `_build` 경로를 비교하세요. 이 실험은 새 바이너리까지 변경이 전달되었는지 확인합니다.

## 실행할 때 막히면

- **컴파일러나 SDK 다운로드 오류:** 최초 빌드의 첫 오류부터 확인하세요. 로컬 C++ 적용 전부터 실패했다면 template 환경 준비 단계의 문제입니다.
- **빌드했는데 확장이 검색되지 않음:** `--ext-folder`가 `_build/linux-x86_64/release/exts`인지 확인하세요.
- **확장은 보이지만 startup 로그가 없음:** native plugin 로드 오류와 의존성을 확인하세요. Enabled 표시와 실제 함수 호출을 함께 봅니다.
- **template에서는 되지만 Isaac Sim에서 로드 실패:** host의 SDK·ABI 호환성 문제일 수 있습니다. 오류에 나온 라이브러리나 symbol을 기록하고 Isaac Sim 통합은 미확인으로 남기세요.
- **재빌드해도 예전 문자열:** 실행 중인 앱을 종료했는지, 다른 복제본의 확장을 불러오는지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Custom Extensions: C++](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_cpp_extensions.html)에 대응합니다. 외부 빌드 배치는 [고정 template의 Hello World 설정](https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp/blob/e8b660c96183f4a35f12f5ff75e37756ae6aee3b/source/extensions/omni.example.cpp.hello_world/config/extension.toml)과 premake 소스로 대조했습니다.

로컬 구현은 시작·종료 로그만 제공합니다. 이번 개정에서 C++ 컴파일이나 두 host의 plugin 로드는 실행하지 않았으며 `tutorial.json`의 검증 상태는 `not_run`입니다.
