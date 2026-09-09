# 디버깅, 성능 측정과 배포

실행이 느리거나 화면이 검게 보이면 설정을 한꺼번에 바꾸지 않는다. 물리, 렌더링, 센서 읽기, ROS 통신, Python 콜백 중 어디에서 문제가 시작되는지 작은 장면부터 확인한다.

## 1. 실패한 실행을 재현할 정보 남기기

저장소 루트에서 기록할 폴더를 만들고 환경과 실행 로그를 남긴다.

```bash
mkdir -p outputs/diagnostics
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used \
  --format=csv > outputs/diagnostics/gpu.csv
uname -a > outputs/diagnostics/kernel.txt
set -o pipefail
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py \
  2>&1 | tee outputs/diagnostics/hello_stage.log
```

`pipefail`은 Python 실행이 실패했는데 `tee`가 성공했다는 이유로 전체 명령이 성공한 것으로 처리되는 상황을 방지한다. 첫 asset 다운로드와 셰이더 준비 시간은 준비된 상태의 반복 실행 성능과 나누어 기록한다.

## 2. 무엇부터 분리해서 확인할 것인가

| 단계 | 구성 | 확인할 결과 |
| --- | --- | --- |
| A | 빈 앱 | 창, 드라이버, Extension 로딩 오류 |
| B | 바닥 + 큐브, 물리만 실행 | 지면 통과, NaN, 정착 높이 |
| C | B + 조명 + 카메라 하나 | 검은 영상, 시야, 깊이 |
| D | 로봇 하나, 센서 없음 | 초기 관통, 관절 축, 구동값 |
| E | D + 센서 하나씩 | 각 센서의 데이터와 VRAM 증가 |
| F | E + ROS 2 Bridge | 토픽 주기, QoS, timestamp |

B가 실패한다면 ROS 2나 카메라 해상도부터 바꿀 이유가 없다. C가 실패한다면 로봇 제어기를 수정하기 전에 조명과 카메라 방향, 렌더링 호출을 확인한다. 여러 오류가 이어질 때는 로그의 첫 실패를 찾고 뒤따르는 오류와 구분한다.

## 3. RTF와 처리 시간을 직접 재기

RTF는 **진행한 시뮬레이션 시간 / 실제로 걸린 시간**이다. 화면 FPS와 다르다. 다음 코드는 standalone의 `world.reset()` 이후에 넣는 측정 블록이다. `world`가 준비되어 있어야 하며 Script Editor에 따로 실행하는 코드는 아니다.

```python
import time
import numpy as np

for _ in range(60):
    world.step(render=False)  # 준비 구간은 측정에서 제외한다.

step_seconds = []
start = time.perf_counter()
for _ in range(600):
    one_step_start = time.perf_counter()
    world.step(render=False)
    step_seconds.append(time.perf_counter() - one_step_start)
elapsed = time.perf_counter() - start
simulated = 600 * world.get_physics_dt()
print("wall_seconds:", elapsed)
print("sim_seconds:", simulated)
print("RTF:", simulated / elapsed)
print("step_ms mean/p95:",
      1000 * np.mean(step_seconds), 1000 * np.percentile(step_seconds, 95))
```

이 측정은 해당 Python 호출의 경과 시간이다. GPU 내부 작업의 세부 시간이나 CPU/GPU 중첩을 직접 분리하지는 못한다. 그래도 같은 장면에서 `render=False/True`, 카메라 해상도, 센서 수를 하나씩 바꾸면 병목의 범위를 좁힐 수 있다. 카메라 데이터를 비교할 때는 반드시 `render=True`로 별도 측정한다.

평균만 보지 말고 p95, 가장 느린 구간과 메모리 증가도 확인한다. 로그를 매 physics step에 출력하는 것 자체가 측정을 방해하므로 필요한 결과만 모아 출력한다.

## 4. VS Code와 Tracy 사용하기

VS Code 디버깅은 설치본에 포함된 설정과 [공식 Debugging 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html)를 따른다. GUI에 연결할 때는 `omni.kit.debug.vscode_debugger`를 활성화한다. breakpoint에서 Python이 멈추면 시뮬레이션과 센서 출력도 정상 주기로 진행되지 않을 수 있으므로 이 상태의 ROS 주기 측정을 정상 성능으로 기록하지 않는다.

Tracy를 사용할 standalone 프로그램에서는 앱 설정에 profiler backend를 지정하고, 실행 명령에 `--enable omni.kit.profiler.tracy`를 함께 전달한다.

