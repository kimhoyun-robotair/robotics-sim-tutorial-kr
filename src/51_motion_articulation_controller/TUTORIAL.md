# 51. Articulation Controller: 관절 목표와 실제 상태

권장 학습 순서 **51** · 로봇 제어와 동작 계획 · 출처 ID `t133`

Franka의 팔과 그리퍼 관절을 이름으로 선택하고 position target을 전달합니다. 공식 Python/OmniGraph 인터페이스를 익히며 순간 이동과 물리 drive 제어의 차이를 확인합니다.

## 이 실습의 의도

Franka의 관절 이름을 실제 DOF 인덱스로 바꾸고 선택한 관절에만 위치 목표를 보내는 흐름을 익힙니다. 기본 실행은 팔 7축과 손가락 2축에 각 관절의 고정된 목표를 반복 전달하고, 물리 drive가 만든 최종 관절 상태를 저장합니다. 목표 배열을 보낸 것과 실제 로봇이 그 값에 도달한 것을 별도로 확인하는 실습입니다.

## 실행 후 확인할 것

- GUI의 `/World/panda`에서 팔이 목표 자세로 움직이고 두 손가락이 지정한 벌림값으로 이동하는지 봅니다. 기본 `--finger-width 0.02`는 손가락 관절 하나의 이동 목표 0.02 m이며 전체 집게 폭 값이 아닙니다.
- 실행을 마친 뒤 `joints.json`의 `joint_names`, `joint_indices`, `targets`, `measured`를 같은 배열 순서로 대조합니다. 기본 모드는 9개, `--fingers-only` 모드는 두 finger 관절만 기록해야 합니다.
- 각 관절의 `absolute_error`를 초기 오차 `|initial-targets|`와 비교해 실제 추종을 확인합니다. 팔의 오차는 rad, 손가락의 오차는 m이므로 같은 숫자로 서로 다른 관절의 품질을 비교하지 않습니다.
- 이 JSON은 초기값과 최종값만 저장합니다. 수렴 과정이나 중간 overshoot는 GUI에서 관찰하거나 서로 다른 `--steps`의 별도 실행을 비교하며, 짧은 실행의 잔류 오차를 곧바로 제어 실패로 판단하지 않습니다.
- `--fingers-only --finger-width 0.03`과 0.01을 비교해 손가락 목표와 간격이 함께 바뀌는지 확인합니다. 이 모드는 팔 관절에 새 목표를 보내지 않으므로 팔 전체가 반드시 정지한다고 보장하는 실험은 아닙니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

Isaac Sim 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. `get_assets_root_path()`가 반환하는 asset 서버 또는 로컬 asset 팩에서 읽습니다. 첫 로딩에는 네트워크가 필요할 수 있습니다. 이 로봇 USD와 해당 재질/mesh 참조를 함께 사용할 수 있어야 합니다.

터미널에서 이 패키지 폴더(`51_motion_articulation_controller`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --fingers-only --finger-width 0.03
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. Stage의 `/World/panda`를 펼칩니다. articulation은 강체 링크와 조인트로 구성된 로봇을 물리 엔진에서 묶어 제어하는 단위입니다.
2. `world.scene.add(SingleArticulation(...))`로 prim을 Python 객체에 연결합니다. `world.reset()`이 scene 객체를 초기화한 뒤에 관절 상태/이름을 읽고 명령을 보냅니다. USD를 참조하는 것만으로 물리 핸들이 초기화되지는 않습니다.
3. `get_dof_index(name)`로 `panda_joint1`부터 7까지와 finger 관절의 실제 인덱스를 얻습니다. `joints.json`에서 이름, 인덱스, 초기값, 목표값, 최종 측정값을 나란히 확인합니다.
4. 기본 실행은 팔의 7개 관절과 손가락 2개를 제어합니다. `--fingers-only --finger-width 0.03`은 두 손가락 관절에 각각 0.03 m의 위치 목표를 보냅니다. 전체 그리퍼 폭은 양쪽 이동량과 geometry를 함께 고려해야 합니다.
5. GUI 실행을 늘려 움직임을 관찰합니다. command가 한 번에 바뀌어도 링크는 물리 drive를 통해 목표로 이동합니다. 종료 시 absolute_error를 초기 오차와 비교합니다.

## API와 단위

`SingleArticulation`은 내부 articulation view와 controller를 소유합니다. `ArticulationAction(joint_positions=..., joint_indices=...)`는 이번 명령의 목표와 적용할 자유도를 표현하고 `apply_action()`이 물리 drive에 전달합니다. 벡터 길이와 인덱스 순서는 반드시 맞아야 합니다. 이 예제는 0이라는 위치도 명시적 목표로 사용합니다. 제어하지 않을 관절은 인덱스에서 제외하는 방식으로 모호함을 피합니다.

각도는 Python API에서 radian, USD 관절 속성 화면에서는 degree일 수 있습니다. 슬라이딩 손가락 관절은 m 단위입니다. `set_joint_positions()`는 상태를 바로 바꾸는 기능이므로 일반적인 목표 추종과 다릅니다. velocity 제어에는 `joint_velocities`, torque 제어에는 `joint_efforts`를 사용하고 controller의 제어 모드와 gain을 맞춰야 합니다. 동일 관절에 위치와 torque 제어를 동시에 적용하지 않습니다.

직접 `ArticulationController`를 구성하려면 복수 articulation view를 만들고 물리 초기화 후 `initialize(view)`에 전달합니다. 단일 로봇의 초급 실습에서는 이를 감싸는 `SingleArticulation`을 사용해 초기화 순서를 단순하게 유지합니다.

## OmniGraph로 같은 손가락 동작 만들기

1. 코드 실행이 끝난 후 새 GUI 세션에서 위 Franka USD를 `/World/panda`에 참조합니다. PhysicsScene을 추가하고 Play합니다.
2. `Window > Graph Editors > Action Graph`에서 새 그래프를 만들고 **On Playback Tick**과 **Isaac Articulation Controller** 노드를 놓습니다.
3. Tick의 exec 출력을 controller의 `execIn`에 연결합니다. `robotPath`를 `/World/panda`로 설정하고 `targetPrim`은 비웁니다.
4. `jointNames`에 `[panda_finger_joint1, panda_finger_joint2]`, `positionCommand`에 `[0.03,0.03]`을 입력합니다. 배열 입력에는 필요한 **Construct Array** 노드를 연결할 수 있습니다. `jointIndices`와 velocity/effort command는 비웁니다.
5. Play 중 손가락을 관찰하고 `positionCommand`만 `[0.01,0.01]`로 바꿉니다. 같은 관절을 Python과 그래프 양쪽에서 동시에 제어하지 않습니다.

## 관찰 기준과 한 변수 실험

`--fingers-only`를 유지하고 `--finger-width`만 0.03에서 0.01로 바꾸어 비교합니다. 두 손가락의 목표와 최종 측정값이 함께 달라지는지 확인합니다. `joints.json`에는 팔의 측정값이나 시간별 응답은 없으므로 팔의 정지 여부와 손가락의 중간 움직임은 GUI에서 별도로 관찰합니다.

## 문제 해결

초기화 오류는 reset/play 이전에 controller를 사용했는지 확인합니다. 관절명 오류는 다른 robot USD를 불러왔는지 확인합니다. 흔들림이나 느린 추종은 목표값과 측정값을 비교하고 USD의 stiffness/damping을 확인합니다. 수치가 출력됐다는 사실만으로 목표 도달을 주장하지 않습니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Articulation Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.
