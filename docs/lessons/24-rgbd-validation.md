# 24. RGB와 깊이 프레임을 수치로 검사하다

## 목표와 준비

23단계의 정지 장면에서 RGB와 깊이를 동시에 저장하고 빈 프레임, 블랙아웃, 잘못된 깊이, 과도한 시간 변화가 검사를 통과하지 못하게 한다. 이 단계의 깊이는 렌더러가 계산한 **이상적인 기하 깊이**이다. 실제 RGBD 카메라의 스테레오 오차·반사·노출·노이즈 모델을 재현한 결과와 구분한다.

## 1. Authoring 객체와 Runtime 객체를 연결하다

`RtxCamera`는 카메라의 위치·광학 설정을 USD에 구성한다. `CameraSensor`는 필요한 Annotator를 붙여 배열을 읽는다. 둘을 나누면 이미 GUI로 만든 카메라도 Runtime 객체로 감싸서 사용할 수 있다.

```python
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor

camera = RtxCamera("/World/Camera", translations=[[0, 0, 3]], tick_rate=30)
sensor = CameraSensor(
    camera,
    resolution=(240, 320),  # 6.0.1 새 API는 (높이, 너비)이다.
    annotators=["rgb", "distance_to_image_plane"],
)
```

이미 `/World/Camera`가 존재한다면 `CameraSensor("/World/Camera", ...)`처럼 경로를 넘길 수도 있다. 같은 경로에 두 센서를 반복 생성하는 것은 피하고 장면 생성과 데이터 수집의 수명을 함께 관리한다.

## 2. 두 깊이 정의를 구분하다

| Annotator | 반환하는 거리 | 의미 |
| --- | --- | --- |
| `distance_to_image_plane` | 카메라 광축 방향의 깊이 | 일반적인 핀홀 투영식의 Z |
| `distance_to_camera` | 카메라 중심까지의 거리 | 광축 밖에서는 Z보다 길어지다 |

광축 방향 깊이 Z를 3차원 점으로 바꾸는 개념은 다음과 같다. 이 예제의 `fx`, `fy`, `cx`, `cy`는 설명용 숫자이다. 실제 처리에서는 카메라의 보정값이나 CameraInfo를 사용한다.

```python
u, v, depth_z = 160, 120, 3.0
fx, fy, cx, cy = 365.0, 365.0, 160.0, 120.0
x_optical = (u-cx) * depth_z / fx
y_optical = (v-cy) * depth_z / fy
z_optical = depth_z
print(x_optical, y_optical, z_optical)  # optical frame에서 (0, 0, 3)
```

## 3. 렌더링을 진행한 뒤 읽다

센서 생성 직후에는 배열이 없을 수 있다. 제공 프로그램은 120번의 준비 갱신 후 12번씩 앱을 더 갱신하며 10개의 표본을 읽는다. `get_data()`는 `(Warp 배열 또는 None, info)`를 반환한다.

```python
# Standalone 루프 안의 핵심이다. Script Editor에서 app을 새로 만들지 않는다.
for _ in range(120):
    app.update()
rgb, rgb_info = sensor.get_data("rgb")
depth, depth_info = sensor.get_data("distance_to_image_plane")
if rgb is None or depth is None:
    raise RuntimeError("준비 시간 뒤에도 카메라 프레임이 없다")
rgb_np = rgb.numpy().copy()
depth_np = depth.numpy().copy()
```

`.copy()`는 다음 렌더링이 내부 버퍼를 갱신해도 이번 표본을 유지하기 위해 사용한다. 앱이 꺼진 뒤 GPU 메모리에 남은 버퍼를 읽으려고 하지 않는다.

## 4. 자동 검사를 실행하다

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/04_camera_check.py \
  --headless --warmup 120 --samples 10 \
  --output-dir artifacts/rgbd-check
