# 122. 창고 지도를 만들고 Nova Carter를 목적지로 보내기

## 이번에 배우는 것

**창고의 점유 지도를 생성하고, LiDAR 관측과 지도 좌표를 맞춘 뒤 Nav2로 로봇을 주행시킵니다.**

로봇에게 목적지를 주려면 먼저 “어디가 비어 있는가”와 “지금 어디에 있는가”를 알아야 합니다. 점유 지도는 첫 번째 질문에, 센서와 위치추정은 두 번째 질문에 답합니다. Nav2는 이 정보를 사용하여 경로와 속도 명령을 계산합니다.

| 구성 | 담고 있는 정보 | 이번에 확인할 결과 |
|---|---|---|
| 창고 USD 장면 | 로봇·환경·충돌 형상·센서 | 실제 로봇과 장애물 배치 |
| 지도 PNG와 YAML | 장애물 픽셀과 픽셀의 좌표·크기 | 같은 장소를 표현하는 2D 지도 |
| `/scan`, `/odom`, `/tf` | 거리 관측·이동 추정·좌표계 연결 | 지도와 센서의 정렬 |
| 외부 Nav2와 RViz | 위치추정·경로 계획·목표 입력 | 경로를 따라 이동하고 정지하는 로봇 |

이 폴더에는 자동 실행기가 없습니다. Isaac Sim에 포함된 GUI 예제와 별도로 빌드한 공식 ROS 패키지를 사용합니다.

## 1. 환경을 준비하고 점유 지도 만들기

아래 명령은 **Ubuntu 24.04와 ROS 2 Jazzy**, Bash 기준입니다. Isaac Sim 5.1.0, 지원 GPU, 5.1 자산에 대한 접근이 필요합니다. ROS desktop과 `rosdep`, `colcon`을 먼저 설치·초기화하세요.

저장소 루트의 ROS용 터미널에서 공식 패키지를 준비합니다. 같은 버전을 이미 빌드했다면 기존 설치 결과를 source하면 됩니다.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
export LESSON_DIR="$PWD/src/122_ros2_ros2_navigation"
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-pointcloud-to-laserscan
colcon build
source install/local_setup.bash
ros2 pkg prefix carter_navigation
mkdir -p "$LESSON_DIR/output"
```

**새 시뮬레이터용 터미널**에서는 시스템 ROS 환경을 source하지 않고 내부 Python 3.11용 라이브러리로 실행합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Window > Examples > Robotics Examples > ROS2 > Navigation > Nova Carter**를 열고 **Load Sample Scene**을 누릅니다. 공식 자산은 `Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd`입니다.
2. 타임라인을 Stop하고 Viewport를 **Top**으로 바꿉니다. **Tools > Robotics > Occupancy Map**을 엽니다.
3. Origin `(0,0,0)`, Lower Bound Z `0.1`, Upper Bound Z `0.62`, Cell Size `0.05`를 설정합니다. 높이 단위와 셀 크기 단위는 m입니다.
4. Stage에서 `warehouse_with_forklifts`를 선택하고 **BOUND SELECTION**으로 X/Y 범위를 잡습니다. Z 경계가 달라졌다면 다시 맞추세요. Origin은 장애물 안이 아닌 빈 바닥에 있어야 합니다.
5. 현재 장면의 `Nova_Carter_ROS`를 삭제하고 **CALCULATE → VISUALIZE IMAGE**를 누릅니다. 로봇을 남겨 두면 움직일 로봇 자체가 지도 속 고정 장애물로 기록될 수 있습니다.
6. Rotate Image **180 degrees**, Coordinate Type **ROS Occupancy Map Parameters File (YAML)**를 선택하고 **RE-GENERATE IMAGE**를 누릅니다.
7. YAML과 **Save Image**의 PNG를 이 튜토리얼의 `output/carter_warehouse_navigation.yaml`, `output/carter_warehouse_navigation.png`로 저장합니다. YAML의 `image:`가 저장한 PNG 파일명을 가리키게 하세요.

### 설정에서 볼 부분

PNG는 픽셀의 색을 담지만, 그 픽셀이 몇 m이며 세계의 어느 위치인지까지 담지는 않습니다. YAML이 이 정보를 보완합니다.

```yaml
image: carter_warehouse_navigation.png
resolution: 0.05
```

`resolution: 0.05`이면 픽셀 20칸이 1 m입니다. `origin: [x, y, yaw]`는 지도 좌하단의 위치와 방향이며 실제 생성된 값을 그대로 사용하세요. PNG만 복사하거나 다른 지도의 origin을 붙이면 통로 모양이 같아도 좌표가 어긋납니다.

### 실행 결과 확인하기

PNG의 벽과 통로를 Top View와 비교해 보세요. 지도는 렌더링 색이 아니라 지정한 높이 범위의 **충돌 형상**에서 만들어집니다. 눈에 보이는 선반이 지도에 없다면 Collider와 높이 범위를 확인합니다. 저장 파일 두 개는 이 단계의 결과이며, 아직 로봇의 주행을 확인한 것은 아닙니다.

## 2. Nav2를 연결하고 목표 보내기

먼저 **Nova Carter 예제를 다시 로드**하여 삭제했던 로봇을 복원하고 Play를 누르세요. 지도 생성용으로 로봇을 지운 장면에서는 주행할 수 없습니다.

ROS용 터미널에서 다음을 실행합니다. 다른 ROS 터미널을 추가할 때도 시스템 ROS와 같은 워크스페이스 설치 결과를 source하세요.

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1.0/jazzy_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch carter_navigation carter_navigation.launch.py use_sim_time:=true
```

