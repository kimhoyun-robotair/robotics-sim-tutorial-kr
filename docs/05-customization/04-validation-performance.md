# 커스텀 자산 검증, 성능 최적화와 회귀시험

## 먼저 저장소의 실행 검증을 수행한다

이 장에는 사용자 자산에 맞게 수정하는 코드 조각과 바로 실행하는 검증 파일이 함께 있다. 첫 실행은 아래 네 예제로 시작한다. 각 예제는 새 프로세스에서 Isaac Sim을 열고 정해진 스텝 수만 실행하며, 검사가 끝나면 종료한다. 공통 실행 코드는 단일 GPU와 `RayTracedLighting`을 사용한다.

저장소 루트에서 다음 명령을 실행한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
python3 scripts/validate_runtime.py \
  --isaacsim-path "$ISAACSIM_PATH" \
  --output-dir results/runtime \
  --timeout 600
```

외부 실행기는 시스템 Python으로 실행하고, 실제 시뮬레이션은 지정한 설치 폴더의 `python.sh`로 실행한다. 첫 실행의 셰이더 준비나 자산 다운로드가 오래 걸려 600초를 넘기면 로그에서 진행 여부를 확인한 뒤 `--timeout 1200`으로 다시 실행한다. 프로그램이 멈춘 상태를 무한히 기다리지는 않는다.

| 실행 파일 | 구성과 검사 | 남기는 자료 |
|---|---|---|
| [hello_stage.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/hello_stage.py) | 0.2 m·1 kg 큐브를 1 m 높이에서 떨어뜨리고, 바닥 위 높이 0.1 m와 잔류 속도를 검사한다. 초기화 후 한 번 더 반복한다. | `result.json` |
| [drive_jetbot.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/drive_jetbot.py) | 공식 Jetbot 자산의 충돌 형상이 바닥과 겹치지 않는지 검사한 뒤, 정지·완만한 가속·직진·감속·초기화를 수행한다. 기울기·높이·바퀴 속도를 확인한다. | `result.json`, `drive.csv` |
| [camera_imu.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/camera_imu.py) | 조명이 있는 기준 장면에서 RGB·깊이 30개 프레임과 정지 IMU를 검사한다. 중앙의 빨간 물체, 예상 깊이 2.5 m, 유효 판독값과 시간 증가를 확인한다. | `result.json`, `rgb.png`, `frames/`의 PNG 30장, `sensor_data.npz` |
| [rtx_lidar.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/rtx_lidar.py) | 원점의 LiDAR를 3 m 떨어진 여섯 벽으로 둘러싼다. 점 수·유한값·벽까지의 거리 오차와 새 데이터 도착을 검사한다. | `result.json`, `lidar_data.npz` |

결과는 `results/runtime/<UTC 시각>/summary.json`에 모이며 각 예제 폴더에 `runtime.log`가 남는다. 실행기는 GPU 이름·드라이버·VRAM, 설치 버전, Git 커밋과 실행 파일의 SHA-256도 기록한다. 기존 결과를 덮어쓰지 않고 새 폴더를 만들어, 이전 실행의 `PASS`가 잘못 재사용되지 않게 한다.

| 결과 | 의미 | 종료 코드 |
|---|---|---:|
| `PASS` | 선택한 범위의 실제 실행과 수치 검사가 통과했다. | 0 |
| `FAIL` 또는 개별 `TIMEOUT`·`INTERRUPTED` | 실행 오류·수치 오차·치명적인 GPU 오류·시간 초과·사용자 중단이 발생했다. | 1 |
| `NOT_RUN` | Isaac Sim 5.1.0 설치나 NVIDIA GPU를 확인하지 못해 실행하지 않았다. | 2 |

`--only camera_imu`처럼 일부만 실행하면 `complete_suite`가 `false`로 기록된다. 이 결과를 전체 센서·로봇의 합격으로 해석하지 않는다. 구문 검사, 링크 검사, 공식 API 대조만으로는 렌더링·관절 안정성·물리 접촉이 검증되지 않는다. 이 작업 환경에서 실제 GPU 실행이 가능한지는 [검증 결과](../appendices/validation-report.md)에 따로 기록한다.

### 센서가 멈췄는데 정상처럼 보이는 경우를 막는다

Isaac Sim 5.1의 `Camera.get_current_frame()["rendering_frame"]`은 단순 프레임 번호가 아니라 Fabric 시간 정보를 담은 사전일 수 있다. `LidarRtx`는 시간의 분자·분모를 튜플로 저장한다. 따라서 두 값을 정수로 바꾸거나 `+1`로 검사하지 않는다. 새 데이터 여부는 `rendering_time`이 증가하는지로 확인한다.

IMU의 `get_current_frame()`은 새 판독이 유효하지 않을 때 이전 사전 내용을 유지할 수 있다. 정지 상태에서 가속도 값이 그럴듯해도 센서가 살아 있다고 단정할 수 없다. 실행 예제는 다음 두 조건을 함께 확인한다.

```python
# SimulationApp과 World를 만들고, IMU가 달린 강체를 초기화한 뒤 실행한다.
from isaacsim.sensors.physics import _sensor

