# 5. Gazebo 센서와 RViz 시각화

이 장에서는 하나의 이동 로봇에 wheel odometry, IMU, 네 종류의 카메라, 2D/3D LiDAR를 붙이고 ROS 2 토픽과 TF가 실제로 이어지는지 확인한다. 예제는 **ROS 2 Humble + Gazebo Classic 11 + `gazebo_ros_pkgs`** 전용이다. 새 Gazebo의 `ros_gz` 플러그인 이름과 섞어 쓰면 안 된다.

예제 모델은 다음 파일에 있다.

```text
ros2_ws/src/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro
```

## 5.1 학습 목표

이 장을 끝내면 다음을 할 수 있다.

- URDF 링크에 Gazebo의 `<sensor>` 요소를 추가한다.
- Gazebo Transport의 센서 값을 `gazebo_ros_pkgs` 플러그인으로 ROS 2 메시지로 변환한다.
- 각 메시지의 `header.frame_id`와 URDF TF 트리의 관계를 설명한다.
- RViz에서 odometry 경로, IMU 자세, 영상, LaserScan, PointCloud2를 확인한다.
- 토픽이 보이지 않거나 RViz가 데이터를 받지 못할 때 frame, QoS, subscriber 유무를 순서대로 점검한다.

## 5.2 센서 모델을 가볍게 나누는 `sensor_profile`

카메라와 3D LiDAR는 CPU와 GPU를 많이 사용한다. 특히 `wideanglecamera`는 내부적으로 cubemap을 렌더링하므로 일반 pinhole 카메라보다 무겁다. 그래서 xacro 인자 하나로 필요한 센서만 생성한다.

| 프로필 | 생성되는 센서 | 추천 용도 |
|---|---|---|
| `all` | IMU, mono, stereo, RGBD, fisheye, 2D/3D LiDAR | 전체 기능 확인, 기본값 |
| `cameras` | IMU와 네 종류의 카메라 | 영상 실습 |
| `lidars` | IMU와 2D/3D LiDAR | LiDAR 실습, GPU가 약한 환경 |
| `minimal` | wheel odom과 IMU | TF·odometry 점검, headless 환경 |

전체 센서로 시작한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all
```

프레임이 끊기거나 Gazebo의 real-time factor가 지나치게 낮으면 먼저 `lidars` 또는 `cameras`로 나누어 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars
```

> `sensor_profile`을 바꾸면 선택되지 않은 센서의 링크도 URDF에서 사라진다. 따라서 해당 링크의 TF와 토픽이 없는 것은 정상이다.

## 5.3 센서 데이터가 ROS 2까지 오는 과정

센서마다 세 층을 구분하면 설정을 이해하기 쉽다.

1. URDF의 `link`와 `joint`가 센서의 장착 위치와 TF를 정의한다.
2. `<gazebo reference="...">` 안의 SDF `<sensor>`가 Gazebo에서 측정값을 만든다.
3. 센서 안의 `<plugin>`이 측정값을 ROS 2 메시지로 발행한다.

예를 들어 2D LiDAR의 핵심은 다음과 같다.

