# 104. TurtleBot을 가져와 바퀴가 구동되는 물리 로봇으로 만들기

## 이번에 배우는 것

**TurtleBot3의 URDF를 USD로 가져오고, 이동 가능한 몸체와 두 바퀴의 속도 drive를 확인합니다.**

로봇 모형이 화면에 보이는 것과 물리적으로 주행할 수 있는 것은 다릅니다. 몸체는 바닥에서 지지되어야 하고, 바퀴 관절은 속도 명령을 받아야 합니다. 이번에는 ROS 메시지를 연결하기 전에 이 두 조건을 먼저 확인합니다.

| 단계 | 사용하는 파일·도구 | 완료 후 확인할 것 |
|---|---|---|
| 로봇 설명 전처리 | 시스템 Python의 `preprocess_urdf.py` | 이름이 확정된 URDF |
| USD 변환 | Isaac Sim URDF Importer | 로봇 형상과 articulation |
| 관절 검사 | Script Editor의 `inspect_robot.py` | 두 바퀴의 angular drive 값 |
| 물리 시험 | Play와 Property | 바닥 접지와 바퀴 회전 |

`preprocess_urdf.py`와 `inspect_robot.py`는 실행 장소가 다릅니다. 이 폴더에는 독립 시뮬레이션용 `run.py`가 없습니다.

## 1. ROS 로봇 설명을 전처리하기

기본 환경은 Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1입니다. Ubuntu 22.04에서는 아래 `jazzy`를 `humble`로 바꿉니다. `xacro`, `colcon`, TurtleBot3 description 빌드에 필요한 ROS 의존성이 준비되어 있어야 합니다.

저장소 루트의 **Bash 터미널**에서 시작하세요.

```bash
source /opt/ros/jazzy/setup.bash
command -v xacro
mkdir -p src/104_ros2_ros2_turtlebot/output
git clone --branch "$ROS_DISTRO" https://github.com/ROBOTIS-GIT/turtlebot3.git src/104_ros2_ros2_turtlebot/output/turtlebot3
```

이미 해당 경로에 description을 준비했다면 clone은 생략합니다. 이 실습 폴더 안의 출력 경로에 가져오므로 원래 저장소 소스와 구분할 수 있습니다. 패키지를 빌드하고 탐색 경로를 등록합니다.

```bash
colcon --log-base src/104_ros2_ros2_turtlebot/output/ros_logs build \
  --base-paths src/104_ros2_ros2_turtlebot/output/turtlebot3/turtlebot3_description \
  --build-base src/104_ros2_ros2_turtlebot/output/ros_build \
  --install-base src/104_ros2_ros2_turtlebot/output/ros_install
source src/104_ros2_ros2_turtlebot/output/ros_install/setup.bash
python3 src/104_ros2_ros2_turtlebot/preprocess_urdf.py \
  src/104_ros2_ros2_turtlebot/output/turtlebot3/turtlebot3_description/urdf/turtlebot3_burger.urdf \
  --output src/104_ros2_ros2_turtlebot/output/turtlebot3/turtlebot3_description/urdf/tb3_burger_processed.urdf
```

### 코드에서 볼 부분

URDF에 남아 있는 xacro 표현식을 펼치는 실제 호출은 다음과 같습니다.

```python
subprocess.run(
    ["xacro", str(source), "namespace:="],
    cwd=source.parent, check=True, capture_output=True, text=True
)
```

`namespace:=`는 빈 접두사를 전달합니다. 그 결과 바퀴 관절 이름은 `wheel_left_joint`, `wheel_right_joint`가 됩니다. 스크립트는 생성된 XML에서 이 두 이름을 검사한 뒤 새 파일을 씁니다.

`cwd=source.parent`는 전처리를 원본 URDF 폴더에서 실행한다는 뜻입니다. 출력도 그 폴더에 두어 상대 경로 자원의 위치 관계를 유지합니다. `package://turtlebot3_description/...` 형식의 메시 경로는 패키지 탐색이 필요하므로 description 전체와 빌드된 workspace를 함께 준비합니다.

### 실행 결과 확인하기

콘솔의 `expanded robot= ... joints= ...`에서 두 바퀴 이름을 확인하세요. `tb3_burger_processed.urdf`가 새로 생겼다면 전처리 결과를 얻은 것입니다. 아직 USD 변환이나 물리 실행까지 끝난 것은 아닙니다.

출력 파일이 이미 있으면 스크립트가 중단합니다. 반복 실험에서는 `tb3_burger_processed_02.urdf`처럼 새 이름을 사용하세요.

## 2. USD로 가져오고 바퀴 drive 읽기

지원 NVIDIA RTX GPU가 있는 Isaac Sim GUI를 엽니다. 공식 가져오기 절차처럼 description workspace를 인식하는 터미널에서 `~/isaacsim/isaac-sim.sh`를 실행할 수 있습니다. 이번 단계는 **URDF 가져오기와 물리 설정**을 사용하며, ROS Bridge 통신을 실행하는 단계는 아닙니다. 이후 Bridge 실습에서는 시스템 ROS와 Isaac Sim 내부 ROS 라이브러리 환경을 별도 터미널로 구성합니다.

