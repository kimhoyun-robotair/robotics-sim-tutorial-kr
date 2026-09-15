# 87. 숫자가 양수인지 판단하는 Python 노드 만들기

## 이번에 배우는 것

**OmniGraph 노드의 입력·출력 선언을 Python 계산에 연결하고, 실행 신호와 계산 결과를 구분합니다.**

그래프에서 필요한 계산을 기본 노드로 표현하기 어렵다면 직접 노드를 만들 수 있습니다. 이번 계산은 `입력 > 0` 한 줄입니다. 계산을 작게 두면 파일 이름, 포트 타입, 실행 신호 중 어느 연결이 필요한지 분명하게 볼 수 있습니다.

| 파일 또는 포트 | 역할 | 이 실습의 값 |
|---|---|---|
| `OgnPositive.ogn` | 노드와 포트의 구조 선언 | 노드 이름 `Positive` |
| `OgnPositive.py` | 실제 비교 계산 | 클래스 `OgnPositive` |
| `execIn` | 계산을 시작하는 실행 입력 | playback tick에서 연결 |
| `value_input` | 비교할 숫자 | `double`, 기본 0.0 |
| `output_bool` | 양수 여부 | `bool` |

`.ogn`은 JSON 형식의 노드 설명 파일입니다. 타입을 포함한 입출력 구조를 먼저 정하고, Python의 `compute(db)`가 그 구조를 통해 데이터를 읽고 씁니다.

## 1. Action Graph에서 노드 실행하기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/87_tools_omnigraph_custom_python_nodes/exts" \
  --enable kr.positive.node
```

1. **Window > Graph Editors > Action Graph**를 열고 새 Action Graph를 만듭니다.
2. **On Playback Tick**과 **Korean Positive**를 검색하여 추가합니다.
3. On Playback Tick의 `tick` 출력을 Korean Positive의 `execIn`에 연결합니다.
4. Korean Positive를 선택하고 Property에서 `value_input`을 -1로 정합니다.
5. 타임라인 **Play**를 누르고 `output_bool`을 확인합니다.
6. 재생을 유지한 채 입력을 0, 2 순서로 바꿉니다.

이 노드에는 다음 노드로 넘길 실행 출력이 없습니다. 이번에는 자신의 boolean 결과를 Property에서 관찰합니다. 관찰을 마치면 Pause하고 앱을 닫으세요. 그래프를 보관하려면 별도로 USD를 저장해야 합니다.

### 실행 결과 확인하기

| `value_input` | `output_bool` | 해석 |
|---:|---|---|
| -1 | False | 0보다 작음 |
| 0 | False | 0은 엄밀한 양수가 아님 |
| 2 | True | 0보다 큼 |

Pause한 다음 입력을 -1로 바꾸어 보세요. 출력은 아직 이전 계산값을 보여줄 수 있습니다. 다시 Play했을 때 False로 갱신되는지 확인합니다. **필드 값을 바꾸는 동작과 실행 입력을 받아 계산하는 동작이 따로 있기 때문**입니다.

## 2. 선언한 포트가 계산 코드로 이어지는 과정

두 노드 파일은 `exts/kr.positive.node/kr_positive_node/ogn/`에 있습니다.

### 코드에서 볼 부분

`OgnPositive.ogn`의 입력과 출력에는 다음 선언이 들어 있습니다.

```json
"value_input": {
  "type": "double",
  "default": 0.0,
  "description": "Number to compare"
}
```

```json
"output_bool": {
  "type": "bool",
  "description": "True exactly when input > 0"
}
```

`value_input`은 숫자 데이터이고 `execIn`은 실행 신호입니다. `double` 대신 `execution` 타입을 가진 신호 포트에 숫자 2를 넣어 계산하는 방식이 아닙니다.

구현은 다음과 같습니다.

```python
class OgnPositive:
    @staticmethod
    def compute(db):
        db.outputs.output_bool = db.inputs.value_input > 0.0
        return True
