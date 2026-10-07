# Workflows
> **출처**: [해당링크](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)  
  
Isaac Sim은 엔비디아 Omniverse의 일환으로 개발이 되었기 때문에, 이걸 사용할 수 있는 여러가지 workflow를 제공한다고 안내가 되어있다. 사용 가능한 workflow는 다음과 같다:
- GUI
- Extensions
- Standalone Python

## Workflows
1. **GUI**
   1. **Key Features** : Visual, Intuitive, Specialized tools for populating and simulating a virtual world
   2. **Recommended Usage** : World building, assemble robots, attach sensors, visual programming using OmniGraphs and Initializing ROS Bridges
2. **Extension**
   1. **Key Features** : Runs asynchronously to allow interactions with the stage, **hot reloading** to reflect changes immediately, adaptive physics steps for real-time simulation
   2. **Recommended Usage** :  Testing Python snippets, building interactive GUIS, custom application modules, and real-time sensitive applications
3. **Standalone Python**
   1. **Key Features** : Control over timing of physics and rendering steps, can be run in headless mode
   2. **Recommended usage** : Large scale training for RL, systematic world generation, and modification

## Combining Workflows
기본적으로 GUI, Extension, Standalone Python의 기능은 거의 다르지 않고, 3개 중 어느걸 선택해도 동일하게 구현 가능하다.
### Extensions and the GUI
> **Extension이란?**  
> Extensions are plugins to Omniverse Kit that extend its capabilities. They are offered with complete source code to help developers easily create, add, and modify the tools and workflows they need to be productive. Extensions are the core building blocks of Omniverse Kit based applications.  
  
Extension들은 Omniverse Kit 기반의 application 개발자들에게 다양한 편의성 및 기능을 제공하기 위해서 만들어진 core들이고, 어느 Omniverse application에서든 다양하게 활용이 가능하다. Isaac Sim의 대부분의 기능들 역시 Extension으로 구성이 되어있다.  
**GUI workflow**의 경우 Isaac Sim의 시작과 동시에 기본적으로 로드되는 extension들의 모음집으로 구성이 되어있다고 할 수 있다. Isaac Sim을 사용함에 있어서 자주 사용되는 `virtual world, robot, examining physics, rendering, material properties, profiling performance, tools for visual programming`이 포함이 되어있으며, 이를 통해서 USD stage와 asset들, 그리고 Robot application을 다룰 수 있다.

### Python Standalone and in an Extension
둘이 사용하는 함수, API 모두 동일하다. 하지만 다른 부분을 정리하자면 다음과 같다.   
  
**Python in an Extension**  
Script Editor를 활용해서 직접 파이썬을 사용한다면, USD stage와 비동기적으로 상호작용이 가능하다. 즉, USD Stage 그 자체를 따로 열 필요 없이 바로 접근해서 사용이 가능하다는 것이다. Extension 내부에서 실행되는 파이썬 코드는 렌더링이나 Physics stepping을 막지 않고 바로 실행이 가능하며, 따라서 physics step이나 rendering step에 맞춰 작업을 수행하고 싶거나, 혹은 blocking이 발생할 가능성이 있는 작업을 수행하려면 해당 기능이 정상적으로 동작하도록 적절한 callback이나 async function을 추가해야 한다.  
  
**Standalone Python**  
파이썬 스크립트를 통해서 Isaac Sim을 실행한다. 이 script 내부에서는 headless 모드와 GUI 모드를 선택 가능하며, rendering step과 physics step을 직접 수동으로 전개할 수 있다(즉, 특정 명령들의 실행이 모두 완료된 후 simulation step이 진행되도록 강제할 수 있다). 따라서 Standalone은 다음에 유리하다.
- policy, control 학습
- 다음 simulation step으로 넘어가기 전에 randomization 작업이 필요한 경우
- ROS에서 messgae publishing rate를 정확하게 제어해야 하는 경우
- headless 모드로 실행하는 경우

## Hot Reloading for Extensions
파이썬 기반의 Extension은 **Hot reload** 기능을 지원하는데, Isaac Sim을 실행한 상태에서 파이썬 코드를 수정한 뒤 파일을 저장하면, Isaac sim을 종료하거나 다시 시작하지 않더라도 그 변경 사항이 어플리케이션에 실시간으로 반영되는 기능이다.
