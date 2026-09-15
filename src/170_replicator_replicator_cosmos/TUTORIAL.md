# 170. 주행 영상과 다섯 가지 제어 영상을 같은 시점에 저장하기

## 이번에 배우는 것

**Carter의 전방 카메라에서 RGB·깊이·분할·경계 영상을 함께 저장하고 Cosmos Transfer 입력을 준비합니다.**

생성형 모델에 장면의 모양을 전달하려면 보기 좋은 RGB만으로는 부족할 수 있습니다. 물체 사이 거리나 경계를 별도 영상으로 전달하면 다른 외형의 영상을 만들 때도 장면 구조를 참고하게 할 수 있습니다. 이번에는 그런 입력을 만드는 과정까지 다룹니다.

| 구성 | 역할 | 결과 |
|---|---|---|
| `run.py` | 창고에서 Carter를 주행시키고 CosmosWriter로 캡처 | clip별 PNG와 MP4 |
| `semantic_mapping.json` | 선택적으로 클래스 이름에 분할 색 지정 | 의미 기반 분할 설정 |
| `prepare_transfer.py` | 모달리티 간 프레임 번호 검사 | Transfer 제어 JSON |
| 외부 Cosmos Transfer | 준비된 영상을 받아 모델 추론 | 별도 환경에서 생성하는 영상 |

**CosmosWriter는 데이터를 저장하는 writer입니다. 이 실행기만으로 Cosmos 모델의 영상 생성까지 수행하지는 않습니다.**

## 1. 두 개의 짧은 주행 clip 만들기

Isaac Sim 5.1, RTX GPU와 지원 드라이버를 준비하세요. 자산 루트의 창고 장면 `full_warehouse_worker_and_anim_cameras.usd`와 `OmniGraph/nova_carter_nav_only.usd`, 두 파일의 참조 자산에도 접근할 수 있어야 합니다. 공식 로봇의 navigation graph는 Script Node를 사용하므로 실행기가 해당 기능을 활성화합니다.

저장소 루트에서 실행합니다.

```bash
~/isaacsim/python.sh src/170_replicator_replicator_cosmos/run.py \
  --headless --clips 2 --frames 10 \
  --output src/170_replicator_replicator_cosmos/output/first
```

`--frames`는 clip 하나의 프레임 수입니다. 위 명령은 총 20개 시점을 저장합니다. 출력 경로는 새 폴더여야 합니다. GUI를 관찰하려면 `--headless`를 빼세요. 생성과 저장 후 창이 남으며, `--steps 120`을 추가하면 **저장 후** 120회 업데이트 뒤 닫힙니다.

### 코드에서 볼 부분

Carter는 `/NavWorld/CarterNav` 아래에 추가됩니다. 시작 이동 값은 `(-6,4,0)`, 그 아래 `targetXform`의 이동 값은 기본 `(3,3,0)`입니다. 두 값은 각각 **해당 Prim의 부모 기준 translate**입니다. 특히 `--target`을 세계 좌표의 목적지로 해석하면 부모의 이동을 빠뜨리므로, Stage의 목표 월드 변환과 로봇 위치를 함께 확인하세요. 전방 카메라를 1280×720 render product에 연결한 뒤 writer를 붙입니다.

```python
rep.orchestrator.set_capture_on_play(False)
writer = rep.WriterRegistry.get("CosmosWriter")
writer.attach(render_product)
```

자동 Play 캡처를 끄는 이유는 **저장할 시점을 반복문에서 직접 정하기 위해서**입니다. 타임라인은 주행을 계속 진행하고, 아래 호출에서 데이터를 수집합니다.

```python
rep.orchestrator.step(pause_timeline=False)
observations.append({"clip": clip, "frame": frame,
                     "timeline_seconds": timeline.get_current_time()})
```

프레임 사이에는 `capture_interval - 1`회의 앱 업데이트를 추가합니다. 기본 `--capture-interval 2`라면 추가 업데이트가 1회입니다. 최초 `--start-delay 0.1`초는 주행 준비를 위한 타임라인 시간이며 저장 프레임에 포함하지 않습니다.

clip이 끝날 때 `writer.next_clip()`을 호출해 PNG 쓰기와 영상 인코딩을 마칩니다. 마지막 clip에도 이 호출이 필요합니다. 다음 clip에서 프레임 번호는 다시 시작하지만 로봇 위치를 초기화하지 않으므로 주행의 다음 구간을 이어서 촬영합니다.

### 실행 결과 확인하기

`output/first/clip_0000/` 아래에서 같은 번호의 영상을 비교하세요.

| 모달리티 | 파일 예 | 읽을 때 주의할 점 |
|---|---|---|
| RGB | `rgb/rgb_0000.png`, `rgb.mp4` | 카메라에 보이는 장면입니다. |
| 깊이 | `depth/depth_0000.png`, `depth.mp4` | 거리의 시각화이며 픽셀 값을 그대로 m로 읽지 않습니다. |
| 분할 | `segmentation/segmentation_0000.png` | 기본은 instance ID로 개체를 구분합니다. |
| 음영 분할 | `shaded_seg/shaded_seg_0000.png` | 경계 추출에도 사용되는 중간 표현입니다. |
| 경계 | `edges/edges_0000.png`, `edges.mp4` | shaded segmentation에 Canny를 적용한 결과입니다. |