```xml
<gazebo reference="lidar_2d_link">
  <sensor name="lidar_2d_sensor" type="ray">
    <ray>...</ray>
    <plugin name="lidar_2d_ros" filename="libgazebo_ros_ray_sensor.so">
      <ros>
        <remapping>~/out:=scan</remapping>
      </ros>
      <output_type>sensor_msgs/LaserScan</output_type>
      <frame_name>lidar_2d_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

`reference`와 `frame_name`은 역할이 다르다. `reference`는 센서를 어느 Gazebo 링크에 붙일지 정하고, `frame_name`은 ROS 메시지 헤더에 기록할 프레임을 정한다. 둘을 무심코 다른 이름으로 쓰면 데이터는 발행되지만 RViz에서 `No transform` 오류가 난다.

## 5.4 토픽과 프레임 계약

`all` 프로필에서 다음 인터페이스가 생성된다. 카메라의 `CameraInfo` 토픽도 함께 확인해야 카메라 보정값과 point cloud 투영을 검사할 수 있다.

| 기능 | ROS 2 토픽 | 메시지 타입 | `frame_id` | 주기 |
|---|---|---|---|---:|
| 속도 명령 | `/cmd_vel` | `geometry_msgs/msg/Twist` | 없음 | 입력 |
| wheel odom | `/odom` | `nav_msgs/msg/Odometry` | `odom`, child `base_footprint` | 50 Hz |
| wheel joint | `/joint_states` | `sensor_msgs/msg/JointState` | 없음 | 50 Hz |
| 누적 경로 | `/wheel_odom_path` | `nav_msgs/msg/Path` | `odom` | odom 연동 |
| IMU | `/imu/data` | `sensor_msgs/msg/Imu` | `imu_link` | 100 Hz |
| mono 영상 | `/camera/image_raw` | `sensor_msgs/msg/Image` (`mono8`) | `camera_optical_frame` | 15 Hz |
| mono 정보 | `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | `camera_optical_frame` | 15 Hz |
| stereo 왼쪽 | `/stereo/left/image_raw` | `sensor_msgs/msg/Image` | `stereo_camera_optical_frame` | 10 Hz |
| stereo 오른쪽 | `/stereo/right/image_raw` | `sensor_msgs/msg/Image` | `stereo_camera_optical_frame` | 10 Hz |
| stereo 정보 | `/stereo/{left,right}/camera_info` | `sensor_msgs/msg/CameraInfo` | `stereo_camera_optical_frame` | 10 Hz |
| RGBD RGB | `/rgbd/image_raw` | `sensor_msgs/msg/Image` | `rgbd_camera_optical_frame` | 10 Hz |
| RGBD RGB 정보 | `/rgbd/camera_info` | `sensor_msgs/msg/CameraInfo` | `rgbd_camera_optical_frame` | 10 Hz |
| RGBD depth | `/rgbd/depth/image_raw` | `sensor_msgs/msg/Image` (`32FC1`) | `rgbd_camera_optical_frame` | 10 Hz |
| RGBD depth 정보 | `/rgbd/depth/camera_info` | `sensor_msgs/msg/CameraInfo` | `rgbd_camera_optical_frame` | 10 Hz |
| RGBD point cloud | `/rgbd/points` | `sensor_msgs/msg/PointCloud2` | `rgbd_camera_optical_frame` | 10 Hz |
| fisheye 영상 | `/fisheye/image_raw` | `sensor_msgs/msg/Image` | `fisheye_camera_optical_frame` | 10 Hz |
| fisheye 정보 | `/fisheye/camera_info` | `sensor_msgs/msg/CameraInfo` | `fisheye_camera_optical_frame` | 10 Hz |
| 2D LiDAR | `/scan` | `sensor_msgs/msg/LaserScan` | `lidar_2d_link` | 15 Hz |
| 3D LiDAR | `/points` | `sensor_msgs/msg/PointCloud2` | `lidar_3d_link` | 10 Hz |

현재 그래프에서 타입을 한 번에 검사한다.

```bash
for topic in \
  /odom /wheel_odom_path /imu/data \
  /camera/image_raw \
  /stereo/left/image_raw /stereo/right/image_raw \
  /rgbd/image_raw /rgbd/depth/image_raw /rgbd/points \
  /fisheye/image_raw /scan /points; do
  printf '%-32s %s\n' "$topic" "$(ros2 topic type "$topic")"
done
```

빈 칸이 나오면 그 토픽에 대응하는 프로필이 켜졌는지 먼저 확인한다.

## 5.5 Wheel odometry와 주행 경로

### 왜 이것을 wheel odom이라고 부르는가

`libgazebo_ros_diff_drive.so`의 `<odometry_source>`는 다음 두 값을 사용한다.

