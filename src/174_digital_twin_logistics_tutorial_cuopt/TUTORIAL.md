# 174. 창고 그림을 운송 경로 문제로 바꾸기

## 이번에 배우는 것

**통로·주문·차량 용량을 cuOpt 입력으로 구성하고, 서비스가 반환한 경로를 장면과 대조합니다.**

창고에 선반과 차량을 배치했다고 최적화할 문제가 완성되지는 않습니다. 차량이 어디로 이동할 수 있는지, 어느 위치에 물건을 얼마나 배달할지, 한 대에 얼마나 실을지를 따로 표현해야 합니다. 이번에는 작은 네트워크에서 시작해 창고 운송까지 네 가지 GUI 예제를 연결합니다.

| 실습 | 새로 표현하는 정보 | 확인할 결과 |
|---|---|---|
| Create Network | 통행 지점과 연결 | 저장된 node·edge |
| Simple Cost Matrix | 방문지 사이 이동 비용과 차량 용량 | 방문 순서와 차량별 경로 |
| Simple Waypoint Graph | 실제로 연결된 통로 | graph edge를 따르는 경로 |
| Intra-warehouse Transport | 창고 장면과 비용 구역 | 구역 변경 후 경로·비용 |

`lab_cases.json`은 GUI에 입력할 작은 실험 조건입니다. 서비스 요청 파일이나 계산된 정답 경로가 아니며, 자동으로 읽는 실행기도 없습니다.

## 1. 네트워크를 만들고 작은 운송 문제 풀기

Isaac Sim 5.1 GUI와 지원 RTX GPU·드라이버가 필요합니다. 저장소 루트에서 앱을 실행하세요.

```bash
~/isaacsim/isaac-sim.sh
```

