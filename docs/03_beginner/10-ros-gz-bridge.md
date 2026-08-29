# Gazebo와 ROS 2를 `ros_gz_bridge`로 연결하기

> **난이도:** 초급
> **Gazebo:** Harmonic
> **ROS 2:** Jazzy
> **선행 학습:** Gazebo Fuel

## 학습 목표

- Gazebo Transport와 ROS 2 DDS가 서로 다른 통신 계층임을 설명한다.
- YAML에서 topic 이름, message type, 방향, QoS를 지정한다.
- 명령은 ROS → Gazebo로, sensor·odom·TF·clock은 Gazebo → ROS로 연결한다.
- image 전용 bridge와 일반 parameter bridge의 역할을 구분한다.
- ROS topic을 RViz의 Image, Camera, LaserScan, PointCloud2, IMU, Odometry, Path display에 연결한다.

## 1. 같은 topic 이름만으로 연결되지는 않는다

Gazebo는 Gazebo Transport를 사용하고 ROS 2는 DDS를 사용한다. 두 graph에 `/scan`이라는 이름이 있어도 message type과 transport가 다르면 자동으로 데이터가 흐르지 않는다. `ros_gz_bridge`가 두 message를 변환해야 한다.

<figure class="course-figure" markdown="span">
  ![Gazebo Transport 센서 토픽이 parameter bridge와 image bridge를 거쳐 ROS 2 토픽으로 변환되는 흐름](../assets/beginner/bridge-dataflow.svg)
  <figcaption>그림 6. 명령은 ROS에서 Gazebo로, 관측값은 Gazebo에서 ROS로 흐른다.</figcaption>
</figure>

<pre class="course-mermaid">
flowchart LR
  G[Gazebo Transport] --> P[parameter_bridge]
  G --> I[image_bridge]
  P --> R[ROS 2 sensor topics]
  I --> C[ROS 2 image topics]
  R --> P --> G
</pre>

## 2. bridge 항목을 다섯 칸으로 읽는다

기본 설정은 `tutorial_bot_bringup/config/bridge.yaml`에 있다. 한 항목은 ROS topic, Gazebo topic, ROS type, Gazebo type, 방향을 정의한다.

```yaml
- ros_topic_name: "/scan"
  gz_topic_name: "/tutorial_bot/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

Gazebo의 `/tutorial_bot/lidar`를 ROS의 `/scan`으로 이름까지 바꾼다. 센서는 `GZ_TO_ROS`, 속도 명령은 `ROS_TO_GZ`를 사용한다.

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ
```

방향을 반대로 쓰면 양쪽 topic이 목록에는 보여도 command가 구독자에게 도달하지 않는다.

## 3. 기본 robot의 전체 mapping을 작성한다

| 데이터 | Gazebo type | ROS type | 방향 |
|---|---|---|---|
| `/clock` | `gz.msgs.Clock` | `rosgraph_msgs/msg/Clock` | GZ → ROS |
| `/cmd_vel` | `gz.msgs.Twist` | `geometry_msgs/msg/Twist` | ROS → GZ |
| `/odom` | `gz.msgs.Odometry` | `nav_msgs/msg/Odometry` | GZ → ROS |
| `/tf` | `gz.msgs.Pose_V` | `tf2_msgs/msg/TFMessage` | GZ → ROS |
| `/joint_states` | `gz.msgs.Model` | `sensor_msgs/msg/JointState` | GZ → ROS |
| `/scan` | `gz.msgs.LaserScan` | `sensor_msgs/msg/LaserScan` | GZ → ROS |
| `/imu` | `gz.msgs.IMU` | `sensor_msgs/msg/Imu` | GZ → ROS |
| RGB-D depth | `gz.msgs.Image` | `sensor_msgs/msg/Image` | GZ → ROS |
| RGB-D points | `gz.msgs.PointCloudPacked` | `sensor_msgs/msg/PointCloud2` | GZ → ROS |

RGB-D 관련 YAML은 다음처럼 작성한다.

