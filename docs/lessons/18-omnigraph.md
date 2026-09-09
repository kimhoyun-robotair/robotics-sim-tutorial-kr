# 18단계. OmniGraph를 GUI와 Python에서 구성하기

**목표:** 노드, 입력·출력 포트, 실행 연결을 이해하고 Python으로 만든 그래프를 GUI에서 확인한다. ROS 2 연결 전에 문자 출력 두 노드로 연습한다.

## 선을 연결하기 전에 구분하기

| 요소 | 이 실습의 예 | 역할 |
|---|---|---|
| Graph | `/World/TutorialGraph` | 관련 노드의 실행 구조를 담음 |
| Node | Tick, Print | 이벤트 생성 또는 실제 작업 수행 |
| 데이터 입력 | `Print.inputs:text` | 출력할 문자열 전달 |
| 실행 입력 | `Print.inputs:execIn` | 언제 작업할지 전달 |
| 실행 출력 | `Tick.outputs:tick` | 연결된 다음 노드의 실행을 요청 |

데이터 포트에 값이 있다고 노드가 반드시 실행되는 것은 아니다. ROS 2 Publisher에 topic 이름과 데이터만 채우고 실행 입력을 연결하지 않으면 발행이 시작되지 않는 경우와 연결해서 이해한다. 반대로 실행 선만 연결하고 필요한 데이터가 없으면 실행 중 오류가 날 수 있다.

## GUI에서 노드를 찾아보다

1. 새 Stage를 만들고 Stop을 누른다.
2. `Window > Graph Editors > Action Graph`를 연다.
3. 노드 검색에서 `On Tick`과 `Print Text`를 찾아본다.
4. 노드의 포트 이름과 설명을 확인한다. 이 단계에서는 검색만 하고, 실제 그래프는 아래 코드로 동일하게 생성한다.

공식 6.0.1 Python 튜토리얼은 `omni.graph.action.OnTick`과 `omni.graph.ui_nodes.PrintText`를 사용한다. GUI에 표시되는 이름과 Python의 노드 타입 문자열이 다르다는 점에 주의한다. [공식 OmniGraph via Python Scripting](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omnigraph/omnigraph_scripting.html)

## Python으로 동일한 그래프를 생성하기

Script Editor에서 아래 **전체 코드**를 실행한다. 외부 터미널용 코드가 아니다.

```python
import omni.graph.core as og
import omni.timeline
import omni.usd

if not omni.timeline.get_timeline_interface().is_stopped():
    raise RuntimeError("Stop 후 그래프를 생성한다.")

stage = omni.usd.get_context().get_stage()
path = "/World/TutorialGraph"
owner = "tutorial.omnigraph"
old = stage.GetPrimAtPath(path)
if old:
    if old.GetCustomDataByKey("tutorialOwner") != owner:
        raise RuntimeError("다른 그래프가 이 경로를 사용한다.")
    stage.RemovePrim(path)

keys = og.Controller.Keys
graph, nodes, _, _ = og.Controller.edit(
    {"graph_path": path, "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("Tick", "omni.graph.action.OnTick"),
            ("Print", "omni.graph.ui_nodes.PrintText"),
        ],
        keys.SET_VALUES: [
            ("Print.inputs:text", "Tutorial graph is running"),
            ("Print.inputs:logLevel", "Warning"),
        ],
        keys.CONNECT: [("Tick.outputs:tick", "Print.inputs:execIn")],
    },
)
stage.GetPrimAtPath(path).SetCustomDataByKey("tutorialOwner", owner)
print("그래프 생성 완료:", path)
```

`Warning`은 이 학습용 메시지를 Console에서 쉽게 찾기 위한 로그 수준이다. 문장이 Warning으로 보인다고 물리 엔진에 오류가 생겼다는 뜻은 아니다. 실제 오류와 혼동하지 않도록 출력 문장을 읽는다.

## 연결을 눈으로 확인하기

1. Stage에서 `/World/TutorialGraph`를 선택한다.
2. Action Graph 편집기의 그래프 선택 기능으로 해당 그래프를 연다.
3. Tick과 Print 사이 실행 선이 있는지 확인한다.
4. Play를 누르고 Console 또는 터미널에서 문장을 확인한다.
5. 확인 후 Stop을 누른다. 로그가 계속 쌓이게 방치하지 않는다.

그다음 Script Editor에서 입력값만 바꾼다.

```python
og.Controller.set(
    og.Controller.attribute("/World/TutorialGraph/Print.inputs:text"),
    "Updated from Python",
)
```

다시 Play하면 새 문장이 출력되어야 한다. 그래프 구조를 다시 생성하지 않고 입력 속성만 변경한 것이다. GUI Property에서 같은 입력값도 확인한다.

## 요청할 때 한 번만 평가하기

앞서 만든 `graph` 변수가 있는 Script Editor 탭에서 Stop 후 다음을 실행한다.

```python
graph.change_pipeline_stage(og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND)
```

이제 Play를 눌러도 이 그래프는 자동으로 반복 평가되지 않는다. Play 상태에서 다음을 한 번 실행한다.

```python
graph.evaluate()
```

문장이 한 번 출력되는지 확인하고 Stop을 누른다. 이 예제는 공식 튜토리얼의 on-demand 흐름을 작은 그래프로 적용한 것이다. 센서나 ROS 2 그래프를 on-demand로 바꾸면 발행 주기도 달라지므로 학습용 그래프에서만 시도한다.

## 자주 생기는 문제

- 노드 타입을 찾지 못하면 Extension Manager에서 OmniGraph 관련 확장과 Print Text 노드 제공 확장이 준비되었는지 확인한다. 이름을 추측해서 다른 노드로 치환하지 않는다.
- 출력이 없으면 Play 상태, `execIn` 연결, 그래프 평가 모드, Console 필터를 차례대로 확인한다.
- 출력 횟수가 물리 스텝 수와 다를 수 있다. On Tick은 물리 Post Step 콜백의 대체물이 아니다. 센서·제어 주기는 해당 이벤트와 실제 발행률로 따로 검증한다.
- `graph`를 찾지 못하면 다른 Script Editor 탭이나 새 실행 환경을 사용한 것은 아닌지 확인한다. 전체 생성 코드를 Stop 상태에서 다시 실행한다.

**완료 기준:** Python으로 만든 두 노드와 실행 선을 GUI에서 확인하고, 반복 평가와 수동 1회 평가를 각각 실행한다.

**과제:** 그래프를 `artifacts/graph_demo.usda`로 저장하고 다시 연다. 그래프의 노드와 입력값은 USD에 남지만 Script Editor의 Python 변수 `graph`는 저장되지 않는다는 점을 확인한다. 이후 로봇 그래프는 [공식 Isaac Sim OmniGraph Tutorial](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/omnigraph/omnigraph_tutorial.html)의 구성을 참고한다.

[이전](17-project-scene-extension.md) · [학습 목차](../../README.md)
