# isaacsim.robot.wheeled_robots.controllers.ackermann_controller

첫 등장: [52번 튜토리얼](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) · [run.py:41](../src/52_motion_mobile_robot_controllers/run.py#L41)

자동차처럼 앞바퀴를 조향하는 Leatherback 로봇을 위한 Ackermann 제어기입니다.

- `AckermannController`: 축간거리, 좌우 바퀴 간격, 앞뒤 바퀴 반지름을 지정합니다.
- `forward()`: 튜토리얼의 조향각·속도 명령으로 조향 관절 위치와 구동 바퀴 속도를 계산합니다.
- 결과의 `joint_positions`는 앞바퀴 조향 관절에, `joint_velocities`는 네 바퀴 구동 관절에 나누어 적용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.robot.wheeled_robots 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html)
