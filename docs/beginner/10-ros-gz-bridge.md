# `ros_gz_bridge`로 ROS 2와 Gazebo 연결하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Fuel

## 학습 목표

- ROS 2 DDS topic과 Gazebo Transport topic의 역할을 구분합니다.
- YAML로 ROS → Gazebo와 Gazebo → ROS bridge를 설정합니다.
- `/cmd_vel`, `/odom`, `/scan`, `/imu`, Camera, `/clock`의 실제 전달을 확인합니다.

## 배경 지식

Gazebo는 내부 통신에 Gazebo Transport를 사용하고 ROS 2는 DDS를 사용합니다. 같은 이름의 topic이라도 두 통신 계층은 자동으로 연결되지 않습니다. `ros_gz_bridge`는 지정한 메시지 형식과 방향에 따라 두 계층 사이에서 메시지를 변환합니다.

이 예제에서는 ROS 2의 `/cmd_vel`을 Gazebo의 `/model/tutorial_bot/cmd_vel`로 보내고, Gazebo의 odometry·LiDAR·IMU·clock을 ROS 2 topic으로 가져옵니다. Camera는 이미지 전용 도구인 `ros_gz_image`로 ROS 2 `sensor_msgs/msg/Image`를 발행합니다.

## 예제 파일

Bridge YAML은 실제 ament package에 있습니다.

`examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`

IMU와 센서 System 설정은 기존 `tutorial_bot` Xacro와 world 원본에 누적됩니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

`examples/gazebo/worlds/first-world.sdf`

통합 headless 검증은 다음 스크립트가 담당합니다.

`scripts/check_ros_gz_bridge.sh`

## Bridge YAML 읽기

`bridge.yaml`의 한 항목은 ROS topic, Gazebo topic, 두 메시지 형식, 방향을 정의합니다.

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ
```

`ROS_TO_GZ`는 ROS 발행자를 Gazebo 구독자로 연결합니다. 반대로 LiDAR와 IMU 항목의 `GZ_TO_ROS`는 Gazebo sensor 메시지를 ROS로 보냅니다. Sensor data에는 `SENSOR_DATA`, `/clock`에는 `CLOCK` QoS profile을 지정했습니다.

## 실행

저장소 루트에서 전체 전달 경로를 검증합니다.

```bash
./scripts/check_ros_gz_bridge.sh
```

스크립트는 headless Gazebo에 `tutorial_bot`을 spawn하고, `parameter_bridge`와 `image_bridge`를 시작합니다. ROS `/cmd_vel`에 `linear.x = 0.2`를 한 번 발행한 뒤, ROS 쪽의 odometry·LiDAR·Camera·IMU·clock을 확인합니다.

정상 출력 예시는 다음과 같습니다.

```text
ROS cmd_vel to Gazebo verified: odom x=0.40..., linear.x=0.20...
Gazebo sensors to ROS verified: scan=258, image=320x240, IMU and clock received.
```

`scan` 숫자는 ROS CLI가 출력한 수신 range 항목 수입니다. LiDAR 자체의 360 raw range 설정은 [센서](08-sensors.md) 검증에서 별도로 확인합니다.

## 직접 실행하기

Gazebo가 이미 실행되고 `tutorial_bot`이 spawn된 상태라면, 다른 terminal에서 YAML bridge를 시작할 수 있습니다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:=examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml
```

Camera는 별도 terminal에서 연결합니다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image
```

그 다음 ROS 2에서 속도 명령과 sensor topic을 확인합니다.

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}'
ros2 topic echo --once /scan sensor_msgs/msg/LaserScan
ros2 topic echo --once /imu sensor_msgs/msg/Imu
```

## 결과 확인

Bridge가 실행되면 ROS 2 topic 목록에 다음이 나타납니다.

```text
/clock
/cmd_vel
/odom
/scan
/imu
/tutorial_bot/camera/image
```

`/odom`의 `pose.pose.position.x`가 양수이고 `twist.twist.linear.x`가 약 `0.2`이면, ROS 명령이 Gazebo DiffDrive와 ROS odometry까지 왕복한 것입니다.

## 자주 발생하는 문제

### ROS topic이 나타나지 않습니다

Gazebo sensor topic이 먼저 생긴 뒤 bridge를 실행했는지와 YAML의 `gz_topic_name`을 확인합니다. ROS topic 이름과 Gazebo topic 이름은 이 예제처럼 다를 수 있습니다.

### Camera topic에 이미지가 없습니다

Camera는 `ros_gz_bridge` YAML 항목이 아니라 `ros_gz_image image_bridge`가 처리합니다. `gz sim`의 렌더 엔진과 `/tutorial_bot/camera/image` topic 존재 여부도 확인합니다.

### 시간이 벽시계와 다릅니다

`/clock`은 simulation time입니다. 이후 ROS node를 만들 때는 `use_sim_time`을 사용해 이 topic을 기준으로 시간을 맞춥니다.

## 정리

ROS 2와 Gazebo는 bridge를 통해 명시적으로 연결됩니다. 다음 마지막 초급 프로젝트에서는 이 경로와 `tutorial_bot`의 모든 기능을 함께 검증합니다.
