# 32. 카메라와 LiDAR 데이터를 ROS로 내보내기

[전체 목차](../../README.md) · [이전](31-tf-odometry-joints.md) · [다음](33-project6-ros-loop.md)

## 이번 단계에서 할 일

카메라 영상이 시뮬레이터에서 보이는 것과 ROS 메시지로 전달되는 것은 서로 다른 확인 항목이다. 이번에는 GUI에서 센서 publisher를 만들고, 메시지 내용과 RViz 표시를 나누어 검사한다. 21~28단계의 센서 원리와 29~31단계의 시간·좌표계 이해가 필요하다. 초기 검사는 **정지한 장면, 낮은 해상도, 센서 하나**로 수행한다.

실행 중인 06/07 예제는 종료한다. GUI를 29단계의 Jazzy 환경에서 실행하고, 바닥·조명·불투명한 상자가 있는 센서 실습 장면을 연다. 카메라가 아무 물체도 없는 하늘을 보고 있으면 depth에서 무한대가 나와도 고장이 아니다.

## 1. 정지 카메라를 준비한다

1. Stage에서 `/World`를 선택하고 **Create > Camera**로 카메라를 만든다.
2. 이름을 `RosCamera`로 바꾼다. 경로는 `/World/RosCamera`이다.
3. 상자가 보이도록 Viewport를 배치한 뒤 카메라를 해당 뷰에 맞춘다. Viewport의 Camera 메뉴에서 `RosCamera`를 선택해 **실제 카메라 뷰**를 확인한다.
4. 처음에는 640×480, 10 Hz로 시작한다. 광각 왜곡, 모션 블러, 임의 노이즈는 기본 시험이 끝난 뒤 추가한다.
5. 카메라 앞 2 m 정도에 불투명한 상자가 있는지 확인한다. 카메라 중심이 상자 내부에 들어가지 않도록 한다.

6.0에서는 Camera Helper의 `frameSkipCount`가 deprecated이다. 센서 Prim의 `OmniSensorAPI`와 `omni:sensor:tickRate`로 주기를 지정한다. 아래 코드는 **이미 생성한 카메라**에 Script Editor에서 실행한다. `RtxCamera`로 기존 Prim을 감싸 센서 설정을 적용하며, 기존 카메라의 위치·회전을 보존한다.

```python
import omni.usd
from isaacsim.sensors.experimental.rtx import RtxCamera

stage = omni.usd.get_context().get_stage()
camera_prim = stage.GetPrimAtPath("/World/RosCamera")
assert camera_prim.IsValid(), "카메라 경로를 먼저 확인한다"
camera = RtxCamera("/World/RosCamera", tick_rate=10.0,
                   reset_xform_op_properties=False)
tick_rate = camera_prim.GetAttribute("omni:sensor:tickRate")
assert tick_rate.IsValid(), "OmniSensorAPI 적용 상태를 확인한다"
print("camera tick rate:", tick_rate.Get())
```

센서 주기는 물리 시간 기준으로 설정한다. RTX 렌더러의 처리 시간이 느리면 벽시계 기준 수신 빈도는 10 Hz보다 낮을 수 있다. [6.0.1 카메라 ROS 변경점](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_camera.html), [Multi-Tick Rendering](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html)

## 2. Camera 그래프를 자동 생성한 뒤 내부를 읽는다

**Tools > Robotics > ROS 2 OmniGraphs > Camera**를 열고 다음 값으로 생성한다.

| 항목 | 값 |
|---|---|
| Graph Path | `/World/RosCamera/ROSGraph` |
| Camera Prim | `/World/RosCamera` |
| Frame ID | `camera_optical` |
| Node Namespace | `camera` |
| 출력 | RGB, Depth, Camera Info |

생성된 그래프를 열어 RGB topicName은 `rgb`, depth는 `depth`, Camera Info는 `camera_info`로 맞춘다. 모든 Helper의 `useSystemTime`은 `False`로 둔다. Render Product 노드에서 width 640, height 480, enabled True를 확인한다. Context는 Domain ID 환경변수를 사용하도록 한다. 30단계의 clock 그래프가 없다면 하나 추가한다.

**Frame ID 입력은 TF를 자동으로 만들어 주지 않는다.** `camera_optical`은 ROS optical 좌표계이며 +Z가 시선 방향, +X가 영상 오른쪽, +Y가 영상 아래쪽이다. 카메라 Prim의 USD 축은 일반적으로 -Z 전방, +Y 위쪽이다. 두 축을 같은 회전이라고 보고 카메라의 world transform을 그대로 optical TF로 발행하지 않는다. 센서 rig 단계에서 만든 optical frame이 있다면 그 Prim을 TF source로 사용한다. 아직 TF를 만들지 않았다면 이번 단계의 Image 표시와 raw 데이터 검사를 먼저 수행하고, Camera/PointCloud의 3D 겹치기는 optical TF가 준비된 뒤 수행한다.

Play를 누른 뒤 터미널 B에서 확인한다.

```bash
ros2 topic list -t
ros2 topic info /camera/rgb --verbose
ros2 topic echo /camera/camera_info --once --qos-reliability best_effort
ros2 run rqt_image_view rqt_image_view /camera/rgb
```

이름 자동 생성 옵션이나 Namespace를 다르게 썼다면 실제 토픽 목록에 출력된 경로를 사용한다. Camera Info의 width/height는 영상과 일치해야 하고 K 행렬의 초점거리 두 값은 양수여야 한다. RGB 한 장을 얻었다는 이유만으로 depth와 Camera Info도 정상이라고 판단하지 않는다.

