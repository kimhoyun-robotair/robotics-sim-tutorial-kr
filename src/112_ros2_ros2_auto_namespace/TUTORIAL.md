# 112. Automatic ROS 2 Namespace Generation

권장 학습 순서 **112** · ROS 2 연결과 기본 통신 · 출처 ID `t021`

**목표:** 로봇 USD 계층에 `isaac:namespace`를 붙여 String, TF, 카메라, Lidar의 ROS 토픽 이름이 어떻게 생성되는지 확인합니다. 로컬 코드는 원문처럼 물리 로봇이 아닌 **계층 실습용 Xform**과 String/TF 그래프를 만듭니다. 센서는 아래 GUI 단계로 추가합니다.

## 이 실습의 의도

USD 계층의 `isaac:namespace` 속성이 일반 ROS 노드와 센서 Helper의 토픽 이름에 어떻게 반영되는지 비교한다. `mock_robot`은 물리 로봇 대신 주소 관계를 보기 위한 Xform 묶음이므로 바퀴 주행이나 로봇 형상은 기본 결과가 아니다. `setup_stage.py`는 계층과 String/TF 그래프까지 만들며, Hawk·LiDAR 추가와 두 로봇 복제는 GUI에서 이어서 수행한다.

## 실행 후 확인할 것

- Script Editor 실행 후 Stage에서 `/mock_robot/base_link` 아래 센서·바퀴 Xform과 `wheel_left/String_graph`, `wheel_left/TF_graph`를 확인한다. 센서 자체와 물리 articulation이 생성되지 않은 것은 이 단계의 정상 범위다.
- 초기 계층을 Play하면 `/wheel_left/topic`의 `std_msgs/msg/String`을 실제 수신해 `wheel namespace lesson`을 확인한다. String publisher는 playback tick에 연결되어 있으며, 별도 센서 추가 전 카메라/LiDAR 토픽이 없는 것은 정상이다.
- 아래 GUI 단계를 마친 뒤에는 `/lidar_link/laser_scan`과 Hawk 좌·우 RGB/CameraInfo를 수신한다. 타입은 각각 `sensor_msgs/msg/LaserScan`, `Image`, `CameraInfo`인지 확인하고, 토픽 존재와 실제 센서 데이터 수신을 구별한다.
- root namespace 추가와 복제 후 `/mock_robot/wheel_left/topic`, `/mock_robot_01/wheel_left/topic`을 각각 echo한다. 복제된 prim 이름뿐 아니라 root의 namespace **속성값**을 직접 바꾸어야 두 로봇의 통신 이름이 분리된다.
- `/mock_robot/tf`, `/mock_robot_01/tf`의 `tf2_msgs/msg/TFMessage`를 읽어 실제 frame 이름도 확인한다. TF 토픽 namespace와 메시지 내부 좌표계 이름을 동일한 문자열 규칙으로 추측하지 않는다.
- String publisher의 `nodeNamespace`만 `manual_test`로 설정한 뒤 `/manual_test/topic`으로 바뀌고 센서 토픽은 유지되는지 본다. 이 속성 변경으로 Xform 위치나 물리 좌표가 바뀌어야 하는 것은 아니다.

## 실행 환경: 이 폴더만으로 시작하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Linux, ROS 2 Humble(이 문서의 명령 기준)이 필요합니다. ROS를 통해 다른 프로세스와 통신하므로 시뮬레이터와 ROS 터미널을 구분합니다. `ISAAC_SIM`은 실제 설치 디렉터리로 바꾸세요.

**터미널 A — Isaac Sim**: ROS 시스템 환경을 source하지 않은 새 Bash에서 내부 Python 3.11용 브리지를 사용합니다. `.bashrc`가 `/opt/ros`를 자동 source한다면 해당 줄을 적용하지 않은 깨끗한 셸을 사용하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

