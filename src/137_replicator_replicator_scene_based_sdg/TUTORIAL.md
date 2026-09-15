# 137. 창고의 관계를 유지하며 데이터셋 만들기

## 이번에 배우는 것

**창고의 지게차·팔레트·상자를 배치하고, 서로 다른 세 시점의 이미지와 정답을 함께 생성합니다.**

장면 중심 합성 데이터는 물체 하나의 모양뿐 아니라 주변 물체와의 관계를 담습니다. 팔레트가 지게차 앞에 있고 상자가 팔레트 위에 있어야 창고 장면으로 해석할 수 있습니다. 이번 코드는 이 관계를 먼저 만든 뒤 조명·배치·시점을 바꿉니다.

| 파일 또는 구성 | 역할 |
|---|---|
| `run.py` | JSON 설정을 조합하고 Isaac Sim 실행 프로세스를 시작합니다. |
| `config.json` | 창고 자산, 해상도, 클래스와 Writer 항목을 정합니다. |
| `scene_based_sdg.py` | 장면 구성과 세 카메라의 캡처를 진행합니다. |
| `scene_based_sdg_utils.py` | 충돌 설정, 상자 배치와 낙하 준비를 담당합니다. |
| TopView·DriverView·PalletView | 위쪽, 운전석 높이, 팔레트 주변의 세 관찰 시점입니다. |

이 폴더에는 NVIDIA 구현과 helper가 포함되어 있습니다. 기본 도형으로 대체하는 예제가 아니라 5.1 자산 라이브러리의 창고와 소품을 불러옵니다.

## 1. 설정 확인과 실제 생성을 나누어 실행하기

먼저 저장소 루트에서 일반 Python으로 적용될 설정을 확인하세요.

```bash
python3 src/137_replicator_replicator_scene_based_sdg/run.py --check-config --headless --frames 6 --output /tmp/tutorial137-first
```

이 명령은 JSON을 읽고 런처가 덮어쓴 값을 출력합니다. **Isaac Sim을 시작하거나 자산 접근·렌더링을 검사하지 않습니다.** JSON이 출력되었다는 사실만으로 데이터 생성 준비가 끝난 것은 아닙니다.

실제 실행에는 Isaac Sim 5.1 전체 설치, RTX GPU와 5.1 자산 서버 또는 같은 구조의 로컬 미러가 필요합니다.

```bash
python3 src/137_replicator_replicator_scene_based_sdg/run.py --isaac-sim ~/isaacsim --headless --frames 6 --output /tmp/tutorial137-first
```

일반 Python 런처가 지정한 설치의 `python.sh`로 `scene_based_sdg.py`를 실행합니다. 출력 폴더는 새 경로여야 하며 적용한 설정은 `effective_config.json`에 남습니다.

GUI로 보려면 `--headless`를 빼세요. 저장 후에도 창을 유지하며 닫으면 종료합니다. `--steps 120`은 **캡처가 끝난 뒤의 GUI 갱신 횟수**입니다. 상자 낙하의 물리 단계나 데이터 장수를 제한하지 않습니다.

### 설정에서 볼 부분

```json
"resolution": [512, 512],
"num_frames": 6,
"writer": "BasicWriter",
"clear_previous_semantics": true
```

CLI `--frames`는 JSON의 `num_frames`보다 우선합니다. 해상도는 세 카메라에 공통으로 적용됩니다. `clear_previous_semantics`는 기존 창고의 의미 라벨을 지운 뒤 실습 대상의 라벨을 붙일지를 정합니다. 배경의 기존 클래스와 새 학습 클래스가 섞이는 것을 제어하는 설정입니다.

자산은 `full_warehouse.usd`, Forklift, 팔레트, TrafficCone, CardBox를 사용합니다. `/Isaac/...`는 컴퓨터 루트 경로가 아니라 `get_assets_root_path()`로 찾은 **자산 루트에 덧붙이는 경로**입니다. USD 내부의 메시·재질·텍스처 참조도 함께 읽을 수 있어야 합니다.