interface = _sensor.acquire_imu_sensor_interface()
reading = interface.get_sensor_reading(
    imu.prim_path, use_latest_data=True, read_gravity=True
)
if not reading.is_valid:
    raise RuntimeError("IMU의 현재 판독값이 유효하지 않다")
if reading.time <= previous_imu_time:
    raise RuntimeError("IMU 시간이 증가하지 않는다")
previous_imu_time = reading.time
```

카메라는 빈 배열·NaN·검은 영상·완전히 포화된 영상·중앙 물체 누락·잘못된 깊이를 구분한다. 배경에 닿지 않은 광선의 깊이가 `Inf`가 되는 것은 정상일 수 있으므로 모든 깊이 픽셀에 무조건 유한값을 요구하지 않는다. 기준 물체가 있는 중앙 영역에서는 양의 유한 깊이와 허용오차를 요구한다. `camera_imu.py`의 출력 주기는 실제 측정값으로 기록하며, 정밀한 30 Hz 보정 시험과 기본 영상 생성 시험을 구분한다.

### 자동 검사와 눈으로 확인할 항목을 함께 사용한다

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/camera_imu.py \
  --gui --output-dir results/camera_visual
```

`rgb.png`와 `frames/`의 연속 이미지 30장에서 표면의 줄무늬·깜박임·잔상·왜곡을 확인한다. 영상의 평균값과 깊이가 맞아도 모든 렌더링 결함을 잡을 수는 없다. GPU 메모리 부족, 드라이버 오류, 해상도 변경, DLSS 설정, 여러 GPU 사용은 별도 조건으로 시험한다. 단일 GPU의 짧은 기준 장면이 통과했다는 결과는 다른 로봇·센서 조합이나 장시간 프로젝트가 무조건 안정적이라는 보장이 아니다.


## 기준 장면의 합격 조건

다음 값은 이 저장소가 만든 작은 장면의 검사 기준이다. 모든 로봇과 센서에 그대로 적용하는 NVIDIA 공통 규격이 아니다.

