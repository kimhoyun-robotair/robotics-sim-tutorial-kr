# isaacsim.cortex.framework.cortex_object

첫 등장: [101번 튜토리얼](../src/101_digital_twin_cortex_4_franka_block_stacking/TUTORIAL.md) · [block_stacking_behavior.py:27](../src/101_digital_twin_cortex_4_franka_block_stacking/block_stacking_behavior.py#L27)

`CortexObject`는 블록 쌓기 예제에서 일반 Core 객체를 Cortex 물체로 감싸는 데 사용합니다. 행동 코드가 물체의 자세와 변환 행렬을 공통 방식으로 읽을 수 있게 합니다.

- `CortexObject(core_object)`: 등록된 장애물이 아직 Cortex 객체가 아닐 때 감쌉니다.
- `get_transform()`, `get_world_pose()`: 블록의 집기 후보와 쌓기 위치를 계산할 때 사용합니다.
- 예제는 각 객체의 `sync_throttle_dt`를 `0.25`로 설정합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
