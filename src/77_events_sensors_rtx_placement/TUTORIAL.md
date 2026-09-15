# 77. 카메라 배치와 보정 도구를 한 장면에서 연결하기

## 이번에 배우는 것

**두 카메라가 있는 작은 방을 열고, 카메라의 배치·보행 영역·보정 파일이 각각 어떤 역할을 하는지 확인합니다.**

카메라가 여러 대 있어도 장애물 뒤를 모두 볼 수 있는 것은 아닙니다. 이번 장면에는 방 한가운데 가림막을 두고 서로 반대편에 카메라를 놓았습니다. 각 시점을 확인한 뒤 상면 이미지와 보정 파일을 만들어, 화면에서 본 배치를 데이터로 옮겨 봅니다.

| 준비된 요소 | 경로 또는 파일 | 이 실습에서의 역할 |
|---|---|---|
| 방 | `room.usda`의 `/World/Room` | 12 m × 10 m 바닥과 중앙 가림막 |
| 관찰 카메라 | `/World/Cameras/Camera_A`, `Camera_B` | 서로 다른 시야 제공 |
| 탐색 범위 | `/World/NavMeshVolume` | 보행 영역을 계산할 범위 |
| 준비 검사 | `inspect_stage.py` | 단위·축·확장·NavMesh·카메라 경로 확인 |
| 공식 도구 | Camera Placement / Camera Calibration | 위치 선정 / 기존 카메라 정보 내보내기 |

여기서는 이미 배치된 두 카메라를 사용합니다. 자동 배치 버튼의 효과는 다음 배치 실습에서 다루고, 이번에는 두 창의 역할과 출력까지 이어지는 준비 순서를 익힙니다.

## 1. 방을 열고 NavMesh 준비하기

Isaac Sim 5.1.0 GUI와 지원 RTX GPU가 필요합니다. 저장소 루트에서 다음을 실행하세요. 설치 경로가 다르면 `~/isaacsim`을 바꿉니다.

```bash
mkdir -p src/77_events_sensors_rtx_placement/output/intro-01
~/isaacsim/isaac-sim.sh --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

1. **File > Open**에서 `src/77_events_sensors_rtx_placement/room.usda`를 엽니다.
2. **Window > Extensions**에서 명령에 지정한 두 확장이 활성화되어 있는지 확인합니다.
3. **Window > Navigation > Navmesh**에서 **Bake**를 누릅니다.
4. 뷰포트의 눈 아이콘에서 **Show By Type > Navmesh**를 켜고 바닥 위 계산된 영역을 확인합니다.
5. **Window > Script Editor**에 이 폴더의 `inspect_stage.py` 전체를 붙여 넣고 실행합니다.

NavMesh는 걸어갈 수 있는 바닥 영역을 표현한 데이터입니다. `NavMeshVolume`은 그 계산의 범위이므로, 볼륨이 있다고 계산 결과까지 준비된 것은 아닙니다. **Bake는 장면의 바닥과 장애물로부터 실제 영역을 만드는 단계입니다.**

### 설정에서 볼 부분

`room.usda`의 시작에는 다음 정보가 있습니다.

```usda
metersPerUnit = 1
upAxis = "Z"
```

장면 길이 1은 1 m이고 Z축이 위쪽입니다. 가림막은 중심 `(0, 0, 1.5)` m, 크기 `1 × 4 × 3` m여서 바닥에 닿아 있습니다. 카메라 둘은 높이 3.5 m에 놓여 있습니다.

USD Camera는 자신의 로컬 -Z 방향을 보고 +Y를 영상 위쪽으로 사용합니다. 장면의 Z-up은 월드 기준이므로 카메라 로컬 축과 구분하세요. 이 방의 부모 Xform에는 변환이 없어 Camera_A/B의 작성 위치와 월드 위치가 같습니다.

### 실행 결과 확인하기

검사기가 성공하면 `meters_per_unit=1`, `up_axis=Z`, `navmesh_available=True`와 카메라 경로 목록을 출력합니다. 처음에는 `Camera_A`, `Camera_B`가 있어야 합니다. 나중에 Top View를 만들면 목록에는 그 카메라도 추가됩니다.

이 스크립트는 카메라를 생성하거나 Bake하지 않습니다. 준비가 빠져 있으면 오류로 중단하여 누락된 단계를 알려 줍니다. 성공 출력 역시 방 전체를 카메라가 볼 수 있다는 뜻은 아닙니다.

## 2. 두 시점을 보정 파일로 내보내기

**Tools > Sensors > Camera Placement**와 **Tools > Sensors > Camera Calibration**을 엽니다. Placement는 주어진 요구에 맞는 카메라 위치를 찾는 도구이고, Calibration은 존재하는 카메라의 위치·투영·관찰 영역을 파일로 정리하는 도구입니다.

먼저 뷰포트 카메라 메뉴에서 `Camera_A`와 `Camera_B`를 번갈아 선택하세요. 가운데 가림막이 화면에 어떻게 들어오고, 어느 바닥이 가려지는지 확인합니다. 카메라 이름을 선택한 것과 Stage에서 prim만 선택한 것은 다르므로 실제 뷰포트 시점이 바뀌었는지 보세요.

### 설정에서 볼 부분

Calibration 창에 아래 값을 넣습니다.

| 필드 | 값 | 필요한 이유 |
|---|---|---|
| Scene Root Prim Path | `/World/Room` | 방의 범위를 기준으로 상면 카메라를 만듭니다. |
| Floor Height | `0` | 바닥 평면의 높이입니다. |
| Ceiling Height | `-1` | 천장이 없는 이 장면에서는 기본 클리핑을 사용합니다. |
| Place Info | `city=Seoul/building=Training/room=SmallRoom` | 내보낼 장소 정보입니다. |
| Raycast Density | `100` | 관찰 영역 경계를 계산할 광선 샘플 밀도입니다. |
| Output Folder Path | 위에서 만든 `output/intro-01`의 절대 경로 | 결과 파일을 저장할 위치입니다. |

1. **Top View Camera > Create**를 누릅니다. Path 필드에 표시된 실제 경로의 카메라로 뷰포트를 전환합니다. 기본 생성 경로는 `/World/Top_Camera/Calibration_Top_Camera`입니다.
2. 방 전체가 상면에 들어오는지 확인합니다. 이 카메라는 바닥을 수직으로 보는 orthographic 카메라이며 회전은 `(0, 0, 0)`입니다.
3. **Create Dot Prims**를 누르고 `/World/Calibration_Dots` 아래 카메라별 보정점을 확인합니다. 기본값은 각 카메라당 6개입니다.
4. **Generate Calibration File**을 누른 다음 **Generate Top View Image**를 누릅니다.
5. **File > Save As**로 `output/intro-01/scene.usda`에 저장합니다. 관찰이 끝나면 창을 닫아도 됩니다.

### 실행 결과 확인하기

출력 폴더에서 `calibration.json`, `Top.png`, `imageMetadata.json`을 직접 열어 보세요. JSON의 카메라 정보와 장소 값, 상면 이미지 속 방의 형태가 방금 사용한 장면과 대응해야 합니다.

보정점은 영상 좌표와 장면 좌표를 연결할 샘플입니다. Top View 카메라는 그 결과를 위에서 보기 위한 카메라이므로 `/World/Cameras`의 두 관찰 카메라와 역할이 다릅니다. 파일이 보이지 않으면 확장을 켠 상태에서 멈춘 것이 아닌지, 두 생성 버튼을 실제 눌렀는지 확인하세요.

## 3. 준비·배치·보정의 관계 정리

```text
room.usda → NavMesh Bake → 장면 준비 확인
                 ↓
