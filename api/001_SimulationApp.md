# isaacsim.SimulationApp

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:36](../src/00_core_quickstart_isaacsim/run.py#L36)

Python 스크립트에서 Isaac Sim 애플리케이션을 시작하고 프레임 갱신과 종료를 관리하는 클래스이다.

- `SimulationApp({"headless": ...})`: GUI 표시 여부 등을 지정해 실행 환경을 만든다.
- `update()` / `is_running()`: 프레임을 갱신하고 실행 중인지 확인한다.
- `close()`: 튜토리얼 종료 시 애플리케이션을 닫는다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html#isaacsim.simulation_app.SimulationApp)
