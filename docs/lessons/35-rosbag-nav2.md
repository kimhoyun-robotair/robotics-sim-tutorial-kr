# 35. rosbag 기록과 공식 Nova Carter Nav2 실습

[전체 목차](../../README.md) · [이전](34-command-safety.md) · [다음](36-project7-replay.md)

## 이번 단계에서 할 일

먼저 작은 장면의 clock·odometry·TF를 rosbag으로 기록한다. 이어서 NVIDIA의 Nova Carter 창고 장면을 사용해 Jazzy Nav2를 실행한다. 두 실습은 별도로 실행한다. 직육면체의 기구학 실험이 실제 바퀴 로봇의 센서·위치 추정·경로 계획을 대체하지 않으므로, 공식 로봇 장면으로 단계를 넓힌다.

## 1. 작은 기록부터 만든다

33단계의 `07_ros_scene.py`를 실행한 상태에서 새 터미널에 Jazzy 환경을 적용한다. 이전과 같은 Domain ID 61을 사용한다.

```bash
cd "$TUTORIAL_ROOT"
mkdir -p artifacts
ros2 bag record --use-sim-time -o artifacts/project6-bag \
  /clock /tutorial/odom /tf
```

기록기는 `/clock`을 받아야 시뮬레이션 시간으로 기록을 시작한다. 별도 터미널에서 `ros_goal.py --distance 0.6`을 실행하고, 목표 도달 후 3초 정도 더 기록한다. **기록기 터미널에서 Ctrl+C**를 눌러 마무리한다. 마지막 저장이 끝날 때까지 기다린 뒤 확인한다.

```bash
ros2 bag info artifacts/project6-bag
```

