# isaacsim.replicator.scene_blox.grid_utils.grid

첫 등장: [176번 튜토리얼](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) · [run.py:45](../src/176_replicator_replicator_sceneblox/run.py#L45)

`Grid`는 타일 배치 규칙과 제약을 만족하는 SceneBlox 격자를 구하는 클래스이다.

- 행·열 수와 `TileSuperposition`으로 초기 격자를 만든다.
- `solve()`로 제약에 맞는 타일 배치를 시도하며, 선택적으로 풀이 과정을 표시한다.
- 배치에 실패하면 `reset()`으로 초기 후보를 복원한 뒤 다시 시도한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 SceneBlox — Grid Generation (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#grid-generation)