```python
from isaacsim import SimulationApp

app = SimulationApp({"headless": False, "profiler_backend": ["tracy"]})
```

관심 있는 계산에 구간 표시를 추가할 수 있다.

```python
import carb
import numpy as np

@carb.profiler.profile
def compute_velocity_command(position, target):
    error = np.asarray(target) - np.asarray(position)
    return np.clip(0.5 * error, -0.2, 0.2)
```

제어기 함수가 빠른데 프레임이 느리면 렌더링이나 센서 readback을 본다. 반대로 큰 배열의 반복 변환이나 파일 저장이 Python 콜백에 몰려 있으면 해당 작업의 주기와 데이터 이동을 줄인다. Tracy 연결과 캡처는 [Profiling Performance](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)를 따른다.

## 5. 결과를 유지하면서 최적화하기

| 변경 | 기대 효과 | 함께 다시 확인할 것 |
| --- | --- | --- |
| 카메라 해상도/개수 감소 | 렌더링과 메모리 사용 감소 | 물체가 충분한 픽셀을 차지하는지 |
| 센서 발행 주기 감소 | ROS 전송량 감소 | 제어기가 필요한 주기인지 |
| 충돌 형상 단순화 | 접촉 계산량 감소 | 얇은 구조나 바퀴 접촉이 바뀌지 않는지 |
| 공유 asset의 instanceable 사용 | 중복 형상 메모리 감소 | 환경별 편집이 필요한 속성과 충돌하지 않는지 |
| Python 처리를 배열 단위로 변경 | 반복 호출 비용 감소 | 객체 순서와 단위가 유지되는지 |
| headless에서 Viewport 갱신 해제 | 불필요한 화면 갱신 감소 | 독립 Render Product는 계속 렌더링하는지 |

```python
app = SimulationApp({"headless": True, "disable_viewport_updates": True})
```

이 설정은 Viewport가 필요 없는 배치 실행에 사용한다. 스트리밍할 화면이 필요하거나 Viewport에 의존하는 센서 예제에는 그대로 적용하지 않는다. 물리 step을 크게 하거나 solver 반복 수를 줄인 뒤 로봇이 흔들린다면 성능 개선으로 채택하지 않는다. 변경 전후의 정착, 관절 안정성, 센서 데이터 검사를 함께 통과해야 한다. [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)

## 6. 컨테이너와 원격 실행으로 옮기기

컨테이너는 GPU 드라이버를 대신 설치하지 않는다. 호스트 드라이버, NVIDIA Container Toolkit, GPU 전달과 asset 접근이 먼저 준비되어야 한다. 이미지 태그는 `nvcr.io/nvidia/isaac-sim:5.1.0`으로 고정하고, NGC 인증이 필요한 환경에서는 공식 로그인 절차를 완료한다.

처음에는 컨테이너에서 GPU가 보이는지만 확인한다. 이미지 이용 약관을 확인한 뒤 실행한다.

```bash
docker run --rm --gpus all \
  --entrypoint nvidia-smi \
  -e ACCEPT_EULA=Y \
  nvcr.io/nvidia/isaac-sim:5.1.0
```

이 명령의 성공은 Isaac Sim의 렌더링 성공을 뜻하지 않는다. 이후 공식 [Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)의 cache와 output volume, 사용자 설정, 실행 명령을 적용하고 앞의 B~F 검사를 다시 수행한다. 결과 파일을 컨테이너 내부에만 두면 컨테이너 삭제 시 잃을 수 있으므로 호스트 출력 폴더를 volume으로 연결한다.

WebRTC 화면 전달은 GPU의 인코더 지원과 네트워크 설정도 필요하다. [Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)의 지원 GPU와 클라이언트 제한을 확인한다. 원격 화면이 끊기는 문제와 시뮬레이터 자체가 멈춘 문제는 서버의 로그와 물리 진행 기록으로 구분한다.

## 7. 검증 결과 표현하기

“코드 검사가 통과했다”, “PhysX 낙하 검사가 통과했다”, “실제 RGB 프레임을 확인했다”는 서로 다른 결과이다. 보고서에는 실행 환경, 명령, 종료 코드, 센서 결과 파일, 관찰한 현상을 적는다. GPU 없는 환경의 문법 검사로 블랙아웃이나 드라이버 문제까지 검증했다고 쓰지 않는다.

## 출처

- [Debugging With Visual Studio Code](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html)
- [Profiling Performance Using Tracy](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)
- [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- [Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)
- [Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)
