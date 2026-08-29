# TF·Joint State·RViz 검증

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `ros_gz_bridge` 심화

## 학습 목표

- URDF joint가 TF로 변환되는 과정을 설명한다.
- `odom → base_link → sensor_link` TF 트리의 소유자를 구분한다.
- `/joint_states`, `/tf`, `/tf_static`, `/odom`의 역할을 구분한다.
- keyboard teleop으로 주행하고 wheel odometry 궤적을 RViz에서 확인한다.

## URDF 기반 TF의 두 종류

`robot_state_publisher`는 URDF의 joint를 읽는다. fixed joint는 한 번만 필요한 정적 변환으로, revolute·continuous joint는 `/joint_states`의 위치가 바뀔 때마다 동적 변환으로 발행한다.

```xml
<!-- 정적 센서 TF: base_link → lidar_link -->
<joint name="lidar_joint" type="fixed">
  <parent link="base_link"/>
  <child link="lidar_link"/>
  <origin xyz="0.10 0 0.09" rpy="0 0 0"/>
</joint>

<!-- 동적 바퀴 TF: base_link → left_wheel_link -->
<joint name="left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="left_wheel_link"/>
  <origin xyz="0 0.19 -0.06" rpy="0 0 0"/>
  <axis xyz="0 1 0"/>
</joint>
```

fixed joint는 `/tf_static`, 바퀴처럼 움직이는 joint는 `/joint_states`를 입력으로 `/tf`에 나타난다. `/joint_states`가 끊겨도 센서 fixed TF는 남을 수 있으므로 두 경로를 따로 확인한다.

## TF 소유권

단일 로봇의 정상 트리는 다음과 같다.

```text
odom                       ← DiffDrive 또는 Ackermann odometry가 소유
└── base_link              ← robot_state_publisher의 URDF root
    ├── left_wheel_link    ← /joint_states로 갱신
    ├── right_wheel_link   ← /joint_states로 갱신
    ├── lidar_link         ← fixed joint
    ├── imu_link           ← fixed joint
    └── camera_link
        └── camera_optical_frame
```

Nav2를 켜면 localization이 `map → odom`을 추가한다. `odom → base_link`를 controller와 별도 node가 동시에 발행하면 child frame에 parent가 둘 생기거나 transform이 튄다. TF 경계마다 소유자를 하나만 둔다.

<figure class="course-figure" id="intermediate-tf-composition">
  <img src="../../assets/intermediate/tf-composition.svg" alt="odom base_link sensor_link TF 변환 합성과 소유자 구조도" loading="lazy">
  <figcaption>그림 1. controller와 robot_state_publisher가 서로 다른 TF 경계를 한 번씩 소유한다.</figcaption>
</figure>

## 계산 예제: 두 변환 합성

<div class="course-worked" data-worked-example="tf-composition">
2차원에서 base가 odom 기준 \((1.0,0.5,30°)\), sensor가 base 기준 \((0.2,0,0°)\)라면 sensor 위치는 \((1+0.2\cos30°,\ 0.5+0.2\sin30°)=(1.173,0.600)\,\mathrm{m}\)이다. 이는 \(T^{odom}_{sensor}=T^{odom}_{base}T^{base}_{sensor}\)의 평면 예이다. 같은 child frame을 두 publisher가 소유하면 이 합성이 하나로 정해지지 않는다.
</div>

## TF와 joint state 실행 확인

GUI 없이 핵심 stack을 시작한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=false rviz:=false
```

다른 terminal에서 frame과 joint를 확인한다.

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 topic echo /joint_states --once
ros2 topic info /tf -v
ros2 topic info /tf_static -v
```

`odom → base_link`의 translation은 주행 중 변하고, `base_link → lidar_link`는 `(0.10, 0, 0.09)` 부근에서 고정되어야 한다. `/joint_states.name`에는 `left_wheel_joint`, `right_wheel_joint`가 있고 position이 주행 중 변해야 한다.

전체 tree를 파일로 남기려면 다음을 실행한다.

```bash
ros2 run tf2_tools view_frames
```

생성된 `frames.pdf`에서 child frame마다 parent가 하나인지, timestamp가 갱신되는지 확인한다.

## RViz 기본 설정

