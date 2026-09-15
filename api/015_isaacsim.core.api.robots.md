# isaacsim.core.api.robots

첫 등장: [02번 튜토리얼](../src/02_core_core_hello_robot/TUTORIAL.md) · [run.py:30](../src/02_core_core_hello_robot/run.py#L30)

USD 장면에 있는 로봇을 감싸 관절 정보와 자세를 읽고 제어하는 Robot 클래스를 제공한다.

- `Robot(prim_path=..., name=...)`: 불러온 Jetbot을 장면 관리용 로봇 객체로 감싼다.
- `num_dof`, `dof_names`, `get_dof_index()`: 관절 개수·이름과 바퀴 관절 인덱스를 확인한다.
- `get_world_pose()` / `get_joint_velocities()`: 로봇의 이동과 실제 바퀴 속도를 관찰한다.
- `get_articulation_controller()`: 바퀴 관절에 명령을 전달할 제어기를 얻는다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Robot API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.robots.Robot)