| 검사 | 실제 코드에서 확인하는 값 | 그 값으로 확인하는 문제 |
| --- | --- | --- |
| Cube | 마지막 60 step에서 중심 높이 0.1 m ±0.02 m, 속도 0.05 m/s 미만 | 바닥 통과, 낙하 후 지속적인 움직임 |
| Jetbot | 정지 후 기울기 25° 이내, 높이 변화 0.05 m 미만 | 전도, 갑작스러운 상승·침하 |
| 직진·정지 | X 이동 0.10~0.50 m, 횡방향 오차 0.08 m 미만, 정지 후 잔류 운동 | 바퀴 이름·부호·반지름 오류, 정지 실패 |
| RGB | 640×480×4, 밝기·분산과 중앙 빨간 표적 | 빈 프레임, 검은 영상, 완전 포화, 카메라 방향 오류 |
| Depth | 중앙 표적의 깊이 2.5 m ±0.05 m | 단위·축·잘못된 depth 종류 |
| IMU | 유효 판독, 증가하는 시간, 정지 시 가속도 크기 약 9.81 m/s², 작은 각속도 | 이전 값 재사용, 부착·중력 설정 오류 |
| RTX LiDAR | 새 출력 30회, 유효 점 수, 좌표 범위, 표적 평면 오차 | 빈 점군, 좌표·거리 오류, 출력 정지 |

물리 검사에서 영상 품질까지 통과했다고 기록하지 않는다. `hello_stage`와 `drive_jetbot`의 결과에는 렌더 검증을 따로 `NOT_TESTED`로 표시한다. 카메라·LiDAR의 수치 검사를 통과해도 아래 시각 검사는 추가로 수행한다.

### JSON과 배열을 읽는 방법

실행기가 출력한 경로에서 결과를 읽는다. `<실행 폴더>`는 실제 UTC 시각 폴더명으로 바꾼다.

```bash
python3 -m json.tool results/runtime/<실행_폴더>/summary.json
python3 -m json.tool results/runtime/<실행_폴더>/camera_imu/result.json
```

`numpy`가 있는 Python 환경에서 센서 배열도 살펴본다. 아래 코드는 저장소 루트에서 실행하며, 입력 경로를 실제 파일로 바꾼다.

```python
import numpy as np

with np.load("results/runtime/실제_실행_폴더/camera_imu/sensor_data.npz",
             allow_pickle=False) as data:
    print("저장 항목:", data.files)
    print("RGBA:", data["rgba"].shape, data["rgba"].dtype)
    print("Depth:", data["depth"].shape)
    print("Camera K:\n", data["intrinsics"])
    print("최초/마지막 센서 시간:", data["camera_frames"][[0, -1], 1])
    print("IMU 표본 수:", len(data["imu"]))
```

표적 위치의 복원 계산은 Isaac Sim 없이도 합성 픽셀로 검사할 수 있다. 시스템에 NumPy가 없다면 Ubuntu의 `python3-numpy` 패키지 또는 별도 가상환경에 설치한다.

```bash
python3 -m unittest discover -s tests -v
```

이 검사는 광학 축·quaternion 변환·무효 depth 처리에 대한 **수학 검사**다. 실제 카메라 프레임 생성이나 ROS 전달을 검사한 결과로 해석하지 않는다.

## 내 로봇·환경으로 바꾸기 전에

원본 에셋은 유지하고 프로젝트 장면에서 reference로 불러온다. 기본 검사에 성공한 상태를 저장한 뒤 한 요소씩 바꾼다. 로봇·센서·환경을 동시에 교체하면 어느 부분이 실패 원인인지 찾기 어렵다.

