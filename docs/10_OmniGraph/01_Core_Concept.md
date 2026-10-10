# Core Concepts
> **출처**: [해당링크](https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph/getting-started/core_concepts.html)  
  
**OmniGraph**는 visual scripting 언어로, static Omniverse World에 **동작(action)**과 **반응(reaction)**을 구현할 수 있도록 해준다. 또한, OmniGraph는 쉽게 확장 가능한(scalable) 아키텍쳐를 제공한다. 계산 작업들을 그래프 형태로 표현해두면, 그래프의 표현 자체를 변경하지 않고도 단일 컴퓨터에서 효율적으로 실행할 수 있으며, 필요에 따라 여러 노드로 구성된 데이터센터의 전체 연산 능력까지 활용 가능하다.

## Graph
그래프는 개념적으로 두 부분으로 구성된다(conceptual pieces).  
> **Authoring Graph**  
> Referes to the difinition of an OmniGraph Structure, including Nodes, Attributes, and Connections.  
  
> **Execution Graph**  
> The intermediate representation of an OmniGraph that has been optimized for fast evaluation, and which follows the business logic needs of a specifically defined Authoring Graph.  
  
  
일반적으로 **graph**라는 용어는 이 둘 중 하나를 가리키거나 둘 모두를 통칭하는데 사용한다. 다만 일반 사용자나, 캐주얼하게 개발하는데 사용하는 개발자들 사이에서는 그래프라고 한다면 보통 **Authoring Graph**를 의미하는 경우가 많다.  
  
또한 **Graph Type**은 때때로 **Evaluation Type**이라고 부르며, 해당 그래프가 어떤 방식으로 실행되어야 하는지에 대해서 나타낸다.

## Node
모든 노드 그래프 시스템의 핵심은 당연히 **노드(Node)**이다. 각 노드는 자신의 노드 타입(node type)에 의해서 정의되며, 내부에 다음과 같은 **Attribute**를 가질 수 있다.
- Input Attribute
- Output Attribute
- State Attribute

여기서 Attribute는 다음과 같이 정의된다.
> **Attribute**  
> A property of a node or node type that consists of a name, a data type, and a set of metadata that defines further properties.

## Attribute
**Attribute**는 고유한 이름(name)을 가지며, 특정 데이터 타입의 값을 저장한다. 또한 한 노드의 attribute를 다른 노드의 attribute와 연결할 수 있으며, 이러한 연결을 톻애 전체적인 **Evaluation Network**가 구성이 된다.

## Connections
그래프 이론의 관점에서, 노드를 **그래프의 정점(vertex)**라고 한다면, **Connection**은 **간선(edge)**에 해당한다. Connection은 graph 안에서 한 노드의 특정 attribute와 다른 노드의 특정 attribute 사이에 존재하는 **방향성을 가진 의존 관계 (directed dependency)**를 표현한다. 즉, 한 Attribute의 출력이나 상태가 다른 Attribute의 계산에 영향을 주도록 연결하는 관계를 의미한다.  
  
엔비디아에서는 다음과 같이 정의한다.  
> **Connection**  
> An edge in the Graph that joins two Nodes, indicating a relationship between the two Nodes, usually that the downstream Node cannot evaluate until the upstream Node has completed evaluation. Generally speaking, the connections are formed between two Attributes on the Node, not between the Nodes directly