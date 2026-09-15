# 58. 새 Manipulator에 RMPflow 설정하기: Cobotta Pro 900

권장 학습 순서 **58** · 로봇 제어와 동작 계획 · 출처 ID `t140`

기존 Franka용 template을 6축 Cobotta에 맞추고, 그리퍼 중심 frame을 URDF에 추가하고, self-collision 근사 모델을 개선합니다. 이 패키지는 **원문의 native Lula Test Widget 실습**과 실제 URDF/YAML 생성 도구를 제공합니다. 완성 robot USD를 대체하는 간이 모델은 만들지 않습니다.

## 준비

Isaac Sim **5.1.0**, GUI 화면, 지원 GPU/드라이버가 필요합니다. [공식 Cobotta_Pro_900_Assets.zip](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/43f1f07841f3ef71cc54f320218ced44/Cobotta_Pro_900_Assets.zip)을 이 패키지의 `input/` 아래 풀어 둡니다. 실제 5.1 다운로드 zip에는 `robot_description.yaml`, Cobotta URDF, `rmpflow_configs/template_rmpflow_config.yaml`이 들어 있습니다. 원문 본문은 USD도 제공한다고 설명하지만 현재 다운로드 archive에는 USD가 없으므로, **5.1 Assets의 `Isaac/Robots/Denso/CobottaPro900/cobotta_pro_900.usd`를 별도로 사용합니다.** Content Browser의 해당 경로에서 로드하며 이 USD의 mesh/재질 참조도 접근 가능해야 합니다. 원본을 보존하며 출력 폴더를 따로 만듭니다. URDF가 참조하는 mesh는 원래 자산의 상대 구조를 유지합니다. 이 패키지 이외의 로컬 학습 모듈은 필요 없습니다.

