# 30. URDF의 링크와 관절을 움직이는 USD 로봇으로 바꾸기

## 이번에 배우는 것

**작은 팔의 URDF를 가져와 관절에 위치 목표를 보내고, 파일 변환과 실제 물리 응답을 나눠 확인합니다.**

URDF는 로봇의 링크와 관절을 XML로 설명하는 형식입니다. 같은 링크 안에도 화면에 보일 형상, 충돌에 사용할 형상, 질량과 관성이 따로 들어갑니다. 이번에는 외부 mesh가 없는 `arm.urdf`로 각 항목을 읽고, 가져온 USD에서 어떤 역할을 하는지 살펴봅니다.

| URDF 요소 | 담고 있는 정보 | 이 실습의 예 |
|---|---|---|
| `visual` | 화면에 표시할 모양 | 바닥의 상자와 가느다란 팔 |
| `collision` | 접촉을 계산할 모양 | 표시 형상과 같은 크기의 box |
| `inertial` | 질량·질량 중심·관성 | base 1 kg, arm 0.3 kg |
| `joint` | 링크 연결과 허용 운동 | Y축으로 회전하는 `shoulder` |

모양이 화면에 보이는 것만으로 관절이 제어 가능한 상태라고 판단할 수는 없습니다. 변환 후 관절 이름을 조회하고 실제 위치도 읽어 봅니다.

## 1. 기본 팔 가져오기와 위치 제어

Isaac Sim 5.1과 지원 RTX GPU가 필요합니다. 실행기는 `isaacsim.asset.importer.urdf` 확장을 활성화합니다. 기본 팔은 이 폴더의 파일만 사용하며 ROS 설치가 필요하지 않습니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 실제 설치 경로로 바꾸세요.

```bash
~/isaacsim/python.sh src/30_importers_import_urdf/run.py --steps 360 --output src/30_importers_import_urdf/output/arm_a
```

새 출력 폴더를 사용해야 합니다. `arm_a`가 있으면 다른 이름을 지정하세요. 기본 `--output`은 이 튜토리얼의 `output/` 자체이므로, 반복 실습에는 위처럼 실행별 경로를 지정하는 편이 구분하기 쉽습니다.

가져온 base는 고정되고 shoulder에는 0.5 rad 위치 목표를 계속 보냅니다. 360단계 후 결과를 기록하고 종료합니다. `--steps`를 생략하거나 GUI에서 0으로 지정하면 창을 닫을 때까지 제어를 계속합니다. Headless는 생략 시 360단계이며 0단계는 허용하지 않습니다.

### 코드에서 볼 부분

`arm.urdf`의 관절은 아래와 같습니다. 자식 팔은 베이스 기준 z=0.12 m에 붙고 Y축을 중심으로 회전합니다.

```xml
<joint name="shoulder" type="revolute">
  <parent link="base"/><child link="arm"/><origin xyz="0 0 0.12"/><axis xyz="0 1 0"/>
  <limit lower="-1.2" upper="1.2" effort="20" velocity="2"/><dynamics damping="0.1" friction="0"/>
</joint>
```

URDF의 revolute 관절 범위는 rad입니다. 0.5 rad 목표는 약 28.6도로 이 범위 안에 있습니다. USD Property의 각도 표시와 숫자가 다르게 보이면 먼저 단위를 확인하세요.

`run.py`는 `URDFParseFile`로 구조를 읽은 뒤 parsed joint의 drive strength=20, damping=1을 지정하고 `URDFImportRobot`으로 현재 Stage에 가져옵니다. `fix_base=True`는 바닥 링크를 고정하며, `distance_scale=1.0`은 m 단위 입력을 유지합니다. 자체 충돌은 꺼 두고 입력에 질량·관성 정보가 있는 작은 모델을 사용합니다.

그 뒤 `SingleArticulation`으로 로봇에 접근해 다음 위치 목표를 보냅니다.

```python
robot.apply_action(ArticulationAction(joint_positions=np.array([0.5])))
```