```yaml
- ros_topic_name: "/camera/depth/image"
  gz_topic_name: "/tutorial_bot/camera/depth_image"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA

- ros_topic_name: "/camera/points"
  gz_topic_name: "/tutorial_bot/camera/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

`SENSOR_DATA` QoS는 sensor stream에 맞는 best-effort 계열 설정을 선택한다. `/clock`에는 `CLOCK`을 사용한다. subscriber가 reliable만 요구하면 best-effort sensor publisher와 호환되지 않을 수 있으므로 `ros2 topic info -v`로 QoS도 확인한다.

## 4. image는 `ros_gz_image`로 연결한다

압축되지 않은 여러 image stream은 `ros_gz_image image_bridge`로 연결한다. RGB-D의 RGB, mono, stereo pair, fisheye를 한 process에서 지정하고 ROS 이름으로 remap한다.

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

기본 robot만 실행한다면 첫 번째 topic만 지정하면 된다.

```bash
ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
  --ros-args -r /tutorial_bot/camera/image:=/camera/image
```

## 5. 실행 전 dependency를 확인한다

설치 누락과 runtime timeout을 구분하기 위해 preflight를 먼저 수행한다.

```bash
for package in ros_gz_bridge ros_gz_image ros_gz_sim xacro; do
  ros2 pkg prefix "$package" >/dev/null || {
    echo "누락: $package"
    echo "설치: sudo apt install ros-jazzy-${package//_/-}"
  }
done
```

저장소의 checker도 같은 dependency 검사를 제공한다.

```bash
./scripts/check_ros_gz_bridge.sh --preflight-only
```

## 6. 기본 bridge를 실행한다

Gazebo에 기본 `tutorial_bot`이 spawn된 상태에서 다음을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge.yaml"
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$bridge"
```

별도 터미널에서 RGB image를 연결한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
  --ros-args -r /tutorial_bot/camera/image:=/camera/image
```

topic의 존재, type, publisher 수를 확인한다.

```bash
ros2 topic list | sort
ros2 topic type /scan
ros2 topic info -v /scan
ros2 topic echo --once /odom
ros2 topic echo --once /imu
ros2 topic echo --once /camera/points
```

## 7. sensor gallery bridge를 실행한다

앞 장의 `05-sensor-gallery.xacro`를 실행했다면 gallery 전용 YAML을 사용한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gallery_bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-sensor-gallery.yaml"
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$gallery_bridge"
```

`bridge-sensor-gallery.yaml`에는 다음 3D LiDAR mapping도 들어 있다.

```yaml
- ros_topic_name: "/lidar_3d/points"
  gz_topic_name: "/tutorial_bot/lidar_3d/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

image bridge는 앞 절의 다섯 topic 명령을 함께 실행한다. bridge를 시작하기 전에 `gz topic -i -t /tutorial_bot/lidar_3d/points`로 Gazebo type이 `gz.msgs.PointCloudPacked`인지 확인한다.

## 8. TF와 wheel odom trajectory를 만든다

Gazebo DiffDrive가 동적 `odom → base_link` TF를 발행하고 `robot_state_publisher`가 URDF의 fixed sensor TF를 발행한다. gallery Xacro를 사용한 경우 다음처럼 robot description을 제공한다.

바퀴 joint는 fixed joint가 아니므로 URDF만으로 현재 회전각을 알 수 없다. 예제의 Gazebo `JointStatePublisher` System이 `/model/<이름>/joint_state`를 발행하고 bridge가 이를 ROS `/joint_states`로 바꾼다. `robot_state_publisher`는 이 값을 받아 `base_link → *_wheel_link` 동적 TF를 만든다.

```yaml
- ros_topic_name: "/joint_states"
  gz_topic_name: "/model/tutorial_bot_sensor_gallery/joint_state"
  ros_type_name: "sensor_msgs/msg/JointState"
  gz_type_name: "gz.msgs.Model"
  direction: GZ_TO_ROS
