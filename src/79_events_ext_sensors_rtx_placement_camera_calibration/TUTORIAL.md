# 79. 카메라 보정 파일의 행렬과 바닥 FOV 읽기

## 이번에 배우는 것

**두 가상 카메라의 보정 파일을 내보내고, 3차원 점이 영상 좌표로 옮겨지는 관계와 실제로 보이는 바닥 영역을 구분해 확인합니다.**

카메라 파일에 위치와 행렬이 가득 있어도 어떤 값을 대조해야 할지 모르면 결과를 해석하기 어렵습니다. 이번에는 영상에 찍힌 보정점과 장면의 점 좌표를 함께 읽습니다. 이어 상면 FOV를 확인해, 투영이 수학적으로 맞는 것과 장애물 뒤가 보이는 것은 별개의 문제임을 살펴봅니다.

| 파일·요소 | 담고 있는 것 | 확인할 질문 |
|---|---|---|
| `room.usda` | 방, 가림막, `Camera_A`와 `Camera_B` | 어떤 시점을 보정했나요? |
| `calibration.json` | K·E·P 행렬과 점 대응, FOV 정보 | 같은 점을 같은 픽셀로 옮기나요? |
| `Top.png`, `imageMetadata.json` | 상면 이미지와 메타데이터 | 장면 전체를 어떻게 펼쳤나요? |
| `inspect_output.py` | 재투영 오차와 행렬 잔차 계산 | 내보낸 데이터가 서로 일관적인가요? |

실제 카메라로 체커보드를 촬영하는 실험은 아닙니다. 위치와 렌즈 설정을 알고 있는 가상 카메라에서 데이터를 내보냅니다.

## 1. 보정점과 출력 파일 만들기

Isaac Sim 5.1.0 GUI와 지원 RTX GPU가 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
mkdir -p src/79_events_ext_sensors_rtx_placement_camera_calibration/output/calibration-01
~/isaacsim/isaac-sim.sh --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

1. **File > Open**으로 이 폴더의 `room.usda`를 엽니다. 두 카메라는 `/World/Cameras` 아래에 있습니다.
2. **Window > Navigation > Navmesh > Bake**를 실행합니다. `inspect_stage.py`를 Script Editor에서 실행해 m 단위, Z-up, 확장 활성화와 NavMesh를 확인합니다.
3. **Tools > Sensors > Camera Calibration**을 엽니다.
4. Scene Root Prim Path=`/World/Room`, Floor Height=`0`, Ceiling Height=`-1`로 지정하고 **Top View Camera > Create**를 누릅니다.
5. 생성된 Path의 카메라로 뷰포트를 전환해 방 전체가 들어오는지 확인합니다. 기본 경로는 `/World/Top_Camera/Calibration_Top_Camera`이며, 회전 `(0, 0, 0)`인 orthographic 카메라입니다.

### 설정에서 볼 부분

| 입력 | 실습값 | 결과에 미치는 영향 |
|---|---|---|
| Place Info | `city=Seoul/building=Training/room=SmallRoom` | JSON의 장소 정보 |
| Output Folder Path | `output/calibration-01`의 절대 경로 | 파일 저장 위치 |
| Raycast Density | `100` | 카메라마다 100 × 100 광선으로 영역 샘플링 |
| Minimum FOV Polygon Edge Length | `0` | 경계 단순화를 하지 않는 시작값 |
| Minimum Area of FOV Polygon Hole to Ignore | `0` | 작은 구멍도 생략하지 않는 시작값 |
| Create Camera View Images | 켬 | 카메라 시점 이미지 생성 |
| Create FOV Polygon Images / Show FOV Polygon | 켬 / 켬 | FOV 이미지 저장과 화면 표시 |

`Ceiling Height=-1`은 이 장면의 천장 높이가 -1 m라는 뜻이 아니라 Top View의 기본 클리핑 사용입니다. Scene Root는 카메라 위치를 정할 장면 범위이므로 방의 geometry를 포함하는 `/World/Room`을 지정합니다.

설정을 마친 뒤 **Create Dot Prims → Generate Calibration File → Generate Top View Image** 순서로 누르세요. 첫 단계가 두 카메라에 대한 보정점을 만들고, 다음 단계가 그 점과 카메라 정보를 파일로 내보냅니다.