1. **단위와 크기:** 미터·Z-up인지 확인한다. 링크 길이와 바퀴 반지름을 수치로 비교한다. mm 모델을 m로 읽으면 크기가 1000배 달라진다.
2. **초기 접촉:** 충돌체 표시를 켜 바닥과 로봇의 겹침을 살펴본다. 바퀴가 지면에 묻혔거나 관절로 묶인 링크가 크게 겹치면 Play 직후 큰 힘이 생길 수 있다.
3. **강체와 관절:** rigid body, articulation root, joint의 body0/body1, 회전축과 limit을 확인한다. Stage의 시각 mesh 계층과 물리 링크 계층을 혼동하지 않는다.
4. **질량과 관성:** 명시한 값과 PhysX가 계산한 값을 구별한다. USD의 mass·inertia 기본값 0은 자동 계산을 뜻하는 경우가 있으므로 무조건 ‘관성이 0인 로봇’으로 판정하지 않는다. 명시적인 값이라면 유한한 양수와 단위를 확인한다.
5. **충돌체 소유권:** CollisionAPI가 rigid body와 같은 prim에 있을 수도 있고 자식에 있을 수도 있다. 자식만 탐색하면 정상적인 상자를 잘못 실패 처리한다. 다른 rigid body 밑의 충돌체를 부모의 충돌체로 세지 않는다.
6. **제어 모드:** 속도 제어할 바퀴에 위치 목표가 계속 적용되거나, 두 제어기가 동시에 명령하지 않는지 확인한다. 초기화가 끝난 뒤 정지 명령부터 보낸다.
7. **센서 위치:** 센서를 차체 안이나 자기 collider 속에 두지 않는다. 카메라 축, 광학 frame, LiDAR 빔 방향은 각각 확인한다.

[Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)과 [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)는 USD 속성과 관절 구성을 살펴보는 데 사용한다. 자동 검사에서 경고가 사라졌다는 이유만으로 주행·집기가 성공했다고 판단하지 않는다. 시뮬레이션을 시작해 정지·저속 제어·종료를 직접 확인한다.

### 관절을 확인하는 부분 코드

아래는 **초기화된 `robot`이 있는 standalone 실습**에 넣는 진단 조각이다. 에셋 경로와 객체 생성 전체는 [이동 로봇 실습](../03-core/06-mobile-and-manipulator.md)을 따른다.

```python
# world.reset() 이후 실행한다.
import numpy as np

positions = robot.get_joint_positions()
velocities = robot.get_joint_velocities()
if positions is None or velocities is None:
    raise RuntimeError("관절 핸들을 확인하지 못했다")
if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
    raise RuntimeError("관절 상태에 NaN 또는 Inf가 있다")
for name, position, velocity in zip(robot.dof_names, positions, velocities):
    print(f"{name}: position={position:.5f}, velocity={velocity:.5f}")
```

회전 관절과 직선 관절의 단위는 다르다. USD 관절 속성의 도 단위와 Core API의 radian 단위를 확인하지 않고 같은 값을 복사하지 않는다.

## 증상별로 처음 확인할 것

| 증상 | 확인 순서 | 다시 성공을 판단하는 기준 |
| --- | --- | --- |
| 로봇이 무너진다 | 초기 관통 → 관절 연결 → articulation root → 질량·관성 → drive | 정지 상태 유지, 작은 명령 후 정상 복귀 |
| 로봇이 떨린다 | 충돌 형상 → 과도한 gain → 질량비 → 물리 주기 | 같은 정지 구간에서 속도·자세 변동 감소 |
| RGB가 검다 | 실제 조명 → 카메라 방향 → clipping → render=True → 준비 프레임 | 표적이 보이고 여러 새 프레임이 도착 |
| 영상에 줄무늬·잔상이 있다 | 단일 GPU → 낮은 부하 → DLSS 설정 → 노출·표적 움직임 | 같은 고정 장면에서 캡처 비교 |
| depth가 대부분 무효다 | 대상이 시야 안에 있는지 → depth annotator → 측정 종류·범위 | 알려진 표적 영역의 거리와 단위 일치 |
| LiDAR 점이 없다 | Play → 렌더링 → annotator 이름 → 빔 범위·표적 → 준비 시간 | 증가하는 센서 시간과 유효 점군 |
| IMU 값이 멈췄다 | 부모 강체 → 유효 판독 → sensor time → 물리 진행 | 유효 시간 증가와 예상 정지값 |
| RViz에서 센서가 튄다 | timestamp → TF 중복 → frame_id → QoS | 같은 시간의 로봇·센서 위치 일치 |
| GPU OOM이 발생한다 | 로그 저장 → 프로세스 종료 → 해상도·센서 수 감소 | 새 실행에서 치명적 오류와 프레임 결함 없음 |

