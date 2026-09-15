# 40. 로봇 팔과 그리퍼를 하나의 기구로 조립하기

## 이번에 배우는 것

**UR10e 손목에 Robotiq 2F-140을 연결하고, 고정 관절·articulation·USD variant가 서로 다른 문제를 해결하는지 확인합니다.**

팔 끝에 그리퍼가 보이도록 배치해도 물리적으로 붙은 것은 아닙니다. 손목과 그리퍼 base를 고정 관절로 연결해야 하며, 하나의 articulation으로 다루려면 두 자산에 있던 root도 정리해야 합니다. 이번에는 먼저 완성 샘플을 조사하고 그 구조를 직접 조립한 결과와 비교합니다.

| 파일 또는 기능 | 입력 | 결과 |
|---|---|---|
| `run.py` | 조립된 USD | 관절 연결과 root 목록 보고서 |
| 수동 Fixed Joint 조립 | 팔 USD + 그리퍼 USD | 손목에 고정된 그리퍼 |
| Robot Assembler | 두 로봇과 장착점 | 조립 결과와 선택 가능한 구성 |
| `prepare_xacro.py` | Robotiq XACRO 소스 | 경로를 정리한 별도 작업 복사본 |

**`run.py`는 조립 검사기입니다.** 기본 실행에서는 공식 완성 샘플을 읽고, 직접 만든 USD는 `--asset`으로 지정합니다.

## 1. 완성 샘플의 연결 구조부터 읽기

Isaac Sim 5.1.0, 지원 GPU와 공식 Manipulator 에셋 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/40_robot_setup_import_assemble_manipulator/run.py \
  --output src/40_robot_setup_import_assemble_manipulator/output/reference
