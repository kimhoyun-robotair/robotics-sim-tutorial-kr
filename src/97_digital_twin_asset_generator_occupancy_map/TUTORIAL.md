# 97. t087 · Occupancy Map에서 Block World까지

권장 학습 순서 **97** · 환경 구축과 로봇 행동 · 출처 ID `t087`

local `mapping_lab.usda`의 충돌 cone으로 2D occupancy map을 만들고 그 이미지를 다시 collision block world로 바꾼다. mesh를 보고 사람이 그린 지도가 아니라 Isaac Sim mapping extension의 실제 계산 결과를 사용한다. 로컬 stage는 지면 원점 근처의 작은 실험용 collision scene이다.

## 이 실습의 의도

3D 장애물의 특정 높이 단면을 occupancy 격자로 계산하고, 저장한 이미지를 다시 블록 형태의 충돌 장면으로 가져오는 왕복 과정을 배운다. 옆으로 눕힌 cone 하나는 샘플 높이와 cell size가 장애물 경계 표현에 미치는 영향을 비교하기 위한 장면이다. USDA를 여는 것은 충돌 장면 준비까지이며 지도 계산·PNG 저장·Block World 생성은 모두 GUI에서 직접 수행한다.

## 실행 후 확인할 것

- **측정 대상:** Stage의 `/World/Cone`에 collider가 있고 중심 `(0.3,0,0.1)`, X 회전 90도가 적용되어 있는지 본다. PhysX Collision Geometry를 사용할 때는 Physics Mesh 표시로 계산 대상 형상도 확인한다.
- **지도 계산:** 아래 z=0.1, cell size=0.05 설정으로 CALCULATE한 뒤 이미지에서 cone 단면의 occupied 영역과 빈 공간을 구분한다. 검정/흰색/회색을 선택했다면 occupied/free/unknown에 각각 대응하며 unknown은 free와 같은 뜻이 아니다.
- **해상도와 좌표:** 표시된 resolution, origin, image rotation을 PNG와 함께 기록한다. bounds는 최대 영역이므로 고정 이미지 크기를 기대하지 말고, cell size를 0.025로 줄인 결과에서 같은 장애물 경계가 더 촘촘한 격자로 표현되는지 비교한다.
- **재구성:** 저장한 `output/occupancy.png`를 같은 cell size로 Block World Generator에 넣으면 검은 pixel 위치에 block geometry와 collider가 생기고 흰색 영역은 열린 공간으로 남아야 한다. 원본 cone 전체의 곡면 복원이 아닌 2D 단면의 격자 근사다.
- **완료 범위:** `output/block_world.usd` 저장과 새 장면의 방향·크기 비교까지 확인한다. ROS Occupancy Map Parameters File 표시를 선택하는 것만으로 ROS 노드나 navigation이 실행되지는 않는다.

## Occupancy 계산

1. `File > Open`으로 `mapping_lab.usda`를 연다. cone에는 Collider가 있고 x=0.3, z=0.1, X 회전 90도, radius=0.15, height=0.4가 설정되어 있다. 원문의 cone 회전/높이 절차를 작은 meter 기준 장면으로 제공했다.
2. `Window > Extensions`에서 `isaacsim.asset.gen.omap`을 확인한다. 메뉴 `Tools > Robotics > Occupancy Map`을 연다.
3. Origin을 `(0,0,0.1)`, Lower Bound를 `(-1,-1,0.1)`, Upper Bound를 `(1,1,0.1)`, Cell Size를 `0.05`m로 설정한다. Origin은 cone 내부가 아닌 열린 공간이어야 한다. bounds는 maximal 영역이므로 실제 mapping extent가 더 작을 수 있다.
4. `Use PhysX Collision Geometry=true`로 CALCULATE 후 VISUALIZE IMAGE를 누른다. cone 단면의 occupied 영역과 free/unknown 영역을 구분한다. viewport eye 메뉴 `Show By Type > Physics Mesh > All`로 collision이 실제 어디에 있는지 확인한다.
5. Occupied Color는 검정, Freespace Color는 흰색으로 둔다. Unknown은 occupied/free와 구분되는 회색을 사용한다. Rotate Image를 180도로 두면 원문에서 설명하는 Block World 방향 대응을 확인할 수 있다.
6. Coordinate Type을 Stage Space와 ROS Occupancy Map Parameters File로 각각 바꾸고 표시되는 origin/resolution 정보를 읽는다. ROS용 정보 출력은 ROS 노드를 실행했다는 뜻이 아니다.
7. Save Image로 새 `output/occupancy.png`에 저장한다. scene/색/회전 변경 뒤에는 CALCULATE와 RE-GENERATE IMAGE 단계가 필요한지 확인하고 새 결과를 저장한다.

## Block World 재구성

1. 원본 stage를 새 이름으로 저장하고 새 stage를 만든다. `Tools > Robotics > Block World Generator`를 연다.
2. Load Image로 방금 저장한 PNG를 고른다. Cell Size=0.05m를 그대로 사용한다. 해상도당 meter 값이 다르면 재구성 크기가 달라진다.
3. Generate Block World를 누른다. 검은 pixel 위치에 geometry와 collision mesh가 생기고 흰색 pixel은 열린 공간으로 남는지 본다.
4. 원본 cone의 연속 곡면과 새 block world의 격자 모양을 비교한다. mapping 높이의 2D 단면으로 만든 근사이므로 원래 3D cone 전체를 복원하는 작업은 아니다. `output/block_world.usd`로 Save As한다.

## 개념과 한 변수 실험

occupancy는 지정 높이에서 공간을 차지하는지 표현한다. PhysX mode는 visual mesh 대신 collision approximation을 사용한다. `Use PhysX Collision Geometry=false`는 충돌 근사를 잠시 제거하고 RTX Lidar가 원 triangle mesh로 계산하는 다른 경로다. 이 mode 비교는 RTX/GPU 환경과 원본 geometry 영향을 함께 고려해야 한다.

첫 비교는 Cell Size만 0.05에서 0.025로 줄이는 것이다. 픽셀 크기가 절반이므로 같은 면적을 표현하는 격자 수가 늘고 경계가 더 촘촘해져야 한다. 계산 시간·결과 dimension도 기록한다. 두 번째 독립 비교에서는 cell size와 xy 영역을 유지하고 샘플 높이를 바꾼다. Origin, Lower Bound, Upper Bound의 z를 같은 새 높이로 맞춰 cone의 다른 단면을 비교한다.

빈 map이면 Collider 활성 여부, 빈 Origin, bounds, sampling 높이를 확인한다. 눈에 보이는 mesh만 있고 collision이 없으면 PhysX mode에서 검출되지 않는다. Block World가 반대로 보이면 image rotation을, 크기가 다르면 cell size를 확인한다. 원문 navigation map 생성과 image import를 모두 실제로 수행해야 전체 workflow 성공으로 볼 수 있다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