- `0`: 좌·우 바퀴 joint의 회전량을 적분하는 encoder odometry
- `1`: Gazebo가 알고 있는 모델의 world pose를 사용하는 ground truth에 가까운 odometry

이 예제는 `0`을 사용한다. 따라서 바퀴가 미끄러지면 `/odom`도 실제 world pose와 어긋난다. 이 차이가 실제 로봇의 wheel encoder 오차를 설명하는 좋은 실습 재료다.

키보드로 원호를 그리며 주행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

`i`로 전진하고 `j`, `l`로 회전한다. `u`, `o`, `m`, `.` 키를 사용하면 전진 또는 후진과 회전을 함께 주어 원호를 만들 수 있다. 다른 터미널에서 값을 확인한다.

```bash
ros2 topic hz /odom
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_footprint
```

RViz에서 다음을 확인한다.

1. **Global Options → Fixed Frame**을 `odom`으로 둔다.
2. **Add → Path**를 추가하고 Topic을 `/wheel_odom_path`로 고른다.
3. Line Style을 `Lines`, Line Width를 `0.03` 정도로 설정한다.
4. **Add → Odometry**도 추가해 Topic을 `/odom`, Keep을 `200`으로 둔다.
5. 로봇을 원형으로 주행시켜 Path의 선과 Odometry 화살표가 함께 누적되는지 본다.

`/odom`은 움직이는데 Path가 비어 있다면 다음을 구분해서 본다.

```bash
ros2 topic info /wheel_odom_path -v
ros2 topic echo /wheel_odom_path --once
```

Path 노드의 subscriber가 `/odom`에 연결되어 있고 `/wheel_odom_path` publisher가 하나 있어야 한다.

### Wheel TF를 누가 발행하는가

차동 구동 플러그인의 `<publish_wheel_tf>`는 `false`다. 대신 `libgazebo_ros_joint_state_publisher.so`가 `/joint_states`를 발행하고 `robot_state_publisher`가 URDF의 실제 부모 관계인 `base_link → left_wheel_link/right_wheel_link`를 계산한다. 이렇게 해야 `base_footprint → wheel` 같은 잘못된 TF나 중복 TF publisher를 피할 수 있다.

```bash
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo base_link left_wheel_link
```

## 5.6 IMU

IMU는 `libgazebo_ros_imu_sensor.so`를 사용한다. xacro에서 각 축의 angular velocity와 linear acceleration에 Gaussian noise를 넣었다. `<initial_orientation_as_reference>false>`는 시작 자세가 아니라 world를 orientation 기준으로 쓰는 REP-145 동작을 선택한다.

```bash
ros2 topic hz /imu/data
ros2 topic echo /imu/data --once
ros2 run tf2_ros tf2_echo base_link imu_link
```

평평한 바닥에 정지해 있어도 가속도계의 Z 값은 중력에 대응하는 약 `+9.8 m/s²` 부근이고 작은 잡음이 섞인다. 회전시키면 angular velocity의 Z와 orientation quaternion이 변한다.

RViz에서 IMU 자세를 직접 보려면 Humble의 IMU RViz 플러그인이 필요하다.

```bash
sudo apt install ros-humble-rviz-imu-plugin
```

RViz에서 **Add → rviz_imu_plugin → Imu**를 추가하고 Topic을 `/imu/data`로 둔다. 플러그인 이름이 보이지 않으면 RViz를 완전히 종료한 뒤 다시 시작한다. TF 프레임이 보이기만 하면 되는 실습에서는 **TF** Display에서 `imu_link` 축을 켜도 된다. 다만 TF 축은 장착 자세를 보여 줄 뿐 IMU 메시지 자체를 구독하지 않으므로, 데이터 검증을 대신하지는 않는다.

## 5.7 카메라

### 5.7.1 Mono camera

일반 `<sensor type="camera">`에 `<format>L8</format>`을 사용한다. `libgazebo_ros_camera.so`는 이를 ROS의 `mono8` encoding으로 변환한다.

```bash
ros2 topic echo /camera/image_raw --field encoding --once
ros2 topic hz /camera/image_raw
```