처음에는 제공된 지도로 실행하여 통신과 기본 주행을 확인합니다. RViz의 **2D Pose Estimate**에서 실제 시작 위치와 방향을 지정하고, LiDAR 점이 벽에 겹치는지 보세요. 이어서 **Navigation2 Goal / 2D Goal Pose**로 가까운 빈 통로에 목표와 방향을 지정합니다.

직접 만든 지도와 비교할 때는 첫 launch를 Ctrl+C로 끝내고 다음을 실행합니다. `LESSON_DIR`는 1절에서 설정한 ROS 터미널의 변수입니다.

```bash
ros2 launch carter_navigation carter_navigation.launch.py map:="$LESSON_DIR/output/carter_warehouse_navigation.yaml" use_sim_time:=true
```

### 설정에서 볼 부분

공식 5.1 `carter_navigation.launch.py`는 LiDAR 점군을 `pointcloud_to_laserscan`에 연결합니다.

```text
/front_3d_lidar/lidar_points → 높이·각도 범위로 추출 → /scan
/scan + 지도 + odometry → 위치추정 → 경로 계획 → 주행 명령
```

따라서 `/scan`이 안 보이면 먼저 원본 점군이 들어오는지 살펴볼 수 있습니다. `map → odom → base_link`의 TF 연결은 센서와 로봇을 같은 지도 위에 놓는 데 필요합니다. `/clock`은 이 계산에 사용할 시뮬레이션 시간을 공급합니다.

### 실행 결과 확인하기