세 토픽의 message count가 모두 0보다 커야 한다. 이 기록에는 속도 명령을 넣지 않았다. 재생은 상태와 TF를 관찰하는 용도이다. 동일한 출력 폴더가 이미 있다면 기존 결과를 삭제하지 말고 `project6-bag-02`처럼 새 이름으로 기록한다. Jazzy의 rosbag CLI 옵션은 설치된 버전에서 `ros2 bag record --help`와 `ros2 bag play --help`로도 확인할 수 있다. [ROS 공식 rosbag2](https://github.com/ros2/rosbag2)

## 2. 공식 ROS workspace를 별도 폴더에 준비한다

Isaac Sim Python 예제와 기록기를 종료한다. 시스템 Jazzy가 설치된 Ubuntu 24.04의 새 터미널에서 실행한다. 이미 rosdep 초기화를 마친 시스템이라면 `sudo rosdep init`은 다시 실행할 필요가 없다.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install git python3-colcon-common-extensions python3-rosdep python3-yaml \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-pointcloud-to-laserscan ros-jazzy-rqt-image-view
sudo rosdep init
rosdep update

git clone --branch IsaacSim-6.0.1 --recurse-submodules \
  https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$HOME/isaac_ros601_ws"
cd "$HOME/isaac_ros601_ws/jazzy_ws"
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --symlink-install
source install/local_setup.bash
ros2 pkg prefix carter_navigation
git -C "$HOME/isaac_ros601_ws" rev-parse HEAD
```

`rosdep init`에 이미 초기화되었다는 메시지가 나오면 다음 명령부터 계속한다. 의존성 설치나 빌드 자체가 실패한 경우에는 실패를 해결한 뒤 이어간다. `IsaacSim-6.0.1`은 공식 workspace의 태그이며, 튜토리얼 저장소의 브랜치와는 별개이다. 움직이는 `main` 대신 이 태그를 사용한다. [공식 태그](https://github.com/isaac-sim/IsaacSim-ros_workspaces/releases/tag/IsaacSim-6.0.1), [ROS 설치 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html)

이 프로젝트는 제공되는 Jazzy `carter_navigation` 패키지를 사용한다. 6.0.1 공식 문서의 **Nova Carter Description Package 설치 절**은 Linux Humble 한정 설명이 포함되어 있으므로 거기의 `ros-humble-*` 설치 명령을 Ubuntu 24.04/Jazzy 터미널에 복사하지 않는다. 여기서는 별도 robot description 설치가 필요 없는 기본 **Nova Carter** 예제 장면을 사용한다.

## 3. 낮은 속도의 실습용 parameter 파일을 만든다

원본 package를 수정하지 않고 설정 파일을 `artifacts`에 복사한다. 아래 명령은 Jazzy의 공식 package 경로를 찾고, 속도와 정지 판정값만 실습에 맞춘다.

```bash
cd "$TUTORIAL_ROOT"
python3 - <<'PY'
from pathlib import Path
import yaml
from ament_index_python.packages import get_package_share_directory

source = Path(get_package_share_directory("carter_navigation")) / "params/carter_navigation_params.yaml"
config = yaml.safe_load(source.read_text())
controller = config["controller_server"]["ros__parameters"]
controller["enable_stamped_cmd_vel"] = False
follow = controller["FollowPath"]
follow.update(max_vel_x=0.15, max_speed_xy=0.15, max_vel_theta=0.5,
              acc_lim_x=0.3, decel_lim_x=-0.3, acc_lim_theta=0.6,
              decel_lim_theta=-0.6, trans_stopped_velocity=0.02)
smoother = config["velocity_smoother"]["ros__parameters"]
smoother.update(max_velocity=[0.15, 0.0, 0.5], min_velocity=[-0.15, 0.0, -0.5],
                max_accel=[0.3, 0.0, 0.6], max_decel=[-0.3, 0.0, -0.6],
                velocity_timeout=0.5, enable_stamped_cmd_vel=False)
behavior = config["behavior_server"]["ros__parameters"]
behavior.update(max_rotational_vel=0.5, min_rotational_vel=0.1,
                rotational_acc_lim=0.6, enable_stamped_cmd_vel=False)
config["collision_monitor"]["ros__parameters"]["enable_stamped_cmd_vel"] = False
target = Path("artifacts/carter-low-speed.yaml")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(yaml.safe_dump(config, sort_keys=False))
print(target.resolve())
PY
```

Nav2 안의 속도 제한과 34단계의 최종 명령 guard를 함께 사용한다. 파라미터의 실제 경로는 [6.0.1 태그의 Carter 설정](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/IsaacSim-6.0.1/jazzy_ws/src/navigation/carter_navigation/params/carter_navigation_params.yaml)에서 확인할 수 있다. 원본 샘플의 collision monitor 설정을 자체 안전 인증으로 해석하지 않는다. 이 실습은 낮은 속도에서 넓은 빈 공간의 짧은 목표부터 시험한다.

## 4. GUI에서 공식 Nova Carter 장면을 연다

Jazzy와 위 workspace를 source한 터미널 A에서 Isaac Sim을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/isaac_ros601_ws/jazzy_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
"$ISAAC_SIM_PATH/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Window > Examples > Robotics Examples**를 연다.
2. 왼쪽 목록에서 **ROS2 > Navigation > Nova Carter**를 선택한다.
3. **Load Sample Scene**을 누르고 창고와 로봇 자산 로딩이 끝날 때까지 기다린다. 외부 자산 서버에 접근할 수 없으면 이 단계는 진행할 수 없으므로 빈 장면을 정상 결과로 기록하지 않는다.
4. **Stop** 상태에서 로봇 아래의 differential drive Action Graph를 연다. `ROS2 Subscribe Twist` 노드를 찾아 `topicName`을 `/tutorial/nav2_cmd_vel_safe`로 변경한다. Namespace가 자동으로 앞에 붙지 않도록 실제 구독 이름을 나중에 확인한다.
5. 이 실습용 장면을 `artifacts/carter-low-speed.usd`로 **Save As**한다.
6. **Play**한 뒤 아직 명령 없이 로봇이 바닥에 안정적으로 서 있는지 확인한다.

센서가 로딩되지 않거나 로봇이 넘어지는 상태에서 Nav2를 시작하지 않는다. 원본 자산이 안정적이어도 GPU 메모리 부족, 누락된 자산, 잘못 저장한 물리 설정까지 자동으로 해결되는 것은 아니다. 공식 장면의 카메라 일부는 성능 때문에 기본 비활성화되어 있으므로 처음부터 모든 영상을 켜지 않는다. [공식 Nova Carter Nav2 실습](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_navigation.html)

## 5. 토픽을 확인하고 Nav2를 실행한다

새 터미널 B도 Jazzy와 workspace, Domain ID를 동일하게 설정한다. 다음 토픽은 6.0.1 태그의 기본 Carter 설정 기준이다.

| 항목 | 토픽·frame |
|---|---|
| 로봇 odometry | `/chassis/odom` |
| 전방 3D 점군 | `/front_3d_lidar/lidar_points` |
| 전방·후방 2D scan | `/front_2d_lidar/scan`, `/back_2d_lidar/scan` |
| launch에서 3D→2D 변환한 scan | `/scan` |
| 기본 좌표계 | `map`, `odom`, `base_link` |
| Nav2 최종 명령 | `/cmd_vel` |
| guard를 거친 실습 명령 | `/tutorial/nav2_cmd_vel_safe` |

```bash
ros2 topic list -t
ros2 topic echo /chassis/odom --once
timeout 5s ros2 run tf2_ros tf2_echo odom base_link
ros2 topic info /front_3d_lidar/lidar_points --verbose
```

정상 수신을 확인한 뒤 실행한다.

```bash
ros2 launch carter_navigation carter_navigation.launch.py \
  use_sim_time:=True params_file:="$TUTORIAL_ROOT/artifacts/carter-low-speed.yaml"
```

이 launch는 map 서버, Nav2, RViz뿐 아니라 `/front_3d_lidar/lidar_points`를 `/scan`으로 바꾸는 `pointcloud_to_laserscan`도 실행한다. 기본 map은 package의 `maps/carter_warehouse_navigation.yaml`이다. [공식 launch 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/IsaacSim-6.0.1/jazzy_ws/src/navigation/carter_navigation/launch/carter_navigation.launch.py)

터미널 C에서 명령의 자료형을 먼저 확인하고 guard를 시작한다.

```bash
ros2 topic type /cmd_vel
python3 scripts/ros_drive_guard.py --input /cmd_vel \
  --output /tutorial/nav2_cmd_vel_safe --timeout 0.5 \
  --linear-limit 0.15 --angular-limit 0.5
```

`/cmd_vel`은 `geometry_msgs/msg/Twist`여야 한다. `TwistStamped`이면 guard를 실행해도 연결되지 않으므로 종료하고 실제 Nav2 노드들의 `enable_stamped_cmd_vel` 적용과 사용 중인 parameter 파일을 확인한다. 시뮬레이터의 `/tutorial/nav2_cmd_vel_safe` 구독과 guard publisher가 각각 하나인지 `ros2 topic info ... --verbose`로 확인한다.

## 6. 가까운 목표 하나를 보낸다

RViz에서 지도와 LiDAR가 겹치는지 확인한다. 필요하면 **2D Pose Estimate**로 로봇의 실제 시작 위치·방향을 맞춘다. 기본 설정의 초기 pose는 map 기준 x=-6, y=-1, yaw≈π이지만 수정한 장면에 그대로 적용하면 안 된다.

**Navigation2 Goal**로 로봇에서 약 1 m 떨어진 넓은 자유 공간을 선택하고 방향을 드래그한다. 메시지 수신과 로봇의 움직임을 보면서 다음도 확인한다.

```bash
ros2 lifecycle get /controller_server
ros2 action list -t
ros2 topic echo /tutorial/nav2_cmd_vel_safe --once
```

controller가 `active`이고 목표가 도달 상태로 끝나며, 정지 후 odometry 속도가 거의 0으로 돌아오면 첫 Nav2 실습을 완료한 것이다. guard나 Nav2 프로세스가 오류로 종료하면 GUI에서 즉시 Pause한다. 공식 로봇 장면의 수신 그래프에 33단계의 내장 watchdog이 들어 있다고 가정하지 않는다.

## 진단과 과제

map이 없으면 `carter_navigation` 경로와 map 파일을, map은 있지만 위치가 안 맞으면 초기 pose·TF·scan을 확인한다. 경로는 있으나 움직이지 않으면 lifecycle, Twist 자료형, 구독 토픽, guard를 확인한다. 목표 근처에서 계속 회전하면 위치·방향 오차와 controller의 정지 판정값을 확인한다.

과제로 같은 가까운 목표를 세 번 실행하고 도달 여부, odometry, guarded command, RTF를 기록한다. 이번 workspace 태그·GPU·드라이버·센서 설정도 함께 남긴다. 원격 문서 확인과 코드의 정적 검사는 GPU에서 이 실습을 수행한 결과를 대신하지 않는다.
