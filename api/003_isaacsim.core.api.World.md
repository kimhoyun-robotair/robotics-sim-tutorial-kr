# isaacsim.core.api.World

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:54](../src/00_core_quickstart_isaacsim/run.py#L54)

장면의 객체와 작업을 관리하면서 물리·렌더링 시뮬레이션을 진행하는 클래스이다.

- `World(...)`: 장면 단위와 물리·렌더링 시간 간격을 지정한다. `instance()` / `clear_instance()`로 공유 인스턴스를 조회·해제한다.
- `reset()` / `step()` / `render()`: 초기 상태로 되돌리고 시뮬레이션 또는 렌더링을 진행한다. `play()` / `pause()` / `stop()`은 재생 상태를 바꾼다.
- `initialize_simulation_context_async()` / `reset_async()` / `pause_async()`: Script Editor 등에서 비동기로 초기화·리셋·일시 정지한다.
- `add_physics_callback()` / `remove_physics_callback()` / `physics_callback_exists()`: 매 물리 스텝에 실행할 콜백을 등록·해제·확인한다.
- `scene`, `add_task()` / `get_observations()`, `get_physics_context()` / `get_data_logger()`: 객체 관리, 작업 관측값, 물리 설정, 기록 기능에 접근한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [World API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.world.World)
