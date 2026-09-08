# F1TENTH 사용 안내

Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11을 기준으로 합니다. [설치 안내](docs/01_setup.md)를 먼저 마친 뒤 진행하세요. 아래에서는 저장소가 `~/robotics-sim-tutorial-kr`에 있다고 가정합니다. 다른 위치에 받았다면 `cd` 경로를 실제 위치로 바꾸세요.

## 1. 작업 공간 빌드하기

이 저장소 안의 패키지를 빌드합니다. 별도의 F1TENTH 저장소나 Cartographer 소스를 추가로 받을 필요는 없습니다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
sudo apt update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install --packages-up-to f1_robot_model
source install/setup.bash
ros2 pkg prefix f1_robot_model
```

마지막 명령에서 현재 작업 공간의 `install/f1_robot_model` 경로가 나오면 패키지를 찾은 것입니다. 빌드가 실패하면 첫 번째 `Failed` 패키지의 오류를 확인하세요. `gazebo_ros_ackermann_drive`는 별도의 ROS 패키지 이름이 아니라 `gazebo_plugins`에 포함된 플러그인입니다.

이후 **새 터미널을 열 때마다** 다음 세 줄을 먼저 실행합니다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## 2. 차량과 월드 실행하기

터미널 A에서 실행합니다. 다른 Gazebo 실습은 먼저 `Ctrl+C`로 종료하세요. 기본 토픽 이름을 공유하므로 두 실습을 동시에 실행하면 `/cmd_vel`이나 센서 데이터가 섞입니다.

```bash
ros2 launch f1_robot_model robot_spawn.launch.py
```

Gazebo Building Editor로 만든 기존 맵 `world/demomap_2/model.sdf`에 차량 한 대가 나타납니다. 차량은 월드 원점에서 `x=0`, `y=0`, `z=0`, `yaw=0`으로 생성됩니다. 기본 구성은 바퀴·IMU·2D 라이다이며, RViz에서도 차량·IMU·2D 라이다를 확인할 수 있습니다. 초기 센서 준비에 시간이 걸릴 수 있습니다. `Spawn status: SpawnEntity: Successfully spawned entity`가 출력되고 `/clock`이 흐르는지 확인하세요.

```bash
# 터미널 B
ros2 topic echo /clock --once
ros2 topic list
```

기본 실행에서는 `/scan`, `/imu/data`, `/joint_states`, `/odom`이 보입니다. `/camera/...`, `/lidar_3d/...`, `/gps/...`, `/left_camera/...`, `/right_camera/...`는 해당 옵션을 켜기 전에는 나타나지 않아야 합니다.

Gazebo 창을 닫고 계산만 실행하려면 A의 실행을 종료한 뒤 다음 명령을 사용합니다. 카메라 렌더링에는 여전히 그래픽 환경이 필요하며, CI에서는 Xvfb를 사용합니다.

```bash
ros2 launch f1_robot_model robot_spawn.launch.py gui:=false rviz:=false
```

기존 `display.launch.py`도 같은 Building Editor 맵과 기본 센서 구성을 실행합니다. 다음 명령은 위 실행을 종료한 뒤 사용하세요.

```bash
ros2 launch f1_robot_model display.launch.py
```

다른 월드를 열 때는 launch 파일을 수정하지 않고 절대 경로를 전달합니다.

```bash
ros2 launch f1_robot_model robot_spawn.launch.py world:=/absolute/path/to/my_world.world
```

`/absolute/path/to/my_world.world`는 예시 자리입니다. 실제 파일로 바꾸지 않으면 실행되지 않습니다. 기본값과 선택 인자는 `ros2 launch f1_robot_model robot_spawn.launch.py --show-args`로 확인할 수 있습니다.

## 3. 차량 주행하기

차량의 앞뒤 차축 간 거리는 0.325 m, 바퀴 반지름은 0.05 m입니다. 플러그인이 실제 충돌 형상에서 치수를 읽습니다. 차체 기준 `base_link`에서 뒤 차축은 x = -0.16 m, 앞 차축은 x = 0.165 m입니다.

기본으로 켜지는 변환 노드에 `/drive`를 보내는 방법부터 사용합니다. 기존 맵의 원점 주변에는 벽이 있으므로 Gazebo에서 앞쪽 공간을 확인한 뒤 짧게 움직이세요. 터미널 B에서 아래 명령을 실행해 0.15 m/s로 전진시킵니다.

```bash
ros2 topic pub --rate 10 /drive ackermann_msgs/msg/AckermannDriveStamped \
  '{drive: {speed: 0.15, steering_angle: 0.0}}'
