# 79. 카메라 보정 파일과 상면 FOV 만들기

권장 학습 순서 **79** · 센서와 측정 데이터 · 출처 ID `t074`

두 가상 카메라의 내부·외부 행렬, 보정점, 바닥 FOV를 공식 Camera Calibration GUI로 내보냅니다. `room.usda`는 12 m × 10 m 바닥, 가림막, 두 Camera prim과 NavMesh 포함 영역을 가진 독립 장면입니다. 공식 Full Warehouse를 작은 장면으로 바꾸었고 보정 계산은 NVIDIA 확장의 원래 구현을 사용합니다. 실제 카메라의 렌즈 왜곡을 측정하는 체커보드 보정 실험과는 구별하세요.

## 필요한 환경과 명령

Isaac Sim 5.1.0 GUI, 지원 RTX GPU, `isaacsim.sensors.rtx.placement`, `omni.anim.navigation.bundle`이 필요합니다. 다른 로컬 튜토리얼·공통 코드·외부 모델은 필요 없습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/79_events_ext_sensors_rtx_placement_camera_calibration
mkdir -p output/calibration-01
"$ISAAC_SIM_PATH/isaac-sim.sh" --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

## 단계별 실습

1. **File > Open**으로 `room.usda`를 엽니다. Stage의 `/World/Cameras` 아래 `Camera_A`, `Camera_B`를 찾습니다. Calibration 도구는 이 경로 아래의 카메라를 수집합니다.
2. **Window > Extensions**에서 두 확장을 켭니다. **Window > Navigation > Navmesh > Bake**로 걷는 바닥 영역을 생성합니다. 뷰포트 눈 아이콘의 **Show By Type > Navmesh**로 바닥이 표시되는지 확인합니다. 장면 단위는 m, 위쪽 축은 Z입니다.
3. **Tools > Sensors > Camera Calibration**을 엽니다. **Scene Root Prim Path**를 `/World/Room`, **Floor Height**를 `0`, **Ceiling Height**를 `-1`로 지정합니다. 이 장면은 천장이 없으므로 -1의 기본 클리핑을 사용합니다.
4. **Top View Camera > Create**를 누릅니다. Path 필드의 실제 카메라 경로를 확인합니다. 5.1 설치 소스의 경로는 `/World/Top_Camera/Calibration_Top_Camera`입니다. 뷰포트 카메라 아이콘에서 이 카메라를 골라 방 전체와 두 카메라의 위치가 화면에 들어오는지 봅니다. top camera는 **orthographic**, 회전 `(0,0,0)`이어야 합니다.
5. **Place Info**에 `city=Seoul/building=Training/room=SmallRoom`을 입력합니다. `/`로 계층을 구분하고 `=` 좌우에 이름과 값을 넣습니다. **Output Folder Path**에는 새 출력 폴더의 절대 경로를 넣습니다.
6. **Raycast Density=100**, **Minimum FOV Polygon Edge Length=0**, **Minimum Area of FOV Polygon Hole to Ignore=0**을 입력합니다. **Create Camera View Images**, **Create FOV Polygon Images**, **Show FOV Polygon**을 켭니다. Density N은 N×N 광선을 의미하므로 100은 카메라마다 10,000개 광선 샘플입니다.
7. **Create Dot Prims**를 누릅니다. `/World/Calibration_Dots/Camera_A`와 `Camera_B` 아래 각각 6개 점을 확인합니다. 뷰포트를 각 카메라로 바꿔 점들이 화면에 보이는지 확인합니다. 점을 만들기 전에 보정 파일 생성 버튼을 누르지 마세요.
8. **Generate Calibration File**을 눌러 `calibration.json`을 생성합니다. 카메라를 선택하면 FOV를 관찰할 수 있습니다. 이어 **Generate Top View Image**를 눌러 `Top.png`와 `imageMetadata.json`을 생성합니다. FOV 이미지 옵션을 켰다면 `Debug/fieldOfViewPolygon`의 이미지도 확인합니다.
9. **File > Save As**로 `output/calibration-01/scene.usda`를 저장합니다. 아래 명령은 실제 내보낸 카메라 수, 점 대응 수, 재투영 오차, 내부×외부 행렬과 투영행렬의 차이를 출력합니다.

```bash
python3 inspect_output.py output/calibration-01/calibration.json
```

