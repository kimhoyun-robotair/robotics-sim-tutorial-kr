# 112. 로봇 계층에서 ROS 토픽 이름 자동 만들기

## 이번에 배우는 것

**USD 계층에 namespace를 지정하고 로봇을 복제하면서, 일반 메시지·TF·센서의 토픽 이름이 만들어지는 규칙을 비교합니다.**

로봇 두 대가 모두 `/rgb`와 `/joint_states`를 발행하면 어느 로봇의 데이터인지 구분하기 어렵습니다. namespace는 토픽 앞에 `robot1`, `robot2` 같은 이름을 붙여 통신 경로를 나눕니다. 이번에는 발행기마다 문자열을 반복 입력하는 대신 USD 계층에 `isaac:namespace`를 지정합니다.

| 대상 | 자동 이름을 만들 때 보는 위치 |
|---|---|
| 일반 ROS OmniGraph 노드 | 해당 노드가 놓인 Stage 계층 |
| Camera·LiDAR Helper | Render Product가 가리키는 센서 계층 |
| TF 노드 | 위쪽 계층에서 가장 상위의 namespace |
| 명시한 `nodeNamespace` | 자동 계산보다 우선하는 직접 지정값 |

`setup_stage.py`의 `mock_robot`은 계층을 배우기 위한 Xform 묶음입니다. 물리 관절이나 주행 가능한 로봇을 생성하지 않습니다.

## 1. 계층과 String 발행기 만들기

Isaac Sim 5.1과 지원 GPU, ROS 2 Humble 또는 Jazzy를 준비합니다. 아래는 저장소 루트의 Bash에서 사용하는 Ubuntu 24.04의 Jazzy 예시입니다. Ubuntu 22.04/Humble이라면 `jazzy` 값과 두 라이브러리·source 경로를 `humble`로 바꾸세요.

터미널 A는 시스템 ROS를 source하지 않은 새 셸입니다. 내부 브리지 라이브러리 경로는 이 셸에서 한 번만 설정합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

터미널 B에서는 시스템 ROS를 source합니다. 뒤의 영상 관찰에는 `rqt_image_view`가 필요합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

1. Isaac Sim에서 **File > New**로 빈 Stage를 열고 Stop 상태로 둡니다.
2. **Window > Script Editor**에 `src/112_ros2_ros2_auto_namespace/setup_stage.py` 전체를 붙여 넣어 실행합니다. 시스템 `python3`용 파일이 아닙니다.
3. 콘솔에 `Hierarchy and wheel String/TF graphs created`가 나타나면 Stage를 펼쳐 봅니다.
4. Play하고 터미널 B에서 문자열을 받습니다.

```bash
ros2 topic echo /wheel_left/topic --once
ros2 topic echo /wheel_left/tf --once
```

### 코드에서 볼 부분

```text
/mock_robot
└─ base_link
   ├─ lidar_link       namespace=lidar_link
   ├─ camera_link      namespace=camera_link
   ├─ wheel_left       namespace=wheel_left
   │  ├─ String_graph
   │  └─ TF_graph
   └─ wheel_right
```

코드는 위 세 prim에 다음 형태로 속성을 추가합니다. `/mock_robot`에는 아직 namespace가 없습니다.

```python
prim.CreateAttribute('isaac:namespace', Sdf.ValueTypeNames.String, custom=True).Set(name)
```

String 발행기의 `topicName`은 `topic`이고 `nodeNamespace`는 비어 있습니다. 따라서 노드에서 부모 방향으로 올라가며 발견한 `wheel_left`가 붙어 `/wheel_left/topic`이 됩니다. Generic Publisher의 String 타입을 설정한 뒤에는 `await ...next_update_async()`로 앱 업데이트를 한 번 기다리고, 생성된 `inputs:data`에 문자열을 넣습니다.

### 실행 결과 확인하기

`/wheel_left/topic`에서 `wheel namespace lesson`을 받아야 합니다. TF 그래프도 wheel_left 아래에 있으므로 초기에는 `/wheel_left/tf`를 확인합니다. 화면에 로봇 형상이 없어도 이 단계에서는 이상하지 않습니다. Xform은 위치·계층만 나타내는 객체이며, 카메라와 LiDAR도 아직 추가하지 않았습니다.

