# 39단계 — GUI 실험을 자동 실행과 검사 기록으로 옮기다

## 목표와 준비

수동으로 한 번 성공한 예제를 여러 번 실행하면서 같은 기준으로 판단한다. 15·22·27·38단계의 프로젝트를 완료한 뒤 진행한다. 자동화는 화면을 보지 않아도 실패를 발견하기 위한 것이며, 화면이 올바른지 확인하는 일까지 없애지는 않는다.

이번 단계의 도구는 [runtime_suite.py](../../scripts/runtime_suite.py)이다. 설치된 Isaac Sim의 `python.sh`를 별도 프로세스로 시작하고 각 예제의 종료 코드와 JSON 검사 결과를 함께 읽는다. 센서가 응답하지 않아 프로그램이 끝나지 않는 경우를 위해 프로세스마다 제한 시간을 둔다.

## 실행 환경을 기록하다

아래 명령은 Isaac Sim을 실행할 Ubuntu PC에서 사용한다. `preflight.py`는 환경 존재 여부를 확인하는 도구이다. GPU 모델·드라이버를 읽었다고 RT Core 지원과 렌더링이 자동으로 검증되는 것은 아니므로 2단계의 Compatibility Checker 결과도 보관한다.

```bash
source /opt/ros/jazzy/setup.bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$TUTORIAL_ROOT"
.venv/bin/python scripts/preflight.py --output artifacts/preflight.json
cat "$ISAAC_SIM_PATH/VERSION"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
```

`VERSION`에 `6.0.1-rc...+release...`처럼 빌드 정보가 붙어 있으면 문자열 전체를 기록한다. 다운로드 이름만 6.0.1이라고 적고 내부 빌드 버전을 생략하면 재현할 때 중요한 차이를 놓칠 수 있다.

## 로컬 검사를 먼저 묶어 실행하다

다른 Isaac Sim 프로세스를 닫고 아래 명령을 실행한다. `.venv`에는 `requirements-dev.txt`가 설치되어 있어야 한다.

```bash
.venv/bin/python scripts/runtime_suite.py \
  --isaac-path "$ISAAC_SIM_PATH" \
  --output-dir artifacts/suite-local-01
```

이 명령은 낙하, 관절 로봇, RGBD, LiDAR, 데이터셋 검사를 차례로 실행한다. 동시에 여러 Isaac Sim을 시작하지 않으므로 다른 실습이 GPU 메모리를 차지하는 상황을 줄일 수 있다. 첫 실행은 셰이더 초기화 때문에 오래 걸릴 수 있다. 기본 제한은 예제당 600초이며 필요한 경우 `--timeout 1200`으로 늘린다. 실패가 반복될 때 제한 시간을 무작정 늘리지 말고 해당 로그를 읽는다.

## 세 가지 결과를 구분하다

| suite 상태 | 종료 코드 | 뜻 |
|---|---:|---|
| PASS | 0 | 요청한 모든 자동 검사와 ROS 동작·정지 검사 통과 |
| FAIL | 1 | 하나 이상 실패, 누락 또는 제한 시간 초과 |
| PARTIAL | 2 | 로컬 검사는 통과했지만 ROS 검사는 실행하지 않음 |

위의 로컬 명령은 ROS를 요청하지 않았기 때문에 모두 성공해도 **PARTIAL**이다. 이것은 실행 오류가 아니라 검사 범위를 나타내는 결과이다. 전 과정을 통과시키려면 40단계에서 `--with-ros`로 실행한다. 결과가 없는 항목을 성공으로 추정하지 않는다.

```bash
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('artifacts/suite-local-01/suite.json').read_text())
print('전체:', r['status'])
for entry in r['entries']:
    print(entry['name'], entry['status'])
PY
```

## 시간이 서로 다른 이유를 이해하다

물리 시간은 시뮬레이션 안에서 흐른 시간이다. 벽시계 시간은 사용자가 실제로 기다린 시간이다. 10초 분량의 움직임을 렌더링하는 데 25초가 걸렸다면 두 시간의 비는 0.4이다. 그래픽 품질을 낮추면 벽시계 시간은 줄어들 수 있지만 물리 스텝이나 센서 주기를 바꾸면 실험 자체가 달라질 수 있다.

```python
simulated_seconds = 10.0
wall_seconds = 25.0
real_time_factor = simulated_seconds / wall_seconds
print(real_time_factor)  # 0.4
```

이 단순 계산에는 앱 시작 시간과 셰이더 컴파일 시간을 넣지 않는다. `suite.json`의 `wall_seconds`는 프로세스 시작부터 종료까지 포함하므로 그 값만으로 물리 RTF라고 보고하면 안 된다. 속도 비교를 할 때에는 앱 초기화 시간을 별도로 측정한다.

## 실패를 좁혀 가다

`camera`만 실패했다면 해당 폴더의 `report.json`, 원시 배열, 미리보기와 `camera.log`를 확인한다. LiDAR와 카메라가 함께 실패하면 GPU 메모리·렌더 설정을 먼저 살펴본다. 낙하와 로봇은 실패하지만 이미지는 정상이면 물리 초기화·충돌·관절 경로 쪽을 확인한다. `.log` 파일에서 오류가 없다고 성공으로 판단하지 않는다. 예제의 수치 검사 결과가 우선이다.

```bash
rg -n 'Error|ERROR|Traceback|out of memory|CUDA' artifacts/suite-local-01/*.log
```

과제는 RGB 검사 함수에 알려진 검은 배열을 넣어 반드시 FAIL이 되는지 단위 테스트로 확인하고, 검사 문턱값을 낮추었을 때 왜 잘못 통과할 수 있는지 설명하는 것이다. 실제 GPU에 고장 난 장면을 반복 실행할 필요는 없다.

## 공식 참고

[Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/reference_material/sim_performance_optimization_handbook.html)에서 렌더링과 물리 병목을 구분한다. [Physics Data Flow and Engine Integration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/new_physics_engine.html)은 USD/Fabric/물리 backend 사이의 상태 흐름을 설명한다.
