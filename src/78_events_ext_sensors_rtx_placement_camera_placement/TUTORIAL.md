# 78. 가림막이 있는 방에 카메라를 자동 배치하기

## 이번에 배우는 것

**바닥 한 지점을 몇 대의 카메라가 보아야 하는지 지정하고, 자동 배치 결과의 위치와 실제 관찰 영역을 함께 확인합니다.**

카메라를 두 대 설치하는 것과 모든 지점을 두 시점에서 관찰하는 것은 다른 요구입니다. 특히 장애물이 있으면 한 카메라의 빈 영역을 다른 카메라가 보완해야 합니다. 이번에는 카메라가 없는 방에서 출발하여 공식 Camera Placement 도구로 위치를 정합니다.

| 구성 | 내용 | 확인할 결과 |
|---|---|---|
| `room.usda` | 12 m × 10 m 바닥, 중앙 가림막, 빈 `/World/Cameras` | 배치 전 장면 |
| NavMesh | 바닥의 보행 영역 | 카메라 후보와 장면 처리의 준비 |
| Coverage Density | 기본 실험값 `1` | 바닥 patch마다 필요한 관찰 카메라 수 |
| `camera_info_payload.json` | 카메라 경로·위치·주시점 | 배치된 자세 |
| `inspect_output.py` | 위치에서 거리와 각도 계산 | JSON의 구조와 기하 정보 |

Patch는 관찰 여부를 평가하기 위해 나눈 작은 바닥 구역입니다. 위치 파일을 읽는 검사와 장애물 뒤까지 실제 보이는지 확인하는 시각화는 함께 사용합니다.

## 1. 카메라가 없는 장면 준비하기

Isaac Sim 5.1.0 GUI, 지원 RTX GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
mkdir -p src/78_events_ext_sensors_rtx_placement_camera_placement/output/density-1
~/isaacsim/isaac-sim.sh --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

1. **File > Open**으로 이 폴더의 `room.usda`를 엽니다.
2. Stage에서 `/World/Cameras`가 비어 있고 `/World/Room` 아래 바닥과 가림막이 있는지 확인합니다.
3. **Window > Navigation > Navmesh > Bake**를 실행합니다. 뷰포트 눈 아이콘의 **Show By Type > Navmesh**로 계산된 바닥 영역을 봅니다.
4. **Window > Script Editor**에서 `inspect_stage.py`를 실행합니다. 단위가 m, 위쪽 축이 Z이며 확장과 NavMesh가 준비되어 있는지 확인합니다.
5. **Tools > Sensors > Camera Placement**를 엽니다.

검사기 출력에서 카메라 목록이 비어 있어도 이 단계에서는 정상입니다. 이 파일은 준비 상태만 읽고 카메라를 만들지 않습니다. 실제 배치는 다음 버튼으로 시작합니다.

### 설정에서 볼 부분

작은 방에 맞춰 다음 값을 GUI에 직접 입력하세요. 로컬 USD가 자동으로 채워 주는 설정이 아닙니다.

| 필드 | 입력값 | 의미 |
|---|---|---|
| Total Camera Number | `-1` | 필요한 전체 대수를 도구가 정합니다. |
| Camera Height Range | `2 ~ 4` m | 허용할 카메라 높이 |
| Camera Distance Range | `2 ~ 10` m | 관찰 지점까지의 거리 조건 |
| Camera Look Down Angle Range | `15 ~ 60`° | 수평에서 아래로 기울이는 각도 |
| Patch Size / Ground Height | `0.5` m / `0` m | 바닥 격자 크기와 높이 |
| Border Checking Index | `0` | 경계 주변 후보 제한값 |
| Camera On Navmesh | 켬 | 수평 위치를 보행 영역으로 제한 |
| Minimum Coverage Increase | `2` | 추가 카메라가 늘려야 할 최소 patch 수 |
| Limit FOV by Distance | 켬 | 거리 조건도 관찰 영역에 반영 |
| Coverage Density | `1` | patch마다 요구하는 최소 카메라 수 |
| Target Coverage Ratio | `0.9` | 목표로 삼을 관찰 비율 |

**Camera Placement Output Path**에는 위에서 만든 `output/density-1`의 절대 경로를 입력합니다. 이 값들은 목표와 후보 조건입니다. `0.9`를 입력했다는 사실만으로 실제 90%를 달성했다고 기록하지 마세요.

## 2. 배치된 카메라와 관찰 영역 읽기

**Place Cameras**를 누르고 계산이 끝날 때까지 기다립니다. 콘솔의 방향별 생성 수와 Stage의 `/World/Cameras` 아래 카메라 수를 확인하세요. 정해진 카메라 대수 하나를 정답으로 삼지 않습니다.

### 실행 결과 확인하기

저장소 루트의 터미널에서 실제 출력 파일을 검사합니다.

```bash
python3 src/78_events_ext_sensors_rtx_placement_camera_placement/inspect_output.py src/78_events_ext_sensors_rtx_placement_camera_placement/output/density-1/camera_info_payload.json
```

| 검사 출력 | 읽는 방법 |
|---|---|
| `camera_count` | 파일에 내보낸 총 카메라 수이며 Stage의 관찰 카메라와 대조합니다. |
| `height_m` | 카메라 위치의 Z값입니다. 바닥이 0인 이 장면에서는 바닥 위 높이입니다. |
| `focus_distance_m` | 카메라와 `focus_point` 사이의 3차원 거리입니다. |
| `look_down_deg` | 카메라에서 주시점으로 내려다보는 각도입니다. |

### 코드에서 볼 부분

