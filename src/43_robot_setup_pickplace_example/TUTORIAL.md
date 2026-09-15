# 43. UR10e+Robotiq의 그리퍼·IK·RMPflow·집기 실행하기

권장 학습 순서 **43** · 로봇 자산 가져오기와 제작 · 출처 ID `t127`

공식 인덱스 **t127** · Isaac Sim **5.1.0**

## 이 실습의 의도

UR10e+Robotiq의 그리퍼 연동, IK 목표 pose 추종, RMPflow 연속 제어, 물리 기반 pick-and-place를 `--exercise`로 나누어 실행합니다. 기본 모드는 `pick`이며 파란 block을 실제로 잡아 옮기는 시퀀스를 진행합니다. 로컬 `config/`의 운동학·motion 설정과 공식 USD의 물리 모델을 함께 사용하여, controller가 명령을 끝낸 것과 손끝·물체가 실제 목적지에 도달한 것을 별도로 측정하는 것이 핵심입니다.

## 실행 후 확인할 것

- **그리퍼 모드:** `--exercise gripper`에서는 `/ur/ee_link`의 손가락이 함께 닫혔다 열려야 합니다. 800 step 주기로 `finger_joint` 목표가 0→0.7→0 rad로 변하므로 `samples[].finger_rad`의 증가·감소를 비교합니다. 120 step 같은 짧은 실행은 한 번의 닫기·열기를 모두 보여 주지 않습니다.
- **IK·RMPflow 모드:** 빨간 `/World/Target`은 기본 `(0.5,0,0.5)` m 목표입니다. 충분히 진행한 뒤 그리퍼 base가 접근하는지 화면과 `target_error_m`로 확인합니다. IK에서는 `ik_failures`도 보며, 이 오차는 위치 거리만 기록하므로 목표 orientation 일치까지 수치로 검증하지는 않습니다.
- **pick의 실제 물체:** `/World/Cube`의 파란 block이 초기 높이에서 바닥으로 내려온 뒤 잡혀 올라가고 `(-0.3,0.6,0.05)` m 부근에 놓이는지 관찰합니다. `samples[].cube_m`과 최종 `cube_target_error_m`를 함께 봅니다. pick의 빨간 표식은 놓기 위치이며 `--target` 값 대신 고정된 place goal을 사용합니다.
- **시퀀스와 성공 구분:** pick에서 `controller_done=true`와 함께 실제 큐브가 목표 3 cm 이내에 안정적으로 놓였는지 확인합니다. 이 3 cm는 본 실습의 관찰 기준이며 실행기가 자동 합격 판정을 하지는 않습니다. `target_error_m`는 그리퍼 base와 표식의 거리이므로 pick의 물체 놓기 성공 기준으로 사용하지 않습니다.
- **완료 후와 파일:** pick 시퀀스가 끝나도 GUI를 열어 둔 동안 물리는 계속 진행하며 다음 집기를 자동으로 재시작하지 않습니다. `result.json`은 창을 닫거나 지정한 step 수를 마칠 때 저장되고, pick 외 모드의 `controller_done`·`cube_target_error_m`는 `null`인 것이 정상입니다.
- **기존 확인 범위:** 아래 실행 기록은 `--exercise ik --headless --steps 120` 조건입니다. 기록의 오차를 모든 목표·모드의 고정 정답으로 삼거나, 그 기록으로 gripper·RMPflow·pick 성공까지 확인했다고 해석하지 않습니다.

## 준비와 실행

필요한 motion 설정을 `config/`에 포함하여 다른 로컬 패키지에서 생성한 파일에 의존하지 않습니다.

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, 설치에 포함된 `isaacsim.robot.manipulators`와 Lula/RMPflow 확장, 다음 공식 실제 로봇 에셋이 필요합니다.
`/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd`
로컬 에셋 팩은 `--asset /절대경로/ur_gripper.usd`로 지정합니다. USD가 참조하는 그리퍼/mesh/재질 파일도 함께 접근 가능해야 합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --exercise gripper
"$ISAAC_SIM_ROOT/python.sh" run.py --exercise ik --target 0.5 0 0.5
"$ISAAC_SIM_ROOT/python.sh" run.py --exercise rmpflow --target 0.5 0 0.5
"$ISAAC_SIM_ROOT/python.sh" run.py --exercise pick
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 6000회 한도를 사용한다. 실행 중에도 물리·제어가 계속 진행되며, 결과 요약은 실행을 마칠 때 기록한다.

