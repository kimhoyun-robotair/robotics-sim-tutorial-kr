# 82. 그래프를 만드는 일과 실행하는 일 구분하기

## 이번에 배우는 것

**Python으로 같은 출력 동작의 두 그래프를 만들고, 재생에 따라 실행되는 그래프와 직접 평가하는 그래프를 비교합니다.**

노드를 만들고 값을 바꿨다고 그 노드가 바로 실행되는 것은 아닙니다. 그래프에는 “무엇을 계산할지”에 해당하는 구성과 “언제 계산할지”에 해당하는 평가 시점이 있습니다. 이번에는 로봇 대신 로그 한 줄을 사용해 그 차이를 관찰합니다.

| 구분 | 일반 그래프 | On-demand 그래프 |
|---|---|---|
| Stage 경로 | `/LessonGraph` | `/LessonDemand` |
| 시작 노드 | `OnPlaybackTick` | `OnTick` |
| 출력 문자열 | `normal playback graph` | `one demand evaluation` |
| 평가 요청 | 앱의 프레임 흐름 | `demand_graph.evaluate()` |
| 이 실습의 실행 조건 | Play 중 | Play 중에 명시적 평가 호출 |

두 그래프는 같은 `create_graphs.py`가 만듭니다. On-demand의 뜻은 자동 프레임 평가를 하지 않는다는 것입니다. 노드가 가진 Play 조건까지 사라지는 것은 아닙니다.

## 1. 두 그래프 생성하기

Isaac Sim 5.1.0 GUI에서 실행합니다. 저장소 루트의 터미널에서 앱을 시작하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 새 Stage를 엽니다.
2. **Window > Script Editor**를 엽니다.
3. 이 폴더의 `create_graphs.py` 전체를 열거나 붙여 넣고 Run합니다.
4. 출력 영역의 `Created /LessonGraph and /LessonDemand`와 Stage의 두 경로를 확인합니다.
5. **Window > Graph Editors > Action Graph**에서 각 그래프를 열어 `tick`과 `print` 노드를 확인합니다.

이 파일은 이미 실행 중인 앱에 그래프를 추가합니다. 일반 `python3`로 실행하거나 별도의 `SimulationApp`을 생성하는 파일이 아닙니다.

### 코드에서 볼 부분

`og.Controller.edit()`에 그래프 정보와 수행할 작업을 사전으로 전달합니다. 반복되는 키를 짧게 쓰기 위해 `keys = og.Controller.Keys`로 둡니다.

```python
keys.CREATE_NODES
keys.SET_VALUES
keys.CONNECT
```

각 키는 노드 생성, 입력값 설정, 포트 연결을 뜻합니다. 일반 그래프에서 실제 연결은 다음 한 줄입니다.

```python
("tick.outputs:tick", "print.inputs:execIn")
```

`print` 노드는 `inputs:text`에 문자열을 가지고 있지만, `execIn`으로 실행 신호가 와야 그 문자열을 출력합니다. 텍스트를 저장하는 것과 출력하는 것이 분리되어 있습니다.

### 실행 결과 확인하기

Play하면 일반 그래프의 `normal playback graph`가 매 재생 프레임마다 출력되고 Stop하면 멈춰야 합니다. 출력 수준이 `Warning`으로 설정되어 있으므로 앱 Console 또는 앱을 시작한 터미널에서 확인하세요. Script Editor 자체의 출력 영역에 모든 그래프 로그가 모이는 것은 아닙니다.

`Created ...`는 파일을 실행한 Python의 생성 완료 로그입니다. 이 한 줄이 보인 것만으로 PrintText가 평가되었다고 판단하지 마세요. On-demand 문자열은 Play만으로 반복 출력되지 않아야 합니다.

## 2. 입력값 수정과 명시적 평가 비교하기

먼저 Stop한 상태에서 Script Editor에 다음을 실행합니다.

```python
import omni.graph.core as og
attr = og.Controller.attribute("/LessonGraph/print.inputs:text")
print("old text:", attr.get())
attr.set("edited text")
```

`old text:`는 즉시 출력하지만 PrintText의 새 문자열은 다음 Play에서 확인합니다. 이후 Stop하고 상수 문자열 노드를 연결해 보세요.

```python
og.Controller.create_node("/LessonGraph/message", "omni.graph.nodes.ConstantString")
og.Controller.attribute("/LessonGraph/message.inputs:value").set("connected message")
og.Controller.connect("/LessonGraph/message.inputs:value", "/LessonGraph/print.inputs:text")
```

