# 28. 성능 저하·노이즈·블랙아웃의 원인을 나누어 찾다

## 목표와 준비

22단계의 로봇 기준 결과와 27단계의 센서 기준 결과를 사용하여 실패 원인을 좁힌다. 느린 실행, 틀린 물리 모델, 카메라 문제, 센서 데이터 문제는 서로 다른 증상이다. 하나의 만능 설정으로 모두 해결하려 하지 않는다.

## 1. 관찰할 값을 먼저 정하다

| 관찰 값 | 알 수 있는 내용 | 그것만으로 알 수 없는 내용 |
| --- | --- | --- |
| Viewport FPS | 화면이 갱신되는 빈도 | 물리 스텝 수와 센서 발행 주기 |
| 시뮬레이션 시간 | 물리 시간이 얼마나 진행되었는지 | 실제로 사용한 운영체제 시간 |
| GPU 메모리 | 렌더링·센서 자료의 메모리 부담 | 로봇 관성의 정확성 |
| 센서 timestamp | 새 측정이 진행되는지 | 측정 내용이 올바른지 |
| RGB/깊이/점군 통계 | 빈 영상·블랙아웃·비정상 수치 | 모든 물체의 의미와 장면 완성도 |

Real Time Factor(RTF)는 시뮬레이션 경과 시간을 실제 경과 시간으로 나눈 값이다. RTF가 낮아도 물리 시간이 일정하게 진행될 수 있다. 반대로 빠른 화면에서도 센서가 같은 배열만 반환할 수 있다.

```python
# 실행 시간 계측의 개념이다.
import time
wall_start = time.perf_counter()
sim_start = SimulationManager.get_simulation_time()
# ... app.update()와 검사 루프 ...
wall_elapsed = time.perf_counter() - wall_start
sim_elapsed = SimulationManager.get_simulation_time() - sim_start
rtf = sim_elapsed / wall_elapsed if wall_elapsed > 0 else 0.0
print("RTF:", rtf)
```

## 2. 장비 상태를 기록하다

문제가 생긴 장비에서 터미널을 하나 더 열고 다음 결과를 저장한다.

```bash
cd "$TUTORIAL_ROOT"
mkdir -p artifacts/diagnostics
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu \
  --format=csv > artifacts/diagnostics/gpu.csv
```

한 번의 순간값으로 부하 전체를 설명할 수 없으므로 실행 전후를 비교한다. VRAM이 부족하다면 카메라 해상도, 센서 수, Render Product 수, 장면 복잡도를 차례로 줄이며 다시 측정한다. 여러 값을 동시에 바꾸면 어느 변경이 효과가 있었는지 알기 어렵다.

## 3. 화면이 검어졌을 때 확인하다

1. 24단계의 카메라 검사 프로그램을 그대로 다시 실행한다.
2. 기준 장면도 실패하면 센서 경로, 렌더러 초기화, GPU 메모리, 드라이버와 공식 Known Issues를 확인한다.
3. 기준 장면은 통과하는데 로봇 장면만 실패하면 카메라 방향과 로봇 내부 가림을 확인한다.
4. RGB만 실패하고 깊이는 정상인지, 두 배열이 모두 비었는지 나누어 본다.
5. headless 실행에서도 `app.update()`와 렌더링이 실제로 진행되는지 확인한다.

```bash
"$ISAAC_SIM_PATH/python.sh" examples/04_camera_check.py \
  --headless --output-dir artifacts/diagnostics/camera-baseline
```

실패한 배열을 보정하여 0이나 임의 색상으로 채우면 원래 원인을 숨기게 된다. 먼저 원시 파일을 보관하고, 보정이 필요한 응용 프로그램에서는 보정 여부와 유효 마스크를 별도로 내보낸다.

## 4. 노이즈와 틀린 모델을 구분하다