```

기본 입력은 `/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd`입니다. 창은 직접 닫을 때까지 유지됩니다. 양수 `--steps`는 앱 갱신 후 종료할 한도이며 자동 물리 실행 횟수가 아닙니다. Headless에서는 생략 시 1200회, `--frames` 지정 시 그 값을 사용하고 `--steps`가 있으면 우선합니다.

### 코드에서 볼 부분

검사기는 `/ur` 아래를 순회하면서 articulation root와 관절 관계를 읽습니다.

```python
roots = [str(prim.GetPath()) for prim in Usd.PrimRange(root)
         if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
```

보고서의 `single_articulation`은 이 목록의 길이가 1인지 계산한 값입니다. `false`를 기록해도 프로그램이 반드시 오류로 종료하지는 않습니다. 따라서 종료 코드만으로 조립 완성을 판단하지 마세요.

### 실행 결과 확인하기

| 출력 파일·항목 | 읽는 방법 |
|---|---|
| `assembly_report.json`의 `asset` | 실제 검사한 입력 파일 |
| `articulation_roots`, `single_articulation` | root가 하나로 정리되었는지 |
| `joints[].body0/body1` | 각 관절이 어떤 두 강체를 연결하는지 |
| `variant_sets` | 루트 prim의 variant 이름과 선택지 |
| `inspection_scene.usda` | 입력 로봇을 참조한 검사 장면 |

손목 연결 관절에서 Body0가 `/ur/wrist_3_link`, Body1이 그리퍼 base 강체인지 찾아보세요. `variant_sets`는 선택지를 읽을 뿐 실제 전환 동작을 시험하지 않습니다.

## 2. 두 자산을 연결하고 자기 결과 검사하기

### 설정에서 볼 부분: 수동 조립

Content Browser에서 다음 두 준비 에셋을 사용하면 ROS 없이 진행할 수 있습니다.

- 팔: `/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur.usd`
- 그리퍼: `/Isaac/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140/robotiq_2f_140.usd`

1. 팔 USD를 열고 **File > Save As**로 새 로컬 작업 파일에 저장합니다.
2. 그리퍼 USD를 `/ur` 아래에 추가하고 prim 이름을 `ee_link`로 정합니다.
3. `/ur/ee_link`의 Translate를 `(1.18425, 0.2907, 0.06085)`, Rotate를 `(-90, 0, -90)`°로 맞춥니다. 손목 끝과 장착면이 만나는지 확인하세요.
4. `/ur/ee_link/root_joint`의 **Articulation Root를 제거**합니다. 팔의 root는 유지합니다.
5. 같은 고정 관절의 **Body0를 `/ur/wrist_3_link`로** 변경하고, 그리퍼 base를 가리키는 Body1은 유지합니다.
6. `/ur`의 IsaacRobotAPI에서 `isaac:physics:robotjoints`와 `isaac:physics:robotLinks`에 `/ur/ee_link`를 추가하여 그리퍼의 로봇 정보를 포함합니다.
7. Play하여 장착이 유지되는지 확인하고 Stop 후 저장합니다.

4번과 5번은 다른 작업입니다. Root 제거는 articulation 구성을 정리하고, Body0 수정은 원래 world 쪽에 연결된 그리퍼를 손목에 연결합니다. 한쪽만 처리하면 “root는 하나지만 그리퍼가 떨어짐” 또는 “붙어 있지만 제어 구조가 나뉨” 같은 결과가 생길 수 있습니다.

### 설정에서 볼 부분: Robot Assembler

같은 팔과 그리퍼를 새 작업 사본에 놓고 **Tools > Robotics > Asset Editor > Robot Assembler**를 엽니다.

1. Base Robot=`/ur`, Attach Point=`wrist_3_link`로 지정합니다.
2. Attach Robot=`/ur/ee_link`, Attach Point=`robotiq_arg2f_base_link`로 지정합니다.
3. Assembly Namespace=`ee_link`로 두고 **Begin Assembling Process**를 누릅니다.
4. 장착 방향을 **Z +90**으로 맞추고 **Assemble and Simulate**로 관찰합니다.
5. **End Simulation And Finish** 후 새 파일에 저장합니다.

수동 조립의 전체 transform과 Assembler의 Z +90은 서로 다른 장착 과정에서 입력하는 값입니다. 같은 작업에 두 보정을 무조건 누적하지 마세요. 조립 후 `/ur`의 `ee_link` variant에서 `None`과 `robotiq_2f_140`을 바꾸어 구성 전환을 확인합니다. Variant는 한 USD 안에 선택 가능한 구성을 표현하는 장치입니다.

### XACRO에서 시작하고 싶다면

준비된 USD 대신 원본 기술 형식을 다루려면 **Ubuntu 24.04의 ROS 2 Jazzy**, xacro, colcon과 초기화된 rosdep이 추가로 필요합니다. [공식 ROS 2 Description 저장소](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description)의 `jazzy` 브랜치로 입력을 준비합니다. 다음은 시스템 ROS를 사용하는 별도 Bash 터미널에서 실행하세요. `~/ur_description_t40_ws`는 새 작업 공간이어야 합니다.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install ros-jazzy-xacro
mkdir -p ~/ur_description_t40_ws/src
git clone --branch jazzy https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git ~/ur_description_t40_ws/src/ur_description
(
  cd ~/ur_description_t40_ws
  rosdep install -i --from-path src --rosdistro jazzy -y
  colcon build
  source install/setup.bash
  ros2 launch ur_description view_ur.launch.py ur_type:=ur10e
)
```

마지막 명령은 설명을 발행하는 노드를 계속 실행합니다. 다른 Jazzy 터미널의 `ros2 node list`에서 `/robot_state_publisher`가 있는지 확인하세요. 이 노드를 켜 둔 상태에서 Isaac Sim의 **ROS 2 Robot Description URDF Importer** 확장을 활성화하고 **File > Import from the ROS 2 URDF Node**를 엽니다. Node에 `robot_state_publisher`를 넣고 Refresh한 뒤 새 로컬 Model 출력 폴더를 선택합니다. 팔 관절을 모두 선택해 Joint Configuration의 Natural Frequency=300을 입력하고 Import하세요.

시스템 ROS 노드와 Isaac Sim은 별도 프로세스입니다. Isaac 측에서 rclpy나 사용자 패키지를 직접 불러오는 구성은 5.1의 [Python 3.11 ROS 환경 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)이 필요합니다. 시스템 Python 패키지를 Isaac Python 경로에 직접 섞지 마세요. 위 작업 공간 빌드와 ROS 발행은 `run.py`나 `prepare_xacro.py`가 대신 수행하지 않습니다.

Robotiq 변환 명령도 `source /opt/ros/jazzy/setup.bash`를 실행한 Bash 터미널에서 진행합니다. UR10e 발행 터미널은 그대로 두고 새 터미널을 사용하세요. Robotiq는 [원본 모델 저장소](https://github.com/ros-industrial-attic/robotiq)의 작업 복사본을 사용합니다. 다음은 저장소 루트에서 시작하는 명령입니다.

```bash
git clone https://github.com/ros-industrial-attic/robotiq.git /tmp/robotiq_source
python3 src/40_robot_setup_import_assemble_manipulator/prepare_xacro.py \
  /tmp/robotiq_source/robotiq_2f_140_gripper_visualization \
  src/40_robot_setup_import_assemble_manipulator/output/robotiq_work
(
  cd src/40_robot_setup_import_assemble_manipulator/output/robotiq_work/urdf
  xacro robotiq_arg2f_140_model.xacro > robotiq_2f_140.urdf
)
```

`prepare_xacro.py`는 복사한 `urdf/*.xacro`의 `$(find ...)`와 `package://...` 경로를 작업 복사본의 절대 경로로 바꿉니다. **XACRO 확장은 마지막 `xacro` 명령이 수행합니다.** 생성 URDF의 mesh 경로가 작업 복사본을 계속 가리키므로 그 폴더를 보존하세요.

Isaac Sim의 **File > Import**로 URDF를 가져올 때 finger_joint Natural Frequency=300, Mimic joint Natural Frequency=2500을 시작점으로 사용합니다. Mimic Reference Joint는 `/robotiq_arg2f_140_model/joints/finger_joint`, Reference Axis는 `rotX`, Damping Ratio는 0.005입니다.

Gearing은 inner finger 두 개가 -1, inner knuckle 두 개와 right outer knuckle이 1입니다. 원문의 USD 각도 범위는 finger_joint 0~40.107°, inner finger -8.021~48.128°, 나머지 mimic 관절 -48.128~8.021°입니다. 생성한 joint의 실제 이름·축·limit를 확인한 뒤 앞의 조립 절차로 이어갑니다.

### 실행 결과 확인하기

자신이 저장한 조립 파일의 절대 경로를 넣어 검사하세요.

```bash
~/isaacsim/python.sh src/40_robot_setup_import_assemble_manipulator/run.py \
  --asset /절대경로/내_ur_gripper.usd --headless --steps 10 \
  --output src/40_robot_setup_import_assemble_manipulator/output/my_assembly
```

`asset`이 자신의 파일인지, root가 하나인지, 손목 고정 관절이 양쪽 강체를 가리키는지 확인합니다. 수동 조립에는 Assembler와 같은 variant가 없어도 됩니다. 검사 장면은 자동 Play하지 않으므로 실제 장착 유지 여부는 GUI에서 따로 관찰하세요.

## 3. 조립에서 확인할 결과 정리

```text
장착 transform → 처음에 어디에 놓이는가
고정 관절      → 움직일 때도 무엇에 붙어 있는가
articulation   → 어떤 관절들을 한 물리 구조로 다루는가
variant        → 어떤 그리퍼 구성을 선택하는가
```

보고서의 root 수 하나만으로 이 모든 조건을 확인할 수는 없습니다. 구조 보고서와 Play 관찰을 함께 읽어야 완성된 조립을 설명할 수 있습니다.

## 4. 간단한 확인 실험

Assembler 결과에서 **`ee_link` variant만 `robotiq_2f_140`에서 `None`으로** 바꿔보세요. 팔의 위치와 관절 설정은 그대로 둡니다.

그리퍼 구성이 사라지는지 관찰하고 다시 원래 선택지로 되돌립니다. 변환값을 지워 숨기는 것과 달리 USD가 선택한 구성을 바꾼다는 점을 Stage에서 확인해 보세요. 이 실험은 해당 variant가 생성된 Assembler 결과에서 진행합니다.

## 실행할 때 막히면

- **그리퍼가 떨어집니다**: `ee_link/root_joint`의 Body0가 손목인지, Body1이 그리퍼 base인지 확인하세요.
- **`single_articulation=false`입니다**: 그리퍼의 Articulation Root가 남았는지 조사하세요. 검사기는 이를 자동으로 고치지 않습니다.
- **모델이나 mesh를 찾지 못합니다**: 기본 에셋 접근과 생성 URDF의 절대 경로를 확인하세요. XACRO 작업 복사본을 옮기면 참조가 끊길 수 있습니다.
- **공식 샘플만 계속 검사합니다**: 직접 만든 파일은 `--asset`으로 지정해야 합니다. `--stage` 옵션은 이 실행기에 없습니다.
- **출력 폴더 오류가 납니다**: `--output`에는 새 경로를 사용하세요. `inspection_scene.usda`는 검사 결과이며 원래 조립 작업 파일도 따로 보존합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 6: Setup a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_import_assemble_manipulator.html)에 대응합니다. 준비 USD를 이용하는 조립 경로와 선택적인 ROS/XACRO 가져오기 경로를 제공합니다.

로컬 코드는 경로 정리와 조립 구조 검사를 수행합니다. ROS 빌드, URDF import, 수동 조립, Assembler 전환의 실행 검증 상태는 `tutorial.json`에서 `not_run`입니다. 보고서 생성과 실제 기구 동작은 구분하여 확인하세요.
