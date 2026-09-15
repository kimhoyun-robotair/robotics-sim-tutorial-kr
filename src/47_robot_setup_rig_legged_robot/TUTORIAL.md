# 47. H1 locomotion policy와 USD 관절 설정 맞추기

권장 학습 순서 **47** · 로봇 자산 가져오기와 제작 · 출처 ID `t131`

공식 Rigging a Legged Robot for Locomotion Policy의 핵심은 **이미 학습된 policy가 가정한 초기 자세·gain·한도와 USD 로봇을 일치시키는 것**이다. 이 패키지는 H1의 19개 관절을 실제 USD API로 설정하고 radians/degrees 변환표를 저장한다. locomotion policy 추론이나 학습을 실행하는 수업은 아니다. Isaac Sim 내부 Policy Controller는 이 설정을 런타임에 처리할 수 있지만 외부 ROS 같은 프로세스가 policy를 구동할 때는 asset 설정 일치가 필요하다.

## 이 실습의 의도

H1 policy 입력의 초기 자세와 actuator 값을 USD의 관절 상태·drive·한도에 옮겨, 같은 로봇 설정을 서로 다른 단위 체계로 표현하는 방법을 익힌다. 19개 revolute joint의 이름을 정규식과 매칭하고 각도·각속도는 rad에서 deg로, gain은 rad당 값에서 deg당 값으로 변환한다. 기본 실행은 로컬 override와 변환 보고서를 작성한 뒤 장면을 열어 두며 Play나 policy 추론을 자동 실행하지 않는다.

## 실행 후 확인할 것

- `joint_configuration.json`에 19개 관절이 있고 초기 위치, USD 위치, rad 기반 gain, deg 기반 gain, effort/velocity limit가 함께 기록됐는지 확인한다. 관절 누락·중복 매칭 또는 19개가 아닌 입력은 코드가 오류로 처리한다.
- `h1_policy.usda`를 연 Property에서 knee의 Joint State Position과 Drive Target Position이 모두 약 45.26°인지 확인한다. 두 값은 입력 0.79 rad에서 변환한 시작 상태와 목표를 각각 뜻한다.
- left_hip_yaw의 USD stiffness≈2.61799와 damping≈0.0872665가 입력 150과 5에 대응하는지 비교한다. 각도와 gain의 변환 방향을 반대로 적용해야 하므로 숫자가 같은 것을 기대하지 않는다.
- `/h1`의 시작 위치가 `(0, 0, 1.05)` m인지 확인한다. 장면이 정지해 있거나 관절 초기 자세가 아직 물리 상태로 반영되지 않은 것만으로 설정 실패라 판단하지 말고 작성된 Property를 먼저 확인한다.
- 런타임 값은 GUI에서 직접 Play한 뒤 `inspect_runtime.py`의 DOF 이름과 rad 기반 값을 대조한다. 이 실습에는 균형 제어 policy가 없으므로 Play 후 서 있기·걷기·넘어지지 않기를 성공 기준으로 삼지 않는다.

## 준비와 실행

Isaac Sim **5.1.0**, RTX GPU, `/Isaac/Robots/Unitree/H1/h1.usd`를 읽을 수 있는 assets root가 필요하다. `h1_policy.json`은 공식 **5.1**의 `h1_env.yaml` 중 초기 joint pose와 legs/feet/arms actuator의 숫자만 담은 로컬 입력이다. 다른 패키지 또는 Isaac Lab 설치 없이 USD 설정 실습을 할 수 있다.

