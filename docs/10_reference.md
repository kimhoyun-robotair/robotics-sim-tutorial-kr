# 빠른 참고표

이 장은 실습 중 명령, 토픽, frame 이름을 빠르게 찾기 위한 요약이다. 처음 학습할 때는 앞 장의 설명과 완료 기준을 먼저 읽는다.

## 기준 환경

| 항목 | 값 |
| --- | --- |
| Ubuntu | 22.04 LTS (Jammy) |
| ROS | ROS 2 Humble |
| Gazebo | Gazebo Classic 11 |
| 저장소 브랜치 | `Humble` |
| workspace | `robotics-sim-tutorial-kr/ros2_ws` |

## 매 터미널에서 실행

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
```

환경이 섞였는지 확인한다.

```bash
echo "ROS_DISTRO=$ROS_DISTRO"
gazebo --version
git -C ~/robotics-sim-tutorial-kr branch --show-current
```

예상값은 각각 `humble`, `Gazebo ... version 11.x`, `Humble`이다.

## 설치와 빌드

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake git ripgrep \
  liburdfdom-tools python3-venv \
  ros-humble-desktop \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-xacro \
  ros-humble-teleop-twist-keyboard \
  ros-humble-rviz-imu-plugin \
  python3-colcon-common-extensions \
  python3-rosdep

cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
```

C++ plugin만 다시 빌드할 때는 다음 명령을 사용한다.

```bash
colcon build \
  --symlink-install \
  --packages-select gazebo_tutorial_plugins
source install/setup.bash
```

## 실행 명령

| 대상 | 명령 |
| --- | --- |
| 2륜 + caster | `ros2 launch gazebo_tutorial_bringup diffbot.launch.py` |
| 4륜 skid/diff | `ros2 launch gazebo_tutorial_bringup rover_diff.launch.py` |
| 4륜 Ackermann | `ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py` |
| 센서 전체 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all` |
| 카메라 묶음 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=cameras` |
| LiDAR 묶음 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars` |
| IMU + 구동만 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=minimal` |
| headless | 위 명령 뒤에 `gui:=false rviz:=false` 추가 |
| pause 시작 | 위 명령 뒤에 `pause:=true` 추가 |

두 로봇 launch를 기본 설정으로 동시에 실행하면 `/cmd_vel`, `/odom`, TF frame과 node 이름이 충돌한다. 한 실습을 `Ctrl-C`로 완전히 종료한 뒤 다음 실습을 시작한다.

## 공통 launch 인자

