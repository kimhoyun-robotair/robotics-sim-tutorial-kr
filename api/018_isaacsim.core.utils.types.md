# isaacsim.core.utils.types

첫 등장: [02번 튜토리얼](../src/02_core_core_hello_robot/TUTORIAL.md) · [run.py:37](../src/02_core_core_hello_robot/run.py#L37)

로봇 제어에 전달할 관절 명령을 묶는 자료형을 제공하는 모듈이다.

- `ArticulationAction`: 목표 관절 위치·속도·힘을 `joint_positions`, `joint_velocities`, `joint_efforts`에 담는다.
- `joint_indices`: 로봇 전체 중 명령을 적용할 관절을 지정한다.
- 튜토리얼에서는 바퀴 속도 제어, 매니퓰레이터 동작, 기록한 관절 명령 재생에 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [ArticulationAction API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.types.ArticulationAction)
