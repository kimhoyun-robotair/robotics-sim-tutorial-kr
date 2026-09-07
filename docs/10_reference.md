# 빠른 참고표

실습 중 필요한 명령·토픽·프레임을 찾기 위한 요약이다. 처음 시작한다면 [설치 안내](01_setup.md), 센서 화면이 이상하다면 [센서 실습](05_sensors.md)과 [문제 해결](08_debugging.md)을 먼저 확인한다.

## 기준 환경과 터미널 설정

| 항목 | 값 |
| --- | --- |
| Ubuntu | 22.04 LTS |
| ROS | ROS 2 Humble |
| Gazebo | Gazebo Classic 11 |
| 브랜치 | `Humble` |
| 작업 공간 | `~/robotics-sim-tutorial-kr/ros2_ws` |

새 터미널마다 실행한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
```

환경이 맞는지 확인한다.

```bash
echo "ROS_DISTRO=$ROS_DISTRO"
gazebo --version
git -C ~/robotics-sim-tutorial-kr branch --show-current
```

예상값은 각각 `humble`, Gazebo 버전 `11.x`, `Humble`이다.

## 빌드

ROS와 Gazebo 설치는 [1장](01_setup.md)의 순서대로 진행한다. 설치와 `rosdep` 초기화를 마쳤다면 다음 명령으로 의존성을 설치하고 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
```

직접 만든 C++ 플러그인만 다시 빌드할 때는 다음 명령을 쓴다. 빌드한 라이브러리를 반영하려면 Gazebo도 종료한 뒤 다시 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
colcon build --symlink-install --packages-select gazebo_tutorial_plugins
source install/setup.bash
```

## 실행 명령

다음 중 **하나만** 실행한다. 기본 설정은 토픽·TF를 공유하므로 동시에 여러 로봇을 실행하면 충돌한다.

| 대상 | 명령 |
| --- | --- |
| 2륜 차동 구동 | `ros2 launch gazebo_tutorial_bringup diffbot.launch.py` |
| 4륜 스키드·차동 구동 | `ros2 launch gazebo_tutorial_bringup rover_diff.launch.py` |
| 4륜 Ackermann | `ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py` |
| 센서 전체 | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all` |
| 카메라와 IMU | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=cameras` |
| 라이다와 IMU | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=lidars` |
| 구동계와 IMU | `ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=minimal` |

`Successfully spawned entity` 로그가 나온 뒤 다른 터미널에서 조회·조종 명령을 실행한다. 다음 실습으로 바꾸려면 기존 실행을 `Ctrl+C`로 끝내고 종료 로그를 기다린다.

## 공통 실행 인자