다시 Play하면 `connected message`가 출력되는지 확인하세요. 그래프에는 세 번째 노드와 데이터 연결이 추가됩니다. 이 ConstantString 노드는 값을 `inputs:value`에 두므로 위 연결 이름을 그대로 사용합니다. 같은 코드로 노드를 다시 만들기 전에 기존 `/LessonGraph/message`가 있는지 확인하세요.

### 코드에서 볼 부분

On-demand 그래프의 생성 설정에는 다음 값이 있습니다.

```python
{
    "graph_path": "/LessonDemand",
    "evaluator_name": "execution",
    "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND
}
```

이 값은 그래프를 프레임 자동 평가에서 분리합니다. **Play 상태를 유지한 채**, 생성 파일을 실행했던 Script Editor 환경에서 다음 한 줄을 실행하세요.

```python
demand_graph.evaluate()
```

`one demand evaluation`이 호출 한 번에 대응해 출력되는지 확인합니다. 여기의 `OnTick`은 `onlyPlayback=True`가 기본값이므로, Stop 상태에서 호출하면 출력이 없을 수 있습니다. **평가를 요청했는지와 시작 노드가 실행 조건을 만족하는지를 모두 확인해야 합니다.**

### 실행 결과 확인하기

| 한 행동 | 기대하는 결과 |
|---|---|
| `attr.set(...)`만 실행 | 저장된 입력 변경, PrintText 실행은 다음 tick까지 대기 |
| Play | 일반 그래프가 반복 출력 |
| Play 중 `demand_graph.evaluate()` 한 번 | On-demand 문자열 한 번 |
| Stop | 재생 조건의 출력 중단 |

일반 그래프의 반복 로그가 구별을 방해하면 생성 때 얻은 `normal_graph`에 다음을 적용할 수 있습니다.

```python
normal_graph.change_pipeline_stage(og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND)
```

이후 일반 그래프도 자동 평가에서 빠집니다. 여기까지 관찰한 뒤 Stop하세요. 그래프를 보존하려면 **File > Save As**로 Stage를 저장합니다. 이 실습은 CSV를 생성하지 않습니다.

## 3. 구성·데이터·평가의 관계 정리

```text
Controller.edit() → 그래프 구조와 초기 입력 구성
attribute.set()  → 저장된 입력값 변경
connect()        → 값을 공급할 경로 연결
Play / evaluate() → 조건에 맞는 실행 신호 → PrintText 출력
```

일반 그래프와 On-demand 그래프 모두 같은 PrintText 노드를 사용합니다. 차이는 출력 내용보다 평가를 요청하는 경로에 있습니다. Stage에 노드가 존재하는지, 데이터 선이 연결되었는지, 실제 실행 신호가 왔는지를 순서대로 보면 그래프가 조용한 이유를 좁힐 수 있습니다.

## 4. 간단한 확인 실험

On-demand 그래프의 **출력 문자열만** 바꿉니다.

```python
og.Controller.attribute("/LessonDemand/print.inputs:text").set("changed demand text")
```

Play 상태에서도 이 수정만으로 새 문자열이 나오는지 먼저 관찰하세요. 이어 `demand_graph.evaluate()`를 한 번 호출합니다. 자동 평가는 꺼져 있으므로 명시적 호출 뒤에 새 문자열이 나타나는 것이 비교 기준입니다. 그래프 경로나 pipeline stage는 바꾸지 않습니다.

## 실행할 때 막히면

- **`/LessonGraph exists` 또는 `/LessonDemand exists`**: 기존 그래프를 덮어쓰지 않는 보호입니다. 저장할 장면은 저장한 뒤 새 Stage에서 생성 파일을 실행하세요.
- **노드 타입을 찾을 수 없음**: `omni.graph.action`, `omni.graph.ui_nodes`가 활성화된 5.1 앱인지 확인하세요.
- **`evaluate()`를 호출해도 On-demand 로그가 없음**: 먼저 Play 상태인지 확인하세요. 시작 노드의 `onlyPlayback` 조건이 적용됩니다.
- **`demand_graph` 이름이 없음**: 생성 파일이 실행된 Script Editor 환경의 변수를 사용해야 합니다. 생성 파일을 새 Stage에서 실행한 뒤 같은 환경에서 후속 코드를 실행하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [OmniGraph via Python Scripting Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)에 대응합니다. 로컬 파일은 두 그래프를 한 번에 만들며, 일반 그래프에 `OnPlaybackTick`을 사용해 재생 조건을 분명하게 합니다.

이번 개정에서는 생성 코드와 설치된 노드 schema를 대조했습니다. 실제 Kit 그래프 평가와 Console 출력은 실행하지 않았고 `tutorial.json`은 `not_run`입니다. 파일의 문법이나 노드 존재 확인만으로 런타임 출력을 검증한 것은 아닙니다.
