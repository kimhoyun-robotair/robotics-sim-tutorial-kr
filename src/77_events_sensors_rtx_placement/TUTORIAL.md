# 77. RTX 센서 배치와 보정 도구 시작하기

권장 학습 순서 **77** · 센서와 측정 데이터 · 출처 ID `t072`

이 패키지는 공식 소개 페이지의 두 창을 실제 장면에서 연결하는 독립 실습입니다. `room.usda`는 외부 에셋 없이 만든 12 m × 10 m 바닥, 가림막, 두 카메라, NavMesh 포함 영역입니다. NVIDIA의 배치·보정 확장을 그대로 사용하며, Full Warehouse 대신 작은 실습 장면을 제공했습니다. 자동 배치 알고리즘 자체를 재구현한 패키지가 아닙니다.

## 이 실습의 의도

미리 배치한 두 카메라와 가운데 가림막을 통해, 카메라를 배치하는 도구와 기존 카메라의 투영·FOV를 내보내는 도구의 역할을 구분합니다. `/World/NavMeshVolume`은 걷는 영역을 계산할 범위이고, 가림막은 렌즈 화각 안에도 보이지 않는 바닥이 생긴다는 점을 보여줍니다. 실행 명령은 GUI와 확장을 준비하며, 장면 열기·NavMesh Bake·보정점 및 파일 생성은 아래 버튼 순서대로 직접 수행해야 합니다. 이 입문 절차에서는 기존 `Camera_A`, `Camera_B`를 사용하고 자동 배치는 별도로 실행하지 않습니다.

## 실행 후 확인할 것

- 원본 장면에서 `/World/Room/Occluder`와 `/World/Cameras/Camera_A`, `Camera_B`가 있는지 확인하고 각 카메라 시점으로 전환합니다. 파란 가림막에 가려지는 바닥은 의도한 관찰 대상이며, 카메라 두 개가 있다는 사실만으로 방 전체가 보이는 것은 아닙니다.
- Bake 후 Navmesh 표시를 켜 바닥의 보행 영역을 확인합니다. Script Editor의 `inspect_stage.py` 출력에서 `meters_per_unit=1`, `up_axis=Z`, `navmesh_available=true`와 두 카메라 경로를 확인합니다. 볼륨 prim만 있거나 검사 스크립트만 실행한 상태는 Bake 완료가 아닙니다.
- Camera Placement와 Camera Calibration 창이 모두 열리고, Calibration에서 생성한 Top View 카메라로 방 전체를 내려다볼 수 있는지 확인합니다. Top View 카메라는 기존 관찰용 두 카메라와 역할이 다릅니다.
- **Create Dot Prims** 뒤 `/World/Calibration_Dots`의 두 카메라별 점 6개를 확인하고, **Generate Calibration File / Generate Top View Image** 뒤 `calibration.json`, `Top.png`, `imageMetadata.json`을 실제로 엽니다. 장면을 열거나 확장을 켜기만 해서는 이 산출물이 생기지 않습니다.
- `calibration.json`의 카메라 정보와 각 시점·상면 이미지를 대조합니다. 이 실습의 stage 검사기는 준비 상태를 확인하며, 파일의 행렬 정확도나 가림막 뒤의 가시성까지 검사하는 도구는 아닙니다.

## 준비와 실행

Isaac Sim **5.1.0**, 지원 RTX GPU, GUI 실행 환경이 필요합니다. 아래 명령의 설치 경로를 자신의 경로로 바꾸세요. 다른 튜토리얼이나 공통 모듈은 필요 없습니다.

