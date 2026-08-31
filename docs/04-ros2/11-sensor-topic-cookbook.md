# 카메라, RTX LiDAR, IMU의 ROS 2 토픽

이 장에서는 센서 prim에서 ROS 2 메시지가 나올 때까지의 render/physics pipeline을 구성하고, 메시지 내용·주기·좌표계를 검증한다.

## 센서별 실행 기반을 구분하다

| 센서 | 계산 기반 | 대표 ROS 메시지 | 주의점 |
|---|---|---|---|
| RGB/depth camera | RTX renderer + render product | `Image`, `CameraInfo`, `PointCloud2` | 렌더 step이 필요하다. |
| RTX LiDAR | RTX Sensor renderer + `OmniLidar` | `LaserScan`, `PointCloud2` | full scan 주기와 frame 주기가 다르다. |
| IMU/contact | PhysX step | `Imu` 또는 사용자 메시지 | sensor frequency는 physics rate를 넘지 못한다. |

## 1. 카메라 prim과 render product를 만들다

GUI에서는 `Create > Camera`로 카메라를 만든다. 카메라를 로봇 link 아래로 이동하고 local transform을 설정하면 link 움직임을 따라간다. Viewport 왼쪽 위 Camera 메뉴에서 해당 prim을 선택해 장착 방향을 먼저 확인한다.

ROS 2 RGB publisher 그래프에는 다음을 둔다.

- `On Playback Tick`
- `ROS 2 Context`
- `Isaac Create Render Product`
- `ROS 2 Camera Helper`

예시 속성은 다음과 같다.

```text
Isaac Create Render Product.cameraPrim = /World/Robot/camera_link/Camera
ROS 2 Camera Helper.type = rgb
ROS 2 Camera Helper.topicName = /camera/color/image_raw
ROS 2 Camera Helper.frameId = camera_color_optical_frame
```

`ROS 2 Camera Helper`는 실행 시 `/Render/PostProcessing/SDGPipeline`을 세션에 생성한다. 이 내부 graph는 Stage에 영구 저장되지 않는다. helper의 `type`으로 pipeline이 생성된 뒤 type을 바꿔 재사용하지 말고, 새 helper를 만들거나 Stage를 다시 연다.

메뉴 단축 경로 `Tools > Robotics > ROS 2 OmniGraphs > Camera`에서 RGB, depth, point cloud, camera info를 선택할 수도 있다.

## 2. 이미지와 CameraInfo를 검증하다

```bash
ros2 topic list -t | grep camera
ros2 topic info /camera/color/image_raw -v
ros2 topic hz /camera/color/image_raw
ros2 topic echo /camera/color/camera_info --once
```

RViz2 또는 `rqt_image_view`를 사용한다.

```bash
ros2 run rqt_image_view rqt_image_view /camera/color/image_raw
rviz2
```

RViz2에서 Image display의 Reliability를 publisher와 맞춘다. 센서 데이터 preset은 보통 Best Effort이므로 RViz2가 Reliable이면 연결되지 않는다.

`CameraInfo`의 내부 파라미터는 해상도와 USD camera aperture/focal length에서 계산된다.

\[
f_x = \frac{W f}{A_h},\qquad
f_y = \frac{H f}{A_v},\qquad
c_x = W/2,\qquad c_y = H/2
\]

5.1 release note에는 `CameraInfo`의 `fy`가 항상 `fx`로 설정되던 문제가 수정되었다. 따라서 실제 출력의 K/P 행렬을 소비 노드에서 다시 확인한다.

## 3. depth, point cloud, ground truth를 발행하다

Camera Helper 하나는 한 data type만 담당한다. 동일한 render product에 helper를 여러 개 연결한다.

```text
type=depth          → /camera/depth/image
type=point_cloud    → /camera/depth/points
type=semantic_segmentation / instance_segmentation
type=bbox_2d_tight / bbox_2d_loose / bbox_3d
```

bounding box 출력은 semantic label이 있는 Stage와 `vision_msgs`가 필요하다.

```bash
sudo apt install -y ros-jazzy-vision-msgs
```

depth가 흑백 두 덩어리로만 보이면 무한히 먼 배경 때문에 display range가 압축된 경우가 많다. 카메라가 벽과 바닥을 포함하도록 시야를 조정하고 RViz2 depth display 범위를 확인한다.

## 4. 카메라 노이즈를 추가하다

공식 5.1 카메라 노이즈 튜토리얼은 Replicator annotator/augmentation을 카메라 pipeline에 추가하는 흐름을 사용한다. 실제 노이즈 모델은 다음 요소를 분리해 설계한다.

- shot/read noise: 밝기에 따라 달라지는 pixel noise
- lens distortion: OpenCV pinhole 또는 fisheye 계수
- blur/exposure: 움직임과 shutter 시간
- dropout/quantization: depth 센서의 유효 범위와 양자화

노이즈가 있는 image topic과 ground-truth topic을 서로 다른 이름으로 유지한다.

```text
/camera/color/image_raw_gt
/camera/color/image_raw_noisy
```

알고리즘 정확도를 평가할 때 두 토픽의 header stamp와 frame ID가 같아야 한다.

## 5. RTX LiDAR를 추가하다

Isaac Sim 5.1의 표준 RTX LiDAR는 `OmniLidar` prim이다. 구형 Camera prim의 `sensorModelConfig` JSON 방식은 deprecated이다. GUI에서는 다음을 사용한다.

