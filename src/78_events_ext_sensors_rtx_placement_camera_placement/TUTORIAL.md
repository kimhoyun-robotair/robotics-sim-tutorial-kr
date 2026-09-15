# 78. 가림을 고려한 카메라 자동 배치

권장 학습 순서 **78** · 센서와 측정 데이터 · 출처 ID `t073`

카메라 수와 바닥의 중복 관찰 요구를 바꾸고 실제 배치 결과를 비교합니다. 이 패키지의 `room.usda`에는 12 m × 10 m 바닥, 가운데 3 m 높이 가림막, NavMesh 포함 영역이 있으며 카메라는 없습니다. 작은 장면만 새로 만든 실습용 대체물이고, 배치 계산과 시각화는 공식 `isaacsim.sensors.rtx.placement`의 원래 GUI로 수행합니다.

## 이 실습의 의도

카메라가 없는 바닥 장면에서 시작해, 가림막이 있는 공간을 얼마나 여러 시점으로 관찰할지에 따라 자동 배치 결과가 달라지는지 확인합니다. `Coverage Density`는 바닥 patch 하나를 관찰해야 하는 카메라 수이고, `Total Camera Number=-1`은 전체 설치 대수를 도구가 정하게 하는 설정입니다. 제공 명령은 GUI를 열 뿐이며 실제 후보 탐색·카메라 생성·JSON 저장은 NavMesh를 Bake하고 **Place Cameras**를 눌렀을 때 공식 확장이 수행합니다.

## 실행 후 확인할 것

- `room.usda`를 처음 열면 `/World/Cameras`가 비어 있는 것이 정상입니다. 바닥과 중앙 파란 가림막, Bake한 NavMesh를 확인한 후에 배치를 시작합니다. `inspect_stage.py`는 단위·축·확장·NavMesh를 검사하며 카메라를 만들지 않습니다.
- **Place Cameras** 완료 후 `/World/Cameras`의 생성 Camera prim 수와 `camera_info_payload.json`의 항목 수를 기록합니다. `inspect_output.py`의 `camera_count`가 비어 있지 않고 실제 카메라 목록과 대응해야 하며, 고정된 카메라 대수를 정답으로 삼지 않습니다.
- 검사 출력의 `height_m`, `focus_distance_m`, `look_down_deg`를 입력한 높이 2~4 m, 거리 2~10 m, 하향 각도 15~60°와 대조합니다. 이 값들은 내보낸 위치와 `focus_point`에서 계산하며, 카메라 렌즈의 focal length를 뜻하지 않습니다.
- 생성한 Camera prim을 모두 선택해 **Show Selected Camera Coverage**를 실행하고 상면에서 겹치는 영역과 가림막 뒤의 빈 영역을 봅니다. JSON의 자세 검사 통과와 `Target Coverage Ratio=0.9` 설정만으로 실제 90% 관찰을 달성했다고 기록하지 않습니다.
- 원본 장면을 다시 열고 Bake한 뒤 Density만 2로 바꾸어 카메라 수와 겹치는 영역을 비교합니다. 더 높은 중복 관찰 요구가 항상 충족되거나 카메라가 정확히 두 배 생성되는 것은 아니므로, 목표 미달·중단도 결과에 함께 기록합니다.

## 독립 실행 준비

