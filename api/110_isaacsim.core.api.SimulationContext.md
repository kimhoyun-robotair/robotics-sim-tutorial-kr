# isaacsim.core.api.SimulationContext

첫 등장: [113번 튜토리얼](../src/113_ros2_ros2_camera/TUTORIAL.md) · [run.py:23](../src/113_ros2_ros2_camera/run.py#L23)

물리 초기화, 재생 상태와 시뮬레이션 스텝을 직접 관리하는 클래스이다.

- `SimulationContext(...)`: 장면 단위와 물리·렌더링 시간 간격을 지정한다.
- `initialize_physics()` / `play()` / `stop()`: 물리를 초기화하고 시뮬레이션을 시작·종료한다.
- `step()` / `is_playing()`: 물리·렌더링을 진행하고 현재 재생 상태를 확인한다.
- ROS 2 카메라와 bridge 예제에서 OmniGraph·센서 갱신을 위한 실행 루프를 구성한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [SimulationContext API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.simulation_context.SimulationContext)
