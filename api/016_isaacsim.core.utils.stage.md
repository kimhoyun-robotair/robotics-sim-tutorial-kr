# isaacsim.core.utils.stage

첫 등장: [02번 튜토리얼](../src/02_core_core_hello_robot/TUTORIAL.md) · [run.py:33](../src/02_core_core_hello_robot/run.py#L33)

USD Stage를 만들거나 열고, 기존 USD 파일을 현재 장면에 참조로 추가하는 함수 모음이다.

- `add_reference_to_stage()`: 로봇·환경 USD 파일을 지정한 Prim 경로에 연결한다.
- `get_current_stage()`: 현재 편집 중인 Stage를 얻는다.
- `open_stage()` / `close_stage()`: USD 장면을 열거나 닫는다.
- `create_new_stage()` / `create_new_stage_async()`: 새 Stage를 동기 또는 비동기로 만든다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [stage API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#module-isaacsim.core.utils.stage)