정확한 목록과 현재 기본값은 `--show-args`가 최종 기준이다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py --show-args
```

| 인자 | 기본값 | 의미 |
| --- | --- | --- |
| `world` | 패키지의 world | 다른 SDF world 선택 |
| `description_package` | `gazebo_tutorial_description` | Xacro를 제공하는 package |
| `xacro_file` | 모델별 파일 | description package의 `urdf/` 아래 파일 |
| `gui` | `true` | `gzclient` 실행 여부 |
| `pause` | `false` | physics 정지 상태로 시작 |
| `verbose` | `false` | Gazebo 상세 로그 |
| `rviz` | `true` | RViz 자동 실행 |
| `rviz_config` | 모델별 `.rviz` | 불러올 RViz 설정 |
| `use_sim_time` | `true` | ROS node가 `/clock` 사용 |
| `entity_name` | 모델별 이름 | Gazebo entity 이름 |
| `x`, `y`, `z`, `yaw` | `0, 0, 0.10, 0` | spawn pose |
| `odom_topic` | `/odom` | Path 변환 입력 |
| `path_topic` | `/wheel_odom_path` | Path 출력 |
| `path_frame` | 빈 문자열 | 비어 있으면 Odometry frame 사용; 변환 기능은 아님 |
| `max_points` | `2000` | 저장할 최대 pose 수 |
| `sensor_profile` | 모델별 기본 | sensor launch: `all`, `cameras`, `lidars`, `minimal` |
| `ground_truth_odom_topic` | `/ground_truth/odom` | Ackermann built-in world-pose 입력 |
| `ground_truth_path_topic` | `/ground_truth_path` | Ackermann 비교용 Path 출력 |
| `publish_world_odom_tf` | `true` | spawn pose를 반영한 `world → odom` static TF |
| `ackermann_publish_tf` | `true` | Ackermann wheel-odom 노드의 `odom → base_footprint` TF |

## 키보드 teleop

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

| 키 | 동작 |
| --- | --- |
| `i` / `,` | 전진 / 후진 |
| `j` / `l` | 좌 / 우 회전 |
| `u` / `o` | 전진 좌 / 우 곡선 |
| `m` / `.` | 후진 좌 / 우 곡선 |
| `k` 또는 space | 정지 |
| `q` / `z` | 전체 속도 배율 증가 / 감소 |
| `w` / `x` | 선속도 배율 증가 / 감소 |
| `e` / `c` | 각속도 배율 증가 / 감소 |

Ackermann은 제자리 회전할 수 없다. 선속도가 있는 곡선 키를 사용한다. Humble의 내장 Ackermann plugin은 `Twist.angular.z`를 중앙 타이어 조향 목표각처럼 사용한다는 점도 [4륜 rover 장](04_rover.md)에서 확인한다.

## 공통 토픽

| 토픽 | 타입 | 발행/구독 주체 | 설명 |
| --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/Clock` | Gazebo | simulation time |
| `/cmd_vel` | `geometry_msgs/Twist` | teleop → drive plugin | 주행 명령 |
| `/joint_states` | `sensor_msgs/JointState` | Gazebo joint-state plugin | 실제 joint 위치/속도 |
| `/odom` | `nav_msgs/Odometry` | drive 또는 wheel odom node | 로봇 odometry |
| `/wheel_odom_path` | `nav_msgs/Path` | `odom_to_path` | RViz 누적 궤적 |
| `/robot_description` | `std_msgs/String` | `robot_state_publisher` | 전개된 URDF |
| `/tf` | `tf2_msgs/TFMessage` | drive/RSP | 동적 transform |
| `/tf_static` | `tf2_msgs/TFMessage` | RSP/static publisher | 고정 transform |
| `/ground_truth_path` | `nav_msgs/Path` | custom plugin 또는 odom-to-path 노드 | diffbot/Ackermann의 Gazebo world pose |

### 모델별 odometry 차이

| 모델 | `/odom`의 계산 근거 | 비교용 값 |
| --- | --- | --- |
| `diffbot` | 좌·우 wheel encoder 적분 | `/ground_truth_path` |
| `rover_diff` | Humble diff plugin의 첫 wheel pair 적분 | Gazebo 화면/world pose |
| `rover_ackermann` | rear wheel 회전 + front steering joint 적분 node | `/ground_truth/odom` → `/ground_truth_path` |
| `sensor_bot` | 좌·우 wheel encoder 적분 | Gazebo 화면/world pose |

## TF tree

기본 연결은 다음과 같다.

```text
world → odom → base_footprint → base_link → wheel/sensor frames
```