내부 그래프는 카메라 Prim을 Render Product와 연결하고, Helper가 후처리와 ROS 전송 파이프라인을 생성하는 구조이다. Helper 하나는 데이터 종류 하나를 담당한다. Play한 뒤 이미 만들어진 Helper의 type을 rgb에서 depth로 바꾸어 재활용하지 말고, 별도 Helper를 추가하거나 장면을 다시 연다.

## 3. RGB 수신을 수치로 검사한다

```bash
cd "$TUTORIAL_ROOT"
python3 scripts/ros_acceptance.py --mode clock --duration 15 \
  --image-topic /camera/rgb --output artifacts/ros-rgb-acceptance.json
```

이 검사는 clock 증가, 영상 수신 개수, `step × height`와 버퍼 길이, 지원하는 8비트 encoding, 최근 영상의 밝기를 확인한다. 마지막 최대 5개 프레임에 밝기가 있어야 하며, 마지막 영상 수신 후 2초가 지나면 실패한다. RGBA의 alpha만 255인 검은 영상은 밝기 검사에서 통과하지 않는다. 평균 밝기를 표본으로 확인하므로 줄무늬·부분 노이즈·왜곡까지 모두 검출하는 검사는 아니다. 원본 영상의 시각적 확인도 수행한다.

Depth는 다음처럼 별도로 확인한다.

```bash
ros2 run rqt_image_view rqt_image_view /camera/depth
ros2 topic echo /camera/depth --once --field encoding --qos-reliability best_effort
```

depth에 8비트 RGB 밝기 검사를 적용하지 않는다. `32FC1` 깊이는 미터 단위 부동소수점 데이터로 해석하며 배경에는 유효하지 않은 값이 있을 수 있다. RViz에서만 검게 보인다면 rqt로 교차 확인한다. NVIDIA도 standalone 카메라 예제의 RViz depth 검은 프레임에 대해 이 확인 방법을 안내한다. [Standalone 카메라 예제](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_python.html)

## 4. RTX LiDAR의 ROS 출력을 만든다

카메라 시험이 끝나면 25~28단계에서 저장한 RTX LiDAR 장면을 연다. 사용하는 센서는 OmniLidar 기반이어야 하며 5.1의 카메라 Prim 위에 LiDAR 속성을 붙인 옛 장면을 그대로 복사하지 않는다.

1. 센서를 바닥에서 떨어진 위치에 두고, 센서 전방의 탐지 범위 안에 벽이나 상자를 둔다.
2. 센서의 `tickRate`와 `scanRateBaseHz`를 일치시킨다. 예를 들어 `Example_Rotary`의 10 Hz 회전 설정은 tickRate도 10 Hz로 사용한다.
3. Action Graph에 `On Playback Tick`, `Isaac Create Render Product`, `ROS2 Context`, `ROS2 RTX Lidar Helper`를 추가한다. Create Render Product의 `cameraPrim`에는 이름과 달리 해당 **OmniLidar Prim**을 지정하고 enabled를 켠다. Tick의 실행 출력을 Create Render Product의 `execIn`, Create Render Product의 `execOut`을 Helper의 `execIn`에 연결한다.
4. Create Render Product의 `renderProductPath` 출력을 Helper의 `renderProductPath` 입력에, Context의 `context`를 Helper의 `context`에 연결한다. Helper는 `type=point_cloud`, `topicName=points`, `frameId=lidar`, `useSystemTime=False`로 정한다.
5. 2D 평면 LiDAR 설정을 선택한 경우에는 별도 Helper를 추가해 `type=laser_scan`, `topicName=scan`, 같은 frameId로 설정한다. 임의의 3D 회전 센서를 평면 LaserScan과 동일하게 해석하지 않는다.
6. Play한 뒤 토픽을 확인한다. RViz에서 PointCloud2 또는 LaserScan을 추가하고 Reliability Policy를 Best Effort로 맞춘다.

```bash
ros2 topic list -t
ros2 topic info /points --verbose
ros2 topic echo /scan --once --field range_max --qos-reliability best_effort
python3 scripts/ros_acceptance.py --mode clock --duration 15 \
  --scan-topic /scan --output artifacts/ros-scan-acceptance.json
```

마지막 명령은 **평면 LaserScan을 실제로 발행하는 장면에서만** 실행한다. PointCloud2를 `/scan`이라는 이름으로 발행해도 자료형이 달라 이 검사에 사용할 수 없다. 본 검사기는 유한한 거리 반환이 있는지 검사하며, 복잡한 3D 점군의 완전한 회전 범위나 보정 정확도까지 검증하지 않는다. [RTX Helper 입력 정의](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.ros2.nodes/docs/ogn/OgnROS2RtxLidarHelper.html)

## 완료 기준과 실패 진단

| 증상 | 원인을 나눠 확인할 방법 |
|---|---|
| Isaac Sim 영상도 검음 | 조명, 렌즈 방향, clipping, GPU 메모리, 렌더 워밍업 |
| Isaac Sim 정상, ROS 영상 없음 | Render Product enabled, Helper, Context, Play, QoS |
| RGB 정상, depth만 검음 | encoding·실제 깊이 값·무한 배경을 확인하고 rqt로 비교 |
| 점군 방향이 반대임 | 센서 frame의 축과 TF 회전 |
| scan 일부만 나타남 | tickRate/scanRateBaseHz, 회전 완료 여부, 센서 프로파일 |
| 영상 켜면 로봇이 느려짐 | RTF와 VRAM을 확인하고 해상도·센서 수·주기를 낮춤 |

한 센서씩 실제 데이터를 확인하고 해당 acceptance JSON을 남기면 완료한다. 센서가 나오지 않는 상태를 timeout이나 빈 배열로 조용히 무시하지 않는다. 과제로 RGB의 조명을 끈 실행과 정상 실행의 JSON을 비교하되, 평균 밝기 검사만으로 모든 렌더링 오류를 검출할 수 없는 이유도 함께 기록한다.