### 실행 결과 확인하기

`/World/Calibration_Dots/Camera_A`와 `Camera_B` 아래에 기본 6개씩 점이 생기는지 확인합니다. 각 카메라 시점에서 점을 살펴보고 다음 파일을 엽니다.

- `calibration.json`: 두 카메라의 행렬·점 좌표·장소 정보
- `Top.png`, `imageMetadata.json`: 상면 결과
- `Debug/fieldOfViewPolygon`: FOV 이미지 옵션으로 생성한 결과

**File > Save As**로 `output/calibration-01/scene.usda`도 저장하세요. 모든 파일을 확인한 뒤 앱을 닫을 수 있습니다.

## 2. 행렬을 이용해 보정점을 다시 투영하기

저장소 루트에서 실제 생성한 파일을 검사합니다. 이 검사기는 표준 Python만 사용합니다.

```bash
python3 src/79_events_ext_sensors_rtx_placement_camera_calibration/inspect_output.py src/79_events_ext_sensors_rtx_placement_camera_calibration/output/calibration-01/calibration.json
```

### 코드에서 볼 부분

`inspect_output.py`는 보정점 `(x, y, z)` 뒤에 1을 붙여 투영행렬 P에 곱합니다.

```python
world = [world_point[k] for k in ('x', 'y', 'z')] + [1]
pixel = [sum(row[j] * world[j] for j in range(4)) for row in projection]
```

계산 결과는 아직 픽셀 좌표 두 개가 아닙니다. 첫 성분과 두 번째 성분을 각각 세 번째 성분으로 나눈 값이 영상의 `(u, v)`입니다. 이렇게 마지막 성분으로 나누어 스케일을 없애는 표현을 동차 좌표라고 합니다.

| JSON 필드 | 크기 | 역할 |
|---|---|---|
| `intrinsicMatrix` K | 3 × 3 | 렌즈와 영상의 내부 투영 정보 |
| `extrinsicMatrix` E | 3 × 4 | 월드 좌표를 카메라 좌표로 옮기는 정보 |
| `cameraMatrix` P | 3 × 4 | 월드 점을 영상으로 투영하는 행렬 |
| `homography` | 3 × 3 | 지정한 바닥 평면과 영상 사이의 변환 |

USD Camera 자체는 로컬 -Z를 보고 +Y가 영상 위쪽입니다. 보정 파일의 E는 도구가 사용하는 카메라 좌표로 월드 점을 옮기는 행렬이므로, Stage의 Translate·Rotate 숫자를 그대로 3×4 배열에 넣어 대체하지 않습니다. 카메라의 부모에 변환이 있다면 그 변환까지 포함한 월드 자세가 필요합니다.

공식 도구는 카메라 설정으로 K와 E를 만들고, 점 대응으로 P를 계산합니다. 검사기는 `K × E`와 P의 스케일을 맞춰 차이를 구합니다. 점 대응에서 얻은 P가 별도로 계산된 카메라 설정과 얼마나 잘 맞는지 확인하는 것입니다.

### 실행 결과 확인하기

`camera_count=2`, 카메라마다 `dot_pairs`가 6 이상인지 확인하세요. 다음 두 수치의 의미는 서로 다릅니다.

- `max_reprojection_error_px`: P로 옮긴 점과 저장된 영상 좌표 사이의 최대 거리입니다. 단위는 픽셀입니다.
- `projection_vs_intrinsic_extrinsic_residual`: 스케일을 맞춘 P와 K×E의 행렬 차이입니다. 픽셀 오차로 읽지 않습니다.

검사기는 잘못된 행렬 크기, 부족한 점 대응, 무한대로 투영되는 점 등을 거부하지만, 위 두 수치에 합격선을 적용하지 않습니다. **명령이 정상 종료했다는 사실만으로 오차가 충분히 작다고 판정하지 마세요.** 수치가 크면 파일의 점 대응과 생성 시 사용한 카메라 조건부터 확인합니다.

### 천장이 있는 공식 창고로 반복하기

NVIDIA 5.1 환경 에셋에 접근할 수 있다면 Content Browser의 `full_warehouse.usd`로도 실습할 수 있습니다. `/World/Cameras` Xform 아래 Camera를 만들고 원문의 예시 Translate `(-13.02311, 7.20828, 5.0)`, Rotate `(-55.253, -56.035, -150.088)`, Focal Length `20.94`를 사용합니다. 부모에 변환이 있으면 이 숫자가 같은 월드 자세를 만들지 않으므로 먼저 부모를 확인하세요.

