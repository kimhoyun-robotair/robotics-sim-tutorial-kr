# tutorial_bot_bringup

ROS 2 실행 파일, 브리지 YAML, RViz 설정, 바퀴 오도메트리를 경로로 누적하는 노드를 설치하는 `ament_cmake` 패키지이다.

| 파일 | 역할 |
|---|---|
| `config/bridge.yaml` | Gazebo DiffDrive를 사용하는 초급 로봇의 통신 연결 |
| `config/bridge-intermediate.yaml` | `gz_ros2_control`을 사용하는 중급 로봇의 센서·시계 연결 |
| `config/bridge-sensor-gallery.yaml` | 단안·스테레오·RGB-D·어안·2D/3D LiDAR 센서 모음 |
| `launch/simulation.launch.py` | Gazebo, ROS 제어, 센서, TF, RViz와 선택적 Nav2 실행 |
| `launch/multi_robot.launch.py` | 두 로봇의 네임스페이스·제어·센서 분리 |
| `launch/rover.launch.py` | 4륜 스키드 조향 또는 Ackermann 로버 실행 |
| `scripts/odom_to_path` | `/odom`을 `/wheel_odom_path` 경로로 누적 |
| `rviz/tutorial_bot.rviz`, `rviz/rover.rviz` | 로봇, 센서, 오도메트리 시각화 |

## 실행

[중급 실행 준비](../../../../docs/04_intermediate/index.md#intermediate-setup)를 마친 뒤 저장소 루트에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py nav2:=false
```

새 터미널에서도 같은 환경을 불러온 뒤 키보드로 조종한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -p use_sim_time:=true \
  -p frame_id:=base_link -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Nav2를 끈 상태의 RViz Fixed Frame은 `odom`, 켠 상태는 `map`이다. 단일 로봇 launch는 기본 네임스페이스와 빈 TF 접두사를 사용한다. 여러 로봇을 실행할 때는 `multi_robot.launch.py`를 사용한다.

## 센서 프레임

브리지 설정에는 ros_gz_bridge 1.0.22 이상이 필요하다. RGB-D 이미지·CameraInfo는 `camera_optical_frame`, 원본 포인트 좌표를 전달하는 `/camera/points`는 `camera_link`를 사용한다. Harmonic의 포인트 XYZ는 +X 전방이므로 광학 프레임으로 이름만 바꾸면 RViz에서 방향이 틀어진다. [센서 실습](../../../../docs/04_intermediate/08-advanced-sensors.md)에서 프레임과 화면 확인 절차를 설명한다.
