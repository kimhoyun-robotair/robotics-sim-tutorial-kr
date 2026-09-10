# 센서 심화: 노이즈와 주기

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `gz_ros2_control`

## 학습 목표

- 바퀴 오도메트리, IMU, 단안·스테레오·RGB-D·어안 카메라, 2D·3D LiDAR의 핵심 파라미터를 읽는다.
- 센서 링크·조인트와 Gazebo 센서 설정을 재사용 가능한 Xacro로 분리한다.
- 브리지 뒤의 ROS 타입, `frame_id`, 발행 빈도, 해상도, 노이즈를 실제 메시지에서 검증한다.
- RViz에서 오도메트리, 영상, LaserScan, PointCloud2, IMU를 시각화한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## 센서 구성 파일

센서 예제는 물리 장착부와 센서 종류를 분리한다.

| 파일 | 역할 |
|---|---|
| `sensors/sensor_mounts.xacro` | 장착 위치, 고정 조인트, 광학 좌표계 |
| `sensors/lidar.xacro` | 2D·3D GPU LiDAR |
| `sensors/cameras.xacro` | 단안·스테레오·RGB-D·어안 카메라 |
| `sensors/imu.xacro` | IMU와 노이즈 |
| `stages/05-sensor-gallery.xacro` | 위 매크로를 불러오는 실행용 로봇 |

실제 파일은 `examples/ros2_ws/src/tutorial_bot_description/urdf/sensors/` 아래에 있다. 최상위 Xacro와 센서 모음 Xacro가 같은 매크로를 재사용하므로 센서 치수와 토픽 이름을 여러 로봇에 복사하지 않는다.

## 장착부와 광학 좌표계 분리 {#sensor-frames}

카메라 링크의 ROS 축과 영상 광학 좌표계의 축은 다르다. 장착부 파일은 고정 조인트로 둘을 연결한다.

```xml
<link name="camera_link"/>
<joint name="camera_joint" type="fixed">
  <parent link="base_link"/>
  <child link="camera_link"/>
  <origin xyz="0.24 0 0.02" rpy="0 0 0"/>
</joint>

<link name="camera_optical_frame"/>
<joint name="camera_optical_joint" type="fixed">
  <parent link="camera_link"/>
  <child link="camera_optical_frame"/>
  <origin xyz="0 0 0"
          rpy="-1.57079632679 0 -1.57079632679"/>
</joint>
```

ROS 몸체 좌표계는 +X 전방, +Y 왼쪽, +Z 위쪽이다. 카메라 광학 좌표계는 +Z 전방, +X 오른쪽, +Y 아래쪽이다. 위 고정 조인트가 두 좌표계를 연결한다. [REP 103의 좌표축 규약](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst)을 따른다.

**영상과 포인트 클라우드의 프레임을 무조건 같게 맞추면 안 된다.** Harmonic RGB-D 센서는 포인트 XYZ를 +X 전방 좌표로 만들면서 헤더에는 광학 좌표계 이름을 넣을 수 있다. 이 저장소는 `/camera/points` 브리지 항목의 `frame_id`를 `camera_link`로 보정한다. 이미지·깊이 영상·CameraInfo는 `camera_optical_frame`을 유지한다. XYZ를 바꾸는 변환이 아니라 잘못 붙은 이름을 바로잡는 설정이다. 근거는 [Harmonic RGB-D 메시지 생성 코드](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/RgbdCameraSensor.cc)와 [포인트 좌표 복사 코드](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/PointCloudUtil.cc)에서 확인할 수 있다.

| ROS 토픽 | 기대하는 `frame_id` | 좌표축 |
|---|---|---|
| `/scan` | `lidar_link` | X 전방, Y 왼쪽, Z 위쪽 |
| `/imu` | `imu_link` | X 전방, Y 왼쪽, Z 위쪽 |
| `/camera/image`, `/camera/depth/image`, `/camera/camera_info` | `camera_optical_frame` | Z 전방, X 오른쪽, Y 아래쪽 |
| `/camera/points` | `camera_link` | X 전방, Y 왼쪽, Z 위쪽 |
| `/lidar_3d/points` | `lidar_3d_link` | X 전방, Y 왼쪽, Z 위쪽 |

카메라 센서의 `<pose>`까지 광학 좌표계 회전으로 돌리면 Gazebo에서 실제 촬영 방향이 바뀐다. 센서 장착 자세와 메시지의 좌표축 규칙을 구분한다.

