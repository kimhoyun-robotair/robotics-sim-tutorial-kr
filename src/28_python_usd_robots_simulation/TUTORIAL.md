# 28. 로봇 snippet: 두 Articulation과 다섯 제어 모드

권장 학습 순서 **28** · 물리 기초와 Core API 확장 · 출처 ID `t097`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 120단계를 사용합니다. 창을 닫을 때까지 관절 제어와 CSV 기록을 계속합니다. 일정 길이의 비교 기록이 필요하면 `--steps 120`처럼 제한을 지정합니다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 준비

Franka Panda 두 대를 하나의 Articulation view로 묶고 전체/단일 자유도 위치·속도·토크 제어를 비교한다. Isaac 5.1 자산 루트의 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`와 그 종속 파일이 필요하다. `--usd /실제/경로/franka.usd`로 로컬 자산을 사용할 수 있다. 로봇 자산은 패키지에 복제하지 않는다.

## 순서대로 실습

```bash
~/isaacsim/python.sh run.py --control position
~/isaacsim/python.sh run.py --control single-position
~/isaacsim/python.sh run.py --control velocity --target 0.1
~/isaacsim/python.sh run.py --control single-velocity --target 0.1
~/isaacsim/python.sh run.py --control effort --target 0.2
```

1. `/World/Franka_1`, `/World/Franka_2`를 생성하고 X=−1,+1 m로 벌린다. `[1-2]` Prim 표현식에 대응하는 view의 행은 로봇 인스턴스, 열은 제어 자유도다.
2. 자산의 variant 이름/선택지를 `robot_info.json`에서 읽는다. 원문은 Gripper의 AlternateFinger와 Mesh의 Quality를 선택하지만 자산에서 그 선택지가 존재하는지 먼저 확인해야 한다. 본 기본 실행은 제공 자산의 기본 variant를 보존한다.
3. `world.reset()` 후 실제 `dof_names`와 limits를 조회한다. 기본 초기 자세를 이름으로 지정한다. 모든 관절을 같은 1.5에 설정하면 직선 손가락 범위를 위반하므로 사용하지 않는다.
4. position은 일곱 팔 관절의 초기값에 작은 사인파 offset을 준다. single-position은 `panda_joint2`만 변경한다. `set_joint_position_targets`가 드라이브 목표를 바꾸며 `set_joint_positions`의 즉시 상태 변경과 구분한다.
5. velocity 모드에서는 제어할 관절의 stiffness를 0, damping을 20으로 바꾼 후 속도 목표를 전달한다. single-velocity는 두 번째 팔 관절만 선택한다.
6. effort는 두 번째 팔 관절의 stiffness와 damping을 모두 0으로 바꾸고 매 스텝 토크를 전달한다. 중력 보상을 넣지 않았으므로 작은 토크를 줘도 중력 때문에 움직일 수 있다. 다른 관절은 초기 자세 드라이브를 유지한다.
7. `states.csv`에서 각 로봇의 positions, velocities, applied_efforts를 비교한다. applied effort는 직접 적용 명령을 읽는 값이며 모든 모터/접촉 반력을 합친 관절 센서 힘이라고 해석하지 않는다.
8. GUI에서 로봇의 Joint Prim을 선택하고 Drive stiffness/damping과 limits를 대조한다. JSON의 `physics_joint_prims`는 USD 타입 검사 `prim.IsA(UsdPhysics.Joint)`의 결과다.

## 원문의 Dynamic Control API와 대응

원문에는 `omni.isaac.dynamic_control`의 핸들 기반 예제도 포함된다. 이 구현은 5.1 Core Articulation으로 동일한 제어 동작을 제공하며 아래처럼 대응한다. 이전 API 코드를 그대로 실행하고 싶은 경우 **Play 이후**에 Script Editor에서 인터페이스를 취득한다.

```python
from omni.isaac.dynamic_control import _dynamic_control
controller = _dynamic_control.acquire_dynamic_control_interface()
handle = controller.get_articulation("/World/Franka_1")
print(controller.peek_object_type("/World/Franka_1"))
print(controller.get_articulation_joint_count(handle), controller.get_articulation_dof_count(handle), controller.get_articulation_body_count(handle))
dof = controller.find_articulation_dof(handle, "panda_joint2")
print(controller.get_dof_state(dof, _dynamic_control.STATE_ALL))
controller.wake_up_articulation(handle)
controller.set_dof_position_target(dof, -0.4)
```

이 snippet은 해당 확장이 제공되는 5.1 GUI의 Script Editor에서 실행한다. `--steps`를 생략한 로컬 실행 장면에는 `/World/Franka_1`이 이미 있다. 별도 빈 Stage에서 실습한다면 **Create > Robots > Franka Emika Panda Arm**으로 로봇을 삽입하고 실제 루트 경로를 `/World/Franka_1`로 맞춘다. 지면과 조명도 **Create > Physics > Ground Plane**, **Create > Lights > Distant Light**로 추가한다. UI에서 그 이름이 다르면 코드 경로도 바꾼다.

| 원문 API | 이 패키지 API/의미 |
|---|---|
| set_articulation_dof_position_targets / set_dof_position_target | `set_joint_position_targets(..., joint_names=...)` |
| set_articulation_dof_velocity_targets / set_dof_velocity_target | `set_joint_velocity_targets`; 속도 제어 전 stiffness를 0으로 변경 |
| set_articulation_dof_efforts | `set_joint_efforts`; direct effort와 drive를 동시에 섞지 않음 |
| get_articulation_dof_states | `get_joint_positions`, `get_joint_velocities`, `get_applied_joint_efforts` |
| get_articulation_*_count | `num_joints`, `num_dof`와 USD Joint 타입/관계 검사 |

## 한 가지 변수 실험과 문제 해결

single-velocity에서 `--target`만 0.1에서 −0.1로 바꾸고 `panda_joint2`의 변화 방향을 비교한다. `--target`은 이 작은 실습에서 절댓값 0.5 이하로 제한한다. 관절 이름 오류는 자산/variant가 다르다는 신호다. 속도나 토크가 먹지 않는다면 여전히 위치 드라이브가 켜져 있는지 확인한다. 손가락은 m 단위이고 회전 관절은 rad 단위다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Robot Simulation Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/robots_simulation.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
