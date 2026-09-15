# isaacsim.robot.manipulators

첫 등장: [43번 튜토리얼](../src/43_robot_setup_pickplace_example/TUTORIAL.md) · [run.py:33](../src/43_robot_setup_pickplace_example/run.py#L33)

사용자가 준비한 로봇 팔 USD에 끝단과 그리퍼를 연결하는 API입니다.

- `SingleManipulator`: UR10e의 Prim, 끝단 경로, `ParallelGripper`를 묶어 Scene에 추가합니다.
- `end_effector.get_world_pose()`: 끝단 위치를 읽어 목표와의 오차를 확인합니다.
- `apply_action()`, `get_joint_positions()`: 역기구학이나 RMPflow가 만든 관절 명령을 적용하고 상태를 읽습니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [SingleManipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators/docs/index.html#isaacsim.robot.manipulators.manipulators.SingleManipulator)
