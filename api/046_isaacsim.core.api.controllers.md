# isaacsim.core.api.controllers

첫 등장: [23번 튜토리얼](../src/23_core_core_adding_controller/TUTORIAL.md) · [run.py:29](../src/23_core_core_adding_controller/run.py#L29)

사용자 정의 제어기를 작성할 때 상속하는 BaseController 클래스를 제공하는 모듈이다.

- `BaseController`: 23번에서 직접 작성하는 `UnicycleController`의 기반 클래스이다.
- `forward(command)`: 선속도·각속도를 좌우 바퀴 속도로 변환하는 계산을 구현하고 `ArticulationAction`을 반환한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [BaseController API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.controllers.BaseController)
