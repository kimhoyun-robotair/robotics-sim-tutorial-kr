# 15단계. 중간 프로젝트 2 — 결과를 검사하는 낙하 실험을 만들다

**목표:** 한 번 보여 주고 끝나는 데모에서 벗어나, 같은 조건으로 다시 실행하고 실패를 구분하는 실험을 완성한다. 산출물은 실행별 JSON이다.

## 실험 조건을 먼저 고정하기

| 항목 | 이 프로젝트의 값 | 이유 |
|---|---|---|
| 단위·위쪽 축 | m, Z-up | 중력·크기·높이 해석을 맞춤 |
| 물리 엔진 | CPU PhysX, TGS | 소형 강체 실험에 집중 |
| 중력 | `(0, 0, -9.81) m/s²` | 아래 방향 자유낙하 |
| 큐브 | 한 변 `0.4 m`, 질량 `1 kg` | 형상과 충돌체를 일치시킴 |
| 시작 중심 | `(0, 0, 2) m` | 바닥과 충분히 떨어뜨림 |
| 바닥 | `10 × 10 × 0.2 m`, 중심 Z `-0.1 m` | 윗면 Z가 0인 두꺼운 정적 충돌체 |
| 접촉 재질 | 정지 마찰 0.8, 운동 마찰 0.6, 반발 0 | 큰 반동 없이 정지 상태 확인 |
| 물리 주기·관측 | 120 Hz, 600샘플 | 관측 시간 5초 |

바닥에는 Collision만 적용하고 Rigid Body를 적용하지 않는다. 큐브에는 두 API를 모두 적용한다. 바닥까지 동적 강체로 만들면 둘이 함께 떨어질 수 있다. 중력·질량·충돌이 서로 다른 속성이라는 점을 확인한다. [공식 Core API Overview의 USD 물리 예제](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/core_api_overview.html)

```python
# 전체 파일에서 발췌한다.
UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(shape.GetPrim())
UsdPhysics.MassAPI.Apply(shape.GetPrim()).CreateMassAttr(1.0)
```

조명은 파일이나 온라인 asset을 내려받지 않는 Dome Light 하나를 사용한다. 카메라도 명시적으로 배치해 바닥과 낙하 영역을 바라보게 한다. 물리 장면 전체가 기본 도형으로 구성되어 외부 로봇 모델의 관절·관성 문제와 분리해서 확인할 수 있다.

## 첫 실행에서 눈으로 확인하기

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py \
  --output artifacts/drop_gui.json
```

1. 초기 셰이더 준비가 끝날 때까지 로그를 확인한다.
2. 파란 큐브가 바닥으로 내려와 멈추는지 본다.
3. 큐브가 바닥을 관통하거나 옆으로 날아가지 않는지 본다.
4. 프로그램이 관측을 마친 뒤 자동 종료하는지 확인한다.
5. 종료 직후 터미널에서 `echo $?`를 실행한다. 성공은 0, 실험 실패는 1이다.

최초 실행이 지나치게 느리면 `--timeout 300`으로 장면 구성 이후의 수집 제한을 늘릴 수 있다. 단, GPU·물리 오류가 있는 상태를 기다리는 시간만 늘려 해결하려고 하지 않는다. 제한 시간은 Python 코드가 제어권을 되돌려 받는 동안 검사되므로 드라이버가 완전히 멈춘 상황의 강제 종료 기능은 아니다.

## headless로 다시 실행하기

```bash
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py \
  --headless --output artifacts/drop_headless.json
```

창을 숨긴 실행도 Isaac Sim 런타임과 지원 GPU 환경이 필요하다. 이 예제에서 headless는 물리 결과를 자동 수집할 때 불필요한 창을 열지 않기 위한 설정이다.

## JSON으로 성공을 판단하기

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("artifacts/drop_headless.json")
data = json.loads(path.read_text())
print("성공:", data["passed"])
print("오류:", data.get("error"))
print("최종 위치:", data.get("final_position_m"))
for name, passed in data.get("checks", {}).items():
    print(name, passed)
assert data["passed"], "실험 결과가 완료 기준을 통과하지 못했다."
PY
```

