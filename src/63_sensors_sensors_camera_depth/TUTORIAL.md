# 63. 같은 장면에서 두 깊이 값이 다른 이유

## 이번에 배우는 것

**카메라의 기하학적 깊이와 센서 후처리를 거친 깊이를 나란히 읽고, 거리·노이즈·시차 설정이 무엇을 바꾸는지 이해합니다.**

장면의 표면까지 거리를 정확히 안다고 해서 실제 깊이 센서와 같은 출력이 되는 것은 아닙니다. 깊이 센서 모델에는 시차 범위, 노이즈, 측정 거리 제한 등이 들어갑니다. 이번에는 한 카메라에서 두 종류의 깊이를 함께 얻어 그 차이를 살펴봅니다.

| 구성 | 값 또는 역할 |
|---|---|
| 카메라 위치 | 높이 4 m에서 아래를 바라봄 |
| 두 상자 높이 | 0.5 m와 1.2 m |
| `distance_to_image_plane` | 카메라 이미지 평면에 대한 기하학적 깊이 |
| `DepthSensorDistance` | 단일 시점 깊이 센서 후처리 결과 |
| `depth.npz` | 마지막 프레임의 두 깊이 배열 |
| `add_depth_sensor.py` | 깊이 설정을 가진 재사용 USD 자산을 만드는 별도 실행 파일 |

두 배열은 같은 장면을 보지만 생성 과정이 다릅니다. 먼저 장면 치수로 설명할 수 있는 기준 깊이를 찾고, 그 위에 센서 모델의 영향을 비교하겠습니다.

## 1. 두 종류의 깊이 저장하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/63_sensors_sensors_camera_depth/run.py --steps 240 --output src/63_sensors_sensors_camera_depth/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 240단계 후 `depth.npz`, `measurements.json`, `scene.usda`를 저장하고 종료합니다. 출력은 아직 없는 폴더를 지정합니다. `--output`을 생략하면 이 튜토리얼의 `output/날짜_시간/`에 저장합니다.

화면 없이 실행하려면 `--headless`를 추가하세요. GUI를 계속 관찰하려면 `--steps 240`을 뺍니다. 이 경우 첫 240단계의 마지막 프레임을 한 번 저장하고 카메라 갱신은 계속하지만, 파일은 더 이상 갱신하지 않습니다.

### 실행 결과 확인하기

`measurements.json`에는 두 배열 각각의 `shape`, `valid_pixels`, `median_m`이 있습니다. 유효 픽셀은 **유한한 양수**인 깊이만 셉니다. 코드도 두 배열 중 하나에 이런 값이 전혀 없으면 오류를 냅니다.

장면의 수직 치수로 이상적 깊이를 예상해 보세요.

| 관찰할 표면 | 높이 계산 | `distance_to_image_plane`의 기대 깊이 |
|---|---|---|
| 바닥 | 4 - 0 | 약 4 m |
| 낮은 상자 윗면 | 4 - 0.5 | 약 3.5 m |
| 높은 상자 윗면 | 4 - 1.2 | 약 2.8 m |

전체 이미지의 중앙값은 바닥 픽셀의 비중에 크게 영향을 받습니다. 두 상자의 깊이를 비교하려면 **각 상자 윗면 픽셀**을 비교해야 합니다. `median_m` 하나만 보고 상자 높이 차이가 사라졌다고 판단하지 마세요.

NPZ를 읽을 때는 다음처럼 두 키를 확인할 수 있습니다. 이 코드는 일반 NumPy 환경에서 저장된 데이터를 읽는 용도입니다.

```python
import numpy as np

data = np.load('src/63_sensors_sensors_camera_depth/output/base/depth.npz')
ideal = data['distance_to_image_plane']
modeled = data['DepthSensorDistance']
valid = np.isfinite(ideal) & np.isfinite(modeled) & (ideal > 0) & (modeled > 0)
print(ideal.shape, modeled.shape, np.count_nonzero(valid))
print('차이의 중앙값(m):', np.median(modeled[valid] - ideal[valid]))
```