배열 원소가 하나인 이유는 기본 팔의 움직이는 관절이 shoulder 하나이기 때문입니다.

### 실행 결과 확인하기

| 출력 | 생성 시점과 읽는 방법 |
|---|---|
| `imported.usda` | 제어 루프 전에 저장한 변환 장면, 링크·관절·물리 속성 검사 |
| `report.json`의 `prim_path` | 실제 가져온 로봇 루트, 기본 입력은 `/tutorial_arm` |
| `joint_names` | 제어 가능한 관절 이름, 기본은 `shoulder` |
| `joint_positions` | 실행이 끝날 때 측정한 관절 위치, rad |

마지막 위치가 0.5 rad 근처로 접근했는지 확인하세요. 유한한 drive와 중력 때문에 정확히 0.5라는 숫자가 나와야만 성공인 것은 아닙니다. 저장된 USD는 마지막 관절 자세를 저장한 파일이 아니라 **변환한 구조**를 검사하는 자료입니다.

## 2. Python·GUI·ROS로 가져오는 방식 비교하기

기본 팔을 오래 살펴보려면 새 출력 경로로 단계 수 없이 실행하세요. Stage의 `/tutorial_arm` 아래에서 base·arm·shoulder를 찾아 Property를 확인합니다. Viewport의 **Show by type > Physics > Colliders > All** 표시를 켜면 보이는 표면과 충돌 형상을 비교할 수 있습니다.

arm의 visual·collision 중심은 링크 기준 z=0.2 m이고 길이는 0.4 m입니다. 따라서 관절 원점에서 위로 뻗는 모양이 됩니다. 링크 원점, 형상의 중심, 질량 중심을 같은 위치라고 가정하지 않고 각각의 `origin`을 읽어 보세요.

### 코드에서 볼 부분

설치된 Franka URDF도 같은 importer로 가져올 수 있습니다.

```bash
~/isaacsim/python.sh src/30_importers_import_urdf/run.py --franka --output src/30_importers_import_urdf/output/franka_a
```

이 모드는 importer 확장의 `data/urdf/robots/franka_description/robots/panda_arm_hand.urdf`를 사용합니다. 내장 mesh와 manipulator·RMPflow 확장도 필요합니다. 가져온 로봇 경로를 `FollowTarget`에 전달하고, `RMPFlowController`가 목표 위치·자세를 관절 명령으로 바꿉니다. 기본 팔의 `[0.5]` 명령을 Franka에 그대로 보내지 않습니다.

### 실행 결과 확인하기

Franka GUI의 목표 물체를 움직여 손끝의 반응을 관찰하세요. 실행을 마친 뒤 `report.json`에서 source와 관절 이름이 Franka로 바뀌었는지 확인합니다. 여기에는 손끝 추종 오차나 성공 boolean이 저장되지 않으므로, 보고서가 생긴 것만으로 목표 추종 정확도를 판정하지 마세요.

### Franka URDF를 GUI에서 직접 가져오기

자동 import와 같은 파일을 수동으로 선택해 볼 수 있습니다. 앞 실행을 종료하고 `~/isaacsim/isaac-sim.sh`로 새 창을 여세요.

1. **Window > Extensions**에서 `isaacsim.asset.importer.urdf`를 켜고 AUTOLOAD 옆 폴더 아이콘으로 설치 위치를 엽니다.
2. `data/urdf/robots/franka_description/robots/panda_arm_hand.urdf`를 찾아 **File > Import**에서 선택합니다.
3. USD Output은 자신의 새 `output/gui_franka` 폴더로 지정합니다. 설치 확장 폴더에 결과를 쓰지 마세요.
4. **Static Base**를 선택하고 Default Density는 비워 둡니다. Colliders의 **Allow Self-Collision**을 켜고 Import합니다. 이 자체 충돌 설정은 `run.py`의 `self_collision=False`와 다릅니다.
5. Stage에서 링크·관절·Collider를 확인합니다. Joint 설정의 Natural Frequency를 조정할 때는 같은 목표와 재생 조건에서 진동을 비교하세요.

