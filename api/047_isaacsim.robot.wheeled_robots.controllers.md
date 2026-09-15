# isaacsim.robot.wheeled_robots.controllers

첫 등장: [23번 튜토리얼](../src/23_core_core_adding_controller/TUTORIAL.md) · [run.py:33](../src/23_core_core_adding_controller/run.py#L33)

차체 속도 또는 목표 위치를 받아 이동 로봇의 바퀴 명령을 계산하는 제어기입니다.

- `DifferentialController`: 선속도와 회전속도를 좌우 바퀴 속도로 변환합니다.
- `WheelBasePoseController`: 현재 위치·방향과 목표 위치를 받아 하위 바퀴 제어기를 통해 주행 명령을 만듭니다.
- `forward()`의 결과를 `WheeledRobot.apply_wheel_actions()`에 전달하며, 여러 로봇에는 각각 별도 제어기를 둡니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [DifferentialController](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html#isaacsim.robot.wheeled_robots.controllers.DifferentialController)
- [WheelBasePoseController](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html#isaacsim.robot.wheeled_robots.controllers.WheelBasePoseController)
