# 113. 같은 장면을 두 카메라의 RGB와 깊이로 보기

## 이번에 배우는 것

**두 카메라의 렌더 결과를 ROS 2로 보내고, RGB·깊이·점군·CameraInfo가 같은 장면을 어떻게 다르게 표현하는지 비교합니다.**

카메라 prim은 “어디에서 어떤 렌즈로 볼지”를 정합니다. **Render Product**는 그 카메라와 출력 해상도를 묶고, ROS Helper는 결과를 메시지로 보냅니다. 카메라를 Stage에 놓는 것만으로 ROS 영상이 생기지는 않습니다.

| 카메라당 출력 | ROS 타입 | 읽을 내용 |
|---|---|---|
| `rgb` | `sensor_msgs/msg/Image` | 물체의 색과 영상상 위치 |
| `depth` | `sensor_msgs/msg/Image` | 영상 평면 기준 깊이(m) |
| `depth_pcl` | `sensor_msgs/msg/PointCloud2` | 깊이를 3차원으로 복원한 표면 |
| `camera_info` | `sensor_msgs/msg/CameraInfo` | 해상도·초점거리·영상 중심 |

`run.py`는 색이 다른 두 물체와 벽·바닥을 직접 만듭니다. 두 카메라는 x축으로 1 m 떨어져 있어 같은 물체를 서로 다른 위치에서 봅니다.

## 1. 두 카메라 실행하고 영상 받기

Isaac Sim 5.1, RTX GPU, ROS 2 Humble 또는 Jazzy, RViz2 또는 `rqt_image_view`가 필요합니다. 아래 명령은 저장소 루트의 Bash 기준입니다. 기본 환경은 Ubuntu 24.04의 Jazzy입니다. Ubuntu 22.04/Humble에서는 `jazzy` 값과 경로를 `humble`로 바꾸세요.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 내부 브리지를 사용합니다. `ISAAC_SIM`은 실제 설치 위치에 맞춥니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/113_ros2_ros2_camera/run.py
```

기본 GUI 실행은 창을 닫을 때까지 유지됩니다. `--steps 1800`을 추가하면 1800스텝 후 종료합니다. `--headless`는 창 없이 렌더링하며, 단계 수를 생략하면 1800회를 사용합니다. 기존 `--frames`는 headless 기본 한도만 정하고 GUI 종료는 제어하지 않습니다.

터미널 B는 시스템 ROS 환경입니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic list -t
ros2 topic echo /camera_1/camera_info --once
rviz2
```

RViz에서 **Add > Image**를 두 개 만들고 토픽을 `/camera_1/rgb`, `/camera_2/rgb`로 지정합니다. 두 영상에서 빨간·파란 물체의 위치가 어떻게 다른지 확인하세요. 깊이는 별도 Image 도구에서 `/camera_1/depth`를 선택합니다.

### 실행 결과 확인하기

카메라 1의 CameraInfo에서 `width=640`, `height=480`, `header.frame_id=camera_1`을 확인합니다. 카메라 2는 `camera_2`를 사용합니다. RGB가 보인 다음 RViz에 **PointCloud2**를 추가하고 `/camera_1/depth_pcl`을 선택하세요. **Fixed Frame은 `camera_1`**로 둡니다.

이 코드는 TF를 발행하지 않습니다. 따라서 첫 카메라의 점군을 `world`나 `camera_2`로 변환하려 하면 필요한 좌표계 연결을 찾지 못합니다. 센서 좌표계에서 표면을 먼저 확인하는 실습입니다.

Image의 `encoding`은 채널 순서와 자료형, `step`은 한 행의 바이트 수입니다. `data`를 읽을 때 단순히 너비×높이의 숫자 배열이라고 가정하지 말고 이 두 필드를 함께 확인하세요. 깊이 값의 단위는 m이며 화면의 밝기는 이 수치를 시각화한 결과입니다.

