# 센서를 Xacro로 모듈화하고 관측하기

> **난이도:** 초급<br>
> **Gazebo:** Harmonic<br>
> **ROS 2:** Jazzy<br>
> **선행 학습:** DiffDrive

## 학습 목표

- 센서의 물리 장착부와 Gazebo 센서 설정을 서로 다른 Xacro로 분리한다.
- 바퀴 오도메트리, IMU, 단안·스테레오·RGB-D·어안 카메라, 2D·3D LiDAR의 주요 파라미터를 읽는다.
- Gazebo Transport 메시지를 먼저 확인한 뒤 ROS 2로 브리지하고 RViz에서 시각화한다.
- 높은 해상도와 갱신률이 시뮬레이션 성능에 미치는 영향을 설명한다.

## 실습 준비

[설치 안내](../02_getting-started/02_installation-jazzy.md)에서 예제를 빌드한 뒤 시작한다. 먼저 2D 라이다·RGB-D·IMU 기본 구성의 자동 검사를 실행하고, 9절부터 여러 센서를 함께 띄운다. 아래 XML은 각 설정을 설명하는 발췌본이며, 실행에는 저장소의 완성된 Xacro 파일을 사용한다.

## 1. 센서는 세 층으로 구성한다

센서 실습에서는 다음 세 층을 분리한다. 링크와 고정 조인트는 센서 좌표계를 만들고, `<sensor>`는 관측 모델을 정의하며, 월드 시스템은 센서를 실제로 갱신한다. 어느 한 층이라도 빠지면 토픽 또는 TF가 생기지 않는다.

| 층 | 파일 | 책임 |
|---|---|---|
| 장착부 | `urdf/sensors/sensor_mounts.xacro` | `*_link`, 광학 좌표계, 고정 조인트 |
| 관측 모델 | `urdf/sensors/lidar.xacro`, `cameras.xacro`, `imu.xacro` | 형식, 해상도, 범위, 노이즈, 토픽 |
| 실행 시스템 | `worlds/sensor-test.sdf` | Sensors(`ogre2`), Imu 시스템, 물리 |

월드에는 렌더링 센서를 갱신하는 Sensors 시스템과 IMU를 갱신하는 Imu 시스템을 둔다.

```xml
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
<plugin filename="gz-sim-imu-system"
        name="gz::sim::systems::Imu"/>
```

카메라와 GPU 라이다는 이 예제의 `ogre2` 렌더링 엔진으로 보이는 형상(`visual`)을 관측한다. 물리 접촉에 쓰는 `collision`과 다르므로 형상이 크게 다르면 센서에 보이는 경계와 충돌 위치가 달라진다. IMU는 별도의 `Imu` 시스템이 갱신한다. `gz sim -s`로 GUI를 꺼도 카메라와 GPU 라이다의 렌더링은 필요하다.

`sensor-test.sdf`에는 조명과 빨간 `sensor_target` 상자를 둔다. 카메라에서는 색과 윤곽을, 깊이·3D LiDAR에서는 거리를, 2D LiDAR에서는 전방 반환점을 같은 물체로 교차 확인할 수 있다.

<figure class="course-figure" markdown="span">
  ![로봇에서 퍼지는 라이다 광선과 RGB-D 카메라 화면 및 IMU 축](../assets/beginner/sensor-observables.svg)
  <figcaption>그림 4. 센서마다 측정하는 값과 갱신률이 다르므로 토픽 형식과 측정 시각을 함께 확인한다.</figcaption>
</figure>

## 2. 센서 Xacro를 include하고 호출한다

최종 로봇 파일은 센서 구현을 복사하지 않고 네 파일을 include한다.

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="tutorial_bot">
  <xacro:include filename="sensors/sensor_mounts.xacro"/>
  <xacro:include filename="sensors/lidar.xacro"/>
  <xacro:include filename="sensors/cameras.xacro"/>
  <xacro:include filename="sensors/imu.xacro"/>

  <!-- base_link와 두 구동 바퀴, caster를 정의한 뒤 mount를 붙인다. -->
  <xacro:tutorial_sensor_mounts/>

  <xacro:gpu_lidar_2d reference="lidar_link" sensor_name="lidar"
                       topic="$(arg lidar_topic)"
                       frame_id="$(arg tf_prefix)lidar_link"/>
  <xacro:rgbd_camera_sensor reference="camera_link" sensor_name="camera"
                             topic="$(arg camera_topic)"
                             frame_id="$(arg tf_prefix)camera_optical_frame"/>
  <xacro:imu_sensor reference="imu_link" sensor_name="imu"
                    topic="$(arg imu_topic)"
                    frame_id="$(arg tf_prefix)imu_link"/>