## 1. 바퀴 오도메트리

바퀴 오도메트리는 별도 `<sensor>`가 아니라 DiffDrive/Ackermann 시스템 플러그인 또는 ROS 컨트롤러가 바퀴 회전량과 기구학으로 계산한다.

```xml
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>0.38</wheel_separation>
  <wheel_radius>0.06</wheel_radius>
  <odom_publish_frequency>30</odom_publish_frequency>
  <frame_id>odom</frame_id>
  <child_frame_id>base_link</child_frame_id>
</plugin>
```

이는 `tutorial_bot.urdf.xacro`의 실제 DiffDrive 블록이다. 별도 토픽을 지정하지 않았으므로 Gazebo 기본 모델 오도메트리 토픽을 사용하고 브리지가 이를 ROS `/odom`으로 바꾼다. ROS에서는 `nav_msgs/msg/Odometry`의 위치와 자세, 선속도·각속도, `header.frame_id`, `child_frame_id`를 확인한다.

```bash
ros2 topic echo /odom --once
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_link
```

바퀴 미끄럼이 있는 4륜 스키드 조향에서는 바퀴 오도메트리가 실제 위치가 아니다. `/wheel_odom_path`는 **바퀴 모델이 추정한 궤적**이라는 점을 유지한다.

## 2. IMU

재사용 매크로는 장착할 링크, 토픽, 좌표계, 갱신 빈도, 노이즈 표준편차를 인자로 받는다.

```xml
<xacro:macro name="imu_sensor"
    params="reference sensor_name topic frame_id
            update_rate:=100 noise_stddev:=0.001">
  <gazebo reference="${reference}">
    <sensor name="${sensor_name}" type="imu">
      <topic>${topic}</topic>
      <gz_frame_id>${frame_id}</gz_frame_id>
      <always_on>true</always_on>
      <update_rate>${update_rate}</update_rate>
      <imu>
        <angular_velocity>
          <x><noise type="gaussian"><mean>0.0</mean>
             <stddev>${noise_stddev}</stddev></noise></x>
          <y><noise type="gaussian"><mean>0.0</mean>
             <stddev>${noise_stddev}</stddev></noise></y>
          <z><noise type="gaussian"><mean>0.0</mean>
             <stddev>${noise_stddev}</stddev></noise></z>
        </angular_velocity>
      </imu>
    </sensor>
  </gazebo>
</xacro:macro>
```

실제 매크로는 선가속도의 x·y·z 노이즈도 같은 방식으로 선언한다. 정지 상태에서 각속도가 항상 정확히 0일 필요는 없고 표본 평균과 표준편차가 설정과 부합해야 한다.

```bash
ros2 topic echo /imu --once
ros2 topic hz /imu
```

정지한 수평 로봇에서는 각속도가 0 부근이고 가속도 Z축에는 중력에 대한 비력 약 +9.81 m/s²가 나타난다. 가속도 세 축이 모두 0이어야 한다고 판단하지 않는다.

RViz에서 IMU 방향을 전용 표시 항목으로 보려면 `ros-jazzy-rviz-imu-plugin`을 설치하고 토픽 `/imu`, Fixed Frame `odom`을 설정한다.

## 3. 2D GPU LiDAR

`gpu_lidar_2d` 매크로의 실제 핵심은 다음과 같다.

```xml
<sensor name="${sensor_name}" type="gpu_lidar">
  <topic>${topic}</topic>
  <gz_frame_id>${frame_id}</gz_frame_id>
  <update_rate>${update_rate}</update_rate>
  <lidar>
    <scan><horizontal>
      <samples>${samples}</samples>
      <resolution>1</resolution>
      <min_angle>${min_angle}</min_angle>
      <max_angle>${max_angle}</max_angle>
    </horizontal></scan>
    <range>
      <min>${min_range}</min>
      <max>${max_range}</max>
      <resolution>${range_resolution}</resolution>
    </range>
    <noise>
      <type>gaussian</type><mean>0.0</mean>
      <stddev>${noise_stddev}</stddev>
    </noise>
  </lidar>
</sensor>
```

센서 모음은 360 표본, -π부터 +π, 0.12–10.0 m, 0.01 m 거리 분해능, 10 Hz를 사용한다. ROS 토픽은 `/scan`, 타입은 `sensor_msgs/msg/LaserScan`이다.