창고 NavMesh를 Bake한 뒤 Scene Root=`/Root`, Floor=`0`, Ceiling=`6`으로 Top View를 만듭니다. 작은 방의 `-1` 대신 천장 높이를 지정하면 상면을 가리는 천장 위 geometry를 클리핑할 수 있습니다. 새 폴더에서 보정점과 파일 생성을 다시 수행하세요. 이 변형은 외부 창고 자산이 필요하며, 기본 두 카메라 실습의 `camera_count=2` 조건을 그대로 적용하지 않습니다.

## 3. 투영과 가시성의 차이 정리

```text
월드의 보정점 ── P로 투영 ── 영상의 픽셀 → 재투영 오차
카메라·가림막 ── 광선 샘플링 ── 보이는 바닥 → FOV 폴리곤
```

가림막 뒤의 점도 수학적으로는 어떤 픽셀 좌표로 투영할 수 있습니다. 그 픽셀에서 실제로 보이는 물체가 가림막인지 바닥인지는 장면의 가림을 확인해야 알 수 있습니다. 그래서 작은 재투영 오차가 방 전체의 가시성을 보장하지는 않습니다.

`homography` 역시 지정한 바닥 평면에 대한 변환입니다. 공중의 물체나 높이가 다른 선반에 그대로 적용하면 같은 관계가 성립하지 않습니다. Top View의 FOV 구멍은 장애물의 영향일 수 있으므로, 보기 좋게 만들기 위해 구멍 제거 임계값부터 높이지 말고 원래 장면과 대조하세요.

## 4. 간단한 확인 실험

**File > Open**으로 원본 `room.usda`를 다시 열고 NavMesh를 Bake합니다. 창고 변형도 실행했다면 Scene Root·Floor·Ceiling을 포함한 GUI 입력을 1절의 작은 방 설정으로 되돌리고 Top View를 만드세요.

`Camera_A`의 **Focal Length만 18에서 30으로** 바꿔 보세요. 카메라 위치·회전과 aperture는 유지합니다.

새 출력 폴더에서 **Create Dot Prims부터** 다시 생성합니다. A의 영상 속 물체 크기, K의 초점거리 성분, 바닥 FOV 폭을 비교하세요. 같은 aperture에서 초점거리가 길어지면 화각이 좁아지고 영상 속 물체는 더 크게 보이는 것이 예상됩니다. B는 렌즈를 바꾸지 않았으므로 비교 기준이 됩니다.

점은 다시 샘플링되므로 두 실행의 보정점 픽셀이 완전히 같아야 하는 것은 아닙니다. 이전 보정 파일을 바뀐 카메라에 재사용하지 마세요.

## 실행할 때 막히면

- **보정 파일 생성이 진행되지 않음**: 유효한 Top View 경로, 장소 문자열 형식, 출력 폴더, `/World/Cameras` 경로와 점 생성 순서를 확인하세요.
- **검사기가 점 대응 부족을 보고함**: 카메라가 바닥을 향하고 NavMesh가 준비되어 있는지 확인한 뒤 점 생성부터 반복하세요.
- **Top View가 잘리거나 기울어짐**: 카메라가 orthographic이고 회전 `(0, 0, 0)`인지, Scene Root가 방 전체를 포함하는지 확인하세요.
- **오차가 큼**: 렌즈나 자세를 변경한 뒤 일부 파일만 다시 만든 것은 아닌지 확인하고 새 폴더에 한 조건의 결과를 모두 생성하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Camera Calibration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html)에 대응합니다. 작은 방은 로컬 대체 장면이며 보정 계산은 공식 확장이 수행합니다. 로컬 검사기는 내보낸 파일의 수학적 일관성을 읽기 위해 추가했습니다.

이번 개정에서는 장면·검사기와 설치된 5.1의 보정 필드 및 계산 흐름을 대조했습니다. 실제 GUI/GPU 보정 파일 생성은 수행하지 않았고 `tutorial.json`은 `not_run`입니다. 실제 카메라 렌즈의 보정 정확도를 검증한 실습은 아닙니다.
