# isaacsim.robot.manipulators.examples.franka.tasks

첫 등장: [24번 튜토리얼](../src/24_core_core_adding_manipulator/TUTORIAL.md) · [run.py:27](../src/24_core_core_adding_manipulator/run.py#L27)

Franka 로봇과 작업에 필요한 물체를 함께 준비하는 예제용 Task입니다.

- `PickPlace`: 집을 큐브, 놓을 위치, Franka 로봇을 준비합니다. 여러 로봇의 협업 작업에도 포함합니다.
- `FollowTarget`: 로봇 끝단이 따라갈 목표 물체를 준비하며, 데이터 기록과 URDF 가져오기 예제에서 사용합니다.
- `get_params()`, `get_observations()`: 생성된 객체 이름과 현재 상태를 제어 코드에 전달합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.robot.manipulators.examples 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators.examples/docs/index.html)