RViz에서 **Add → Image**를 추가하고 Topic을 `/camera/image_raw`로 둔다. Image Display는 Fixed Frame과 무관하게 영상만 확인할 수 있다. 3D 장면에 카메라 frustum까지 겹쳐 보려면 **Camera** Display를 추가하고 같은 image topic을 선택한다. 이때 `/camera/camera_info`와 `camera_optical_frame` TF가 모두 필요하다.

### 5.7.2 Stereo camera

Gazebo의 `multicamera` 센서 안에 `left`, `right` 카메라를 두었다. 두 영상은 같은 sensor update에서 생성되므로 별도의 카메라 두 개보다 시간 동기화가 쉽다.

```bash
ros2 topic hz /stereo/left/image_raw
ros2 topic hz /stereo/right/image_raw
ros2 topic echo /stereo/left/camera_info --once
```

RViz에서 Image Display를 두 개 만들고 왼쪽과 오른쪽 토픽을 각각 고른다. 가까운 물체가 두 영상에서 수평으로 이동해 보이는 시차를 확인한다.

이 예제는 **raw stereo 영상 확인**을 위한 최소 구성이다. 두 Gazebo camera pose의
간격은 0.08 m이며 `<hack_baseline>0.08</hack_baseline>`을 함께 설정해 CameraInfo
projection matrix에도 baseline이 반영되게 했다. 다만 `gazebo_ros_camera`의 multicamera 출력은
두 영상에 하나의 공통 `stereo_camera_optical_frame`을 사용한다. 정밀한 disparity/depth
계산을 하려면 좌·우 optical TF, 각 카메라의 보정 행렬, rectification을 실제 센서 사양에
맞춰 별도로 구성해야 한다.

### 5.7.3 RGBD camera

Gazebo의 `<sensor type="depth">` 하나와 `libgazebo_ros_camera.so`가 다음 네 종류의 데이터를 동시에 만든다.

- RGB: `/rgbd/image_raw`
- 깊이: `/rgbd/depth/image_raw`
- RGB/depth 보정 정보: `/rgbd/camera_info`, `/rgbd/depth/camera_info`
- 색이 포함된 point cloud: `/rgbd/points`

```bash
ros2 topic echo /rgbd/depth/image_raw --field encoding --once
ros2 topic hz /rgbd/points
ros2 topic echo /rgbd/points --field header --once
```

RViz에서는 다음처럼 본다.

1. Image Display 두 개에 `/rgbd/image_raw`와 `/rgbd/depth/image_raw`를 지정한다.
2. **PointCloud2** Display에 `/rgbd/points`를 지정한다.
3. Size (Pixels)를 `2` 또는 `3`, Style을 `Points`, Color Transformer를 `RGB8`로 둔다.
4. Fixed Frame은 `odom` 또는 `base_link`를 사용한다.

Point cloud가 카메라 앞이 아니라 옆이나 뒤로 뻗으면 `rgbd_camera_optical_frame` 변환부터 검사한다.

```bash
ros2 run tf2_ros tf2_echo base_link rgbd_camera_optical_frame
```

ROS optical frame은 `+Z`가 전방, `+X`가 오른쪽, `+Y`가 아래쪽이다. Gazebo 카메라 링크의 `+X` 전방 규약과 다르므로 xacro에 `roll=-π/2, yaw=-π/2`인 fixed joint를 두었다.

### 5.7.4 Fisheye camera

단순히 pinhole 영상에 왜곡 계수를 넣은 것이 아니라 Gazebo 11의 `<sensor type="wideanglecamera">`와 `equidistant` lens를 사용한다. 수평 FOV는 약 180°이고 cubemap texture 크기는 512다.

```bash
ros2 topic hz /fisheye/image_raw
ros2 topic echo /fisheye/image_raw --field width --once
```

RViz에서 Image Display의 Topic을 `/fisheye/image_raw`로 둔다. 일반 카메라와 비교해 영상 가장자리에서 직선이 크게 휘고 훨씬 넓은 시야가 보이면 정상이다.

