# 54. Lula Kinematics Solver: FK와 IK

권장 학습 순서 **54** · 로봇 제어와 동작 계획 · 출처 ID `t138`

원하는 end-effector 위치에서 관절 해를 구하고, 실제 관절 위치로부터 말단 좌표를 다시 계산합니다. IK 수렴 플래그와 FK 거리 오차를 함께 기록하여 해의 존재와 물리 추종을 구분합니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

Isaac Sim 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. `get_assets_root_path()`가 반환하는 asset 서버 또는 로컬 asset 팩에서 읽습니다. 첫 로딩에는 네트워크가 필요할 수 있습니다. 이 로봇 USD와 해당 재질/mesh 참조를 함께 사용할 수 있어야 합니다.

터미널에서 이 패키지 폴더(`54_motion_manipulators_lula_kinematics`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --target 0.3 0 0.5
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --target 0.4 0.1 0.6
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. `load_supported_lula_kinematics_solver_config('Franka')`로 URDF와 robot description을 가져옵니다. `LulaKinematicsSolver`는 robot kinematics를 계산하며 `ArticulationKinematicsSolver`는 simulator의 관절 상태와 연결합니다.
2. `--frame right_gripper`가 기본 end-effector입니다. `kinematics.json`의 available_frames는 실제 URDF에서 읽은 목록입니다. USD prim 경로와 URDF frame 이름은 같은 문자열 체계를 사용하지 않으므로 `/World/panda/...`를 frame 인수로 넣지 않습니다.
3. target의 월드 위치를 읽고 solver에 현재 base pose를 지정합니다. base가 원점이라는 가정을 없애야 target도 월드 좌표로 해석됩니다.
4. `compute_inverse_kinematics(position)`의 `(action, success)`를 확인합니다. success일 때만 action을 적용합니다. 이 예제는 위치 목표만 사용하며 원문처럼 orientation도 제한하려면 normalized quaternion을 두 번째 인수로 전달합니다.
5. 물리 스텝 후 `compute_end_effector_pose()`로 실제 관절 상태의 FK를 계산합니다. 반환값은 위치와 **3×3 회전행렬**입니다. 이것을 quaternion 4개와 혼동하지 않습니다.
6. `kinematics.json`의 trace에서 IK success와 FK position_error를 비교합니다. IK가 즉시 성공해도 로봇의 drive가 따라가는 데는 시간이 필요합니다.

## 핵심 개념

Forward Kinematics(FK)는 관절 값 q를 말단 pose로 보내는 계산입니다. Inverse Kinematics(IK)는 목표 pose에 맞는 q를 찾으며 해가 여러 개이거나 없을 수 있습니다. 7축 Franka는 같은 위치에 도달하는 여러 자세를 가질 수 있습니다. warm start를 현재 자세로 잡는 wrapper가 연속 움직임에 도움이 되지만 경로의 collision이나 최적성을 보장하지 않습니다.

`LulaKinematicsSolver`를 단독으로 사용할 때는 `compute_forward_kinematics(frame_name, active_joint_positions)`로 원하는 관절 벡터의 pose를 계산할 수 있습니다. 여기서는 `ArticulationKinematicsSolver`가 actual articulation state를 읽고 Lula active joint 순서로 매핑합니다. USD articulation의 gripper를 조립/변경했다면 URDF frame과 offset도 일치시켜야 합니다.

## 관찰 기준과 한 변수 실험

정지된 도달 가능 target에서 `ik_success=true`가 나타나고 `position_error_m`가 줄어드는지 확인합니다. `--target`의 z만 0.5에서 0.6으로 바꾸어 결과를 비교합니다. 그 뒤 `--target 3 0 3`으로 도달 불가능한 목표의 실패 처리도 확인합니다. 실패한 action을 이전 성공값으로 꾸며 기록하지 않습니다.

## 문제 해결

알 수 없는 frame 오류는 출력 가능한 frame 목록을 확인합니다. 좌표가 일정하게 어긋나면 base pose, frame offset, 단위를 확인합니다. IK success가 true인데 물체를 통과하는 것은 IK 자체가 collision-free path planner가 아니기 때문입니다. 실제 pick-and-place 경로를 계획했다는 의미로 사용하지 않습니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Lula Kinematics Solver](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_kinematics.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