## 2. 카메라 그래프와 내부 파라미터 읽기

Stage에서 `/World/Camera_1`, `/World/Camera_2`를 찾고 **Window > Graph Editors > Action Graph**에서 `/World/CameraGraph_1`을 엽니다.

### 코드에서 볼 부분

```text
Tick → Once → Render Product 생성 → Info·RGB·Depth·PointCloud Helper 준비
                          └─ renderProductPath를 각 Helper에 전달
```

`Once`는 렌더 출력과 후처리 연결을 매 프레임 새로 만들지 않도록 초기 실행을 제한합니다. 준비된 센서 파이프라인이 이후 렌더링 결과를 발행합니다. 실행 포트 연결 외에 `renderProductPath` 연결이 필요한 이유는 각 Helper가 **어느 카메라의 출력인지** 알아야 하기 때문입니다.

코드는 카메라마다 아래 설정을 사용합니다.

```python
camera.CreateHorizontalApertureAttr(20.955)
camera.CreateVerticalApertureAttr(15.71625)
camera.CreateFocalLengthAttr(18)
```

640×480 해상도에서 픽셀 단위 초점거리는 다음과 같이 구할 수 있습니다.

```text
fx = 640 × 18 / 20.955 ≈ 549.75 pixel
fy = 480 × 18 / 15.71625 ≈ 549.75 pixel
```

CameraInfo의 내부 파라미터 행렬 K는 ROS 메시지에서 소문자 `k` 배열로 표시됩니다. 3×3 행렬을 펼친 9개 숫자로, `k[0]`, `k[4]`가 fx·fy, `k[2]`, `k[5]`가 중심점 cx·cy이며 이번 설정에서는 중심이 약 `(320, 240)`입니다. 렌즈 설정을 바꾸면 단순히 그림만 바뀌는 것이 아니라 이 값도 달라집니다.

그래프를 손으로 재구성하려면 Stop 후 두 번째 카메라 그래프만 삭제하고 새 그래프를 만드세요. Camera_2 prim은 남깁니다.

1. **On Playback Tick**, **Isaac Run One Simulation Frame**, **Isaac Create Render Product**, **ROS2 Context**, **ROS2 Camera Helper**, **ROS2 Camera Info Helper**를 추가합니다.
2. Tick.tick → Once.execIn → Once.step → Render.execIn을 연결합니다. Render의 execOut과 renderProductPath를 두 Helper의 대응 입력에 연결합니다. Context.context도 두 Helper에 연결합니다.
3. Render는 `cameraPrim=/World/Camera_2`, 640×480, `enabled=True`로 설정합니다.
4. Camera Helper는 `type=rgb`, `topicName=manual_rgb`, `frameId=camera_2`, Info Helper는 `topicName=manual_camera_info`, 같은 frameId로 설정합니다. Context는 환경 Domain ID를 사용하도록 합니다.
5. Play 후 `ros2 topic echo /manual_camera_info --once`와 `/manual_rgb` 영상으로 확인합니다.

같은 작업은 **Tools > Robotics > ROS 2 OmniGraphs > Camera**에서도 구성할 수 있습니다. Graph Path와 Camera Prim을 지정하고 원하는 RGB·Depth 출력을 선택하세요. 별도 Render Product를 사용하므로 탐색용 Viewport 카메라를 바꾸어도 발행 카메라는 그대로입니다.

### 실행 결과 확인하기

기본 실행에는 인식 결과가 없습니다. 의미 라벨까지 비교하려면 앞의 앱을 종료하고 터미널 A에서 다음처럼 실행합니다.

```bash
"$ISAAC_SIM/python.sh" src/113_ros2_ros2_camera/run.py --perception semantic_segmentation
```

코드는 Red와 Blue prim에 `red`, `blue` 라벨을 추가합니다. `/camera_1/semantic_segmentation`과 `/camera_1/labels`를 함께 읽어 색 또는 ID가 어떤 물체를 뜻하는지 연결하세요. 경계 상자를 보려면 별도 실행에서 `--perception bbox_3d`를 선택하며 외부 ROS에 `vision_msgs`가 필요합니다.

