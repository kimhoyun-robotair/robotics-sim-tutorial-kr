# TF·Joint State·RViz 검증

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `ros_gz_bridge` 심화

## 학습 목표

- URDF 조인트가 TF로 변환되는 과정을 설명한다.
- `odom → base_link → sensor_link` TF 트리의 소유자를 구분한다.
- `/joint_states`, `/tf`, `/tf_static`, `/odom`의 역할을 구분한다.
- 키보드 조종으로 주행하고 바퀴 오도메트리 궤적을 RViz에서 확인한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## URDF 기반 TF의 두 종류

`robot_state_publisher`는 URDF의 조인트를 읽는다. 고정 조인트는 한 번만 필요한 정적 변환으로, revolute·continuous 조인트는 `/joint_states`의 위치가 바뀔 때마다 동적 변환으로 발행한다.

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

고정 조인트는 `/tf_static`, 바퀴처럼 움직이는 조인트는 `/joint_states`를 입력으로 `/tf`에 나타난다. `/joint_states`가 끊겨도 센서 고정 TF는 남을 수 있으므로 두 경로를 따로 확인한다.

## 어느 노드가 TF를 발행하는가

2륜 `tutorial_bot`의 정상 TF는 다음과 같다. 각 변환을 발행하는 노드를 함께 확인한다.

| 변환 | 발행하는 노드 | 확인할 입력 |
|---|---|---|
| `odom → base_link` | `diff_drive_controller` | 바퀴 회전량 |
| `base_link → left_wheel_link`, `right_wheel_link` | `robot_state_publisher` | `/joint_states` |
| `base_link → lidar_link`, `imu_link`, `camera_link` | `robot_state_publisher` | URDF 고정 조인트 |
| `camera_link → camera_optical_frame` | `robot_state_publisher` | URDF 광학 좌표계 회전 |

4륜 예제의 루트는 `base_footprint`이므로 `odom → base_footprint → base_link`가 된다. 두 모델의 TF 구조를 혼동하지 않는다.

Nav2를 켜면 위치 추정이 `map → odom`을 추가한다. `odom → base_link`를 컨트롤러와 별도 노드가 동시에 발행하면 자식 좌표계에 부모가 둘 생기거나 변환이 튄다. TF 경계마다 소유자를 하나만 둔다.

<figure class="course-figure" id="intermediate-tf-composition">
  <img src="../../assets/intermediate/tf-composition.svg" alt="odom base_link sensor_link TF 변환 합성과 소유자 구조도" loading="lazy">
  <figcaption>그림 1. 컨트롤러와 robot_state_publisher가 서로 다른 TF 경계를 한 번씩 소유한다.</figcaption>
</figure>

## 계산 예제: 두 변환 합성

<div class="course-worked" data-worked-example="tf-composition">
2차원에서 로봇 몸체가 `odom` 기준 \((1.0,0.5,30°)\), 센서가 몸체 기준 \((0.2,0,0°)\)라면 센서 위치는 \((1+0.2\cos30°,\ 0.5+0.2\sin30°)=(1.173,0.600)\,\mathrm{m}\)이다. 이는 \(T^{odom}_{sensor}=T^{odom}_{base}T^{base}_{sensor}\)의 평면 예이다. 같은 자식 좌표계를 두 발행 노드가 소유하면 이 합성이 하나로 정해지지 않는다.
</div>

## TF와 조인트 상태 실행 확인

GUI 없이 핵심 시스템을 시작한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=false rviz:=false
```

다른 터미널에서 좌표계와 조인트를 확인한다.

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 topic echo /joint_states --once
ros2 topic info /tf -v
ros2 topic info /tf_static -v
```

`odom → base_link`의 위치 값은 주행 중 변하고, `base_link → lidar_link`는 `(0.10, 0, 0.09)` 부근에서 고정되어야 한다. `/joint_states.name`에는 `left_wheel_joint`, `right_wheel_joint`가 있고 위치가 주행 중 변해야 한다.

전체 트리를 파일로 남기려면 다음을 실행한다.

```bash
ros2 run tf2_tools view_frames
```

생성된 `frames*.pdf`에서 자식 좌표계마다 부모가 하나인지 확인한다. 동적 TF는 시간이 갱신되어야 한다. `/tf` 토픽에는 여러 발행 노드가 있는 것이 정상일 수 있으므로, 토픽의 발행 노드 수와 같은 변환의 중복 발행을 구분한다.

## RViz 기본 설정