모델별 drive 구성은 **Window > Examples > Robotics Examples > Import Robots**의 Franka·Nova Carter·Kaya·UR10 예제에서도 볼 수 있습니다. 예제를 하나씩 열어 **Load Robot → Configure Drives → Play → Move to Pose**를 실행하고 Open Source Code로 설정을 확인하세요. 이동 로봇의 base는 Moveable, 구동 바퀴는 Velocity, 조향 관절은 Position 방식이 필요할 수 있습니다. 직접 토크 정책으로 제어하는 다리 관절은 drive를 None으로 두고 gain을 0으로 만드는 등 제어 방식에 맞는 설정이 필요합니다. 한 로봇의 gain을 다른 로봇에 그대로 적용하지 않습니다.

### ROS 2 노드의 로봇 설명 가져오기

이 선택 경로는 **Ubuntu 24.04와 ROS 2 Jazzy의 Bash 터미널**을 기준으로 합니다. ROS 노드가 XACRO를 확장해 `robot_description`을 제공하고 Isaac Sim이 그 설명을 받아 가져옵니다. 기본 한 축 팔 실습에는 ROS가 필요하지 않습니다.

Jazzy와 ROS 패키지 저장소가 준비된 환경에서 터미널 1에 다음을 실행하세요. `ur_description`을 이미 별도 workspace에 빌드했다면 설치 명령 대신 해당 workspace의 `install/setup.bash`를 source합니다.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install ros-jazzy-ur-description
export ROS_DOMAIN_ID=0
UR_DESCRIPTION_SHARE="$(ros2 pkg prefix --share ur_description)"
if [ -f "$UR_DESCRIPTION_SHARE/launch/view_ur.launch.py" ]; then
  UR_VIEW_LAUNCH=view_ur.launch.py
else
  UR_VIEW_LAUNCH=view_ur.launch.xml
fi
ros2 launch ur_description "$UR_VIEW_LAUNCH" ur_type:=ur10e
```

설치한 `ur_description` 버전에 따라 launch 파일이 `.py` 또는 `.xml`일 수 있어 실제 파일을 확인합니다. 실행한 터미널은 publisher를 계속 유지합니다. 터미널 2에서는 같은 ROS 환경에서 노드를 확인하세요.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
ros2 node list
```

`/robot_state_publisher`를 확인한 뒤 **시스템 ROS를 source하지 않은 새 터미널 3**에서 Isaac Sim을 시작합니다.

```bash
export ROS_DOMAIN_ID=0
export AMENT_PREFIX_PATH="/opt/ros/jazzy${AMENT_PREFIX_PATH:+:$AMENT_PREFIX_PATH}"
~/isaacsim/isaac-sim.sh
```

Ubuntu 24.04에서 다른 ROS 라이브러리를 source하지 않으면 Isaac Sim은 내부 Jazzy 라이브러리를 사용합니다. Isaac Python 3.11과 시스템 ROS의 Python 모듈을 섞지 않기 위한 구분입니다. `AMENT_PREFIX_PATH`는 importer가 `package://ur_description/...`의 mesh를 찾을 경로이며 Python 모듈을 추가하는 `PYTHONPATH`와 다릅니다. 별도 workspace의 모델을 사용하면 그 workspace의 install prefix도 여기에 포함해야 합니다. 환경 설정의 근거는 [Isaac Sim 5.1 ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)입니다.

