# URDF로 이해하는 TF와 RViz

로봇을 Gazebo에 띄웠는데 RViz에서는 바퀴가 몸체에서 떨어져 보이거나, 센서 데이터가
`No transform` 오류와 함께 사라지는 경우가 있다. 대부분은 **어떤 노드가 어느 TF를
발행해야 하는지**를 구분하지 못해서 생긴다. 이 장에서는 URDF의 joint가 TF로 바뀌는
과정부터 wheel odometry 궤적을 RViz에서 확인하는 과정까지 연결한다.

## 1. TF는 좌표계 사이의 관계다

TF는 각 link의 절대 위치 목록이 아니라, 부모 좌표계에서 자식 좌표계를 바라본 변환을
시간과 함께 관리하는 트리다. 이 튜토리얼 로봇의 중심 줄기는 보통 다음과 같다.

```text
odom → base_footprint → base_link → sensor_link
                              └──→ wheel_link
```

- `odom`: wheel odometry가 시작된 연속적인 로컬 기준 좌표계
- `base_footprint`: 지면에 투영한 로봇 기준점
- `base_link`: 관성, collision, visual이 붙는 본체 좌표계
- `*_link`: 바퀴와 센서의 장착 좌표계

TF는 트리이므로 한 child frame에는 부모가 하나만 있어야 한다. 같은 child를 두 노드가
동시에 발행하면 RViz에서 로봇이 떨리거나 위치가 순간이동한다. frame 이름에는 선행
슬래시를 붙이지 않는 것이 ROS 2 관례다. 즉 `/base_link`가 아니라 `base_link`를 쓴다.

## 2. URDF joint가 만드는 두 종류의 TF

URDF의 `<joint>`는 parent link와 child link의 좌표 관계를 정의한다.

| joint 종류 | 예 | TF 발행 방식 |
|---|---|---|
| `fixed` | `base_footprint → base_link`, `base_link → camera_link` | 시작할 때 `/tf_static`으로 한 번 발행 |
| `revolute`, `continuous`, `prismatic` | 바퀴, steering knuckle | `/joint_states` 값이 올 때마다 `/tf`로 갱신 |

예를 들어 다음 fixed joint의 `xyz`와 `rpy`는 `base_footprint`에서 `base_link`를 바라본
고정 변환이다.

```xml
<joint name="base_footprint_joint" type="fixed">
  <parent link="base_footprint"/>
  <child link="base_link"/>
  <origin xyz="0 0 0.12" rpy="0 0 0"/>
</joint>
```

바퀴처럼 움직이는 joint는 축과 현재 joint position이 모두 필요하다.

```xml
<joint name="left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="left_wheel_link"/>
  <origin xyz="0 0.18 0" rpy="-1.5708 0 0"/>
  <axis xyz="0 0 1"/>
</joint>
```

`<origin>`은 장착 위치, `<axis>`는 회전축이다. 바퀴가 엉뚱한 방향으로 돌면 visual의
회전만 고치기보다 joint 축이 바퀴의 실제 회전축과 일치하는지 먼저 확인한다.

## 3. `robot_state_publisher`의 역할

launch 파일은 Xacro를 확장한 URDF 문자열을 `robot_description` 파라미터로
`robot_state_publisher`에 전달한다. 이 노드는 다음 일을 한다.

1. URDF 트리를 읽고 fixed joint를 `/tf_static`에 발행한다.
2. `/joint_states`를 구독한다.
3. 각 movable joint의 현재 값으로 계산한 변환을 `/tf`에 발행한다.

Gazebo 안에서 joint가 움직인다는 사실만으로 ROS의 `/joint_states`가 생기지는 않는다.
모델에 Gazebo ROS joint-state publisher 플러그인을 넣거나, controller가
`sensor_msgs/msg/JointState`를 발행해야 한다. 반대로 같은 joint state를 두 플러그인이
발행하지 않도록 하나의 소유자만 정한다.

현재 상태는 다음 명령으로 확인한다.

```bash
ros2 node info /robot_state_publisher
ros2 topic echo --once /joint_states
ros2 topic info /tf_static --verbose
```

`/tf_static`의 durability는 Transient Local이다. 늦게 시작한 RViz도 이미 발행된 fixed
transform을 받을 수 있어야 하기 때문이다.

## 4. Gazebo wheel odometry와 `odom → base_footprint`