| edge | 소유자 | 성격 |
| --- | --- | --- |
| `world → odom` | bringup static publisher | spawn 원점과 encoder odom 원점 연결 |
| `odom → base_footprint` | drive plugin 또는 Ackermann wheel odom node | 주행에 따라 변함 |
| `base_footprint → base_link` | URDF + RSP | fixed |
| `base_link → sensor_*` | URDF + RSP | fixed |
| `base_link → wheel/steering` | URDF + `/joint_states` + RSP | joint에 따라 변함 |

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_link lidar_2d_link
ros2 run tf2_tools view_frames
```

## 센서 토픽과 RViz Display

| 센서 | 토픽 | 타입 | RViz Display |
| --- | --- | --- | --- |
| wheel odom | `/odom` | `nav_msgs/Odometry` | Odometry |
| wheel 궤적 | `/wheel_odom_path` | `nav_msgs/Path` | Path |
| IMU | `/imu/data` | `sensor_msgs/Imu` | `rviz_imu_plugin/Imu` |
| mono | `/camera/image_raw` | `sensor_msgs/Image` | Image |
| stereo left/right | `/stereo/{left,right}/image_raw` | `sensor_msgs/Image` | Image 2개 |
| RGB | `/rgbd/image_raw` | `sensor_msgs/Image` | Image |
| depth | `/rgbd/depth/image_raw` | `sensor_msgs/Image` | Image |
| RGBD cloud | `/rgbd/points` | `sensor_msgs/PointCloud2` | PointCloud2 |
| fisheye | `/fisheye/image_raw` | `sensor_msgs/Image` | Image |
| 2D LiDAR | `/scan` | `sensor_msgs/LaserScan` | LaserScan |
| 3D LiDAR | `/points` | `sensor_msgs/PointCloud2` | PointCloud2 |

CameraInfo는 이미지와 같은 namespace의 `/camera_info`에 있다. RGBD depth 정보는 `/rgbd/depth/camera_info`에 있다. fisheye 영상은 Gazebo의 `equidistant` 렌즈로 렌더링되지만 Humble camera plugin의 CameraInfo는 `plumb_bob`/pinhole 형식이므로 정밀 보정값으로 사용하지 않는다. stereo 출력은 동기화된 left/right raw 영상과 물리 baseline을 제공하지만, 정확한 disparity 계산에는 별도 calibration·rectification 단계가 필요하다.

```bash
ros2 topic hz /imu/data
ros2 topic hz /camera/image_raw
ros2 topic hz /scan
ros2 topic bw /points
ros2 topic echo /scan --once --qos-reliability best_effort
```

## Gazebo Classic plugin 파일

| 기능 | library |
| --- | --- |
| differential drive | `libgazebo_ros_diff_drive.so` |
| Ackermann drive | `libgazebo_ros_ackermann_drive.so` |
| joint states | `libgazebo_ros_joint_state_publisher.so` |
| IMU | `libgazebo_ros_imu_sensor.so` |
| mono/stereo/RGBD/fisheye | `libgazebo_ros_camera.so` |
| 2D/3D ray sensor | `libgazebo_ros_ray_sensor.so` |
| 이 과정의 custom path | `libground_truth_path_plugin.so` |

### 센서 Xacro include와 재사용 형식

센서 구현은 `urdf/sensors/` 아래에서 종류별 macro로 분리하고, 최상위 로봇 Xacro는 필요한
파일을 include한 뒤 장착 위치와 출력 설정만 전달한다. 다음 코드는 실제
`sensor_bot.urdf.xacro`와 같은 조합 형식을 축약한 예이다.

```xml
<robot name="my_sensor_robot"
       xmlns:xacro="http://www.ros.org/wiki/xacro">
  <!-- 각 센서 macro가 사용하는 장착 link와 optical frame helper를 먼저 읽는다. -->
  <xacro:include filename="$(find gazebo_tutorial_description)/urdf/sensors/sensor_common.xacro"/>
  <xacro:include filename="$(find gazebo_tutorial_description)/urdf/sensors/imu_sensor.xacro"/>
  <xacro:include filename="$(find gazebo_tutorial_description)/urdf/sensors/mono_rgb_camera.xacro"/>
  <xacro:include filename="$(find gazebo_tutorial_description)/urdf/sensors/lidar_2d.xacro"/>

  <!-- base_link는 이 파일 앞부분에서 이미 정의했다고 가정한다. -->
  <xacro:gazebo_imu_sensor
    prefix="imu" parent="base_link" xyz="0 0 0.10"
    topic="imu/data" update_rate="100.0"
    angular_stddev="0.0002" linear_stddev="0.017"/>

  <xacro:gazebo_mono_rgb_camera
    prefix="front_camera" parent="base_link" xyz="0.30 0 0.08"
    camera_name="front" format="R8G8B8"
    width="640" height="480" update_rate="15.0"/>

  <xacro:gazebo_lidar_2d
    prefix="lidar" parent="base_link" xyz="0.10 0 0.22"
    topic="scan" samples="720" min_range="0.12" max_range="15.0"/>