현재 기본값과 전체 목록은 다음 명령이 기준이다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py --show-args
```

| 인자 | 기본값 | 의미 |
| --- | --- | --- |
| `world` | 모델별 월드 | 사용할 `.world` 파일의 절대 경로 |
| `description_package` | `gazebo_tutorial_description` | Xacro를 제공하는 패키지 |
| `xacro_file` | 모델별 파일 | 패키지 `urdf/` 아래의 Xacro 파일명 |
| `gui` | `true` | Gazebo 화면인 `gzclient` 실행 여부 |
| `rviz` | `true` | RViz 자동 실행 |
| `rviz_config` | 모델별 `.rviz` | 불러올 RViz 설정 |
| `pause` | `false` | 물리 계산을 일시 정지한 상태로 시작 |
| `verbose` | `false` | Gazebo 상세 로그 출력 |
| `use_sim_time` | `true` | ROS 노드가 `/clock` 사용 |
| `entity_name` | 모델별 이름 | Gazebo 모델 이름 |
| `x`, `y`, `z`, `yaw` | `0, 0, 0.10, 0` | 생성 위치(m)와 방향(rad) |
| `odom_topic` / `path_topic` | `/odom` / `/wheel_odom_path` | 궤적 변환의 입력·출력 |
| `path_frame` | 빈 문자열 | 입력 프레임을 그대로 사용. TF 변환 기능은 없음 |
| `max_points` | `2000` | 누적 궤적의 최대 점 수 |
| `sensor_profile` | 센서 실행은 `all` | `all`, `cameras`, `lidars`, `minimal` |
| `ground_truth_odom_topic` | `/ground_truth/odom` | Ackermann의 기준 위치 입력 |
| `ground_truth_path_topic` | `/ground_truth_path` | Ackermann의 비교용 궤적 출력 |
| `publish_world_odom_tf` | `true` | 생성 위치를 반영한 `world → odom` 고정 TF |
| `ackermann_publish_tf` | `true` | Ackermann 오도메트리 TF 발행 |

GUI 없이 실행하려면 명령 뒤에 `gui:=false rviz:=false`를 추가한다. 카메라는 GUI를 꺼도 렌더링 환경이 필요하다.

## 키보드 조종

별도 터미널에서 환경을 읽고 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

| 키 | 동작 |
| --- | --- |
| `i` / `,` | 전진 / 후진 |
| `j` / `l` | 좌 / 우 제자리 회전. 차동 구동 차량에서 사용 |
| `u` / `o` | 전진하며 좌 / 우 회전 |
| `m` / `.` | 후진하며 좌 / 우 회전 |
| `k` 또는 스페이스 | 정지 |
| `q` / `z` | 선속도·회전 명령 크기 함께 증가 / 감소 |
| `w` / `x` | 선속도 증가 / 감소 |
| `e` / `c` | 회전 명령 크기 증가 / 감소 |

Ackermann은 제자리 회전할 수 없다. Humble의 내장 플러그인은 `Twist.angular.z`를 중앙 바퀴의 조향 목표각(rad)으로 사용하므로, 일반적인 차동 구동의 각속도 명령(rad/s)과 구분한다. 종료할 때는 `k`로 멈춘 뒤 `Ctrl+C`를 누른다.

## 공통 토픽과 오도메트리

| 토픽 | 메시지 타입 | 역할 |
| --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 시뮬레이션 시간 |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 주행 명령 |
| `/joint_states` | `sensor_msgs/msg/JointState` | 실제 관절 위치·속도 |
| `/odom` | `nav_msgs/msg/Odometry` | 바퀴로 계산한 로봇 위치·속도 |
| `/wheel_odom_path` | `nav_msgs/msg/Path` | 오도메트리 누적 궤적 |
| `/robot_description` | `std_msgs/msg/String` | 전개한 URDF |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | 동적·고정 좌표 변환 |
| `/ground_truth_path` | `nav_msgs/msg/Path` | diffbot·Ackermann의 월드 기준 궤적 |

| 모델 | `/odom`의 계산 근거 |
| --- | --- |
| `diffbot`, `sensor_bot` | 좌우 바퀴 회전량 적분 |
| `rover_diff` | Humble 차동 구동 플러그인의 첫 번째 좌우 바퀴 쌍 적분 |
| `rover_ackermann` | 뒷바퀴 회전량·앞바퀴 조향각 적분 후 뒤 차축에서 차체 중심으로 좌표 변환 |

Ackermann 내장 플러그인의 출력은 `/ground_truth/odom`으로 분리한다. 이것은 바퀴 엔코더가 아닌 Gazebo의 위치를 사용한다. 별도 노드의 `rear_axle_offset=0.28`은 뒤 차축과 `base_footprint` 사이의 거리를 반영한다.

## TF와 RViz

| 연결 | 발행자 |
| --- | --- |
| `world → odom` | 실행 파일의 고정 TF 노드 |
| `odom → base_footprint` | 구동 플러그인 또는 Ackermann 오도메트리 노드 |
| `base_footprint → base_link` | URDF를 읽는 `robot_state_publisher` |
| 차체 → 센서 | 고정 관절을 읽는 `robot_state_publisher` |
| 차체 → 바퀴·조향부 | `/joint_states`를 읽는 `robot_state_publisher` |

주행용 `odom.rviz`의 Fixed Frame은 `odom`, 센서용 `sensors.rviz`는 `world`다. 센서 설정은 IMU의 월드 기준 자세까지 같은 좌표계에서 표시한다. RobotModel의 Description Topic은 `/robot_description`, Durability는 `Transient Local`로 둔다. 센서는 `Best Effort` + `Volatile`로 시작한다.

```bash
timeout 10s ros2 run tf2_ros tf2_echo odom base_footprint
timeout 10s ros2 run tf2_ros tf2_echo world rgbd_camera_optical_frame
ros2 run tf2_tools view_frames
```

`view_frames`는 현재 디렉터리에 TF 트리 PDF를 만들고 종료한다. `/tf` 발행자가 여러 개인 것만으로 중복 TF라고 판정하지 않는다. 같은 **자식 프레임**을 두 곳에서 발행하는지 확인한다.

## 센서 토픽

| 센서 | 토픽 | RViz 디스플레이 | 메시지 프레임 |
| --- | --- | --- | --- |
| IMU | `/imu/data` | `rviz_imu_plugin/Imu` | `imu_link` |
| 흑백 | `/camera/image_raw` | Image | `camera_optical_frame` |
| 스테레오 왼쪽 | `/stereo/left/image_raw` | Image | `stereo_camera_left_optical_frame` |
| 스테레오 오른쪽 | `/stereo/right/image_raw` | Image | `stereo_camera_right_optical_frame` |
| RGBD 색상·깊이 | `/rgbd/image_raw`, `/rgbd/depth/image_raw` | Image | `rgbd_camera_optical_frame` |
| RGBD 점군 | `/rgbd/points` | PointCloud2, RGB8 색상 | `rgbd_camera_optical_frame` |
| 어안 | `/fisheye/image_raw` | Image | `fisheye_camera_optical_frame` |
| 2D 라이다 | `/scan` | LaserScan | `lidar_2d_link` |
| 3D 라이다 | `/points` | PointCloud2, AxisColor 색상 | `lidar_3d_link` |

영상과 같은 접두사의 `/camera_info`에서 보정값을 받는다. RGBD 깊이 보정은 `/rgbd/depth/camera_info`다. Classic RGBD 점군은 광학 좌표계의 **+Z 전방**이며, 라이다는 센서 링크의 **+X 전방**이다.

스테레오 좌우 간격은 0.08 m다. 기본 오른쪽 `CameraInfo.p[3]`은 약 −22.170, 왼쪽은 0이다. 독립 카메라이므로 시차 계산 전에는 영상 타임스탬프를 확인한다. 어안 영상은 `equidistant` 렌즈지만 기본 CameraInfo는 핀홀 모델이므로 정밀 역투영에 사용하지 않는다.

```bash
timeout 10s ros2 topic echo /scan --field header --once \
  --qos-reliability best_effort