```bash
ros2 topic echo /scan --once --field ranges
ros2 topic echo /scan --once --field header.frame_id
ros2 topic hz /scan
```

RViz에서 LaserScan 표시 항목을 추가하고 토픽 `/scan`, Reliability `Best Effort`, Size `0.02` 정도로 설정한다.

## 4. 3D GPU LiDAR

2D LiDAR에 수직 방향의 스캔 범위와 채널 수를 추가하면 여러 높이를 함께 측정한다.

```xml
<scan>
  <horizontal>
    <samples>640</samples>
    <min_angle>-3.14159265359</min_angle>
    <max_angle>3.14159265359</max_angle>
  </horizontal>
  <vertical>
    <samples>16</samples>
    <min_angle>-0.261799</min_angle>
    <max_angle>0.261799</max_angle>
  </vertical>
</scan>
<range>
  <min>0.20</min><max>30.0</max><resolution>0.01</resolution>
</range>
```

한 번 측정할 때의 이론상 광선 수는 \(640\times16=10{,}240\)개이다. 브리지는 Gazebo `gz.msgs.PointCloudPacked`를 ROS `sensor_msgs/msg/PointCloud2`의 `/lidar_3d/points`로 변환한다.

```bash
ros2 topic echo /lidar_3d/points --once --field width
ros2 topic echo /lidar_3d/points --once --field height
ros2 topic echo /lidar_3d/points --once --field point_step
ros2 topic echo /lidar_3d/points --once --field header.frame_id
ros2 topic hz /lidar_3d/points
```

RViz에서 PointCloud2 표시 항목의 토픽을 `/lidar_3d/points`, Reliability를 Best Effort로 지정한다.

## 5. 단안 카메라

실제 `mono_camera_sensor` 매크로는 해상도, 수평 시야각(HFOV), 렌더링 거리 범위, 노이즈를 인자로 노출하고 픽셀 형식을 `L8`로 고정한다.

```xml
<sensor name="${sensor_name}" type="camera">
  <topic>${topic}/image</topic>
  <gz_frame_id>${frame_id}</gz_frame_id>
  <update_rate>${update_rate}</update_rate>
  <camera name="${sensor_name}">
    <horizontal_fov>${hfov}</horizontal_fov>
    <image>
      <width>${width}</width><height>${height}</height>
      <format>L8</format>
    </image>
    <clip><near>${near}</near><far>${far}</far></clip>
    <noise><type>gaussian</type><mean>0.0</mean><stddev>0.007</stddev></noise>
    <optical_frame_id>${frame_id}</optical_frame_id>
  </camera>
</sensor>
```

`topic` 인자에는 `/tutorial_bot/mono` 같은 기본 경로를 넘긴다. 매크로가 `/image`를 붙이므로 영상은 `/tutorial_bot/mono/image`에 나오고, Harmonic은 같은 기본 경로의 `/tutorial_bot/mono/camera_info`도 만든다. 센서 모음 단안 카메라는 640×480, 30 Hz, 수평 시야각(HFOV) 1.047 rad를 사용한다. `clip/near`보다 가까운 물체와 `clip/far`보다 먼 물체는 렌더링 범위 밖이다.

```bash
ros2 topic echo /mono/image --once --field width
ros2 topic echo /mono/image --once --field height
ros2 topic echo /mono/image --once --field encoding
ros2 topic echo /mono/image --once --field header.frame_id
ros2 topic echo /mono/camera_info --once
```

RViz Image는 TF 없이도 영상을 표시한다. Camera 표시 항목은 이미지·CameraInfo와 해당 광학 TF가 필요하다. PointCloud2는 자신의 프레임에서 Fixed Frame까지 이어지는 TF를 사용하며 CameraInfo를 직접 요구하지 않는다.

## 6. 스테레오 카메라

센서 모음 예제에서는 동일한 핀홀 카메라 두 개를 좌우로 0.10 m 떨어뜨린다. 두 카메라 사이 거리를 기선 길이(baseline)라고 한다. 한 매크로에서 같은 카메라 설정을 두 번 불러온다.

