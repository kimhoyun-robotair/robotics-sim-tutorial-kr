# 94. t079 · 창고의 시각 자산을 물리 variant로 만들기

권장 학습 순서 **94** · 환경 구축과 로봇 행동 · 출처 ID `t079`

NVIDIA Assets에서 참조로 가져온 시각용 box pile에 개별 rigid body/collider를 작성한다. local `apply_box_physics.py`는 **Script Editor에서 현재 선택한 pile의 직접 자식들을 각각 box로 간주하여** physics를 붙이는 보조 구현이다. 선택한 자식이 실제로 독립 box인지 먼저 Stage에서 확인해야 한다. 자동으로 모든 asset의 의미를 판별하지 않는다.

## 이 실습의 의도

창고에서 보기만 하던 box pile을 상자별로 떨어지고 부딪히는 물리 자산으로 바꾸며 reference와 현재 edit layer의 역할을 익힌다. pile 전체가 한 몸체로 움직이지 않도록 직접 자식마다 강체를, 그 아래 mesh/cube마다 collider를 작성하는 구성이다. 스크립트는 선택한 자산에 물리 속성만 추가하므로 자산 가져오기·단위 확인·지면 추가·Play·새 USD 저장은 GUI에서 수행한다.

## 실행 후 확인할 것

- **대상과 크기:** Stage에서 선택한 pile root의 직접 Xformable 자식 하나가 실제 상자 하나인지 확인한다. import parent를 바꾸거나 reparent한 뒤에도 의도한 실제 크기가 유지되어야 한다.
- **속성이 쓰인 위치:** Script Editor의 `Rigid box: <경로>`마다 해당 자식에 `RigidBodyAPI`가 있고, 하위 mesh/cube에 `CollisionAPI`가 있는지 Property에서 확인한다. mesh에는 `convexHull` 근사가 적용된다.
- **개별 접촉 반응:** Ground Plane을 추가하고 Play한 뒤 아래 상자를 움직이면 다른 상자가 각각 중력과 접촉에 반응하는지 본다. pile이 통째로 움직이거나 상자가 지면을 통과하면 성공 기준을 충족하지 못한 것이다.
- **저장과 재사용:** `output/pile_physics.usd`로 Save As한 뒤 Layer에서 원본 reference와 현재 layer의 physics 작성 내용을 확인한다. 스크립트의 완료 메시지는 속성 작성 완료이며 낙하 시험이나 파일 저장 완료를 뜻하지 않는다.
- **선택 오류의 의미:** root를 하나만 선택하지 않았거나 직접 Xformable 자식이 없으면 중단된다. 반대로 `Rigid box` 출력이 있더라도 자식 아래에 지원 대상 mesh/cube가 없으면 collider가 작성되지 않으므로 출력 수만으로 물리 구성을 판단하지 않는다.

## 창고 조립과 단위 확인

1. `Window > Browsers > NVIDIA Assets`를 연다. `Industrial > Buildings > Warehouse`에서 `Warehouse01`을 찾는다. Stage의 `/World`로 drag하면 해당 parent 원점에 reference가 들어간다. viewport에 drag하면 마우스로 놓은 위치가 사용된다.
2. 선반·racks를 찾아 배치한다. meter 기준 stage에 centimeter 단위로 제작된 일부 NVIDIA Assets를 넣으면 100배 커 보일 수 있다. Properties에서 실제 크기를 확인한 뒤 해당 import parent에 scale `(0.01,0.01,0.01)`을 적용한다. 이미 meter 자산이면 다시 축소하지 않는다.
3. 원본 asset 자체는 시각만 제공할 수 있다. `SimReady`는 semantic labeling과 physics 설정을 갖춘 curated 자산 범주지만 실제 사용한 prim의 schema를 확인한다. 보이는 mesh와 물리 collider는 별개의 설정이다.

## WarehousePile_A04 물리 variant

1. 새 stage에 `/World/Import` Xform을 만들고 scale 0.01을 준다. `NVIDIA Assets`에서 `WarehousePile_A04`를 찾아 그 아래로 drag한다.
2. source reference를 유지한 채 box가 독립 자식인지 확인한다. 원문처럼 Stage의 Show Root를 켜고 pile을 root로 옮겨 `Set as Default Prim`을 할 수 있다. **reparent 후 world 크기가 유지되는지** 확인한다. parent에만 있던 0.01 scale이 사라지면 pile에 동일 scale을 적용하여 보존한다.
3. GUI 방식은 box 자식들을 선택하고 `Add > Physics > Rigid Body with Colliders` preset을 적용한다. 코드 방식은 pile root 하나를 선택한 뒤 `Window > Script Editor`에서 `apply_box_physics.py`를 열어 Run한다. script는 root의 각 직접 Xformable 자식에 RigidBodyAPI, 하위 mesh/cube에 CollisionAPI, mesh에 convexHull approximation을 붙인다.
4. `Create > Physics > Ground Plane`을 추가하고 Play한다. 아래쪽 box를 Shift-click drag하여 나머지가 접촉·중력에 따라 쓰러지는지 본다. 전체 pile 하나가 통째로 움직이면 rigid body를 parent에만 넣었는지 확인한다.
5. Stop 후 material friction 또는 box mass 하나를 바꾸고 새 이름 `output/pile_physics.usd`로 Save As한다. 원본 NVIDIA 파일은 수정하지 않는다.
6. Layer 탭에서 root layer를 우클릭하여 Edit한다. 외부 reference와 locally authored physics attributes가 함께 있는지 읽는다. ground plane을 실험용으로 추가했다면 재사용용 variant에 지면을 포함할지 명시적으로 결정한다.

## USD와 물리 API

USD reference는 기존 asset 내용을 합성하고, edit layer는 바뀐 값만 더 강하게 적용한다. defaultPrim은 다른 stage에서 참조할 대표 prim이다. 변형 layer에 physics를 작성하면 원본 visual asset을 교체하지 않고 여러 용도의 variant를 유지할 수 있다. `UsdPhysics.RigidBodyAPI`는 운동 단위, `CollisionAPI`는 접촉 검출, `MeshCollisionAPI`는 mesh 근사 방식을 정의한다. convex hull은 box에 적당한 단순 근사이나 안이 빈 선반처럼 오목한 구조를 그대로 보존하지 않는다.

한 변수 실험은 아래쪽 box 한 개 mass만 바꾸고 동일한 외력/낙하를 관찰하는 것이다. 여러 mass와 friction을 동시에 바꾸지 않는다. 시뮬레이션 성공은 개별 box의 접촉 반응으로 확인한다. Script Editor는 이미 열린 Kit 환경에서 실행하므로 `python3 apply_box_physics.py`로 실행하지 않는다. 선택 오류가 나면 pile root와 직접 자식 구조를 확인한다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/tutorial_static_assets.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
