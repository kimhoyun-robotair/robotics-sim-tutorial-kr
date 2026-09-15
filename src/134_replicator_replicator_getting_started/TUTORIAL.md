# 134. 같은 장면도 촬영을 요청하는 방법이 다릅니다

## 이번에 배우는 것

**고정 촬영, 다중 카메라, 무작위화, 낙하 이벤트를 비교하며 캡처의 기준을 구분합니다.**

Replicator에서 한 프레임을 만든다는 말에는 “어떤 상태를”, “어느 카메라로”, “언제” 촬영하는지가 함께 들어 있습니다. 이번 `run.py`는 같은 `carton` 상자로 네 가지 질문을 따로 확인하도록 구성되어 있습니다.

| `--example` | 바뀌는 조건 | 주요 확인 파일 |
|---|---|---|
| `basic` | 고정 상태를 반복 촬영합니다. | RGB·분할·2D box, `observations.json` |
| `multi` | 카메라 2대로 같은 상태를 봅니다. | `camera_metadata_*.json`, 카메라별 RGB |
| `randomize` | 위치와 조명을 다른 주기로 바꿉니다. | 위치 기록과 RGB |
| `events` | 낙하 높이 조건을 만족하면 한 쌍을 촬영합니다. | `height`, `pair` 기록 |

각 실행은 새 장면에서 시작합니다. `events`만 강체와 중력을 추가하며, 다른 모드의 상자는 자동으로 떨어지지 않습니다.

## 1. 고정 장면에서 카메라 출력 읽기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트의 터미널을 사용하세요.

```bash
~/isaacsim/python.sh src/134_replicator_replicator_getting_started/run.py --example basic --headless --frames 4 --output /tmp/tutorial134-basic
~/isaacsim/python.sh src/134_replicator_replicator_getting_started/run.py --example multi --headless --frames 4 --output /tmp/tutorial134-multi
```

출력 폴더는 아직 없어야 합니다. 두 명령은 각각 네 번 촬영한 뒤 종료합니다. GUI로 보려면 `--headless`를 빼세요. `--steps`도 생략하면 파일 저장 후 창을 닫을 때까지 유지합니다. 양수 `--steps`를 지정한 실행은 작업 후 GUI 대기 없이 종료합니다.

### 코드에서 볼 부분

```python
rep.orchestrator.set_capture_on_play(False)
writer.attach(products)
rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
```

Play에 따른 자동 기록을 끄고, 이 호출로 촬영 시점을 정합니다. `delta_time=0.0`은 물리 시간을 추가하지 않는다는 뜻입니다. 기본 `rt_subframes=4`는 같은 시점에서 렌더를 안정시키는 반복이며 사진 네 장을 의미하지 않습니다.

`multi`는 기존 512×512 front 카메라에 320×240 side 카메라를 더합니다. `CameraMetadataWriter`는 `camera_params`와 `bounding_box_3d`를 받아 NumPy 배열을 JSON으로 바꿉니다. 이 변환은 측정값을 파일에 담기 위한 작업이며 새로운 카메라 값을 만들어 넣는 과정은 아닙니다.

### 실행 결과 확인하기

`basic`의 `observations.json`에서 `position`은 네 행 모두 `[0, 0, 0]`입니다. 물체 배치가 같은 네 사진은 정상 결과입니다. RGB의 상자와 `carton` 의미 라벨·2D box를 맞춰 보세요.

`multi`에서는 같은 관찰 행의 `rgb_shapes`가 `[512, 512, ...]`와 `[240, 320, ...]`를 포함하는지 확인합니다. 배열 크기는 **높이, 너비, 채널** 순서라 카메라 해상도 표기와 순서가 다릅니다. `camera_metadata_0000.json`은 render product별 카메라 정보와 3D box를 담습니다.

`--pose-writer`를 `multi`에 추가하면 `pose/`에 PoseWriter 결과와 디버그 이미지도 기록합니다. BasicWriter의 검출 배열과 PoseWriter의 포즈 파일은 저장 규약이 다르므로 파일 이름만 보고 서로 바꾸어 사용하지 마세요.

## 2. 변화와 사건을 촬영 조건으로 사용하기

```bash
~/isaacsim/python.sh src/134_replicator_replicator_getting_started/run.py --example randomize --headless --frames 4 --output /tmp/tutorial134-random
~/isaacsim/python.sh src/134_replicator_replicator_getting_started/run.py --example events --headless --frames 4 --steps 300 --output /tmp/tutorial134-events
```