별도의 ROS 터미널에서 다음을 관찰합니다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /odom --once
ros2 topic hz /scan
ros2 run tf2_ros tf2_echo map base_link
```

`hz`와 `tf2_echo`는 계속 실행되므로 각각 관찰 후 Ctrl+C로 종료하세요. RViz에서는 **지도와 scan 정렬 → 경로 생성 → 로봇 위치 갱신**을 확인합니다. Isaac Sim에서는 같은 로봇이 실제로 움직이고 목표 근처에서 정지하는지 봅니다. 경로 그림만 생겼다면 계획 단계까지만 확인한 상태입니다.

### 다른 로봇과 자동 목표로 이어 보기

기본 Carter가 도착했다면 앞의 launch를 종료하고 **ROS2 > Navigation > iw_hub**를 불러올 수 있습니다. Play 후 아래 launch로 실행하세요. 로봇에 맞는 지도·센서·제어 설정을 함께 바꾸는 비교입니다.

```bash
ros2 launch iw_hub_navigation iw_hub_navigation.launch.py
```

다시 Carter 창고 장면과 Carter Nav2를 실행한 상태에서는 별도의 ROS 터미널에서 공식 목표 생성기를 사용할 수 있습니다.

```bash
ros2 launch isaac_ros_navigation_goal isaac_ros_navigation_goal.launch.py
```

공식 `src/navigation/isaac_ros_navigation_goal/launch/isaac_ros_navigation_goal.launch.py`의 `iteration_count`는 3이고 `goal_generator_type`은 `RandomGoalGenerator`입니다. 이 생성기는 지도 빈 공간에서 목표를 고릅니다. 한 목표만 비교하려면 실습 checkout에서 `iteration_count`만 1로 바꾸고 해당 패키지를 다시 빌드·source한 뒤 실행하세요. 지도와 `initial_pose`는 실제 Carter 장면과 일치해야 합니다. 생성기가 끝났다는 사실만으로 도착을 판단하지 말고 action 결과와 로봇 위치를 확인합니다.

정해진 순서를 쓰려면 `GoalReader`와 목표 파일을 선택합니다. 파일의 각 줄은 `x y qx qy qz qw`이며, RViz에서 확인한 빈 위치를 적으세요. `iteration_count`는 파일의 목표 수 이하로 설정합니다.

### 장면 안에서 Waypoint Follower 사용하기

이 방식은 Isaac Sim 프로세스 안에서 Nav2 Python 메시지를 사용합니다. 1절의 내부 기본 라이브러리만으로는 준비가 끝나지 않습니다. 공식 ROS 설치 안내의 사용자 패키지 절차로 `./build_ros.sh -d jazzy -v 24.04`를 수행하고, 필요한 Nav2 패키지가 Python 3.11 빌드에 포함되었는지 확인하세요.

새 시뮬레이터 터미널에서는 다음처럼 두 Python 3.11 overlay만 source하고 앱을 시작합니다. 앞의 Isaac Sim 창은 먼저 닫으세요. 외부 Nav2 터미널은 시스템 ROS 환경을 유지합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
source "$ROS_WS_REPO/build_ws/jazzy/jazzy_ws/install/local_setup.bash"
source "$ROS_WS_REPO/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

`build_ros.sh`는 기존 `build_ws/jazzy`를 다시 만듭니다. 이 폴더에 사용자 변경이 있다면 먼저 보존하거나 새 실습 checkout에서 빌드하세요. Docker 실행과 Python 3.11 패키지 빌드 준비는 [공식 ROS 설치 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)를 따릅니다.

1. Carter 창고 장면에서 **ROS2 > Navigation > Add Waypoint Follower**를 선택합니다.
2. Graph Path `/World/ROS_Nav2_Waypoint_Follower`, Frame ID `map`, Navigation Mode **Waypoint**로 그래프를 만듭니다.
3. Play와 Carter Nav2 launch를 시작한 뒤 `/World/Waypoints/waypoint_1`을 빈 통로로 옮깁니다.
4. 그래프의 **OnImpulseEvent > Send Impulse**로 목표를 전송하고 실제 도착을 확인합니다.

Patrolling 모드에 waypoint 두 개를 만들면 두 위치의 반복 방문을 살펴볼 수 있습니다. RViz 클릭, 외부 목표 생성기, 장면의 waypoint는 입력 방식이 다르며 모두 현재 위치와 지도 좌표가 맞아야 사용할 수 있습니다.


### 로봇 모델과 TF 발행 방식을 비교하기

기본 Carter 장면은 Isaac Sim에서 로봇 TF를 직접 발행합니다. 원문에는 `Joint States → robot_state_publisher → TF`로 만드는 대안도 있습니다. 이 비교에 사용하는 NVIDIA `nova_carter_description` 설치 절차는 **Ubuntu 22.04/Humble용**입니다. 기본 Jazzy 주행 실습은 그대로 사용할 수 있으며, 아래 Humble 패키지와 저장소를 Ubuntu 24.04에 추가하지 않습니다.

Humble 환경의 별도 ROS 터미널에서 1절과 같은 공식 workspace의 `humble_ws`를 빌드·source한 뒤 description 패키지를 준비하세요. NVIDIA release-3 저장소가 없다면 다음과 같이 등록합니다. 이미 등록했다면 같은 항목을 중복 작성하지 마세요.

```bash
sudo apt install curl gnupg
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://isaac.download.nvidia.com/isaac-ros/repos.key \
  | gpg --dearmor | sudo tee /etc/apt/keyrings/isaac-ros.gpg >/dev/null
printf '%s\n' 'deb [signed-by=/etc/apt/keyrings/isaac-ros.gpg] https://isaac.download.nvidia.com/isaac-ros/release-3 jammy release-3.0' \
  | sudo tee /etc/apt/sources.list.d/isaac-ros-release3.list