1. Isaac Sim의 Extensions에서 `isaacsim.ros2.bridge`, `isaacsim.ros2.urdf`를 켭니다.
2. **File > Import from ROS2 URDF Node**를 엽니다. 공식 문서에서는 ROS 2를 띄어 표기하기도 합니다.
3. 터미널 2에서 확인한 node 이름을 넣고 Refresh한 뒤 새 USD 출력 폴더를 지정해 Import합니다.
4. 생성된 UR10e의 링크와 joint를 확인합니다. 노드가 발견되었다는 사실과 mesh까지 읽었다는 사실을 나누어 보세요.
5. 다른 모델을 비교하려면 터미널 1에서 Ctrl+C로 publisher를 끝내고 같은 명령의 `ur_type`만 `ur3`으로 바꿉니다. importer에서 Refresh하고 다른 출력 폴더에 가져옵니다.

노드가 없으면 양쪽 `ROS_DOMAIN_ID`와 bridge 상태를 확인하고, `package` 경로 오류라면 Isaac 실행 환경에서 `ur_description`의 share 디렉터리를 찾을 수 있는지 확인하세요. `.bashrc`가 시스템 ROS를 자동 source한다면 Isaac용 터미널에는 그 설정이 적용되지 않도록 준비해야 합니다.

## 3. URDF에서 물리 응답까지 정리

```text
URDF: 모양 + 접촉 형상 + 질량·관성 + 관절
    → 파싱한 모델의 drive 설정
    → USD 링크·관절 생성
    → World 초기화와 Articulation 연결
    → 관절 목표 적용 → 물리 진행 → 실제 위치 조회
```

변환은 로봇 설명을 USD 구조로 옮깁니다. 제어는 그 구조에 명령을 적용합니다. 두 과정을 이어서 확인해야 “파일이 열렸다”와 “로봇이 의도한 방식으로 반응한다”를 구분할 수 있습니다.

## 4. 간단한 확인 실험

`arm.urdf`를 복사한 뒤 arm 링크의 **visual box x 크기만** 0.04에서 0.08 m로 바꿔 보세요. collision과 inertial은 그대로 둡니다.

```bash
cp src/30_importers_import_urdf/arm.urdf /tmp/tutorial30_visual_wide.urdf
```

편집기에서 `/tmp/tutorial30_visual_wide.urdf`의 arm 아래 visual geometry를 바꾼 뒤 실행하세요.

```bash
~/isaacsim/python.sh src/30_importers_import_urdf/run.py --urdf /tmp/tutorial30_visual_wide.urdf --steps 360 --output src/30_importers_import_urdf/output/visual_wide
```

팔이 두꺼워 보이지만 collider 윤곽은 원래 폭이어야 합니다. 외관만 바뀐 것이므로 질량·관성도 자동으로 두 배가 되지 않습니다. 화면의 표면과 충돌 표시를 함께 보며 어떤 입력을 바꿨는지 확인하세요.

## 실행할 때 막히면

- **출력 폴더가 이미 있다는 오류**: 기본 출력은 고정 경로입니다. 새 `--output`을 지정하세요.
- **다른 URDF에서 관절 명령 크기 오류**: 일반 `--urdf` 경로의 루프는 움직이는 관절 하나를 전제로 `[0.5]`를 보냅니다. 여러 관절 로봇용 범용 제어기는 아닙니다.
- **mesh나 재질을 못 찾음**: URDF 기준 상대경로와 참조된 파일을 함께 준비하세요. XML 파일만 복사하면 종속 자산이 빠질 수 있습니다.
- **팔은 보이지만 움직이지 않음**: 가져온 joint, articulation 초기화, 물리 재생을 확인하세요. GUI에서 Pause했다면 Play를 재개하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)에 대응합니다. 기본 한 축 팔의 변환·제어와 선택적 Franka 목표 추종은 실행기로 수행합니다. GUI 가져오기, 로봇별 예제와 ROS 2 node import는 별도의 선택 절차이며 자동 실행기에 포함되지 않습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 2026-09-14의 기본 headless 120단계에서 shoulder와 실제 위치 약 0.51539 rad를 확인한 기록이 있습니다. 과거 기록의 source 경로는 폴더 번호 정리 전 경로입니다. 수치는 당시 조건의 참고값이며 Franka·GUI·ROS import나 현재 코드의 재검증 결과는 아닙니다.