각 물체의 경계가 같은 화면 위치에 대응해야 합니다. 기본 instance 색은 학습 클래스 이름을 의미하지 않습니다. MP4 재생도 확인하고, `capture_times.json`의 타임라인 초를 함께 읽으세요. 영상 인코딩 FPS와 저장 시점 간 시뮬레이션 시간 차이를 같은 것으로 가정하지 않습니다.

## 2. 저장한 영상을 Transfer 설정으로 연결하기

데이터가 만들어졌다면 일반 Python으로 다음 검사를 실행합니다.

```bash
python3 src/170_replicator_replicator_cosmos/prepare_transfer.py \
  --clip src/170_replicator_replicator_cosmos/output/first/clip_0000 \
  --output src/170_replicator_replicator_cosmos/output/first/transfer_control.json
```

다섯 모달리티의 PNG 번호 집합이 같고 MP4가 비어 있지 않아야 JSON을 작성합니다. 이 검사는 MP4를 디코딩하거나 영상 정렬을 눈으로 확인하는 검사를 대신하지 않습니다.

### 설정에서 볼 부분

생성된 JSON에는 RGB의 절대 경로인 `input_video_path`와 네 제어 가지가 들어갑니다.

| 제어 가지 | 기본 가중치 | 추가 영상 경로 |
|---|---|---|
| `vis` | 0.25 | 입력 RGB를 사용합니다. |
| `edge` | 0.25 | 이 스키마에는 별도 `input_control`을 쓰지 않습니다. |
| `depth` | 0.25 | `depth.mp4` |
| `seg` | 0.25 | `segmentation.mp4` |

가중치의 합은 1입니다. `--edge-only`를 지정하면 `edge`의 가중치가 1인 별도 설정을 만들 수 있습니다. 캡처한 `edges.mp4`가 있다는 사실과 제어 JSON이 그 파일을 명시적으로 참조하는지는 구분해서 읽으세요.

의미별 색이 필요하면 다음처럼 mapping을 전달합니다.

```bash
~/isaacsim/python.sh src/170_replicator_replicator_cosmos/run.py \
  --headless --semantic-mapping src/170_replicator_replicator_cosmos/semantic_mapping.json \
  --output src/170_replicator_replicator_cosmos/output/semantic
```

제공한 파일은 `floor`, `wall`, `rack`을 RGBA 색에 대응시킵니다. 장면에 해당 semantic class가 붙어 있어야 효과가 있으며, mapping 자체가 자산에 라벨을 새로 붙이지는 않습니다.

실제 Transfer 추론은 [5.1 문서의 Transfer 연결 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html#using-data-with-cosmos-transfer)에 해당하는 모델 환경과 가중치를 별도로 준비한 뒤 진행하세요. 선택한 모델 버전의 GPU 메모리, 해상도와 입력 길이 조건을 확인해야 합니다. 이 실습의 10프레임 clip이 모든 모델의 길이 조건에 맞는 것은 아닙니다.

## 3. 캡처 시간과 모델 입력의 관계 정리

```text
주행 타임라인 → 전방 카메라의 한 시점 → 다섯 모달리티
                                           ↓
                             프레임 번호 검사 → 제어 JSON
                                           ↓
                                  별도 Transfer 모델 추론
```

같은 번호는 모달리티를 묶는 기준이고, `timeline_seconds`는 장면 속 시점을 해석하는 기준입니다. 생성형 모델의 결과를 얻은 뒤에는 원래 깊이·분할과 구조가 얼마나 유지되는지 다시 확인해야 합니다. 입력 라벨이 있다고 생성 영상이 자동으로 완벽한 정답 영상이 되는 것은 아닙니다.

## 4. 간단한 확인 실험

`--canny-low`만 **10 → 30**으로 바꾸고 새 출력 경로에 실행해 보세요. `--canny-high`는 기본 100으로 유지합니다.

약한 경계가 연결되는 범위와 노이즈가 어떻게 달라지는지 `edges.mp4`에서 비교하세요. RGB의 모든 텍스처가 경계로 나와야 한다고 예상하지 않습니다. 이 writer의 경계 입력은 shaded segmentation이기 때문입니다.

## 실행할 때 막히면

- **Carter 카메라나 목표 prim이 없음**: 창고만 열린 상태일 수 있습니다. navigation USD와 참조 자산을 확인하세요.
- **로봇이 움직이지 않음**: Script Node, navigation graph, 목표 위치와 장애물을 확인하세요. 짧은 clip의 끝이 목표 도달을 뜻하지는 않습니다.
- **의미 분할이 비어 보임**: mapping의 클래스명과 장면 라벨을 대조하고 기본 instance 모드와 비교하세요.
- **PNG만 있고 MP4가 없음**: video encoding 로그를 확인하세요. 파일 저장과 인코딩은 별도 단계입니다.
- **Transfer 준비 검사 실패**: 같은 번호의 PNG가 모든 모달리티에 있는지 확인하세요. 불완전한 clip의 누락 파일을 임의로 복사하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Cosmos Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html)에 대응합니다. 공식 창고·Carter 장면과 CosmosWriter를 사용하고, 로컬 실행기에 타임라인 기록과 Transfer 입력 검사를 추가했습니다.

실행기·설정·writer 연결을 문서와 대조했으며 GPU 캡처, MP4 재생, 외부 모델 추론은 이번 개정에서 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
