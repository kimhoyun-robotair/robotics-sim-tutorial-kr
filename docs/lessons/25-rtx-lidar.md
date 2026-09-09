# 25. RTX LiDAR의 한 바퀴 스캔을 검증하다

## 목표와 준비

RTX LiDAR를 방 가운데 설치하고 벽을 측정한다. 점이 조금 보인다는 이유로 성공이라 판단하지 않고, 한 바퀴의 방향 범위와 새 timestamp, 거리의 유효성을 검사한다. 24단계 카메라 검사를 마친 뒤 별도 프로세스에서 실행한다.

RTX LiDAR는 렌더링 시점에 GPU에서 광선을 계산한다. 물리 스텝만 진행하고 렌더링을 생략하면 센서가 갱신되지 않을 수 있다. 이 실습은 멀티 GPU 관련 문제를 분리하기 위해 `SimulationApp`에 `multi_gpu=False`를 지정한다.

## 1. scan rate와 tick rate를 맞추다

- `scanRateBaseHz`는 센서 스캔의 기본 주기이다.
- `tick_rate`는 센서가 출력을 만드는 주기를 정한다.
- `accumulate_outputs=True`는 여러 갱신에 걸친 측정을 누적하여 완성된 스캔을 얻는 설정이다.

6.0.1에서는 **OmniLidar의 tick_rate와 scanRateBaseHz를 같게 설정해야 한다.** 두 값이 다르면 오류 메시지 없이 부분 스캔이 나올 수 있다. 예제는 둘을 10 Hz로 고정한다.

```python
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

lidar = Lidar.create(
    "/World/Lidar",
    config="Example_Rotary",
    tick_rate=10.0,
    translations=[[0.0, 0.0, 1.5]],
    orientations=[[1.0, 0.0, 0.0, 0.0]],
    accumulate_outputs=True,
    attributes={"omni:sensor:Core:scanRateBaseHz": 10.0},
)
sensor = LidarSensor(lidar, annotators=["generic-model-output"])
```

`Example_Rotary` 설정은 Isaac Sim의 센서 자료를 사용한다. 자산 접근에 실패하면 실습을 성공 처리하지 않는다. 외부 자산을 내려받는 환경에서는 첫 실행에 로딩 시간이 추가될 수 있다.

## 2. 측정용 방을 구성하다

제공 프로그램은 내부 벽을 X/Y의 ±3 m에, 바닥을 Z=0 m에, 천장을 Z=3 m에 둔다. LiDAR는 중앙의 높이 1.5 m에 있으므로 어느 방향을 보더라도 표면을 만난다. 센서가 벽이나 로봇 내부에 들어가지 않는 기준 장면이다.

```python
# 바깥쪽 중심이 x=3.05이고 두께가 0.1이므로 안쪽 벽은 x=3.0이다.
wall_center = (3.05, 0.0, 1.5)
wall_size = (0.1, 6.2, 3.0)
print(wall_center[0] - wall_size[0]/2)  # 3.0
```

실제 로봇에 옮길 때는 센서의 케이스와 장착물도 광선을 가릴 수 있다. 이 단계에서 정상 결과를 얻은 뒤 로봇에 붙여야 가림 문제를 분리할 수 있다.

## 3. GMO를 좌표 배열로 바꾸다

GenericModelOutput(GMO)은 RTX 센서가 전달하는 공통 버퍼이다. `x`, `y`, `z`라는 이름만 보고 항상 XYZ 위치라 생각하면 안 된다. `elementsCoordsType`이 SPHERICAL이면 각각 방위각(degree), 고도각(degree), 거리(m)이다.

```python
import numpy as np
from isaacsim.sensors.experimental.rtx import parse_generic_model_output_data
from omni.sensors.generic_model_output import CoordsType

data, info = sensor.get_data("generic-model-output")
if data is None or data.size == 0:
    raise RuntimeError("LiDAR 데이터가 없다")
gmo = parse_generic_model_output_data(data)
if gmo.elementsCoordsType == CoordsType.SPHERICAL:
    az = np.radians(gmo.x)
    el = np.radians(gmo.y)
    r = np.array(gmo.z, copy=True)
    points = np.column_stack([
        r*np.cos(el)*np.cos(az),
        r*np.cos(el)*np.sin(az),
        r*np.sin(el),
    ])
elif gmo.elementsCoordsType == CoordsType.CARTESIAN:
    points = np.column_stack([gmo.x, gmo.y, gmo.z])
else:
    raise RuntimeError("지원하지 않는 좌표 형식이다")
```

