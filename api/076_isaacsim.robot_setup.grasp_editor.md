# isaacsim.robot_setup.grasp_editor

첫 등장: [61번 튜토리얼](../src/61_motion_grasp_editor/TUTORIAL.md) · [run.py:27](../src/61_motion_grasp_editor/run.py#L27)

Grasp Editor로 저장한 물체 기준 집기 자세를 읽고, 물체의 현재 자세에 맞춰 변환하는 API입니다.

- `import_grasps_from_file()`: 집기 자세 파일을 `GraspSpec`으로 읽습니다.
- `get_grasp_names()`: 요청한 집기 자세 이름이 파일에 있는지 확인합니다.
- `compute_gripper_pose_from_rigid_body_pose()`: 물체의 위치·쿼터니언으로 그리퍼의 위치·쿼터니언을 계산합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [import_grasps_from_file](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_setup.grasp_editor/docs/index.html#isaacsim.robot_setup.grasp_editor.import_grasps_from_file)
- [GraspSpec](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_setup.grasp_editor/docs/index.html#isaacsim.robot_setup.grasp_editor.GraspSpec)
