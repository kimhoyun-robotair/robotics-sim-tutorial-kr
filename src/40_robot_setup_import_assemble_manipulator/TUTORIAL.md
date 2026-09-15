# 40. UR10e와 Robotiq 2F-140을 하나의 로봇으로 조립하기

권장 학습 순서 **40** · 로봇 자산 가져오기와 제작 · 출처 ID `t124`

공식 인덱스 **t124** · Isaac Sim **5.1.0**

## 이 실습의 의도

UR10e 손목과 Robotiq 그리퍼를 fixed joint로 연결하고 articulation root를 하나로 정리하여, 두 자산을 하나의 제어 가능한 로봇으로 조립하는 과정을 배웁니다. 수동 연결과 Robot Assembler의 variant 구성을 각각 GUI에서 수행하고 결과의 구조를 비교합니다. 기본 `run.py`는 이미 조립된 공식 샘플을 열어 구조를 기록하는 검사기이며, 직접 만든 로봇은 `--asset`으로 지정해야 검사 대상이 됩니다. `prepare_xacro.py`는 선택한 Robotiq 소스의 작업 복사본과 경로만 준비하며 XACRO 확장·URDF import·조립은 해당 절차에서 따로 수행합니다.

## 실행 후 확인할 것

- **검사 대상:** `assembly_report.json`의 `asset`이 공식 `ur_gripper.usd`인지 자신의 조립 결과인지 먼저 확인합니다. 기본 샘플이 보이는 것만으로 사용자가 만든 조립 결과가 검사된 것은 아닙니다.
- **articulation 통합:** 보고서의 `articulation_roots`가 하나이고 `single_articulation=true`인지 확인합니다. 이 값은 기록만 되므로 `false`여도 실행 종료 코드가 자동으로 오류가 되지는 않습니다.
- **손목 연결:** `joints`에서 그리퍼 고정 joint의 `body0`가 `/ur/wrist_3_link`, `body1`이 그리퍼 base 강체를 가리키는지 확인합니다. GUI에서 Play하여 장착 위치를 유지하는지도 봅니다. 이 검사기는 물리를 자동 재생하거나 팔 목표를 보내지 않습니다.
- **조립 방식별 결과:** Robot Assembler로 만든 경우 `variant_sets`의 `ee_link` 선택지와 GUI의 `None`↔`robotiq_2f_140` 전환을 확인합니다. 보고서는 선택지 이름을 기록할 뿐 전환을 실행하지 않으며, 수동 Fixed Joint 조립에는 같은 variant가 없어도 됩니다.
- **보존할 파일:** `inspection_scene.usda`는 검사 장면이고 실제 조립 편집은 작업한 로컬 USD에 저장합니다. ROS/XACRO 경로를 택했다면 생성 URDF가 `robotiq_work`의 mesh를 계속 참조하는지도 확인합니다.

## 준비

Isaac Sim 5.1.0, NVIDIA GPU와 정상 드라이버, 5.1 asset root가 필요합니다. **ROS를 설치하지 않아도** Content Browser에서 다음 준비된 공식 에셋으로 조립 실습 전체를 진행할 수 있습니다. 경로는 대소문자를 구별합니다.

- 팔: `Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur.usd`
- 그리퍼: `Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140/robotiq_2f_140.usd`
- 수동 조립 참고: `.../ur10e/ur/ur_gripper_manual.usd`
- Assembler 조립 참고: `.../ur10e/ur/ur_gripper.usd`

원본 설치 에셋을 덮어쓰지 않도록 File > Save As로 이 패키지 `output/` 아래 새 파일에 작업합니다. 프로그램의 저장 파일은 원본 USD reference를 유지하므로 외부 asset root의 접근은 계속 필요합니다.

## 1. Linux에서 URDF로 시작하는 선택 경로

처음부터 import하려면 Linux, 시스템 ROS 2 Humble 또는 Jazzy, `xacro`, `colcon`, `rosdep`, `robot_state_publisher`, `rqt_graph`가 필요합니다. Isaac 내부 rclpy는 Python 3.11용입니다. 시스템 ROS의 Python 모듈을 Isaac의 Python 경로에 직접 섞지 않습니다. ROS 노드 발행을 시스템 ROS 프로세스에서 하고 Isaac은 호환되는 bridge 환경으로 실행할 수 있습니다.

