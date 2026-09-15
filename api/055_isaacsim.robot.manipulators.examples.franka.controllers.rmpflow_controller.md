# isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller

첫 등장: [27번 튜토리얼](../src/27_core_advanced_data_logging/TUTORIAL.md) · [run.py:29](../src/27_core_advanced_data_logging/run.py#L29)

Franka용 RMPflow 설정을 사용해 끝단 목표를 관절 명령으로 바꾸는 예제 제어기입니다.

- `RMPFlowController`: 대상 Franka articulation을 연결해 생성합니다.
- `forward()`: 목표 끝단의 위치와 방향을 입력받아 로봇에 적용할 action을 반환합니다.
- 목표 추종 데이터를 기록하는 예제와 URDF로 가져온 Franka를 움직이는 예제에서 사용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.robot.manipulators.examples 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators.examples/docs/index.html)
