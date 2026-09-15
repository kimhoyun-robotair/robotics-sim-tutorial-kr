# isaacsim.examples.interactive.base_sample

첫 등장: [86번 튜토리얼](../src/86_tools_custom_interactive_examples/TUTORIAL.md) · [exts/kr.browser.example/kr_browser_example/__init__.py:5](../src/86_tools_custom_interactive_examples/exts/kr.browser.example/kr_browser_example/__init__.py#L5)

Load·Reset 버튼과 비동기 장면 초기화 흐름을 갖춘 사용자 예제의 기반 클래스 모음이다.

- `BaseSample`: `setup_scene()`, `setup_post_load()`, `setup_post_reset()`을 구현해 장면 생성과 초기화 동작을 정한다.
- `get_world()`: 예제가 관리하는 World를 얻어 객체를 추가하거나 조회한다.
- `BaseSampleUITemplate`: 예제 제목·설명·샘플 객체를 받아 기본 UI를 구성한다. `build_window` / `build_ui`를 브라우저에 연결한다.
- 5.1 문서에 클래스별 API 항목이 없어 해당 클래스를 설명하는 공식 가이드를 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [BaseSampleUITemplate·BaseSample 공식 가이드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html#basesampleuitemplate-basesample-classes)
