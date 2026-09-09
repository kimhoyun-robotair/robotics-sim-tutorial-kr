# Replicator로 합성 데이터 생성하기

이 장에서는 물체와 조명, 카메라, 클래스 라벨을 직접 만든 뒤 RGB·깊이·분할 결과를 10장 저장한다. 대규모 무작위 생성 전에 **작은 데이터셋이 실제로 올바른지** 확인하는 것이 목표이다.

## 1. 화면에 보이는 장면이 데이터가 되기까지

| 구성 요소 | 역할 | 이 실습의 설정 |
| --- | --- | --- |
| Stage | 촬영할 물체와 환경 | 0.4 m 큐브, 바닥, Dome Light |
| Camera | 시점과 투영 | `[2,2,1.5]`에서 큐브를 바라봄 |
| Render Product | 카메라를 렌더링할 출력 | 640 × 480 |
| Semantic label | 물체의 정답 클래스 | `course_cube` |
| Annotator | 렌더 결과에서 정답 데이터 추출 | RGB, 거리, 의미 분할 |
| Writer | 디스크에 기록 | `BasicWriter` |
| Orchestrator | 촬영 시점 제어 | `step_async()` 10회 |

카메라 Prim만 만들면 파일이 저장되는 것은 아니다. Render Product를 만들고 Writer를 연결한 다음 촬영을 요청해야 한다. 물체에 라벨이 없으면 분할 이미지가 생성되어도 원하는 클래스의 정답 데이터가 없다. [Replicator Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html)

## 2. 먼저 10장을 저장하기

1. 진행 중인 Replicator 촬영이 있다면 완료한다. 현재 장면을 저장하고 **File > New**로 빈 장면을 만든다.
2. **Window > Script Editor**를 연다. 타임라인은 Stop 상태로 둔다.
3. [capture_dataset.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/script_editor/capture_dataset.py)를 전체 복사해 실행한다.
4. 촬영하는 동안 File > Open/New, Play, 다른 Replicator 코드를 실행하지 않는다.
5. Console에 완료 메시지와 출력 경로가 나타날 때까지 기다린다. 예제는 `~/isaacsim-course/outputs/sdg_실행시각/`에 매번 새 폴더를 만든다.
6. `manifest.json`의 `completed_capture_requests`가 10인지 확인하고, RGB 파일을 직접 열어 큐브가 조금씩 이동하는지 확인한다.

첫 렌더링은 셰이더 준비 때문에 오래 걸릴 수 있다. 기다리는 동안 같은 코드를 다시 실행하면 이전 촬영과 겹치므로 예제에서 중복 실행을 거부한다. 취소가 필요하면 Script Editor에서 `course_capture_task.cancel()`을 실행하고 종료 메시지를 기다린다. 취소한 폴더는 일부 프레임만 기록될 수 있다.

### 명시적인 클래스와 출력 만들기

전체 파일에서 다음 부분이 핵심이다.

```python
from isaacsim.core.utils.semantics import add_labels

add_labels(cube.GetPrim(), labels=["course_cube"], instance_name="class")
render_product = rep.create.render_product(camera, (640, 480))
writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(
    output_dir=str(output),
    rgb=True,
    distance_to_camera=True,
    semantic_segmentation=True,
)
writer.attach([render_product])
```

`distance_to_camera`는 카메라 중심까지의 거리이다. 광축 방향 Z 깊이와 다르므로 나중에 실제 RGB-D 센서와 비교할 때 이름만 보고 같은 값으로 취급하지 않는다. 투영 모델에 따라 영상 가장자리에서 차이가 커질 수 있다. [Depth Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)

## 3. GUI에서는 비동기 촬영을 사용하기

```python
for index in range(10):
    translation.Set(Gf.Vec3d(-0.45 + 0.1 * index, 0.0, 0.2))
    await rep.orchestrator.step_async(rt_subframes=4, delta_time=0.0)
await rep.orchestrator.wait_until_complete_async()
```

이 실습은 강체를 생성하지 않는다. 정지한 큐브를 바닥과 겹치지 않는 높이에 두고, 위치만 바꿔 촬영한다. `delta_time=0.0`을 사용하므로 프레임 사이에 물리 시간이 흐르는 실험도 아니다. 물리적으로 물체를 떨어뜨린 뒤 찍으려면 낙하와 정착을 먼저 검증하고 촬영 단계를 이어 붙인다.

`rt_subframes=4`는 같은 상태를 여러 차례 렌더링해 위치 변경 직후의 잔상과 재질 준비 영향을 줄이는 설정이다. 모든 그래픽 문제를 해결하는 값은 아니다. 공식 문서는 작은 해상도의 SDG에서 DLSS Quality를 권장하므로 예제는 촬영 중 `/rtx/post/dlss/execMode=2`를 사용하고 끝난 뒤 기존 값으로 복원한다. [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)

이미 실행 중인 GUI에서는 동기 `wait_until_complete()`를 그대로 붙여 넣지 않는다. `step_async()`와 `wait_until_complete_async()`를 사용해 앱에 제어권을 돌려준다. standalone에서 같은 작업을 할 때는 `SimulationApp`을 먼저 생성하고 동기 `step()`을 사용할 수 있다.