차이는 같은 픽셀에서 계산해야 합니다. 두 배열에서 유효값만 각각 뽑은 뒤 순서대로 빼면 서로 다른 표면을 비교할 수 있습니다.

## 2. 깊이 후처리와 재사용 자산 살펴보기

### 코드에서 볼 부분

```python
camera.set_baseline_mm(args.baseline_mm)
camera.set_focal_length_pixel(320)
camera.set_max_disparity_pixel(110)
camera.set_noise_mean(.5)
camera.set_noise_sigma(args.noise_sigma)
camera.attach_annotator('DepthSensorDistance')
camera.attach_annotator('distance_to_image_plane')
```

Annotator는 render product에서 어떤 데이터를 읽을지 지정합니다. 여기서는 RGB를 붙이지 않고 깊이 출력 두 개를 요청합니다. 따라서 PNG가 없는 것은 정상이며 NPZ의 수치를 확인해야 합니다.

Stereo에서 시차는 같은 표면 점이 두 카메라 이미지의 서로 다른 픽셀에 나타나는 간격입니다. `baseline_mm`은 그 두 시점 사이 간격에 대응하는 모델 값입니다. 기본 55는 **55 mm**, 저장 깊이는 **m**입니다. 초점 값 320은 **픽셀**입니다. 단위가 서로 다른 이유는 깊이를 시차로 바꾸는 관계에 각각 다른 역할로 들어가기 때문입니다.

```text
시차(픽셀) ≈ 초점 값(픽셀) × baseline(m) / 깊이(m)
```

이 설정에서 깊이 4 m의 시차는 약 `320 × 0.055 / 4 = 4.4` 픽셀입니다. 먼 표면은 시차가 작아 같은 시차 변화가 거리값에 더 크게 반영될 수 있습니다. `SingleViewDepthSensor`는 이런 특성을 하나의 렌더 시점에 후처리로 적용합니다. 실제 좌우 영상의 stereo 매칭 전체를 수행하는 코드는 아닙니다.

### 설정을 USD로 저장하기

측정과 별도로, 깊이 카메라 설정을 자산으로 만들 수 있습니다.

```bash
~/isaacsim/python.sh src/63_sensors_sensors_camera_depth/add_depth_sensor.py --headless --output src/63_sensors_sensors_camera_depth/output/depth_camera.usd
```

위 headless 명령은 장면 깊이를 측정하지 않고 파일을 만든 뒤 한 번 앱을 갱신하고 종료합니다. `--headless`를 빼면 창을 직접 닫을 때까지 작성된 Stage를 볼 수 있습니다. GUI에서도 유한하게 실행하려면 양수 `--steps`로 앱 업데이트 횟수를 지정하세요.

```python
SingleViewDepthSensorAsset.add_template_render_product(
    parent_prim_path='/root/TemplateRenderProduct',
    camera_prim_path='/root/Camera',
    **{'omni:rtx:post:depthSensor:baselineMM': 42},
)
```

`/root/Camera`와 연결된 템플릿 render product에 baseline 42 mm를 저장합니다. 앞의 측정 실행 기본값 55 mm와는 다른, **이 자산 작성 예제의 설정**입니다. 자산을 저장했다는 사실과 깊이 배열을 생성했다는 사실을 구별하세요.

### 뷰포트와 기존 센서 자산에서 확인하기

기본 장면을 `--steps` 없이 열어 두고 뷰포트를 `/World/Depth`로 전환하세요. **Render Settings > Post Processing > Depth Sensor**를 켠 뒤 **RGB Depth Output Mode > Disparity**를 선택하면 시차를 색으로 볼 수 있습니다. 전역 설정은 다른 render product에도 적용되므로 이 관찰은 NPZ 비교를 마친 뒤 진행합니다. 색의 밝기를 곧바로 미터 거리로 해석하지 마세요.

기존 자산의 템플릿을 읽는 방식도 확인할 수 있습니다. 새 Isaac Sim 창의 빈 stage에서 **Window > Script Editor**를 열고 다음 코드를 실행하세요. 5.1 Assets의 RealSense D455와 종속 자산에 접근할 수 있어야 하며, 이 코드는 `run.py`에 붙이는 코드가 아닙니다.