```xml
<xacro:macro name="stereo_camera_pair"
    params="left_reference right_reference topic_prefix
            left_frame_id right_frame_id update_rate:=20 width:=640 height:=480">
  <xacro:mono_camera_sensor
      reference="${left_reference}" sensor_name="stereo_left"
      topic="${topic_prefix}/left" frame_id="${left_frame_id}"
      update_rate="${update_rate}" width="${width}" height="${height}"/>
  <xacro:mono_camera_sensor
      reference="${right_reference}" sensor_name="stereo_right"
      topic="${topic_prefix}/right" frame_id="${right_frame_id}"
      update_rate="${update_rate}" width="${width}" height="${height}"/>
</xacro:macro>
```

왼쪽과 오른쪽 영상은 `/stereo/left/image`, `/stereo/right/image`에서 확인한다. 같은 시각에 촬영한 좌우 영상 쌍을 사용해야 스테레오 정합이 가능하다. 이 예제는 두 영상과 TF 생성까지만 다룬다. 독립 카메라 두 개를 배치하는 것만으로 스테레오 보정이 끝나지는 않는다. `stereo_image_proc`로 깊이를 계산하려면 영상 동기화·정류와 오른쪽 CameraInfo의 투영행렬 `P[3] = -fx × baseline` 등 보정 정보를 추가로 준비해야 한다.

## 7. RGB-D 카메라

RGB-D 센서는 RGB 영상, 깊이 영상, CameraInfo, 포인트 클라우드를 함께 만든다.

```xml
<sensor name="camera" type="rgbd_camera">
  <topic>/tutorial_bot/camera</topic>
  <gz_frame_id>camera_optical_frame</gz_frame_id>
  <update_rate>30</update_rate>
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image><width>320</width><height>240</height><format>R8G8B8</format></image>
    <clip><near>0.1</near><far>10.0</far></clip>
    <optical_frame_id>camera_optical_frame</optical_frame_id>
  </camera>
</sensor>
```

```bash
ros2 topic echo /camera/image --once --field width
ros2 topic echo /camera/image --once --field height
ros2 topic echo /camera/image --once --field encoding
ros2 topic echo /camera/depth/image --once --field encoding
ros2 topic echo /camera/points --once --field header.frame_id
```

RViz에서는 RGB와 깊이를 Image 표시 항목으로, `/camera/points`를 PointCloud2 표시 항목으로 확인한다. 포인트 클라우드의 벽이 옆으로 눕거나 바닥이 수직으로 보이면 `/camera/points.header.frame_id`가 `camera_link`인지 먼저 확인한다. 이미지·CameraInfo가 정상인 상태에서 광학 조인트를 임의로 돌려 화면만 맞추지 않는다.

## 8. 어안 카메라

Harmonic의 광각 카메라는 `wideanglecamera` 타입과 렌즈 모델을 사용한다.

```xml
<sensor name="fisheye_camera" type="wideanglecamera">
  <topic>/tutorial_bot/fisheye/image</topic>
  <gz_frame_id>fisheye_camera_optical_frame</gz_frame_id>
  <update_rate>15</update_rate>
  <camera>
    <horizontal_fov>2.792527</horizontal_fov>
    <image><width>640</width><height>480</height><format>R8G8B8</format></image>
    <lens>
      <type>equisolid_angle</type>
      <scale_to_hfov>true</scale_to_hfov>
      <cutoff_angle>1.57079632679</cutoff_angle>
      <env_texture_size>512</env_texture_size>
    </lens>
    <optical_frame_id>fisheye_camera_optical_frame</optical_frame_id>
  </camera>
</sensor>
```

수평 시야각(HFOV) 2.792527 rad는 약 160°이다. Gazebo가 어안 렌즈 모델로 영상을 렌더링한다. 일반 핀홀 카메라의 왜곡 계수만 바꾸는 방식과 결과가 다르다. RViz Image 표시 항목에서 `/fisheye/image`를 선택해 가장자리 왜곡과 넓은 시야를 확인한다.

## 센서 모음 Xacro에서 구성하기

실제 `05-sensor-gallery.xacro`는 다음 패턴으로 모든 센서를 조립한다.