주의할 점이 있다. `libgazebo_ros_camera.so`가 만드는 `CameraInfo`는 기본적으로 pinhole/`plumb_bob` 형태다. Gazebo의 `equidistant` lens mapping 자체를 완전한 ROS fisheye calibration으로 바꾸어 주지는 않는다. 영상 시각화에는 문제가 없지만 OpenCV fisheye 보정이나 정밀 투영에 쓰려면 실제 `equidistant` calibration을 발행하는 별도 노드 또는 커스텀 플러그인이 필요하다.

## 5.8 2D와 3D LiDAR

두 센서 모두 Gazebo의 CPU `ray` 센서와 `libgazebo_ros_ray_sensor.so`를 사용한다. 차이는 수직 scan 채널과 ROS 출력 타입이다.

### 2D LiDAR

수평 720 sample, 360° scan을 `sensor_msgs/msg/LaserScan`으로 발행한다.

```bash
ros2 topic hz /scan
ros2 topic echo /scan --field ranges --once
ros2 run tf2_ros tf2_echo base_link lidar_2d_link
```

RViz에서 **LaserScan** Display를 추가한다.

- Topic: `/scan`
- Reliability: `Best Effort` (제공 RViz 설정의 호환성 우선값)
- Style: `Points`
- Size (m): `0.03`
- Decay Time: `0.2`

Gazebo에 box나 cylinder를 놓고 로봇을 회전시켰을 때 점들이 장애물 표면에 붙어 움직이는지 확인한다.

### 3D LiDAR

수평 360 sample과 수직 16 channel을 조합해 `sensor_msgs/msg/PointCloud2`로 발행한다.

```bash
ros2 topic hz /points
ros2 topic echo /points --field width --once
ros2 run tf2_ros tf2_echo base_link lidar_3d_link
```

RViz에서 **PointCloud2** Display를 추가한다.

- Topic: `/points`
- Reliability: `Best Effort` (제공 RViz 설정의 호환성 우선값)
- Style: `Points`
- Size (Pixels): `2`
- Color Transformer: `AxisColor`
- Axis: `Z`

3D LiDAR의 point cloud와 RGBD의 `/rgbd/points`는 이름이 비슷하지만 서로 다른 센서다. RViz Display 이름도 `3D LiDAR`와 `RGBD Points`처럼 명확히 바꾸어 두면 혼동이 줄어든다.

## 5.9 QoS를 반드시 확인하기

RViz의 Topic 목록에 이름은 보이는데 화면이 비어 있다면 QoS가 맞지 않을 수 있다. 이 튜토리얼이 기준으로 삼는 Humble `gazebo_ros_pkgs`의 camera, IMU, ray sensor publisher는 기본적으로 **Reliable + Volatile**로 생성된다. 제공하는 `sensors.rviz`는 subscriber 쪽 Reliability를 `Best Effort`로 요청한다. Reliable publisher는 Best Effort subscriber의 요청을 만족하므로 이 조합은 정상 연결되며, 나중에 센서 publisher를 Best Effort로 바꾸어도 RViz 설정을 그대로 쓸 수 있다.

실행 환경의 실제 QoS가 문서보다 우선이다. 다음 명령으로 publisher와 subscriber를 직접 확인한다.

```bash
ros2 topic info /scan -v
ros2 topic info /rgbd/points -v
ros2 topic info /imu/data -v
```

출력에서 확인할 항목은 다음과 같다.

- Publisher count가 1 이상인가?
- Reliability가 RViz Display 설정과 같은가?
- Durability가 `VOLATILE`인가?
- Topic type이 RViz Display가 기대하는 타입과 같은가?