URDF는 로봇 내부의 기구학 트리를 설명하지만 `odom`에서 로봇이 어디에 있는지는 알지
못한다. Differential Drive 플러그인은 wheel 회전량을 적분해 이 변환을 계산한다.
이 튜토리얼의 differential drive 플러그인은 다음 두 출력을 소유한다.

- `/odom`: `nav_msgs/msg/Odometry`, 보통 `header.frame_id: odom`,
  `child_frame_id: base_footprint`
- `/tf`: `odom → base_footprint` 동적 transform

따라서 완전한 트리는 drive 플러그인의 `odom → base_footprint`와
`robot_state_publisher`의 `base_footprint → ...`가 이어져 만들어진다.

Humble의 `gazebo_ros_ackermann_drive`는 이름과 달리 wheel encoder를 적분하지 않고
Gazebo world pose를 Odometry로 내보낸다. 이를 wheel odometry로 오해하지 않도록
Ackermann Xacro는 built-in 출력을 `/ground_truth/odom`으로 remap하고 TF 발행을 끈다.
대신 bringup의 `ackermann_odom` 노드가 rear left/right wheel position 평균 이동거리와
front left/right steering angle의 Ackermann 기하로부터 복원한 등가 중앙 조향각을 bicycle model로
적분해 `/odom` 및
`odom → base_footprint`를 발행한다. world-pose 입력은 별도 Path로 바꿔 비교한다.

중복을 피하기 위한 원칙은 간단하다.

- drive 플러그인이 `odom → base_footprint`를 발행하면 EKF나 별도 odometry 노드는 같은
  transform을 발행하지 않는다.
- `robot_state_publisher`가 wheel transform을 만들고 있다면 drive 플러그인의
  `publish_wheel_tf`는 끈다.
- localization을 추가해도 보통 localization은 `map → odom`, drive는
  `odom → base_footprint`를 각각 소유한다.

## 5. TF를 눈으로 확인하기

먼저 workspace를 빌드하고 한 로봇을 실행한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

두 frame 사이 변환이 계속 들어오는지 확인한다.

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_link left_wheel_link
```

전체 트리와 발행 주기는 다음 명령이 유용하다.

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_monitor odom base_link
```

RViz의 `TF` display에서 이름과 축을 켜면 부모-자식 관계를 3차원으로 볼 수 있다.
`Fixed Frame`은 이 실습에서 `odom`으로 둔다. `base_link`로 두면 로봇이 화면 중앙에
고정되어 주행 궤적이 움직이는 것처럼 보여 odometry 검증에 적합하지 않다.

## 6. Wheel odometry trajectory 실습

각 bringup launch는 `gazebo_tutorial_tools/odom_to_path`를 함께 실행한다. 이 노드는
`/odom`의 pose를 누적해 `/wheel_odom_path`라는 `nav_msgs/msg/Path`를 발행한다. 기본
RViz 설정에는 초록색 `Wheel Odom Trajectory` display가 이미 들어 있다.

별도 터미널에서 키보드 teleop을 시작한다.

```bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

직진, 제자리 회전, 사각형 또는 원 궤적을 차례로 주행한다. Differential Drive에서는
좌우 wheel 속도 차이가 곡률로 나타나며 Ackermann 모델에서는 steering angle 때문에
회전 반경을 가진 곡선이 나타나야 한다.

토픽 계약을 직접 확인할 수도 있다.

```bash
ros2 topic hz /odom
ros2 topic echo --once /odom
ros2 topic info /wheel_odom_path --verbose
```

RViz를 닫았다가 다시 열어도 마지막 Path가 즉시 보인다. Path publisher가 Reliable +
Transient Local QoS를 사용하기 때문이다. Gazebo 계열 publisher와 폭넓게 맞도록 Odometry
입력은 Best Effort + Volatile로 구독한다.

launch에서 토픽과 보관할 점 수를 바꿀 수 있다.

```bash
ros2 launch gazebo_tutorial_bringup rover_diff.launch.py \
  odom_topic:=/odom path_topic:=/wheel_odom_path max_points:=5000
