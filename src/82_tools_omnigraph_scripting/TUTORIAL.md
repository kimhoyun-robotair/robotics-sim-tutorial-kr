# 82. OmniGraph via Python Scripting Tutorial

권장 학습 순서 **82** · OmniGraph와 확장 개발 · 출처 ID `t110`

Python Controller API로 두 그래프를 만들고, 속성 편집/노드 추가/연결/수동 평가를 차례로 수행한다. 그래프 화면과 Console 출력이 함께 확인 대상이다.

## 이 실습의 의도

같은 PrintText 동작을 일반 playback 그래프와 명시적으로 평가하는 on-demand 그래프에 넣어, **그래프를 만들거나 값을 바꾸는 일**과 **평가를 실행하는 일**을 구별한다. `create_graphs.py`는 실행 중인 Kit에 `/LessonGraph`, `/LessonDemand`를 생성하고 연결·초기 문자열을 설정하는 단계까지만 수행한다. 이후 Play, 속성 변경, ConstantString 연결, `evaluate()` 호출은 Script Editor에서 직접 진행하며 로봇이나 물리 장면을 만들지는 않는다.

## 실행 후 확인할 것

- 새 Stage에서 파일을 Run한 뒤 `Created /LessonGraph and /LessonDemand`와 두 Graph prim을 확인한다. 각 그래프에 `tick`, `print`가 있는지 Action Graph에서 열어 보고, 생성 로그와 PrintText의 실행 로그를 구분한다.
- Play 중 `/LessonGraph`가 Warning 수준으로 `normal playback graph`를 반복 출력하고 Stop하면 멈추는지 확인한다. 반복 출력은 프레임마다 평가되는 의도한 동작이다.
- 속성을 직접 편집한 다음 Play 시 `edited text`가 나오는지, ConstantString을 연결한 다음에는 `connected message`가 나오는지 확인한다. 세 번째 `message` 노드의 존재뿐 아니라 실제 PrintText 입력을 바꾸는 데이터 연결을 함께 본다.
- `/LessonDemand`는 Play만으로 `one demand evaluation`을 반복 출력하지 않아야 한다. 생성 스크립트의 변수가 있는 환경에서 `demand_graph.evaluate()`를 한 번 호출해 해당 메시지 한 번과 대응시키며, 입력 수정만으로 실행되었다고 판단하지 않는다.
- 일반 그래프도 `GRAPH_PIPELINE_STAGE_ONDEMAND`로 바꾸면 Play 중 자동 출력이 멈추는지 확인한다. 같은 장면에서 생성 파일을 다시 실행할 때 기존 경로 오류가 나는 것은 두 그래프를 덮어쓰지 않도록 만든 보호 동작이다.

## 실행 환경

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더를 어디로 복사해도 다른 로컬 튜토리얼 없이 실행한다. 아래처럼 시작한 뒤 **Window > Script Editor**를 연다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Script Editor의 **File > Open**으로 본문의 Python 파일을 열고 **Run**을 누른다. 이 코드는 이미 실행 중인 Kit 안에서 동작하므로 별도의 `SimulationApp`을 만들지 않는다. 일반 시스템 `python3`에서 실행하는 파일이 아니다. Stage는 현재 USD 장면, prim은 장면의 경로로 식별되는 요소다. 같은 파일을 재실행할 때 기존 결과를 삭제하거나 덮어쓰지 않도록 해당 prim이 있으면 에러를 내는 예제를 사용한다.

## 실습

1. 새 Stage에서 `create_graphs.py`를 Run한다. `/LessonGraph`와 `/LessonDemand`가 생긴다. `Window > Graph Editors > Action Graph`에서 각각 연다.
2. Play하면 일반 그래프가 매 playback frame 로그를 쓴다. Stop하면 멈춘다. normal graph는 명확한 playback 동작을 위해 원문의 OnTick 대신 OnPlaybackTick을 사용한다.
3. 새 Script Editor 탭에서 다음을 실행한다.

```python
import omni.graph.core as og
attr = og.Controller.attribute("/LessonGraph/print.inputs:text")
print("old text:", attr.get())
attr.set("edited text")
```

4. Play 시 edited text가 출력되는지 본다. 다음 코드로 ConstantString 노드를 추가한다.

```python
og.Controller.create_node("/LessonGraph/message", "omni.graph.nodes.ConstantString")
og.Controller.attribute("/LessonGraph/message.inputs:value").set("connected message")
og.Controller.connect("/LessonGraph/message.inputs:value", "/LessonGraph/print.inputs:text")
```

5. 그래프에 세 번째 노드와 데이터 연결이 나타나는지 확인한다. Constant 노드는 값을 `inputs:value`에 두는 이 노드의 schema에 따른 연결이다.
6. Play 중에도 `/LessonDemand`는 자동 로그를 내지 않는다. 생성 스크립트를 실행한 같은 Script Editor 환경에서 `demand_graph.evaluate()`를 **한 번** 실행하면 한 번 출력된다.
7. `normal_graph.change_pipeline_stage(og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND)`로 바꾸고 자동 실행이 멈추는지 본다. 데이터 값 수정과 그래프 평가가 별도라는 점을 확인한다.

`og.Controller.edit`는 그래프 생성·노드·속성·연결을 선언형으로 묶는다. Keys.CREATE_NODES/SET_VALUES/CONNECT는 작업의 종류, evaluator_name=`execution`은 action 실행 방식이다. pipeline stage는 프레임 자동 평가인지 명시적 평가인지를 정한다. Graph prim과 node prim은 USD Stage에 존재하지만 execution pulse는 단순 숫자 데이터와 다르다.

한 변수 실험: demand graph text만 바꾼 뒤 evaluate 전/후 로그를 비교한다. 반복 로그가 많으면 Stop한다. 노드 타입 없음은 `omni.graph.action`과 `omni.graph.ui_nodes` extension 활성 상태를 확인한다. 원문의 더 긴 물리/렌더 callback 실험은 설치 파일 `standalone_examples/api/isaacsim.core.api/omnigraph_triggers.py`에서 확인할 수 있다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html).
