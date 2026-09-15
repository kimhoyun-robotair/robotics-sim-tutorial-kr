# omni.ext

첫 등장: [15번 튜토리얼](../src/15_tools_carb_settings/TUTORIAL.md) · [exts/kr.settings.demo/kr_settings_demo/__init__.py:2](../src/15_tools_carb_settings/exts/kr.settings.demo/kr_settings_demo/__init__.py#L2)

Python 확장의 시작과 종료 동작을 구현하는 기본 인터페이스를 제공한다.

- `IExt`를 상속하고 `on_startup(ext_id)`에서 설정 읽기, UI 생성, 예제 등록 등을 수행한다.
- `on_shutdown()`에서 창·구독·등록 정보를 정리한다.
- 설정 확장, 템플릿 확장, Examples Browser 확장과 Cortex 확장에서 같은 수명주기를 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/carb_settings.html)
- [omni.ext API](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/omni.ext.html#module-omni.ext)
