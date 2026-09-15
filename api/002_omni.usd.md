# omni.usd

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:50](../src/00_core_quickstart_isaacsim/run.py#L50)

Isaac Sim에서 현재 열린 USD Stage를 가져오고 장면의 로딩·선택 상태를 관리한다.

- `get_context().get_stage()`로 얻은 Stage에 객체·조명·카메라를 추가하거나 USD 속성을 수정한다.
- `new_stage()`·`open_stage()`와 비동기 버전으로 장면을 새로 만들거나 연다.
- `get_selection()`으로 Prim을 선택하고, Stage 이벤트를 구독해 장면 변경을 받는다.
- `get_stage_next_free_path()`·`get_world_transform_matrix()`·`get_shader_from_material()`로 경로, 월드 변환, 재질 Shader를 찾는다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [omni.usd API](https://docs.omniverse.nvidia.com/kit/docs/omni.usd/latest/omni.usd.html#module-omni.usd)