| 증상 | 가능한 원인 | 비교 실험 |
| --- | --- | --- |
| 정지 RGB가 조금씩 달라지다 | 렌더러 샘플링·후처리·노출 | 고정 조명과 정지 장면에서 시간 변화 통계를 읽다 |
| 깊이가 전체적으로 잘못되다 | 단위·좌표·Annotator 종류 혼동 | 3 m 기준 평면을 측정하다 |
| 점군이 부채꼴로 끊기다 | LiDAR tick/scan 주기 불일치 | 둘을 10 Hz로 맞춘 기본 검사를 실행하다 |
| IMU가 접촉 직후 튀다 | 실제 충격·수치 진동·필터 지연 | 낙하 구간과 정지 구간을 따로 기록하다 |
| 로봇이 계속 떨리다 | 초기 겹침·잘못된 관성·과도한 Drive | 센서를 떼고 단일 관절 물리 검사부터 진행하다 |
| 이미지가 모두 같아지다 | 정지 장면 또는 갱신 정지 | timestamp와 움직이는 표적의 결과를 함께 확인하다 |

노이즈를 줄이는 것과 센서의 현실성을 높이는 것은 같은 목표가 아니다. 학습용 데이터에서 의도적으로 노이즈를 추가한다면 노이즈 없는 기준 결과, 사용한 분포·파라미터·seed, 추가 후 결과를 구분한다. 실제 장치의 오차를 흉내 내는 경우에는 장치 측정값에 근거해 분포를 정한다.

```python
# 일반 Python에서 수행하는 별도 후처리 실험이다. 원본 depth를 덮어쓰지 않는다.
import numpy as np
rng = np.random.default_rng(42)
depth = np.load("artifacts/project05/camera/depth_000.npy")
valid = np.isfinite(depth) & (depth > 0)
noisy_depth = depth.copy()
noisy_depth[valid] += rng.normal(0.0, 0.005, size=int(valid.sum()))
np.save("artifacts/diagnostics/depth_noise_example.npy", noisy_depth)
```

이 예제의 5 mm 표준편차는 설명용 값이다. Isaac Sim의 물리적 깊이 센서 모델이나 특정 RGBD 제품의 실제 오차를 뜻하지 않는다.

## 5. 로봇이 무너졌을 때 확인하다

```bash
"$ISAAC_SIM_PATH/python.sh" examples/03_robot_stability.py \
  --headless --output-dir artifacts/diagnostics/robot-baseline
```

기준 로봇의 보고서가 실패했다면 센서나 ROS 제어를 추가하지 않고 관절·질량·고정을 확인한다. 사용자 로봇만 실패하면 아래 순서로 비교한다.

1. 링크의 단위와 collision origin을 확인한다.
2. Play 전 충돌 형상끼리 겹쳐 있지 않은지 확인한다.
3. 고정식·이동식 로봇에 맞는 base 조건과 Articulation Root를 확인한다.
4. 관절 위치 제한, effort·velocity 제한, Drive를 확인한다.
5. 목표 명령을 작게 하고 천천히 보낸다.
6. 그 뒤 물리 간격과 solver 반복 수를 비교한다.

## 기대 결과와 완료 기준

문제가 발생한 실행과 기준 실행의 결과 폴더 두 개를 남기고, 변경한 설정 하나와 그 결과를 설명할 수 있어야 한다. “화면이 괜찮아 보인다” 대신 실패 항목과 관련된 측정값으로 판단한다.

다음 ROS 단계로 넘어가기 전에는 로봇 기준 검사와 센서 기준 검사를 장비에서 실행한다. CPU 문법·수치 테스트 통과만으로 GPU 렌더링까지 검증했다고 기록하지 않는다. 이 저장소 작성 환경에서는 GPU 실험을 실행하지 못했다.

## 과제와 실행 파일

[03_robot_stability.py](../../examples/03_robot_stability.py), [04_camera_check.py](../../examples/04_camera_check.py), [05_lidar_check.py](../../examples/05_lidar_check.py)의 report에서 문제 하나를 골라 원인을 설명한다. 그다음 같은 하드웨어에서 카메라 해상도 또는 측정 표본 수 중 한 가지만 바꾸고 실행 시간과 품질 검사를 비교한다. 해상도를 바꾸면 기대 배열 크기 검사도 함께 조정해야 한다.

## 공식 참고 자료

- [6.0.1 성능 최적화 가이드](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/reference_material/sim_performance_optimization_handbook.html)
- [6.0.1 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)
- [6.0.1 RTX LiDAR의 단일 GPU 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_rtx_lidar.html)
- [6.0.1 로봇 시뮬레이션 팁](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_simulation/robot_simulation_tips.html)

[이전](27-project-sensor-lab.md) · [전체 목차](../../README.md)
