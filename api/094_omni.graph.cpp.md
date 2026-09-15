# OmniGraph C++ node API

첫 등장: [90번 튜토리얼](../src/90_tools_omnigraph_custom_cpp_nodes/TUTORIAL.md) · [OgnExampleNode.cpp:11](../src/90_tools_omnigraph_custom_cpp_nodes/OgnExampleNode.cpp#L11)

OGN 정의에서 생성된 데이터베이스를 통해 C++ OmniGraph 노드를 구현하는 API이다.

- `.ogn`에서 생성되는 `OgnExampleNodeDatabase`의 `inputs`와 `outputs`로 값을 주고받는다.
- `compute()`는 입력 값이 양수인지 계산하며, `REGISTER_OGN_NODE()`로 구현을 등록한다.
- 131번의 ROS 2 노드는 `internalState<T>()`, `sPerInstanceState<T>()`, `releaseInstance()`로 인스턴스별 통신 상태를 관리하고 정리한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 OmniGraph — C++ 노드 인터페이스](https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/dev/ogn/node_architects_guide.html#c-abi-interface)
- [공식 Isaac Sim 5.1 — C++ OmniGraph 노드 구현](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_cpp_nodes.html)
