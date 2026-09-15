# omni::ext::IExt

첫 등장: [89번 튜토리얼](../src/89_tools_custom_cpp_extensions/TUTORIAL.md) · [HelloWorldExtension.cpp:11](../src/89_tools_custom_cpp_extensions/HelloWorldExtension.cpp#L11)

C++ Kit 확장의 시작과 종료 동작을 구현하는 인터페이스이다.

- `omni::ext::IExt`를 상속해 `ExampleCppHelloWorldExtension`을 만든다.
- `onStartup(const char* extId)`에서 확장 시작 시 메시지를 출력한다.
- `onShutdown()`에서 확장 종료 시 메시지를 출력한다. 생명주기 호출은 Kit가 담당한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_cpp_extensions.html)
- [공식 Carbonite API — omni::ext::IExt](https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/api/classomni_1_1ext_1_1IExt.html)
