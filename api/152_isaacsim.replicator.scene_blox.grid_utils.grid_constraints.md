# isaacsim.replicator.scene_blox.grid_utils.grid_constraints

첫 등장: [176번 튜토리얼](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) · [run.py:46](../src/176_replicator_replicator_sceneblox/run.py#L46)

`GridConstraints`는 SceneBlox 격자의 영역별 타일 배치 제한을 관리하는 클래스이다.

- `from_yaml()`로 `constraints.yaml`과 격자 크기를 읽어 제약을 만든다.
- 제약 객체를 `Grid.solve()`에 전달하고, 풀이 재시도 전 `reset()`으로 상태를 초기화한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 SceneBlox — Constraints (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#constraints)
