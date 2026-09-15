# 174. t080 · cuOpt 네트워크부터 창고 운송까지

권장 학습 순서 **174** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t080`

원문에 있는 **네 가지 GUI workflow**를 모두 수행하는 패키지다. `lab_cases.json`에 네트워크 꼭짓점·연결과 작은 capacity 비교 조건을 담았다. 파일은 관찰 실험 명세이며 cuOpt HTTP 요청을 흉내 낸 결과가 아니다. 실제 최적화는 사용자가 준비한 NVIDIA cuOpt service가 계산해야 한다.

이 패키지는 이미 실행한 Isaac Sim GUI에서 실습합니다. 로컬 검사·설정 도구가 GUI 수명을 제한하지 않으며, 사용자가 창을 직접 닫을 때까지 유지됩니다.

## 추가 준비

[cuOpt server quickstart](https://docs.nvidia.com/cuopt/user-guide/latest/cuopt-server/quick-start.html)에 따라 실제 endpoint를 준비한다. Isaac Sim 5.1의 `omni.cuopt.service`와 호환되는 서버 API/인증 설정이 필요하다. 외부 `latest` 문서는 5.1에 고정되지 않으므로 사용하는 server 버전을 기록한다. 자격 증명은 UI에 입력하며 이 저장소에 저장하지 않는다. 작성 과정에서 서버 설치나 요청을 수행하지 않았다.

`Window > Extensions`에서 `omni.cuopt.examples`를 켠다. `omni.cuopt.service`, `omni.cuopt.visualization`도 함께 활성화된다. 이후 cuOpt 메뉴가 나타난다.

## 1. Create Network

1. Ctrl+N으로 새 stage를 만들고 `cuOpt > Create Network`를 연다.
2. CREATE NODE로 네 node를 만든다. Move 도구/Property Transform에서 `lab_cases.json`의 `(0,0,0)`, `(4,0,0)`, `(4,4,0)`, `(0,4,0)`에 둔다.
3. 두 node씩 선택하여 CREATE EDGE로 0-1, 1-2, 2-3, 3-0을 연결한다. node/edge visualization이 닫힌 순환 graph를 이루는지 확인한다.
4. `output/network.usd`에 Save As한다. 이후 LOAD SCENE 입력으로 재사용할 수 있다. Open Source Code로 scene node를 graph 데이터로 읽는 구현을 확인한다.

## 2. Simple Cost Matrix

1. 새 stage에서 `cuOpt > Simple Cost Matrix`를 연다. 실제 service credentials/endpoint를 UI에서 설정한다.
2. Fleet Size=2, Vehicle Capacity=4, Number of Locations=6, Solver Time Limit=5초를 넣고 SETUP PROBLEM을 누른다. cone은 depot, sphere는 demand 1의 방문지다.
3. SOLVE를 누른 뒤 텍스트 route와 viewport route를 비교한다. 모든 방문지가 포함되고 차량별 방문 수가 capacity를 넘지 않는지 수작업으로 센다. fleet size는 최대 수이므로 반드시 두 대를 써야 하는 것은 아니다.
4. Capacity만 2로 바꾸고 같은 6개 demand 조건을 다시 구성한다. 총 capacity 4로 demand 6을 처리할 수 없으므로 infeasibility를 어떻게 보고하는지 확인한다. 무조건 성공 route를 출력하는 것은 올바른 검증이 아니다.

## 3. Simple Waypoint Graph

1. 새 stage에서 해당 메뉴를 연다. LOAD JSON 또는 앞서 저장한 network USD를 Stage로 가져와 LOAD SCENE을 누른다. 처음에는 제공 sample graph로 전체 흐름을 익힌다.
2. Waypoint Graph → Orders → Vehicles 순서로 LOAD한다. order 지점은 녹색, vehicle은 Node_0에서 시작하지만 별도 차량 mesh가 보이지 않을 수 있다.
3. SOLVE하고 returned routes가 graph edge를 따라가는지 확인한다. 직선 거리 cost matrix와 달리 graph는 벽·통로 연결을 표현한다.
4. Open Source Code로 `wpgraph/extension_data/waypoint_graph.json`, `orders_data.json`, `vehicle_data.json`을 확인한다. 5.1 설치본은 **orders_data.json**이며 본문의 일부 단수 `order_data.json` 표기와 다르다. `node_locations`와 `graph` adjacency, `task_locations`/`demand`, `vehicle_locations`/`capacities` 스키마를 읽는다. LOAD JSON은 설치본 sample 경로를 사용하므로 `lab_cases.json`을 임의로 해당 버튼에 넣는 기능은 없다.

## 4. Intra-warehouse Transport

1. 새 stage에서 `cuOpt > Intra-warehouse Transport Demo`를 연다. Sample Warehouse → Waypoint Graph → Orders → Vehicles 순서로 LOAD한다.
2. warehouse building/conveyors/shelves JSON이 scene을 구성하고 waypoint graph가 통행 network를 따로 정의한다. 시각적으로 빈 공간이라고 자동으로 통행 edge가 생기지는 않는다.
3. Semantic Zone을 Generate하여 한 통로 edge를 덮도록 옮긴다. UPDATE를 눌러 현재 위치에 따른 edge cost를 반영한 다음 SOLVE한다.
4. zone을 옆으로 옮기고 UPDATE → SOLVE를 반복한다. route 또는 cost가 달라지는지 비교한다. Generate를 다시 누르면 기존 zone 이동이 아니라 **새 zone 추가**이므로 처음 실험은 하나만 유지한다.

`omni.cuopt.service`는 scene 문제를 요청으로 변환하고 service와 통신한다. `omni.cuopt.visualization`은 graph/warehouse/semantic zone을 표시하며 zone 주변 edge 비용을 조정한다. semantic zone은 비용 페널티이며 물리 collider나 절대 통행금지와 같은 뜻이 아니다. scene USD와 route 최적화 입력을 별도로 이해해야 한다.

해결 실패 시 endpoint/API 호환, credentials, graph 연결, demand/capacity를 구분해서 확인한다. render된 선이 있다고 최적해라고 가정하지 않는다. 제한시간을 늘릴 때는 동일 문제와 objective 값을 비교한다. 실제 서버 없이는 Create Network 실습까지는 가능하지만 SOLVE 결과 검증은 미실행이다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/logistics_tutorial_cuopt.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
