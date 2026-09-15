# omni.graph.core

첫 등장: [82번 튜토리얼](../src/82_tools_omnigraph_scripting/TUTORIAL.md) · [create_graphs.py:2](../src/82_tools_omnigraph_scripting/create_graphs.py#L2)

Python으로 OmniGraph의 노드·연결·입력값을 만들고 그래프를 실행한다.

- `Controller.edit()`와 `Controller.Keys`로 그래프 생성, 노드 연결, 초기 입력값 설정을 묶어서 수행한다.
- `Controller.attribute()`·`set()`으로 속성을 읽거나 쓰고, `create_attribute()`로 사용자 노드의 입력을 추가한다.
- `Controller.connect()`와 `evaluate_sync()`로 연결을 만들거나 그래프를 명시적으로 실행한다.
- ROS 2 통신, 로봇 구동, 시간·카메라 발행, 사용자 randomizer에서 같은 제어 방식을 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)
- [omni.graph.core API](https://docs.omniverse.nvidia.com/kit/docs/omni.graph/latest/omni.graph.core.html#module-omni.graph.core)