timeout 10s ros2 topic echo /rgbd/depth/image_raw --field encoding --once \
  --qos-reliability best_effort
timeout 10s ros2 topic hz /imu/data
timeout 10s ros2 topic bw /points
```

깊이 영상의 encoding은 `32FC1`, 단위는 m다. 계속 출력하는 명령은 10초 뒤 종료된다. `timeout`의 코드 124는 관찰 시간 종료를 뜻한다. `echo --once`가 아무 값도 받지 못했다면 토픽·프로필·일시 정지·QoS를 확인한다.

## Gazebo Classic 플러그인

| 기능 | 라이브러리 |
| --- | --- |
| 차동 구동 | `libgazebo_ros_diff_drive.so` |
| Ackermann 구동 | `libgazebo_ros_ackermann_drive.so` |
| 관절 상태 | `libgazebo_ros_joint_state_publisher.so` |
| IMU | `libgazebo_ros_imu_sensor.so` |
| 카메라 | `libgazebo_ros_camera.so` |
| 2D/3D 라이다 | `libgazebo_ros_ray_sensor.so` |
| 직접 만든 기준 궤적 | `libground_truth_path_plugin.so` |

```bash
find "$(ros2 pkg prefix gazebo_plugins)/lib" -name 'libgazebo_ros_*.so'
find "$(ros2 pkg prefix gazebo_tutorial_plugins)/lib" \
  -name 'libground_truth_path_plugin.so'
```

직접 만든 플러그인은 `package.xml`의 `<gazebo_ros plugin_path="${prefix}/../../lib"/>`로 탐색 경로를 등록한다. `${prefix}`는 이 설정에서 패키지의 share 디렉터리다. 자세한 빌드·오류 확인은 [플러그인 장](07_custom_plugin.md)을 참고한다.

## 모델·월드 정적 검사

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
for model in diffbot rover_diff rover_ackermann sensor_bot; do
  xacro "src/gazebo_tutorial_description/urdf/${model}.urdf.xacro" \
    > "/tmp/${model}.urdf"
  check_urdf "/tmp/${model}.urdf"
done
for profile in all cameras lidars minimal; do
  xacro src/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro \
    "sensor_profile:=${profile}" > "/tmp/sensor_bot_${profile}.urdf"
  check_urdf "/tmp/sensor_bot_${profile}.urdf"
done
gz sdf -k src/gazebo_tutorial_bringup/worlds/empty.world
gz sdf -k src/gazebo_tutorial_bringup/worlds/sensor.world
```

URDF에서는 파싱 성공과 링크 트리, SDF에서는 검사 성공을 확인한다. 이는 문법 검사이며 실제 주행·센서 측정·RViz 표시는 별도로 검증해야 한다.

## 종료와 재실행

키보드 조종에서 `k`로 정지한 뒤 키보드 노드를 종료하고, Gazebo를 실행한 터미널에서도 `Ctrl+C`를 누른다. 종료 로그를 기다린 뒤 필요하면 남은 프로세스를 조회한다.

```bash
pgrep -af 'gzserver|gzclient|robot_state_publisher|rviz2'
ros2 node list
```

Xacro와 실행 파일을 바꿨다면 다시 실행한다. C++ 소스나 설치 설정을 바꿨다면 먼저 다시 빌드한다. 매번 `build/`, `install/`, `log/`를 삭제할 필요는 없다. Gazebo 초기화로 메시지 시각이 뒤로 가면 이 저장소의 Path 노드·플러그인은 이전 궤적을 비운다.
