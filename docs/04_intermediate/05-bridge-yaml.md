# ros_gz_bridge YAML 심화

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Robot Spawn

## 학습 목표

- Gazebo Transport와 ROS 2 DDS가 자동으로 연결되지 않는 이유를 설명한다.
- YAML로 여러 bridge의 topic, type, 방향, QoS를 선언한다.
- `ROS_TO_GZ`, `GZ_TO_ROS`, `BIDIRECTIONAL`을 구분한다.
- CLI 축약 문법의 `[`와 `]` 방향을 올바르게 읽는다.
- topic remapping으로 Gazebo model 이름과 ROS API를 분리한다.

## bridge 항목의 다섯 요소

bridge 한 항목은 다음 질문에 답한다.

1. ROS topic 이름은 무엇인가?
2. Gazebo topic 이름은 무엇인가?
3. 양쪽 메시지 type은 무엇인가?
4. 어느 방향으로 전달하는가?
5. 어떤 QoS를 사용하는가?

저장소의 `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`에서 LaserScan 항목은 다음과 같다.

```yaml
- ros_topic_name: "/scan"
  gz_topic_name: "/tutorial_bot/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

Gazebo sensor가 `/tutorial_bot/lidar`에 `gz.msgs.LaserScan`을 발행하면 bridge가 ROS `/scan`의 `sensor_msgs/msg/LaserScan`으로 변환한다. 이름과 type 중 하나라도 틀리면 endpoint가 연결되지 않는다.

## 방향 선택

| 데이터 | 권장 방향 | 이유 |
|---|---|---|
| velocity command | `ROS_TO_GZ` | teleop/controller 명령을 Gazebo actuator로 보낸다 |
| LiDAR, CameraInfo, IMU, odometry | `GZ_TO_ROS` | Gazebo가 생성한 관찰값을 ROS에서 사용한다 |
| `/clock` | `GZ_TO_ROS` | simulation time의 소유자는 Gazebo이다 |
| 양쪽에서 모두 발행해야 하는 특수 topic | `BIDIRECTIONAL` | 두 통신 계층의 publisher가 모두 필요할 때만 사용한다 |

무조건 `BIDIRECTIONAL`로 두면 같은 데이터가 되돌아오는 loop나 publisher 중복을 만들 수 있다. 데이터 소유자를 먼저 정하고 필요한 한 방향만 연다.

## `/clock`과 센서 QoS

`/clock`은 전용 profile을 사용한다.

```yaml
- topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS
  qos_profile: CLOCK
```

LiDAR·IMU·Camera처럼 새 표본의 최신성이 중요한 데이터에는 `SENSOR_DATA`를 사용한다. RViz가 sensor topic을 구독할 때도 일반적으로 Best Effort를 선택해야 publisher와 호환된다.

```yaml
- ros_topic_name: "/imu"
  gz_topic_name: "/tutorial_bot/imu"
  ros_type_name: "sensor_msgs/msg/Imu"
  gz_type_name: "gz.msgs.IMU"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

<figure class="course-figure" id="intermediate-bridge-qos">
  <img src="../../assets/intermediate/bridge-qos.svg" alt="ROS 2와 Gazebo Transport 사이 bridge 방향과 QoS 선택도" loading="lazy">
  <figcaption>그림 1. 명령은 ROS에서 Gazebo로, 센서와 clock은 Gazebo에서 ROS로 흐른다.</figcaption>
</figure>

## Camera와 image bridge

RGB-D Camera는 여러 topic을 만든다. 일반 메시지는 parameter bridge로, RGB pixel stream은 `ros_gz_image`로 연결할 수 있다.

```yaml
- ros_topic_name: "/camera/camera_info"
  gz_topic_name: "/tutorial_bot/camera/camera_info"
  ros_type_name: "sensor_msgs/msg/CameraInfo"
  gz_type_name: "gz.msgs.CameraInfo"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA

- ros_topic_name: "/camera/points"
  gz_topic_name: "/tutorial_bot/camera/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

```bash
ros2 run ros_gz_image image_bridge \
  /tutorial_bot/camera/image \
  --ros-args \
  -r /tutorial_bot/camera/image:=/camera/image
```

RGB-D의 원본 depth topic은 `/tutorial_bot/camera/depth_image`이다. 이 예제에서는 위 YAML의 `parameter_bridge`가 이를 ROS `/camera/depth/image`로 이미 변환하므로 `image_bridge`에 depth를 중복 지정하지 않는다.

CameraInfo의 `frame_id`와 Image의 optical frame이 TF에 연결되어야 RViz에서 PointCloud2가 올바른 방향으로 보인다.

## YAML로 bridge 실행하기

source tree 파일을 직접 시험할 때는 절대 경로를 전달한다.

```bash
bridge="$PWD/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