</robot>
```

재사용의 핵심은 매크로의 `topic`, `frame_id`, `update_rate`, `samples`를 인자로 만드는 것이다. 같은 센서 매크로를 다른 로봇에서 호출할 때 토픽과 장착부만 바꾸면 된다. `04-sensors-final.xacro`는 기본 2D LiDAR·RGB-D·IMU 구성을, `05-sensor-gallery.xacro`는 모든 센서 구성을 조립한다.

## 3. 바퀴 오도메트리는 주행 시스템의 관측값이다

바퀴 오도메트리는 별도의 `<sensor>`가 아니라 바퀴 회전과 기구학을 사용하는 DiffDrive 시스템의 출력이다.

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

`wheel_separation`과 `wheel_radius`가 실제 URDF 치수와 다르면 로봇은 움직여도 오도메트리 축척과 회전량이 틀어진다. Gazebo 토픽 `/model/tutorial_bot/odometry`를 ROS `/odom`으로 브리지한 뒤 `nav_msgs/msg/Odometry`의 위치·자세와 twist를 확인한다.

## 4. 2D 라이다를 구성한다

기본 매크로의 핵심은 다음과 같다.

```xml
<sensor name="${sensor_name}" type="gpu_lidar">
  <topic>${topic}</topic>
  <gz_frame_id>${frame_id}</gz_frame_id>
  <always_on>true</always_on>
  <update_rate>${update_rate}</update_rate>
  <lidar>
    <scan>
      <horizontal>
        <samples>${samples}</samples>
        <resolution>1</resolution>
        <min_angle>${min_angle}</min_angle>
        <max_angle>${max_angle}</max_angle>
      </horizontal>
    </scan>
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

기본값은 10 Hz, 360 표본, `-π..π`, `0.12..10.0 m`, 거리 해상도 0.01 m, 가우시안 노이즈 표준편차 0.01 m이다. 두 끝 각도를 모두 표본에 포함하므로 각도 간격은 다음과 같다.

\[
\Delta\theta=\frac{\pi-(-\pi)}{360 - 1}=\frac{2\pi}{359}\approx1.0028^\circ
\]

반환점이 범위 안에 없으면 `ranges`에 `inf`가 들어갈 수 있다. `inf`는 10 m 물체가 아니라 유효 반환점이 없다는 뜻이다.

## 5. 3D 라이다는 수직 방향 광선을 추가한다

3D LiDAR도 `type="gpu_lidar"`와 `<lidar>`를 사용한다. 차이는 수직 광선이 하나보다 많다는 점이다.

```xml
<scan>
  <horizontal>
    <samples>640</samples>
    <min_angle>-3.14159265359</min_angle>
    <max_angle>3.14159265359</max_angle>
  </horizontal>
  <vertical>
    <samples>16</samples>
    <min_angle>-0.261799</min_angle>  <!-- -15 deg -->
    <max_angle>0.261799</max_angle>   <!-- +15 deg -->
  </vertical>
</scan>
```

한 프레임은 최대 `640 × 16 = 10,240` 점을 만든다. 10 Hz라면 렌더링과 브리지가 처리할 양도 커지므로 처음에는 표본과 갱신률을 낮게 둔다. Gazebo의 `/tutorial_bot/lidar_3d/points`(`gz.msgs.PointCloudPacked`)를 ROS `sensor_msgs/msg/PointCloud2`로 변환해 RViz의 PointCloud2 디스플레이로 본다.

## 6. IMU의 노이즈를 축마다 정의한다

IMU는 각속도와 선형 가속도를 각각 x·y·z 세 축으로 발행한다. 예제는 각 축에 같은 표준편차를 적용한다.

