# Gazebo와 ROS 2를 `ros_gz_bridge`로 연결하기

> **난이도:** 초급<br>
> **Gazebo:** Harmonic<br>
> **ROS 2:** Jazzy<br>
> **선행 학습:** Gazebo Fuel

## 학습 목표

- Gazebo Transport와 ROS 2 DDS가 서로 다른 통신 계층임을 설명한다.
- YAML에서 토픽 이름, 메시지 타입, 방향, QoS를 지정한다.
- 명령은 ROS → Gazebo로, 센서·odom·TF·clock은 Gazebo → ROS로 연결한다.
- 영상 전용 브리지와 일반 파라미터 브리지의 역할을 구분한다.
- ROS 토픽을 RViz의 Image, Camera, LaserScan, PointCloud2, IMU, Odometry, Path 디스플레이에 연결한다.

## 실습 준비와 선택할 구성

[센서 장](08-sensors.md)의 월드와 로봇 생성까지 마친 뒤 진행한다. 기본 4단계 로봇이면 6절의 `bridge.yaml`, 센서 모음 5단계 로봇이면 7절의 `bridge-sensor-gallery.yaml`을 선택한다. 두 YAML을 동시에 실행하면 `/odom`, `/tf`, `/scan`이 중복될 수 있다. 통합 `simulation.launch.py`는 브리지를 자동 실행하므로 이 수동 실습과 함께 켜지 않는다.

새 터미널마다 다음 세 줄을 실행한다. 이어지는 브리지, 상태 발행자, 경로 누적기, 조종기, RViz는 각각 별도의 터미널에서 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

## 1. 같은 토픽 이름만으로 연결되지는 않는다

Gazebo는 Gazebo Transport를 사용하고 ROS 2는 DDS를 사용한다. 두 통신 그래프에 `/scan`이라는 이름이 있어도 메시지 타입과 통신 체계가 다르면 자동으로 데이터가 흐르지 않는다. `ros_gz_bridge`가 두 메시지를 변환해야 한다.

<figure class="course-figure" markdown="span">
  ![Gazebo Transport 센서 토픽이 파라미터 브리지와 영상 브리지를 거쳐 ROS 2 토픽으로 변환되는 흐름](../assets/beginner/bridge-dataflow.svg)
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

## 2. 브리지 항목을 다섯 칸으로 읽는다

기본 설정은 `tutorial_bot_bringup/config/bridge.yaml`에 있다. 한 항목은 ROS 토픽, Gazebo 토픽, ROS 타입, Gazebo 타입, 방향을 정의한다.

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

방향을 반대로 쓰면 양쪽 토픽이 목록에는 보여도 명령이 구독자에게 도달하지 않는다.

## 3. 기본 로봇의 전체 연결 관계를 작성한다

| 데이터 | Gazebo 타입 | ROS 타입 | 방향 |
|---|---|---|---|
| `/clock` | `gz.msgs.Clock` | `rosgraph_msgs/msg/Clock` | GZ → ROS |
| `/cmd_vel` | `gz.msgs.Twist` | `geometry_msgs/msg/Twist` | ROS → GZ |
| `/odom` | `gz.msgs.Odometry` | `nav_msgs/msg/Odometry` | GZ → ROS |
| `/tf` | `gz.msgs.Pose_V` | `tf2_msgs/msg/TFMessage` | GZ → ROS |
| `/joint_states` | `gz.msgs.Model` | `sensor_msgs/msg/JointState` | GZ → ROS |
| `/scan` | `gz.msgs.LaserScan` | `sensor_msgs/msg/LaserScan` | GZ → ROS |
| `/imu` | `gz.msgs.IMU` | `sensor_msgs/msg/Imu` | GZ → ROS |
| RGB-D 깊이 | `gz.msgs.Image` | `sensor_msgs/msg/Image` | GZ → ROS |
| RGB-D 점군 | `gz.msgs.PointCloudPacked` | `sensor_msgs/msg/PointCloud2` | GZ → ROS |

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
  frame_id: camera_link
