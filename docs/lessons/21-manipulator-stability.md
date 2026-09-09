# 21. 고정식 로봇의 제어 안정성을 검사하다

## 목표와 준비

19~20단계의 단일 관절 로봇에서 초기 배치, 속도, 기울기, 침투를 따로 검사한다. 복잡한 다관절 로봇에 같은 방법을 적용하기 전에 실패를 알아볼 수 있는 작은 장면을 만든다. 물리 엔진은 이 실습의 기본 PhysX 구성을 사용한다. Newton으로 바꾸는 비교 실험은 별도 결과로 남긴다.

## 1. 팔과 바닥의 간격을 먼저 계산하다

제공 URDF의 팔은 관절 높이가 0.35 m이고 두께가 0.08 m이다. Z축 주위로만 회전하므로 팔의 바닥면은 정상 상태에서 약 0.31 m이다. 받침대 바닥면은 0 m이다.

```python
joint_height = 0.35
arm_thickness = 0.08
arm_bottom = joint_height - arm_thickness/2
assert arm_bottom > 0
print(arm_bottom)  # 0.31 m
```

링크 원점의 Z값만으로 침투를 판단하면 안 된다. 원점은 바닥 위에 있어도 긴 팔의 끝은 바닥을 뚫을 수 있다. 검사 프로그램은 각 링크의 충돌 상자 꼭짓점 8개를 실제 링크 자세로 변환하고, 그중 가장 낮은 Z값을 구한다. 따라서 변형된 복잡한 로봇에 적용할 때는 그 로봇의 collision geometry에 맞는 검사를 새로 구성해야 한다.

## 2. 목표를 천천히 바꾸다

0에서 목표값으로 갑자기 뛰는 명령보다 짧은 구간에 걸쳐 변화하는 명령이 원인 분석에 유리하다. 아래는 1초 대기, 2초 이동, 목표 유지로 구성한 실습 명령이다.

```python
def target_angle(time_s):
    progress = min(max((time_s - 1.0) / 2.0, 0.0), 1.0)
    return 0.4 * progress

for t in [0, 1, 2, 3, 4]:
    print(t, target_angle(t))
# 0:0.0, 1:0.0, 2:0.2, 3:0.4, 4:0.4
```

시간은 `SimulationManager.get_simulation_time()`으로 읽는다. 화면 FPS나 운영체제 시간으로 위 식을 계산하면 느린 PC에서 로봇이 아직 충분히 움직이지 않았는데 명령만 앞서갈 수 있다.

## 3. 언제 실패로 판정하는지 정하다

이번 검사용 로봇은 다음 조건을 적용한다. 임계값은 **이 장면의 교육용 합격 기준**이며 제조사 허용 오차가 아니다.

| 항목 | 실패 기준 | 의미 |
| --- | --- | --- |
| 관절·링크 수치 | NaN 또는 inf가 하나라도 나오다 | 수치가 망가진 결과를 저장 후 합격시키지 않다 |
| 관절 범위 | ±π/2에서 0.02 rad 이상 벗어나다 | 제한을 넘는 움직임을 잡다 |
| 관절 속도 | 1.2 rad/s를 넘다 | 급격한 발산을 잡다 |
| 받침대 위치 | 원점에서 5 mm 이상 이동하다 | 고정 조건의 실패를 잡다 |
| 받침대 기울기 | 1°를 넘다 | 전도 또는 회전 오류를 잡다 |
| 링크 바닥면 | -5 mm보다 낮아지다 | 지면 침투를 잡다 |
| 최종 관절 오차 | 0.03 rad보다 크다 | 목표에 도달하지 못한 결과를 잡다 |

아래 코드는 결과를 읽을 때 반드시 사용할 패턴이다. 빈 배열을 `all()`로 검사하면 `True`가 나올 수 있으므로 먼저 크기를 확인한다.

```python
import numpy as np

def check_joint_array(values):
    values = np.asarray(values)
    if values.size == 0:
        raise RuntimeError("관절 데이터가 없다")
    if not np.isfinite(values).all():
        raise RuntimeError("유효하지 않은 관절값이 있다")
    return values
```

## 4. 물리 계산과 화면 갱신을 구분하다

물리 간격은 1/120 s로 설정한다. 렌더링을 포함한 앱 갱신 한 번이 언제나 물리 스텝 한 번인 것은 아니다. 검사 파일은 앱 갱신 횟수와 별개로 실제 시뮬레이션 시간이 5초 이상 지났는지 확인한다.

이 로봇 예제는 초기 20회 앱 갱신 뒤부터 앱 갱신마다 상태를 읽는다. 따라서 초기 구간과 두 표본 사이의 모든 물리 스텝까지 검사했다고 해석하지 않는다. 아주 짧은 침투나 속도 급증을 분석하려면 14~15단계의 `PHYSICS_POST_STEP` 콜백 방식으로 표본 수집을 확장한다. GUI에서 Play 직후의 자세도 함께 확인한다.

```python
from isaacsim.core.simulation_manager import SimulationManager

SimulationManager.set_physics_dt(1.0 / 120.0)
start = SimulationManager.get_simulation_time()
# 이후 루프에서 app.update()로 앱과 물리 갱신을 진행한다.
elapsed = SimulationManager.get_simulation_time() - start
```

다른 장면으로 확장할 때는 물리 간격을 바꾸기 전에 초기 겹침, 관성, 관절 좌표를 먼저 수정한다. 잘못된 모델을 작은 시간 간격만으로 덮어두면 계산량만 늘어날 수 있다.

## 기대 결과와 문제 진단

정상 상태에서는 받침대가 월드에 고정되어 있고 팔만 수평으로 움직인다. 팔이 아래로 처지거나 받침대 전체가 돌아가면 목표값을 더 크게 보내지 않고 Stop 후 연결 구조를 살펴본다.

1. 수치 검사 전에 Play 직후의 로봇을 눈으로 관찰한다.
2. 초기 상태가 정상이라면 22단계 명령을 실행한다.
3. CSV의 `base_bottom_m`과 `arm_bottom_m` 열을 확인한다.
4. 목표 추종 오차와 받침대 움직임을 분리해서 판단한다.

실행 파일은 [03_robot_stability.py](../../examples/03_robot_stability.py)이고, 전체 실행과 결과 읽기는 다음 중간 프로젝트에서 진행한다. 이 저장소 작성 환경에서는 Isaac Sim과 GPU가 없어 위 물리 검사를 실행하지 못했다. 코드의 검사항목과 실제 PC에서 생성한 결과를 구분해야 한다.

## 확인 과제

관절 축이 Z에서 Y로 바뀌면 팔의 바닥 높이와 중력에 대한 Drive 요구가 어떻게 달라지는지 스케치한다. 기준 URDF를 바로 수정해 실행하지 말고, 이 단계의 임계값을 그대로 쓸 수 있는지 먼저 계산한다.

## 공식 참고 자료

- [6.0.1 로봇 시뮬레이션 팁](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_simulation/robot_simulation_tips.html)
- [6.0.1 Articulation의 gain·limit·실행 중 상태 API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.core.experimental.prims/docs/index.html)
- [6.0.1 Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html)

[이전](20-articulation-drives.md) · [다음](22-project-joint-rig.md)