```xml
<sensor name="${sensor_name}" type="imu">
  <topic>${topic}</topic>
  <gz_frame_id>${frame_id}</gz_frame_id>
  <update_rate>100</update_rate>
  <imu>
    <angular_velocity>
      <x><noise type="gaussian"><mean>0.0</mean><stddev>0.001</stddev></noise></x>
      <y><noise type="gaussian"><mean>0.0</mean><stddev>0.001</stddev></noise></y>
      <z><noise type="gaussian"><mean>0.0</mean><stddev>0.001</stddev></noise></z>
    </angular_velocity>
    <linear_acceleration>
      <!-- y, z도 같은 구조로 정의한다. -->
      <x><noise type="gaussian"><mean>0.0</mean><stddev>0.001</stddev></noise></x>
    </linear_acceleration>
  </imu>
</sensor>
```

중력을 받으며 수평으로 정지한 IMU의 z 가속도는 약 `+9.8 m/s²`, 각속도는 약 0이어야 한다. 노이즈가 있으므로 모든 표본이 정확히 같지는 않다. `imu_link`의 축 방향, 중력에 따른 가속도, 타임스탬프 증가, 표준편차 범위를 함께 확인한다. RViz 기본 배포에는 IMU 디스플레이가 없으므로 `ros-jazzy-rviz-imu-plugin`을 설치해야 한다.

## 7. 카메라 네 종류를 구성한다

### 7.1 단안 카메라

단안(mono)은 카메라가 하나라는 뜻이며 흑백 영상만 뜻하지는 않는다. 이 실습의 단안 카메라는 `type="camera"`와 흑백 `L8` 형식을 사용한다.

```xml
<sensor name="mono_camera" type="camera">
  <topic>/tutorial_bot/mono/image</topic>
  <gz_frame_id>mono_camera_optical_frame</gz_frame_id>
  <update_rate>30</update_rate>
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image><width>640</width><height>480</height><format>L8</format></image>
    <clip><near>0.10</near><far>30.0</far></clip>
    <optical_frame_id>mono_camera_optical_frame</optical_frame_id>
  </camera>
</sensor>
```

일반 카메라와 광각 카메라는 영상 토픽의 마지막 `/image`를 기준으로 같은 상위 경로 아래에 `/camera_info`를 만든다. 따라서 위 단안 예제의 정보 토픽은 `/tutorial_bot/mono/camera_info`이다. 반면 RGB-D 매크로에는 `/tutorial_bot/camera`라는 기본 경로만 넘긴다. RGB-D 시스템이 그 아래에 `/image`, `/depth_image`, `/points`, `/camera_info`를 각각 붙이기 때문이다.

### 7.2 스테레오 카메라

Harmonic에서 별도의 표준 `stereo` 센서 타입을 가정하지 않는다. 동일한 해상도·시야각·갱신률을 가진 left/right 카메라 두 개를 0.10 m 기준선 거리로 배치한다.

```xml
<xacro:stereo_camera_pair
    left_reference="stereo_left_link"
    right_reference="stereo_right_link"
    topic_prefix="/tutorial_bot/stereo"
    left_frame_id="stereo_left_optical_frame"
    right_frame_id="stereo_right_optical_frame"
    update_rate="20" width="640" height="480"/>
```

`sensor_gallery_mounts`가 left/right 링크를 y축 `+0.05 m`, `-0.05 m`에 둔다. 이 구성은 두 시점의 영상을 비교하는 실습이다. 바로 깊이 영상을 만드는 구성은 아니다. 스테레오 거리 추정까지 확장하려면 좌우 영상 동기화, 보정, 정렬(rectification), 실제 기준선 거리가 반영된 CameraInfo를 함께 준비해야 한다.

### 7.3 RGB-D 카메라

`rgbd_camera`는 RGB 영상, 깊이 영상, 카메라 정보, 점군을 한 설정에서 만든다. 영상과 CameraInfo는 광학 좌표계 `camera_optical_frame`을 사용하고 30 Hz로 갱신한다. Harmonic의 RGB-D 점군은 아래 설명처럼 별도의 프레임 보정이 필요하다.

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

RGB는 `/tutorial_bot/camera/image`, 깊이는 `/tutorial_bot/camera/depth_image`, 점군은 `/tutorial_bot/camera/points`에 나타난다.