앞의 GUI 없는 launch를 `Ctrl+C`로 종료한 뒤, 같은 로봇을 GUI와 함께 다시 실행한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=true rviz:=true
```

Nav2를 끈 상태에서는 RViz의 **Fixed Frame**을 `odom`으로 설정한다. 다음 표시 항목을 추가한다.

| 표시 항목 | Topic/설정 | 확인할 것 |
|---|---|---|
| RobotModel | `/robot_description` | URDF 링크와 바퀴 회전 |
| TF | 전체 | 부모 중복과 센서 좌표계 방향 |
| Odometry | `/odom`, Keep `100` 이상 | 바퀴 오도메트리 위치와 자세 화살표의 누적 |
| Path | `/wheel_odom_path` | 바퀴 오도메트리의 연속 궤적 |
| LaserScan | `/scan`, Best Effort | `lidar_link`에서 시작하는 scan |
| PointCloud2 | `/camera/points`, Best Effort | `camera_link` 기준의 깊이 포인트 클라우드 |

Nav2를 켠 상태에서는 Fixed Frame을 `map`으로 바꾸고 `/plan` Path를 별도로 추가한다. `/plan`은 경로 계획기의 예정 경로이고 `/wheel_odom_path`는 실제 바퀴 오도메트리 누적이므로 서로 다른 데이터이다.

RViz 왼쪽 **Displays → Global Options → Fixed Frame**에서 `odom`을 선택한다. 센서는 **Add → By topic**에서 추가하고, LaserScan·PointCloud2의 **Topic → Reliability Policy**를 `Best Effort`로 맞춘다. RobotModel은 **Description Source: Topic**, `/robot_description`, **Durability: Transient Local**을 사용한다. 저장소의 설정 파일에는 주요 항목이 이미 들어 있으므로 먼저 토픽과 상태가 `Ok`인지 확인한다.

이미지는 정상인데 포인트 클라우드가 옆으로 누워 보이면 다음을 확인한다.

```bash
ros2 topic echo /camera/points --once --field header.frame_id
ros2 run tf2_ros tf2_echo base_link camera_link
ros2 run tf2_ros tf2_echo camera_link camera_optical_frame
```

이 예제의 `/camera/points` 프레임은 `camera_link`이다. 이미지·CameraInfo는 `camera_optical_frame`을 사용한다. 원본 포인트의 숫자는 그대로 두고 프레임 이름만 광학 좌표계로 바꾸면 축이 어긋난다. 자세한 내용은 [센서 좌표계 확인](08-advanced-sensors.md#sensor-frames)을 참고한다.

## 바퀴 오도메트리를 Path로 누적하는 코드

실행 예제의 `examples/ros2_ws/src/tutorial_bot_bringup/scripts/odom_to_path`는 `/odom` 위치와 자세를 `nav_msgs/msg/Path`로 누적한다. 메시지를 받을 때 실행되는 핵심 함수은 다음과 같다.

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

`minimum_translation=0.01`이면 로봇이 1 cm 이상 움직일 때만 위치와 자세를 추가하고 `max_poses=2000`이면 메모리 사용량을 제한한다. 오도메트리 `header`의 `frame_id`를 그대로 Path에 사용해야 RViz가 같은 기준 좌표계에서 그린다.

launch에서는 다음 노드를 함께 시작한다.

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

## 키보드 조종으로 궤적 만들기

`simulation.launch.py`의 DiffDrive 컨트롤러는 시간 정보가 포함된 속도 명령을 사용한다. Jazzy의 `teleop_twist_keyboard`가 `TwistStamped`를 발행하도록 설정하고 컨트롤러 토픽으로 이름을 연결한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p use_sim_time:=true \
  -p frame_id:=base_link \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

`i`, `j`, `l`, `,` 키로 직선과 회전을 조합한다. RViz의 `Wheel Odom Trajectory`가 이동 경로를 이어 그려야 한다. 새 터미널에서 오도메트리 주기와 누적된 경로도 확인한다. `k`는 정지이다. 키를 누른 뒤 움직이지 않는다면 `/clock`과 명령 메시지의 시간을 먼저 확인한다.

```bash
ros2 topic hz /odom
ros2 topic echo /wheel_odom_path --once --field poses
```

4륜 실습으로 전환하려면 2륜 launch와 키보드 조종을 모두 종료한다. 4륜 예제의 Gazebo 시스템 플러그인은 `Twist` 타입의 `/cmd_vel`을 사용한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

다른 터미널에서 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

전용 `rover.rviz`는 Fixed Frame `odom`, Odometry `/odom`, Path `/wheel_odom_path`를 이미 설정한다. `drive_mode:=ackermann`으로 바꿔도 같은 키보드 조종과 RViz 관찰 절차를 사용한다.

## 자동 검증

```bash
./scripts/check_intermediate_control_tf.sh --evidence /tmp/tutorial-intermediate-control_tf --launch
```

검증 스크립트는 여섯 좌표계의 반복 표본, 중복 부모 부재, 컨트롤러 전환, 실제 변위를 확인한다. GUI 관찰은 이 자동 검증을 대신하지 않고 보완한다.

## 문제 해결

- RViz의 `No transform` 오류가 나오면 Fixed Frame, 메시지 `frame_id`, TF 연결을 함께 확인한다.
- Message Filter가 메시지를 버리면 `/clock`이 증가하는지와 모든 노드의 `use_sim_time`을 확인한다.
- RobotModel은 보이나 바퀴가 돌지 않으면 `/joint_states`의 name과 위치를 확인한다.
- `/odom`은 변하지만 Path가 비면 `odom_to_path` 노드와 `/wheel_odom_path` 발행 노드를 확인한다.
- Path가 순간이동하면 `odom → base_link` 발행 노드가 중복되지 않았는지 확인한다.
- LaserScan이 보이지 않으면 Reliability를 Best Effort로 바꾼다.

## 정리

URDF는 링크 사이 정적 관계와 조인트 축을 정의하고, `/joint_states`와 바퀴 오도메트리가 실행 중의 동적 TF를 완성한다. TF, RobotModel, Odometry, Path를 함께 보면 로봇 구조와 실제 주행 궤적을 같은 좌표계에서 검증할 수 있다.

[이전: ros_gz_bridge 심화](05-bridge-yaml.md) · [다음: gz_ros2_control](07-gz-ros2-control.md)