수동으로 RViz Display를 추가할 때도 우선 `Best Effort`를 고르면 두 종류 publisher에 모두 연결하기 쉽다. 손실 없는 전달을 실험하려면 publisher가 Reliable인지 확인한 뒤 RViz도 Reliable로 올린다. Reliable publisher에 Best Effort subscriber는 연결될 수 있지만, 반대 조합인 Best Effort publisher와 Reliable subscriber는 호환되지 않는다.

## 5.10 TF 전체 점검

센서 데이터는 값만 맞아서는 부족하다. 모든 header frame이 `odom`까지 연결되어야 RViz의 한 장면에 겹쳐 보인다.

```text
odom
└── base_footprint                 (diff drive plugin)
    └── base_link                  (robot_state_publisher, fixed joint)
        ├── imu_link
        ├── camera_link ── camera_optical_frame
        ├── stereo_camera_link ── stereo_camera_optical_frame
        ├── rgbd_camera_link ── rgbd_camera_optical_frame
        ├── fisheye_camera_link ── fisheye_camera_optical_frame
        ├── lidar_2d_link
        └── lidar_3d_link
```

현재 TF를 PDF로 저장하려면 다음을 실행한다.

```bash
ros2 run tf2_tools view_frames
```

`frames.pdf`에서 센서 프레임이 두 번 발행되거나 끊겨 있지 않은지 확인한다. 특정 센서만 빠르게 확인할 때는 다음처럼 한다.

```bash
ros2 run tf2_ros tf2_echo odom camera_optical_frame
ros2 run tf2_ros tf2_echo odom lidar_3d_link
```

`Invalid frame ID`가 나오면 sensor profile과 `robot_state_publisher` 실행 여부를 확인한다. TF는 있는데 `Extrapolation into the future`가 반복되면 모든 노드의 `use_sim_time`이 `true`인지 확인한다.

```bash
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /rviz2 use_sim_time
```

## 5.11 성능 조정

센서 부하는 대략 `update_rate × sample 수 × 렌더링 해상도`에 비례한다. 시뮬레이션이 느리면 한 번에 모든 값을 무작정 줄이지 말고 병목을 분리한다.

1. `sensor_profile:=minimal`에서 물리와 wheel odom이 실시간에 가까운지 본다.
2. `lidars`를 켜고 3D LiDAR의 horizontal/vertical samples 또는 update rate를 줄인다.
3. `cameras`를 켜고 영상 width/height, update rate를 줄인다.
4. fisheye의 `env_texture_size`를 512에서 256으로 줄여 비교한다.
5. Gazebo GUI의 sensor visualization은 추가 렌더링 비용이 있으므로 필요하지 않으면 `<visualize>false>`로 둔다.

다음 값은 교육용으로 의도적으로 낮춘 설정이다.

| 센서 | 주요 비용 설정 |
|---|---|
| mono | 320×240, 15 Hz |
| stereo | 320×240 두 장, 10 Hz |
| RGBD | 320×240, 10 Hz + point cloud |
| fisheye | 320×240, 10 Hz, cubemap 512 |
| 2D LiDAR | 720 ray, 15 Hz |
| 3D LiDAR | 360×16 ray, 10 Hz |

## 5.12 문제 해결 체크리스트

### 토픽 자체가 없다

```bash
ros2 topic list | sort
ros2 node list
```

- 원하는 센서가 현재 profile에 포함되는가?
- Gazebo 터미널에 `Failed to load plugin`이 있는가?
- `ros-humble-gazebo-plugins`가 설치되어 있는가?
- `gzserver`가 `libgazebo_ros_init.so`와 ROS factory를 사용해 시작되었는가?

### 토픽은 있지만 `hz`가 0이다

카메라 계열은 subscriber가 생긴 뒤 활성화되는 구성을 만날 수 있다. 먼저 RViz Image/Camera Display 또는 다음 명령으로 subscriber를 붙인다.

```bash
ros2 topic hz /camera/image_raw
```

Gazebo가 pause 상태인지도 확인한다. `/clock`이 증가하지 않으면 센서 timestamp도 진행하지 않는다.

```bash
ros2 topic hz /clock
```

### RViz에 `No transform`이 나온다

