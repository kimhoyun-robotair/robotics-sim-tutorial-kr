# isaacsim.robot.wheeled_robots.controllers.differential_controller

첫 등장: [52번 튜토리얼](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) · [run.py:39](../src/52_motion_mobile_robot_controllers/run.py#L39)

좌우 바퀴의 속도 차이로 회전하는 로봇을 위한 제어기 모듈입니다.

- `DifferentialController`: 바퀴 반지름과 좌우 바퀴 간격을 지정합니다.
- `forward([선속도, 회전속도])`: Jetbot의 바퀴 속도 action을 계산하며, 결과를 `apply_wheel_actions()`로 적용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [DifferentialController](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html#isaacsim.robot.wheeled_robots.controllers.DifferentialController)
