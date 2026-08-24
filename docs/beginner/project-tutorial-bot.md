# 프로젝트: ROS 2와 연결된 `tutorial_bot`

> **난이도:** 초급 프로젝트  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `ros_gz_bridge`

## 프로젝트 목표

지금까지 단계적으로 만든 하나의 `tutorial_bot`을 headless Gazebo와 ROS 2에서 함께 실행합니다. 이 프로젝트를 마치면 ROS 2 `/cmd_vel`로 로봇을 움직이고, ROS 2에서 LiDAR·Camera·IMU·odometry·simulation time을 받을 수 있습니다.

```text
tutorial_bot
├── DiffDrive
├── LiDAR
├── Camera
├── IMU
└── ros_gz_bridge
```

## 구성 요소

- 로봇 Xacro 원본: `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`
- Gazebo world와 System: `examples/gazebo/worlds/first-world.sdf`
- ROS ↔ Gazebo YAML: `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`
- 통합 검증: `scripts/check_ros_gz_bridge.sh`

Xacro가 robot description의 유일한 원본입니다. world에는 physics·sensor System을 두고, Gazebo 전용 DiffDrive·sensor 설정은 Xacro의 `<gazebo>` 확장으로 연결합니다.

## 실행

먼저 두 ROS 2 package를 빌드합니다.

```bash
cd examples/ros2_ws
colcon build --packages-select tutorial_bot_description tutorial_bot_bringup \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
cd ../..
```

그 다음 저장소 루트에서 통합 검증을 실행합니다.

```bash
./scripts/check_ros_gz_bridge.sh
```

## 완료 조건

스크립트가 아래 두 줄을 출력하면 프로젝트의 핵심 데이터 흐름이 검증된 것입니다.

```text
ROS cmd_vel to Gazebo verified: odom x=0.40..., linear.x=0.20...
Gazebo sensors to ROS verified: scan=258, image=320x240, IMU and clock received.
```

검증은 다음 순서로 동작합니다.

```text
ROS 2 /cmd_vel
      │
      ▼
ros_gz_bridge
      │
      ▼
Gazebo DiffDrive → odometry
      │
      ├── LiDAR → ROS 2 /scan
      ├── IMU → ROS 2 /imu
      ├── Camera → ROS 2 /tutorial_bot/camera/image
      └── /clock → ROS 2 /clock
```

## 확장 과제

- RViz에서 `/scan`, `/imu`, Camera image를 표시합니다.
- `use_sim_time`을 사용하는 ROS 2 node를 만듭니다.
- 중급 단계에서 ROS 2 launch, TF, `ros2_control`, Nav2를 추가합니다.

## 정리

초급 과정의 `tutorial_bot`은 하나의 Xacro 원본에서 DiffDrive·LiDAR·Camera·IMU를 제공하고, ROS 2와 실제 메시지를 주고받습니다. 다음 단계부터는 이 로봇을 ROS 2 launch와 TF 중심의 simulation stack으로 확장합니다.