```

```bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
ros2 run robot_state_publisher robot_state_publisher --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro "$gallery")"
```

`/odom`의 pose를 RViz Path로 누적한다.

```bash
ros2 run tutorial_bot_bringup odom_to_path --ros-args \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_poses:=2000 \
  -p minimum_translation:=0.01
```

`minimum_translation`은 거의 같은 pose를 계속 저장하지 않기 위한 거리 문턱이고 `max_poses`는 memory가 무한히 증가하지 않도록 하는 상한이다.

## 9. keyboard teleop으로 왕복 경로를 검증한다

native Gazebo DiffDrive는 ROS `/cmd_vel`의 `geometry_msgs/msg/Twist`를 bridge로 받는다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

직진, 좌회전, 우회전을 차례로 입력하고 다음 값을 확인한다.

```bash
ros2 topic hz /odom
ros2 topic echo --once /wheel_odom_path
ros2 run tf2_ros tf2_echo odom lidar_link
```

`/wheel_odom_path`의 pose 수가 늘고 RViz 선이 로봇 이동을 따라가면 command → wheel motion → odom → Path 흐름이 연결된 것이다.

## 10. RViz display를 연결한다

IMU display는 별도 package를 설치한다.

```bash
sudo apt install ros-jazzy-rviz-imu-plugin
rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz"
```

Fixed Frame은 `odom`으로 지정한다.

| Display | Topic | 확인할 결과 |
|---|---|---|
| RobotModel | `/robot_description` | sensor link가 본체에 고정된다 |
| TF | `/tf`, `/tf_static` | `odom → base_link → sensor_link`가 이어진다 |
| Odometry | `/odom` | pose 화살표가 이동한다 |
| Path | `/wheel_odom_path` | wheel odom trajectory가 누적된다 |
| LaserScan | `/scan` | 2D scan이 장애물 윤곽을 만든다 |
| PointCloud2 | `/camera/points` | RGB-D point cloud가 나타난다 |
| PointCloud2 | `/lidar_3d/points` | 3D LiDAR 층이 나타난다 |
| Camera/Image | `/camera/image`, `/mono/image`, `/stereo/*/image`, `/fisheye/image` | 각 image가 갱신된다 |
| `rviz_imu_plugin/Imu` | `/imu` | orientation과 축이 갱신된다 |

## 11. 자동 통합 검증을 실행한다

기본 robot의 양방향 경로는 다음 checker로 검증한다.

```bash
./scripts/check_ros_gz_bridge.sh
```

checker는 ROS `/cmd_vel`을 보내고 `/odom`, `/scan`, `/imu`, RGB image, `/clock`을 실제 메시지에서 읽는다.

```text
ROS cmd_vel to Gazebo verified: odom x=0.40..., linear.x=0.20...
Gazebo sensors to ROS verified: scan=360, image=320x240, IMU and clock received.
```

## 자주 발생하는 문제

### ROS topic은 있지만 메시지가 없다

YAML의 방향, `gz_topic_name`, Gazebo message type을 `gz topic -i` 결과와 비교한다. 존재하지 않는 Gazebo topic을 bridge해도 ROS 이름만 보일 수 있다.

### RViz의 LaserScan 또는 PointCloud2가 오류 상태이다

QoS를 Best Effort로 바꾸고 `header.frame_id`에서 Fixed Frame까지 TF가 이어지는지 확인한다. sensor message가 있어도 TF가 없으면 3D 공간에 놓을 수 없다.

### `/clock`은 움직이는데 node timestamp가 벽시계이다

ROS node에 `use_sim_time:=true`를 전달한다. simulation이 pause되면 `/clock`과 sensor timestamp도 멈추는 것이 정상이다.

## 정리

bridge는 topic 이름뿐 아니라 양쪽 type, 방향, QoS를 명시하는 변환 경계이다. 다음 프로젝트에서는 launch, teleop, sensor, TF, wheel odom trajectory를 한 번에 실행한다.

[이전: Gazebo Fuel](09-gazebo-fuel.md) · [다음: 초급 프로젝트](11_project-tutorial-bot.md)
