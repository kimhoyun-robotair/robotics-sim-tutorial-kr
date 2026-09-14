# 02 — ROS 2 Sensor Robot + Navigation

## Goal / Architecture / Execution Context

**Isaac Sim 5.1.0 + ROS 2 Jazzy.** `run.py`는 Standalone simulator입니다. `ros/`는 외부 ROS 2 프로세스에서 실행합니다. simulator의 Python 3.11과 시스템 ROS Python을 섞지 않고 DDS로 통신합니다.

```text
Jetbot + Camera/RTX LiDAR/IMU
  ├─ OmniGraph: Tick → clock, RGB/depth/info, LiDAR
  └─ simulator rclpy: cmd_vel → wheels, ground-truth odom/TF/IMU
                     ↓ DDS
              SLAM Toolbox → map → Nav2 → cmd_vel
```

### Sources

- NVIDIA Isaac Sim 5.1 — [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- NVIDIA Isaac Sim 5.1 — [ROS 2 Bridge in Standalone Workflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html)

## Dependencies / How to Run

Ubuntu 24.04 + ROS 2 Jazzy 환경을 기준으로 검증했습니다. 외부 ROS 환경에는 `nav2_bringup`, `nav2_regulated_pure_pursuit_controller`, `slam_toolbox`, `rviz2`가 필요합니다. 설치되지 않았다면 ROS 공식 설치 방법을 따라 준비하세요. 아래 명령은 **모두 저장소 루트에서**, 각기 다른 터미널에서 실행합니다.

터미널 A — simulator:

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
export ROS_DOMAIN_ID=51
bash src/02_ros2_sensor_navigation/run_sim.sh --headless
```

`run_sim.sh`는 자식 프로세스에서 시스템 ROS 경로를 비우고 Isaac Sim의 내부 ROS 환경을 설정합니다. GPU·camera rendering은 headless에서도 실행됩니다. 기본 60 Hz로 wall time pacing을 하고, 기본 36,000 step 후 종료합니다. Ctrl+C로 먼저 종료할 수 있습니다.

터미널 B — 센서 확인, SLAM + Nav2:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=51
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
python3 src/02_ros2_sensor_navigation/ros/check_topics.py
python3 src/02_ros2_sensor_navigation/ros/launch_navigation.py
```

터미널 C — 목표 이동:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=51
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
python3 src/02_ros2_sensor_navigation/ros/send_goal.py --x 0.8 --y 0.0
```

`send_goal.py`는 Nav2 lifecycle의 active 상태와 `/clock`을 기다린 후 action을 보내고, 결과가 `SUCCEEDED`인지 확인합니다. timeout이면 취소 요청 후 오류로 종료합니다. 실제 검증에서 기본 goal의 `Navigation SUCCEEDED`를 확인했습니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)
- ROS Navigation 공식 Jazzy 소스 — [Nav2 parameters](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/params/nav2_params.yaml)
- SLAM Toolbox 공식 Jazzy 소스 — [Lifecycle launch](https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/launch/online_async_launch.py)

## Robot Model / USD Assets / Physics Configuration

Jetbot reference는 1번과 같습니다. Stage에는 `/World/Robot/chassis` 아래에 Camera, IMU, Lidar가 있고, `/World/Wall_0`부터 `Wall_4`까지 방의 벽과 장애물을 생성합니다. 벽은 `FixedCuboid`, 로봇 질량·관성·joint drive는 원본 USD 설정을 사용합니다. physics/render dt는 1/60초, controller의 wheel radius/base는 0.03/0.1125m입니다.

RTX LiDAR는 5.1 `Example_Rotary_2D`의 USD attribute를 이 작은 방에 맞춰 near/far 0.05/10m, scan rate 10Hz, report rate 3600Hz로 설정했습니다. **프로젝트용 추천 설정**이며 실제 제품 사양이 아닙니다. Camera clipping은 0.01–20m입니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html)
- NVIDIA 5.1 공식 asset — [Example_Rotary_2D.usda](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Sensors/NVIDIA/Example_Rotary_2D.usda)
- NVIDIA Isaac Sim 5.1 — [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)

## APIs Used / Topic와 TF

| Topic | 역할 / frame |
|---|---|
| `/cmd_vel` | `Twist` 구독, 전진 ±0.2m/s / 회전 ±1rad/s 제한, 0.5 wall-second 동안 새 명령이 없으면 정지 |
| `/clock` | `IsaacReadSimulationTime` → `ROS2PublishClock` |
| `/odom` | 실제 chassis pose/velocity, pose는 `odom`, twist는 `base_link` 기준 |
| `/tf` | `odom → base_link`; SLAM이 `map → odom` 추가 |
| `/tf_static` | `base_link → laser / imu_link / camera_optical_frame` |
| `/camera/rgb`, `/camera/depth` | 320×240, `camera_optical_frame`, 4 render frame마다 publish |
| `/camera/camera_info` | 같은 camera의 intrinsics |
| `/scan_raw` → `/scan` | RTX LaserScan → beam 개수와 마지막 각도를 일치시킨 scan |
| `/imu` | `IMUSensor`, `imu_link`, 중력을 포함한 acceleration |

`odom`은 wheel integration이나 localization 추정값이 아닌 **simulator ground truth**입니다. 학습을 단순화한 선택이며 현실의 drift를 모델링하지 않습니다. IMU와 topic 검사 subscriber는 sensor-data QoS를 사용합니다. ROS sensor의 frame과 USD camera 축을 혼동하지 않도록 `camera_axes="ros"`의 pose로 TF를 작성합니다.

### Sources

- ROS 2 공식 Jazzy 소스 — [Odometry.msg](https://github.com/ros2/common_interfaces/blob/jazzy/nav_msgs/msg/Odometry.msg)
- NVIDIA Isaac Sim 5.1 — [ROS2 Transform Trees and Odometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html)
- NVIDIA Isaac Sim 5.1 — [IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
- NVIDIA Isaac Sim 5.1 — [ROS 2 QoS](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)

## RViz / 공부 순서 / Known Limitations

ROS 터미널에서 `rviz2 --ros-args -p use_sim_time:=true`를 실행하세요. Fixed Frame은 SLAM 전 `odom`, SLAM 후 `map`으로 정하고 TF, LaserScan(`/scan`), Map(`/map`), Image(`/camera/rgb`) display를 추가합니다. 센서 subscriber QoS가 맞지 않으면 Best Effort를 선택해 확인하세요.

1. [run.py](run.py)에서 sensor가 움직이는 chassis의 자식인 이유를 확인합니다.
2. [graphs.py](graphs.py)의 node, exec connection, data connection을 구분합니다.
3. [ros_interface.py](ros_interface.py)에서 ROS quaternion 순서와 frame 변환을 읽습니다.
4. [navigation.yaml](configs/navigation.yaml)의 footprint·속도·inflation을 한 항목씩 바꿉니다.

관찰된 5.1 기본 RTX profile에서는 scan의 `angle_max`가 beam 개수와 맞지 않아 SLAM Toolbox가 scan을 거부했습니다. `on_scan()`은 마지막 beam 각도를 계산해 header를 맞추며, range 측정값을 추가하거나 합성하지 않습니다. 360 beam 설정과 topic/TF 검사 및 Nav2 goal을 실제 실행했습니다. 움직임 중 RTX motion distortion, 실제 센서 noise, EKF, 복잡한 navigation 환경은 이 예제의 범위 밖입니다. Humble 조합은 별도로 검증하지 않았습니다.

실험: 카메라 publish 주기 바꾸기 → 로봇 수동 회전으로 지도 확장 → goal 변경 → QoS 하나를 일부러 바꾸고 통신 실패 계층 찾기. 수동 명령과 Nav2는 동시에 실행하지 마세요.

### Sources

- ROS 2 공식 Jazzy 소스 — [LaserScan.msg](https://github.com/ros2/common_interfaces/blob/jazzy/sensor_msgs/msg/LaserScan.msg)
- NVIDIA Isaac Sim 5.1 — [ROS 2 Cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html)