```

처음에는 1초 정도만 움직인 뒤 `Ctrl+C`로 발행을 끝내고, **바로 정지 명령을 보냅니다.** 플러그인은 마지막 명령을 유지하므로 발행을 끝내는 것만으로 차가 멈추지 않습니다.

```bash
ros2 topic pub --once /drive ackermann_msgs/msg/AckermannDriveStamped \
  '{drive: {speed: 0.0, steering_angle: 0.0}}'
ros2 topic echo /odom --once
```

다음에는 천천히 왼쪽으로 돌립니다. 앞바퀴 방향과 `/odom`의 위치·자세가 함께 바뀌는지 확인하세요. 정지 상태에서는 차동 구동 로봇처럼 제자리 회전하지 않습니다.

```bash
ros2 topic pub --rate 10 /drive ackermann_msgs/msg/AckermannDriveStamped \
  '{drive: {speed: 0.15, steering_angle: 0.2}}'
```

1초 정도 뒤 `Ctrl+C`를 누르고 위의 정지 명령을 다시 실행합니다. `speed`의 단위는 m/s, `steering_angle`은 rad이며 양수는 왼쪽입니다. `speed`에 음수를 넣으면 후진합니다. 변환 노드는 Classic 플러그인의 후진 시 조향 부호 처리를 보정합니다.

직접 `/cmd_vel`을 사용하는 경우에는 아래 차이를 구분해야 합니다.

| 입력 | `linear.x` | `angular.z` |
|---|---|---|
| 일반 ROS `Twist` 의미 | 전진 속도(m/s) | 차체 각속도(rad/s) |
| 이 Classic Ackermann 플러그인 | 전진 속도(m/s) | 조향각(rad); 내부에서 속도 부호를 곱함 |

플러그인에 전달할 조향각을 다시 `v × tan(조향각) / 차축 간 거리`로 바꾸면 안 됩니다. 그 식의 결과는 차체 각속도입니다. 기존 변환 코드는 이 둘을 혼동했으며, 현재 코드는 조향각을 전달합니다. 구현 근거는 [공식 Ackermann 플러그인 소스](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_ackermann_drive.cpp)의 `OnCmdVel`과 `OnUpdate`입니다.

직접 토픽을 확인할 때는 다음처럼 사용합니다. `/drive`, `/cmd_vel`, 조이스틱 중 **한 가지 명령 공급원만** 사용하세요.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.15}, angular: {z: 0.2}}'
# Ctrl+C를 누른 뒤 정지
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'
```

조이스틱은 `joystick:=true`일 때만 실행됩니다. 기본 설정은 `config/MXswitch.config.yaml`이며, A 버튼을 누른 상태에서 왼쪽 스틱을 움직입니다. 장치마다 축과 버튼 번호가 다르므로 `/joy`를 먼저 확인하세요.

## 4. 기본 센서와 RViz 확인하기

### 토픽과 프레임

| 데이터 | 토픽 | `header.frame_id` |
|---|---|---|
| 2D 라이다 | `/scan` | `laser` |
| IMU | `/imu/data` | `imu` |
| 주행 위치 | `/odom` | `odom` (`child_frame_id`: `base_link`) |

터미널 B에서 한 개씩 확인합니다. `--once`는 한 메시지를 받은 뒤 종료합니다.

```bash
ros2 topic echo /scan --once --field header
ros2 topic echo /imu/data --once
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo odom laser
```

