# 20. Articulation과 관절 Drive를 구분하다

## 목표와 준비

19단계에서 가져온 로봇을 기준으로, 관절의 연결과 관절을 움직이는 힘이 다른 설정이라는 점을 이해한다. 실행 코드는 22단계의 단일 관절 검사 프로그램에 포함되어 있다. 이 단계의 코드 조각은 그 프로그램의 관련 부분을 읽기 위한 예제이다.

| 구성 | 담당하는 일 | 이 실습의 예 |
| --- | --- | --- |
| Rigid Body | 링크 하나의 운동을 계산하다 | 받침대와 팔 |
| Joint | 두 링크 사이에서 허용하는 움직임을 정하다 | Z축 회전 하나 |
| Articulation | 연결된 링크와 관절을 로봇 단위로 계산하다 | 로봇 전체 |
| Drive | 목표 위치·속도를 따라가도록 힘을 만들다 | 0.4 rad 목표 |
| Fixed Joint | 두 좌표계를 붙들어 두다 | 받침대를 월드에 고정하다 |

## 1. 관절 좌표를 읽다

URDF에서 `origin`은 자식 링크가 처음 놓이는 위치이자 관절 기준 좌표를 정한다. `axis`는 이 관절 좌표계에서의 축이다.

```xml
<joint name="shoulder" type="revolute">
  <parent link="base_link"/>
  <child link="arm_link"/>
  <origin xyz="0 0 0.35" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-1.57079632679" upper="1.57079632679"
         effort="20" velocity="1"/>
</joint>
```

받침대 원점에서 0.35 m 위에 축을 놓고 팔을 Z축으로 회전시킨다. 각도 범위는 -90°~90°이다. Python 제어값은 rad이고 USD의 회전 관절 속성은 degree를 사용하므로 단위가 다르다.

```python
import math
print(math.radians(90))   # 1.570796...
print(math.degrees(0.4))  # 약 22.9도
```

GUI에서 `shoulder`를 선택하여 Body 0/Body 1, Axis, Lower/Upper Limit를 확인한다. Property에 보이는 90을 Python 목표값에 그대로 넣으면 90 rad가 되므로 잘못된 명령이다.

## 2. 받침대를 월드에 고정하다

이번 로봇은 바퀴가 없는 고정식 검사 장치이다. 바닥 마찰만으로 붙들어 두면 팔의 운동이 받침대에 반작용을 일으키므로, 처음부터 월드와 연결한 Fixed Joint를 사용한다. `Body0`를 비워 두는 것은 월드에 연결한다는 의미이다.

```python
from pxr import Gf, UsdPhysics

# stage와 base_path는 가져온 장면에서 얻은 값이다.
fixed = UsdPhysics.FixedJoint.Define(stage, "/World/Robot/world_fixed_joint")
fixed.CreateBody1Rel().SetTargets([base_path])
fixed.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0))
fixed.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
```

이 두 위치가 모두 0인 이유는 제공 로봇의 받침대 원점과 월드 원점을 맞추었기 때문이다. 이미 이동한 다른 로봇에 그대로 적용하면 첫 프레임에 큰 보정력이 생긴다. 완결 프로그램은 가져온 Articulation Root를 찾아 정리하고 고정 관절에 하나만 설정한다. 중첩된 Articulation Root를 여러 개 덧붙이지 않는다.

## 3. 새 Articulation API로 위치를 지시하다

6.0.1의 새 코드는 `isaacsim.core.experimental.prims.Articulation`을 사용한다. `SingleArticulation`, `ArticulationController`, `ArticulationAction`은 공식 문서에서 deprecated로 분류되어 있다.

```python
from isaacsim.core.experimental.prims import Articulation

robot = Articulation("/World/Robot")
# Play 후 적어도 한 번 이상 물리 갱신을 진행해야 tensor 조회가 가능하다.
print(robot.dof_names)
assert list(robot.dof_names) == ["shoulder"]
robot.set_dof_gains(stiffnesses=[40.0], dampings=[8.0])
robot.set_dof_max_efforts([20.0])
robot.set_dof_max_velocities([1.0])
robot.set_dof_position_targets([0.4])
angles = robot.get_dof_positions().numpy()
print(angles)  # 로봇 수 x 관절 수: 이 경우 (1, 1)
```

목표값을 설정해도 그 자리로 순간 이동하지 않는다. Drive가 힘을 내고 이후 물리 스텝에서 각도가 변한다. 반대로 상태 자체를 설정하는 함수는 로봇을 순간 이동시킬 수 있으므로, 매 프레임 관절의 현재 위치를 덮어쓰는 방식으로 제어하지 않는다.

## 4. stiffness와 damping을 해석하다

단순화하면 위치 Drive의 작동을 다음 식으로 이해할 수 있다.

```python
# 개념을 설명하는 계산이다. 이 값을 별도 토크 명령으로 동시에 보내지 않는다.
stiffness, damping = 40.0, 8.0
q_target, q, qd = 0.4, 0.2, 0.1
estimated_effort = stiffness * (q_target - q) - damping * qd
print(estimated_effort)  # 7.2
```

stiffness는 목표에서 벗어난 정도에 반응하고 damping은 운동을 억제한다. 숫자를 무조건 크게 하면 정밀도가 높아지는 것이 아니다. 질량·관성, 시간 간격, 힘 제한을 함께 고려해야 한다. 이번 값은 제공한 소형 단일 관절 장면의 시작값이며 다른 로봇의 권장값은 아니다.

## 기대 결과와 문제 진단

22단계 프로그램을 실행하면 1초 동안 초기 위치를 유지하고 2초에 걸쳐 0.4 rad까지 움직인 뒤 멈춘다. 관절 목록이 하나가 아니면 프로그램은 실패한다. 이름이나 배열 길이를 무시하고 첫 번째 원소만 제어하지 않는다.

| 증상 | 먼저 확인하다 |
| --- | --- |
| 관절이 움직이지 않다 | Play 상태, Root 경로, DOF 이름, Drive 힘 제한을 확인한다. |
| 텐서가 유효하지 않다는 오류 | Stop 상태에서 관절값을 읽었는지 확인한다. |
| 로봇이 처음에 튀다 | 고정 관절의 두 프레임이 실제로 일치하는지 확인한다. |
| 값이 매우 크게 움직이다 | degree/rad 혼동과 속도 제한을 확인한다. |

## 확인 과제와 실행 파일

목표 0.4 rad를 degree로 계산하고, ±90° 제한 안에 있는지 확인한다. 그다음 22단계의 [03_robot_stability.py](../../examples/03_robot_stability.py)에서 `set_dof_position_targets`와 `get_dof_positions`가 어느 순서로 호출되는지 설명한다.

## 공식 참고 자료

- [6.0.1 Articulation API와 반환 배열](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.core.experimental.prims/docs/index.html)
- [6.0.1 관절 위치·속도·힘 제어 예제](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/robots_simulation.html)
- [기존 Articulation Controller의 deprecated 안내와 각도 단위](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_simulation/articulation_controller.html)

[이전](19-urdf-inertia.md) · [다음](21-manipulator-stability.md)