검사기는 내보낸 좌표로 다음 계산을 수행합니다.

```python
distance = math.dist(position, focus)
look_down = math.degrees(math.asin((position[2] - focus[2]) / distance))
```

첫 계산은 공간상의 두 점 사이 거리입니다. 두 번째 계산은 그 거리에서 수직 높이 차이가 차지하는 비율로 하향 각도를 구합니다. `focus_distance_m`는 렌즈의 focal length가 아닙니다. JSON에는 모든 가림과 광선 결과가 없으므로 이 계산만으로 커버리지 비율을 복원할 수 없습니다.

실제 관찰 영역은 GUI에서 이어서 확인하세요.

1. **Tools > Sensors > Camera Calibration**에서 Scene Root를 `/World/Room`, Floor Height를 `0`, Ceiling Height를 `-1`로 지정합니다.
2. **Top View Camera > Create**를 누르고 생성된 Path의 카메라로 뷰포트를 전환합니다.
3. Stage에서 `/World/Cameras` 아래의 **Camera prim들을 모두 선택**합니다.
4. Placement 창의 **Show Selected Camera Coverage**를 누릅니다. 방 가장자리와 가림막 뒤에 빈 영역이 남는지 확인합니다.
5. **Hide Coverage**로 표시를 지우고 **File > Save As**로 `output/density-1/scene.usda`를 저장합니다.

### 공식 창고 장면으로 반복하기

원문의 더 큰 장면도 비교하려면 Content Browser에서 `full_warehouse.usd`를 검색해 엽니다. 이 파일은 NVIDIA 5.1 환경 에셋이며 이 폴더에 포함되어 있지 않습니다.

NavMesh를 새로 Bake하고 `Total Camera Number=-1`, `Coverage Density=2`, `Target Coverage Ratio=0.99`로 설정합니다. 높이는 2~4 m, 거리는 원문 기본값 6.5~14 m를 확인하고 나머지는 해당 설치 기본값을 사용하세요. 작은 방의 2~10 m 조건을 그대로 복사하지 않습니다. Top View 생성 시 실제 장면 루트가 `/Root`라면 Scene Root도 `/Root`로 지정합니다. 별도 출력 폴더에서 Place Cameras와 Coverage 표시까지 반복해 규모가 달라졌을 때 필요한 카메라 수를 비교하세요.

## 3. 배치 요구와 달성 결과 정리

```text
방과 NavMesh + 후보 높이·거리·각도
    → patch별 관찰 요구 설정
    → Place Cameras
    ├─ JSON: 어디에 몇 대를 배치했는지
    └─ Coverage 표시: 어느 영역이 실제로 겹쳐 보이는지
```

`Coverage Density=2`라면 patch 하나를 최소 두 대가 보아야 합니다. 전체 카메라 수를 두 대로 고정하는 뜻은 아닙니다. 가림막 한쪽에 카메라를 더 놓아도 반대편의 빈 영역을 메우지 못한다면 배치 요구가 그대로 남을 수 있습니다.

Patch Size를 작게 하면 더 세밀하게 평가하지만 계산량도 증가합니다. 이번에는 0.5 m로 유지하여, 격자 해상도 변경과 관찰 중복 요구 변경을 한 번에 섞지 않습니다.

## 4. 간단한 확인 실험

**Coverage Density만 1에서 2로** 바꿔 반복하세요.

1. `room.usda` 원본을 다시 열고 NavMesh를 다시 Bake합니다.
2. 새 출력 폴더 `output/density-2`를 만들고 출력 경로를 바꿉니다.
3. 높이·거리·각도·patch 크기·목표 비율을 **1절 표의 작은 방 설정으로** 확인하고 Density만 2로 설정합니다. 창고 변형도 실행했다면 거리와 목표 비율을 먼저 원래 값으로 되돌립니다.
4. 배치 후 카메라 수와 겹치는 관찰 영역을 기준 결과와 비교합니다.

더 많은 중복 시야가 필요하므로 배치 수가 늘거나 목표 달성이 어려워질 수 있습니다. 정확히 두 배의 카메라가 나와야 하는 실험은 아닙니다. 도구가 조건을 충족하지 못하거나 중단한 경우도 결과에 기록하세요. 원본부터 시작하는 이유는 이전 카메라가 비교에 섞이지 않게 하기 위해서입니다.

## 실행할 때 막히면

- **배치가 시작되지 않음**: 확장 활성화와 NavMesh Bake를 `inspect_stage.py`로 먼저 확인하세요.
- **카메라가 적거나 배치가 중단됨**: 거리·각도·최소 추가 patch 조건이 함께 만족 가능한지 살펴보세요. 목표 비율을 결과 비율로 대신 기록하지 않습니다.
- **커버리지 표시가 없음**: 부모 `/World/Cameras`만 선택한 것이 아닌지 확인하고, 실제 Camera prim들을 선택하세요.
- **검사기가 `No cameras were exported`를 출력함**: 빈 결과입니다. JSON 생성만으로 배치 성공을 판단하지 말고 콘솔과 Stage를 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Camera Placement](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_placement.html)에 대응합니다. 공식 배치 계산을 사용하고 로컬 방과 자세 검사기를 제공합니다. 원문의 Full Warehouse는 별도 NVIDIA 환경 자산이 필요하며, 크기가 다른 장면에는 후보 거리도 다시 정해야 합니다.

이번 개정에서는 장면·검사 코드와 공식 입력 필드를 대조했습니다. 실제 GUI 배치와 커버리지 관찰은 실행하지 않았으며 `tutorial.json`은 `not_run`입니다.