GUI로 실행한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=true rviz:=true
```

Nav2를 끈 상태에서는 RViz의 **Fixed Frame**을 `odom`으로 설정한다. 다음 display를 추가한다.

| Display | Topic/설정 | 확인할 것 |
|---|---|---|
| RobotModel | `/robot_description` | URDF link와 바퀴 회전 |
| TF | 전체 | parent 중복과 센서 frame 방향 |
| Odometry | `/odom`, Keep `100` 이상 | wheel odometry pose arrow의 누적 |
| Path | `/wheel_odom_path` | wheel odometry의 연속 궤적 |
| LaserScan | `/scan`, Best Effort | `lidar_link`에서 시작하는 scan |
| PointCloud2 | `/camera/points`, Best Effort | optical frame 방향의 depth cloud |

Nav2를 켠 상태에서는 Fixed Frame을 `map`으로 바꾸고 `/plan` Path를 별도로 추가한다. `/plan`은 planner의 예정 경로이고 `/wheel_odom_path`는 실제 wheel odometry 누적이므로 서로 다른 데이터이다.

## wheel odometry를 Path로 누적하는 코드

실행 예제의 `examples/ros2_ws/src/tutorial_bot_bringup/scripts/odom_to_path`는 `/odom` pose를 `nav_msgs/msg/Path`로 누적한다. 핵심 callback은 다음과 같다.

```python
def _on_odometry(self, message: Odometry) -> None:
    x = message.pose.pose.position.x
    y = message.pose.pose.position.y
    if self._poses:
        previous = self._poses[-1].pose.position
        if hypot(x - previous.x, y - previous.y) < self._minimum_translation:
            return

    pose = PoseStamped()
    pose.header = message.header
    pose.pose = message.pose.pose
    self._poses.append(pose)

    path = Path()
    path.header = message.header
    path.poses = list(self._poses)
    self._publisher.publish(path)
```

`minimum_translation=0.01`이면 로봇이 1 cm 이상 움직일 때만 pose를 추가하고 `max_poses=2000`이면 메모리 사용량을 제한한다. odometry header의 `frame_id`를 그대로 Path에 사용해야 RViz가 같은 기준 좌표계에서 그린다.

launch에서는 다음 node를 함께 시작한다.

```python
wheel_odom_path = Node(
    package="tutorial_bot_bringup",
    executable="odom_to_path",
    parameters=[{
        "use_sim_time": True,
        "odom_topic": "/odom",
        "path_topic": "/wheel_odom_path",
        "max_poses": 2000,
        "minimum_translation": 0.01,
    }],
)
```

## keyboard teleop으로 궤적 만들기

`simulation.launch.py`의 DiffDrive controller는 stamped velocity를 사용한다. Jazzy의 `teleop_twist_keyboard`가 `TwistStamped`를 발행하도록 설정하고 controller topic으로 remap한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p frame_id:=base_link \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

`i`, `j`, `l`, `,` 키로 직선과 회전을 조합한다. RViz의 `Wheel Odom Trajectory`가 이동 경로를 이어 그려야 한다. 동시에 message 크기와 마지막 pose를 확인한다.

```bash
ros2 topic hz /odom
ros2 topic echo /wheel_odom_path --once --field poses
```

4륜 rover 예제의 Gazebo System은 unstamped `/cmd_vel`을 사용하므로 다음처럼 실행한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

다른 terminal에서 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

전용 `rover.rviz`는 Fixed Frame `odom`, Odometry `/odom`, Path `/wheel_odom_path`를 이미 설정한다. `drive_mode:=ackermann`으로 바꿔도 같은 teleop과 RViz 관찰 절차를 사용한다.

## 자동 검증

```bash
./scripts/check_intermediate_control_tf.sh --launch
```

검증 스크립트는 여섯 frame의 반복 표본, 중복 parent 부재, controller 전환, 실제 변위를 확인한다. GUI 관찰은 이 자동 검증을 대신하지 않고 보완한다.

## 문제 해결

- RViz의 `No transform` 오류가 나오면 Fixed Frame, message `frame_id`, TF 연결을 함께 확인한다.
- Message Filter가 message를 버리면 `/clock`이 증가하는지와 모든 node의 `use_sim_time`을 확인한다.
- RobotModel은 보이나 바퀴가 돌지 않으면 `/joint_states`의 name과 position을 확인한다.
- `/odom`은 변하지만 Path가 비면 `odom_to_path` node와 `/wheel_odom_path` publisher를 확인한다.
- Path가 순간이동하면 `odom → base_link` publisher가 중복되지 않았는지 확인한다.
- LaserScan이 보이지 않으면 Reliability를 Best Effort로 바꾼다.

## 정리

URDF는 link 사이 정적 관계와 joint 축을 정의하고, `/joint_states`와 wheel odometry가 runtime의 동적 TF를 완성한다. TF, RobotModel, Odometry, Path를 함께 보면 로봇 구조와 실제 주행 궤적을 같은 좌표계에서 검증할 수 있다.

[이전: ros_gz_bridge 심화](05-bridge-yaml.md) · [다음: gz_ros2_control](07-gz-ros2-control.md)