Helper가 초기화된 뒤 `type` 문자열만 바꾸어 재사용하지 마세요. 새로운 데이터 종류를 선택할 때는 앱을 다시 실행하거나 새 Helper를 만들어 후처리 파이프라인을 구성합니다.

## 3. 색·깊이·점군의 관계 정리

```text
같은 카메라와 Render Product
    ├─ RGB: 픽셀의 색
    ├─ Depth: 픽셀에 보인 표면까지의 영상 평면 기준 깊이
    ├─ PointCloud: 깊이 + 카메라 내부 파라미터로 복원한 3D 위치
    └─ CameraInfo: 그 복원에 필요한 렌즈·해상도 정보
```

깊이 영상은 어두운 픽셀이 검은 재질이라는 뜻이 아닙니다. 거리를 명암으로 표시한 것입니다. 배경의 무한대 값 때문에 대비가 한쪽으로 몰릴 수 있으므로 물체·벽·바닥처럼 유한한 거리의 표면을 비교하세요.

USD 카메라는 로컬 -Z를 바라보고 +Y가 위입니다. ROS 영상의 optical frame은 +Z가 앞, +X가 영상 오른쪽, +Y가 아래입니다. `camera_1`이라는 frame 이름만 보고 USD 축과 같은 방향으로 점군을 해석하지 마세요. [Jazzy Image 메시지 정의](https://raw.githubusercontent.com/ros2/common_interfaces/jazzy/sensor_msgs/msg/Image.msg)도 이 광학 좌표와 CameraInfo의 frame 일치를 요구합니다.

두 카메라의 독립적인 CameraInfo를 발행하는 구성은 자동으로 스테레오 보정 전체를 수행하는 구성과도 다릅니다. 여기서는 시점 차이와 각 카메라의 렌더 출력에 집중합니다.

## 4. 간단한 확인 실험

`run.py`의 **`camera.CreateFocalLengthAttr(18)`만 `36`으로 바꾸고 다시 실행**해 보세요. 해상도와 카메라 위치는 유지합니다.

물체가 영상에서 더 크게 보이고 fx·fy가 약 1099.5 pixel로 두 배가 되는지 확인합니다. 중심점은 같은 해상도에서 유지되어야 합니다. 그래프의 카메라 두 개가 같은 생성 코드를 사용하므로 이 변경은 둘 다에 적용됩니다.

## 실행할 때 막히면

- **RGB 토픽은 보이지만 영상이 안 옴**: `ros2 topic info -v /camera_1/rgb`로 publisher QoS를 확인하고 RViz Reliability를 맞추세요. 렌더 초기화도 기다립니다.
- **점군에 TF 오류가 남음**: 이 실습은 TF를 만들지 않습니다. 첫 카메라 점군의 Fixed Frame을 `camera_1`로 설정하세요.
- **깊이 영상이 검거나 두 색으로만 보임**: 무한대 배경과 자동 대비를 확인하세요. RGB처럼 색상값으로 해석하지 않습니다.
- **인식 결과 토픽이 없음**: 기본 `--perception none`인지 확인하세요. 선택한 결과만 추가 발행됩니다.
- **`--frames`를 줬는데 GUI가 종료되지 않음**: GUI 종료 한도는 `--steps`입니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS 2 Cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html)에 대응하며, 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고합니다.

공식 TurtleBot 장면 대신 직접 생성한 두 물체와 카메라를 사용합니다. 주행·TF는 포함하지 않고 카메라 Helper와 출력 해석을 실습합니다. `tutorial.json`은 `verification: not_run`입니다. 수치 계산은 코드 설정에서 도출한 기대값이며 실제 GPU 렌더링·ROS 영상 수신 결과는 별도 확인이 필요합니다.