```

점군 항목의 `frame_id`는 Harmonic RGB-D 점군의 실제 축 방향에 맞춰 헤더를 보정한다. 영상과 CameraInfo에는 `camera_optical_frame`, 점군에는 `camera_link`를 사용한다. [브리지 YAML 설정 구현](https://github.com/gazebosim/ros_gz/blob/0fa70cb7c15f7500c495190020dd6292188c8e54/ros_gz_bridge/src/bridge_config.cpp)에서 항목별 `frame_id`를 확인할 수 있다. 전체 좌표 관계는 [센서 장](08-sensors.md)의 RGB-D 설명을 참고한다.

`SENSOR_DATA` QoS는 센서 스트림에 맞는 best-effort 계열 설정을 선택한다. `/clock`에는 `CLOCK`을 사용한다. 구독자가 reliable만 요구하면 best-effort 센서 발행자와 호환되지 않을 수 있으므로 `ros2 topic info -v`로 QoS도 확인한다.

## 4. 영상은 `ros_gz_image`로 연결한다

여러 영상 스트림은 `ros_gz_image image_bridge`로 연결한다. RGB-D 컬러 영상, 단안, 좌우 스테레오, 어안 영상를 한 프로세스에서 지정하고 ROS에서 쓸 토픽 이름으로 바꾼다.

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

기본 로봇만 실행한다면 첫 번째 토픽만 지정하면 된다.

```bash
ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
  --ros-args -r /tutorial_bot/camera/image:=/camera/image
```

## 5. 실행 전 의존성을 확인한다

브리지 패키지는 1.0.22 이상이어야 한다. 구버전에서는 YAML의 QoS 또는 프레임 보정이 적용되지 않아 토픽이 보이더라도 RViz 결과가 다를 수 있다. [설치 안내](../02_getting-started/02_installation-jazzy.md)의 버전 확인과 갱신을 먼저 수행한다.

설치가 빠진 것인지 실행 중 응답이 늦는 것인지 구분하기 위해 의존성부터 확인한다.

```bash
for package in ros_gz_bridge ros_gz_image ros_gz_sim xacro; do
  ros2 pkg prefix "$package" >/dev/null || {
    echo "누락: $package"
    echo "설치: sudo apt install ros-jazzy-${package//_/-}"
  }
done
```

저장소의 검사 스크립트도 같은 의존성 검사를 제공한다.

```bash
./scripts/check_ros_gz_bridge.sh --preflight-only
```

## 6. 기본 브리지를 실행한다

Gazebo에 `04-sensors-final.xacro`로 만든 기본 `tutorial_bot`이 생성되어 있어야 한다. 3단계 로봇에는 센서가 없으므로 `/scan`이나 영상이 나오지 않는다. 센서 모음 로봇을 생성했다면 이 절을 건너뛰고 7절로 이동한다. 기본 구성을 새로 시작하려면 먼저 이전 Gazebo를 종료한 뒤 터미널 1과 2에서 다음을 실행한다.

터미널 1에서는 센서 시험 월드를 연다.

```bash
gz sim -r "$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf"
```

터미널 2에서는 기본 센서 로봇을 생성한다.

```bash
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/04-sensors-final.xacro"
xacro "$stage" > /tmp/tutorial_bot-stage-04.urdf
ros2 run ros_gz_sim create -world sensor_test \
  -name tutorial_bot -file /tmp/tutorial_bot-stage-04.urdf -z 0.12
```

터미널 3에서는 브리지를 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge.yaml"
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$bridge"
```

별도 터미널에서 RGB 영상을 연결한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
  --ros-args -r /tutorial_bot/camera/image:=/camera/image
