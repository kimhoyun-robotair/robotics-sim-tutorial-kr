# carb C++ plugin API

첫 등장: [89번 튜토리얼](../src/89_tools_custom_cpp_extensions/TUTORIAL.md) · [HelloWorldExtension.cpp:21](../src/89_tools_custom_cpp_extensions/HelloWorldExtension.cpp#L21)

C++ 확장을 Kit에서 읽을 수 있는 Carbonite 플러그인으로 등록하는 API이다.

- `carb::PluginImplDesc`에 플러그인 이름·설명·작성자·버전을 기록한다.
- `carb::PluginHotReload::eEnabled`로 실행 중 다시 불러오기를 허용한다.
- `CARB_PLUGIN_IMPL`로 구현 클래스를 등록하고 `fillInterface()`를 제공한다. Python의 `omni.ext.IExt`와는 별도의 C++ 등록 절차이다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_cpp_extensions.html)
- [공식 Carbonite API — CARB_PLUGIN_IMPL](https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/api/define_PluginUtils_8h_1aaf7b6097101d3be5c65e68a10794fdc6.html)