`--headless`는 창을 숨깁니다. 물리/GPU 요구사항은 그대로입니다. default output은 이 폴더 `output/<고유번호>/result.json`이며 `--output`은 새 경로만 허용합니다. 양수 `--steps` 또는 headless 기본 한도를 사용하면 지정 횟수 후 종료하며, step 한도 없는 GUI는 창을 닫을 때까지 유지됩니다. pick은 물리 **200 Hz**, 나머지는 **60 Hz**입니다. 따라서 6000 pick steps는 시뮬레이션 시간 30초입니다.

## 파일과 원문에서 조정한 부분

- `run.py`: 모델 로딩, 그리퍼/IK/RMPflow/pick 제어, 실제 상태 측정.
- `config/ur10e_kinematics.urdf`: 공식 모델의 joint/link/inertial을 유지한 운동학용 URDF. visual/collision mesh 요소는 제거했습니다. 렌더링/접촉은 공식 USD가 담당합니다.
- `config/robot_descriptor.yaml`: 팔의 cspace, default_q, 고정 그리퍼 joint와 collision spheres.
- `config/ur10e_rmpflow_common.yaml`: RMPflow의 목표·관절제한·충돌 반응 파라미터.
- `NOTICE.md`, `LICENSE-APACHE-2.0.txt`: 포함한 공식 5.1 설정의 출처/수정/라이선스.

원문 코드의 gripper closed=40은 Python 관절 단위와 구분해야 합니다. 이 구현은 실제 URDF finger_joint limit **0.7 rad**에 맞춰 0~0.7 rad를 사용합니다(USD inspector에서는 약 40.1°). 또한 공식 descriptor의 `ee_link/...` sphere 이름 7개를 함께 제공된 URDF의 실제 link 이름으로 맞췄습니다. block 높이 0.1 m에 맞춰 놓기 목표 z는 **0.05 m**로 지정했습니다. 수정 이유를 숨긴 채 원문 코드와 동일하다고 설명하지 않습니다.

## 1. Gripper: 하나의 drive와 mimic

1. gripper 모드로 실행해 Stage의 `/ur/ee_link`를 봅니다. 손가락 하나의 `finger_joint`가 직접 구동되고 다른 finger/knuckle joint는 mimic으로 연결됩니다.
2. `ParallelGripper(..., use_mimic_joints=True)`의 end effector path와 joint 이름을 읽습니다. 닫힘은 0.7 rad, 열림은 0 rad입니다.
3. 0~400단계에는 선형으로 닫고 400~800단계에는 엽니다. 결과 samples의 실제 `finger_rad`가 목표 방향을 따라가는지 봅니다.
4. `SingleManipulator`는 팔 articulation과 이 gripper를 묶어 높은 수준의 API로 접근하도록 합니다. `world.reset()` 후에 관절/그리퍼 핸들을 사용합니다.

## 2. IK: 원하는 pose를 관절 값으로

1. ik 모드로 실행하면 빨간 Target cube가 (0.5,0,0.5) m에 생깁니다. GUI에서 Target을 조금 움직여도 됩니다.
2. `LulaKinematicsSolver`가 로컬 URDF/descriptor를 읽고, `ArticulationKinematicsSolver`가 solver의 여섯 arm joint를 실제 articulation DOF 순서에 연결합니다.
3. `compute_inverse_kinematics`의 `success`가 참일 때만 action을 적용합니다. 실패 횟수는 result의 `ik_failures`로 남깁니다.
4. end effector가 실제 Target에 도달하는지 result의 `target_error_m`를 확인합니다. 이는 IK 해의 존재뿐 아니라 물리 실행 후 실제 pose의 오차입니다.