```xml
<xacro:include filename="../macros/stage_components.xacro"/>
<xacro:include filename="../sensors/sensor_mounts.xacro"/>
<xacro:include filename="../sensors/lidar.xacro"/>
<xacro:include filename="../sensors/cameras.xacro"/>
<xacro:include filename="../sensors/imu.xacro"/>

<xacro:stage_base/>
<xacro:stage_wheels/>
<xacro:stage_diff_drive model_name="tutorial_bot_sensor_gallery"/>
<xacro:tutorial_sensor_mounts/>
<xacro:sensor_gallery_mounts/>

<xacro:gpu_lidar_2d reference="lidar_link" sensor_name="lidar"
                     topic="/tutorial_bot/lidar" frame_id="lidar_link"/>
<xacro:gpu_lidar_3d reference="lidar_3d_link" sensor_name="lidar_3d"
                     topic="/tutorial_bot/lidar_3d" frame_id="lidar_3d_link"/>
<xacro:imu_sensor reference="imu_link" sensor_name="imu"
                  topic="/tutorial_bot/imu" frame_id="imu_link"/>
```

이 구조에서는 새 로봇의 최상위 Xacro가 필요한 매크로만 선택해 호출한다. 센서 XML 전체를 복사하지 않으므로 토픽, 좌표계, 발행 빈도를 인자로 검토할 수 있다.

## 센서 모음 실행

먼저 설치된 센서 모음 Xacro를 펼치고 검사한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
xacro "$gallery" > /tmp/tutorial_bot_sensor_gallery.urdf
check_urdf /tmp/tutorial_bot_sensor_gallery.urdf
```

터미널 1에서 센서 검사용 월드를 실행한다.

```bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf"
gz sim -r "$world"
```

터미널 2에서 엔티티를 생성한다.

```bash
ros2 run ros_gz_sim create \
  -world sensor_test \
  -name tutorial_bot_sensor_gallery \
  -file /tmp/tutorial_bot_sensor_gallery.urdf \
  -z 0.12
```

터미널 3에서 같은 로봇 설명으로 TF를 발행한다.

```bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro "$gallery")"
```

터미널 4에서 YAML 브리지를 실행한다.

```bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-sensor-gallery.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

터미널 5에서 이미지 브리지를 실행한다. RGB·단안·스테레오·어안 영상을 ROS 토픽으로 연결한다.

```bash
ros2 run ros_gz_image image_bridge \
  /tutorial_bot/camera/image \
  /tutorial_bot/mono/image \
  /tutorial_bot/stereo/left/image \
  /tutorial_bot/stereo/right/image \
  /tutorial_bot/fisheye/image \
  --ros-args \
  -r /tutorial_bot/camera/image:=/camera/image \
  -r /tutorial_bot/mono/image:=/mono/image \
  -r /tutorial_bot/stereo/left/image:=/stereo/left/image \
  -r /tutorial_bot/stereo/right/image:=/stereo/right/image \
  -r /tutorial_bot/fisheye/image:=/fisheye/image
```

YAML이 오도메트리 TF와 `/joint_states`를 브리지하므로 `robot_state_publisher`의 바퀴·고정 센서 TF와 합쳐 `odom → base_link → wheel_link 또는 sensor_link`가 된다. 터미널 6에서 궤적 노드를, 터미널 7에서 RViz를 실행한다.

```bash
ros2 run tutorial_bot_bringup odom_to_path --ros-args -p use_sim_time:=true
```

```bash
rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz" \
  --ros-args -p use_sim_time:=true
```

RViz에는 Nav2가 실행되지 않으므로 **Fixed Frame을 `odom`**으로 맞춘다. LaserScan과 PointCloud2의 Reliability는 `Best Effort`로 설정한다. 추가 영상은 **Add → Image**에서 `/mono/image`, `/stereo/left/image`, `/stereo/right/image`, `/fisheye/image`를 각각 선택한다.

## RViz에서 센서 위치와 방향 확인하기

1. 로봇을 정지시킨다. Gazebo의 벽 위치와 RViz의 `/scan`, `/camera/points`를 비교한다. 정면 벽의 포인트가 로봇의 +X 방향에 있어야 한다.
2. TF 표시에서 `base_link`, `camera_link`, `camera_optical_frame`의 축을 켠다. 카메라 광학 Z축이 몸체 X축과 같은 전방을 향해야 한다.
3. `/lidar_3d/points`를 추가한다. 수직 방향으로 여러 층이 생겨야 하며, 위쪽 채널이 옆으로 눕지 않아야 한다.
4. 키보드로 조금 움직인 뒤 멈춘다. `odom` 기준에서 벽이 로봇과 함께 움직인다면 센서 데이터의 프레임과 TF 시간부터 확인한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

센서 모음은 Gazebo DiffDrive 플러그인을 쓰므로 `Twist` 명령을 사용한다. 기본 중급 launch의 `TwistStamped` 명령과 구분한다.