```

| 검사 | 기본 장면의 합격 기준 |
| --- | --- |
| 배열 형태 | RGB `(240, 320, 3 또는 4)`, 깊이 `(240, 320)` |
| RGB 값 | uint8이고 모든 채널 값이 유한하다 |
| 블랙아웃·단색 화면 | 평균과 채널별 공간 표준편차의 최댓값이 각각 2 초과, 검은 픽셀 비율 98% 미만이다 |
| 깊이 유효값 | 0~10 m 사이의 유한한 양수 픽셀이 90% 이상이다 |
| 깊이 거리 | 유효 깊이 중앙값이 2~3.2 m이다 |
| 알려진 표적 영역 | 바닥 3.0 m, 빨강 상자 2.6 m, 파랑 상자 2.4 m의 내부 영역 깊이가 각각 ±0.05 m 안이다 |
| 표적 색 | 빨강·파랑 상자 위치에서 해당 색 채널이 다른 채널보다 1.3배 이상 크다 |
| 정지 장면의 RGB 변화 | 표본 사이 평균 절대 변화가 15 이하이다 |
| 이상적 깊이 변화 | 유한한 픽셀의 평균 절대 변화가 0.02 m 이하이다 |

이 값은 불량 프레임을 알아보기 위해 설계한 검사 장면에만 적용한다. 실제 야간 장면이 어둡다는 이유로 불량이라는 뜻은 아니다. 하늘을 보는 센서에서는 inf 깊이가 정상적인 미검출 표현일 수 있지만, 바닥으로 시야 전체를 덮은 이번 장면에서 대부분의 깊이가 inf면 실패이다.

## 5. 결과를 다시 읽다

```bash
python3 - <<'PY'
import json
import numpy as np
from pathlib import Path
folder = Path('artifacts/rgbd-check')
report = json.loads((folder/'report.json').read_text())
print('합격:', report['passed'])
for frame in report['frames']:
    print(frame['sample'], frame['passed'], frame['failures'])
if not report['passed']:
    raise SystemExit(1)
frames = np.load(folder/'camera_frames.npz')
print('RGB 전체 배열:', frames['rgb'].shape)
print('깊이 전체 배열:', frames['depth'].shape)
PY
```

실패한 프레임도 `rgb_000.npy`, `depth_000.npy` 같은 개별 파일로 저장한다. 보고서에는 각 표본의 형태·밝기·깊이 통계와 실패 사유가 남는다. 준비 시간 이후 하나라도 실패하면 프로그램은 실패 종료한다.

## 기대 결과, 제한과 진단

두 색의 상자가 있는 `rgb_preview.png`, 모든 원시 프레임, `report.json`이 만들어진다. 이번 정지 장면만으로 카메라가 계속 새 timestamp를 내는지 입증할 수는 없다. ROS에서의 timestamp와 수신 빈도 검사는 뒤의 ROS 실습에서 추가한다. 작성 환경에서는 GPU 실행을 하지 못했으며 실제 측정값은 사용자의 실행으로 생성해야 한다.

검사가 실패하면 해상도 순서, sensor 경로, 조명, 렌더링 갱신을 먼저 확인한다. 임계값을 낮춰 실패를 지우기 전에 저장된 원시 배열과 그림을 살펴본다.

## 확인 과제와 실행 파일

[04_camera_check.py](../../examples/04_camera_check.py)와 [sensor_metrics.py](../../examples/sensor_metrics.py)를 읽고, 빈 깊이 배열과 전체 inf 배열이 각각 어떤 검사에서 실패하는지 설명한다. `np.nan_to_num()`으로 깊이를 모두 0으로 바꾸면 원래 실패의 원인이 사라지는 이유도 확인한다.

## 공식 참고 자료

- [6.0.1 카메라 센서와 Annotator](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_camera.html)
- [6.0.1 CameraSensor 반환값·해상도 규약](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.sensors.experimental.rtx/docs/index.html)
- [6.0.1 물리적 깊이 센서 모델](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_camera_depth.html)

[이전](23-camera-coordinates.md) · [다음](25-rtx-lidar.md)