```

토픽의 존재, 타입, 발행자 수를 확인한다.

```bash
ros2 topic list | sort
ros2 topic type /scan
ros2 topic info -v /scan
ros2 topic echo --once /odom
ros2 topic echo /imu --qos-reliability best_effort --once
ros2 topic echo /camera/points --field header --qos-reliability best_effort --once
```

## 7. 센서 모음 브리지를 실행한다

[센서 장](08-sensors.md)의 `tutorial_bot_sensor_gallery`를 사용한다면 이 YAML을 실행한다. 이미 같은 브리지를 실행했다면 새로 켜지 않는다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gallery_bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-sensor-gallery.yaml"
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$gallery_bridge"
```

`bridge-sensor-gallery.yaml`에는 다음 3D LiDAR 연결 관계도 들어 있다.

```yaml
- ros_topic_name: "/lidar_3d/points"
  gz_topic_name: "/tutorial_bot/lidar_3d/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

영상 브리지는 앞 절의 다섯 토픽 명령을 함께 실행한다. 브리지를 시작하기 전에 `gz topic -i -t /tutorial_bot/lidar_3d/points`로 Gazebo 타입이 `gz.msgs.PointCloudPacked`인지 확인한다.

## 8. TF와 바퀴 주행 궤적을 만든다

Gazebo DiffDrive가 동적 `odom → base_link` TF를 내보내고 브리지가 ROS로 전달한다. `robot_state_publisher`는 URDF에 정의된 센서의 고정 TF를 발행한다. 앞 장에서 이미 실행했다면 그대로 두고, 새로 시작한다면 다음 예제를 사용한다.

바퀴 조인트는 고정 조인트가 아니므로 URDF만으로 현재 회전각을 알 수 없다. 예제의 Gazebo `JointStatePublisher` 시스템이 `/model/<이름>/joint_state`를 발행하고 브리지가 이를 ROS `/joint_states`로 바꾼다. `robot_state_publisher`는 이 값을 받아 `base_link → *_wheel_link` 동적 TF를 만든다.

```yaml
- ros_topic_name: "/joint_states"
  gz_topic_name: "/model/tutorial_bot_sensor_gallery/joint_state"
  ros_type_name: "sensor_msgs/msg/JointState"
  gz_type_name: "gz.msgs.Model"
  direction: GZ_TO_ROS
```

```bash
gallery="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/05-sensor-gallery.xacro"
xacro "$gallery" > /tmp/tutorial_bot_sensor_gallery.urdf
ros2 run robot_state_publisher robot_state_publisher \
  /tmp/tutorial_bot_sensor_gallery.urdf --ros-args -p use_sim_time:=true
```

기본 로봇을 사용했다면 위 파일 대신 `04-sensors-final.xacro`를 변환한다. 항상 Gazebo에 생성한 모델과 동일한 URDF를 사용해야 한다.

새 터미널에서 `/odom`의 위치를 RViz Path로 누적한다.

```bash
ros2 run tutorial_bot_bringup odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_poses:=2000 \
  -p minimum_translation:=0.01
```

`minimum_translation`은 거의 같은 위치와 자세를 계속 저장하지 않기 위한 최소 이동 거리이고 `max_poses`는 메모리가 무한히 증가하지 않도록 하는 상한이다.

## 9. 키보드 조종으로 왕복 경로를 검증한다

Gazebo 자체 DiffDrive는 ROS `/cmd_vel`의 `geometry_msgs/msg/Twist`를 브리지로 받는다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p speed:=0.2 -p turn:=0.6 \
  -p repeat_rate:=10.0 -p key_timeout:=0.6 \
  -r cmd_vel:=/cmd_vel
```

영문 입력 상태에서 `i`로 직진, `j`로 좌회전, `l`로 우회전, `k`로 정지한다. 확인용 터미널에서 다음 값을 확인한다. `hz`와 `tf2_echo`는 계속 실행되므로 각각 `Ctrl+C`로 끝낸 뒤 다음 명령을 실행한다.

