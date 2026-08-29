# 센서 심화: 노이즈와 주기

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `gz_ros2_control`

## 학습 목표

- wheel odometry, IMU, mono·stereo·RGB-D·fisheye Camera, 2D·3D LiDAR의 핵심 파라미터를 읽는다.
- sensor link·joint와 Gazebo sensor 설정을 재사용 가능한 Xacro로 분리한다.
- bridge 뒤의 ROS type, `frame_id`, rate, 해상도, 노이즈를 실제 message에서 검증한다.
- RViz에서 odometry, image, LaserScan, PointCloud2, IMU를 시각화한다.

## 센서 구성 파일

센서 예제는 물리 mount와 sensor 종류를 분리한다.

```text
urdf/
├── sensors/
│   ├── sensor_mounts.xacro  # link, fixed joint, optical frame
│   ├── lidar.xacro          # 2D/3D GPU LiDAR macro
│   ├── cameras.xacro        # mono, stereo, RGB-D, fisheye macro
│   └── imu.xacro            # IMU와 noise macro
└── stages/
    └── 05-sensor-gallery.xacro  # include 후 필요한 macro 조립
```

실제 파일은 `examples/ros2_ws/src/tutorial_bot_description/urdf/sensors/` 아래에 있다. main Xacro와 gallery Xacro가 같은 macro를 재사용하므로 센서 치수와 topic 계약을 여러 로봇에 복사하지 않는다.

## mount와 optical frame 분리

Camera link의 ROS 축과 영상 optical frame의 축은 다르다. mount 파일은 fixed joint로 둘을 연결한다.

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

ROS body frame은 +x 전방, +y 좌측, +z 위쪽을 사용한다. optical frame은 +z 전방, +x 오른쪽, +y 아래쪽을 사용한다. image와 point cloud의 `frame_id`에는 optical frame을 사용한다.

## 1. Wheel odometry

Wheel odometry는 별도 `<sensor>`가 아니라 DiffDrive/Ackermann System 또는 ROS controller가 바퀴 회전량과 기구학으로 계산한다.

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

이는 `tutorial_bot.urdf.xacro`의 실제 DiffDrive 블록이다. 별도 topic을 지정하지 않았으므로 Gazebo 기본 model odometry topic을 사용하고 bridge가 이를 ROS `/odom`으로 바꾼다. ROS에서는 `nav_msgs/msg/Odometry`의 pose, twist, `header.frame_id`, `child_frame_id`를 확인한다.

```bash
ros2 topic echo /odom --once
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_link
```

바퀴 slip이 있는 4륜 skid-steer에서는 wheel odometry가 ground truth가 아니다. `/wheel_odom_path`는 **바퀴 모델이 추정한 궤적**이라는 점을 유지한다.

## 2. IMU

재사용 macro는 link reference, topic, frame, update rate, noise 표준편차를 인자로 받는다.

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

실제 macro는 linear acceleration의 x·y·z noise도 같은 방식으로 선언한다. 정지 상태에서 각속도가 항상 정확히 0일 필요는 없고 표본 평균과 표준편차가 설정과 부합해야 한다.

```bash
ros2 topic echo /imu --once
ros2 topic hz /imu
```

RViz에서 IMU 방향을 전용 display로 보려면 `ros-jazzy-rviz-imu-plugin`을 설치하고 topic `/imu`, Fixed Frame `odom`을 설정한다.

## 3. 2D GPU LiDAR

`gpu_lidar_2d` macro의 실제 핵심은 다음과 같다.

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

gallery는 360 sample, -π부터 +π, 0.12–10.0 m, 0.01 m resolution, 10 Hz를 사용한다. ROS topic은 `/scan`, type은 `sensor_msgs/msg/LaserScan`이다.

```bash
ros2 topic echo /scan --once --field ranges
ros2 topic echo /scan --once --field header.frame_id
ros2 topic hz /scan
```

RViz에서 LaserScan display를 추가하고 topic `/scan`, Reliability `Best Effort`, Size `0.02` 정도로 설정한다.

## 4. 3D GPU LiDAR

2D LiDAR에 vertical scan을 추가하면 여러 ring을 가진 3D scan을 만든다.

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

한 frame의 이론상 ray 수는 \(640\times16=10{,}240\)개이다. bridge는 Gazebo `gz.msgs.PointCloudPacked`를 ROS `sensor_msgs/msg/PointCloud2`의 `/lidar_3d/points`로 변환한다.

