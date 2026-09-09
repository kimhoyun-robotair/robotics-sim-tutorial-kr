# 27. 중간 프로젝트 5 — RGBD·LiDAR 센서 검사실을 만들다

## 프로젝트 목표와 준비

23~26단계의 센서 지식을 사용하여 RGBD와 LiDAR의 검사 결과를 한 폴더에 모은다. 센서를 로봇에 장착하기 전에 독립적인 기준 결과를 확보하는 프로젝트이다. 카메라와 LiDAR의 기본 검사는 각각의 작은 장면에서 실행하며, 동시에 실행한 복합 장면의 성능 검증으로 해석하지 않는다.

이번 프로젝트의 산출물은 두 센서의 원시 데이터, 미리보기, 검사 보고서와 두 결과를 확인한 통합 JSON이다. 로봇이 무너지거나 GPU 부하가 늘었을 때 센서 자체의 기준 결과와 비교할 수 있게 한다.

## 1. 결과 폴더를 새로 만들다

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$TUTORIAL_ROOT"
mkdir -p artifacts/project05
```

이전 결과를 비교 기준으로 유지하려면 `project05-run02`처럼 새 이름을 사용한다. 아래 명령에서 폴더 이름을 한 번 정하면 모두 같은 경로를 사용한다.

## 2. 카메라 검사를 실행하다

```bash
"$ISAAC_SIM_PATH/python.sh" examples/04_camera_check.py \
  --headless --warmup 120 --samples 10 \
  --output-dir artifacts/project05/camera
```

`camera/report.json`을 먼저 읽고, 합격했더라도 `rgb_preview.png`에서 빨강·파랑 상자가 실제로 보이는지 확인한다. 수치 검사는 블랙아웃과 비정상 깊이 등을 잡지만 사람이 의도한 장면의 의미까지 모두 보장하지 않는다.

## 3. LiDAR 검사를 실행하다

```bash
"$ISAAC_SIM_PATH/python.sh" examples/05_lidar_check.py \
  --headless --warmup 120 --samples 10 \
  --output-dir artifacts/project05/lidar
```

`lidar/report.json`에서 timestamp가 증가하고 방향 구간이 충분히 채워지는지 확인한다. 첫 스캔의 점 배열은 다음 코드로 살펴볼 수 있다.

```bash
python3 - <<'PY'
import numpy as np
scan = np.load('artifacts/project05/lidar/scan_000.npz')
points = scan['points']
print('점 배열:', points.shape)
if points.size == 0 or not np.isfinite(points).all():
    raise SystemExit('비어 있거나 유효하지 않은 점군이다')
print('XYZ 범위:', points.min(axis=0), points.max(axis=0))
print('거리 중앙값:', np.median(np.linalg.norm(points, axis=1)))
PY
```

LiDAR 원점이 센서 위치이므로 바닥과 천장은 대략 센서 높이의 아래·위쪽에 나타난다. 일반 로봇에 달았을 때 센서 좌표와 월드 좌표를 섞지 않는 연습이다.

## 4. 두 결과를 엄격하게 합치다

보고서 파일이 없거나 실패한 실행이면 통합 결과도 실패한다. 빈 보고서 목록에 `all()`만 적용하여 합격하는 경우를 막기 위해 예상한 파일 두 개를 명시한다.

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('artifacts/project05')
combined = {'passed': False, 'components': {}, 'errors': []}
for name, field in [('camera', 'frames'), ('lidar', 'scans')]:
    path = root / name / 'report.json'
    try:
        result = json.loads(path.read_text())
        samples = result.get(field, [])
        passed = (result.get('passed') is True and not result.get('error')
                  and len(samples) >= 3
                  and all(sample.get('passed') is True for sample in samples))
        combined['components'][name] = {'passed': passed, 'sample_count': len(samples)}
        if not passed:
            combined['errors'].append(f'{name}: 검사 실패 또는 표본 부족')
    except (OSError, ValueError, TypeError, AttributeError) as error:
        combined['components'][name] = {'passed': False}
        combined['errors'].append(f'{name}: {error}')
combined['passed'] = not combined['errors'] and len(combined['components']) == 2
(root / 'report.json').write_text(json.dumps(combined, ensure_ascii=False, indent=2))
print(json.dumps(combined, ensure_ascii=False, indent=2))
raise SystemExit(0 if combined['passed'] else 1)
PY
```

## 5. 검사가 불량 입력을 거부하는지 확인하다

실제 GPU 실행과 별개로, 저장소에는 수치 검사 함수의 CPU 테스트도 제공한다. 시스템 Python에 NumPy가 없다면 2단계에서 준비한 Python 환경을 사용한다. Isaac Sim 실행기를 사용해도 된다.

```bash
"$ISAAC_SIM_PATH/python.sh" -m unittest discover -s tests -p test_sensor_metrics.py -v
```

테스트는 정상 배열의 통과뿐 아니라 빈 배열, 검은 영상, NaN·inf 깊이, 잘못된 배열 크기, 한쪽에만 있는 부분 스캔이 실패하는지도 확인한다. CPU 테스트의 성공은 렌더러 실행 성공과 다른 검증 결과이다.

## 기대 결과와 완료 기준

| 결과 | 확인할 내용 |
| --- | --- |
| `camera/report.json` | 모든 표본의 밝기·깊이 검사에 합격하다 |
| `camera/rgb_preview.png` | 의도한 색상 표적과 바닥이 보이다 |
| `lidar/report.json` | 새 스캔 10개와 넓은 각도 범위를 확인하다 |
| `lidar/scan_000.npz` 등 | 유효한 원시 점군을 다시 읽을 수 있다 |
| `project05/report.json` | 예상한 센서 두 개의 검사 결과를 포함하다 |

보고서에 적힌 수치와 실제 영상을 함께 확인해야 프로젝트가 끝난다. 이 저장소를 작성한 환경에서는 RTX 센서를 실행하지 못했다. 미리 만들어 놓은 성공 보고서 대신 사용자의 장비에서 생성한 결과가 필요하다.

## 문제 진단과 확장 과제

각 센서가 따로 통과하는데 같은 로봇 장면에서 실패한다면 장착 방향, 가림, Render Product 수, GPU 메모리, 실행 주기를 비교한다. 실패를 줄이기 위해 센서 갱신을 끄고 이전 배열을 계속 내보내는 방식은 사용하지 않는다.

26단계의 IMU·접촉 결과도 `project05/physics`에 저장하여 통합 보고서를 확장한다. 센서마다 의미가 다른 검사를 유지한다. LiDAR의 VALID 플래그나 접촉 센서의 `in_contact`를 RGB의 밝기처럼 검사할 수는 없다.

## 실행 파일과 공식 참고 자료

- [카메라 검사](../../examples/04_camera_check.py), [LiDAR 검사](../../examples/05_lidar_check.py), [공통 수치 검사](../../examples/sensor_metrics.py)
- [6.0.1 RTX 센서 API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.sensors.experimental.rtx/docs/index.html)
- [6.0.1 센서 배치·보정 관련 카메라 자료](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_camera.html)

[이전](26-imu-contact.md) · [다음](28-performance-diagnostics.md)