이 패키지 폴더에서 다음을 실행합니다. zip 안의 최상위 폴더 이름에 따라 `INPUT`을 실제 압축 해제 위치로 지정하고 `--urdf`에 원본 URDF 파일명을 선택합니다. `find` 대신 파일 관리자에서 URDF 이름을 확인해도 됩니다. Python 도구는 Isaac Sim에 포함된 PyYAML을 사용합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
INPUT="$PWD/input/Cobotta_Pro_900_Assets"
python3 prepare_config.py --help
"$ISAAC_SIM_ROOT/python.sh" prepare_config.py   --template "$INPUT/rmpflow_configs/template_rmpflow_config.yaml"   --urdf "$INPUT/cobotta_pro_900.urdf"   --descriptor "$INPUT/robot_description.yaml"   --output "$PWD/output/basic"
"$ISAAC_SIM_ROOT/python.sh" prepare_config.py   --template "$INPUT/rmpflow_configs/template_rmpflow_config.yaml"   --urdf "$INPUT/cobotta_pro_900.urdf"   --descriptor "$INPUT/robot_description.yaml"   --output "$PWD/output/conservative" --conservative
"$ISAAC_SIM_ROOT/isaac-sim.sh"
```

도구는 cspace 길이 6과 필요한 gripper link들을 확인하고 기존 output 경로는 거부합니다. URDF에 이미 gripper_center가 있으면 중복 생성하지 않고 오류로 알려 줍니다. 생성된 URDF는 Lula의 kinematics 입력에 쓰며 시각 mesh 재수입용 파일로 간주하지 않습니다. Lula는 URDF의 질량/mesh 대신 link/joint 구조와 관절 한계를 사용합니다.

## 단계별 native 실습

1. 새 Stage를 열고 Content Browser의 5.1 Assets에서 `Isaac/Robots/Denso/CobottaPro900/cobotta_pro_900.usd`를 Stage로 드래그합니다. Stage에서 articulation root가 있는 로봇을 확인합니다. USD는 실제 강체/관절/drive를 정의하며 URDF는 Lula의 운동학 정의입니다.
2. `Window > Extensions`에서 **Lula Test Widget**을 검색해 활성화하고 `Tools > Robotics > Lula Test Widget`을 엽니다.
3. Play를 누른 뒤 위젯의 **Select Articulation**에서 Stage의 Cobotta articulation을 선택합니다. 기본 비교는 zip의 robot_description, 원본 URDF와 template YAML을 살펴보는 것부터 시작합니다. template의 joint_limit_buffers 7개는 Cobotta cspace 6개와 맞지 않으므로 실행 설정에는 생성된 `output/basic` 파일을 사용합니다.
4. **Robot Description YAML**에 `output/basic/robot_description.yaml`, **Robot URDF**에 `output/basic/cobotta_gripper_frame.urdf`를 선택하고 **Load Selected Config > Load**를 누릅니다. **Select End Effector Frame**은 **gripper_center**로 지정합니다. RmpFlow 패널을 펼쳐 **RmpFlow Config YAML**에 `output/basic/rmpflow.yaml`을 선택합니다. 이 패널의 **Follow Target**을 누르고 target을 gripper 앞쪽의 도달 가능한 위치로 옮깁니다.
5. 최소 구성의 body cylinder는 원점에서 z=0.333 m까지 반지름 0.05 m인 capsule이며 collision controller는 right_inner_finger에 있습니다. target을 base 주변으로 옮겨 어떤 self-collision이 여전히 가능한지 관찰합니다.
6. 테스트를 멈추고 `output/conservative`의 동일 세 파일로 바꿉니다. base capsule 반지름은 0.08 m, 두 번째 링크를 넓게 근사하는 구의 반지름은 0.16 m입니다. J5/J6/양쪽 finger와 knuckle에 작은 sphere를 두어 충돌 근사를 넓힙니다. 같은 target 이동에서 덜 접근하지만 움직일 수 있는 공간도 줄어드는지 확인합니다.
7. gripper_center 대신 **right_inner_finger**를 end-effector로 선택하고 같은 target을 따라가게 합니다. 손가락 frame과 실제 집게 중심이 서로 다른 지점을 추종한다는 차이를 확인한 뒤 gripper_center로 되돌립니다.
8. 생성된 RMPflow YAML에서 joint_velocity_cap_rmp의 max_velocity=1.0 rad/s, velocity_damping_region=0.3 rad/s를 확인합니다. URDF의 1 rad/s 제한에 맞춘 값입니다. 제공 USD의 drive gain도 확인합니다. 원문은 이 설정에서 P=10000, D=10000인 자산을 사용하며, D=1000으로 남기면 진동이 생겼음을 설명합니다. 이 값을 모든 로봇의 보편적인 gain으로 복사하지 않습니다.

## 새 frame을 만드는 계산

기존 gripper의 부모는 `onrobot_rg6_base_link`입니다. 코드가 새 `gripper_center` link와 fixed joint `gripper_center_joint`를 만들고 `origin xyz="0 0 0.24" rpy="0 0 0"`를 추가합니다. 0.24 m는 finger 끝 쪽에 둔 중심 frame의 offset입니다. fixed joint이므로 새로운 제어 DOF는 생기지 않습니다. 이 변경은 그리퍼 위치를 보고 계산하는 Lula URDF에 필요하며 USD에 같은 이름의 prim이 반드시 존재해야 한다는 뜻은 아닙니다.

## 설정 파일을 읽는 순서

`robot_description.yaml`의 cspace는 제어할 관절 이름/순서와 default 자세, collision sphere를 정의합니다. `joint_limit_buffers=[0.01]*6`은 각 관절의 실제 limit에서 0.01 rad 안쪽으로 제한을 둡니다. prismatic joint라면 같은 숫자의 단위는 m입니다.

`body_cylinders`는 base 좌표계의 고정 capsule 근사이고 `body_collision_controllers`는 지정 URDF frame에 붙은 sphere입니다. 둘은 gripper와 base 간 self-collision을 줄이는 제한된 기능입니다. RMPflow가 모든 link 쌍의 mesh self-collision을 자동 검사한다고 해석하지 않습니다. 지나치게 큰 capsule은 정상 작업 자세도 배제할 수 있습니다.

## 관찰 기준과 한 변수 실험

생성된 두 출력 폴더에 URDF/YAML 세 개씩 있고 gripper_center frame이 위젯 목록에 보여야 합니다. basic과 conservative 설정에서 같은 target을 이동하여 접근 가능한 공간과 self-collision 차이를 비교합니다. 다음 실험은 conservative의 `second_link.radius`만 0.16에서 0.14로 낮추는 것입니다. 여유 공간이 늘어나는 만큼 충돌도 다시 확인합니다. 원문 본문의 0.12 언급과 code block의 0.16이 다르며 이 패키지는 code block의 구성을 사용합니다.

## 문제 해결과 검증 범위

frame을 못 찾으면 잘못된 URDF를 선택했는지 확인합니다. cspace mismatch는 6개 robot joints와 buffer 길이를 맞춥니다. mesh가 안 보이는 문제는 USD의 상대 asset 참조를 확인하고 Lula config 오류와 분리합니다. 위젯 설정을 바꾼 뒤 재시작/리셋하여 이전 controller와 동시에 로봇을 구동하지 않습니다.

이 패키지는 config 생성과 native 실습 절차를 구현했습니다. 실제 Cobotta 자산 로딩·위젯 조작·충돌/추종은 `verification`이 not_run이면 미검증입니다. 문법 검사만으로 물리 동작을 성공했다고 판단하지 않습니다.

## 출처

- [Isaac Sim 5.1.0 — Configuring RMPflow for a New Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)
- [Template와 Cobotta 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html#modifying-the-template-for-the-cobotta-pro-900)
- [End Effector Frame](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html#creating-an-end-effector-frame)