10. `calibration.json`의 첫 `sensors` 항목에서 `place`, `intrinsicMatrix`, `extrinsicMatrix`, `cameraMatrix`, `homography`, `imageCoordinates`, `globalCoordinates`를 직접 찾아 검사 출력과 비교합니다. 파일의 `attributes` 안 `fieldOfViewPolygon` 값과 상면 이미지의 흰 FOV 모양도 비교합니다.

## 행렬·좌표·가림의 의미

USD Camera는 로컬 -Z를 보고 +Y가 영상 위쪽입니다. Z-up 장면에 있어도 카메라 자체의 축 관례는 바뀌지 않습니다. Prim 경로는 장면 주소이고 Xform은 부모에 대한 위치·방향·크기입니다.

`intrinsicMatrix` K는 초점거리와 주점을 픽셀 단위로 표현하는 3×3 행렬입니다. `extrinsicMatrix` E는 월드 점을 카메라 좌표로 바꾸는 3×4 행렬이며 P=K×E는 3×4 투영행렬입니다. 동차 좌표는 스케일이 달라도 같은 픽셀을 나타내므로 검사기는 행렬 스케일을 맞춘 뒤 잔차를 계산합니다. `homography`는 지정한 바닥 평면과 영상 사이의 3×3 변환이며 바닥 밖의 임의 3D 물체에 그대로 적용할 수 없습니다.

보정점의 월드 좌표를 P로 변환하고 마지막 성분으로 나눈 결과와 저장된 픽셀 좌표를 비교한 값이 재투영 오차입니다. 작은 오차는 **파일 안 좌표의 일관성**을 뜻합니다. 그 자체로 현실 카메라의 정확도나 장애물 뒤의 가시성을 증명하지 않습니다. FOV 폴리곤은 렌즈 화각뿐 아니라 장면의 가림과 raycast 샘플링에 영향을 받습니다.

성공하면 카메라 두 개의 유효 행렬과 카메라마다 6쌍 이상의 점 좌표가 있고 상면 이미지와 폴리곤이 보입니다. 점 샘플은 달라질 수 있으므로 원문 스크린샷과 픽셀이 같을 필요는 없습니다.

## 한 값 변경하기

`Camera_A` Focal Length만 `18`에서 `30`으로 바꾸고 새 폴더에서 **Create Dot Prims부터** 다시 수행합니다. K의 초점거리 성분, 영상 속 물체 크기, FOV 폴리곤의 폭을 비교합니다. 카메라를 옮기거나 렌즈 값을 바꾼 뒤 이전 보정 파일을 재사용하면 좌표가 맞지 않습니다.

## Full Warehouse와 문제 해결

공식 환경으로 반복하려면 Content Browser에서 `full_warehouse.usd`를 열고 `/World/Cameras` Xform 아래 **Create > Camera**로 카메라를 만듭니다. 카메라 선택 후 Translate `(-13.02311,7.20828,5.0)`, Rotate `(-55.253,-56.035,-150.088)`, Focal Length `20.94`를 원문 예제로 사용합니다. 부모 변환이 있으면 월드 자세가 달라집니다. Scene Root는 `/Root`, Floor `0`, Ceiling `6`으로 Top View를 생성해 천장을 잘라냅니다. 에셋은 NVIDIA 5.1 환경 자산 접근이 필요하며 패키지에 포함되지 않습니다.

점이 생성되지 않으면 NavMesh 베이크와 카메라 경로·시선 방향을 확인합니다. Top View에 방이 안 들어오면 루트 경로와 orthographic/회전 값을 확인합니다. FOV 구멍을 제거하는 threshold를 높이면 작은 사각지대가 시각화에서 사라질 수 있으니 초기값 0으로 시작합니다. 기존 파일을 덮어쓰지 않게 매번 새로운 출력 폴더를 사용합니다. `inspect_stage.py`를 Script Editor에서 실행하면 사전 조건을 점검할 수 있습니다. 실제 GUI/GPU 보정 실행은 아직 검증하지 않았습니다.

## 출처

- [Isaac Sim 5.1 — Camera Calibration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html#using-the-camera-calibration-tool-tutorial)
- [5.1 — Calibration 입력 필드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html#input-fields)
- [5.1 — 보정점과 파일 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html#generate-calibration-dots)

행렬 필드 이름과 top camera 경로는 설치된 5.1 `isaacsim.sensors.rtx.placement`의 `data/calibration_template.json`, `camera_calibration/calibration_helper.py`, `settings.py`에서도 확인했습니다.
