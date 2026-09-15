# 56. Lula RMPflow: 동적 목표와 장애물

권장 학습 순서 **56** · 로봇 제어와 동작 계획 · 출처 ID `t136`

Franka가 빨간 목표를 향해 움직이며 파란 장애물을 회피하도록 RMPflow를 연결합니다. 목표/세계 상태 갱신, 기본 설정 로딩, collision sphere 시각화와 내부 rollout 디버깅을 각각 실습합니다.

## 이 실습의 의도

Franka가 목표에 접근하는 반응과 등록한 장애물을 피하는 반응을 RMPflow로 조합하고 실제 물리 관절에 전달합니다. 빨간 목표는 추종 위치를 표시하고 파란 고정 박스는 물리 충돌체이면서 정책에 명시적으로 등록한 장애물입니다. 기본 목표와 장애물은 정지해 있지만 매 스텝 pose를 갱신하므로 GUI에서 옮긴 위치에도 대응하며, 위치 추종 결과를 실제 관절 상태의 FK로 기록합니다.

## 실행 후 확인할 것

- GUI에서 `/World/panda`, 빨간 `/World/target`, 파란 `/World/obstacle`을 확인합니다. 기본 `(0.5, 0, 0.7)` m 목표 쪽으로 말단이 접근하는지 보되, 빨간 marker를 잡거나 손의 방향까지 맞추는 동작을 기대하지 않습니다.
- `tracking.json`에서 30스텝 간격의 `target_m`, `end_effector_m`, `position_error_m`를 비교합니다. 정지한 도달 가능 목표에서 실제 FK 오차가 전반적으로 줄어드는지 확인하고, 마지막 표본의 값을 고정된 합격 수치로 사용하지 않습니다.
- GUI Move 도구로 target을 옮기면 추종 위치가 바뀌는지, obstacle을 옮기거나 `--obstacle-y` 부호를 바꾸면 접근 경로가 어떻게 달라지는지 확인합니다. 바닥 등 장면에 보이는 모든 물체가 자동으로 정책에 등록되는 것은 아닙니다.
- `--debug-spheres`에서 collision sphere와 실제 로봇 외곽을 함께 살펴보고 장애물 근처의 여유를 관찰합니다. `tracking.json`에는 접촉이나 최소 충돌 거리가 없으므로 작은 위치 오차만으로 충돌 회피까지 판정하지 않습니다.
- `--ignore-state --debug-spheres`를 함께 사용하면 내부 rollout 시각화가 실제 로봇보다 앞서거나 달라질 수 있습니다. 이는 정책이 실제 상태 갱신을 무시하는 비교 모드의 의도이며, 실제 추종은 여전히 FK 기록으로 확인합니다. 막힌 배치에서 정체할 수도 있으므로 전역 경로 탐색 성공을 보장하는 실습으로 해석하지 않습니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

Isaac Sim 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. `get_assets_root_path()`가 반환하는 asset 서버 또는 로컬 asset 팩에서 읽습니다. 첫 로딩에는 네트워크가 필요할 수 있습니다. 이 로봇 USD와 해당 재질/mesh 참조를 함께 사용할 수 있어야 합니다.

터미널에서 이 패키지 폴더(`56_motion_manipulators_rmpflow`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --debug-spheres
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --target 0.5 -0.2 0.6
"$ISAAC_SIM_ROOT/python.sh" run.py --debug-spheres --ignore-state
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. 기본 실행에서 `/World/panda`, `/World/target`, `/World/obstacle`을 확인합니다. GUI Move 도구로 target을 움직이면 다음 물리 스텝에서 새로운 월드 위치를 읽습니다.
2. `RmpFlow` 설정을 읽는 줄을 확인합니다. `load_supported_motion_policy_config('Franka','RMPflow')`가 robot description YAML, URDF, RMPflow parameter YAML, end-effector frame, 내부 substep 설정을 반환합니다. 이 파일은 `isaacsim.robot_motion.motion_generation/motion_policy_configs/franka/` 아래 설치되어 있습니다.
3. `policy.add_obstacle(obstacle)`은 보이는 물체를 정책의 장애물로 등록합니다. USD 장면에 보이는 것만으로 Lula의 world 모델에 자동 등록되는 것은 아닙니다. 매 스텝 `update_world()`로 등록한 물체의 pose를 갱신합니다.
4. `--obstacle-y 0.15`와 `--obstacle-y -0.15`를 별도로 실행해 회피 경로가 어떻게 달라지는지 관찰합니다. GUI에서 obstacle을 움직였을 때도 world 갱신으로 반영됩니다.
5. `--debug-spheres`로 로봇을 감싼 collision sphere와 end-effector 시각화를 켭니다. 구가 실제 mesh를 충분히 감싸는지 확인합니다.
6. `--ignore-state`를 추가합니다. 이 모드는 실제 관절 상태를 다음 계산에 반영하지 않고 정책 내부에서 이상적으로 추종한다고 가정하여 rollout합니다. 시각화가 로봇보다 앞서 갈 때는 정책 경로와 실제 drive 성능을 나누어 살펴볼 수 있습니다. 기본 제어에는 이 옵션을 끕니다.

## RMPflow와 물리 제어의 역할

RMPflow는 task-space target을 향한 가속과 충돌/관절 한계 등 여러 반응을 조합하는 reactive motion policy입니다. 전역 경로 탐색과 같지 않으며 막힌 환경에서는 local minimum에 머물 수 있습니다. 이 실습은 위치 목표만 지정하므로 orientation 목표는 강제하지 않습니다.

`set_end_effector_target()`은 목표를 지정하고 `ArticulationMotionPolicy.get_next_articulation_action()`은 로봇 관절 순서에 맞는 action을 만듭니다. `robot.apply_action()`이 drive 목표로 전달한 뒤 `world.step()`이 물리 상태를 계산합니다. 내부 최대 integration substep과 바깥 물리 시간간격 1/60 s는 서로 다릅니다.

USD articulation과 Lula URDF는 같은 조립 구조를 표현해야 합니다. 그리퍼를 추가했다면 URDF의 link/frame 및 robot description도 맞춰야 합니다. 로봇 base를 움직였을 때는 `set_robot_base_pose()`에 현재 월드 pose를 넘겨야 target과 collision 위치가 같은 좌표계가 됩니다. 이 코드에서는 매 스텝 갱신합니다.

## 관찰 기준과 한 변수 실험

`tracking.json`은 30스텝마다 목표, 실제 관절 상태로 계산한 end-effector FK, 거리 오차를 기록합니다. 목표가 정지한 도달 가능 위치라면 오차가 줄어드는지 봅니다. sphere가 장애물과 겹치지 않는지 화면도 확인하지만, 샘플 위치만으로 연속 시간 충돌 부재를 증명하지는 않습니다. `--obstacle-y`만 바꾸어 같은 목표에서 경로 차이를 비교합니다.

## 문제 해결

목표를 따라가지 않으면 먼저 target이 작업영역 안인지, base pose가 맞는지, 실제 end-effector frame이 `right_gripper`인지 확인합니다. 로봇이 sphere와 달리 늦게 움직이면 joint drive gain과 physics timestep을 살펴봅니다. 빠른 움직임의 overshoot를 RMPflow 파라미터 문제라고 단정하지 않습니다. 지원 config를 못 찾으면 5.1 motion generation extension의 설치/활성 상태를 확인합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Lula RMPflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_rmpflow.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
