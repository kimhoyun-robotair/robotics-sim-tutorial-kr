# 22. 중간 프로젝트 4 — 단일 관절 검사용 로봇을 완성하다

## 프로젝트 목표

URDF 변환부터 고정된 로봇의 제어, 안정성 결과 저장까지 한 번에 수행한다. 화려한 로봇 동작보다 **같은 파일에서 같은 검사를 다시 실행할 수 있는 상태**를 목표로 한다. 19~21단계를 마친 뒤 진행한다.

완성물은 주황색 팔이 0.4 rad까지 천천히 회전하는 장면과 검사 보고서이다. 프로그램이 종료되었다는 사실만으로 성공이라 판단하지 않고 `report.json`의 `passed`를 확인한다.

## 1. 프로그램을 GUI로 실행하다

기존 GUI의 Script Editor에 붙여 넣지 않고 터미널에서 아래 명령을 실행한다. `SimulationApp`이 새 Isaac Sim 프로세스를 시작하므로 열어 둔 GUI와 별개로 실행된다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/03_robot_stability.py \
  --output-dir artifacts/project04/gui
```

새 창이 열리면 로봇을 관찰한다. 처음에는 확장 로딩과 URDF 변환으로 잠시 기다릴 수 있다. 프로그램이 정해진 횟수만큼 실행한 후 자동으로 종료한다. 진행 중 Play/Stop을 직접 누르지 않는다.

실행 파일은 [03_robot_stability.py](../../examples/03_robot_stability.py), 입력 로봇은 [one_joint_arm.urdf](../../assets/one_joint_arm.urdf)이다.

## 2. 코드의 흐름을 이해하다

| 순서 | 수행 내용 | 그 단계가 필요한 이유 |
| --- | --- | --- |
| 1 | `SimulationApp`을 만들다 | Isaac Sim용 Python 모듈을 불러올 준비를 하다 |
| 2 | 필요한 Extension을 켜다 | URDF 변환과 새 Core API를 사용하다 |
| 3 | URDF를 USD로 변환하다 | ROS 로봇 설명을 시뮬레이션 장면으로 옮기다 |
| 4 | 실제 링크 경로를 찾다 | 변환기 출력 구조를 추측하지 않다 |
| 5 | 월드 고정과 바닥을 구성하다 | 움직임의 기준과 접촉 조건을 정하다 |
| 6 | Play 후 Drive를 설정하다 | 물리 상태를 읽고 관절을 제어하다 |
| 7 | 목표를 갱신하며 기록하다 | 제어와 측정을 같은 루프에서 수행하다 |
| 8 | JSON과 배열을 저장하다 | 성공·실패의 근거를 남기다 |

실제 경로를 찾는 핵심은 아래와 같다. 동일한 이름의 몸체가 여러 개 발견되면 실패하도록 작성한다.

```python
candidates = [
    prim for prim in stage.Traverse()
    if prim.GetName() == "base_link"
    and prim.HasAPI(UsdPhysics.RigidBodyAPI)
]
if len(candidates) != 1:
    raise RuntimeError("base_link가 없거나 여러 개이다")
base_path = candidates[0].GetPath()
```

## 3. 결과를 읽다

```bash
python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/project04/gui/report.json')
result = json.loads(path.read_text())
print(json.dumps(result, ensure_ascii=False, indent=2))
if not result['passed']:
    raise SystemExit('로봇 검사가 실패했다. error와 traceback을 확인한다.')
PY
```

| 결과 파일 | 내용 |
| --- | --- |
| `report.json` | 합격 여부, 최종 오차, 받침대 이동·기울기, 실패 원인 |
| `joint_history.csv` | 시간과 목표·현재 각도, 속도, 바닥 높이의 시계열 |
| `joint_history.npy` | CSV와 같은 수치 배열 |
| `robot_scene.usda` | 장면 설정을 확인할 USD 스냅샷 |
| `imported/` | URDF 변환기가 만든 USD와 보조 자료 |

`robot_scene.usda`는 실행 설정을 살펴보는 파일이다. 모든 프레임의 움직임을 재생하는 녹화 파일은 아니다. 장면의 로봇 reference는 같은 결과 폴더 안의 변환 자료를 가리키므로 폴더 전체를 유지한다.

```python
# 일반 Python + NumPy에서 실행한다.
import numpy as np
values = np.load("artifacts/project04/gui/joint_history.npy")
time_s, target, measured = values[:, 0], values[:, 1], values[:, 2]
print("측정 시간:", time_s[-1])
print("최종 오차:", abs(target[-1] - measured[-1]))
print("가장 낮은 충돌면:", values[:, 6:].min())
```

## 4. 창 없이 같은 검사를 실행하다

```bash
"$ISAAC_SIM_PATH/python.sh" examples/03_robot_stability.py \
  --headless --output-dir artifacts/project04/headless
```

Headless는 창을 만들지 않는 실행 방식이다. GPU 없이 실행한다는 의미는 아니다. 결과 폴더를 나누어 GUI 실행의 근거를 덮어쓰지 않는다.

## 합격 조건과 문제 진단

보고서가 `passed: true`이고, 충분한 시뮬레이션 시간과 관절 표본이 존재해야 한다. 코드 자체를 작성한 환경에서는 GPU 실행을 하지 못했으므로 저장소에는 실제 성공 측정값을 넣지 않았다.

- 변환부터 실패하면 `error`에서 경로와 Importer 오류를 확인한다.
- DOF 목록이 다르면 URDF와 실제로 읽은 파일이 같은지 확인한다.
- 받침대 이동·기울기 실패면 world fixed joint를 먼저 살펴본다.
- 최종 오차만 실패면 관절 제한, Drive, 실제 경과 시간을 확인한다.
- 조정할 때는 한 가지 값을 바꾸고 새 결과 폴더를 사용한다.

## 확장 과제

프로그램 사본에서 목표를 0.4 rad에서 0.6 rad로 바꾸고 최종 검사 목표도 함께 바꾼다. 기준 실행과 최종 오차, 최대 속도를 비교한다. 다음으로 목표 변화 시간을 2초에서 4초로 늘려 같은 항목을 비교한다. 고정된 받침대의 움직임이 달라지면 원인 분석이 필요하다.

## 공식 참고 자료

- [6.0.1 URDF Importer API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.asset.importer.urdf/docs/index.html)
- [6.0.1 Robot Simulation Snippets](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/robots_simulation.html)
- [6.0.1 Experimental Core API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/docs/overview/experimental.html)

[이전](21-manipulator-stability.md) · [다음](23-camera-coordinates.md)