```python
from isaacsim.sensors.camera import SingleViewDepthSensorAsset
from isaacsim.storage.native import get_assets_root_path

asset = SingleViewDepthSensorAsset(
    '/World/D455',
    asset_path=get_assets_root_path() + '/Isaac/Sensors/Intel/RealSense/rsd455.usd',
)
asset.initialize()
print(asset.get_all_depth_sensor_paths())
depth = asset.get_child_depth_sensor('/World/D455/RSD455/Camera_Pseudo_Depth')
depth.attach_annotator('DepthSensorDistance')
```

출력 목록의 카메라 경로와 Stage의 경로를 대조하세요. wrapper는 저장된 템플릿에서 후처리 속성을 읽고 실제 render product에 복사합니다. 목록이 생긴 것은 자산과 카메라 연결을 확인한 것이며, 깊이 값은 재생과 렌더링 후에 얻습니다. D455의 pseudo depth 역시 실제 stereo 펌웨어를 실행한 결과는 아닙니다. [공식 깊이 자산 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)을 함께 확인할 수 있습니다.

## 3. 기준 깊이와 센서 모델의 차이 정리

```text
같은 카메라·같은 표면
    ├─ 기하학적 깊이 → distance_to_image_plane
    └─ 깊이 후처리 → 시차·노이즈·거리 제한 → DepthSensorDistance
```

장면 치수는 기준 깊이를 확인하는 데 쓰고, 두 배열의 픽셀별 차이는 후처리 영향을 확인하는 데 씁니다. 카메라가 30 Hz이고 물리·렌더링은 60 Hz이므로, 이번 NPZ는 240개의 독립 깊이 영상을 담은 파일이 아니라 마지막 깊이 한 쌍입니다.

## 4. 간단한 확인 실험

노이즈의 표준편차만 1에서 0으로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/63_sensors_sensors_camera_depth/run.py --steps 240 --noise-sigma 0 --output src/63_sensors_sensors_camera_depth/output/sigma-zero
```

두 실행에서 바닥이나 상자 윗면의 같은 영역을 골라 후처리 깊이의 퍼짐을 비교하세요. 노이즈의 무작위 변동은 줄어들 것으로 예상하지만 `noise_mean=0.5`, 시차 제한, 거리 제한은 그대로입니다. 따라서 **표준편차 0이 이상적 깊이와 완전히 같다는 뜻은 아닙니다.**

## 실행할 때 막히면

- **`No finite positive depth`**: 새 출력 경로에서 `--steps 480`으로 렌더 준비 시간을 늘려 보세요. 마지막까지 유효 깊이가 없으면 결과를 사용할 수 없습니다.
- **첫 프레임의 texture-size/AOV 오류**: 공식 5.1 문서에 초기 프레임 문제가 기록되어 있습니다. 이후 배열이 실제로 채워지는지 확인하고, 계속 반복되는 오류까지 정상으로 처리하지 마세요.
- **GUI의 색과 깊이 수치가 맞지 않음**: Disparity 등 시각화 모드의 색은 미터값 자체가 아닙니다. NPZ의 깊이 배열을 읽으세요.
- **비교할 때 두 출력이 함께 달라짐**: 전역 Render Settings를 바꿨다면 다른 render product에도 영향을 줄 수 있습니다. 비교 실행은 동일한 장면 설정에서 시작하세요.
- **USD는 생겼지만 `depth.npz`가 없음**: `add_depth_sensor.py`는 자산 작성용입니다. 깊이 측정에는 `run.py`를 사용하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Depth Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)에 대응합니다. 로컬 두 상자로 두 annotator를 비교하고, 별도 스크립트로 깊이 카메라 설정의 USD 저장을 다룹니다.

이번 개정에서는 두 실행 파일과 공식 후처리·자산 작성 절차를 대조했습니다. 실제 깊이 렌더링은 실행하지 않았으며 `tutorial.json`의 검증 상태는 `not_run`입니다. 위 거리와 차이는 실행 시 확인할 기준입니다.
