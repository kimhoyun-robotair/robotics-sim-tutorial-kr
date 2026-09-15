# isaacsim.core.api.scenes.Scene

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:82](../src/00_core_quickstart_isaacsim/run.py#L82)

World 안의 시뮬레이션 객체를 이름으로 등록하고 찾아 사용하는 장면 관리 클래스이다.

- `world.scene`: 튜토리얼에서 `Scene` 객체에 접근하는 경로이다.
- `add(...)`: 도형·로봇·Prim 래퍼를 장면에 등록한다.
- `add_default_ground_plane()`: 물체를 받칠 기본 지면을 추가한다.
- `get_object(name)` / `object_exists(name)`: 등록한 객체를 찾거나 이름의 존재 여부를 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Scene API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.scenes.Scene)
