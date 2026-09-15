# 89. Custom Extensions: C++

권장 학습 순서 **89** · OmniGraph와 확장 개발 · 출처 ID `t166`

C++ extension의 startup/shutdown을 실제 native plugin으로 빌드한다. 로컬 파일은 공식 template의 Hello World 구현을 대체하며 복잡한 observer 없이 extension lifecycle 자체를 학습한다.

## 이 실습의 의도

작은 C++ `omni::ext::IExt` 구현을 공식 template의 plugin target에 넣어, 소스 파일이 native binary가 되고 host의 활성화·비활성화 이벤트를 받는 과정을 확인한다. 출력 메시지만 남기도록 구현해 USD 장면이나 UI와 관계없이 startup/shutdown을 관찰할 수 있게 했다. 제공 `HelloWorldExtension.cpp`만으로 실행 가능한 확장은 아니며, 고정 template 준비·소스 복사·빌드·확장 활성화를 사용자가 수행해야 한다. template Kit 앱에서의 로드와 Isaac Sim 5.1에서의 로드는 각각 확인한다.

## 실행 후 확인할 것

- 고정 template의 `omni.example.cpp.hello_world` source 경로에 제공 파일을 복사했는지 확인하고 빌드 로그에서 해당 target의 컴파일·링크가 성공했는지 본다. 최초 template 빌드와 로컬 파일을 적용한 재빌드를 구분한다.
- template Kit 앱에서 `omni.example.cpp.hello_world`를 활성화할 때 Console/터미널에 `Korean C++ extension started: <실제 ext id>`가 나타나는지 확인한다. `.so`나 `.dll` 파일이 생긴 것만으로는 이 lifecycle이 실행된 것이 아니다.
- 비활성화할 때 `Korean C++ extension stopped`가 한 번 나오고 다시 활성화하면 새 startup 메시지가 나오는지 확인한다. 각 enable/disable 전환과 로그가 대응해야 하며 별도 도형이나 창이 생성되지 않는 것은 의도한 동작이다.
- 같은 빌드의 `_build/.../release/exts` 경로를 Isaac Sim 5.1에 연결하여 동일한 startup/shutdown을 확인한다. template 앱에서 성공했어도 Isaac Sim host의 ABI·dependency·로드 성공까지 자동으로 확인되는 것은 아니다.
- startup 문자열만 바꾼 실험에서는 재빌드·재시작 후 새 문자열이 출력되는지 확인한다. 이전 문자열이 계속 보이면 extension 검색 경로와 실제 로드한 binary를 대조한다.

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

## 실습

1. `source/extensions/omni.example.cpp.hello_world/plugins/omni.example.cpp.hello_world/HelloWorldExtension.cpp` 원본을 output backup에 보관한다.
2. 이 패키지의 `HelloWorldExtension.cpp`를 그 경로에 복사한다. 같은 plugin id/namespace를 유지하여 제공된 `premake5.lua`와 `config/extension.toml`이 그대로 사용된다.
3. template 루트에서 `./build.sh`를 실행한다. `./_build/linux-x86_64/release/omni.app.example.extension_browser.sh`로 Kit 앱을 연다.
4. `Window > Extensions`에서 `omni.example.cpp.hello_world`를 찾아 Enabled를 켠다. Console/터미널에서 `Korean C++ extension started`와 실제 ext id를 확인한다.
5. Enabled를 끄면 `Korean C++ extension stopped`가 한 번 나온다. 다시 켜서 startup/shutdown이 쌍으로 실행되는지 본다.
6. template 앱을 종료하고 Isaac Sim 5.1을 다음 인자로 실행해 같은 활성/비활성을 확인한다.

```bash
"$HOME/isaacsim/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/output/cpp-template/_build/linux-x86_64/release/exts --enable omni.example.cpp.hello_world
```

이 예제는 USD를 바꾸지 않는다. extension은 code lifecycle 단위이고 Stage는 별도 데이터 장면이다. binary가 로드되었는지는 startup 출력으로 확인하며 단순 `.so` 생성은 host 실행 성공의 증거가 아니다.

## 구성과 확장

`config/extension.toml`은 package, dependency, native plugin 경로를 기술한다. `premake5.lua`는 source를 어떤 target으로 빌드할지 정한다. `carb::PluginImplDesc`는 plugin metadata, `CARB_PLUGIN_IMPL`은 `omni::ext::IExt` 구현을 Carbonite에 노출한다. `onStartup`/`onShutdown`은 활성/비활성 이벤트이며, callback subscription을 추가한다면 shutdown에서 해제해야 한다.

독자 이름의 새 확장을 만들 때는 `source/extensions` 아래 예제 폴더를 복사하고 **폴더명, extension.toml, premake target, plugin id, C++ namespace**를 함께 바꾼다. `omni` 접두사는 NVIDIA 예약 이름이므로 사용자 새 이름은 `kr.cpp.lesson`처럼 정한다. 이 실습은 원본 example 이름에 코드를 적용해 build 연결을 먼저 배우는 단계다.

한 변수 실험: startup 메시지만 바꾸고 재빌드/재시작하여 이전 binary가 아닌 새 빌드를 로드하는지 확인한다. 컴파일 오류는 최초 error, 로드 오류는 ABI/dependency와 실제 `_build/.../exts` 경로를 확인한다. GPU/SDK build는 작성 환경에서 실행하지 않았다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_cpp_extensions.html).
