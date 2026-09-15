# 87. Custom Python Nodes

권장 학습 순서 **87** · OmniGraph와 확장 개발 · 출처 ID `t107`

직접 작성한 `.ogn` schema와 Python compute를 가진 독립 확장을 제공한다. 입력 수가 0보다 큰지 판단하며 원문의 `output_bool`/`out` 불일치를 일관된 `output_bool`로 수정했다.

## 이 실습의 의도

`.ogn`의 typed 입력·출력 선언이 Python `compute(db)`의 데이터 읽기·쓰기로 연결되는 최소 노드를 만든다. 판정은 **입력이 엄밀히 0보다 큰가**이며, 결과 boolean과 계산 함수의 성공 반환값을 구분하는 것이 핵심이다. 확장을 켜면 노드 등록을 준비하고, 사용자가 Action Graph에 Korean Positive와 playback tick을 배치·연결한 뒤 Play해야 입력 판정이 실행된다.

## 실행 후 확인할 것

- 확장 `kr.positive.node`를 켠 뒤 Action Graph 검색에서 **Korean Positive**가 나타나는지 확인한다. 노드에 `execIn`, double형 `value_input`, bool형 `output_bool`이 있어야 `.ogn`과 구현이 올바른 이름으로 연결된 것이다.
- **On Playback Tick → execIn**을 연결하고 Play 중 `value_input`을 `-1 → 0 → 2`로 바꾼다. Property의 `output_bool`은 차례로 `False → False → True`여야 하며, 특히 0의 경계 결과를 확인한다.
- 출력이 False인 입력에서도 `compute()`의 `return True`는 정상 계산 완료를 뜻한다. 출력 False 자체를 노드 오류나 계산 실패로 해석하지 않는다.
- Pause 후 입력만 바꿨을 때 출력이 이전 값으로 남을 수 있음을 확인하고 Play 후 새 판정이 반영되는지 본다. 입력 필드 편집과 execution 신호를 받은 계산은 별개의 단계다.
- 비교식을 `>= 0`으로 바꾸는 확장 실험에서는 reload 후 입력 0이 True로 바뀌는지 확인한다. 등록 lifecycle을 다시 확인할 때는 노드를 쓰던 그래프를 새 Stage로 정리하고 확장을 껐다 켜며, 생성된 Database 파일을 직접 수정하지 않는다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 실행과 관찰

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.positive.node
```

1. `Window > Graph Editors > Action Graph`에서 New Action Graph를 만든다.
2. **On Playback Tick**과 **Korean Positive**를 검색하여 추가한다. tick→execIn을 연결한다.
3. value_input을 `-1`, `0`, `2` 순으로 바꾸고 Play 중 output_bool을 Property에서 확인한다. 각각 **False, False, True**여야 한다.
4. Pause 후 입력만 바꾸면 execution pulse가 없으므로 compute가 실행되지 않을 수 있다. Play하면 새 값이 출력된다.
5. extension을 껐다 켜면 node 등록도 lifecycle에 맞춰 수행된다. 기존 그래프가 해당 노드를 사용 중이면 먼저 새 Stage로 전환한다.

## 파일과 API

`.ogn`은 JSON이며 입력·출력 이름/타입과 UI 이름을 정의한다. `OgnPositive.py`의 클래스 `OgnPositive`와 schema의 `Positive`가 대응한다. `compute(db)`는 `db.inputs.value_input`을 읽고 `db.outputs.output_bool`에 쓴다. 반환 True는 **계산 성공**이며 출력 boolean 자체와 다르다. 입력 0에서는 출력 False여도 compute는 True를 반환해야 한다.

`omni.graph.core`는 활성화되는 extension의 Python module 트리에서 `.ogn`/구현을 검색하고 필요한 Database wrapper를 캐시에 생성·등록한다. 사용자가 생성된 `OgnPositiveDatabase.py`를 직접 고치지 않는다. `execIn`은 Action Graph 실행 신호이고, Push Graph에서는 데이터 평가 방식이 다르다.

한 변수 실험: 구현 비교식만 `> 0`에서 `>= 0`으로 바꾸고 hot reload 후 입력 0의 경계 결과가 달라지는지 확인한다. 노드 검색 실패는 확장 Enabled 상태와 Console의 OGN parse 오류를 확인한다. 쉼표/파일명/schema 출력명 불일치가 흔한 원인이다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html).
