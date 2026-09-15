# isaacsim.core.api.controllers.ArticulationController

첫 등장: [02번 튜토리얼](../src/02_core_core_hello_robot/TUTORIAL.md) · [run.py:68](../src/02_core_core_hello_robot/run.py#L68)

ArticulationAction에 담긴 관절 명령을 로봇의 관절 구조에 적용하는 제어기이다.

- `robot.get_articulation_controller()`: 로봇이 사용하는 관절 제어기를 얻는다.
- `apply_action(...)`: 목표 바퀴 속도 등의 관절 명령을 전달한다.
- 튜토리얼에서는 이동 제어기가 계산한 결과를 실제 로봇 관절에 적용하는 마지막 단계에 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [ArticulationController API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.controllers.ArticulationController)