## 자동 검증

기본 `tutorial_bot` 센서의 발행 빈도·노이즈·좌표계 설정은 다음 명령으로 검사한다.

```bash
./scripts/check_intermediate_sensors.sh --evidence /tmp/tutorial-intermediate-sensors --launch
```

검증 스크립트는 최대 실제 시간 90초 안에 각 센서가 준비되는지 확인하고, 메시지 타임스탬프 기준으로 시뮬레이션 시간 10초 동안 데이터를 모은다. 느린 렌더링 환경에서는 실제 수집 시간이 더 길어질 수 있으며 최대 180초까지 기다린다. 2D LiDAR 거리 360개, RGB-D 320×240 해상도, 프레임, 카메라 내부 파라미터, 유효한 측정값, 발행 빈도와 노이즈를 검사한다. 추가 센서 전체의 화면까지 자동 검증하는 스크립트는 아니므로 앞 절의 시각화 확인도 수행한다.

<figure class="course-figure" id="intermediate-sensor-statistics">
  <img src="../../assets/intermediate/sensor-statistics.svg" alt="센서의 가우시안 노이즈 분포와 메시지 수신률 계산도" loading="lazy">
  <figcaption>그림 1. 센서 품질은 설정값이 아니라 실제 표본의 발행 빈도, 평균, 표준편차로 판정한다.</figcaption>
</figure>

검사용 월드의 정면 표적은 기본 로봇 시작 위치에서 LiDAR 약 **1.70 m**, RGB-D 중앙 포인트의 X값 약 **1.56 m**에 있다. 센서 장착 X좌표가 각각 0.10 m, 0.24 m이기 때문에 두 거리 값이 다르다. 정면 포인트의 X가 양수이고 Y·Z가 0 부근인지 함께 확인하면 프레임 이름만 맞는 오류도 찾을 수 있다.

## 계산 예제: 발행 빈도와 노이즈

<div class="course-worked" data-worked-example="sensor-statistics" markdown="1">
10초 동안 30 Hz 센서를 검사하면 기대 표본은 300개이고 95% 기준은 285개이다. 수집한 유효 표본이 296개, 첫·끝 타임스탬프 차가 9.84초면 관측 발행 빈도는 \((296-1)/9.84=29.98\,\mathrm{Hz}\)이다. 노이즈 \(\sigma=0.01\), \(n=296\)이면 평균 오차 허용항 \(5\sigma/\sqrt n=0.00291\)이며 표본 표준편차도 \([0.005,0.015]\) 안이어야 한다.
</div>

## 문제 해결

- 센서 토픽이 없으면 월드의 Sensors·Imu 시스템 플러그인과 Xacro `<gazebo reference>` 이름을 확인한다.
- 발행 빈도가 낮으면 실시간 배율(RTF)을 먼저 확인한다. 예를 들어 시뮬레이션이 실제 시간의 절반 속도로 진행되면 30 Hz 센서를 `ros2 topic hz`로 조회한 값도 약 15 Hz가 될 수 있다. 센서 자체의 주기는 메시지 타임스탬프 간격으로 따로 확인한다.
- 영상은 있으나 CameraInfo가 없으면 파라미터 브리지의 타입과 Gazebo 토픽을 확인한다.
- PointCloud2가 RViz에 보이지 않으면 메시지의 `header.frame_id`까지 이어지는 TF와 유효한 깊이 값을 확인한다.
- 스테레오 좌우가 뒤바뀌면 장착부 y 좌표와 토픽 접두사를 확인한다.
- 어안 영상이 일반 카메라처럼 보이면 센서 타입이 `wideanglecamera`인지와 `<lens>`를 확인한다.
- IMU 표시 항목이 없으면 RViz IMU 플러그인 설치 여부를 확인하되 CLI 메시지 검증은 계속 수행한다.

## 정리

센서 설정은 토픽이 존재하는지만으로 검증할 수 없다. 장착부 TF, SDF 파라미터, 브리지 타입·QoS, 실제 메시지의 좌표계·발행 빈도·형상·노이즈를 연결해서 확인해야 한다. 센서 매크로를 종류별 파일로 분리하면 2륜 로봇과 4륜 로버가 같은 검증된 설정을 재사용할 수 있다.

[이전: gz_ros2_control](07-gz-ros2-control.md) · [다음: 다중 로봇](09-multi-robot.md)
