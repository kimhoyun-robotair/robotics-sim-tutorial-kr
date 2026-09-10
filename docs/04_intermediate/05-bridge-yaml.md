# ros_gz_bridge YAML 심화

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 로봇 생성

## 학습 목표

- Gazebo Transport와 ROS 2 DDS가 자동으로 연결되지 않는 이유를 설명한다.
- YAML로 여러 브리지의 토픽, 타입, 방향, QoS를 선언한다.
- `ROS_TO_GZ`, `GZ_TO_ROS`, `BIDIRECTIONAL`을 구분한다.
- CLI 축약 문법의 `[`와 `]` 방향을 올바르게 읽는다.
- 토픽 이름 재지정으로 Gazebo 모델 이름과 ROS 토픽 이름을 분리한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## 브리지 버전 확인

이 예제는 항목별 `frame_id`와 `qos_profile`을 지원하는 **ros_gz_bridge 1.0.22 이상**을 사용한다. Jazzy를 오래전에 설치했다면 패키지를 갱신한다.

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz-bridge
ros2 pkg xml ros_gz_bridge | grep '<version>'
```

Jazzy의 항목별 `frame_id` 지원은 1.0.20, YAML `qos_profile` 지원은 1.0.22에 추가되었다. 설정이 적용되지 않으면 먼저 [공식 변경 이력](https://github.com/gazebosim/ros_gz/blob/0fa70cb7c15f7500c495190020dd6292188c8e54/ros_gz_bridge/CHANGELOG.rst)과 설치 버전을 비교한다.

## 브리지 항목의 다섯 요소

브리지 한 항목은 다음 질문에 답한다.

1. ROS 토픽 이름은 무엇인가?
2. Gazebo 토픽 이름은 무엇인가?
3. 양쪽 메시지 타입은 무엇인가?
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

Gazebo 센서가 `/tutorial_bot/lidar`에 `gz.msgs.LaserScan`을 발행하면 브리지가 ROS `/scan`의 `sensor_msgs/msg/LaserScan`으로 변환한다. 이름과 타입 중 하나라도 틀리면 메시지가 전달되지 않는다.

## 방향 선택

| 데이터 | 권장 방향 | 이유 |
|---|---|---|
| 속도 명령 | `ROS_TO_GZ` | 키보드나 컨트롤러의 명령을 Gazebo 구동기로 보낸다 |
| LiDAR, CameraInfo, IMU, 오도메트리 | `GZ_TO_ROS` | Gazebo가 생성한 관찰값을 ROS에서 사용한다 |
| `/clock` | `GZ_TO_ROS` | 시뮬레이션 시간의 소유자는 Gazebo이다 |
| 양쪽에서 모두 발행해야 하는 특수 토픽 | `BIDIRECTIONAL` | 두 통신 계층의 발행 노드가 모두 필요할 때만 사용한다 |

센서처럼 Gazebo에서만 만들어지는 데이터는 `GZ_TO_ROS`로 충분하다. 한 방향을 지정하면 발행 주체가 분명해지고, 중복 브리지를 추가했을 때 잘못된 연결을 찾기도 쉽다.

## `/clock`과 센서 QoS

`/clock`은 전용 QoS 프로필을 사용한다.

```yaml
- topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS
  qos_profile: CLOCK
```

LiDAR·IMU·카메라처럼 새 표본의 최신성이 중요한 데이터에는 `SENSOR_DATA`를 사용한다. RViz가 센서 토픽을 구독할 때도 일반적으로 Best Effort를 선택해야 발행 노드와 호환된다.

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
  <figcaption>그림 1. 명령은 ROS에서 Gazebo로, 센서와 시계는 Gazebo에서 ROS로 흐른다.</figcaption>
</figure>

## 카메라와 영상 브리지

RGB-D 카메라는 여러 토픽을 만든다. 일반 메시지는 파라미터 브리지로, RGB 픽셀 데이터는 `ros_gz_image`로 연결할 수 있다.

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
  frame_id: "camera_link"
```

```bash
ros2 run ros_gz_image image_bridge \
  /tutorial_bot/camera/image \
  --ros-args \
  -r /tutorial_bot/camera/image:=/camera/image
```

RGB-D의 원본 깊이 토픽은 `/tutorial_bot/camera/depth_image`이다. 이 예제에서는 위 YAML의 `parameter_bridge`가 이를 ROS `/camera/depth/image`로 이미 변환하므로 `image_bridge`에 깊이를 중복 지정하지 않는다.