메시지의 frame을 먼저 본다.

```bash
ros2 topic echo /scan --field header --once
ros2 run tf2_ros tf2_echo odom lidar_2d_link
```

오탈자를 가리기 위해 Fixed Frame을 센서 frame으로 바꾸는 것은 최종 해결이 아니다. `odom`에서 센서 frame까지 TF가 이어지도록 URDF, `frame_name`, robot_state_publisher를 바로잡아야 한다.

### 영상이 검거나 fisheye가 매우 느리다

- 카메라가 장애물 내부에 장착되지 않았는지 Gazebo GUI에서 본다.
- `<clip><near>`가 지나치게 큰지 확인한다.
- headless 렌더링 환경에서 OGRE/OpenGL이 동작하는지 확인한다.
- fisheye만 느리면 `env_texture_size`와 update rate를 먼저 낮춘다.

### PointCloud2는 오지만 색이나 모양이 이상하다

- `/points`와 `/rgbd/points`를 혼동하지 않았는지 확인한다.
- RGBD는 `Color Transformer=RGB8`, 3D LiDAR는 `AxisColor`로 먼저 본다.
- optical frame 회전과 LiDAR frame TF를 각각 확인한다.
- RViz의 Fixed Frame을 `odom`으로 두고 `use_sim_time=true`인지 확인한다.

## 5.13 더 해 볼 실험

1. 2D LiDAR의 Gaussian noise 표준편차를 `0.01`에서 `0.10`으로 바꾸고 벽 표면 점 분포를 비교한다.
2. wheel friction을 낮춘 뒤 제자리 회전하여 Gazebo world pose와 encoder odom 경로가 얼마나 벌어지는지 본다.
3. RGBD의 `<max_depth>`를 줄이고 point cloud가 잘리는 위치를 확인한다.
4. fisheye lens type을 `stereographic`, `equisolid_angle`, `orthographic`으로 바꾸어 같은 장면을 비교한다.
5. 3D LiDAR의 vertical sample을 16에서 4, 32로 바꾸고 CPU 사용량과 수직 해상도의 관계를 측정한다.

## 5.14 사용한 Gazebo Classic 플러그인

| 기능 | 파일명 | 핵심 SDF 태그 |
|---|---|---|
| 차동 구동 + wheel odom | `libgazebo_ros_diff_drive.so` | `left_joint`, `right_joint`, `odometry_source`, `publish_odom_tf` |
| wheel joint state | `libgazebo_ros_joint_state_publisher.so` | 반복 가능한 `joint_name`, `update_rate` |
| IMU | `libgazebo_ros_imu_sensor.so` | `~/out` remap, `frame_name`, `initial_orientation_as_reference` |
| mono/stereo/RGBD/fisheye | `libgazebo_ros_camera.so` | `camera_name`, `frame_name`; sensor type에 따라 출력 자동 확장 |
| 2D/3D LiDAR | `libgazebo_ros_ray_sensor.so` | `~/out` remap, `output_type`, `frame_name` |

설정의 기준은 Humble용 [`gazebo_ros_pkgs` 3.9.0 소스](https://github.com/ros-simulation/gazebo_ros_pkgs/tree/3.9.0)와 Gazebo Classic의 [Wide-Angle Camera 튜토리얼](https://classic.gazebosim.org/tutorials?tut=wide_angle_camera)이다. `gazebo_ros_camera`는 `camera`, `depth`, `multicamera`를 명시적으로 처리하며, Gazebo 11의 `WideAngleCameraSensor`가 `CameraSensor`를 상속하므로 `wideanglecamera`도 camera 경로로 ROS 영상을 발행한다.

> Gazebo Classic 11과 `gazebo_ros_pkgs`는 2025년 1월에 EOL이 되었다. 이 저장소는 Humble/Classic 유지보수와 기존 프로젝트 재현을 위한 학습 자료다. 새 프로젝트에서는 최신 Gazebo로의 이전 계획도 함께 세운다.