```bash
ros2 topic hz /odom
ros2 topic echo --once /wheel_odom_path
ros2 run tf2_ros tf2_echo odom lidar_link
```

`/wheel_odom_path`의 위치 표본 수가 늘고 RViz 선이 로봇 이동을 따라가면 명령 → 바퀴 회전 → 오도메트리 → Path 흐름이 연결된 것이다.

## 10. RViz 디스플레이를 연결한다

IMU 디스플레이는 별도 패키지를 설치한다.

```bash
sudo apt install ros-jazzy-rviz-imu-plugin
rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz" \
  --ros-args -p use_sim_time:=true
```

Fixed Frame은 `odom`으로 지정한다. LaserScan과 PointCloud2의 Topic 아래 Reliability Policy를 `Best Effort`로 맞춘다. Camera 디스플레이는 영상뿐 아니라 `/camera/camera_info`와 영상 프레임의 TF도 필요하다. 화면에 영상만 띄우는 Image 디스플레이부터 확인하면 원인을 좁히기 쉽다.

| Display | 토픽 | 확인할 결과 |
|---|---|---|
| RobotModel | `/robot_description` | 센서 링크가 본체에 고정된다 |
| TF | `/tf`, `/tf_static` | `odom → base_link → sensor_link`가 이어진다 |
| Odometry | `/odom` | 위치와 자세 화살표가 이동한다 |
| Path | `/wheel_odom_path` | 바퀴 주행 궤적이 누적된다 |
| LaserScan | `/scan` | 2D 스캔이 장애물 윤곽을 만든다 |
| PointCloud2 | `/camera/points` | RGB-D 점군이 나타난다 |
| PointCloud2 | `/lidar_3d/points` | 3D LiDAR 층이 나타난다 |
| Camera/Image | `/camera/image`, `/mono/image`, `/stereo/*/image`, `/fisheye/image` | 각 영상이 갱신된다 |
| `rviz_imu_plugin/Imu` | `/imu` | 자세와 축이 갱신된다 |

## 11. 자동 통합 검증을 실행한다

기본 로봇의 양방향 경로는 다음 검사 스크립트로 검증한다.

```bash
./scripts/check_ros_gz_bridge.sh
```

검사 스크립트는 ROS `/cmd_vel`을 보내고 `/odom`, `/scan`, `/imu`, RGB 영상, `/clock`을 실제 메시지에서 읽는다.

```text
ROS cmd_vel to Gazebo verified: odom x=0.40..., linear.x=0.20...
Gazebo sensors to ROS verified: scan=360, image=320x240, IMU and clock received.
```

## 자주 발생하는 문제

### ROS 토픽은 있지만 메시지가 없다

YAML의 방향, `gz_topic_name`, Gazebo 메시지 타입을 `gz topic -i` 결과와 비교한다. 존재하지 않는 Gazebo 토픽을 브리지해도 ROS 이름만 보일 수 있다.

### RViz의 LaserScan 또는 PointCloud2가 오류 상태이다

디스플레이의 QoS를 Best Effort로 바꾸고 `header.frame_id`에서 Fixed Frame까지 TF가 이어지는지 확인한다. 센서 메시지가 있어도 TF가 없으면 3D 공간에 놓을 수 없다.

### `/clock`은 움직이는데 노드 타임스탬프가 벽시계이다

ROS 노드에 `use_sim_time:=true`를 전달한다. 시뮬레이션이 pause되면 `/clock`과 센서 타임스탬프도 멈추는 것이 정상이다.

## 정리

브리지는 토픽 이름뿐 아니라 양쪽 타입, 방향, QoS를 명시하는 변환 경계이다. 다음 프로젝트에서는 실행 구성, teleop, 센서, TF, 바퀴 주행 궤적을 한 번에 실행한다.

[이전: Gazebo Fuel](09-gazebo-fuel.md) · [다음: 초급 프로젝트](11_project-tutorial-bot.md)
