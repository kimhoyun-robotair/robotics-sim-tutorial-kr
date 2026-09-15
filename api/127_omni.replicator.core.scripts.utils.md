# omni.replicator.core.scripts.utils

첫 등장: [140번 튜토리얼](../src/140_replicator_replicator_custom_og_randomizer/TUTORIAL.md) · [run.py:34](../src/140_replicator_replicator_custom_og_randomizer/run.py#L34)

사용자 OmniGraph 노드를 Replicator의 트리거 안에서 호출할 수 있게 연결한다.

- `@ReplicatorWrapper`로 구 내부·표면·껍질에 위치를 샘플링하는 사용자 함수를 감싼다.
- `create_node()`로 `omni.graph.scriptnode.ScriptNode`를 생성한다.
- `set_target_prims()`로 노드의 target 입력에 배치 대상 Prim 경로들을 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [omni.replicator.core.scripts.utils 공식 활용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_custom_og_randomizer.html#implementation)