파일 저장 완료를 기다리는 것과 이미지가 올바른지 검사하는 것은 별개이다. 예제의 `validated_images`는 자동으로 `true`가 되지 않는다.

## 4. 출력 검사하기

출력 폴더에는 RGB PNG, 깊이 배열, 분할 배열/이미지와 클래스 대응 정보가 기록된다. 정확한 하위 경로는 Writer 설정에 따라 달라질 수 있으므로 먼저 파일 목록을 확인한다.

```bash
# 완료 메시지에 나온 실제 폴더로 바꾼다.
export SDG_OUTPUT="$HOME/isaacsim-course/outputs/sdg_실행시각"
rg --files "$SDG_OUTPUT"
cat "$SDG_OUTPUT/manifest.json"
```

| 확인 항목 | 통과 기준 | 실패했을 때 먼저 확인할 것 |
| --- | --- | --- |
| RGB | 큐브와 바닥이 보이고 10장이 저장됨 | 조명, 카메라 방향, 출력 경로 |
| 깊이 | 큐브가 있는 영역의 값이 양수이고 유한함 | 거리 종류, clipping 범위, 렌더 준비 |
| 분할 | 클래스 대응 정보에 `course_cube`가 있음 | 라벨 부착 위치와 Writer 옵션 |
| 프레임 대응 | 같은 번호의 RGB·깊이·분할이 같은 위치를 나타냄 | 중복 촬영, Writer 연결, 저장 완료 |
| 변화 | 프레임마다 큐브의 위치가 순서대로 변함 | Stage 속성 갱신과 촬영 순서 |
| 종료 | 창이 반응하고 다음 촬영에 VRAM이 계속 누적되지 않음 | Writer detach, Render Product destroy |

다음 코드는 NumPy와 Pillow가 설치된 Python에서 RGB 한 장의 기본 통계를 확인하는 예제이다. `RGB_FILE`을 실제 RGB PNG 경로로 지정한다.

```bash
export RGB_FILE="$SDG_OUTPUT/rgb_0000.png"
python3 - <<'PY'
import os
import numpy as np
from PIL import Image

image = np.asarray(Image.open(os.environ["RGB_FILE"]).convert("RGB"))
print("shape:", image.shape)
print("range:", int(image.min()), int(image.max()))
print("mean/std:", float(image.mean()), float(image.std()))
assert image.shape == (480, 640, 3)
assert image.max() > 0, "전체가 검은 영상이다."
assert image.std() > 1.0, "거의 단색이다. 장면과 조명을 직접 확인한다."
PY
```

이 통계는 이번 큐브 장면의 간단한 이상 감지이다. 실제 영상의 의미나 분할 정답을 판정하지 못하며, 이 통과만으로 전체 데이터셋 품질을 보장하지 않는다. NumPy/Pillow가 없다면 별도 가상환경에 설치하고 Isaac Sim의 Python 환경을 임의로 업그레이드하지 않는다.

## 5. 무작위 생성을 추가하는 순서

고정된 10장이 정상일 때부터 다음 순서로 범위를 넓힌다.

1. 큐브의 X 위치만 정해진 범위에서 무작위로 바꾼다. seed와 위치를 각 프레임에 기록한다.
2. XY 위치를 바꾸되 카메라 시야 밖이나 바닥 아래에 놓이지 않도록 범위를 제한한다.
3. 색상과 조명 세기를 바꾼다. 노출이 포화되거나 거의 검은 샘플의 비율을 확인한다.
4. 가리는 물체를 추가하고 목표 물체의 최소 가시 면적을 정한다.
5. asset과 배경을 늘리고 train/validation/test에 같은 장면이 중복되지 않도록 나눈다.

```yaml
dataset:
  version: 1
  isaac_sim: 5.1.0
  seed: 42
  frames: 1000
  resolution: [640, 480]
  classes: [course_cube]
  depth_kind: distance_to_camera
  depth_unit: meter
  x_range_m: [-0.45, 0.45]
  split_by: scene_seed
```

같은 seed가 모든 GPU에서 픽셀 단위로 같은 이미지를 보장하지 않는다. Isaac Sim 버전, 드라이버, GPU, asset 버전, 렌더 설정과 프레임 수를 함께 기록한다.

## 6. 더 큰 프로젝트로 이어가기

GUI로 녹화 조건을 먼저 확인하려면 [Synthetic Data Recorder](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html)를 사용한다. 설정 파일 중심의 배치 생성은 [Scene-based SDG](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html), 로봇 이동 경로와 센서 데이터 생성은 [Synthetic Data Generation 목록](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/index.html)에서 MobilityGen 과정으로 이어간다.

완료 기준은 파일 개수만 맞는 것이 아니다. 대표 RGB와 깊이·분할을 나란히 열어 보고, 클래스 분포와 프레임 대응을 확인하며, 취소한 실행의 일부 출력을 학습 데이터에 섞지 않아야 한다. 실제 렌더링 검증에는 Isaac Sim 5.1.0과 RTX GPU가 필요하다.

## 출처

- [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- [Scene-based SDG](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
- [Depth Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)