### 실행 결과 확인하기

기본 완료 시 6캡처 × 3카메라의 RGB를 확인합니다. 로그의 `Actual PNG files`에는 의미 분할 이미지도 포함될 수 있으므로 이 숫자를 RGB 장수와 바로 비교하지 마세요.

| 출력 항목 | 이미지와 연결해서 볼 부분 |
|---|---|
| 카메라별 RGB | TopView, DriverView, PalletView가 같은 장면을 다르게 보는지 확인합니다. |
| Semantic segmentation | `forklift`, `traffic_cone`, `pallet`, `cardbox`를 읽습니다. |
| 2D tight box | 보이는 물체의 이미지상 경계와 픽셀 좌표를 비교합니다. |
| 3D box·occlusion | 물체 공간 범위와 가림 정보를 살펴봅니다. |
| `distance_to_image_plane` | 카메라 광축 방향의 깊이입니다. RGB 색과 별도의 수치 데이터입니다. |

세 카메라에서 모든 클래스가 항상 보여야 하는 것은 아닙니다. 가림과 시야를 먼저 확인한 뒤 해당 프레임의 정답을 읽으세요.

## 2. 배치 관계와 무작위화 순서 따라가기

### 코드에서 볼 부분

팔레트는 월드 좌표에서 독립적으로 놓지 않고 지게차의 변환을 기준으로 배치합니다.

```python
forklift_tf = omni.usd.get_world_transform_matrix(forklift_prim)
pallet_offset_tf = Gf.Matrix4d().SetTranslate(
    Gf.Vec3d(0, random.uniform(-1.2, -1.8), 0))
pallet_pos_gf = (pallet_offset_tf * forklift_tf).ExtractTranslation()
```

먼저 지게차 기준의 앞쪽 위치를 고르고, 그 변환을 월드 좌표로 옮깁니다. 지게차가 회전해도 팔레트와의 관계를 유지하기 위한 계산입니다.

상자는 두 방식으로 준비합니다. `register_scatter_boxes()`는 팔레트 크기로 숨은 평면을 만들고 충돌 검사를 켠 `scatter_2d`로 다섯 상자를 배치합니다. `simulate_falling_objects()`는 별도의 팔레트 위로 여덟 상자를 떨어뜨립니다. 후자는 최대 250단계 또는 **마지막 상자의 선속도 <0.001 m/s**에서 준비를 끝냅니다. 전체 상자에 대한 연속 정착 검사는 아니므로 “모든 상자가 완전히 안정되었다”는 보장으로 읽지 마세요.

캡처에 들어가면 변화의 주기가 나뉩니다.

| 변경 대상 | 코드의 기준 |
|---|---|
| 팔레트 위 scatter 상자·조명·Driver/Pallet 카메라 | `on_frame()` |
| Top 카메라 | `on_frame(interval=4)` |
| Traffic cone | 0부터 센 짝수 캡처에서 custom event 전송 |

Top 카메라는 near clipping 거리를 크게 두어 가까운 천장 면을 제외합니다. 따라서 다른 카메라처럼 가장 가까운 물체까지 모두 보여 주는 시점은 아닙니다.

### Writer 설정을 확장할 때

`config_basic_writer.yaml`, `config_default_writer.json`, `config_coco_writer.yaml`, `config_kitti_writer.yaml`은 다른 저장 설정의 예시입니다. 입문 런처는 JSON만 받지만 본체는 YAML도 받습니다. 예를 들어 저장소 루트에서 BasicWriter YAML을 복사하세요.

```bash
cp src/137_replicator_replicator_scene_based_sdg/config_basic_writer.yaml /tmp/tutorial137-basic.yaml
```

복사본에서 `launch_config.headless`를 `true`, `writer_config.output_dir`를 아직 없는 `/tmp/tutorial137-basic`으로 바꾸고 최상위에 `num_frames: 6`을 추가합니다. 본체의 기본 캡처 수는 20이므로 런처를 거치지 않을 때는 이 값을 직접 지정해야 합니다. 준비한 복사본을 설치 Python으로 실행하세요.

