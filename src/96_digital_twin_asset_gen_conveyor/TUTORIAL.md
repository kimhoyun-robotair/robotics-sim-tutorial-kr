# 96. t078 · Conveyor의 표면 속도와 Track Builder

권장 학습 순서 **96** · 환경 구축과 로봇 행동 · 출처 ID `t078`

컨베이어는 장면 전체가 이동하는 rigid body와 다르다. belt 표면 속도로 위 물체에 접촉 운동을 전달하고 texture animation은 움직이는 벨트를 시각적으로 표현한다. 이 패키지의 `conveyor_lab.usda`는 3m belt 표면과 0.5kg parcel, PhysX scene, 조명을 포함한 작은 독립 실험 장면이다. 아직 Conveyor OmniGraph를 붙이지 않았으므로 아래 단계가 실제 기능 구현 과정이다.

## 작은 belt부터 움직이기

1. `File > Open`에서 `conveyor_lab.usda`를 연다. `Window > Extensions`에서 `conveyor`를 검색하고 `isaacsim.asset.gen.conveyor.ui`를 Enable한다.
2. Stage에서 **`/World/Belt`만** 선택한다. `Create > Isaac Sim > Warehouse Items > Conveyor`를 실행한다. extension이 conveyor speed/animation을 관리하는 OmniGraph를 만든다.
3. 생성된 graph의 conveyor node에서 `conveyorPrim=/World/Belt`, `Direction=(1,0,0)`, `Curved=false`, `Enabled=true`, `Velocity=0.2`로 설정한다. node 하나에 prim 하나만 연결한다. Belt가 rigid body가 아니면 extension이 필요한 기본 설정을 추가한다.
4. Play를 누른다. `/World/Parcel`이 belt 위에 떨어진 뒤 +X 방향으로 이동해야 한다. belt 자체가 통째로 자유낙하하거나 parcel이 통과하면 graph 대상과 rigid/collider 구성을 확인한다.
5. graph prim의 speed 변수를 -0.2로 바꿔 방향이 반전되는지 관찰한다. 여러 belt 속도를 맞출 때는 `read_speed`가 같은 graph variable을 읽도록 연결한다. 처음에는 하나만 사용한다.
6. texture를 쓰는 자산에서는 `Animate Texture`, `Animate Direction`(UV), `Animate Scale`을 조절한다. provided lab은 단색이므로 texture 이동 관찰용이 아니다. contact 이동과 texture 이동이 각각 어떤 설정에 의존하는지 구분한다.

## Digital Twin Track Builder 실습

1. 새 stage에서 `Tools > Conveyor Track Builder`를 연다. 기본 Digital Twin conveyor asset pack에 접근할 수 있어야 한다.
2. Style을 Belt/Roller/Dual 중 하나로 좁히고 Start, Straight, End와 curvature/elevation filter를 사용해 첫 track을 넣는다. 기존 track을 선택하면 `Selected Endpoint`에서 비어 있는 출구를 고를 수 있다.
3. 출구를 선택하고 straight를 추가한 뒤 90도에 해당하는 Half curvature track을 연결한다. endpoint가 이미 연결되면 후보 목록에서 빠진다. 필요하면 New Track의 입력 anchor, variant, mirror를 조정한다.
4. 시작 조각, 직선, 회전, 끝 조각 순으로 연결한 결과를 위에서 확인한다. 생성기는 자유로운 결합을 허용하므로 작은 정렬 보정이 필요할 수 있다.
5. `Edit > Preferences > Conveyor Builder`에서 assets 폴더와 metadata JSON을 확인한다. 기본 원격 자산 대신 로컬 dataset으로 바꾸려면 모든 track USD가 지정한 폴더 바로 아래 있어야 한다. 복귀는 `Reset To Default`다.

## dataset/API 계약

각 USD는 defaultPrim이 있어야 하고 그 transform의 이동·회전은 0이어야 한다. track은 Xform parent 아래 visual/collision mesh를 모은다. 입구는 원점, track은 X축 방향, 가운데는 Y=0이며 anchor는 Z=0의 끝점에 놓는다. track별 material을 분리해야 개별 texture animation이 다른 track에 전파되지 않는다.

metadata JSON의 `assets` key 아래에는 확장자를 뺀 파일 이름이 온다. `style`, `start_level`, `angle`, `curvature`, `ramp`, `type`, `anchors`, `conveyor_nodes`가 UI filter와 node 생성에 쓰인다. `anchors`의 빈 문자열은 root 입구, `/Anchorpoint`는 자식 출구 경로다. 실제 완전한 예시는 설치본 `exts/isaacsim.asset.gen.conveyor.ui/data/track_types.json`에 있다. 원문의 주석 달린 JSON은 설명용이므로 JSON 파일에 그대로 붙이지 않는다.

`Curved=true`에서는 Direction을 선속도 벡터로 해석하지 않고 회전축으로 사용한다. 기본 `(0,0,1)`은 Z축 회전이다. 축 크기는 원본 convention에 따라 회전 효과를 바꾸므로 straight belt의 velocity와 같은 의미로 비교하지 않는다.

한 변수 실험은 Velocity 부호만 바꾸는 것이다. 성공은 parcel의 이동 방향 반전이다. 저장은 `File > Save As > output/conveyor.usd`의 새 경로로 한다. 단순 shader animation을 물리 conveyor 성공으로 판단하지 않는다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