URDF link 이름 `ee_link_robotiq_arg2f_base_link`는 USD Prim `/ur/ee_link/robotiq_arg2f_base_link`와 표기가 다릅니다. 둘 다 자기 데이터 구조 안의 주소이며 구분해서 사용합니다. 목표 orientation은 공식 FollowTarget 기본값에 맞춘 Euler (-π,0,π)의 쿼터니언입니다.

## 3. RMPflow: 매 순간의 motion 정책

1. rmpflow 모드로 같은 목표를 실행합니다. RmpFlow는 목표와 현재 상태로 motion을 계속 갱신합니다.
2. `ArticulationMotionPolicy`가 RMPflow와 실제 로봇의 시간 간격을 연결하고 `MotionPolicyController.forward()`가 action을 만듭니다.
3. initial arm joint를 YAML의 default_q로 맞추는 코드를 확인합니다. USD 초기 pose와 solver 모델의 초기 pose 불일치를 피합니다.
4. 목표/관절제한/충돌 RMP 설정을 YAML에서 찾아 봅니다. 이 단순 장면은 별도의 외부 장애물 등록을 포함하지 않으므로 임의의 새 obstacle을 넣었다고 자동으로 motion 충돌 회피가 증명되지는 않습니다.

## 4. Pick and place: controller 상태와 실제 성공 분리

1. pick 모드에서 (0.3,0.3,0.3) m의 파란 block을 봅니다. 크기는 (0.1,0.0515,0.1) m입니다. 목표는 (-0.3,0.6,0.05) m입니다.
2. PickPlaceController는 RMPflow를 cspace controller로 쓰고 접근, 하강, 그리퍼 닫기, 상승, 운반, 놓기 단계를 실행합니다.
3. `end_effector_offset=[0,0,0.20]`은 gripper base에서 실제 집는 지점까지의 보정입니다. 물체 중심을 로봇 base에 직접 겹치는 값이 아닙니다.
4. `events_dt`는 10단계의 시간 진행을 정합니다. 센서로 잡힘을 감지하는 성공 판정 값이 아닙니다.
5. result의 `controller_done`과 **실제 cube_target_error_m**를 함께 확인합니다. 큐브가 실제로 들어 올려지고 목표 3 cm 근처에 놓였는지 화면/숫자로 판단합니다. controller_done만으로 성공이라 하지 않습니다.

한 변수 실험은 IK의 `--target` x만 0.5→0.6으로 바꾸는 것입니다. 다음에는 gripper 모드에서만 속도를 바꾸어 다른 변수와 섞지 않습니다. pick에서 놓치면 finger friction/max force, block pose, 0.20 m grasp offset과 이벤트 시간을 각각 따로 검토합니다.

## 범위와 문제 해결

이 튜토리얼은 simulator의 정확한 cube pose를 직접 읽습니다. 실제 로봇의 지각·물체 검출·접촉 추정·일반 물체 grasp planning을 구현하지 않습니다. 물리 기반 실습의 성공 여부는 실제 측정으로 기록하며 미실행을 성공으로 표시하지 않습니다.

모델이 없으면 asset 경로와 gripper variant를 확인합니다. IK가 실패하면 목표를 더 가까운 기본 위치로 돌리고 joint/link 이름을 점검합니다. YAML sphere 이름과 URDF link 이름이 다르면 solver 설정 오류를 수정해야 합니다. 일반 Python은 `--help`만 가능하며 실제 실행은 Isaac의 python.sh를 사용합니다.
## 버전 고정 출처

- [NVIDIA Isaac Sim 5.1.0 — Tutorial 9: Pick and Place Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html)

한국어 절차는 새로 작성했습니다. 원문 GUI 기능과 이 폴더의 준비/검사/실행 코드를 구별해 설명합니다. 실제 runtime 검증 범위는 tutorial.json의 verification 기록을 확인합니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