```bash
~/isaacsim/python.sh src/137_replicator_replicator_scene_based_sdg/scene_based_sdg.py --config /tmp/tutorial137-basic.yaml
```

이 YAML은 Grid 배경과 RGB만 선택합니다. 1절의 창고·분할·깊이 구성과 결과가 다른 이유를 `env_url`과 `writer_config`에서 확인해 보세요. GUI로 실행하려면 복사본의 `headless`를 `false`로 바꿉니다. 이때 `--steps`를 생략하면 저장 후 창을 유지하고, `--steps 120`을 붙이면 저장 후 최대 120번 앱을 갱신합니다.

직접 실행은 런처의 새 출력 폴더 검사를 거치지 않습니다. CocoWriter의 클래스 ID와 KittiWriter 옵션을 BasicWriter 인자에 덧붙이는 식으로 섞지 말고, **Writer 종류와 그 설정 묶음을 함께 선택**하세요. 이 실습의 기본 데이터 생성은 모델 학습을 시작하지 않습니다.

## 3. 물리 준비와 캡처의 역할 정리

```text
창고 참조 → 지게차 기준으로 팔레트 배치
    → 상자 배치 그래프 등록 + 별도 상자 낙하 준비
    → render product 활성화
    → 캡처별 무작위화 → delta_time=0으로 촬영
    → 파일 쓰기 완료 대기 → GUI 관찰 또는 종료
```

센서 렌더는 물리 준비 중 꺼 두었다가 캡처 전에 켭니다. 물리적으로 가능한 배치를 준비하는 일과, 그 상태의 여러 외관을 촬영하는 일을 나누어 비용을 줄입니다. `rt_subframes`는 렌더 안정화 반복이며 상자가 떨어지는 시간을 늘리는 설정이 아닙니다.

## 4. 간단한 확인 실험

`config.json`을 `/tmp/tutorial137-small.json`으로 복사하고 **`resolution`만 `[256, 256]`으로 바꾸세요.** 다음 명령으로 실행합니다.

```bash
python3 src/137_replicator_replicator_scene_based_sdg/run.py --isaac-sim ~/isaacsim --config /tmp/tutorial137-small.json --headless --frames 6 --output /tmp/tutorial137-small
```

카메라 수와 캡처 수는 그대로이고 RGB 한 장의 픽셀 수는 1/4이 됩니다. 검출 좌표가 새 해상도를 기준으로 저장되는지 확인하세요. 실행 사이 난수 배치가 고정되지 않으므로 상자가 정확히 같은 위치에 있을 것을 기대하지는 않습니다.

## 실행할 때 막히면

- **`python.sh not found`**: `--isaac-sim`이 설치 폴더를 가리키는지 확인하세요. 스크립트 파일 경로 자체를 넣는 옵션은 아닙니다.
- **창고·재질 로딩 실패**: 자산 루트와 내부 참조 경로를 확인하세요. JSON 검사는 이 접근을 시험하지 않습니다.
- **Writer 초기화 오류**: 선택한 Writer와 설정 인자 종류가 맞는지 확인하세요.
- **PNG 개수가 예상보다 많음**: RGB와 분할 PNG를 나누어 세세요. 카메라가 세 대라는 점도 반영합니다.
- **`Output exists`**: 이전 결과를 보존하고 새로운 `--output`을 지정하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)에 대응합니다. 포함한 NVIDIA 코드의 출처와 변경 고지는 [NOTICE.txt](NOTICE.txt)에 있습니다. 기본 JSON은 세 카메라와 BasicWriter의 입문용 설정이며 TAO 모델 학습은 범위 밖입니다.

[VERIFICATION.md](VERIFICATION.md)는 문법·도움말·설정 읽기를 확인한 기록이고 `tutorial.json`은 `not_run`입니다. 이 문서에서 제시한 장수와 정답 항목은 실제 자산·GPU 환경에서 확인할 기준입니다.