```bash
ros2 topic echo /lidar_3d/points --once --field width
ros2 topic echo /lidar_3d/points --once --field height
ros2 topic echo /lidar_3d/points --once --field point_step
ros2 topic echo /lidar_3d/points --once --field header.frame_id
ros2 topic hz /lidar_3d/points
```

RViz에서 PointCloud2 display의 topic을 `/lidar_3d/points`, Reliability를 Best Effort로 지정한다.

## 5. Mono Camera

실제 `mono_camera_sensor` macro는 해상도, HFOV, clip range, noise를 인자로 노출하고 pixel format을 `L8`로 고정한다.

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

`topic` 인자에는 `/tutorial_bot/mono` 같은 base를 넘긴다. macro가 `/image`를 붙이므로 영상은 `/tutorial_bot/mono/image`에 나오고, Harmonic은 같은 base의 `/tutorial_bot/mono/camera_info`도 만든다. gallery mono Camera는 640×480, 30 Hz, HFOV 1.047 rad를 사용한다. clip near보다 가까운 물체와 far보다 먼 물체는 렌더링 범위 밖이다.

```bash
ros2 topic echo /mono/image --once --field width
ros2 topic echo /mono/image --once --field height
ros2 topic echo /mono/image --once --field encoding
ros2 topic echo /mono/image --once --field header.frame_id
ros2 topic echo /mono/camera_info --once
```

RViz의 Image display는 TF가 없어도 pixel을 볼 수 있지만 Camera 또는 PointCloud2 display로 공간에 배치하려면 optical TF와 CameraInfo가 필요하다.

## 6. Stereo Camera

Harmonic gallery는 검증하기 쉬운 pinhole Camera 두 개를 0.10 m baseline으로 배치한다. 같은 설정을 두 번 복사하지 않고 pair macro에서 mono macro를 재사용한다.

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

왼쪽과 오른쪽 image는 `/stereo/left/image`, `/stereo/right/image`에서 확인한다. stamp가 가까운 두 frame을 사용해야 stereo matching이 가능하다. 이 예제는 영상 생성과 calibration anatomy를 다루며 disparity 계산 node 자체는 포함하지 않는다.

## 7. RGB-D Camera

RGB-D sensor는 RGB image, depth image, CameraInfo, point cloud를 함께 만든다.

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

RViz에서는 RGB와 depth를 Image display로, `/camera/points`를 PointCloud2 display로 확인한다. PointCloud2가 누워 보이면 `camera_optical_frame` 회전을 먼저 확인한다.

## 8. Fisheye Camera

Harmonic의 wide-angle camera는 `wideanglecamera` type과 lens model을 사용한다.

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

HFOV 2.792527 rad는 약 160°이다. 일반 pinhole distortion coefficient만 바꾼 것과 다르게 Gazebo가 wide-angle lens model로 image를 렌더링한다. RViz Image display에서 `/fisheye/image`를 선택해 가장자리 왜곡과 넓은 시야를 확인한다.

## gallery Xacro에서 include하고 조립하기

실제 `05-sensor-gallery.xacro`는 다음 패턴으로 모든 센서를 조립한다.

```xml
<xacro:include filename="../macros/stage_components.xacro"/>
<xacro:include filename="../sensors/sensor_mounts.xacro"/>
<xacro:include filename="../sensors/lidar.xacro"/>
<xacro:include filename="../sensors/cameras.xacro"/>
<xacro:include filename="../sensors/imu.xacro"/>

<xacro:stage_base/>
<xacro:stage_wheels/>
<xacro:stage_diff_drive/>
<xacro:tutorial_sensor_mounts/>
<xacro:sensor_gallery_mounts/>

<xacro:gpu_lidar_2d reference="lidar_link" sensor_name="lidar"
                     topic="/tutorial_bot/lidar" frame_id="lidar_link"/>
<xacro:gpu_lidar_3d reference="lidar_3d_link" sensor_name="lidar_3d"
                     topic="/tutorial_bot/lidar_3d" frame_id="lidar_3d_link"/>
<xacro:imu_sensor reference="imu_link" sensor_name="imu"
                  topic="/tutorial_bot/imu" frame_id="imu_link"/>
```

이 구조에서는 새 로봇의 main Xacro가 필요한 macro만 선택해 호출한다. sensor XML 전체를 복사하지 않으므로 topic, frame, rate를 인자로 검토할 수 있다.