설치된 package를 기준으로 실행할 때는 다음 경로를 사용한다.

```bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-intermediate.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

## CLI 축약 문법 읽기

소수의 topic만 빠르게 연결할 때는 type pair를 명령줄에 적을 수 있다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock' \
  '/model/rover/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry' \
  '/model/rover/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist'
```

구분 기호는 ROS에서 바라본 데이터 방향을 나타낸다.

- `ROS_TYPE[GZ_TYPE`: Gazebo → ROS이다.
- `ROS_TYPE]GZ_TYPE`: ROS → Gazebo이다.
- `ROS_TYPE@GZ_TYPE`: 양방향이다.

shell이 대괄호를 해석하지 않도록 각 인자를 작은따옴표로 감싸는 습관이 안전하다. 여러 topic과 QoS를 관리할 때는 CLI보다 YAML이 검토하기 쉽다.

## 4륜 rover의 동적 model topic remapping

`rover.launch.py`는 `model_name`으로 Gazebo topic을 만들고 ROS 쪽 API는 공통 이름으로 remap한다.

```python
gz_cmd_vel = f"/model/{model_name}/cmd_vel"
gz_odom = f"/model/{model_name}/odometry"

bridge = Node(
    package="ros_gz_bridge",
    executable="parameter_bridge",
    arguments=[
        f"{gz_cmd_vel}@geometry_msgs/msg/Twist]gz.msgs.Twist",
        f"{gz_odom}@nav_msgs/msg/Odometry[gz.msgs.Odometry",
    ],
    remappings=[
        (gz_cmd_vel, "/cmd_vel"),
        (gz_odom, "/odom"),
    ],
)
```

따라서 `model_name:=warehouse_rover`를 사용해도 teleop은 `/cmd_vel`, RViz는 `/odom`을 그대로 사용한다.

## keyboard teleop과 전달 확인

4륜 DiffDrive 또는 Ackermann rover를 먼저 실행한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

다른 terminal에서 keyboard teleop을 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

세 번째 terminal에서 양쪽 transport의 topic과 실제 메시지를 확인한다.

```bash
ros2 topic hz /cmd_vel
ros2 topic echo /odom --once
gz topic -i -t /model/rover/cmd_vel
gz topic -i -t /model/rover/odometry
```

teleop key를 누르는 동안 ROS `/cmd_vel` rate가 나타나고 Gazebo command topic에 subscriber가 있으며 `/odom` pose가 변하면 왕복 경로가 정상이다.

## 계산 예제: queue 지연과 방향

<div class="course-worked" data-worked-example="bridge-qos">
30 Hz LaserScan에서 queue depth가 5라면 consumer가 밀렸을 때 오래된 표본의 최대 대기량은 대략 \((5-1)/30=0.133\,\mathrm{s}\)이다. 센서는 작은 depth와 Best Effort로 최신성을 택하고 `/cmd_vel`은 `ROS_TO_GZ`로만 선언해 되먹임 loop를 막는다. `ros2 topic info /scan -v`로 실제 QoS endpoint가 호환되는지 확인한다.
</div>

## 결과 확인

```bash
ros2 topic list | grep -E '^/(clock|scan|imu|camera|odom|cmd_vel)'
ros2 topic info /scan -v
ros2 topic echo /clock --once
ros2 topic echo /scan --once --field header.frame_id
```

topic 목록만으로 합격시키지 않는다. publisher 수가 1 이상인지, type이 예상과 같은지, QoS가 구독자와 호환되는지, message가 실제로 도착하는지 함께 확인한다.

## 문제 해결

- bridge가 생기지 않으면 양쪽 type 문자열의 대소문자와 package 이름을 확인한다.
- ROS topic은 있으나 message가 없으면 `gz topic -e -t <topic>`으로 Gazebo 원본부터 확인한다.
- RViz가 LaserScan을 받지 못하면 display Reliability를 Best Effort로 설정한다.
- `/clock`이 여러 publisher를 가지면 bridge를 중복 실행했는지 확인한다.
- command가 전달되지 않으면 `[`와 `]`을 반대로 쓰지 않았는지 확인한다.
- Gazebo Classic의 `gazebo_ros_pkgs` 예제를 섞지 않는다.

## 정리

YAML bridge는 Gazebo와 ROS 사이 topic 계약을 코드와 분리한다. 각 항목에서 이름, type, 방향, QoS를 함께 선언하고 실제 양쪽 endpoint와 message를 확인해야 한다. 명령과 센서의 소유자를 분명히 하면 불필요한 양방향 bridge와 loop를 피할 수 있다.

[이전: Robot Spawn](04-spawn-model.md) · [다음: TF·Joint State·RViz](06-tf-rviz.md)
