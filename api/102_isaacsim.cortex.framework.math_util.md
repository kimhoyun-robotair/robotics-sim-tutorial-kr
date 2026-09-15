# isaacsim.cortex.framework.math_util

첫 등장: [100번 튜토리얼](../src/100_digital_twin_cortex_3_example_peck_games/TUTORIAL.md) · [peck_decider_network.py:16](../src/100_digital_twin_cortex_3_example_peck_games/peck_decider_network.py#L16)

`isaacsim.cortex.framework.math_util`은 Cortex 행동에서 위치, 회전, 변환 행렬을 계산하는 데 사용합니다. 튜토리얼은 이 모듈을 `math_util`이라는 이름으로 가져온다.

- `normalized()`, `make_rotation_matrix()`, `matrix_to_quat()`: 접근 방향을 정규화하고 목표 방향을 회전 행렬·쿼터니언으로 표현합니다.
- `pack_R()`, `unpack_R()`, `pack_Rp()`, `unpack_T()`: 회전축, 위치, 변환 행렬을 구성하거나 분해합니다.
- `pq2T()`, `T2pq()`: 위치·쿼터니언과 변환 행렬 사이를 변환합니다.
- `transforms_are_close()`: 현재 말단 자세가 집기·배치 목표에 충분히 가까운지 검사합니다.
- `Quaternion`: 컨베이어에 생성할 상자의 방향을 구성하고 회전을 합성합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