## sensor gallery 실행

먼저 설치된 gallery Xacro를 펼치고 검사한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
xacro "$gallery" > /tmp/tutorial_bot_sensor_gallery.urdf
check_urdf /tmp/tutorial_bot_sensor_gallery.urdf
```

Terminal 1에서 sensor test world를 실행한다.

```bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf"
gz sim -r "$world"
```

Terminal 2에서 entity를 spawn한다.

```bash
ros2 run ros_gz_sim create \
  -world sensor_test \
  -name tutorial_bot_sensor_gallery \
  -file /tmp/tutorial_bot_sensor_gallery.urdf \
  -z 0.12
```

Terminal 3에서 같은 description으로 TF를 발행한다.

```bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro "$gallery")"
```

Terminal 4에서 YAML bridge를 실행한다.

```bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-sensor-gallery.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

RGB·mono·stereo·fisheye pixel stream은 image bridge로 연결하고 ROS 이름으로 remap한다.

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

YAML이 odometry TF와 `/joint_states`를 bridge하므로 `robot_state_publisher`의 wheel·fixed sensor TF와 합쳐 `odom → base_link → wheel_link 또는 sensor_link`가 된다. wheel trajectory node와 RViz는 다음처럼 실행한다.

```bash
ros2 run tutorial_bot_bringup odom_to_path
```

```bash
rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz"
```

## 자동 검증

기본 `tutorial_bot` 센서의 rate·noise·frame 계약은 다음 명령으로 검사한다.

```bash
./scripts/check_intermediate_sensors.sh --launch
```

검증은 20초 준비 뒤 10초 동안 표본을 모아 2D LiDAR 360개 range, RGB-D 320×240, frame ID, intrinsic, 유한값, rate, noise를 확인한다. gallery의 추가 센서는 위 CLI로 topic type과 geometry를 각각 확인한다.

<figure class="course-figure" id="intermediate-sensor-statistics">
  <img src="../../assets/intermediate/sensor-statistics.svg" alt="센서의 가우시안 노이즈 분포와 메시지 수신률 계산도" loading="lazy">
  <figcaption>그림 1. 센서 품질은 설정값이 아니라 실제 표본의 rate, 평균, 표준편차로 판정한다.</figcaption>
</figure>

## 계산 예제: rate와 노이즈

<div class="course-worked" data-worked-example="sensor-statistics">
10초 동안 30 Hz 센서를 검사하면 기대 표본은 300개이고 95% 기준은 285개이다. retained finite 표본이 296개, 첫·끝 stamp 차가 9.84초면 관측 rate는 \((296-1)/9.84=29.98\,\mathrm{Hz}\)이다. noise \(\sigma=0.01\), \(n=296\)이면 평균 오차 허용항 \(5\sigma/\sqrt n=0.00291\)이며 sample standard deviation도 \([0.005,0.015]\) 안이어야 한다.
</div>

## 문제 해결

- sensor topic이 없으면 world의 Sensors·Imu System과 Xacro `<gazebo reference>` 이름을 확인한다.
- rate가 낮으면 simulation RTF와 bridge 처리량을 확인하고 GUI sensor visualization을 잠시 끈다.
- image는 있으나 CameraInfo가 없으면 parameter bridge의 type과 Gazebo topic을 확인한다.
- PointCloud2가 RViz에 보이지 않으면 optical frame까지의 TF, `frame_id`, finite depth를 확인한다.
- stereo 좌우가 뒤바뀌면 mount y 좌표와 topic prefix를 확인한다.
- fisheye가 일반 Camera처럼 보이면 sensor type이 `wideanglecamera`인지와 `<lens>`를 확인한다.
- IMU display가 없으면 RViz IMU plugin 설치 여부를 확인하되 CLI message 검증은 계속 수행한다.

## 정리

센서 설정은 topic이 존재하는지만으로 검증할 수 없다. mount TF, SDF parameter, bridge type·QoS, 실제 message의 frame·rate·geometry·noise를 연결해서 확인해야 한다. sensor macro를 종류별 파일로 분리하면 2륜 로봇과 4륜 rover가 같은 검증된 설정을 재사용할 수 있다.

[이전: gz_ros2_control](07-gz-ros2-control.md) · [다음: 다중 로봇](09-multi-robot.md)