한 장의 `rgb.png`만으로 시간에 따른 깜박임을 확인할 수 없다. 기본 예제가 `frames/frame_0000.png`부터 저장하는 **서로 다른 센서 시간의 이미지 30장**을 비교한다. 더 긴 시간의 결함을 확인하려면 표본 수와 실행 시간을 함께 늘린다. 같은 배열을 여러 파일에 복사한 것은 여러 프레임 검증이 아니다.

5.1의 다중 GPU 검은 화면, 저해상도 DLSS 문제, OmniGraph 초기화 순서는 [알려진 문제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)와 [버전 비교](../appendices/release-notes-4x-to-5-1.md)를 함께 확인한다. 알려진 문제와 문구가 비슷하다는 이유로 모든 경고를 숨기지 않는다.

## 성능은 정확성이 확인된 뒤 측정한다

같은 장면에서 물리 주기·렌더 주기·센서 수·해상도·GPU를 고정한다. 에셋 로드와 셰이더 준비 시간은 별도로 기록하고, 실제 측정 구간에는 포함할지 명시한다. RTF는 ‘진행한 시뮬레이션 시간 / 실제 경과 시간’이다. FPS와 같은 값이 아니다.

다음은 `world`와 로봇이 이미 준비된 standalone 예제에서 측정 구간에 넣는 코드다. 렌더링이 포함된 전체 step 시간을 측정하므로 **물리 계산만의 시간**이라고 부르지 않는다.

```python
import time
import numpy as np

for _ in range(120):
    world.step(render=True)

samples = []
start = time.perf_counter()
steps = 600
for _ in range(steps):
    before = time.perf_counter()
    world.step(render=True)
    samples.append(time.perf_counter() - before)
wall_seconds = time.perf_counter() - start
sim_seconds = steps * world.get_physics_dt()
print("RTF:", sim_seconds / wall_seconds)
print("전체 step 중앙값(ms):", 1000 * np.median(samples))
print("전체 step p95(ms):", 1000 * np.quantile(samples, 0.95))
```

이 구간에서 Play 상태와 물리 진행을 유지해야 한다. Pause 상태에서 반복문 횟수만 세거나, `render=False`로 바꾼 결과를 카메라가 켜진 성능과 직접 비교하지 않는다. 더 자세한 CPU·GPU 원인은 [Tracy 프로파일링](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)을 사용한다.

비교할 때는 GPU·드라이버, 물리 dt, 해상도, 센서/annotator 수, DLSS 모드, MotionBVH 설정을 함께 남긴다. 주기나 해상도를 줄였다면 그 변화로 제어 응답과 센서 품질이 달라지는지도 확인한다.

## 반복 실행과 기록

처음 상태에서 새 프로세스로 세 번 실행하고 결과를 비교한다. 앱 실행 성공, 각 센서 수치, 제어 성공, 이미지 상태, 실행 시간을 별도 항목으로 기록한다. 접촉 중간 상태를 저장했다가 다시 불러온 결과와 처음부터 계산한 결과가 완전히 같다고 가정하지 않는다.

```text
장면·코드 commit:
GPU / driver / VRAM:
실행 명령:
센서 수 / 해상도 / 물리 주기:
반복 1: PASS / FAIL / NOT_RUN, 이유, 결과 경로
반복 2: PASS / FAIL / NOT_RUN, 이유, 결과 경로
반복 3: PASS / FAIL / NOT_RUN, 이유, 결과 경로
RGB 시각 확인:
로봇 정지·주행·정지 확인:
ROS 전달 확인:
```

배포 전에는 [검증 기록](../appendices/validation-report.md)과 같은 형식으로 통과·실패·미실행을 나눈다. 검사 기준을 완화해 실패를 감추기보다, 기준 장면에서 원인을 고친 뒤 실제 프로젝트 조건으로 확장한다.

## 출처

- [Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)
- [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Isaac Sim Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
