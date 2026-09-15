# isaacsim.core.utils.string

첫 등장: [25번 튜토리얼](../src/25_core_core_adding_multiple_robots/TUTORIAL.md) · [handover_task.py:5](../src/25_core_core_adding_multiple_robots/handover_task.py#L5)

장면에 여러 작업이나 로봇을 추가할 때 겹치지 않는 이름을 만드는 유틸리티이다.

- `find_unique_string_name(initial_name, is_unique_fn)`: 후보 이름을 검사 함수에 전달하며 사용할 수 있는 고유 이름을 찾는다.
- 튜토리얼에서는 `is_prim_path_valid()`와 장면 객체 이름 검사를 이용해 USD 경로 및 객체 이름 충돌을 피한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [find_unique_string_name API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.string.find_unique_string_name)
