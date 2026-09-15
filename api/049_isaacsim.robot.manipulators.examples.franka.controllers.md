# isaacsim.robot.manipulators.examples.franka.controllers

첫 등장: [24번 튜토리얼](../src/24_core_core_adding_manipulator/TUTORIAL.md) · [run.py:28](../src/24_core_core_adding_manipulator/run.py#L28)

Franka 로봇과 그리퍼에 맞춰 준비된 pick-and-place 제어기입니다.

- `PickPlaceController`: `robot_articulation`과 `gripper`를 연결해 사용합니다.
- `forward()`: 물체 위치, 놓을 위치, 현재 관절 위치를 받아 다음 관절 명령을 계산합니다.
- `reset()`, `is_done()`: 작업을 처음부터 시작하고 집기·옮기기 완료 여부를 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.robot.manipulators.examples 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators.examples/docs/index.html)