```

`path_frame`을 비워 두면 Odometry의 `header.frame_id`를 그대로 사용한다. 이 노드는 TF
좌표 변환기가 아니므로 `path_frame:=map`처럼 입력과 다른 frame 이름을 주면 pose를
거짓으로 재라벨링하지 않고 메시지를 버린다. `map` 궤적이 필요하다면 먼저 실제 TF로
pose를 변환해야 한다.

Gazebo reset으로 simulation time이 뒤로 가거나 입력 frame이 바뀌면 이전 run과 새 run이
한 선으로 이어지지 않도록 Path를 자동으로 비운다. `max_points` 기본값은 2,000으로,
장시간 실습의 메모리 사용량을 제한한다.

## 7. RViz에서 센서 frame 확인하기

센서 모델은 전용 설정으로 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all
```

`sensors.rviz`에는 IMU, mono/stereo/RGBD/fisheye 영상, 2D LaserScan, 3D PointCloud2,
RGBD point cloud가 준비되어 있다. 센서 데이터가 발행되는데 보이지 않는다면 먼저
메시지의 frame을 확인한다.

```bash
ros2 topic echo --once /scan --field header
ros2 topic echo --once /points --field header
ros2 run tf2_ros tf2_echo base_link lidar_3d_link
```

RViz가 데이터를 그리려면 메시지의 `header.frame_id`에서 `Fixed Frame`까지 이어지는 TF가
같은 timestamp에 존재해야 한다. 센서 link를 URDF에 fixed joint로 달았는지, 플러그인의
`frame_name`이 그 link 이름과 정확히 같은지 확인한다.

## 8. 중복 TF를 진단하는 순서

RViz에서 로봇이 떨리거나 `TF_OLD_DATA`, `extrapolation` 경고가 보이면 다음 순서로
범위를 줄인다.

1. `ros2 topic info /tf --verbose`로 publisher가 몇 개인지 확인한다.
2. `view_frames`에서 한 child가 기대하지 않은 parent에 붙었는지 본다.
3. drive 플러그인, EKF, static transform publisher 중 누가 같은 child를 소유하는지
   찾는다.
4. 모든 관련 노드의 `use_sim_time`이 `true`인지 확인한다.
5. wheel TF라면 drive 플러그인의 `publish_wheel_tf`와
   `robot_state_publisher + /joint_states` 중 하나만 남긴다.

```bash
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /odom_to_path use_sim_time
ros2 topic echo --once /clock
```

TF 오류는 이름만 맞춘다고 해결되지 않는다. **발행 주체, 부모-자식 방향, timestamp,
QoS** 네 가지를 함께 확인하면 원인을 빠르게 찾을 수 있다.

## 9. Wheel odometry를 해석할 때의 한계

RViz의 Path는 플러그인이 계산한 wheel odometry이지 Gazebo ground truth가 아니다.
바닥 마찰, wheel slip, 잘못된 wheel radius/separation, Ackermann steering geometry 오차가
모두 누적된다. 따라서 예쁜 궤적이 보이는 것만으로 파라미터가 정확하다고 판단하지 않는다.

- 직진 명령에서 yaw가 꾸준히 틀어지면 좌우 wheel radius와 friction을 확인한다.
- 회전 각도가 계속 작거나 크면 differential 모델의 wheel separation을 확인한다.
- Ackermann 회전 반경이 명령과 다르면 wheelbase, track width, steering limit를 확인한다.
- 실제 이동과 odometry를 비교하려면 custom ground-truth 플러그인 또는 Gazebo model pose를
  별도 frame/topic으로 기록한다. ground truth가 `odom → base_footprint`를 대신 발행하게
  해서는 안 된다.

이 저장소의 custom 플러그인은 `world` frame의 `/ground_truth_path`를 발행하고 RViz는 이를
빨간 선으로 표시한다. 공통 launch는 모든 encoder odometry 모델의 spawn `x`, `y`,
`yaw`를 `world → odom` static TF에 반영한다. 따라서 offset으로 spawn해도 0에서 시작하는
wheel odometry와 world 좌표 ground truth의 원점이 맞는다. Ackermann built-in world pose도
`/ground_truth/odom`에서 `/ground_truth_path`로 변환해 같은 방법으로 비교한다. 이미 다른
노드가 `world → odom`을 소유하면
`publish_world_odom_tf:=false`로 중복 발행을 막는다.

TF 트리의 책임을 분리해 두면 센서를 추가하거나 localization을 연결해도 같은 원칙을
그대로 적용할 수 있다.
