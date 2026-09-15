# 114. 카메라 출력에 ROS writer와 좌표계 연결하기

## 이번에 배우는 것

**Python에서 카메라 Render Product에 ROS writer를 붙이고, 영상·점군·CameraInfo·TF를 함께 읽습니다.**

앞의 카메라 Helper 방식은 그래프 노드가 발행 파이프라인을 준비했습니다. 이번에는 Python에서 writer를 직접 얻고 설정한 뒤 렌더 출력에 연결합니다. 같은 출력에 여러 writer를 붙여 색, 깊이, 점군을 나누어 보낼 수 있습니다.

| writer 또는 그래프 | 출력 | 이번에 읽을 내용 |
|---|---|---|
| `RgbROS2PublishImage` | `/camera_rgb` | 색 영상 |
| `DistanceToImagePlaneROS2PublishImage` | `/camera_depth` | 깊이 영상(m) |
| `DistanceToImagePlaneROS2PublishPointCloud` | `/camera_pointcloud` | 깊이에서 복원한 표면 |
| `ROS2PublishCameraInfo` | `/camera_camera_info` | 실제 카메라의 내부 파라미터 |
| `/World/CameraTF` 그래프 | `/tf`, `/clock` | 좌표계 관계와 시뮬레이션 시간 |

이번 장면은 큐브·벽·바닥을 코드로 생성합니다. 별도 창고 자산을 다운로드할 필요는 없습니다.

## 1. 카메라 데이터 발행하기

Isaac Sim 5.1, RTX GPU, Ubuntu 24.04의 ROS 2 Jazzy와 RViz2·`tf2_ros`를 준비합니다. 명령은 저장소 루트의 Bash에서 실행하세요. Ubuntu 22.04/Humble에서는 아래의 `jazzy` 값과 경로를 모두 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸입니다. 내부 브리지를 쓰며 설치 위치가 다르면 `ISAAC_SIM`을 바꿉니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/114_ros2_ros2_camera_publishing/run.py --frequency 30
```

GUI는 창을 닫을 때까지 유지됩니다. `--steps 1800`은 1800스텝 후 종료하며 `--headless`만 주면 같은 한도를 사용합니다. `--frames`는 `--steps` 없는 headless 실행의 한도만 정합니다.

터미널 B에서는 시스템 ROS를 source합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /camera_camera_info --once
ros2 topic echo /clock --once
rviz2 --ros-args -p use_sim_time:=true
```

RViz에서 Image를 추가해 `/camera_rgb`를 확인하고, 두 번째 Image에는 `/camera_depth`를 지정하세요. PointCloud2를 추가해 `/camera_pointcloud`를 선택합니다. 우선 Fixed Frame을 `camera`로 두어 센서 좌표에서 표면을 확인한 다음 `world`로 바꾸어 TF 연결도 확인합니다.

### 실행 결과 확인하기

CameraInfo의 해상도는 640×480, frame은 `camera`입니다. 콘솔에 다음 두 종류의 정보가 나옵니다.

```text
Gate step=2; theoretical render-relative rate=30 Hz. ...
CameraInfo: 640x480, fx=..., fy=...
```

fx·fy는 코드가 `read_camera_info()`로 읽은 값입니다. 다른 튜토리얼의 렌즈 설정에서 얻은 숫자를 그대로 기대하지 마세요. 또한 콘솔의 30 Hz는 렌더 간격으로 계산한 값입니다. 실제 수신 빈도는 `ros2 topic hz /camera_rgb`로 따로 관찰하고 Ctrl+C로 종료합니다.

## 2. Render Product에서 ROS 메시지까지 따라가기

### 코드에서 볼 부분

카메라 객체를 초기화하면 렌더 출력 경로를 얻을 수 있습니다.

```python
camera.initialize()
product = camera.get_render_product_path()
```

이 경로가 writer에 연결할 데이터의 출처입니다. 색 영상을 보내는 부분을 읽기 쉽게 나누면 다음 흐름입니다.

```python
writer = rep.writers.get('RgbROS2PublishImage')
writer.initialize(frameId='camera', nodeNamespace='', queueSize=1, topicName='camera_rgb')
writer.attach([product])
```

`initialize()`는 ROS 메시지의 이름과 설정을 정하고 `attach()`는 실제 렌더 파이프라인에 연결합니다. `frameId`는 좌표계 이름, `topicName`은 통신 경로입니다. 종료할 때는 연결한 writer를 `detach()`한 뒤 앱을 닫습니다.

CameraInfo에는 카메라에서 읽은 K·R·P와 왜곡 정보를 넘깁니다. K와 R은 3×3, P는 3×4 행렬이므로 writer 입력에 맞춰 각각 `[1,9]`, `[1,12]` 형태로 바꿉니다. 카메라 설정을 나중에 수정하면 초기화 때 읽어 둔 정보도 다시 읽어 writer를 재설정해야 합니다.

### 발행 간격에서 볼 부분

```python
step = max(1, int(60 / args.frequency))
```

시뮬레이션의 물리·렌더 간격은 1/60초입니다. Gate를 N으로 설정하면 N번째 렌더 프레임마다 writer가 실행됩니다. 요청 빈도를 정수 프레임 간격으로 바꾸므로 모든 요청값을 정확히 구현할 수는 없습니다.

