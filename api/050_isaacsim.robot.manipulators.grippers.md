# isaacsim.robot.manipulators.grippers

첫 등장: [24번 튜토리얼](../src/24_core_core_adding_manipulator/TUTORIAL.md) · [run.py:40](../src/24_core_core_adding_manipulator/run.py#L40)

그리퍼 관절과 열림·닫힘 위치를 연결하는 API입니다.

- `ParallelGripper`: 끝단 경로, 손가락 관절 이름, 열린 위치와 닫힌 위치를 지정합니다.
- `use_mimic_joints=True`: 튜토리얼의 Robotiq 그리퍼에서 대표 손가락 관절을 통해 연동 관절을 움직입니다.
- `set_joint_positions()`, `apply_action()`, `get_joint_positions()`: 초기화, 개폐 명령, 현재 손가락 위치 확인에 사용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [ParallelGripper](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators/docs/index.html#isaacsim.robot.manipulators.grippers.ParallelGripper)