## 2. 센서를 추가하고 로봇별 이름 나누기

Stop한 상태에서 센서를 추가합니다. Hawk와 RTX LiDAR 자산을 가져올 수 있는 5.1 asset 서버 또는 로컬 asset pack이 필요합니다.

1. **Create > Sensors > RTX Lidar > NVIDIA > Example Rotary 2D**로 센서를 만들고 `lidar_link` 아래로 옮깁니다. 센서의 로컬 Translate를 0으로 맞춥니다.
2. **Create > Sensors > Camera and Depth Sensors > LeopardImaging > Hawk**를 만들어 `camera_link` 아래로 옮깁니다.
3. Hawk, Hawk/left, Hawk/right를 각각 선택합니다. **Property > Add > Isaac > Namespace**로 속성을 추가하고 값은 `Hawk`, `left`, `right`로 지정합니다.
4. **Tools > Robotics > ROS 2 OmniGraphs > Camera**에서 다음 두 카메라 발행기를 만듭니다. `nodeNamespace`는 비우고 RGB·CameraInfo를 사용하며 Depth는 해제합니다. 생성된 RGB Helper의 `topicName=rgb`, Info Helper의 `topicName=camera_info`를 확인합니다. 앞에 `/`를 붙이지 않은 상대 이름으로 두어 자동 namespace와 결합하게 합니다.

| Camera Prim | Graph Path |
|---|---|
| `/mock_robot/base_link/camera_link/Hawk/left/camera_left` | `/mock_robot/base_link/camera_link/Hawk/Camera_Left_Graph` |
| `/mock_robot/base_link/camera_link/Hawk/right/camera_right` | `/mock_robot/base_link/camera_link/Hawk/Camera_Right_Graph` |

5. **ROS 2 OmniGraphs > RTX Lidar**에서는 센서 prim을 `/mock_robot/base_link/lidar_link/Example_Rotary_2D`, 그래프를 `/mock_robot/base_link/lidar_link/Lidar_Graph`로 지정합니다. **Laser Scan만** 선택하고 namespace는 비우며 `topicName=laser_scan`으로 맞춥니다. 실제 생성된 prim 이름이 다르면 Stage의 경로를 사용하세요.
6. 빈 계층에 센서만 추가했으므로 관찰할 표면과 조명을 준비합니다. **Create > Mesh > Cube**로 상자를 만들고 중심을 `(2,0,0.4)` m, 한 변을 1 m로 맞추세요. LiDAR 높이의 수평 스캔에 표면이 걸립니다. **Create > Light > Dome Light**를 추가해 intensity를 1500으로 설정합니다.
7. Viewport의 Camera 선택 메뉴에서 Hawk의 왼쪽 카메라로 전환합니다. 상자가 시야에 없으면 Stop 상태에서 Hawk 부모의 회전을 조정해 상자를 바라보게 하고 오른쪽 카메라에서도 확인하세요. 센서 namespace 속성은 그대로 유지합니다.
8. Play 후 `/lidar_link/laser_scan`, `/camera_link/Hawk/left/rgb`, `/camera_link/Hawk/right/rgb`와 양쪽 `camera_info`를 확인합니다. `ros2 topic echo /lidar_link/laser_scan --once`에서 유한한 range를 찾고, `ros2 run rqt_image_view rqt_image_view`에서 좌·우 RGB를 선택해 상자가 보이는지 확인하세요. 토픽 이름 생성과 센서의 실제 데이터 생성을 함께 확인하는 단계입니다.

### 설정에서 볼 부분

센서 Helper는 **그래프 위치가 아니라 센서의 위치**에서 namespace를 모읍니다. 왼쪽 카메라에서 위로 올라가면 `left`, `Hawk`, `camera_link`를 만나므로 토픽은 `/camera_link/Hawk/left/rgb`가 됩니다. 이름이 있는 모든 prim을 무조건 붙이는 것이 아니라 `isaac:namespace` 값이 있는 prim만 반영합니다.

이제 Stop하고 로봇 전체를 구분할 이름을 추가합니다.