사용할 ROS workspace를 `$UR_WORKSPACE`에 지정한 뒤 다음을 실행합니다. 아래는 Humble이며 Jazzy라면 source 경로와 git branch를 모두 jazzy로 바꿉니다. 설치 명령은 사용자의 ROS 환경에 실행하는 절차입니다.

```bash
source /opt/ros/humble/setup.bash
sudo apt install ros-humble-xacro
UR_WORKSPACE="$HOME/ur_description_ws"
mkdir -p "$UR_WORKSPACE/src"
git clone --branch humble https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git "$UR_WORKSPACE/src/ur_description"
cd "$UR_WORKSPACE"
rosdep install -i --from-path src --rosdistro humble -y
colcon build
source install/setup.bash
ros2 launch ur_description view_ur.launch.py ur_type:=ur10e
```

다른 같은 ROS 환경 터미널에서 `rqt_graph`를 실행하고 robot_state_publisher가 있는지 확인합니다. Isaac의 Window > Extensions에서 **ROS 2 Robot Description URDF Importer**를 Enable합니다. 검색되지 않으면 `@feature` 필터를 지웁니다. File > Import from the ROS 2 URDF Node에서 Node=`robot_state_publisher`, Refresh, 새 로컬 Model 출력 폴더를 선택합니다. Joint Configuration을 **Natural Frequency**, 모든 팔 관절을 **300**으로 설정하고 Import합니다.

Isaac용 Python 3.11 ROS workspace를 사용하는 경로는 Isaac 공식 `IsaacSim-ros_workspaces`의 `build_ros.sh`로 ROS와 ur_description을 함께 빌드하고 `build_ws/humble/humble_ws/install/local_setup.bash`, `build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash`를 source한 뒤 Isaac을 시작합니다. 이 패키지가 ROS 빌드 자체를 포함하거나 실행하지는 않습니다. 이 방식이 필요할 때의 전체 준비 출처는 아래 Python 3.11 ROS 가이드입니다.

## 2. Robotiq XACRO를 URDF로 바꾸기

```bash
git clone https://github.com/ros-industrial-attic/robotiq.git /tmp/robotiq_source
# 이 패키지 폴더에서 실행
python3 prepare_xacro.py /tmp/robotiq_source/robotiq_2f_140_gripper_visualization output/robotiq_work
cd output/robotiq_work/urdf
xacro robotiq_arg2f_140_model.xacro > robotiq_2f_140.urdf
```

ROS1의 `$(find robotiq_2f_140_gripper_visualization)`와 `package://...`를 복사본의 절대 경로로 바꿉니다. 원본 clone은 수정하지 않습니다. 출력 URDF가 이 복사본의 mesh를 참조하므로 `robotiq_work`를 유지합니다. 공식 repo는 ROS1의 보관된 모델 저장소이며 ROS1 노드를 실행할 필요는 없습니다.

Isaac File > New → File > Import → `robotiq_2f_140.urdf`를 선택합니다. USD 출력은 새 로컬 폴더로 지정합니다. **finger_joint Natural Frequency=300**, **Mimic joint Natural Frequency=2500**으로 설정합니다. Mimic 기준 joint는 `/robotiq_arg2f_140_model/joints/finger_joint`, axis는 rotX, damping ratio는 **0.005**입니다.

| 관절/종류 | lower–upper (USD degree) | gearing |
|---|---|---|
| finger_joint | 0–40.107 | 직접 drive |
| left/right inner finger | -8.021–48.128 | -1 |
| left inner knuckle, right inner/outer knuckle | -48.128–8.021 | 1 |

finger_joint의 참고 drive 값은 stiffness=37.51957, damping=0.00125, max force=1000입니다. 다른 5개 관절은 mimic으로 연동합니다. USD 편집기의 degree 값과 Python articulation API의 radian 값을 혼동하지 않습니다.

## 3. 수동 Fixed Joint 조립

