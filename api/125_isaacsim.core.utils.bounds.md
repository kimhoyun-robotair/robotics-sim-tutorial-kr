# isaacsim.core.utils.bounds

첫 등장: [137번 튜토리얼](../src/137_replicator_replicator_scene_based_sdg/TUTORIAL.md) · [scene_based_sdg_utils.py:25](../src/137_replicator_replicator_scene_based_sdg/scene_based_sdg_utils.py#L25)

Prim의 경계 상자를 계산해 물체 배치와 카메라 촬영 범위를 정하는 함수 모음이다.

- `create_bbox_cache()`: USD 경계 계산을 재사용할 캐시를 만든다.
- `compute_combined_aabb()`: 여러 물체를 함께 감싸는 월드 축 기준 경계 상자를 구한다.
- `compute_obb()` / `get_obb_corners()`: 물체 방향을 고려한 경계 상자의 중심·축·반크기와 모서리 좌표를 얻는다.
- 장면 기반 합성 데이터의 배치·촬영 영역과 UR10 상자의 접촉 조회 범위를 계산할 때 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [create_bbox_cache API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.bounds.create_bbox_cache)
- [compute_combined_aabb API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.bounds.compute_combined_aabb)
- [compute_obb API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.bounds.compute_obb)
- [get_obb_corners API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.bounds.get_obb_corners)
