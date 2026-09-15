# isaacsim.robot.surface_gripper

첫 등장: [60번 튜토리얼](../src/60_motion_robot_surface_gripper/TUTORIAL.md) · [run.py:31](../src/60_motion_robot_surface_gripper/run.py#L31)

접촉한 물체를 부착해 들어 올리는 표면 그리퍼를 제어하는 API입니다.

- `GripperView`: Stage에 만든 그리퍼 Prim 경로를 연결합니다.
- `set_surface_gripper_properties()`: 흡착 거리, 축 방향·전단 힘 한계, 재시도 간격을 지정합니다.
- `apply_gripper_action()`: 예제의 정해진 시점에 그리퍼를 닫고 엽니다.
- `get_surface_gripper_status()`, `get_gripped_objects()`: 현재 상태와 붙잡은 물체 경로를 읽어 기록합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [GripperView](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.surface_gripper/docs/index.html#isaacsim.robot.surface_gripper.GripperView)
