# isaacsim.examples.browser

첫 등장: [86번 튜토리얼](../src/86_tools_custom_interactive_examples/TUTORIAL.md) · [exts/kr.browser.example/config/extension.toml:7](../src/86_tools_custom_interactive_examples/exts/kr.browser.example/config/extension.toml#L7)

사용자 예제를 Isaac Sim Examples Browser에 등록하고 해제하는 모듈이다.

- `get_instance()`: 예제 브라우저 인스턴스를 얻는다. 튜토리얼은 `get_browser_instance`라는 별칭으로 import한다.
- `register_example()`: 예제 이름·분류와 창 구성 함수를 연결한다.
- `deregister_example()`: 확장 종료 시 등록한 예제를 해제한다.
- 5.1 문서에 개별 함수 API 항목이 없어 확장 문서와 실제 등록 코드를 담은 공식 가이드를 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Example Browser 확장 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.examples.browser/docs/index.html)
- [register_example 공식 사용 예](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html#basesampleuitemplate-basesample-classes)