**터미널 B — ROS CLI**: 별도 Bash에서 시스템 ROS를 사용합니다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic list
```

Humble의 기본 Python 3.10 모듈을 Isaac Sim의 Python 3.11에 넣으면 ABI 오류가 납니다. Jazzy를 사용한다면 두 터미널의 배포판 이름과 내부 라이브러리 경로를 모두 `jazzy`로 바꿉니다. 같은 컴퓨터에서 먼저 실습하세요. 여러 컴퓨터는 DDS 네트워크/방화벽 설정도 일치해야 합니다. 다른 로컬 튜토리얼이나 공통 모듈은 필요하지 않습니다.

### 로컬 Script Editor 파일 실행

새 Stage에서 시작하고 Play를 정지합니다. **Window > Script Editor**에서 이 폴더의 `setup_stage.py`를 열어 Run을 누릅니다. 파일 열기 대신 아래 코드의 경로를 이 폴더의 절대 경로로 바꿔 실행해도 됩니다.

```python
from pathlib import Path
lesson = Path("/absolute/path/to/this/package")
exec(compile((lesson / "setup_stage.py").read_text(), str(lesson / "setup_stage.py"), "exec"))
```

이 코드는 이미 실행 중인 Kit 안에서 쓰는 코드입니다. 시스템 `python3 setup_stage.py`로 실행하지 않습니다. 재실행할 때는 **File > New**로 새 Stage를 열어 기존 실습 Stage와 구분하세요. 결과를 보존하려면 이 폴더 아래 새 이름의 USD로 **File > Save As**합니다.


## 실습 순서

1. `setup_stage.py`를 실행하고 Stage에서 `/mock_robot/base_link` 아래 `lidar_link`, `camera_link`, `wheel_left`, `wheel_right`를 펼칩니다. `wheel_left` Property에 `isaac:namespace = wheel_left`가 있습니다. `/mock_robot`에는 아직 namespace를 넣지 않습니다.
2. **Create > Sensors > RTX Lidar > NVIDIA > Example Rotary 2D**로 센서를 만들고 Stage 트리에서 `/mock_robot/base_link/lidar_link` 아래로 드래그합니다. 로컬 translate는 0으로 맞춥니다. **Create > Sensors > Camera and Depth Sensors > LeopardImaging > Hawk**도 만들어 `/mock_robot/base_link/camera_link` 아래로 이동합니다. 센서 asset은 Isaac Sim 5.1 asset 서버 또는 로컬 asset pack 접근이 필요합니다.
3. **Tools > Robotics > ROS 2 OmniGraphs > Camera**에서 아래 두 그래프를 만듭니다. 두 경우 **Depth**는 해제합니다.

   | Camera Prim | Graph Path |
   |---|---|
   | `/mock_robot/base_link/camera_link/Hawk/left/camera_left` | `/mock_robot/base_link/camera_link/Hawk/Camera_Left_Graph` |
   | `/mock_robot/base_link/camera_link/Hawk/right/camera_right` | `/mock_robot/base_link/camera_link/Hawk/Camera_Right_Graph` |

4. **Tools > Robotics > ROS 2 OmniGraphs > RTX Lidar**에서 Lidar Prim=`/mock_robot/base_link/lidar_link/Example_Rotary_2D`, Graph Path=`/mock_robot/base_link/lidar_link/Lidar_Graph`, **Laser Scan만** 체크합니다. 실제 생성된 prim 이름이 다르면 Stage에서 정확한 경로를 복사합니다.
5. Hawk, Hawk/left, Hawk/right를 각각 선택하고 **Property > Add > Isaac > Namespace**를 적용해 값에 `Hawk`, `left`, `right`를 각각 입력합니다. `lidar_link`, `camera_link`, `wheel_left` 값은 코드가 이미 만들었습니다.
6. Play 후 `ros2 topic list`에서 `/wheel_left/topic`, `/wheel_left/tf`, `/lidar_link/laser_scan`, `/camera_link/Hawk/left/rgb`, `/camera_link/Hawk/right/rgb`와 양쪽 `camera_info`가 보이는지 확인합니다. `ros2 topic echo /wheel_left/topic --once`로 문자열도 확인합니다.
7. Stop합니다. `/mock_robot`에 Namespace를 추가하고 `mock_robot`로 설정합니다. `/mock_robot`를 우클릭 **Duplicate**하여 `/mock_robot_01`을 만들고 복제된 root의 Namespace를 `mock_robot_01`로 **직접 변경**합니다. 다시 Play합니다.
8. 이제 `/mock_robot/wheel_left/topic`과 `/mock_robot_01/wheel_left/topic`이 분리됩니다. 카메라는 `/mock_robot/camera_link/Hawk/left/rgb`와 복제 로봇 경로로 분리되고 TF는 `/mock_robot/tf`, `/mock_robot_01/tf`로 나뉩니다. Topic 이름만 비교하지 말고 `ros2 topic echo /mock_robot/tf --once`의 frame_id도 읽어보세요.

## API와 개념

USD Xform은 계층/변환을 나타내며 articulation이나 충돌체를 자동 생성하지 않습니다. `CreateAttribute('isaac:namespace', Sdf.ValueTypeNames.String, custom=True)`는 USD에 사용자 attribute를 저장합니다. 브리지가 이 값을 읽어 ROS 이름을 구성합니다. prim 이름을 바꾸는 것만으로 attribute 문자열 값이 자동 바뀌지는 않습니다.

일반 ROS 노드는 **그래프 노드가 놓인 계층**을 따라 namespace를 모읍니다. Camera/Lidar Helper는 **Render Product가 가리키는 센서 계층**을 기준으로 합니다. TF는 로봇의 최상위 namespace만 사용하므로 복제 후 TF가 `/mock_robot/wheel_left/tf`가 되지 않습니다. `nodeNamespace`를 명시적으로 채우면 자동 생성보다 우선합니다. ROS namespace는 토픽 충돌을 피하는 이름 규칙이며 로봇 물리 좌표계 자체를 바꾸지 않습니다.

## 한 가지 변수 실험과 문제 해결

String publisher의 `nodeNamespace`만 `manual_test`로 지정해 `/manual_test/topic`으로 바뀌는지 확인합니다. 나머지 센서 토픽은 유지되어야 합니다. 두 로봇이 같은 토픽을 발행하면 복제 root의 **attribute 값**을 확인하세요. 센서 토픽이 없으면 Play, Helper가 참조하는 센서 경로, asset 로딩 오류를 순서대로 확인합니다. 재실행 오류는 기존 `/mock_robot`을 덮어쓰지 않도록 한 보호 장치이며 File > New 후 실행합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
