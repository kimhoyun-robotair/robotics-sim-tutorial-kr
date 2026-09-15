# isaacsim.replicator.scene_blox.grid_utils.tile_superposition

첫 등장: [176번 튜토리얼](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) · [run.py:48](../src/176_replicator_replicator_sceneblox/run.py#L48)

`TileSuperposition`은 격자 한 칸에 놓일 수 있는 타일 후보와 선택 가중치를 담는 클래스이다.

- `tile_loader()`가 반환한 타일 목록과 가중치로 초기 후보 집합을 만든다.
- 같은 후보 집합을 `Grid` 생성과 `grid.reset()`에 전달해 격자를 초기화한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 SceneBlox — Grid Generation (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#grid-generation)