완결 파일은 `ElementFlags.VALID`도 확인하여 유효한 반사점만 검사한다. 알려지지 않은 필드를 추측해서 배열로 해석하지 않는다. 좌표 기준도 SENSOR인지 검사한다. 월드 좌표를 센서 좌표라고 간주하면 로봇에 장착한 뒤 RViz에서 위치가 어긋난다.

## 4. 실행하고 결과를 읽다

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/05_lidar_check.py \
  --headless --output-dir artifacts/lidar-check
python3 - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('artifacts/lidar-check/report.json').read_text())
print('합격:', result['passed'])
for scan in result['scans']:
    print(scan['timestamp_ns'], scan['point_count'],
          scan['occupied_30deg_sectors'], scan['failures'])
if not result['passed']:
    raise SystemExit(1)
PY
```

준비 갱신 120회 후 서로 다른 timestamp의 스캔 10개를 수집한다. 시도 횟수에 상한이 있으므로 센서가 영원히 비어 있어도 무한 대기하지 않는다. 다음 조건을 확인한다.

| 검사 | 합격 기준 |
| --- | --- |
| 새 스캔 | timestamp가 이전 표본보다 증가하다 |
| 점 개수 | 유효 XYZ 점이 100개 이상이다 |
| 수치 | 유효한 점에 NaN·inf가 없다 |
| 거리 | 점의 95% 이상이 0.1~10 m 안에 있다 |
| 방향 범위 | 30°씩 나눈 12구간 중 11구간 이상에서 점이 있다 |
| 실제 방의 표면 | 점의 95% 이상이 방 경계 안에 있고 X/Y=±3 m 또는 Z=±1.5 m 표면에서 0.1 m 이내이다 |
| GMO 유효 반사 | 폐쇄된 방에서 VALID 반사 비율이 90% 이상이다 |

방향 구간 검사는 스캔이 한쪽 부채꼴에만 생기는 문제를 잡기 위한 것이다. 제조사의 각 해상도나 모든 빔의 완전성을 검증하는 정밀 교정은 아니다.

## 기대 결과와 문제 진단

`gmo_000.npy`에는 파싱 전 원시 버퍼가, `scan_000.npz`에는 원래 필드와 변환된 점이 저장된다. `report.json`은 실패 이유를 기록한다. GUI로 보고 싶으면 `--headless`를 빼고 실행한다. 점 시각화는 센서 데이터 수집과 별도 기능이므로 Viewport에서 점이 안 보인다는 이유만으로 배열이 비어 있다고 판단하지 않는다.

| 문제 | 확인하다 |
| --- | --- |
| 한쪽 방향에만 점이 생기다 | tick/scan 주기 일치와 누적 설정을 확인한다. |
| 거의 모든 점이 매우 가깝다 | 센서가 메쉬 내부에 있는지 확인한다. |
| CUDA 700과 함께 종료하다 | 단일 GPU 실행 및 공식 Known Issues를 확인한다. |
| 방위각이 위치처럼 보이다 | GMO의 SPHERICAL/CARTESIAN을 확인한다. |
| 계속 같은 스캔을 읽다 | 렌더링 갱신과 timestamp 증가를 확인한다. |

## 과제와 실행 파일

[05_lidar_check.py](../../examples/05_lidar_check.py)에서 방향 범위를 검사하는 부분을 찾는다. scan rate만 20 Hz로 바꾸면 왜 잘못된 실험인지 설명한다. 비교하려면 tick rate도 함께 바꾸고 새로운 결과 폴더를 사용한다. 작성 환경에는 Isaac Sim/GPU가 없어 이 RTX 실행 결과는 아직 측정하지 않았다.

## 공식 참고 자료

- [6.0.1 RTX LiDAR 생성과 주기 설정](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_rtx_lidar.html)
- [6.0.1 Multi-Tick Rendering의 주기 일치 조건](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html)
- [6.0.1 GenericModelOutput의 Python binding과 좌표 정의](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/docs/source/generic_model_output/generic_model_output.html)
- [6.0.1 RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_rtx_annotators.html)

[이전](24-rgbd-validation.md) · [다음](26-imu-contact.md)