sudo apt update
sudo apt install ros-humble-nova-carter-description
source /opt/ros/humble/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1.0/humble_ws/install/local_setup.bash"
ros2 pkg prefix nova_carter_description
ros2 launch carter_navigation nova_carter_description_isaac_sim.launch.py
```

기존 TF 방식의 로봇 메시가 RViz에 표시되는지 먼저 확인합니다. description launch는 URDF 기반 모델을 제공합니다. 그다음 기존 Nav2/description launch를 종료하고 다음을 비교하세요.

1. Humble 내부 브리지로 실행한 Isaac Sim에서 **ROS2 > Navigation > Nova Carter Joint States**를 로드합니다. 자산은 `Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation_joint_states.usd`입니다.
2. Play한 뒤 위 description launch를 실행하고, 다른 Humble ROS 터미널에서 `ros2 launch carter_navigation carter_navigation.launch.py`를 시작합니다.
3. 로봇의 `joint_states` 그래프가 관절 위치를 발행하고 `robot_state_publisher`가 URDF와 관절값으로 내부 TF를 만드는지 봅니다. `odom → base_link`는 시뮬레이터의 odometry 그래프가 계속 맡습니다.
4. `ros2 topic echo /joint_states --once`와 `ros2 run tf2_ros tf2_echo map base_link`로 메시지와 좌표 연결을 확인하고 가까운 목표로 다시 주행합니다.

Hawk 카메라의 기기별 보정 TF는 별도 카메라 그래프가 맡을 수 있습니다. 같은 변환을 두 장면에서 동시에 발행하지 않도록 한 장면씩 비교하세요. Jazzy에서 이 대안을 확장하려면 사용하는 description 패키지와 launch 의존성이 Jazzy에서도 제공되는지 먼저 확인해야 합니다.

## 3. 지도에서 주행까지의 연결 정리

```text
환경의 충돌 형상 → PNG의 장애물/빈 공간
PNG + resolution + origin → 좌표가 있는 지도
지도 + 실제 LiDAR 관측 → 현재 위치 추정
현재 위치 + 목표 → 경로와 속도 → Isaac Sim의 로봇 이동
```

한 줄이 어긋나면 다음 줄도 영향을 받습니다. 예를 들어 해상도를 잘못 읽으면 벽 사이의 거리부터 달라져, 초기 위치를 여러 번 지정해도 scan 전체를 맞출 수 없습니다.

## 4. 간단한 확인 실험

지도의 **Cell Size만 0.05에서 0.10 m**로 바꾸어 같은 경계를 다시 계산하고 별도 PNG/YAML로 저장해 보세요.

- 지도 가로·세로 픽셀 수는 각각 대략 절반이 됩니다.
- 같은 통로가 더 적은 픽셀로 표현되어 좁은 틈이나 모서리가 거칠어질 수 있습니다.
- 지도상의 실제 거리 단위는 유지됩니다. 픽셀 수 감소를 창고 크기 감소로 읽지 않습니다.

각 지도는 자기 YAML과 짝지어 Nav2에 전달하고, 같은 시작점과 목표에서 통로 표현과 계획 경로를 비교하세요.

## 실행할 때 막히면

- **Jazzy 빌드 준비에서 `topic_based_ros2_control` rosdep 오류**: 공식 설치 안내에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control`을 실행한 뒤 rosdep 명령을 다시 수행하세요.
- **Occupancy Map 메뉴가 없음**: `isaacsim.asset.gen.omap` 확장을 켜세요.
- **지도에 로봇 자국이 남음**: 로봇을 삭제한 뒤 다시 계산하고 주행 전에 원본 예제를 다시 불러오세요.
- **map은 보이는데 scan이 없음**: Play 상태와 `/front_3d_lidar/lidar_points`, 변환 노드의 로그를 확인하세요.
- **벽이 일정 비율로 어긋남**: PNG와 YAML의 짝, `resolution`, `origin`을 확인하세요. 초기 pose만 반복해서 바꾸지 않습니다.
- **경로는 생기지만 움직이지 않음**: 시계 증가, Nav2 오류, 실제 속도 토픽 연결을 확인하세요. 토픽 이름은 `ros2 topic list -t`로 확인합니다.

Ubuntu 22.04/Humble을 사용한다면 위 명령의 `jazzy`를 `humble`로 맞추세요. 시뮬레이터와 외부 ROS의 배포판을 함께 변경합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)에 대응합니다. [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html), [Mapping](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html), [고정 버전 Carter launch](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/launch/carter_navigation.launch.py)를 함께 참고하세요.

이 폴더는 장면 자산과 Nav2 소스를 재배포하지 않습니다. 공식 GUI·launch 설정에 대조한 실행 안내이며 지도 생성, DDS 수신, 실제 도착을 이 개정에서 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
