# gazebo_tutorial_bringup

Gazebo Classic 서버, Xacro 변환, `robot_state_publisher`, model spawn,
wheel odometry Path 변환, RViz를 한 번에 시작하는 launch 패키지다.

## 빌드

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## 실행

```bash
# 2륜 + caster
ros2 launch gazebo_tutorial_bringup diffbot.launch.py

# 4륜 differential/skid steering
ros2 launch gazebo_tutorial_bringup rover_diff.launch.py

# 4륜 Ackermann steering
ros2 launch gazebo_tutorial_bringup rover_ackermann.launch.py

# 센서 로봇. 기본 sensor_profile은 all, 기본 world는 sensor.world
ros2 launch gazebo_tutorial_bringup sensors.launch.py

# 새 Xacro를 같은 파이프라인으로 빠르게 실행
ros2 launch gazebo_tutorial_bringup simulation.launch.py \
  xacro_file:=my_robot.urdf.xacro entity_name:=my_robot
```

각 launch는 `gazebo_ros`의 `gazebo.launch.py`로 Gazebo 11을 띄운다. 이어서 Xacro를
`robot_description`으로 변환하고, `robot_state_publisher`와 `spawn_entity.py`를 실행한다.
`gazebo_tutorial_tools/odom_to_path`가 `/odom`을 `/wheel_odom_path`로 누적하며 RViz는
각 로봇에 맞는 설정을 자동으로 불러온다.

custom ground-truth 플러그인의 `world` frame Path도 같은 RViz에서 비교할 수 있도록
기본 launch는 `world → odom` static TF를 발행한다. encoder odometry가 0에서 시작하므로
모든 로봇의 spawn `x`, `y`, `yaw`를 변환에 반영하며, offset spawn에서도 두 궤적의
원점이 맞는다. 기존 TF가 이 변환을 소유한다면 `publish_world_odom_tf:=false`로 끈다.

Gazebo Classic의 built-in Ackermann 플러그인은 wheel encoder가 아니라 world pose를
Odometry로 계산한다. `rover_ackermann.launch.py`는 이 출력을 `/ground_truth/odom`으로
분리하고 `ackermann_odom` 노드가 rear wheel position과 front steering angle을 적분해
실제 wheel odometry `/odom`과 `odom → base_footprint` TF를 발행한다. 동시에 built-in
world pose를 `/ground_truth_path`로 바꿔 빨간 선으로 비교한다.

키보드 제어는 입력을 받아야 하므로 별도 터미널에서 실행한다.

```bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

## 자주 쓰는 launch 인자

```bash
# GUI 없이 실행하고 RViz도 끄기
ros2 launch gazebo_tutorial_bringup diffbot.launch.py gui:=false rviz:=false

# 정지 상태로 시작하기
ros2 launch gazebo_tutorial_bringup rover_diff.launch.py pause:=true

# 카메라 센서만 생성하기
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=cameras

# 다른 world와 spawn pose 사용하기
ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  world:=/absolute/path/to/my.world x:=1.0 y:=-0.5 yaw:=1.57
```

전체 인자는 다음 명령으로 확인한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py --show-args
```

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `gui` | `true` | Gazebo client 실행 여부. `false`면 headless |
| `pause` | `false` | physics 정지 상태로 시작 |
| `use_sim_time` | `true` | ROS 노드가 `/clock`을 사용 |
| `rviz` | `true` | RViz 자동 실행 여부 |
| `entity_name` | 로봇별 이름 | Gazebo 안에서 중복되지 않을 model 이름 |
| `x`, `y`, `z`, `yaw` | `0, 0, 0.1, 0` | spawn pose |
| `odom_topic` | `/odom` | Path 변환 입력 |
| `path_topic` | `/wheel_odom_path` | RViz Path 출력 |
| `ground_truth_odom_topic` | `/ground_truth/odom` | Ackermann world-pose 입력 |
| `ground_truth_path_topic` | `/ground_truth_path` | Ackermann 비교 Path 출력 |
| `path_frame` | 빈 값 | 비어 있으면 Odometry frame 사용 |
| `max_points` | `2000` | Path가 유지할 최대 pose 수 |
| `publish_world_odom_tf` | `true` | ground truth 비교용 `world → odom` static TF |
| `ackermann_publish_tf` | `true` | Ackermann wheel odometry의 `odom → base_footprint` TF |
| `sensor_profile` | 로봇별 값 | `all`, `cameras`, `lidars`, `minimal` |

센서 전용 `sensor.world`에는 서로 다른 거리와 색의 box, cylinder, wall이 있어 Camera와
LiDAR를 시작하자마자 확인할 수 있다. 센서 설정은 `/imu/data`, `/camera/image_raw`, stereo/RGBD/fisheye 이미지,
`/scan`, `/points`, `/rgbd/points`를 한 화면에서 확인하도록 준비되어 있다. RViz가 늦게
시작되어도 궤적이 바로 보이도록 Path 출력은 Reliable + Transient Local QoS를 쓴다.
