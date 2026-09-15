# isaacsim.replicator.scene_blox.generation.scene_generator

첫 등장: [176번 튜토리얼](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) · [run.py:43](../src/176_replicator_replicator_sceneblox/run.py#L43)

`SceneGenerator`는 완성된 SceneBlox 격자를 실제 USD 장면으로 만드는 클래스이다.

- `generation.yaml`과 충돌 생성 여부로 생성기를 구성한다.
- `generate_scene(grid, world, ...)`에 해결된 격자와 World를 전달해 미로 장면을 USD 파일로 저장한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 SceneBlox — Tile Randomization (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#tile-randomization)