`tf2_echo`는 계속 실행되므로 확인 후 `Ctrl+C`로 종료합니다. Gazebo에서 보이는 벽의 방향과 RViz의 2D 라이다 점들을 비교하세요. 차량이 움직이면 바퀴 각도와 `/odom`이 바뀌고, 라이다 점들은 주변 벽의 위치를 계속 가리켜야 합니다. 측정 거리는 맵 안의 실제 위치와 방향에 따라 달라집니다. 무한대 라이다 값은 측정 범위 안에 반사면이 없다는 뜻일 수 있으므로, 모든 값이 유한해야 한다고 가정하지 마세요.

RViz 설정을 새로 만들 때는 다음 값을 사용합니다.

| RViz 항목 | 설정 |
|---|---|
| Global Options → Fixed Frame | `odom` |
| RobotModel → Description Topic | `/robot_description`, Durability `Transient Local` |
| LaserScan → Topic | `/scan`, Reliability `Best Effort` |
| Imu → Topic | `/imu/data`, Reliability `Best Effort` |

`robot_state_publisher`가 센서와 바퀴 TF를 담당하고, Gazebo의 조인트 상태 플러그인이 실제 바퀴 각도를 발행합니다. 시뮬레이션 중 `joint_state_publisher`를 별도로 실행하면 실제 각도와 0도 값이 번갈아 전달될 수 있습니다. Ackermann 플러그인의 바퀴 TF도 꺼서 같은 TF를 두 곳에서 발행하지 않도록 했습니다.

## 5. RGB-D 카메라와 3D 라이다 추가하기

기본 차량과 맵은 그대로 두고 필요한 센서만 추가합니다. `depth_camera`, `lidar_3d`, `stereo_camera`, `gps`의 기본값은 모두 `false`입니다.

### 실행할 구성 선택하기

아래 네 가지 중 **하나만** 실행하세요. 구성을 바꿀 때는 속도 0을 보낸 뒤 터미널 A에서 `Ctrl+C`를 눌러 이전 실행을 종료하고, 같은 터미널에서 새 명령을 실행합니다.

```bash
# 1. 기본 차량: 바퀴 + IMU + 2D 라이다
ros2 launch f1_robot_model robot_spawn.launch.py

# 2. 기본 차량에 RGB-D 카메라만 추가
ros2 launch f1_robot_model robot_spawn.launch.py depth_camera:=true

# 3. 기본 차량에 3D 라이다만 추가
ros2 launch f1_robot_model robot_spawn.launch.py lidar_3d:=true

# 4. 기본 차량에 RGB-D 카메라와 3D 라이다를 함께 추가
ros2 launch f1_robot_model robot_spawn.launch.py depth_camera:=true lidar_3d:=true
```

기본 RViz 설정에서는 RGB-D 옵션에 맞춰 `Depth points`와 `RGB camera`가, 3D 라이다 옵션에 맞춰 `3D LiDAR (optional)`이 자동으로 켜집니다. 옵션을 끄면 해당 센서도 생성되지 않습니다. 토픽을 구독하거나 TF를 확인하는 명령은 해당 센서를 켠 상태에서 실행하세요.

### RGB-D 영상과 점군 확인하기

`depth_camera:=true`로 실행한 뒤 터미널 B에서 확인합니다.

```bash
ros2 topic echo /camera/image_raw --once --field header
ros2 topic echo /camera/camera_info --once
ros2 topic echo /camera/depth/image_raw --once --field header
ros2 topic echo /camera/points --once --field header
ros2 run tf2_ros tf2_echo odom camera_link_optical
```

| 데이터 | 토픽 | `header.frame_id` |
|---|---|---|
| RGB 영상 / 보정 정보 | `/camera/image_raw`, `/camera/camera_info` | `camera_link_optical` |
| 깊이 영상 / 보정 정보 | `/camera/depth/image_raw`, `/camera/depth/camera_info` | `camera_link_optical` |
| RGB-D 점군 | `/camera/points` | `camera_link_optical` |