```bash
cd src/47_robot_setup_rig_legged_robot
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 120 --output output/authored
# GUI에서 Property를 확인할 때:
"$ISAAC_SIM_PATH/python.sh" run.py --output output/gui
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

`h1_policy.usda`는 원본 H1 위의 로컬 override layer다. `joint_configuration.json`은 실제로 찾아 설정한 19개 joint의 값이다. 기존 output은 덮어쓰지 않는다. 이 프로그램은 timeline Play를 자동으로 누르지 않는다.

## 초기 자세와 관절 API

1. `h1_policy.json`의 정규식과 관절명을 맞춘다. `.*_hip_pitch=-0.28`, `.*_knee=0.79`, `.*_ankle=-0.52`, `.*_shoulder_pitch=0.28`, `.*_elbow=0.52` **rad**다. 나머지 hip yaw/roll, torso, shoulder roll/yaw는 0이다. joint velocity는 모두 0이다.
2. USD 관절의 Property에 **Joint State Angular**, **Angular Drive**가 생겼는지 확인한다. `Target Position`과 Joint State Position은 rad를 deg로 변환한 값이다. 예를 들어 knee 0.79 rad는 약 45.26°다. Joint State는 시작 상태, Drive Target은 제어 목표이므로 둘 다 확인한다.
3. 실제 GUI 방식으로 자세를 저장하려면 각 joint target을 입력하고 Play로 정착시킨다. 넘어짐 방지용으로 `/h1/torso_link`와 world 사이에 임시 Fixed Joint를 만들 수 있다. **Edit → Preferences → Physics → Reset Simulation on Stop**을 잠시 해제하여 Stop 뒤 상태를 저장한다. 임시 fixed joint를 지우고 저장한 뒤 Reset Simulation on Stop은 다시 켠다. 이 패키지는 같은 초기 joint state를 API로 직접 작성한다.
4. 원본 environment의 robot initial world position은 (0,0,1.05) m, orientation=(1,0,0,0) wxyz다. generated override의 root transform과 source asset의 feet 높이를 확인한다. joint state를 넣는 것만으로 자율 균형 제어가 생기지 않으므로 아무 policy 없이 자유 낙하하는 동작을 보행 성공으로 판정하지 않는다.

## actuator 설정과 단위 변환

| 관절 그룹 | stiffness (Nm/rad) | damping (Nm·s/rad) | effort limit (Nm) | velocity limit (rad/s) |
|---|---:|---:|---:|---:|
| hip yaw/roll | 150 | 5 | 300 | 100 |
| hip pitch/knee/torso | 200 | 5 | 300 | 100 |
| ankle | 20 | 4 | 100 | 100 |
| shoulder/elbow | 40 | 10 | 300 | 100 |

5. `q_deg = q_rad × 180/π`, `velocity_deg_s = velocity_rad_s × 180/π`다. 반면 degree당 힘을 만드는 USD gain은 **`k_deg = k_rad × π/180`, `d_deg = d_rad × π/180`**이다. 각도와 gain을 같은 방향으로 변환하면 안 된다.
6. 예를 들어 left_hip_yaw는 USD stiffness 약 2.61799, damping 약 0.0872665, maxForce=300, maxVelocity 약 5729.58 deg/s다. `DriveAPI`는 이 값을 저장하고 `PhysxJointAPI`는 max joint velocity를 저장한다. official actuator의 armature/friction이 null인 항목은 로컬 코드에서 임의의 0으로 덮어쓰지 않는다.
7. Play 중 **Window → Script Editor**에서 `inspect_runtime.py`를 실행한다. `SingleArticulation.initialize()` 후 DOF 이름, 관절 위치, `dof_properties`를 읽는다. **runtime API의 값은 rad 기반**으로 돌아오므로 Property의 deg 기반 숫자와 그대로 비교하지 않는다. joint order는 이름 목록과 함께 대조한다.
8. left_hip_yaw의 runtime maxVelocity≈100, maxEffort≈300, stiffness≈150, damping≈5를 확인한다. source와 같은 순서라고 가정하지 말고 `dof_names`로 이름을 매칭한다. asset 비교 기준은 `/Isaac/Samples/Rigging/H1/h1_rigged.usd`다.

## 코드 읽기와 실험

`matching_value`는 정규식이 각 관절에 **정확히 하나** 매칭되는지 검사한다. 누락·중복된 actuator 설정을 자동으로 추측하지 않는다. 각 RevoluteJoint에 `UsdPhysics.DriveAPI`와 `PhysxSchema.JointStateAPI`를 적용하고 local layer를 저장한다. 19개가 아니면 H1 모델/버전 차이를 의심하도록 실패한다.

한 변수 실험: arms stiffness만 40→20으로 바꾼 별도 JSON으로 `--config`를 실행하고 authored USD와 runtime 반환값을 비교한다. policy의 원래 수치와 달라진 것이므로 실제 보행 성능 비교는 별도의 policy 추론 실험이 필요하다. 정규식 매칭 실패는 joint 이름, 초기 자세가 틀리면 rad/deg, gain이 57배쯤 다르면 gain 변환 방향을 확인한다.

검증 범위: Python 문법·CLI, 공식 H1/environment URL 확인, 정규식/단위 입력의 로컬 검토. RTX 로딩, tensor runtime 값, 보행 안정성은 미검증이다.

## 출처

- [Isaac Sim 5.1 Rigging a Legged Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html)
- [Joint configuration](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html#setting-joint-configuration), [Runtime verification](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html#verify-joint-configuration)
- [버전 고정 H1 environment 입력](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Policies/H1_Policies/h1_env.yaml)