```text
Create > Sensors > RTX Lidar > NVIDIA > Example Rotary 2D
Create > Sensors > RTX Lidar > NVIDIA > Example Rotary
```

LiDAR prim을 robot의 `base_scan` link 아래로 옮기고 local transform을 0으로 만든다. Action Graph에 각각 render product와 helper를 연결한다.

```text
On Playback Tick
  → Isaac Run One Simulation Frame
  → Isaac Create Render Product(cameraPrim=/.../OmniLidar)
  → ROS 2 RTX Lidar Helper
```

2D LiDAR helper:

```text
type=laser_scan
topicName=/scan
frameId=base_scan
```

3D LiDAR helper:

```text
type=point_cloud
topicName=/point_cloud
frameId=base_scan
publishFullScan=true 또는 false를 용도에 맞게 선택한다.
```

rotary LiDAR의 `LaserScan`은 한 바퀴가 완성될 때 발행된다. 10 Hz 회전, 60 Hz render step이면 약 6 frame에 한 메시지가 생성된다. point cloud는 helper의 `Publish Full Scan`에 따라 매 frame 또는 누적 full scan 단위로 발행한다.

```bash
ros2 topic hz /scan
ros2 topic echo /scan --once --field header
ros2 topic echo /point_cloud --once --field width
```

RViz2에서 Fixed Frame을 `base_scan` 또는 연결된 상위 frame으로 설정한 다음 LaserScan과 PointCloud2 display를 추가한다.

## 6. Python에서 5.1 RTX LiDAR를 생성하다

다음 코드는 Script Editor 또는 `SimulationApp` 생성 이후의 standalone 본문에서 사용한다.

```python
import numpy as np
from isaacsim.sensors.rtx import LidarRtx

lidar = LidarRtx(
    prim_path='/World/Robot/base_scan/lidar',
    translation=np.array([0.0, 0.0, 0.0]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),  # wxyz
    config_file_name='Example_Rotary',
    **{'omni:sensor:Core:scanRateBaseHz': 20},
)

# LidarRtx는 OmniLidar를 만들고 render product를 붙이는 고수준 wrapper이다.
print(lidar.get_data())
```

저수준 command도 사용할 수 있다.

```python
import omni.kit.commands
from pxr import Gf

_, sensor = omni.kit.commands.execute(
    'IsaacSensorCreateRtxLidar',
    translation=Gf.Vec3d(0, 0, 1),
    orientation=Gf.Quatd(1, 0, 0, 0),
    path='/World/lidar',
    parent=None,
    config='Example_Rotary',
    visiblity=False,  # 5.1 command signature의 철자를 그대로 사용한다.
    variant=None,
    force_camera_prim=False,
    **{'omni:sensor:Core:scanRateBaseHz': 20},
)
```

`force_camera_prim=True`는 deprecated Camera prim 호환 경로이므로 새 자산에서는 사용하지 않는다.

## 7. IMU를 만들고 발행하다

robot의 `imu_link`를 선택한 뒤 `Create > Sensors > Imu Sensor`를 실행한다. Action Graph에 다음을 연결한다.

```text
On Playback Tick → Isaac Simulation Gate(step=N) → Isaac Read IMU
                                             → ROS 2 Publish Imu
```

```text
Isaac Read IMU.imuPrim=/World/Robot/imu_link/Imu_Sensor
ROS 2 Publish Imu.topicName=/imu/data
ROS 2 Publish Imu.frameId=imu_link
```

60 Hz physics에서 `step=2`이면 약 30 Hz이다. camera/RTX helper의 `frameSkipCount=N`은 보통 `N+1` frame마다 발행한다. 실제 주기는 반드시 측정한다.

```bash
ros2 topic hz /imu/data
ros2 topic echo /imu/data --once
```

정지한 IMU에서 linear acceleration z 성분의 부호와 크기는 sensor orientation과 gravity 포함 여부 설정에 따라 달라진다. 기대값을 정하기 전에 frame orientation과 sensor property를 기록한다.

## 8. 주기, QoS, 대역폭을 함께 설계하다

```bash
ros2 topic bw /camera/color/image_raw
ros2 topic bw /point_cloud
ros2 topic info /scan -v
```

예를 들어 1920×1080 RGB8 30 Hz 원시 영상은 payload만 약 186 MB/s이다. 해상도, 주기, 활성 helper 수를 줄이고 사용하지 않는 render product는 `enabled=False`로 둔다. sensor QoS는 Best Effort/Volatile을 기본으로 검토하고, 정적 calibration 정보는 Reliable/Transient Local이 적절할 수 있다.

## 완료 체크

- [ ] 카메라 영상과 `CameraInfo` stamp/frame이 일치한다.
- [ ] depth의 단위와 invalid value를 확인했다.
- [ ] RTX LiDAR가 `OmniLidar` prim으로 생성되었다.
- [ ] `/scan`, `/point_cloud`, `/imu/data`의 실제 Hz를 측정했다.
- [ ] RViz2 QoS가 publisher와 호환된다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html)
- [Isaac Sim 5.1.0 — Add Noise to Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html)
- [Isaac Sim 5.1.0 — Publishing Camera’s Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html)
- [Isaac Sim 5.1.0 — RTX Lidar Sensors with ROS 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html)
- [Isaac Sim 5.1.0 — RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [Isaac Sim 5.1.0 — ROS2 Setting Publish Rates](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html)
