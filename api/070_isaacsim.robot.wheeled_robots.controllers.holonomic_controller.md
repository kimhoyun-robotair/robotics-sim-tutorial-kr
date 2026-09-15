# isaacsim.robot.wheeled_robots.controllers.holonomic_controller

첫 등장: [52번 튜토리얼](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) · [run.py:40](../src/52_motion_mobile_robot_controllers/run.py#L40)

옆 방향으로도 움직일 수 있는 전방향 이동 로봇의 바퀴 제어기입니다.

- `HolonomicController`: Kaya의 바퀴 반지름·위치·방향과 롤러 각도를 지정합니다.
- `forward([전후 속도, 좌우 속도, 회전속도])`: 각 바퀴의 속도 action을 계산합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [HolonomicController](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html#isaacsim.robot.wheeled_robots.controllers.HolonomicController)