1. 준비한 `ur.usd`를 열고 Save As로 작업 사본을 만듭니다. 그리퍼 USD를 Stage의 `/ur` 아래로 끌어놓고 Prim 이름을 `ee_link`로 바꿉니다.
2. `/ur/ee_link` Transform을 Translate=(1.18425,0.2907,0.06085), Rotate=(-90,0,-90) degree로 설정합니다. 팔 wrist_3_link 끝과 그리퍼 장착면이 겹치는지 봅니다.
3. `/ur/ee_link/root_joint`의 Physics Articulation Root를 제거합니다. 전체 로봇에는 하나의 articulation root만 있어야 합니다.
4. 같은 root_joint의 Body0을 `/ur/wrist_3_link`로 설정합니다. 원래 그리퍼 base를 가리키는 Body1은 유지합니다. Fixed joint가 손목과 그리퍼를 묶습니다.
5. `/ur`의 IsaacRobotAPI에서 `isaac:physics:robotjoints`와 `isaac:physics:robotLinks`에 `/ur/ee_link`를 추가해 그리퍼의 로봇 스키마를 포함합니다.
6. Play로 팔과 그리퍼가 하나로 붙어 있는지 확인하고 Stop 후 새 파일에 저장합니다.

## 4. Robot Assembler와 variant로 조립

1. 새 팔 사본에서 다시 시작해 그리퍼를 `/ur/ee_link`에 넣습니다. Tools > Robotics > Asset Editor > Robot Assembler를 엽니다.
2. Base Robot=`/ur`, Attach Point=`wrist_3_link`; Attach Robot=`/ur/ee_link`, Attach Point=`robotiq_arg2f_base_link`를 지정합니다.
3. Assembly Namespace=`ee_link`, Begin Assembling Process를 누릅니다. Z +90으로 그리퍼 장착 방향을 맞춥니다.
4. Assemble and Simulate로 동작을 확인한 뒤 End Simulation And Finish를 누릅니다.
5. `/ur`의 Variants에서 `ee_link=None`과 `ee_link=robotiq_2f_140`을 바꿔 그리퍼가 제거/추가되는지 봅니다. 결과를 새 로컬 파일에 저장합니다.

variant는 다른 로봇을 매번 복사하는 대신 같은 USD의 선택 가능한 구성을 표현합니다. payload는 선택한 그리퍼 데이터를 필요할 때 로딩하는 합성 요소입니다. articulation은 joint로 연결된 강체 집합이며 로봇 조립 후 root가 두 개 남으면 한 articulation으로 제어할 수 없습니다.

## 5. 이 폴더의 실제 USD 검사

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --asset /절대경로/내_ur_gripper.usd --headless --frames 10
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 1200회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

`assembly_report.json`에는 articulation root 목록과 `single_articulation`, joint의 실제 body0/body1 관계, variant 선택지 이름을 기록합니다. 손목 연결이 올바른지는 보고서를 보고 직접 대조하며, root 개수나 variant 전환 성공을 자동 합격/불합격 판정하지 않습니다. GUI 준비기는 물리를 자동 시작하지 않습니다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 직접 확인할 수 있습니다. 기본 출력은 `output/<고유번호>/`이며 `--output`은 존재하지 않는 새 경로만 허용합니다.

성공은 모델이 보이는 것뿐 아니라 root 하나, 손목–그리퍼 fixed joint와 실제 장착 유지로 판정합니다. Assembler 경로에서는 variant 전환 후 구성 변화도 확인합니다. 한 변수 실험으로 Assembler의 Z +90만 생략해 장착 방향이 어떻게 달라지는지 비교합니다. gripper가 떨어지면 root_joint의 Body0/Body1과 articulation root 수를 확인합니다. Import가 모델을 못 찾으면 작업 복사본의 mesh 경로와 ROS node 이름을 먼저 확인합니다.
## 버전 고정 출처

- [NVIDIA Isaac Sim 5.1.0 — Tutorial 6: Setup a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_import_assemble_manipulator.html)
- [공식 Python 3.11 ROS workspace 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Universal Robots ROS 2 Description](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description)
- [Robotiq 원본 모델](https://github.com/ros-industrial-attic/robotiq)

한국어 절차는 새로 작성했습니다. 원문 GUI 기능과 이 폴더의 준비/검사/실행 코드를 구별해 설명합니다. 실제 runtime 검증 범위는 tutorial.json의 verification 기록을 확인합니다.