카메라 본체의 `camera_link`는 **x축이 전방, y축이 왼쪽, z축이 위**이다. 광학 좌표계는 **z축이 전방, x축이 오른쪽, y축이 아래**이므로 두 좌표계 사이에 회전이 필요하다. 예제의 고정 조인트는 `rpy="-1.57079632679 0 -1.57079632679"`로 이 관계를 정의한다. 카메라 센서는 본체 링크에 붙이고 영상의 헤더만 광학 좌표계를 사용한다.

Harmonic RGB-D 점군의 XYZ는 본체 좌표계 기준으로 생성된다. 브리지 설정의 `/camera/points` 항목에 `frame_id: camera_link`를 지정해 실제 좌표와 헤더를 일치시킨다. 영상·깊이 영상·CameraInfo는 `camera_optical_frame`을 유지한다. 프레임 이름을 바꾸는 것은 좌표를 회전시키는 연산이 아니므로 이 보정을 다른 센서에 그대로 적용해서는 안 된다. [RGB-D 센서 구현](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/RgbdCameraSensor.cc), [점군 좌표 복사 구현](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/PointCloudUtil.cc).

### 7.4 어안 카메라

Harmonic의 광각 카메라는 `type="wideanglecamera"`와 `<lens>`를 함께 사용한다. 예제는 등입체각(equisolid-angle) 투영, 수평 시야각 약 160°, 크기 512의 환경 텍스처를 사용한다.

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

`env_texture_size`를 높이면 선명도가 좋아지지만 GPU 비용이 증가한다. 사용자 정의 렌즈가 필요하면 `<type>custom</type>`과 `<custom_function>`의 `c1`, `c2`, `c3`, `f`, `fun`을 명시한다.

## 8. 기본 센서를 자동 검증한다

저장소 루트에서 다음을 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/04-sensors-final.xacro"
xacro "$stage" > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
./scripts/check_sensors.sh
```

검사 스크립트는 `04-sensors-final.xacro`를 확장하고 실제 Gazebo 메시지를 검사한다. LiDAR 360개 거리 값, 320×240 RGB-D 영상, 100 Hz IMU를 설정값과 비교한다.

```text
LiDAR scan verified: 360 ranges, ... obstacle readings.
Camera image verified: 320x240.
```

## 9. 여러 센서를 함께 실행한다

앞 장에서 실행한 Gazebo와 브리지, RViz를 종료한다. 새 터미널 1에서 센서 관측용 월드를 연다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf"
gz sim -r "$world"
```

터미널 2에서 센서 모음 Xacro를 URDF로 변환한 뒤 로봇을 생성한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
xacro "$gallery" > /tmp/tutorial_bot_sensor_gallery.urdf
ros2 run ros_gz_sim create -world sensor_test \
  -name tutorial_bot_sensor_gallery \
  -file /tmp/tutorial_bot_sensor_gallery.urdf -z 0.12
