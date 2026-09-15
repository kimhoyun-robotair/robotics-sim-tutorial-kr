# isaacsim.cortex.framework.cortex_rigid_prim

첫 등장: [102번 튜토리얼](../src/102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) · [run.py:40](../src/102_digital_twin_cortex_5_ur10_bin_stacking/run.py#L40)

`CortexRigidPrim`은 UR10 상자 쌓기 예제에서 USD로 추가한 상자를 강체 객체로 연결하는 데 사용합니다. 생성한 객체를 Scene에 등록하여 컨베이어 위 움직임을 제어합니다.

- `CortexRigidPrim(name=..., prim_path=...)`: 새 상자의 Prim을 감싸 Scene에 추가합니다.
- `set_world_pose()`, `set_linear_velocity()`, `set_visibility()`: 생성 위치·방향, 컨베이어 진행 속도, 표시 여부를 설정합니다.
- `get_world_pose()`: 기존 상자가 컨베이어 영역을 벗어났는지 확인하여 다음 상자를 생성합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