RViz에서 Image의 토픽은 `/camera/image_raw`, PointCloud2의 토픽은 `/camera/points`이며, 둘 다 Reliability를 `Best Effort`로 설정합니다. RGB 영상 속 벽이 점군에서도 차량 앞쪽에 서 있는지 확인하세요. 2D 라이다와 카메라의 설치 위치와 높이는 다르므로 모든 점이 완전히 겹칠 필요는 없습니다. 바닥과 벽의 방향이 Gazebo 화면과 맞는지가 먼저입니다.

카메라 본체는 x축 전방, y축 왼쪽, z축 위쪽입니다. **Classic 카메라 점군은 optical 좌표인 z축 전방, x축 오른쪽, y축 아래쪽**을 사용합니다. 따라서 영상·CameraInfo·점군을 모두 `camera_link_optical`로 표시하고, 고정 조인트로 본체 좌표와 연결합니다. 점군의 프레임 이름만 `camera_link`로 바꾸면 벽이 옆이나 바닥으로 눕습니다. [공식 카메라 구현](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_camera.cpp)에서 토픽 이름과 좌표 변환을 확인할 수 있습니다.

### 3D 라이다 점군 확인하기

`lidar_3d:=true`로 실행한 뒤 터미널 B에서 확인합니다.

```bash
ros2 topic echo /lidar_3d/points --once --field header
ros2 topic hz /lidar_3d/points
# hz를 Ctrl+C로 종료한 뒤 실행
ros2 run tf2_ros tf2_echo odom lidar_3d_link
```

RViz의 PointCloud2 토픽은 `/lidar_3d/points`, Reliability는 `Best Effort`입니다. 프레임은 `lidar_3d_link`이며, 라이다 본체 좌표의 x축이 전방입니다. 카메라의 optical 프레임과 혼동하지 마세요. 2D 라이다가 한 높이에서 벽을 그리는 데 비해, 3D 라이다는 여러 높이의 벽과 바닥을 보여 줍니다.

이 센서는 수평 220개 × 수직 32개 광선을 사용하며, 범위 밖의 점은 기본적으로 제외합니다. 따라서 한 메시지의 점 개수가 항상 7,040개인 것은 아닙니다. CPU·그래픽 성능과 실시간 배율에 따라 벽시계 기준 수신 주기가 달라질 수 있습니다. `hz`와 `tf2_echo`는 확인 후 각각 `Ctrl+C`로 종료하세요.

### 좌우 카메라와 GPS가 필요한 경우

이 두 옵션도 기본으로 꺼져 있습니다. 앞의 RGB-D·3D 라이다 실습에는 필요하지 않으며, 별도로 사용하려면 기존 실행을 종료한 뒤 다음 명령 중 하나를 실행합니다.

```bash
ros2 launch f1_robot_model robot_spawn.launch.py stereo_camera:=true
# 위 실행을 Ctrl+C로 종료한 뒤 GPS만 추가하는 예
ros2 launch f1_robot_model robot_spawn.launch.py gps:=true
```

`stereo_camera:=true`는 `/left_camera/image_raw`, `/right_camera/image_raw`와 각 `camera_info`를 추가합니다. 좌우 간격은 0.2 m이며, 오른쪽 보정 정보의 투영 행렬에 이 간격이 반영됩니다. RViz에 Image 두 개를 추가해 각각의 토픽을 선택하고 Reliability를 `Best Effort`로 설정하세요. 두 센서는 독립 카메라이므로 스테레오 알고리즘을 연결할 때는 영상 시각 동기화와 보정을 별도로 확인해야 합니다.

`gps:=true`는 `/gps/data`를 추가하며 `header.frame_id`는 `gps`입니다. `ros2 topic echo /gps/data --once`로 수신을 확인합니다.

## 6. 저장된 지도에서 위치 추정하기