```

Gazebo Transport에서 실제 토픽과 타입을 확인한다.

```bash
gz topic -l | grep -E '/tutorial_bot/(lidar|lidar_3d|imu|mono|stereo|camera|fisheye)'
gz topic -i -t /tutorial_bot/lidar
gz topic -i -t /tutorial_bot/lidar_3d/points
gz topic -e -t /tutorial_bot/imu -n 1
```

토픽 이름을 추측하지 말고 `gz topic -l` 결과를 먼저 사용한다. 센서 생성에 실패하면 `gz sim -v 4`로 다시 실행해 Sensors 시스템과 렌더링 엔진 오류를 확인한다.

## 10. ROS 2와 RViz에서 시각화한다

센서 메시지를 RViz에 놓으려면 브리지, 로봇의 TF, 시뮬레이션 시계가 모두 필요하다. 앞 절의 Gazebo를 계속 실행한 채 아래 프로그램을 각각 **새 터미널**에서 시작한다. 매번 저장소 루트로 이동하고 기본 ROS 환경과 작업 공간 환경을 불러온다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

1. **터미널 3 — 센서·시계·주행 상태 브리지**

    ```bash
    ros2 run ros_gz_bridge parameter_bridge --ros-args \
      -p config_file:="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-sensor-gallery.yaml"
    ```

2. **터미널 4 — RGB 영상 브리지**

    ```bash
    ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
      --ros-args -r /tutorial_bot/camera/image:=/camera/image
    ```

    먼저 기본 RGB 영상을 확인한다. 단안·스테레오·어안 영상도 보고 싶다면 이 프로그램을 종료한 뒤 [브리지 장의 다섯 영상 연결 예제](10-ros-gz-bridge.md)를 실행한다.

3. **터미널 5 — 로봇과 센서의 TF**

    ```bash
    ros2 run robot_state_publisher robot_state_publisher \
      /tmp/tutorial_bot_sensor_gallery.urdf --ros-args -p use_sim_time:=true
    ```

    앞 절에서 생성한 것과 같은 URDF를 사용한다. 센서의 고정 TF는 URDF에서, 바퀴의 회전 TF는 `/joint_states`에서 만든다.

4. **터미널 6 — RViz**

    ```bash
    rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz" \
      --ros-args -p use_sim_time:=true
    ```

    Fixed Frame은 `odom`으로 둔다. 먼저 RobotModel, TF, LiDAR, RGB-D Camera, RGB-D Points, IMU만 켠다. 아직 실행하지 않은 영상과 Path 항목은 꺼 둔다. IMU 플러그인이 없다는 오류가 나면 `sudo apt install ros-jazzy-rviz-imu-plugin`으로 설치한 뒤 RViz를 다시 연다.

별도 확인용 터미널에서 다음을 실행한다. `tf2_echo`는 계속 출력되므로 각 결과를 확인한 뒤 `Ctrl+C`를 눌러 다음 명령으로 넘어간다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /scan --field header --qos-reliability best_effort --once
ros2 topic echo /camera/points --field header --qos-reliability best_effort --once
ros2 run tf2_ros tf2_echo odom lidar_link
ros2 run tf2_ros tf2_echo odom camera_link
ros2 run tf2_ros tf2_echo base_link camera_optical_frame
```

| 데이터 | ROS 토픽 | 기대하는 `header.frame_id` | RViz 항목 |
|---|---|---|---|
| 2D 라이다 | `/scan` | `lidar_link` | LaserScan |
| 3D 라이다 | `/lidar_3d/points` | `lidar_3d_link` | PointCloud2 |
| IMU | `/imu` | `imu_link` | `rviz_imu_plugin/Imu` |
| RGB·깊이 영상, 카메라 정보 | `/camera/image`, `/camera/depth/image`, `/camera/camera_info` | `camera_optical_frame` | Camera 또는 Image |
| RGB-D 점군 | `/camera/points` | `camera_link` | PointCloud2 |

정지한 로봇 앞의 빨간 상자가 영상 안에 보이고, 점군과 라이다의 관측점이 RViz에서 그 상자의 위치에 모여야 한다. 바닥의 점군은 바닥과 평행해야 한다. 로봇을 회전시켰을 때 고정된 장애물의 관측점이 함께 회전한다면 센서 축이나 TF를 다시 확인한다. 주행과 Path 누적은 [다음 브리지 실습](10-ros-gz-bridge.md)의 8~9절에서 이어서 실행한다.

## 자주 발생하는 문제

### Gazebo 토픽이 없다

월드에 Sensors 시스템과 Imu 시스템이 있는지, 시뮬레이션이 재생 중인지, 센서가 달린 모델이 spawn됐는지 확인한다.

### RViz에 데이터가 있지만 보이지 않는다

`header.frame_id`에서 Fixed Frame까지 TF가 연결되는지 확인한다. 영상만 보는 Image 디스플레이는 TF가 없어도 보이지만 LaserScan과 PointCloud2는 올바른 TF가 필요하다.

### 설정값보다 토픽 발행률이 낮다

카메라 수, 영상 크기, LiDAR 표본 수, 갱신률을 한 번에 높였는지 확인한다. 기본 RGB-D 해상도 `320×240`과 낮은 갱신률부터 시작한다. `gz topic -e -t /world/sensor_test/stats -n 1`의 실시간 계수와 실제 메시지 수신률을 보면서 하나씩 높인다.

## 정리

센서 장착부, 센서 매크로, 월드 시스템을 분리하면 같은 관측 모델을 다른 로봇에도 재사용할 수 있다. 다음 장에서는 Gazebo와 ROS 2의 서로 다른 통신 체계를 YAML 브리지로 연결한다.

[이전: DiffDrive](07-diff-drive.md) · [다음: Gazebo Fuel](09-gazebo-fuel.md)