| 요청 | Gate step | 렌더 시간 기준 빈도 |
|---|---|---|
| 30 Hz | 2 | 30 Hz |
| 20 Hz | 3 | 20 Hz |
| 25 Hz | 2 | 30 Hz |

RGB는 `RgbIsaacSimulationGate`, 깊이와 점군은 `DistanceToImagePlaneIsaacSimulationGate`, CameraInfo는 `PostProcessDispatchIsaacSimulationGate`를 사용합니다. **깊이와 점군은 같은 Gate를 공유**하므로 여기서 둘의 간격을 독립적으로 조절하는 것은 아닙니다. 내부 Gate 경로는 writer가 연결되어 파이프라인이 생긴 뒤 찾습니다.

### 실행 결과 확인하기

터미널 B에서 `ros2 run tf2_ros tf2_echo world camera`를 실행합니다. Stage의 `/World/camera`는 위치 `(4,0,2)` m에서 큐브와 벽을 바라보도록 생성됩니다. TF의 위치와 Stage의 위치를 함께 비교하세요.

`/World/CameraTF`에는 실제 카메라 pose를 읽는 노드와 `camera → camera_world` 회전을 입력하는 RawTF 노드가 있습니다. 코드의 RawTF 입력은 `[0.5,-0.5,0.5,0.5]`입니다. 설치된 5.1 노드 스키마의 입력 순서는 **IJKR, 즉 x/y/z/w**입니다. `Gf.Quatd(w,x,y,z)`와 순서를 혼동하지 마세요. RViz에 TF 표시를 추가해 두 frame의 원점은 같고 축 방향은 다른지 확인합니다.

Clock과 TF는 카메라 writer의 Gate와 별개로 매 playback tick에 실행됩니다. RViz의 `use_sim_time=true`는 `/clock`을 읽도록 하는 설정입니다. 카메라 데이터와 TF의 시간을 같은 기준으로 비교할 수 있게 합니다.

## 3. 깊이가 3차원 표면으로 바뀌는 과정 정리

깊이 z와 픽셀 위치 `(u,v)`가 있을 때 카메라 내부 파라미터를 사용해 다음처럼 복원할 수 있습니다.

```text
x = (u - cx) × z / fx
y = (v - cy) × z / fy
```

영상 중심에서 멀리 떨어진 픽셀일수록 같은 깊이에서 더 큰 x·y 위치가 됩니다. 점군은 이 센서 좌표의 점들을 모은 것입니다. ROS optical 좌표는 +Z가 앞, +X가 오른쪽, +Y가 아래입니다. TF가 있어야 이 표면을 `world` 같은 다른 좌표계에서 배치할 수 있습니다.

따라서 점군이 센서 좌표에서는 보이는데 world에서 안 보인다면, 깊이 생성과 TF 조회를 나누어 조사할 수 있습니다.

## 4. 간단한 확인 실험

앞의 실행을 종료하고 **`--frequency`만 30에서 20으로 바꿔 보세요.**

```bash
"$ISAAC_SIM/python.sh" src/114_ros2_ros2_camera_publishing/run.py --frequency 20
```

로그의 Gate는 2에서 3으로, 렌더 기준 이론값은 30 Hz에서 20 Hz로 바뀌어야 합니다. 같은 렌더 진행률에서는 카메라 메시지의 발행 기회가 이전의 2/3로 줄어듭니다. `ros2 topic hz /camera_rgb`로 실제 수신도 비교하되 GPU 부하 때문에 이론값과 다를 수 있음을 함께 기록하세요. `/clock`과 TF는 별도 tick 연결을 사용하므로 이 옵션으로 주기가 바뀌지 않습니다.

## 실행할 때 막히면

- **world에서 점군만 보이지 않음**: Fixed Frame을 `camera`로 바꾸어 데이터부터 확인하고 `/tf`, `/clock`을 차례로 점검하세요.
- **Gate 경로를 못 찾음**: writer가 attach되었는지, Isaac Sim 버전이 5.1인지 확인하세요. `_get_node_path`는 버전에 의존하는 내부 경로 접근입니다.
- **토픽은 있지만 RGB가 안 옴**: `ros2 topic info -v /camera_rgb`로 실제 QoS를 읽고 RViz Reliability를 맞추세요.
- **렌즈를 바꿨는데 CameraInfo가 이전 값임**: 실행 초기에 읽어 둔 정보가 남아 있을 수 있습니다. 앱을 종료하고 다시 초기화하세요.
- **이론값보다 모든 영상이 느림**: GPU 렌더 속도와 DDS 수신 부하를 확인하세요. `ros2 topic hz`는 벽시계 기준입니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Publishing Camera’s Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html)에 대응합니다. 실행 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 writer 함수들을 로컬 장면의 실행 흐름으로 구성했습니다. Gate와 RawTF 입력 설명은 로컬 코드·설치 스키마와 대조했습니다. `tutorial.json`은 `verification: not_run`이므로 실제 영상·점군·TF의 통합 수신과 축 정렬을 이번 문서 개정에서 검증했다고 해석하지 않습니다.