다음 표는 **예상 통과 조건**이다. 실제 실행한 결과를 대신하는 측정값이 아니다.

| 검사 | 통과 조건 | 실패가 의미하는 것 |
|---|---|---|
| `sample_count` | 요청한 물리 샘플 수와 일치 | 조기 종료나 이벤트 수집 문제 |
| `physics_dt` | `1/physics_hz`와 오차 `10⁻⁶ s` 이내 | 주기 설정 불일치 |
| `fell_at_least_one_metre` | 초기 관측 대비 1 m 넘게 하강 | 중력·강체 설정 또는 상태 읽기 문제 |
| `final_height` | 마지막 0.5초간 중심 Z가 `0.20 ± 0.02 m` | 관통, 잘못된 형상·크기, 미정착 |
| `settled_height` | 마지막 0.5초 높이 범위가 `0.01 m` 이하 | 튐·떨림 |
| `settled_linear_speed` | 마지막 0.5초 속력 `0.05 m/s` 이하 | 계속 미끄러지거나 흔들림 |
| `settled_angular_speed` | 마지막 0.5초 각속력 `0.1 rad/s` 이하 | 불필요한 회전·미정착 |

추가로 매 스텝에서 유한값, 중심 Z 범위, XY 방향 이동, 과도한 속력을 확인한다. 비정상 데이터는 `NaN`이 포함된 JSON으로 저장하지 않고 명시적 오류로 기록한다. 구간 평균만 보는 것보다 마지막 0.5초 전체가 안정적인지 확인하는 편이 짧은 튐을 찾기 쉽다.

`samples`에는 물리가 끝난 시점의 상태를 보관한다. 마지막 앱 갱신에 추가 물리 스텝이 발생하더라도 요청한 첫 N개 샘플만 분석한다. Stop이 라이브 장면을 초기 상태로 되돌릴 수 있으므로 최종 값도 Stop 이후 Stage에서 다시 읽지 않고 이미 기록한 마지막 샘플에서 가져온다.

## 문제가 생기면 이 순서로 확인하기

1. JSON의 `error`와 터미널의 첫 Python·PhysX 오류를 읽는다.
2. 큐브가 안 떨어지면 질량보다 먼저 Rigid Body, 중력, Play, 샘플의 Z 변화를 확인한다.
3. 관통하면 바닥 Collision, 바닥 윗면 높이, 큐브 초기 겹침, 시간 간격을 확인한다. 이 예제는 Scene과 큐브 양쪽에 CCD를 켠다.
4. 떨리면 충돌체의 겹침, 스케일, 반발계수를 확인한다. 수치를 임의로 크게 올리는 것으로 관성·좌표 오류를 덮지 않는다.
5. 화면만 검으면 Dome Light, 카메라 방향·clipping, 렌더러 오류와 GPU 메모리를 확인한다. 물리 통과가 RGB 영상의 정상 출력을 보증하지 않는다.

**완료 기준:** GUI 1회와 headless 1회의 JSON을 각각 보관하고 `passed: true` 및 모든 검사값을 확인한다. GUI의 색·조명·물체 표시도 눈으로 확인한다. 센서 blackout이나 실제 로봇의 관절 안정성은 이후 센서·로봇 프로젝트에서 따로 검증한다.

**추가 과제:** 같은 옵션으로 3회 실행하되 결과 파일명을 다르게 한다. 각 실행의 최종 높이와 소요 시간을 표로 비교한다. 다른 형상의 로봇에 이 큐브의 임계값을 그대로 재사용하지 말고, 왜 새 기준이 필요한지 적는다.

[이전](14-timing.md) · [다음: Extension 기초](16-extension-basics.md) · [학습 목차](../../README.md)