**Window > Extensions**에서 `omni.cuopt.examples`를 켭니다. 서비스·시각화 확장도 함께 활성화되는지 확인하세요. **SOLVE를 실행하려면 실제 호환 cuOpt endpoint가 필요합니다.** [cuOpt 서버 안내](https://docs.nvidia.com/cuopt/user-guide/latest/cuopt-server/quick-start.html)를 참고해 준비하되, 현재 서버 API와 5.1의 `omni.cuopt.service`가 맞는지 확인하고 버전을 기록합니다. 네트워크 편집은 서비스 연결 전에 살펴볼 수 있습니다.

### 설정에서 볼 부분

먼저 **File > New**로 새 장면을 만들고 **cuOpt > Create Network**를 엽니다.

1. CREATE NODE로 지점 4개를 만듭니다.
2. Property의 Transform에서 위치를 차례로 `(0,0,0)`, `(4,0,0)`, `(4,4,0)`, `(0,4,0)`에 놓습니다.
3. 두 지점씩 선택하고 CREATE EDGE로 `0–1`, `1–2`, `2–3`, `3–0`을 연결합니다.
4. 이 튜토리얼의 새 `output/network.usd` 경로에 Save As합니다. 다시 열어 네 지점과 닫힌 연결이 유지되는지 확인하세요.

이제 새 장면에서 **cuOpt > Simple Cost Matrix**를 엽니다. 실제 서비스 연결·인증 정보를 UI에 설정하고 다음 값을 넣으세요.

| 입력 | 값 | 의미 |
|---|---|---|
| Fleet Size | 2 | 사용할 수 있는 차량 수 |
| Vehicle Capacity | 4 | 차량 한 대가 담당할 수 있는 수요 |
| Number of Locations | 6 | 수요가 1인 방문지 수 |
| Solver Time Limit | 5초 | 최적화에 배정한 시간 |

SETUP PROBLEM을 누르면 depot를 표시하는 cone과 방문 sphere가 생성됩니다. 여기서는 총 수요 6을 총 용량 `2 × 4 = 8`로 나눌 수 있습니다. 다만 용량 조건을 만족한다는 사실만으로 경로 비용까지 결정되는 것은 아닙니다.

### 실행 결과 확인하기

SOLVE를 누른 뒤 응답의 텍스트 route와 viewport 경로를 함께 보세요.

- 방문지 6개가 경로에 포함되는지 확인합니다.
- 각 차량이 맡은 방문지의 수요 합이 4 이하인지 셉니다.
- depot 번호를 주문 위치로 잘못 세지 않았는지 확인합니다.
- 반환된 비용과 사용된 차량 수를 기록합니다.

Fleet Size는 사용할 수 있는 차량의 수입니다. 일반적으로 모든 차량을 반드시 쓰는 조건과는 다르지만, 이번 기본 문제에서는 수요 6이 한 대의 용량 4보다 커서 한 대만으로 모두 처리할 수 없습니다. 그림에 선이 생겼다는 사실만으로 최적성을 판단하지 말고 서비스 응답의 상태와 비용도 읽으세요.

## 2. 통로와 창고의 비용 구역으로 확장하기

### 설정에서 볼 부분

새 장면에서 **cuOpt > Simple Waypoint Graph**를 열고 **Waypoint Graph → Orders → Vehicles** 순서로 LOAD합니다. 처음에는 설치된 sample JSON으로 전체 흐름을 확인하세요. 앞서 저장한 network USD를 사용할 때는 장면에 연 뒤 LOAD SCENE을 사용합니다.

각 데이터의 역할은 다음과 같습니다.

| 데이터 | 주요 항목 | 장면과 연결되는 의미 |
|---|---|---|
| waypoint graph | `node_locations`, `graph` | 지점 좌표와 연결 가능한 이웃 |
| orders | `task_locations`, `demand` | 방문할 지점과 처리량 |
| vehicles | `vehicle_locations`, `capacities` | 출발 지점과 적재 한도 |

Open Source Code에서 설치본의 `waypoint_graph.json`, `orders_data.json`, `vehicle_data.json`을 확인할 수 있습니다. 설치본 파일명은 복수형 `orders_data.json`입니다. `lab_cases.json`은 이 데이터 스키마가 아니므로 LOAD JSON 버튼에 넣는 파일로 사용하지 않습니다.

SOLVE 후 경로가 graph edge를 따라가는지 확인하세요. 녹색 주문 지점과 Node_0 출발점을 연결해 읽습니다. 차량의 별도 mesh가 보이지 않아도 경로 계산 입력은 존재할 수 있습니다. Cost Matrix와 달리 waypoint graph는 어떤 통로가 연결되어 있는지 직접 표현합니다.

창고 장면은 다음 순서로 진행합니다.

1. 새 장면에서 **cuOpt > Intra-warehouse Transport Demo**를 엽니다.
2. **Sample Warehouse → Waypoint Graph → Orders → Vehicles** 순서로 LOAD합니다.
3. 한 번 SOLVE해 기본 경로와 비용을 기록합니다.
4. Semantic Zone을 Generate하고 특정 통로 edge를 덮도록 옮깁니다.
5. UPDATE로 변경된 구역을 비용에 반영한 뒤 SOLVE합니다.
6. 같은 zone을 옆으로 이동하고 UPDATE → SOLVE를 반복합니다.

Generate를 다시 누르면 기존 zone을 이동하는 대신 새 zone이 추가됩니다. 한 구역의 효과를 비교할 때는 동일한 zone 하나를 움직이세요.

### 실행 결과 확인하기

구역이 덮는 edge와 반환 경로·비용을 비교합니다. Semantic Zone은 이동 비용에 주는 페널티입니다. 물리 collider나 절대 통행금지와 같은 뜻은 아닙니다. 우회로가 더 비싸다면 경로가 그대로일 수 있고, 경로는 같아도 비용이 달라질 수 있습니다.

창고 건물·컨베이어·선반을 만드는 데이터와 통행 graph는 별도입니다. 화면에 빈 공간이 있다고 그 사이에 이동 edge가 자동으로 생기지는 않습니다. 경로가 예상과 다르면 시각적 배치뿐 아니라 graph 연결도 확인하세요.

## 3. 장면과 최적화 입력의 관계 정리

```text
창고 USD → 사람이 이해하는 공간 배치
통행 graph + 주문 수요 + 차량 용량 + 구역 비용
    → cuOpt 서비스의 실제 계산
    → 응답 경로·비용 → 장면 시각화와 대조
```

문제가 풀리지 않을 때는 서비스 연결 문제와 수학적으로 불가능한 입력을 나누어 확인합니다. 서버 인증 실패는 수요를 줄여 해결할 문제가 아니고, 끊긴 graph는 렌더링 품질을 높여 해결할 문제가 아닙니다.

## 4. 간단한 확인 실험

Simple Cost Matrix의 **Vehicle Capacity만 4 → 2**로 바꾸고 SETUP PROBLEM을 누르세요. Fleet Size 2와 입력한 방문지 6은 그대로 둡니다.

고정된 수요 6은 총 용량 `2 × 2 = 4`로 처리할 수 없습니다. 하지만 설치된 5.1 UI는 이 상황에서 `NOTE : AUTOMATIC VALUE CHANGE`를 표시하고 **방문지 수를 4개로 줄입니다.** SOLVE 전에 Number of Locations와 sphere 수가 바뀌었는지 확인하세요.

따라서 여기서 얻은 응답은 “6개 주문이 불가능하다는 서버 응답”과 다릅니다. `lab_cases.json`의 `expected_feasibility` 문장은 6개 수요를 고정한 수학적 조건이며, 실제 GUI의 보정 이후 입력과 구분해서 읽어야 합니다. 이 실험은 최적화 결과 전에 **실제로 전송된 문제가 무엇인지 확인하는 이유**를 보여 줍니다.

## 실행할 때 막히면

- **cuOpt 메뉴가 없음**: `omni.cuopt.examples`와 의존 확장의 로딩 로그·registry 접근을 확인하세요.
- **SOLVE에서 연결·인증 오류**: endpoint, 서비스 API 버전과 credentials를 확인하세요. Create Network가 동작해도 서비스가 연결된 것은 아닙니다.
- **방문지 수가 입력한 값과 다름**: SETUP PROBLEM의 자동 보정 메시지를 확인하세요.
- **경로가 통로와 맞지 않음**: USD 그림과 waypoint graph를 구분하고 실제 edge 연결을 살펴보세요.
- **zone을 옮겨도 결과가 같음**: UPDATE 수행 여부, 해당 edge를 사용하는지, 우회 비용을 함께 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [NVIDIA cuOpt](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/logistics_tutorial_cuopt.html)의 네 GUI workflow에 대응합니다. `lab_cases.json`의 입력 조건과 설치본 `costmat/extension.py`의 자동 보정 흐름을 대조했습니다.

이번 개정에서 GPU GUI 조작과 외부 서비스 요청은 실행하지 않았습니다. `tutorial.json`은 `not_run`이며, 경로·비용은 실제 서비스 실행 뒤 직접 확인할 결과입니다.