1. **File > New**를 선택합니다. **Create > Physics**에서 Ground Plane과 Physics Scene을 만들고 **Create > Light > Distant Light**로 조명을 추가합니다. 공식 예제처럼 Simple Room을 쓰려면 Content Browser의 `Isaac/Environments/Simple_Room/simple_room.usd`를 넣고 환경의 이동값을 0으로 맞춥니다.
2. **File > Import**에서 앞의 processed URDF를 선택합니다.
3. **Referenced Model**, Links의 **Moveable Base**를 선택합니다. Joints & Drives에서 두 wheel joint의 Target을 **Velocity**로 설정합니다.
4. **USD Output**을 이 폴더의 새 `output/import_01`로 지정하고 Import합니다.
5. 로봇을 테이블이나 다른 물체와 겹치지 않는 바닥 바로 위에 놓습니다. Play 후 바닥으로 내려와 지지되는지 보고 Stop합니다.
6. 두 바퀴 관절의 Angular Drive에서 **Stiffness=0**, **Damping=10000000**, **Target Velocity=0**으로 맞춥니다.
7. **Window > Script Editor**에서 `inspect_robot.py` 전체를 붙여 넣고 실행합니다.

### 설정에서 볼 부분

Moveable Base는 차체가 월드에 고정되지 않게 합니다. 고정 베이스로 가져오면 바퀴가 돌아도 로봇 몸체가 이동할 수 없습니다.

속도 drive에서 stiffness를 0으로 두는 이유는 관절을 특정 각도로 끌어당기는 위치 항을 제거하기 위해서입니다. damping은 목표 속도와 현재 속도의 차이에 반응하는 항입니다. `10000000`은 이 공식 TurtleBot 실습의 시작값이며 모든 로봇에 적용할 값은 아닙니다.

`inspect_robot.py`는 실제 Stage의 관절에서 값을 읽습니다.

```python
drive = UsdPhysics.DriveAPI.Get(prim, "angular")
```

두 이름의 관절이 있고 angular drive가 있는지는 검사하지만, stiffness와 damping이 올바른 값인지까지 자동 판정하지는 않습니다. 따라서 출력값을 다음 기준과 직접 비교합니다.

### 실행 결과 확인하기

| 출력 필드 | 이번 설정의 값 | 해석 |
|---|---|---|
| `path` | 두 wheel joint의 실제 경로 | 검사한 관절 확인 |
| `stiffness` | `0.0` | 위치 목표 항 제거 |
| `damping` | `10000000.0` | 속도 오차에 대한 gain |
| `target_velocity` | `0.0` | 시험 전 정지 명령 |
| `articulation_roots` | 로봇의 root 경로 포함 | 링크와 관절을 묶는 물리 계통 |

바퀴가 두 개라는 검사는 통과해도 articulation root나 값이 적절하지 않을 수 있습니다. 목록이 비어 있지 않은지, 다른 로봇이 함께 들어 있지 않은지 확인하세요. 작업 장면은 `output/turtlebot_lab.usd`처럼 새 경로로 저장합니다. References의 Asset Path에는 Importer가 생성한 USD가 연결됩니다.

## 3. 로봇 설명과 물리 설정의 관계 정리

```text
xacro 표현식 → 확정된 URDF 이름·구조
URDF Importer → USD 링크·관절·질량·충돌 정보
Moveable Base + 바퀴 속도 drive + 바닥 접촉 → 주행 가능한 물리 구성
```

Importer가 형상을 읽었어도 질량·관성·마찰을 함께 확인해야 합니다. 바퀴가 미끄러지는 문제와 목표 속도를 따라가지 못하는 문제는 원인이 다릅니다. 마찰은 바닥과 바퀴의 Physics Material을, 관절 응답은 drive 값을 확인합니다.

## 4. 간단한 확인 실험

**왼쪽 바퀴의 Target Velocity만 0에서 30 degree/s로** 바꿔 Play해 보세요. 오른쪽은 0, stiffness와 damping은 그대로 둡니다.

왼쪽 바퀴의 회전과 차체의 회전 반응을 확인합니다. GUI의 USD angular drive 값은 degree/s이므로 이후 ROS 제어 코드의 rad/s와 같은 숫자로 비교하지 마세요. 시험 뒤 Stop하고 왼쪽 Target Velocity를 0으로 복구합니다.

## 실행할 때 막히면

- **`xacro` 명령이 없음**: 선택한 배포판의 xacro를 준비하고 ROS setup을 source했는지 확인하세요. 전처리는 시스템 `python3`로 실행합니다.
- **가져온 로봇의 메시 일부가 없음**: processed URDF의 `mesh filename`과 description의 `meshes/` 위치를 대조하세요. `ros2 pkg prefix turtlebot3_description`으로 패키지 탐색도 확인합니다.
- **바퀴는 도는데 차체가 고정됨**: Moveable Base로 가져왔는지 확인하세요.
- **검사에서 바퀴가 2개보다 많거나 적음**: 이름 접두사가 남았거나 Stage에 로봇이 여러 대 있을 수 있습니다. 새 장면에서 한 대로 검사합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [URDF Import: Turtlebot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html)에 대응합니다. 외부 입력은 [ROBOTIS TurtleBot3 description](https://github.com/ROBOTIS-GIT/turtlebot3/tree/jazzy/turtlebot3_description)이며, ROS 준비는 [5.1 ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

두 보조 스크립트는 전처리와 Stage 검사를 돕습니다. `tutorial.json`의 검증 상태는 `not_run`이며 패키지 빌드·가져오기·바퀴 운동은 위 절차로 확인할 기준입니다. 외부 ROS 토픽 통신은 이번 실습 범위가 아닙니다.
