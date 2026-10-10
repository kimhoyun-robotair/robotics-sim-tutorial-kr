# OmniGraph via Python Scripting Tutorial
> **출처**: [해당 링크](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)  
  
Omnigraph는 visual scripting 도구로 설계되었지만, 편하게 쓰라고 파이썬으로도 인터페이스 가능하도록 기능이 구현되어있다.

## 학습 목표
- 파이썬 API만을 활용해서 OmniGraph를 구성하는 예제
- OmniGraph의 기본 개념과 자주 사용되는 파라미터들을 소개하고, 스크립트 예제를 통해 확인

## Getting Started
### 사전 준비
- GUI 튜토리얼은 최소한 하고 오자. 특히 [Isaac Sim Omnigraph Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html#isaac-sim-app-tutorial-gui-omnigraph)랑 [Omniverse Script Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html#isaac-sim-app-omniverse-script-editor)는 한번 보고 오자.
- Core API 튜토리얼도 한번 보고오는 것이 좋다. 특히 [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html#isaac-sim-app-tutorial-core-hello-world) 튜토리얼을 통해서 파이썬을 활용한 Extension Workflow랑 Python Standalone Workflow에 익숙해진 상태에서 하는 것을 권장한다.

### Graph 만들기
1. `Window > Script Editor`를 열고 다음 코드를 작성하자.
```
import omni.graph.core as og

keys = og.Controller.Keys
(graph_handle, list_of_nodes, _, _) = og.Controller.edit(
    {"graph_path": "/action_graph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("tick", "omni.graph.action.OnTick"),
            ("print","omni.graph.ui_nodes.PrintText")
        ],
        keys.SET_VALUES: [
            ("print.inputs:text", "Hello World"),
            ("print.inputs:logLevel","Warning")                 # setting the log level to warning so we can see the printout in terminal
        ],
        keys.CONNECT: [
            ("tick.outputs:tick", "print.inputs:execIn")
        ],
    },
)
```
2. Run을 눌러서 실행하면 `/action_graph`라는 prim이 생성되는 것을 볼 수 있다.
3. Stage에서 `/action_graph` Prim을 펼쳐보면 그래프 아래에 다음 2개의 Node를 볼 수 있다: `tick`, `print`. 이 노드들은 Stage에 있는 다른 Prim들과 마찬가지로 접근 가능하다.
4. Play를 눌러서 시뮬레이션을 시작하면, 매 Frame마다 콘솔에 다음 문자열을 출력한다: `Hello World`
5. `Window > Graph Editors > Action Graph`를 열고 Stage Tree에서 방금 만든 그래프를 선택한 상태에서 그래프 에디터 창의 **Edit Action Graph** 아이콘을 클릭한다 그러면 두 노드가 하나의 Connection으로 연결된 것을 볼 수 있다.

### 그래프 편집하기
**Getting and Setting Attribute Values**
스크립트 에디터의 새로운 tab을 열고 다음 코드를 붙여넣고 실행하자.
```
# get existing value from an attribute
existing_text = og.Controller.attribute("/action_graph/print.inputs:text").get()
print("Existing Text: ", existing_text)

# set new value
og.Controller.attribute("/action_graph/print.inputs:text").set("New Texts to print")
```
이 코드를 실행하면 `Print Text Node`에 저장되어있는 값이 `Hello World`에서 `New Texts to print`로 변경된다. 다만 이 변경 효과는 그래프가 처음으로 Tick 되기 전에 실제 실행 결과에 반영이 되지 않으므로, **Run**을 누른 직후에는 아직 반영이 되어있지 않다. 기본적으로 코드는 현재 노드에 저장되어있는 값을 먼저 가져오기 때문에 `Existing Text: Hello World`가 먼저 출력이 되며, **Play**를 눌러서 시뮬레이션을 갱신하게 되면 그때부터 Tick마다 업데이트 된 문자열 `New Texts to print`가 출력이 된다.  
  
  
**새로운 노드와 Connection 추가하기**
```
og.Controller.create_node("/action_graph/new_node_name", "omni.graph.nodes.ConstantString")
og.Controller.attribute("/action_graph/new_node_name.inputs:value").set("This is a new node")
og.Controller.connect("/action_graph/new_node_name.inputs:value", "/action_graph/print.inputs:text")
```
그러면 `new_node_name`이라는 이름의 새로운 노드가 생긴다. 이 노드는 `Print Text Node`에 연결이 되며, 그래프 에디터에서 기존에는 2개인 노드가 3개로 늘어난 것을 확인할 수 있다.

### 그래프 실행(Execution)
기본적으로 그래프는 매 프레임마다 **Evaluation** 된다. 하지만 그래프가 자동으로 매 프레임 실행되는 대신 사용자가 명시적으로 호출했을 때만 실행이 되도록 변경할 수 있다(즉, 그래프를 직접 트리거 했을 때만 실행되도록 설정할 수 있다). 이를 위해 **`pipeline_stage`**라는 파라미터를 사용해서, **On Demand** 방식으로 설정할 수 있다.
1. 기존 그래프를 삭제하자.
2. 새로운 스크립트 에디터 창을 열고, 다음 코드를 작성하자.
```
(demand_graph_handle,_,_,_) = og.Controller.edit(
    {
        "graph_path": "/ondemand_graph",
        "evaluator_name": "execution",
        "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND
    },
    {
        keys.CREATE_NODES: [
            ("tick", "omni.graph.action.OnTick"),
            ("print","omni.graph.ui_nodes.PrintText")
        ],
        keys.SET_VALUES: [
            ("print.inputs:text", "On Demand Graph"),
            ("print.inputs:logLevel","Warning")
        ],
        keys.CONNECT: [
            ("tick.outputs:tick", "print.inputs:execIn")
        ],
    },
)
```
3. Run을 누르면 새로운 그래프 `/ondemand_graph`가 생성된다.
4. Play를 눌러 시작하면, On-demand 호출이 되도록 설정했기에 아무것도 출력이 되지 않는다.
5. 그래프를 실행하려면 스크립트 에디터에서 새로운 탭을 열고 다음 코드를 입력하면 된다.
```
demand_graph_handle.evaluate()
```
6. 콘솔에서 Run을 한번 누를 때마다 그래프가 실행이 된다.