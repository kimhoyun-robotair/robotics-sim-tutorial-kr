# isaacsim.robot.manipulators.controllers

첫 등장: [43번 튜토리얼](../src/43_robot_setup_pickplace_example/TUTORIAL.md) · [run.py:35](../src/43_robot_setup_pickplace_example/run.py#L35)

로봇 팔의 이동과 그리퍼 개폐를 단계별로 진행하는 공통 제어기입니다.

- `PickPlaceController`: `cspace_controller`와 `gripper`를 받아 UR10e 집기 작업을 구성합니다.
- `forward()`: 집을 위치, 놓을 위치, 관절 상태, 끝단 오프셋으로 다음 action을 계산합니다.
- `events_dt`, `is_done()`: 단계별 진행 속도를 설정하고 전체 작업 완료 여부를 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [PickPlaceController](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators/docs/index.html#isaacsim.robot.manipulators.controllers.PickPlaceController)