기존 Camera_A/B의 시야 확인 → 보정점 생성 → calibration.json
                 ↓
          Top View 생성 → Top.png + imageMetadata.json
```

Stage는 현재 장면 전체이고 prim은 그 안에서 경로로 찾는 요소입니다. Camera prim의 위치와 렌즈 속성이 투영을 정하고, 가림막 같은 geometry가 실제로 보이는 영역을 제한합니다. 화각이 넓다는 것만으로 장애물 뒤까지 보이는 것은 아닙니다.

여기서 보정은 알고 있는 가상 카메라 정보를 내보내는 과정입니다. 실제 카메라를 촬영해 렌즈 왜곡을 추정하는 체커보드 실험으로 해석하지 않습니다. 행렬과 좌표의 수학적 검사는 79번에서 더 자세히 다룹니다.

## 4. 간단한 확인 실험

`/World/Room/Occluder`를 선택해 **Scale의 Y만 4에서 2로** 줄여 보세요. 위치와 X·Z 크기, 카메라는 유지합니다.

가림막의 가로 길이가 짧아지면 끝부분 너머로 보이는 바닥이 늘어날 수 있습니다. NavMesh를 다시 Bake하고 새 출력 폴더에서 보정점과 파일을 다시 생성하세요. 두 카메라 시점과 Top View를 비교해, 렌즈를 바꾸지 않아도 관찰 가능한 바닥이 달라지는지 확인합니다. 기존 결과와 수정 결과를 같은 파일에 섞지 않습니다.

## 실행할 때 막히면

- **Sensors 메뉴에 두 창이 없음**: `isaacsim.sensors.rtx.placement`의 활성 상태를 확인하세요.
- **검사기가 Bake를 요구함**: 포함 볼륨만 존재하는 상태일 수 있습니다. Navigation 창에서 Bake를 끝낸 뒤 다시 실행하세요.
- **보정점이 없음**: 카메라가 `/World/Cameras` 아래에 있는지, 바닥을 향하는지, NavMesh가 준비되었는지 확인하세요.
- **상면 이미지가 잘림**: Scene Root가 `/World/Room`인지 확인하고 Top View를 다시 만드세요. 생성된 Path 필드가 실제 카메라를 가리켜야 합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Sensors Placement and Calibration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_sensors_rtx_placement.html)에 대응합니다. 상세 출력 절차는 [Camera Calibration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html)을 함께 참고하세요.

공식 확장의 도구를 그대로 사용하며, 외부 창고 자산 대신 이 폴더의 작은 방을 제공합니다. 이번 개정에서는 USD·검사 코드와 공식 자료를 대조했습니다. GUI의 Bake와 보정 파일 생성은 실행하지 않았고 `tutorial.json`은 `not_run`입니다.