</robot>
```

같은 macro를 다시 호출할 때는 `prefix`를 반드시 다르게 정한다. `prefix`에서 sensor link,
joint, Gazebo sensor/plugin 이름이 파생되므로 중복되면 Xacro는 전개되어도 URDF 이름과
Gazebo entity가 충돌한다.

| macro | 위치·이름 parameter | 핵심 동작 parameter |
| --- | --- | --- |
| `gazebo_imu_sensor` | `prefix`, `parent`, `xyz`, `rpy`, `topic` | `update_rate`, `angular_stddev`, `linear_stddev` |
| `gazebo_mono_rgb_camera` | `prefix`, `parent`, `xyz`, `camera_name` | `format`, `width`, `height`, `horizontal_fov`, `near`, `far`, `image_noise_stddev` |
| `gazebo_stereo_camera` | `prefix`, `parent`, `xyz`, `camera_name` | `baseline`, `width`, `height`, `update_rate`, `image_noise_stddev` |
| `gazebo_rgbd_camera` | `prefix`, `parent`, `xyz`, `camera_name` | `min_depth`, `max_depth`, `width`, `height`, `image_noise_stddev`(색상 채널 잡음) |
| `gazebo_fisheye_camera` | `prefix`, `parent`, `xyz`, `camera_name` | `horizontal_fov`, `lens_type`, `cutoff_angle`, `env_texture_size` |
| `gazebo_lidar_2d` | `prefix`, `parent`, `xyz`, `topic` | `samples`, 각도·거리 범위, `range_resolution`, `noise_stddev` |
| `gazebo_lidar_3d` | `prefix`, `parent`, `xyz`, `topic` | 수평·수직 sample/각도, 거리 범위, `update_rate` |

macro의 기본값과 전체 parameter는 `ros2_ws/src/gazebo_tutorial_description/urdf/sensors/`
아래 해당 파일의 `params="..."` 선언을 최종 기준으로 확인한다.

플러그인 탐색 상태는 다음 명령으로 확인한다.

```bash
echo "$GAZEBO_PLUGIN_PATH" | tr ':' '\n'
find $(ros2 pkg prefix gazebo_plugins) -name 'libgazebo_ros_*.so' | sort
find $(ros2 pkg prefix gazebo_tutorial_plugins) \
  -name 'libground_truth_path_plugin.so'
```

## 모델·world 정적 검사

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws

for model in diffbot rover_diff rover_ackermann sensor_bot; do
  xacro src/gazebo_tutorial_description/urdf/${model}.urdf.xacro \
    > /tmp/${model}.urdf
  check_urdf /tmp/${model}.urdf
done

gz sdf -k src/gazebo_tutorial_bringup/worlds/empty.world
gz sdf -k src/gazebo_tutorial_bringup/worlds/sensor.world
```

센서 profile도 각각 전개한다.

```bash
for profile in all cameras lidars minimal; do
  xacro \
    src/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro \
    sensor_profile:=${profile} \
    > /tmp/sensor_bot_${profile}.urdf
  check_urdf /tmp/sensor_bot_${profile}.urdf
done
```

## ROS graph 진단

```bash
ros2 node list
ros2 topic list -t
ros2 topic info /odom --verbose
ros2 topic info /points --verbose
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /odom_to_path use_sim_time
```

한 메시지만 기다릴 때 무한정 멈추지 않도록 `timeout`을 함께 사용할 수 있다.

```bash
timeout 5s ros2 topic echo /odom --once
timeout 5s ros2 topic echo /scan --once \
  --qos-reliability best_effort
```

## 종료와 재실행

launch를 실행한 터미널에서 `Ctrl-C`를 한 번 누르고 종료 로그를 기다린다. 그래도 이전 프로세스가 의심되면 먼저 읽기 전용으로 확인한다.

```bash
pgrep -af 'gzserver|gzclient|robot_state_publisher|rviz2'
ros2 node list
```

Gazebo GUI의 **Reset Model Poses**는 pose만 되돌리고, **Reset World** 또는 simulation reset은 시간과 상태를 더 넓게 되돌린다. 시간 stamp가 뒤로 가면 이 저장소의 Path node/plugin은 이전 궤적을 비운다.

빌드 산출물을 완전히 새로 만들 필요가 있을 때만 workspace의 정확한 경로를 확인한 후 `build/`, `install/`, `log/`를 지우고 다시 빌드한다. 일상적인 URDF/launch 변경은 `--symlink-install` 덕분에 전체 삭제가 필요하지 않다.
