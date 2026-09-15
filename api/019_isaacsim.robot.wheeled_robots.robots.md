# isaacsim.robot.wheeled_robots.robots

첫 등장: [02번 튜토리얼](../src/02_core_core_hello_robot/TUTORIAL.md) · [run.py:39](../src/02_core_core_hello_robot/run.py#L39)

Jetbot이나 Kaya처럼 바퀴로 움직이는 로봇을 불러오고, 바퀴 관절에 명령을 전달하는 API입니다.

- `WheeledRobot`: USD 경로와 `wheel_dof_names`를 지정해 로봇을 생성하거나 연결합니다.
- `apply_wheel_actions()`: 제어기가 계산한 바퀴 속도 명령을 지정된 바퀴 관절에 적용합니다.
- `get_world_pose()`, `get_dof_index()`: 이동 결과와 관절 번호를 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [WheeledRobot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html#isaacsim.robot.wheeled_robots.robots.WheeledRobot)
