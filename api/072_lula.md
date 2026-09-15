# lula

첫 등장: [55번 튜토리얼](../src/55_motion_manipulators_lula_trajectory_generator/TUTORIAL.md) · [run.py:31](../src/55_motion_manipulators_lula_trajectory_generator/run.py#L31)

Isaac Sim의 모션 생성 기능에서 사용하는 Lula 라이브러리입니다. 튜토리얼에서는 복합 궤적의 경로를 정의할 때 직접 호출합니다.

- `Rotation3`, `Pose3`: 회전과 위치를 묶어 끝단의 시작 자세를 표현합니다.
- `create_task_space_path_spec()`: 이동, 회전, 세 점을 지나는 원호를 끝단 경로에 추가합니다.
- `create_c_space_path_spec()`: 관절 공간의 경유점을 지정합니다.
- `create_composite_path_spec()`, `CompositePathSpec.TransitionMode.FREE`: 끝단 경로와 관절 경로를 하나의 복합 경로로 연결합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Pose3](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.lula/docs/index.html#lula.Pose3)
- [TaskSpacePathSpec](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.lula/docs/index.html#lula.TaskSpacePathSpec)
- [CompositePathSpec](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.lula/docs/index.html#lula.CompositePathSpec)
