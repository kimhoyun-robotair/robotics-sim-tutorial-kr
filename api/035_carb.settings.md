# carb.settings

첫 등장: [15번 튜토리얼](../src/15_tools_carb_settings/TUTORIAL.md) · [change_setting.py:1](../src/15_tools_carb_settings/change_setting.py#L1)

경로 형태의 키로 Isaac Sim과 확장의 실행 설정을 읽고 쓴다.

- `get_settings()`로 설정 인터페이스를 얻고 `get()`·`set()`·`set_bool()`로 값을 다룬다.
- 15번 예제는 `/exts/kr.settings.demo/data/foo` 값을 바꾸고 확장을 다시 로드해 설정 반영을 확인한다.
- 합성 데이터 예제에서는 렌더링, 고정 시간 간격, 모션 블러와 ScriptNode 사용 설정을 조절한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/carb_settings.html)
- [carb.settings API](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/carb.settings.html#module-carb.settings)
