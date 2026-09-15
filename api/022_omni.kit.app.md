# omni.kit.app

첫 등장: [05번 튜토리얼](../src/05_python_usd_python_scripting_concepts/TUTORIAL.md) · [script_editor.py:3](../src/05_python_usd_python_scripting_concepts/script_editor.py#L3)

Isaac Sim을 실행하는 Kit 앱의 업데이트와 확장 관리 인터페이스에 접근한다.

- `get_app().next_update_async()`로 다음 앱 업데이트를 기다려 Script Editor의 비동기 작업을 진행한다.
- `get_extension_manager()`로 확장의 활성화 여부를 확인하고 확장을 켜거나 다시 로드한다.
- `GLOBAL_EVENT_UPDATE`는 이벤트 예제에서 앱 업데이트 횟수를 관찰할 때 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html)
- [omni.kit.app API](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/omni.kit.app.html#module-omni.kit.app)