Isaac Sim 5.1.0 GUI, RTX GPU, `isaacsim.sensors.rtx.placement`, `omni.anim.navigation.bundle`이 필요합니다. 외부 에셋·다른 로컬 패키지 없이 실행할 수 있습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/78_events_ext_sensors_rtx_placement_camera_placement
mkdir -p output/density-1
"$ISAAC_SIM_PATH/isaac-sim.sh" --enable isaacsim.sensors.rtx.placement --enable omni.anim.navigation.bundle
```

## 따라 하기

1. **File > Open**으로 `room.usda`를 엽니다. Stage의 `/World/Room` 아래 바닥과 장애물, `/World/NavMeshVolume`을 확인합니다. 이 장면은 m 단위와 Z-up입니다.
2. **Window > Extensions**에서 두 확장이 Enabled인지 확인합니다. **Window > Navigation > Navmesh > Bake**를 실행합니다. 베이크 완료 후 뷰포트 눈 아이콘 **Show By Type > Navmesh**를 켜서 바닥 탐색 영역이 보이는지 확인합니다.
3. **Tools > Sensors > Camera Placement**를 엽니다. **Camera Placement Output Path**에 `output/density-1`의 절대 경로를 넣습니다. **Total Camera Number**는 `-1`로 설정해 필요한 카메라 수를 도구가 결정하도록 합니다.
4. 작은 장면에 맞춰 다음 표를 직접 입력합니다. 이는 공식 창에 입력하는 실습값이며 확장이 자동으로 읽는 설정 파일은 아닙니다.

| 필드 | 값 | 의미 |
|---|---:|---|
| Camera Height Range | 2 ~ 4 m | 바닥 위 후보 카메라 높이 |
| Camera Distance Range | 2 ~ 10 m | 관찰 지점까지 후보 거리 |
| Camera Look Down Angle Range | 15 ~ 60° | 수평 0°, 수직 하향 90° |
| Patch Size | 0.5 m | 관찰 여부를 평가할 바닥 격자 크기 |
| Ground Height | 0 m | 바닥 평면 높이 |
| Border Checking Index | 0 | 경계 주변 후보 제한 |
| Camera On Navmesh | 켬 | 카메라 수평 위치를 보행 영역으로 제한 |
| Minimum Coverage Increase | 2 | 새 카메라가 추가로 보여야 할 patch 수 |
| Limit FOV by Distance | 켬 | 거리에 따른 관찰 영역 제한 |
| Coverage Density | 1 | 각 patch에서 요구하는 카메라 수 |
| Target Coverage Ratio | 0.9 | 원하는 바닥 관찰 비율 |

5. **Place Cameras**를 누르고 완료될 때까지 기다립니다. 콘솔의 방향별 카메라 수와 `/World/Cameras` 아래 실제 카메라 수를 기록합니다. 요청 조건을 만족하지 못하면 생성 수가 예상과 다를 수 있습니다. 목표 비율을 실제 달성률로 기록하지 마세요.
6. **Tools > Sensors > Camera Calibration**에서 **Scene Root Prim Path**를 `/World/Room`, 바닥 `0`, 천장 `-1`로 지정하고 **Top View Camera > Create**를 누릅니다. 생성 경로 필드를 확인하여 뷰포트를 그 카메라로 전환합니다. 회전 0,0,0의 orthographic 카메라가 바닥을 수직으로 내려다봅니다.
7. Stage에서 `/World/Cameras` 아래의 **Camera prim들을 모두 선택**한 뒤 Placement 창에서 **Show Selected Camera Coverage**를 누릅니다. 여러 카메라의 관찰 영역이 겹치는 곳과 장애물 뒤를 확인합니다. **Hide Coverage**로 표시를 지웁니다.
8. **File > Save As**로 `output/density-1/scene.usda`에 저장합니다. 터미널에서 다음 검사로 실제 위치·주시점까지의 거리·하향 각도를 계산합니다.

```bash
python3 inspect_output.py output/density-1/camera_info_payload.json
```

9. **File > Open**으로 원본 `room.usda`를 다시 열고 다시 Bake합니다. 새 폴더 `output/density-2`를 만들고 **Coverage Density만 2**로 바꿔 반복합니다. 겹쳐 보이는 영역을 늘리려면 카메라 수가 어떻게 달라지는지 비교합니다. Density가 2일 때 원문 예시는 한 번 관찰되는 곳을 빨강, 두 번 관찰되는 곳을 초록으로 보여줍니다.

## 공식 Full Warehouse 예제도 수행하기

원문과 같은 장면은 **Content Browser**에서 `full_warehouse.usd`를 검색해 엽니다. Isaac Sim 5.1 환경 에셋에 접근할 수 있어야 하며 이 패키지에는 배포하지 않습니다. 다시 Bake하고, `Total Camera Number=-1`, `Coverage Density=2`, `Target Coverage Ratio=0.99`로 설정합니다. 나머지는 해당 설치의 기본값을 사용합니다. 작은 장면의 거리 2~10 m를 그대로 쓰지 말고 원문 기본 거리 6.5~14 m와 높이 2~4 m를 확인하세요. 장면 루트가 `/Root`이면 Top View 생성 시 `/Root`를 씁니다. 저장은 별도 폴더에 합니다.

## API·USD 해설과 확인

배치 결과 `camera_info_payload.json`은 방향별 리스트이며 각 항목의 `camera_path`는 USD prim 주소, `camera_position`은 카메라 위치, `focus_point`는 바라보는 지점입니다. `inspect_output.py`의 `math.dist`와 `asin` 계산은 이 **내보낸 값**으로 거리와 기울기를 계산합니다. JSON에는 장애물과 모든 광선 결과가 없으므로 이 검사만으로 커버리지 비율을 복원할 수 없습니다.

NavMesh는 보행 영역, patch는 커버리지 평가의 샘플 격자입니다. 작은 patch는 더 세밀하지만 계산량이 커집니다. `Coverage Density=2`는 전체 카메라 수가 2개라는 뜻이 아닙니다. 카메라의 USD transform과 렌즈 속성이 실제 화각을 결정합니다.

`inspect_stage.py`를 Script Editor에서 실행하면 단위·축·확장·NavMesh가 검사됩니다.

배치가 멈추면 거리 제한·높이·추가 patch 요구를 차례대로 확인하세요. 카메라가 없는 JSON은 검사에서 실패합니다. 이미 배치한 카메라가 섞이지 않게 비교 실험은 원본 장면을 다시 여는 것으로 시작합니다. 실제 GUI/GPU 배치는 아직 실행 검증하지 않았습니다.

## 출처

- [Isaac Sim 5.1 — Camera Placement](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_placement.html#camera-placement-tool-tutorial)
- [5.1 — 배치 입력값](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_placement.html#input-fields)
- [5.1 — Warehouse 환경 에셋](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_environments.html#warehouse)