`randomize`의 상자 위치는 Python이 매 프레임 x/y를 -1~1 m 범위에서 고릅니다. 조명 색은 별도 OmniGraph 이벤트를 보낼 때만 바뀝니다.

```python
if frame % 2 == 0:
    rep.utils.send_og_event(event_name="change_light")
```

즉, 0부터 센 짝수 프레임에 조명 변경을 요청합니다. 물체 이동과 조명 변화가 같은 주기를 가져야 할 이유는 없습니다. `observations.json`은 위치를 기록하므로 조명 변화는 해당 RGB와 함께 판단하세요.

### 코드에서 볼 부분

`events`의 상자는 중심 높이 2 m에서 떨어지며 바닥은 없습니다. 이전 촬영 높이보다 0.4 m 이상 낮아졌을 때 다음 부분을 실행합니다.

```python
if previous_height - height >= 0.4:
    timeline.pause()
    rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
    UsdGeom.Imageable(cube).MakeInvisible()
```

이어서 숨긴 상태를 한 번 더 촬영하고, `finally`에서 상자를 다시 보이게 합니다. 촬영하는 동안 타임라인을 멈추므로 **같은 물리 순간의 상자 있는 사진과 없는 사진**을 얻습니다. 물리 변화와 대상의 존재 여부를 따로 비교할 수 있는 구성입니다.

### 실행 결과 확인하기

`events`의 관찰 행에는 `step`, `height`, `pair`가 있습니다. `pair: [0, 1]`은 첫 사건에서 생성한 두 연속 캡처를 뜻합니다. 숨긴 사진에는 `carton` 검출·분할 정답도 없어지는지 확인하세요.

이 모드의 `--frames 4`는 **최대 사건 네 번**입니다. 사건 하나마다 두 번 촬영하므로 최대 여덟 캡처이지만, 상자 높이가 0 아래로 내려가거나 앱 갱신 한도 `--steps 300`에 도달하면 일찍 끝납니다. 정확한 결과는 관찰 행 수와 `Capture steps:` 로그로 읽으세요. 사건이 하나도 관찰되지 않으면 코드는 오류를 냅니다.

## 3. 촬영 요청의 차이 정리

```text
basic / multi : 고정 상태 → step → 카메라별 출력
randomize     : 위치 변경 → 필요한 프레임에 조명 이벤트 → step
 events       : 물리 진행 → 높이 조건 → pause → 표시/숨김 한 쌍 → 재개
```

여기서 `step()`은 데이터 생성의 한 단위이고 `app.update()`는 앱이 처리할 일을 진행하는 호출입니다. 특히 events의 `--steps`는 앱 갱신의 상한이므로 고정된 초 단위의 낙하 시간을 직접 뜻하지 않습니다.

모든 모드는 마지막에 파일 쓰기를 기다린 뒤 writer·annotator를 분리하고 render product를 해제합니다. GUI가 남는 시간과 저장할 프레임 수가 서로 독립인 이유입니다.

## 4. 간단한 확인 실험

`events`를 **`--frames 1`로만 바꾸어** 새 출력 경로에 실행해 보세요. `--steps 300`은 유지합니다.

첫 낙하 사건이 감지되면 관찰 행 하나와 캡처 두 개가 생겨야 합니다. 요청값이 1인데 RGB가 두 장인 이유를 `pair`로 설명해 보세요. 사건을 감지하기 전까지 기다린 앱 갱신 수는 1이 아닙니다.

## 실행할 때 막히면

- **`No falling-height event observed`**: Physics Scene, Cube의 RigidBody 설정, USD 위치 갱신을 확인하세요. `--steps`가 너무 작으면 첫 조건에 도달하지 못합니다.
- **multi의 이미지 크기가 뒤집힌 것처럼 보임**: 해상도는 너비×높이, NumPy shape는 높이·너비 순서입니다.
- **randomize에서 매 사진마다 빛이 바뀌지 않음**: 조명 이벤트는 두 프레임마다 보냅니다. 상자 위치 변화와 구분하세요.
- **재실행이 출력 경로 오류로 끝남**: 각 실행에 새 `--output`을 사용하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)에 대응합니다. 공식 캡처·다중 카메라·이벤트 개념을 자체 도형과 독립 실행 CLI로 구성했습니다. `run.py` 전체를 이미 열린 Script Editor에 붙여 넣는 방식은 지원하지 않습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 기존 기록은 `basic --headless --frames 2`에서 RGB 두 장과 비어 있지 않은 검출 정답을 확인한 범위입니다. 다른 모드·GUI·PoseWriter는 별도 확인이 필요하며 이번 문서 개정에서는 GPU 실행을 추가하지 않았습니다.
