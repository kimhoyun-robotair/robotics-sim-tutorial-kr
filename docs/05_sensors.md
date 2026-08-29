# 5. Gazebo 센서와 RViz 시각화

이 장에서는 이동 로봇에 wheel odometry, IMU, 카메라, 2D/3D LiDAR를 장착하고 Gazebo의 측정값이 ROS 2 토픽과 TF를 거쳐 RViz에 나타나는 전 과정을 실습한다. 단순히 완성 모델을 실행하는 데서 멈추지 않고, 센서마다 **장착 링크 → Gazebo 센서 → ROS 플러그인 → 토픽 → RViz**가 어떻게 이어지는지 실제 Xacro 코드로 확인한다.

예제는 **ROS 2 Humble + Gazebo Classic 11 + `gazebo_ros_pkgs` 3.9 계열**을 대상으로 한다. 새 Gazebo에서 사용하는 `ros_gz` 플러그인이나 `<gz_frame_id>` 같은 태그를 이 예제에 섞어 쓰지 않아야 한다.

이 장의 학습 흐름은 [MOGI-ROS Week-5-6 Gazebo sensors](https://github.com/MOGI-ROS/Week-5-6-Gazebo-sensors)의 센서별 실습 구성을 참고한다. 다만 대상 시뮬레이터가 다르므로 모델 구조, 플러그인, 토픽 계약, 코드와 설명은 Gazebo Classic 11에 맞게 새로 작성한다.

## 5.1 학습 목표

이 장을 마치면 다음 작업을 수행할 수 있다.

- URDF의 `link`와 `joint`로 센서 장착 위치와 TF를 정의한다.
- `<gazebo reference="...">` 안에 SDF `<sensor>`와 `gazebo_ros_pkgs` 플러그인을 작성한다.
- IMU, mono/RGB, stereo, RGBD, 네이티브 wide-angle 카메라, 2D/3D LiDAR의 핵심 파라미터를 조정한다.
- 센서별 Xacro를 파일로 분리하고 메인 로봇에서 `xacro:include`와 매크로 호출로 재사용한다.
- ROS 2 토픽의 타입, 주기, QoS, `header.frame_id`를 확인한다.
- RViz에서 IMU, 영상, LaserScan, PointCloud2, wheel odom 경로를 시각화한다.
- Gazebo Classic의 네이티브 wide-angle 카메라와 Humble ROS 카메라 플러그인의 호환 한계를 설명한다.

## 5.2 예제 파일 구조

센서 구현을 메인 URDF 하나에 모두 넣으면 다른 로봇에 센서를 재사용하기 어렵고 코드 검토도 복잡해진다. 이 예제는 센서 종류마다 Xacro 모듈을 분리한다.

```text
gazebo_tutorial_description/urdf/
├── sensor_bot.urdf.xacro          # 차체, 구동계, 센서 조합
└── sensors/
    ├── sensor_common.xacro        # 장착 링크와 optical frame
    ├── imu_sensor.xacro
    ├── mono_rgb_camera.xacro
    ├── stereo_camera.xacro
    ├── rgbd_camera.xacro
    ├── fisheye_camera.xacro       # Classic wideanglecamera와 equidistant 렌즈
    ├── lidar_2d.xacro
    └── lidar_3d.xacro
```

`CMakeLists.txt`는 `urdf` 디렉터리 전체를 설치하므로 `sensors/` 아래 파일도 함께 설치된다.

```cmake
install(
  DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)
```

### 센서 모듈을 가져오는 방법

메인 파일 `sensor_bot.urdf.xacro`의 시작 부분은 다음처럼 센서 모듈을 가져온다. Xacro에서 다른 파일을 가져오는 태그는 XML의 일반 `import`가 아니라 `xacro:include`이다.

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="sensor_bot">
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/sensor_common.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/imu_sensor.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/mono_rgb_camera.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/stereo_camera.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/rgbd_camera.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/fisheye_camera.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/lidar_2d.xacro"/>
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/sensors/lidar_3d.xacro"/>
  ...
</robot>
```

가져온 매크로는 다음처럼 필요한 위치와 설정만 넘겨 호출한다. 메인 파일은 센서 내부 구현보다 **어떤 센서를 어디에 장착하는가**를 보여 주는 조립 명세가 된다.

```xml
<xacro:gazebo_imu_sensor
  prefix="imu" parent="base_link" xyz="0 0 0.10"
  topic="imu/data" update_rate="100.0"/>

<xacro:gazebo_lidar_2d
  prefix="lidar_2d" parent="base_link" xyz="0.13 0 0.22"
  topic="scan" samples="720" update_rate="15.0"/>
```

`prefix`를 바꾸면 link, sensor, plugin 이름이 함께 바뀌므로 같은 센서 매크로를 여러 번 호출할 수 있다. 여러 로봇이나 동일 종류의 센서를 동시에 사용할 때는 `ros_namespace`와 토픽도 함께 분리해야 한다.

## 5.3 센서 모델 실행

카메라와 3D LiDAR는 CPU와 GPU 부하가 크므로 `sensor_profile` 인자로 필요한 묶음만 생성한다.

| 프로필 | 생성되는 센서 | 추천 용도 |
|---|---|---|
| `all` | IMU, mono, stereo, RGBD, wide-angle, 2D/3D LiDAR | 전체 인터페이스 확인 |
| `cameras` | IMU와 네 종류의 카메라 | 영상 실습 |
| `lidars` | IMU와 2D/3D LiDAR | 거리 센서 실습 |
| `minimal` | 구동계와 IMU | TF·odometry·headless 점검 |

워크스페이스를 빌드하고 전체 센서 모델을 실행한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all
```

LiDAR만 확인하려면 다음처럼 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars
```

선택되지 않은 센서의 링크도 Xacro 조건문에서 생성하지 않으므로 해당 TF와 토픽이 없는 것이 정상이다.

생성된 URDF만 먼저 검사하려면 다음 명령을 사용한다.

```bash
xacro \
  $(ros2 pkg prefix gazebo_tutorial_description)/share/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro \
  sensor_profile:=all > /tmp/sensor_bot.urdf
check_urdf /tmp/sensor_bot.urdf
```

## 5.4 센서 데이터가 ROS 2까지 오는 구조

하나의 센서는 세 층으로 구성된다.

1. URDF의 `link`와 fixed `joint`가 장착 위치와 TF를 정의한다.
2. `<gazebo reference="센서_링크">` 안의 SDF `<sensor>`가 Gazebo 측정값을 생성한다.
3. `<plugin>`이 Gazebo 측정값을 ROS 2 메시지로 변환해 발행한다.

2D LiDAR를 축약한 다음 코드에서 세 층을 한 번에 확인할 수 있다.

```xml
<!-- 1. URDF: 센서 링크와 장착 joint -->
<link name="lidar_2d_link"> ... </link>
<joint name="lidar_2d_link_joint" type="fixed">
  <parent link="base_link"/>
  <child link="lidar_2d_link"/>
  <origin xyz="0.13 0 0.22" rpy="0 0 0"/>
</joint>

<!-- 2. SDF 확장: Gazebo가 ray를 계산 -->
<gazebo reference="lidar_2d_link">
  <sensor name="lidar_2d_sensor" type="ray">
    <update_rate>15</update_rate>
    <ray> ... </ray>

    <!-- 3. ROS 플러그인: LaserScan을 /scan으로 발행 -->
    <plugin name="lidar_2d_ros" filename="libgazebo_ros_ray_sensor.so">
      <ros><remapping>~/out:=scan</remapping></ros>
      <output_type>sensor_msgs/LaserScan</output_type>
      <frame_name>lidar_2d_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

`gazebo reference`와 `frame_name`은 역할이 다르다. `reference`는 센서를 Gazebo의 어느 링크에 붙일지 정하고, `frame_name`은 ROS 메시지 헤더에 기록할 좌표계를 정한다. 두 이름이 TF로 연결되지 않으면 토픽은 발행되지만 RViz에서 `No transform` 오류가 발생한다.

## 5.5 공통 장착 링크와 optical frame

`sensor_common.xacro`의 `sensor_mount_box`는 센서 외형, 관성, fixed joint를 한 번에 생성한다. 실제 제품 mesh를 사용할 때는 이 매크로의 visual만 교체하고, 센서 원점은 제품 데이터시트에 맞추는 방식으로 확장할 수 있다.

```xml
<xacro:macro
  name="sensor_mount_box"
  params="link_name parent xyz rpy:='0 0 0'
          size_x:=0.05 size_y:=0.05 size_z:=0.05
          color:='sensor_gray' mass:=0.05">
  <link name="${link_name}">
    <visual>
      <geometry><box size="${size_x} ${size_y} ${size_z}"/></geometry>
      <material name="${color}"/>
    </visual>
    <inertial>
      <mass value="${mass}"/>
      <inertia
        ixx="${mass * (size_y * size_y + size_z * size_z) / 12.0}"
        ixy="0" ixz="0"
        iyy="${mass * (size_x * size_x + size_z * size_z) / 12.0}"
        iyz="0"
        izz="${mass * (size_x * size_x + size_y * size_y) / 12.0}"/>
    </inertial>
  </link>
  <joint name="${link_name}_joint" type="fixed">
    <parent link="${parent}"/>
    <child link="${link_name}"/>
    <origin xyz="${xyz}" rpy="${rpy}"/>
  </joint>
</xacro:macro>
```

`size_x`, `size_y`, `size_z`는 visual box와 직육면체 관성식에 동시에 사용한다. 외형 치수만 바꾸고 관성을 고정 상수로 남기면 모델의 회전 응답이 외형과 맞지 않으므로 두 계산의 입력을 반드시 공유해야 한다.

카메라에는 일반 장착 프레임과 ROS optical frame이 모두 필요하다. REP-103 카메라 optical frame은 `+Z` 전방, `+X` 오른쪽, `+Y` 아래쪽을 사용한다. 로봇의 일반 프레임은 보통 `+X` 전방이므로 다음 고정 회전을 추가한다.

```xml
<xacro:macro name="sensor_optical_frame" params="frame_name parent">
  <link name="${frame_name}"/>
  <joint name="${frame_name}_joint" type="fixed">
    <parent link="${parent}"/>
    <child link="${frame_name}"/>
    <origin xyz="0 0 0" rpy="${-pi / 2.0} 0 ${-pi / 2.0}"/>
  </joint>
</xacro:macro>
```

이 회전을 생략하면 영상 자체는 보일 수 있지만 RGBD point cloud가 로봇의 옆이나 뒤를 향해 나타난다.

## 5.6 토픽과 프레임 계약

`sensor_profile:=all`에서 다음 인터페이스를 사용한다.

| 기능 | ROS 2 토픽 | 메시지 타입 | 메시지 프레임 | 주기 |
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
| wide-angle 영상 | `/fisheye/image_raw` | `sensor_msgs/msg/Image` | `fisheye_camera_optical_frame` | 10 Hz |
| wide-angle 정보 | `/fisheye/camera_info` | `sensor_msgs/msg/CameraInfo` | `fisheye_camera_optical_frame` | 10 Hz |
| 2D LiDAR | `/scan` | `sensor_msgs/msg/LaserScan` | `lidar_2d_link` | 15 Hz |
| 3D LiDAR | `/points` | `sensor_msgs/msg/PointCloud2` | `lidar_3d_link` | 10 Hz |

토픽 타입을 한 번에 검사한다.

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

빈 결과가 나오면 현재 profile에 센서가 포함되는지와 Gazebo 터미널의 플러그인 로드 오류를 먼저 확인한다.

## 5.7 Wheel odometry와 경로

Wheel odometry는 별도 Gazebo `<sensor>`가 아니라 차동 구동 플러그인이 바퀴 joint 회전을 적분해 만든다. 핵심 설정은 다음과 같다.

```xml
<plugin name="sensor_bot_diff_drive" filename="libgazebo_ros_diff_drive.so">
  <ros>
    <namespace>/</namespace>
    <remapping>cmd_vel:=cmd_vel</remapping>
    <remapping>odom:=odom</remapping>
  </ros>
  <update_rate>50</update_rate>
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>${wheel_separation}</wheel_separation>
  <wheel_diameter>${2.0 * wheel_radius}</wheel_diameter>
  <odometry_source>0</odometry_source>
  <publish_odom>true</publish_odom>
  <publish_odom_tf>true</publish_odom_tf>
  <publish_wheel_tf>false</publish_wheel_tf>
  <odometry_frame>odom</odometry_frame>
  <robot_base_frame>base_footprint</robot_base_frame>
</plugin>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `left_joint`, `right_joint` | 좌·우 구동 joint 이름 | wheel joint |
| `wheel_separation` | 좌·우 바퀴 중심 간 거리 | 0.43 m |
| `wheel_diameter` | 바퀴 직경 | 0.20 m |
| `odometry_source` | `0`은 encoder 적분, `1`은 world pose | 0 |
| `publish_odom` | `/odom` 메시지 발행 여부 | true |
| `publish_odom_tf` | `odom → base_footprint` TF 발행 여부 | true |
| `publish_wheel_tf` | 플러그인의 wheel TF 발행 여부 | false |

이 예제는 `odometry_source=0`을 사용하므로 바퀴가 미끄러지면 `/odom`과 Gazebo world pose가 달라진다. 이 차이는 실제 wheel encoder 기반 위치 추정의 누적 오차를 재현한다.

키보드로 원호를 그리며 주행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

다른 터미널에서 odom과 TF를 확인한다.

```bash
ros2 topic hz /odom
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_footprint
```

RViz에서 다음 순서로 경로를 확인한다.

1. **Global Options → Fixed Frame**을 `odom`으로 설정한다.
2. **Add → Path**를 추가하고 Topic을 `/wheel_odom_path`로 설정한다.
3. **Add → Odometry**를 추가하고 Topic을 `/odom`으로 설정한다.
4. `u`, `o`, `m`, `.` 키로 원호를 주행해 경로 선과 odometry 화살표가 함께 쌓이는지 확인한다.

`publish_wheel_tf`는 `false`로 둔다. `libgazebo_ros_joint_state_publisher.so`가 `/joint_states`를 발행하고 `robot_state_publisher`가 URDF joint를 이용해 wheel TF를 계산하므로 중복 TF를 방지할 수 있다.

## 5.8 IMU

### Xacro 구현

`imu_sensor.xacro`는 장착 링크와 Gazebo IMU, ROS 플러그인을 하나의 매크로로 묶는다.

```xml
<xacro:macro
  name="gazebo_imu_sensor"
  params="prefix parent xyz rpy:='0 0 0'
          ros_namespace:='/' topic:='imu/data'
          update_rate:=100.0 angular_stddev:=0.0002
          linear_stddev:=0.017 visualize:=false">
  <xacro:sensor_mount_box
    link_name="${prefix}_link" parent="${parent}"
    xyz="${xyz}" rpy="${rpy}"
    size_x="0.05" size_y="0.04" size_z="0.02"/>

  <gazebo reference="${prefix}_link">
    <sensor name="${prefix}_sensor" type="imu">
      <update_rate>${update_rate}</update_rate>
      <imu>
        <angular_velocity>
          <x><noise type="gaussian"><mean>0</mean><stddev>${angular_stddev}</stddev></noise></x>
          ...
        </angular_velocity>
        <linear_acceleration>
          <x><noise type="gaussian"><mean>0</mean><stddev>${linear_stddev}</stddev></noise></x>
          ...
        </linear_acceleration>
      </imu>
      <plugin name="${prefix}_ros" filename="libgazebo_ros_imu_sensor.so">
        <ros><remapping>~/out:=${topic}</remapping></ros>
        <frame_name>${prefix}_link</frame_name>
        <initial_orientation_as_reference>false</initial_orientation_as_reference>
      </plugin>
    </sensor>
  </gazebo>
</xacro:macro>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `update_rate` | 시뮬레이션 측정 주기 | 100 Hz |
| `angular_stddev` | 각속도 Gaussian 잡음 표준편차 | 0.0002 rad/s |
| `linear_stddev` | 선가속도 Gaussian 잡음 표준편차 | 0.017 m/s² |
| `initial_orientation_as_reference` | 시작 자세를 0 기준으로 사용할지 결정 | false |
| `frame_name` | `Imu.header.frame_id` | `imu_link` |
| `~/out` remap | ROS 출력 토픽 | `/imu/data` |

### 토픽과 RViz 확인

```bash
ros2 topic hz /imu/data
ros2 topic echo /imu/data --once
ros2 run tf2_ros tf2_echo base_link imu_link
```

정지 상태에서도 Z 선가속도는 중력에 대응하는 약 `+9.8 m/s²` 부근을 나타내며 설정한 잡음이 섞인다. 로봇을 회전하면 Z 각속도와 orientation quaternion이 변한다.

Humble에서 IMU 메시지의 자세를 직접 시각화하려면 IMU RViz 플러그인을 설치한다.

```bash
sudo apt install ros-humble-rviz-imu-plugin
```

RViz에서 **Add → rviz_imu_plugin → Imu**를 추가하고 Topic을 `/imu/data`로 설정한다. **TF** Display의 `imu_link` 축은 센서의 장착 자세만 보여 주며 IMU 메시지를 구독하지 않으므로 데이터 검증을 대신하지 못한다.

작은 실험으로 `angular_stddev`를 `0.02`로 높여 정지 상태 각속도의 흔들림을 비교한다. 매크로 인자 하나만 바꾸면 세 축에 같은 잡음 설정을 재사용할 수 있다.

## 5.9 Mono/RGB 카메라

### Xacro 구현

Gazebo의 `camera` 센서는 영상 렌더링을 담당하고 `libgazebo_ros_camera.so`가 `Image`와 `CameraInfo`를 발행한다.

```xml
<sensor name="${prefix}_sensor" type="camera">
  <always_on>true</always_on>
  <visualize>${visualize}</visualize>
  <update_rate>${update_rate}</update_rate>
  <camera name="${camera_name}">
    <horizontal_fov>${horizontal_fov}</horizontal_fov>
    <image>
      <width>${width}</width>
      <height>${height}</height>
      <format>${format}</format>
    </image>
    <clip><near>${near}</near><far>${far}</far></clip>
    <noise>
      <type>gaussian</type><mean>0</mean><stddev>${image_noise_stddev}</stddev>
    </noise>
  </camera>
  <plugin name="${prefix}_ros" filename="libgazebo_ros_camera.so">
    <ros><namespace>${ros_namespace}</namespace></ros>
    <camera_name>${camera_name}</camera_name>
    <frame_name>${prefix}_optical_frame</frame_name>
  </plugin>
</sensor>
```

메인 파일은 단안 카메라를 다음처럼 호출한다.

```xml
<xacro:gazebo_mono_rgb_camera
  prefix="camera" parent="base_link" xyz="0.30 -0.12 0.07"
  camera_name="camera" format="L8"
  width="320" height="240" update_rate="15.0"/>
```

| 파라미터 | 의미 | 조정 효과 |
|---|---|---|
| `format` | `L8` 또는 `R8G8B8` | mono8 또는 RGB 영상 |
| `width`, `height` | 영상 해상도 | 높을수록 렌더링 부하 증가 |
| `horizontal_fov` | 수평 화각, rad | 클수록 넓게 보이며 물체가 작아짐 |
| `near`, `far` | 렌더링 절단 거리 | 범위 밖 물체를 그리지 않음 |
| `image_noise_stddev` | 정규화된 color channel Gaussian 잡음 | 영상 노이즈 증가 |
| `update_rate` | 영상 생성 주기 | 높을수록 부하와 대역폭 증가 |
| `camera_name` | 토픽의 기본 이름 | `camera/image_raw` 등을 생성 |
| `frame_name` | 영상 헤더의 프레임 | optical frame을 사용 |

`format="R8G8B8"`로 바꾸면 같은 매크로를 RGB 카메라로 사용할 수 있다. 센서 장착과 플러그인 코드를 복사할 필요가 없다.

### 토픽과 RViz 확인

```bash
ros2 topic echo /camera/image_raw --field encoding --once
ros2 topic hz /camera/image_raw
ros2 topic echo /camera/camera_info --once
```

RViz에서 **Add → Image**를 추가하고 Topic을 `/camera/image_raw`로 설정한다. 3D 장면에 영상을 투영하려면 **Camera** Display를 추가한다. Camera Display는 `/camera/camera_info`와 `camera_optical_frame` TF도 필요하다.

작은 실험으로 `horizontal_fov`를 `1.047`에서 `0.52`로 줄여 같은 물체가 영상에서 얼마나 크게 보이는지 비교한다.

## 5.10 Stereo 카메라

### Xacro 구현

Gazebo Classic의 `multicamera` 센서는 한 update에서 왼쪽과 오른쪽 영상을 렌더링하므로 독립 camera 센서 두 개보다 timestamp를 맞추기 쉽다.

```xml
<sensor name="${prefix}_sensor" type="multicamera">
  <update_rate>${update_rate}</update_rate>
  <camera name="left">
    <pose>0 ${baseline / 2.0} 0 0 0 0</pose>
    <horizontal_fov>${horizontal_fov}</horizontal_fov>
    <image>
      <width>${width}</width><height>${height}</height><format>R8G8B8</format>
    </image>
    <clip><near>${near}</near><far>${far}</far></clip>
    <noise>
      <type>gaussian</type><mean>0</mean><stddev>${image_noise_stddev}</stddev>
    </noise>
  </camera>
  <camera name="right">
    <pose>0 ${-baseline / 2.0} 0 0 0 0</pose>
    ...
  </camera>
  <plugin name="${prefix}_ros" filename="libgazebo_ros_camera.so">
    <camera_name>${camera_name}</camera_name>
    <frame_name>${prefix}_optical_frame</frame_name>
  </plugin>
</sensor>
```

```xml
<xacro:gazebo_stereo_camera
  prefix="stereo_camera" parent="base_link" xyz="0.30 0 0.15"
  camera_name="stereo" baseline="0.08"
  width="320" height="240" update_rate="10.0"/>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `baseline` | 좌·우 카메라 중심 간 거리 | 0.08 m |
| `pose` | 각 sub-camera의 위치 | ±baseline/2 |
| `image_noise_stddev` | 좌·우 영상의 정규화된 channel 잡음 | 0.003 |
| `camera_name` | 토픽 루트 | `/stereo` |
| `update_rate` | 좌·우 영상 생성 주기 | 10 Hz |

Stereo의 `<camera><noise>`도 depth나 disparity 잡음이 아니라 각 RGB channel `[0, 1]`에 적용되는 영상 잡음이다. 매크로는 같은 값을 좌·우 카메라에 적용해 두 영상의 설정을 일관되게 유지한다.

토픽을 확인한다.

```bash
ros2 topic hz /stereo/left/image_raw
ros2 topic hz /stereo/right/image_raw
ros2 topic echo /stereo/left/camera_info --once
```

RViz에 Image Display를 두 개 추가하고 `/stereo/left/image_raw`, `/stereo/right/image_raw`를 각각 설정한다. 가까운 물체가 두 영상에서 수평 방향으로 다르게 보이는 시차를 확인한다.

이 예제는 같은 sensor update에서 생성되는 **동기화된 raw stereo pair**와 물리적인 baseline을 확인하는 최소 구성이다. Humble의 multicamera 출력은 공통 `stereo_camera_optical_frame`을 사용하며, 이 예제는 의도적으로 `hack_baseline`을 넣지 않는다. 플러그인은 하나의 `hack_baseline` 값을 좌·우 CameraInfo에 동일하게 적용하므로 이를 추가하는 것만으로 올바른 좌·우 projection matrix가 만들어진다고 볼 수 없기 때문이다. 정밀한 disparity와 depth 계산에는 좌·우 optical frame, 각 카메라의 실제 보정 행렬, rectification과 CameraInfo republisher를 센서 사양에 맞게 추가해야 한다.

## 5.11 RGBD 카메라

### Xacro 구현

Gazebo의 `depth` 센서와 `libgazebo_ros_camera.so`를 결합하면 RGB, depth, CameraInfo, PointCloud2를 한 번에 발행한다.

```xml
<sensor name="${prefix}_sensor" type="depth">
  <update_rate>${update_rate}</update_rate>
  <camera name="${camera_name}">
    <horizontal_fov>${horizontal_fov}</horizontal_fov>
    <image>
      <width>${width}</width><height>${height}</height><format>R8G8B8</format>
    </image>
    <clip><near>${min_depth}</near><far>${max_depth}</far></clip>
    <noise>
      <type>gaussian</type><mean>0</mean><stddev>${image_noise_stddev}</stddev>
    </noise>
  </camera>
  <plugin name="${prefix}_ros" filename="libgazebo_ros_camera.so">
    <camera_name>${camera_name}</camera_name>
    <frame_name>${prefix}_optical_frame</frame_name>
    <min_depth>${min_depth}</min_depth>
    <max_depth>${max_depth}</max_depth>
  </plugin>
</sensor>
```

```xml
<xacro:gazebo_rgbd_camera
  prefix="rgbd_camera" parent="base_link" xyz="0.30 0.12 0.07"
  camera_name="rgbd" min_depth="0.10" max_depth="12.0"
  width="320" height="240" update_rate="10.0"/>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `min_depth` | 유효한 최소 깊이와 near clip | 0.10 m |
| `max_depth` | 유효한 최대 깊이와 far clip | 12.0 m |
| `image_noise_stddev` | 정규화된 RGB channel Gaussian 잡음 | 0.002 |
| `width`, `height` | RGB/depth 해상도 | 320×240 |
| `frame_name` | RGB, depth, cloud 공통 프레임 | optical frame |

`<camera><noise>`는 깊이 거리 잡음이 아니다. Gazebo는 프레임마다 각 픽셀의 정규화된 color channel `[0, 1]`에 이 잡음을 더한다. `libgazebo_ros_camera.so`의 depth callback은 Gazebo가 만든 float depth buffer를 그대로 복사하고, `min_depth`와 `max_depth` 밖의 값만 음·양의 무한대로 바꾼다. 실제 깊이 측정의 거리 의존 잡음이나 결측 패턴을 재현하려면 depth 후처리 노드나 커스텀 센서 플러그인이 필요하다.

생성되는 토픽은 다음과 같다.

- `/rgbd/image_raw`: RGB 영상
- `/rgbd/camera_info`: RGB 보정 정보
- `/rgbd/depth/image_raw`: `32FC1` 깊이 영상
- `/rgbd/depth/camera_info`: 깊이 보정 정보
- `/rgbd/points`: 색 정보를 포함한 point cloud

```bash
ros2 topic echo /rgbd/depth/image_raw --field encoding --once
ros2 topic hz /rgbd/points
ros2 topic echo /rgbd/points --field header --once
```

RViz에서 Image Display 두 개에 `/rgbd/image_raw`와 `/rgbd/depth/image_raw`를 설정한다. PointCloud2 Display에는 `/rgbd/points`를 설정하고 `Color Transformer=RGB8`, `Style=Points`, `Size (Pixels)=2` 정도로 둔다.

point cloud 방향이 잘못되면 다음 TF를 먼저 검사한다.

```bash
ros2 run tf2_ros tf2_echo base_link rgbd_camera_optical_frame
```

작은 실험으로 `max_depth`를 `3.0`으로 줄여 3 m보다 먼 점이 사라지는지 확인한다.

## 5.12 네이티브 wide-angle 카메라

Gazebo Classic 11은 cubemap을 렌더링한 뒤 렌즈 함수로 투영하는 `wideanglecamera` 센서를 제공한다. 이 예제는 `equidistant` 렌즈를 선택해 일반 pinhole 카메라보다 넓은 시야와 어안 왜곡을 직접 렌더링한다.

Humble의 `libgazebo_ros_camera.so`는 내부에서 부모 센서를 `CameraSensor`로 변환해 Gazebo `CameraPlugin`을 초기화한다. Gazebo 11의 `WideAngleCameraSensor`는 `CameraSensor`를 상속하므로 네이티브 wide-angle 센서에도 이 플러그인을 연결해 ROS 영상을 발행할 수 있다.

### Xacro 구현

```xml
<sensor name="${prefix}_sensor" type="wideanglecamera">
  <update_rate>${update_rate}</update_rate>
  <camera name="${camera_name}">
    <horizontal_fov>${horizontal_fov}</horizontal_fov>
    <image>
      <width>${width}</width><height>${height}</height><format>R8G8B8</format>
    </image>
    <clip><near>${near}</near><far>${far}</far></clip>
    <lens>
      <type>${lens_type}</type>
      <scale_to_hfov>true</scale_to_hfov>
      <cutoff_angle>${cutoff_angle}</cutoff_angle>
      <env_texture_size>${env_texture_size}</env_texture_size>
    </lens>
  </camera>
  <plugin name="${prefix}_ros" filename="libgazebo_ros_camera.so">
    <camera_name>${camera_name}</camera_name>
    <frame_name>${prefix}_optical_frame</frame_name>
  </plugin>
</sensor>
```

```xml
<xacro:gazebo_fisheye_camera
  prefix="fisheye_camera" parent="base_link" xyz="0.06 -0.10 0.22"
  camera_name="fisheye" horizontal_fov="3.1415926535"
  lens_type="equidistant" cutoff_angle="1.5707"
  env_texture_size="512" update_rate="10.0"/>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `horizontal_fov` | 최종 영상의 수평 화각 | 약 π rad |
| `lens_type` | cubemap을 영상 평면에 투영하는 렌즈 함수 | `equidistant` |
| `scale_to_hfov` | 렌즈 스케일을 요청한 FOV에 맞출지 결정 | true |
| `cutoff_angle` | 렌즈가 렌더링하는 최대 각도 경계 | 약 π/2 rad |
| `env_texture_size` | cubemap 각 면의 texture 크기 | 512 px |
| `update_rate` | wide-angle 영상 생성 주기 | 10 Hz |

```bash
ros2 topic hz /fisheye/image_raw
ros2 topic echo /fisheye/camera_info --once
```

RViz에서 Image Display의 Topic을 `/fisheye/image_raw`로 설정한다. 일반 카메라와 비교해 영상 가장자리의 직선이 크게 휘고 더 넓은 시야가 보이는지 확인한다.

### `CameraInfo`의 중요한 한계

영상은 Gazebo의 네이티브 equidistant 렌즈로 렌더링되지만 `libgazebo_ros_camera.so`가 만드는 `CameraInfo`는 wide-angle 렌즈 모델을 그대로 표현하지 못한다. Humble 3.9.0 구현은 `distortion_model`을 `plumb_bob`으로 설정하고 pinhole 수평 FOV 공식으로 focal length를 계산한다. 따라서 `/fisheye/camera_info`의 timestamp, frame, 해상도는 연결 점검에 사용할 수 있지만, `K`, `P`, `D`를 정확한 equidistant 보정값으로 신뢰하면 안 된다.

RViz Image Display로 영상을 관찰하는 데에는 문제가 없다. 그러나 OpenCV fisheye 보정, 3D ray 역투영, SLAM처럼 정확한 내·외부 파라미터가 필요한 작업에는 실제 equidistant calibration을 발행하는 별도 CameraInfo 노드나 커스텀 Gazebo 플러그인이 필요하다.

작은 실험으로 `lens_type`을 `stereographic`, `equisolid_angle`, `orthographic`으로 바꾸어 같은 장면의 투영 차이를 비교한다. `env_texture_size`를 512에서 256으로 낮추면 렌더링 부하는 줄지만 영상 가장자리 품질도 낮아질 수 있다.

## 5.13 2D LiDAR

### Xacro 구현

2D LiDAR는 Gazebo `ray` 센서의 수평 scan 한 줄을 `sensor_msgs/msg/LaserScan`으로 변환한다.

```xml
<sensor name="${prefix}_sensor" type="ray">
  <update_rate>${update_rate}</update_rate>
  <ray>
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
      <type>gaussian</type><mean>0</mean><stddev>${noise_stddev}</stddev>
    </noise>
  </ray>
  <plugin name="${prefix}_ros" filename="libgazebo_ros_ray_sensor.so">
    <ros><remapping>~/out:=${topic}</remapping></ros>
    <output_type>sensor_msgs/LaserScan</output_type>
    <frame_name>${prefix}_link</frame_name>
  </plugin>
</sensor>
```

```xml
<xacro:gazebo_lidar_2d
  prefix="lidar_2d" parent="base_link" xyz="0.13 0 0.22"
  topic="scan" update_rate="15.0" samples="720"
  min_angle="-3.14159265" max_angle="3.14159265"
  min_range="0.12" max_range="15.0"/>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `samples` | 한 scan의 수평 ray 수 | 720 |
| `min_angle`, `max_angle` | 수평 scan 범위 | -π ~ +π rad |
| `min_range`, `max_range` | 유효 거리 범위 | 0.12~15.0 m |
| `range_resolution` | 거리 분해능 | 0.01 m |
| `noise_stddev` | 거리 Gaussian 잡음 | 0.01 m |
| `output_type` | ROS 출력 메시지 | `LaserScan` |

```bash
ros2 topic hz /scan
ros2 topic echo /scan --field ranges --once
ros2 run tf2_ros tf2_echo base_link lidar_2d_link
```

RViz에서 **LaserScan** Display를 추가하고 다음 값을 설정한다.

- Topic: `/scan`
- Reliability: `Best Effort`
- Style: `Points`
- Size (m): `0.03`
- Decay Time: `0.2`

Gazebo world에 box를 놓고 로봇을 회전시켜 점들이 장애물 표면에 붙어 보이는지 확인한다. `samples`를 90과 720으로 바꾸면 원형 물체의 윤곽 차이가 뚜렷하다.

## 5.14 3D LiDAR

### Xacro 구현

3D LiDAR도 CPU `ray` 센서를 사용하지만 vertical scan을 추가하고 결과를 `PointCloud2`로 발행한다.

```xml
<ray>
  <scan>
    <horizontal>
      <samples>${horizontal_samples}</samples>
      <min_angle>${min_horizontal_angle}</min_angle>
      <max_angle>${max_horizontal_angle}</max_angle>
    </horizontal>
    <vertical>
      <samples>${vertical_samples}</samples>
      <min_angle>${min_vertical_angle}</min_angle>
      <max_angle>${max_vertical_angle}</max_angle>
    </vertical>
  </scan>
  <range>
    <min>${min_range}</min><max>${max_range}</max>
    <resolution>${range_resolution}</resolution>
  </range>
</ray>
<plugin name="${prefix}_ros" filename="libgazebo_ros_ray_sensor.so">
  <ros><remapping>~/out:=${topic}</remapping></ros>
  <output_type>sensor_msgs/PointCloud2</output_type>
  <frame_name>${prefix}_link</frame_name>
</plugin>
```

```xml
<xacro:gazebo_lidar_3d
  prefix="lidar_3d" parent="base_link" xyz="-0.12 0 0.22"
  topic="points" update_rate="10.0"
  horizontal_samples="360" vertical_samples="16"
  min_vertical_angle="-0.261799" max_vertical_angle="0.261799"
  min_range="0.20" max_range="20.0"/>
```

| 파라미터 | 의미 | 예제 값 |
|---|---|---:|
| `horizontal_samples` | 한 층의 수평 ray 수 | 360 |
| `vertical_samples` | 수직 채널 수 | 16 |
| 수평 각도 범위 | 360° 회전 범위 | -π ~ +π rad |
| 수직 각도 범위 | 위·아래 시야 | 약 -15° ~ +15° |
| `min_range`, `max_range` | 유효 거리 범위 | 0.20~20.0 m |
| `output_type` | ROS 출력 메시지 | `PointCloud2` |

```bash
ros2 topic hz /points
ros2 topic echo /points --field width --once
ros2 run tf2_ros tf2_echo base_link lidar_3d_link
```

RViz에서 **PointCloud2** Display를 추가하고 다음 값을 설정한다.

- Topic: `/points`
- Reliability: `Best Effort`
- Style: `Points`
- Size (Pixels): `2`
- Color Transformer: `AxisColor`
- Axis: `Z`

`/points`는 3D LiDAR이고 `/rgbd/points`는 RGBD 카메라의 cloud이다. RViz Display 이름을 `3D LiDAR`와 `RGBD Points`로 바꾸면 혼동을 줄일 수 있다.

작은 실험으로 `vertical_samples`를 4, 16, 32로 바꾸어 수직 해상도와 CPU 부하를 비교한다.

## 5.15 QoS 확인

RViz의 Topic 목록에는 이름이 보이지만 화면이 비어 있다면 QoS 호환성을 확인한다. Humble `gazebo_ros_pkgs`의 camera, IMU, ray sensor publisher는 일반적으로 Reliable + Volatile로 생성된다. 제공하는 `sensors.rviz`는 subscriber Reliability를 Best Effort로 두어 Reliable과 Best Effort publisher 모두에 연결되기 쉽게 구성한다.

실행 환경의 실제 QoS가 문서의 일반값보다 우선한다.

```bash
ros2 topic info /scan -v
ros2 topic info /rgbd/points -v
ros2 topic info /imu/data -v
```

다음 항목을 확인한다.

- Publisher count가 1 이상인지 확인한다.
- Topic type이 RViz Display가 기대하는 타입과 같은지 확인한다.
- Publisher와 subscriber의 Reliability가 호환되는지 확인한다.
- Durability가 `VOLATILE`인지 확인한다.

Reliable publisher는 Best Effort subscriber 요청을 만족할 수 있지만 Best Effort publisher는 Reliable subscriber 요청을 만족하지 못한다.

## 5.16 TF 전체 점검

센서 메시지의 모든 header frame이 `odom`까지 연결되어야 RViz의 한 장면에 데이터를 겹칠 수 있다.

```text
odom
└── base_footprint                 (diff drive plugin)
    └── base_link                  (robot_state_publisher)
        ├── imu_link
        ├── camera_link ── camera_optical_frame
        ├── stereo_camera_link ── stereo_camera_optical_frame
        ├── rgbd_camera_link ── rgbd_camera_optical_frame
        ├── fisheye_camera_link ── fisheye_camera_optical_frame
        ├── lidar_2d_link
        └── lidar_3d_link
```

전체 TF를 PDF로 저장한다.

```bash
ros2 run tf2_tools view_frames
```

특정 센서만 검사할 때는 다음 명령을 사용한다.

```bash
ros2 run tf2_ros tf2_echo odom camera_optical_frame
ros2 run tf2_ros tf2_echo odom lidar_3d_link
```

`Invalid frame ID`가 나오면 `sensor_profile`과 `robot_state_publisher` 실행 여부를 확인한다. `Extrapolation into the future`가 반복되면 모든 노드가 simulation time을 사용하는지 확인한다.

```bash
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /rviz2 use_sim_time
```

## 5.17 성능 조정

센서 부하는 대략 `update_rate × sample 수 × 렌더링 해상도`에 비례한다. 한 번에 모든 값을 낮추기보다 다음 순서로 병목을 분리한다.

1. `sensor_profile:=minimal`에서 물리와 wheel odom이 정상 속도로 동작하는지 확인한다.
2. `lidars`를 켜고 3D LiDAR의 horizontal/vertical samples와 update rate를 조정한다.
3. `cameras`를 켜고 영상 width, height, update rate를 조정한다.
4. Gazebo GUI 센서 시각화가 필요하지 않으면 `<visualize>false>`로 설정한다.

예제의 기본 부하는 다음과 같다.

| 센서 | 주요 비용 설정 |
|---|---|
| mono | 320×240, 15 Hz |
| stereo | 320×240 두 장, 10 Hz |
| RGBD | 320×240, 10 Hz + point cloud |
| wide-angle | 320×240, 10 Hz, cubemap 512 |
| 2D LiDAR | 720 ray, 15 Hz |
| 3D LiDAR | 360×16 ray, 10 Hz |

## 5.18 문제 해결

### 토픽 자체가 없는 경우

```bash
ros2 topic list | sort
ros2 node list
```

- 현재 profile에 원하는 센서가 포함되는지 확인한다.
- Gazebo 터미널에 `Failed to load plugin` 또는 `unsupported sensor type`이 있는지 확인한다.
- `ros-humble-gazebo-plugins`가 설치되어 있는지 확인한다.
- `gzserver`가 `libgazebo_ros_init.so`와 ROS factory를 사용해 시작되는지 확인한다.

### 토픽은 있지만 주기가 0인 경우

카메라 플러그인은 subscriber가 생긴 뒤 렌더링 출력을 활성화할 수 있다. RViz Image Display나 다음 명령으로 subscriber를 붙인다.

```bash
ros2 topic hz /camera/image_raw
```

Gazebo pause 여부와 `/clock`도 확인한다.

```bash
ros2 topic hz /clock
```

### RViz에 `No transform`이 나타나는 경우

메시지의 실제 frame과 TF를 함께 검사한다.

```bash
ros2 topic echo /scan --field header --once
ros2 run tf2_ros tf2_echo odom lidar_2d_link
```

Fixed Frame을 임시로 센서 frame으로 바꾸는 것은 원인을 가릴 뿐 최종 해결이 아니다. URDF joint, 플러그인의 `frame_name`, `robot_state_publisher`를 바로잡아 `odom`부터 센서까지 연결한다.

### 영상이 검거나 매우 느린 경우

- 카메라가 차체나 장애물 내부에 장착되지 않았는지 Gazebo GUI에서 확인한다.
- `<clip><near>`가 지나치게 큰지 확인한다.
- headless 환경에서 OGRE/OpenGL 렌더링이 가능한지 확인한다.
- 해상도와 update rate를 먼저 낮춘다.
- wide-angle 카메라가 느리면 `env_texture_size`와 update rate를 먼저 낮춘다.

### PointCloud2의 모양이나 색이 이상한 경우

- `/points`와 `/rgbd/points`를 혼동하지 않았는지 확인한다.
- RGBD는 `Color Transformer=RGB8`, 3D LiDAR는 `AxisColor`로 먼저 확인한다.
- RGBD optical frame과 LiDAR frame TF를 각각 확인한다.
- RViz Fixed Frame을 `odom`으로 두고 `use_sim_time=true`인지 확인한다.

## 5.19 센서 모듈을 다른 로봇에 재사용하기

다른 로봇의 메인 Xacro에서 필요한 파일만 include하고 매크로를 호출한다.

```xml
<xacro:include
  filename="$(find gazebo_tutorial_description)/urdf/sensors/sensor_common.xacro"/>
<xacro:include
  filename="$(find gazebo_tutorial_description)/urdf/sensors/lidar_2d.xacro"/>

<xacro:gazebo_lidar_2d
  prefix="front_lidar"
  parent="my_robot_base_link"
  xyz="0.35 0 0.25"
  topic="front/scan"
  samples="1080"
  min_angle="-2.35619"
  max_angle="2.35619"/>
```

이 호출은 `front_lidar_link`, `front_lidar_sensor`, `front_lidar_ros`를 만들고 `/front/scan`을 발행한다. 센서 내부 코드를 복사하지 않으므로 잡음 모델이나 플러그인 설정을 고칠 때 모듈 한 곳만 수정하면 된다.

동일 센서를 두 번 장착할 때는 `prefix`와 `topic`을 모두 다르게 지정한다.

```xml
<xacro:gazebo_lidar_2d
  prefix="front_lidar" parent="base_link" xyz="0.30 0 0.20"
  topic="front/scan" min_angle="-1.57" max_angle="1.57"/>
<xacro:gazebo_lidar_2d
  prefix="rear_lidar" parent="base_link" xyz="-0.30 0 0.20" rpy="0 0 3.14159"
  topic="rear/scan" min_angle="-1.57" max_angle="1.57"/>
```

## 5.20 마무리 점검표

각 센서에 대해 다음 질문에 모두 답할 수 있으면 구성이 완료된 것이다.

- 어떤 URDF link에 장착되며 부모 joint의 `xyz/rpy`는 무엇인지 설명한다.
- Gazebo `<sensor type>`과 물리·렌더링 파라미터를 설명한다.
- 어떤 `libgazebo_ros_*.so` 플러그인을 사용하는지 설명한다.
- ROS 토픽 이름, 메시지 타입, update rate를 확인한다.
- 메시지의 `header.frame_id`가 `odom`까지 TF로 연결되는지 확인한다.
- RViz Display 종류와 QoS를 올바르게 설정한다.
- profile과 주요 파라미터를 바꾸어 예상한 변화가 나타나는지 실험한다.

## 5.21 사용한 Gazebo Classic 플러그인

| 기능 | 플러그인 파일 | 핵심 태그 |
|---|---|---|
| 차동 구동 + wheel odom | `libgazebo_ros_diff_drive.so` | `left_joint`, `right_joint`, `odometry_source`, `publish_odom_tf` |
| wheel joint state | `libgazebo_ros_joint_state_publisher.so` | `joint_name`, `update_rate` |
| IMU | `libgazebo_ros_imu_sensor.so` | `~/out` remap, `frame_name`, `initial_orientation_as_reference` |
| mono/RGB, stereo, RGBD, wide-angle | `libgazebo_ros_camera.so` | `camera_name`, `frame_name`, `min_depth`, `max_depth`; wide-angle lens는 sensor 태그에서 설정 |
| 2D/3D LiDAR | `libgazebo_ros_ray_sensor.so` | `~/out` remap, `output_type`, `frame_name` |

플러그인 설정은 Humble용 [`gazebo_ros_pkgs` 3.9.0 소스](https://github.com/ros-simulation/gazebo_ros_pkgs/tree/3.9.0)를 기준으로 한다. Gazebo Classic 11과 `gazebo_ros_pkgs`는 2025년 1월에 EOL에 도달했다. 이 저장소는 Humble/Classic 프로젝트의 유지보수와 재현을 위한 학습 자료이며 새 프로젝트에서는 최신 Gazebo로 이전할 계획도 함께 세워야 한다.
