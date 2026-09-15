# omni.graph.action

첫 등장: [82번 튜토리얼](../src/82_tools_omnigraph_scripting/TUTORIAL.md) · [create_graphs.py:12](../src/82_tools_omnigraph_scripting/create_graphs.py#L12)

튜토리얼의 `omni.graph.action.*` 이름은 `og.Controller`에 전달하는 OmniGraph 노드 타입입니다.

- `OnPlaybackTick`은 재생 중 프레임마다 다음 노드로 실행 신호를 보냅니다.
- `OnTick`은 앱 갱신을 바탕으로 실행하며, 82번에서는 수동 평가하는 그래프의 시작 노드로 사용합니다.
- `outputs:tick`을 다른 노드의 `inputs:execIn`에 연결하여 출력·ROS 2 발행·로봇 제어를 실행합니다.
- `OnImpulseEvent`는 119번에서 `state:enableImpulse`로 수동 실행 신호를 발생시킬 때 사용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 OmniGraph Python Scripting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)
- [NVIDIA Kit On Playback Tick 노드](https://docs.omniverse.nvidia.com/kit/docs/omni.graph.action_nodes_core/latest/GeneratedNodeDocumentation/OgnOnPlaybackTick.html)
- [NVIDIA Kit On Tick 노드](https://docs.omniverse.nvidia.com/kit/docs/omni.graph.action_nodes_core/latest/GeneratedNodeDocumentation/OgnOnTick.html)
