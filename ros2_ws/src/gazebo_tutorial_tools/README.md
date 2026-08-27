# gazebo_tutorial_tools

튜토리얼에서 반복해서 사용하는 작은 ROS 2 Python 노드를 모은 패키지다.

## `odom_to_path`

`nav_msgs/msg/Odometry`의 pose를 누적해 `nav_msgs/msg/Path`로 발행한다. 기본 입력은
`/odom`, 기본 출력은 `/wheel_odom_path`이며, 오래 실행해도 메모리가 계속 증가하지
않도록 최근 2,000개 점만 유지한다.

```bash
ros2 run gazebo_tutorial_tools odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_points:=2000
```

주요 파라미터는 다음과 같다.

| 파라미터 | 기본값 | 의미 |
|---|---:|---|
| `odom_topic` | `/odom` | 입력 Odometry 토픽 |
| `path_topic` | `/wheel_odom_path` | 출력 Path 토픽 |
| `path_frame` | 빈 문자열 | 비어 있으면 Odometry의 `header.frame_id` 사용 |
| `max_points` | `2000` | 보관할 점 수. 0 이하는 무제한 |
| `input_qos_reliability` | `best_effort` | 센서/시뮬레이터 입력과 호환되는 QoS |
| `input_qos_durability` | `volatile` | 입력 durability |
| `input_qos_depth` | `20` | 입력 큐 크기 |
| `output_qos_reliability` | `reliable` | Path 출력 reliability |
| `output_qos_durability` | `transient_local` | 늦게 켠 RViz도 최신 Path 수신 |
| `output_qos_depth` | `1` | 출력 큐 크기 |

`path_frame`은 좌표 변환 옵션이 아니다. 입력 Odometry 프레임과 다른 값을 주면 잘못된
궤적을 만들지 않기 위해 메시지를 버리고 오류를 출력한다. 시뮬레이션을 reset해 시간이
뒤로 가거나 Odometry 프레임이 바뀌면 기존 Path를 자동으로 비운다.

## `ackermann_odom`

Gazebo Classic의 `gazebo_ros_ackermann_drive`는 wheel encoder 적분값 대신 Gazebo world
pose를 Odometry로 사용한다. 이 노드는 rear left/right wheel joint position의 평균 이동
거리와 front left/right steering angle의 Ackermann 기하로부터 복원한 등가 중앙 조향각을
bicycle model로 적분해 실제 wheel
odometry `/odom`과 `odom → base_footprint` TF를 만든다.

```bash
ros2 run gazebo_tutorial_tools ackermann_odom --ros-args \
  -p use_sim_time:=true \
  -p wheel_radius:=0.16 \
  -p wheelbase:=0.56
```

| 파라미터 | 기본값 | 의미 |
|---|---:|---|
| `joint_states_topic` | `/joint_states` | wheel/steering position 입력 |
| `odom_topic` | `/odom` | wheel odometry 출력 |
| `odom_frame` | `odom` | Odometry parent frame |
| `base_frame` | `base_footprint` | Odometry child frame |
| `rear_left_joint` | `rear_left_wheel_joint` | left encoder joint |
| `rear_right_joint` | `rear_right_wheel_joint` | right encoder joint |
| `front_left_steering_joint` | `front_left_steering_joint` | left steering joint |
| `front_right_steering_joint` | `front_right_steering_joint` | right steering joint |
| `wheel_radius` | `0.16` | wheel radius [m] |
| `wheelbase` | `0.56` | front/rear axle distance [m] |
| `max_wheel_delta` | `2.0` | 한 sample에서 허용할 최대 wheel 회전 [rad] |
| `publish_tf` | `true` | `odom → base_footprint` 발행 여부 |

continuous joint position이 ±π에서 wrap되어도 최단 각도 차이로 이어서 적분한다.
simulation timestamp가 뒤로 가거나 비정상적으로 큰 wheel position jump를 감지하면
원점과 encoder baseline을 reset한다. `/odom`은 Reliable + Volatile QoS로 발행한다.