```bash
cd src/77_events_sensors_rtx_placement
mkdir -p output/intro-run-01
"$ISAAC_SIM_PATH/isaac-sim.sh" --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

`ISAAC_SIM_PATH`는 실행 전에 `export ISAAC_SIM_PATH=/path/to/isaacsim`으로 지정합니다. 기존 결과 폴더에는 저장하지 말고 실행마다 새 폴더를 만드세요.

## 실습 순서

1. **File > Open**에서 이 패키지의 `room.usda`를 엽니다. Stage 트리에서 `/World/Room`, `/World/Cameras/Camera_A`, `/World/Cameras/Camera_B`, `/World/NavMeshVolume`을 확인합니다.
2. **Window > Extensions**에서 `isaacsim.sensors.rtx.placement`와 `omni.anim.navigation.bundle`이 Enabled인지 확인합니다. 확장은 메뉴·UI·센서 처리를 추가하는 Kit 기능 단위입니다.
3. **Window > Navigation > Navmesh**의 **Bake**를 누릅니다. NavMesh는 사람이 걸을 수 있는 바닥을 삼각형으로 표현한 데이터입니다. 단순히 볼륨 prim이 존재하는 것만으로 베이크가 완료된 것은 아닙니다. 뷰포트 눈 아이콘 **Show By Type > Navmesh**로 바닥과 장애물 주변을 관찰합니다.
4. **Tools > Sensors > Camera Placement**와 **Tools > Sensors > Camera Calibration**을 모두 엽니다. 첫 도구는 카메라의 위치를 정하고, 둘째 도구는 이미 존재하는 카메라의 투영·위치·FOV를 기록합니다.
5. 뷰포트 카메라 메뉴에서 `Camera_A`와 `Camera_B`를 번갈아 선택합니다. 가운데 가림막이 반대쪽 바닥을 가리는지 관찰합니다. **Stage**에서 카메라의 `Translate`, `Rotate`, `Focal Length`를 확인합니다.
6. Calibration의 **Scene Root Prim Path**를 `/World/Room`, **Floor Height**를 `0`, **Ceiling Height**를 `-1`로 설정하고 **Top View Camera > Create**를 누릅니다. 경로 필드에 생성된 카메라 경로가 표시됩니다. `/World/Top_Camera/Calibration_Top_Camera`가 일반적인 실제 경로입니다. 이 카메라를 선택해 바닥 전체가 보이는지 확인합니다.
7. **Place Info**에 `city=Seoul/building=Training/room=SmallRoom`, **Output Folder Path**에 방금 만든 출력 폴더의 절대 경로를 넣습니다. **Raycast Density**는 `100`을 사용합니다. **Create Dot Prims** 후 **Generate Calibration File**, 마지막으로 **Generate Top View Image**를 누릅니다.
8. `/World/Calibration_Dots`에 카메라마다 6개 점이 생겼는지 확인하고 출력 폴더의 `calibration.json`, `Top.png`, `imageMetadata.json`을 엽니다. **File > Save As**로 `output/intro-run-01/scene.usda`에 저장하면 원본 실습 장면을 보존할 수 있습니다.
9. **Window > Script Editor**에서 `inspect_stage.py` 내용을 붙여 실행합니다. 실제 stage 단위, 위쪽 축, 확장 활성화, 베이크된 NavMesh, 카메라 경로를 검사합니다. 이 검사는 보정 정확도 검사가 아닙니다.

## 개념과 성공 기준

USD **Stage**는 장면 전체이고 **prim**은 `/World/Cameras/Camera_A`처럼 주소를 가진 항목입니다. Xform은 부모 좌표계를 만들며, Camera prim의 위치는 부모 변환을 포함한 월드 위치와 다를 수 있습니다. 이 장면은 부모 Xform에 변환이 없어 두 좌표가 같습니다. USD 카메라는 자신의 -Z 방향을 보고 +Y가 영상의 위쪽입니다. 장면의 Z-up과 카메라의 로컬 축은 별개입니다.

FOV는 화각 또는 실제 보이는 바닥 영역을 뜻합니다. 렌즈 화각이 넓어도 장애물 뒤는 관찰할 수 없습니다. Calibration은 가상 장면의 알려진 카메라 정보를 내보내는 작업이며 실제 카메라에서 체커보드로 렌즈 왜곡을 추정하는 실험과 다릅니다.

## 한 가지 바꾸기와 문제 해결

`Camera_A`의 Focal Length만 `18`에서 `30`으로 바꾸고 새 출력 폴더에서 점 생성부터 반복하세요. 다른 조건을 유지한 채 영상 폭과 FOV 폴리곤을 비교합니다. 보정 데이터를 만든 뒤 카메라를 옮겼다면 반드시 다시 생성해야 합니다.

메뉴가 없으면 확장이 Enabled인지 확인합니다. NavMesh가 없으면 바닥이 포함 볼륨 안에 있고 단위가 m인지 확인한 뒤 다시 Bake합니다. 보정 점이 없으면 카메라가 `/World/Cameras`의 자손인지, 카메라가 바닥을 향하는지 확인합니다. Top View가 잘렸다면 `/World/Room`을 장면 루트로 선택했는지 확인합니다. GPU 실행과 실제 출력은 이 작성 환경에서 검증하지 않았습니다.

## 출처

- [Isaac Sim 5.1 — RTX Sensors Placement and Calibration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_sensors_rtx_placement.html#enable-isaacsim-sensors-rtx-placement)
- [5.1 — Camera Calibration 입력과 생성 순서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html#using-the-camera-calibration-tool-tutorial)
