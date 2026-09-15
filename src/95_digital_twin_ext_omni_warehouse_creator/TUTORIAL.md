# 95. t077 · 모듈형 Warehouse Creator로 창고 외곽과 기둥 편집

권장 학습 순서 **95** · 환경 구축과 로봇 행동 · 출처 ID `t077`

직사각형 외곽에서 벽·내부 tile·기둥을 생성한 다음 벽의 용도와 기둥 배치를 바꾸는 **공식 GUI 실습**이다. `floor_plan.json`은 사용할 외곽 꼭짓점과 실험 순서를 tile 단위로 기록한 로컬 설계도다. 자동 warehouse generator를 흉내 낸 코드가 아니라 설치된 `omni.warehouse_creator`를 직접 조작한다.

## 이 실습의 의도

모듈형 자산의 격자에 맞춰 창고 외곽을 닫고, 생성된 구조의 벽 스타일과 내부 기둥을 전용 편집기로 변경하는 과정을 배운다. 4×3 tile 직사각형은 외곽 생성 결과를 쉽게 확인하면서 같은 구조 안에서 variant와 기둥 편집을 비교하기 위한 기준이다. 로컬 JSON은 사람이 따라 그릴 설계도이며 자동으로 읽어 창고를 생성하는 실행 파일은 제공하지 않는다.

## 실행 후 확인할 것

- **외곽과 바닥:** GUI에서 `vertices_tiles` 순서대로 그리고 Finish한 뒤 닫힌 직사각형 벽과 내부 바닥 tile이 생성되는지 본다. 4×3은 meter가 아닌 tile 수이므로 실제 크기는 선택한 dataset의 모듈 크기와 비교한다.
- **벽 variant:** Component 선택으로 직선 벽 하나의 style을 바꿨을 때 해당 벽이 loading dock/access 등 선택한 형태로 바뀌고 외곽은 유지되는지 확인한다.
- **기둥 Confirm:** `Edit Column Placement`에서 기둥 하나를 disabled로 바꾸면 편집 중 반투명 녹색으로 표시되고, Confirm 후 그 배치가 적용되는지 본다. 편집할 때 천장과 세부 요소가 숨겨지는 것도 이 모드의 일부다.
- **기둥 Cancel:** 다시 편집하여 Flip All을 누른 뒤 Cancel하면 직전에 Confirm한 기둥 배치가 유지되어야 한다. 편집 중 미리보기와 확정된 상태를 비교한다.
- **USD 저장:** `output/warehouse.usd`를 새로 저장하고 다시 열었을 때 벽 style과 확정한 기둥 상태를 확인한다. 참조 자산을 사용하는 결과이므로 dataset 연결이 끊긴 상태의 빈 장면을 정상 생성 결과로 판단하지 않는다.

## 순서대로 만들기

1. Isaac Sim에서 새 stage를 만든다. `Window > Extensions`에서 `Warehouse Creator`를 검색하여 `omni.warehouse_creator`를 설치/활성화한다. 이미 있는 버전은 5.1 환경에 맞는 것을 사용한다.
2. `Tools > Modular Warehouse Creator`를 연다. Dataset Source는 기본 원격 자산 또는 로컬 `[Isaac Sim Assets]/Isaac/Environments/Modular_Warehouse/Props`를 선택한다. 폴더 경로는 해당 Props 폴더 자체여야 한다.
3. `Build Warehouse`를 누른다. 나타나는 curve draw dialog는 직접 조작하지 않는다. drawing mode에서 viewport 클릭이 벽 segment가 된다.
4. `floor_plan.json`의 `(0,0) → (4,0) → (4,3) → (0,3) → (0,0)`을 tile 격자에 맞춰 반시계 방향으로 그린다. 이것은 meter 좌표 입력이 아니라 **4×3 tile 크기**의 도형 기준이다. 실제 길이는 선택한 dataset tile 크기를 따른다.
5. 시작점 가까이 마지막 점을 찍어 닫거나 마지막 점이 첫 점과 일직선이면 `Finish`를 누른다. 외곽이 닫히며 내부 tile이 채워져야 한다. 자기 교차 외곽은 지원되지 않는다.
6. viewport toolbar를 우클릭하여 Select Mode를 `Component`로 바꾼다. 직선 벽 block 하나를 고르고 Property의 style에서 loading dock/access 등 dataset이 제공하는 다른 variant를 선택한다. 같은 type을 다중 선택하면 선택한 block들에 같은 style이 적용된다.
7. floor plan prim을 선택하고 `Edit Column Placement`를 누른다. 천장과 세부 요소가 숨겨진다. 내부 기둥 하나를 클릭하여 disabled 상태의 반투명 녹색을 확인한 뒤 `Confirm`한다.
8. 다시 편집해서 `Flip All`을 누른 뒤 `Cancel`한다. 이전에 Confirm한 배치로 되돌아가야 한다. enable/disable all 버튼과 드래그 다중 선택도 각각 시도한다.
9. `File > Save As`로 이 패키지의 새 `output/warehouse.usd`에 저장한다. 자산 reference와 custom 변경사항이 보존되므로 원격 source가 계속 필요할 수 있다.

## 개념과 관찰

USD **reference**는 벽 부품을 장면에 합성하고, **variant**는 같은 부품의 스타일 선택을 나타낸다. floor plan은 창고 구조를 모으는 parent prim이다. 내부 기둥은 인접 block의 네 부분이 합쳐져 보이므로 하나의 mesh를 지우는 방식보다 전용 column editor를 쓴다. 이 실습에서 Python API를 호출하지 않으며 extension UI가 USD 편집을 수행한다.

성공 기준은 닫힌 외곽, 내부 바닥 tile, 한 벽의 style 변경, Confirm/Cancel에 맞는 기둥 상태이다. 한 변수 실험은 외곽을 유지하고 같은 직선 벽의 style만 바꾸는 것이다. generation 실패 시 선 교차, 너무 가까운 점, dataset 연결을 확인한다. 시작점 선택이 어렵다면 해당 부분을 확대한다. 원격 자산 최초 로딩이 늦으면 로컬 다운로드 자산 경로를 사용한다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_omni_warehouse_creator.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