Image·CameraInfo는 `camera_optical_frame`을 사용한다. Harmonic의 원본 RGB-D 포인트 좌표는 +X 전방이므로 `/camera/points`만 `camera_link`로 표시하도록 해당 브리지 항목에 `frame_id`를 지정한다. 이 설정은 XYZ를 회전시키지 않고 실제 좌표축에 맞는 이름을 붙인다. PointCloud2를 그릴 때는 그 메시지의 `frame_id`에서 RViz Fixed Frame까지 TF가 이어져야 하며, CameraInfo는 PointCloud2 표시의 필수 입력이 아니다.

## YAML로 브리지 실행하기

앞 장의 수동 생성 실습을 실행한 상태에서 새 터미널에 브리지를 추가한다. `simulation.launch.py`에는 같은 브리지가 이미 포함되어 있으므로 별도로 중복 실행하지 않는다. 다음 두 명령 중 **하나만** 선택한다. 소스 파일을 시험할 때는 절대 경로를 전달한다.

```bash
bridge="$PWD/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

설치된 패키지를 기준으로 실행할 때는 다음 경로를 사용한다.

```bash
bridge="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-intermediate.yaml"
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$bridge"
```

## CLI 축약 문법 읽기

소수의 토픽만 빠르게 연결할 때는 양쪽 메시지 타입을 명령줄에 적을 수 있다.

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

셸이 대괄호를 해석하지 않도록 각 인자를 작은따옴표로 감싸는 습관이 안전하다. 여러 토픽과 QoS를 관리할 때는 CLI보다 YAML이 검토하기 쉽다.

## 4륜 로버의 동적 모델 토픽 이름 재지정

`rover.launch.py`는 `model_name`으로 Gazebo 토픽을 만들고 ROS 쪽 토픽은 공통 이름으로 연결한다.

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

따라서 `model_name:=warehouse_rover`를 사용해도 키보드 조종은 `/cmd_vel`, RViz는 `/odom`을 그대로 사용한다.

## 키보드 조종과 전달 확인

4륜 DiffDrive 또는 Ackermann 로버를 먼저 실행한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

다른 터미널에서 키보드 조종을 실행한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

세 번째 터미널에서 ROS와 Gazebo의 토픽과 실제 메시지를 확인한다.

```bash
ros2 topic hz /cmd_vel
ros2 topic echo /odom --once
gz topic -i -t /model/rover/cmd_vel
gz topic -i -t /model/rover/odometry
```

키보드 조종 키를 누르는 동안 ROS `/cmd_vel` 발행 빈도가 나타나고 Gazebo 명령 토픽에 구독 노드가 있으며 `/odom` 위치와 자세가 변하면 왕복 경로가 정상이다.

## 계산 예제: 큐 지연과 방향

<div class="course-worked" data-worked-example="bridge-qos" markdown="1">
30 Hz 데이터를 큐 5칸에 보관하면 가장 오래된 표본과 최신 표본 사이 시간차는 대략 \((5-1)/30=0.133\,\mathrm{s}\)이다. 이것이 통신 전체의 최대 지연을 보장하는 값은 아니다. 센서 구독에서는 작은 큐와 Best Effort를 사용해 오래된 데이터가 쌓이는 것을 줄인다. `ros2 topic info /scan -v`로 발행·구독 양쪽 QoS를 확인한다.
</div>

## 결과 확인

```bash
ros2 topic list | grep -E '^/(clock|scan|imu|camera|odom|cmd_vel)'
ros2 topic info /scan -v
ros2 topic echo /clock --once
ros2 topic echo /scan --once --field header.frame_id
```

토픽 목록만으로 합격시키지 않는다. 발행 노드 수가 1 이상인지, 타입이 예상과 같은지, QoS가 구독자와 호환되는지, 메시지가 실제로 도착하는지 함께 확인한다.

## 문제 해결

- 브리지가 생기지 않으면 양쪽 타입 문자열의 대소문자와 패키지 이름을 확인한다.
- ROS 토픽은 있으나 메시지가 없으면 `gz topic -e -t <topic>`으로 Gazebo 원본부터 확인한다.
- RViz가 LaserScan을 받지 못하면 표시 항목 Reliability를 Best Effort로 설정한다.
- `/clock`이 여러 발행 노드를 가지면 브리지를 중복 실행했는지 확인한다.
- 명령이 전달되지 않으면 `[`와 `]`을 반대로 쓰지 않았는지 확인한다.
- Gazebo Classic의 `gazebo_ros_pkgs` 예제를 섞지 않는다.

## 정리

브리지 YAML에는 Gazebo와 ROS의 토픽 이름, 타입, 전달 방향을 한곳에 적는다. 각 항목에서 이름, 타입, 방향, QoS를 함께 선언하고 실제 양쪽 통신 연결과 메시지를 확인해야 한다. 명령과 센서의 소유자를 분명히 하면 불필요한 양방향 브리지와 순환을 피할 수 있다.

[이전: 로봇 생성](04-spawn-model.md) · [다음: TF·Joint State·RViz](06-tf-rviz.md)