이 단계는 AMCL의 위치 추정 실습입니다. 경로 계획과 자동 주행 노드는 실행하지 않습니다. 기존 시뮬레이터를 종료한 뒤 실행하세요.

```bash
ros2 launch f1_robot_model amcl.launch.py
```

이 launch는 기본 주행 실습과 같은 `demomap_2/model.sdf` 월드에 대응하는 `map/demomap_2.yaml`을 함께 엽니다. 지도와 월드는 한 쌍입니다. 직접 만든 지도를 사용할 때는 `map:=/절대/경로/지도.yaml world:=/절대/경로/월드.world`를 함께 전달합니다. YAML 안의 이미지 경로는 YAML 파일 위치를 기준으로 해석합니다.

터미널 B에서 지도와 AMCL이 활성화됐는지 확인합니다.

```bash
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 topic echo /map --once --field info --qos-durability transient_local
```

두 노드가 `active`이면 RViz의 `2D Pose Estimate`로 차량의 위치와 앞 방향을 지정합니다. 그다음 아래 명령으로 `map → odom`이 연결됐는지 확인하세요.

```bash
ros2 run tf2_ros tf2_echo map odom
```

초기 위치를 지정하기 전에는 RViz Fixed Frame `map`에서 차량 표시가 준비되지 않을 수 있습니다. 위치 지정 후에도 TF가 없으면 지도·`/scan`·`/odom` 순서로 확인합니다. 주행용 `odom → base_link`는 계속 필요합니다. SLAM이나 AMCL을 사용한다는 이유만으로 odometry TF를 끄지 마세요. 각 TF 연결은 한 노드만 발행해야 합니다.

## 7. 막혔을 때와 종료 방법

| 증상 | 먼저 확인할 내용 |
|---|---|
| 패키지를 찾지 못함 | 새 터미널에서 `/opt/ros/humble/setup.bash`와 작업 공간의 `install/setup.bash`를 순서대로 적용했는지 |
| 차량이 바뀌지 않거나 바퀴가 흔들림 | `/joint_states` 발행자가 중복되지 않는지, 다른 실습이 남아 있지 않은지 |
| RViz 모델이 늦게 열면 안 보임 | RobotModel의 Durability가 `Transient Local`인지 |
| 센서 토픽은 있지만 RViz에 안 보임 | Fixed Frame, 메시지 `frame_id`, 해당 시각의 TF, `Best Effort` 설정 |
| 카메라나 3D 라이다 토픽이 없음 | 기본으로 꺼져 있으므로 실행 명령에 `depth_camera:=true` 또는 `lidar_3d:=true`를 추가했는지 |
| 3D 라이다 플러그인을 찾지 못함 | `--packages-up-to f1_robot_model`로 의존 패키지도 빌드했는지, 설치 공간을 source했는지 |
| 차가 계속 움직임 | 명령 발행 종료 뒤 속도 0을 따로 보냈는지 |
| 지도와 라이다가 어긋남 | 실제 월드에 대응하는 지도를 사용하고 초기 위치·방향을 지정했는지 |

`Steering wheel joint [steering_wheel_joint] not found`는 운전자가 돌리는 **운전대 모델의 선택 조인트**가 없다는 뜻입니다. 이 차량은 운전대 장식을 포함하지 않습니다. 네 바퀴와 앞바퀴 조향 힌지 두 개를 제어하는 조인트는 별도로 존재하므로, 이 경고만으로 차량 조향이 실패한 것은 아닙니다. 실제 바퀴 조인트를 찾지 못했다는 오류와 구분하세요. [공식 플러그인](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_ackermann_drive.cpp)은 운전대가 없으면 여섯 개 주행 조인트로 계속 실행합니다.

끝낼 때는 속도 0을 발행한 뒤 터미널 A에서 `Ctrl+C`를 누릅니다. `tf2_echo`, `topic hz` 같은 관찰 명령도 각각 종료합니다. 실제 검증 결과와 아직 수동 확인이 필요한 범위는 저장소의 Humble 점검 기록을 기준으로 확인하세요.
