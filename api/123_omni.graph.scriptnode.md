# omni.graph.scriptnode

첫 등장: [136번 튜토리얼](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) · [run.py:48](../src/136_replicator_replicator_isaac_snippets/run.py#L48)

`omni.graph.scriptnode.ScriptNode`는 Python 스크립트를 실행하는 OmniGraph 노드 타입입니다.

- 140번은 `inputs:script`에 `sphere_node.py` 코드를 넣고 Prim 목록·반지름·시드 입력을 추가합니다.
- 같은 위치 샘플링 코드를 수동 그래프 평가와 Replicator 랜덤화 흐름에 연결합니다.
- 관련 예제는 `/app/omni.graph.scriptnode/opt_in` 설정으로 스크립트 실행을 허용합니다.

첫 등장은 136번의 `/app/omni.graph.scriptnode/opt_in` 설정이며, `ScriptNode` 생성은 140번에서 다룬다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html)
- [NVIDIA Kit Script Node 입력·출력 문서](https://docs.omniverse.nvidia.com/kit/docs/omni.graph.scriptnode/latest/GeneratedNodeDocumentation/OgnScriptNode.html)