1. `/mock_robot`에 Namespace를 추가하고 값은 `mock_robot`으로 설정합니다.
2. root를 우클릭해 **Duplicate**합니다.
3. 복제한 `/mock_robot_01`의 Namespace **속성값도** `mock_robot_01`로 수정합니다. prim 이름이 바뀌어도 복사된 문자열은 그대로일 수 있습니다.
4. 복제한 센서 Helper와 TF의 대상 경로가 복제 계층을 가리키는지 확인하고 Play합니다.

### 실행 결과 확인하기

```bash
ros2 topic echo /mock_robot/wheel_left/topic --once
ros2 topic echo /mock_robot_01/wheel_left/topic --once
ros2 topic echo /mock_robot/tf --once
ros2 topic echo /mock_robot_01/tf --once
```

String은 두 번 모두 같은 내용이지만 통신 경로는 분리됩니다. 카메라도 `/mock_robot/camera_link/Hawk/left/rgb`와 `/mock_robot_01/camera_link/Hawk/left/rgb`로 나뉩니다. TF는 가장 상위 namespace만 사용하므로 `/mock_robot/wheel_left/tf`가 아니라 `/mock_robot/tf`가 됩니다.

TF 토픽 이름이 분리되었다고 메시지 내부의 모든 frame 문자열을 추측할 수는 없습니다. `header.frame_id`와 `child_frame_id`도 직접 읽어 보세요. 이 mock 계층은 articulation이 아니므로 실제 로봇의 전체 관절 TF를 검증하는 실습도 아닙니다.

## 3. 이름을 모으는 기준 정리

```text
일반 메시지: 그래프 노드 → 부모 계층의 namespace들을 연결
센서 메시지: 센서 prim  → 부모 계층의 namespace들을 연결
TF 메시지:   해당 계층의 최상위 namespace만 사용
```

namespace는 통신 이름을 바꿉니다. `lidar_link`의 높이 0.4 m나 `wheel_left`의 위치 -0.2 m를 바꾸지 않습니다. 로봇의 공간적 위치와 메시지를 구분하는 이름을 서로 독립적으로 다룰 수 있습니다.

## 4. 간단한 확인 실험

원본 로봇의 String Publisher에서 **`nodeNamespace`만 `manual_test`로 바꿔 보세요.** Stop/Play 후 터미널 B에서 실행합니다.

```bash
ros2 topic echo /manual_test/topic --once
```

직접 지정한 값이 자동 계산보다 우선하므로 원본 String은 이 토픽으로 옮겨갑니다. 복제 로봇의 String과 센서 토픽은 그대로여야 합니다. 실험 후 입력을 비우면 계층에서 계산하는 방식으로 돌아갑니다.

## 실행할 때 막히면

- **`Open a new stage without /mock_robot first` 오류**: 코드가 기존 장면을 덮어쓰지 않도록 중단한 것입니다. 필요한 장면을 저장하고 File > New에서 다시 실행하세요.
- **복제했는데 같은 토픽에 두 publisher가 보임**: 복제 root의 prim 이름과 Namespace 속성값을 각각 확인하세요.
- **센서만 이름 규칙이 다름**: Helper의 `nodeNamespace`가 채워져 있는지, Render Product가 올바른 센서를 가리키는지 확인하세요.
- **LiDAR·영상 데이터가 비어 있음**: namespace뿐 아니라 센서의 실제 렌더 대상도 필요합니다. Play와 자산 로딩을 확인하고 센서 앞에 관찰할 물체를 배치하세요.
- **시스템 ROS를 source한 뒤 Isaac Sim import 오류**: 터미널 A를 새로 열어 내부 Python 3.11용 브리지를 사용하세요. 외부 ROS Python은 터미널 B에 둡니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Automatic ROS 2 Namespace Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)에 대응합니다. 내부 라이브러리 설정은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

로컬 파일은 계층·String·TF 그래프까지 만들고 센서 추가와 복제는 GUI에서 수행합니다. 자동 센서 namespace는 설치된 5.1 `collect_namespace.py`와 대조했습니다. `tutorial.json`은 `verification: not_run`이며 실제 GUI 복제·센서 수신 결과는 이번 문서 개정에서 실측하지 않았습니다.