```

`db`는 노드 데이터를 읽고 쓰는 창구입니다. `db.inputs.value_input`과 `db.outputs.output_bool`의 이름이 선언 파일과 정확히 맞아야 합니다. `@staticmethod`는 이 계산이 별도의 `self` 인수 없이 호출된다는 뜻입니다. 비교 결과는 오직 현재 입력에 따라 결정되고 이전 입력을 누적하는 코드는 없습니다.

**`return True`는 “계산을 정상적으로 마쳤다”는 뜻입니다.** 입력이 -1일 때는 출력이 False여도 함수는 True를 반환합니다. 두 boolean은 서로 다른 질문에 답합니다.

### 설정에서 볼 부분

`config/extension.toml`은 `omni.graph.core`와 `omni.graph.action`을 의존성으로 두고 `kr_positive_node` 모듈을 불러옵니다. OmniGraph의 확장 등록 과정이 모듈 아래 노드 파일을 찾아 필요한 Database 코드를 생성·등록합니다.

파일 이름 `OgnPositive.py`, 클래스 `OgnPositive`, 선언의 `Positive`를 함께 보세요. `Ogn` 접두사가 붙는 위치를 맞춰야 등록 과정이 계산 구현을 찾을 수 있습니다. 자동 생성되는 Database 파일은 편집 대상이 아닙니다.

### 실행 결과 확인하기

Graph 검색 결과의 **Korean Positive**는 선언의 `metadata.uiName`에서 정한 표시 이름입니다. 표시 이름이 보이는 것은 등록 확인이고, -1·0·2 결과가 맞는 것은 계산 확인입니다.

확장 코드를 다시 불러오는 과정을 확인하려면 먼저 새 Stage로 전환해 해당 노드를 쓰는 그래프를 정리한 뒤 `kr.positive.node`를 껐다 켜세요. 모듈을 다시 불러오고 그래프를 만들었을 때 같은 포트와 결과가 나타나는지 확인합니다.

## 3. 실행 신호와 boolean 결과 정리

```text
Play → On Playback Tick.tick → execIn
                                  ↓
value_input → compute(db) → output_bool
                  └→ return True: 계산 완료 보고
```

Action Graph에서는 **언제 계산할지**를 실행 선으로 연결하고, **무엇을 계산할지**를 데이터 입력으로 정합니다. 값이 False인 것과 노드가 실행되지 않은 것은 출력 하나만 보면 구별하기 어려우므로 경계 입력을 바꾸고 재생 상태까지 함께 확인해야 합니다.

## 4. 간단한 확인 실험

`OgnPositive.py`의 비교 연산자 **`>`만 `>=`로** 바꾸세요. 저장 후 새 Stage에서 확장을 다시 불러오고 앞의 그래프를 만듭니다.

입력 -1과 2의 결과는 그대로이고 **입력 0만 False에서 True로** 바뀌어야 합니다. 이때 `.ogn`의 설명에는 여전히 엄밀한 양수라고 적혀 있습니다. 실험을 마치면 코드를 되돌리세요. 실제 기능을 바꾸어 배포한다면 포트 설명도 새 조건과 맞춰야 합니다.

## 실행할 때 막히면

- **Korean Positive가 검색되지 않음:** 확장 Enabled 상태와 Console의 OGN 등록 오류를 확인하세요. `.ogn` JSON의 쉼표와 파일·클래스 이름도 확인합니다.
- **입력을 바꿔도 출력이 그대로임:** tick → execIn 연결과 Play 상태를 확인하세요. Action Graph에 노드를 배치한 것만으로 실행 신호가 생기지는 않습니다.
- **`db.outputs`의 속성을 찾지 못함:** 출력 이름이 `output_bool`인지 확인하세요. 선언과 구현이 다른 이름을 쓰면 연결되지 않습니다.
- **False가 오류처럼 보임:** 입력이 0 이하라면 정상 결과입니다. Console 오류 여부와 `compute` 반환 의미를 구분하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Custom Python Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html)에 대응합니다. 로컬 예제는 입력 숫자의 양수 여부를 계산하며 선언과 구현에서 `output_bool`이라는 동일한 이름을 사용합니다.

이번 개정에서는 JSON 선언, Python 비교식과 확장 의존성을 대조했습니다. 실제 Kit의 OGN 생성·등록과 Action Graph 평가 결과는 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
