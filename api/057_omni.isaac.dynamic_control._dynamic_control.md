# omni.isaac.dynamic_control._dynamic_control

첫 등장: [28번 튜토리얼](../src/28_python_usd_robots_simulation/TUTORIAL.md) · [TUTORIAL.md:51](../src/28_python_usd_robots_simulation/TUTORIAL.md#L51)

`_dynamic_control`은 로봇과 관절을 핸들로 찾아 상태를 읽고 제어하는 Python API입니다. 28번의 비교용 Script Editor 예제에서 등장합니다.

- `acquire_dynamic_control_interface()`로 인터페이스를 얻고 `get_articulation()`으로 로봇 핸들을 찾습니다.
- `find_articulation_dof()`, `get_dof_state()`로 특정 관절의 상태를 조사하고 `set_dof_position_target()`으로 위치 목표를 줍니다.
- Isaac Sim 4.5부터 deprecated로 표시된 API입니다. 28번의 기본 실행 코드는 5.1 Core Articulation을 사용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Dynamic Control API — Deprecated](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/deprecated/omni.isaac.dynamic_control/docs/index.html#api)
