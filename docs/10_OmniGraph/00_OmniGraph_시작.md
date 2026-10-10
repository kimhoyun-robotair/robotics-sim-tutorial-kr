# OmniGraph
> **출처**: [해당링크](https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph.html)  
  
**OmniGraph**는 Omniverse의 **Visual Scripting Language**이다. OmniGraph를 사용하면 Omniverse 안의 World에 **동작(Behavior)**과 **상호작용(Interactivity)**을 부여할 수 있으며, 단순 이벤트 처리 뿐만 아니라 다음과 같은 다양한 계산 작업도 수행할 수 있다.
- Deformable Body
- Particle Simulation
- Event-Based Graph 등등

그리고 OmniGraph는 단일 Graph 구조를 얘기하는 것은 아니고 서로 다른 여러 종류의 그래프를 통합해 단일 프레임워크로 만들었다고 보는게 맞다. OmniGraph 내에서 생성할 수 있는 대표적인 그래프 타입은 다음과 같다.
- **Action Graph**
  - Event에 의해서 동작하는 **event-driven behavior**를 구현
- **Push Graph**
  - Node들을 지속적으로(continuously) 평가하고 실행하는 그래프  

이외에도 다음과 같은 기능을 위한 별도 Node 라이브러리가 제공이 된다.
- Particle System 생성
- Skeletal Animation 등 다양한 기능