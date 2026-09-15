# isaacsim.core.api.articulations.ArticulationSubset

첫 등장: [101번 튜토리얼](../src/101_digital_twin_cortex_4_franka_block_stacking/TUTORIAL.md) · [block_stacking_behavior.py:709](../src/101_digital_twin_cortex_4_franka_block_stacking/block_stacking_behavior.py#L709)

로봇 articulation의 관절 일부를 이름으로 묶는 클래스이다. 이 튜토리얼에서는 Cortex의 팔 제어기가 가진 반환 객체를 통해 사용한다.

- `robot.arm.articulation_subset`으로 팔 제어에 해당하는 관절 집합에 접근한다.
- `get_joints_state().positions`로 현재 팔 관절 위치를 읽어, 블록을 들어 올릴 때 유지할 기준 자세로 설정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 Isaac Sim 5.1 API — ArticulationSubset 반환 객체 설명 (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.ArticulationMotionPolicy.get_active_joints_subset)
