# 122. ROS 2 Navigation — 지도를 만들고 Nova Carter를 목적지로 이동시키기

권장 학습 순서 **122** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t023`

공식 GUI 예제를 실제로 조작하는 실습이다. 이 폴더는 창고/로봇 USD와 Nav2 자체를 재배포하지 않으며, 공식 장면의 지도 생성·ROS 데이터 흐름·여러 제어 방식을 독립적으로 설명한다. 결과는 RViz의 경로와 Isaac Sim 로봇의 실제 이동이 함께 나타나는 것이다.

## 설치와 터미널 준비

이 폴더만 복사해도 실습할 수 있다. 다른 로컬 튜토리얼이나 공통 Python 모듈은 필요 없다. 외부 프로그램인 Isaac Sim 5.1.0, 공식 5.1 자산, ROS 2와 아래 공식 ROS 워크스페이스는 필요하다. 아래 명령은 **Ubuntu 22.04 + Humble**, bash 터미널 기준이다. Ubuntu 24.04에서는 `humble`을 `jazzy`로 바꾼다. Windows는 원문에서도 부분 지원이며 이 실습의 검증 대상으로 삼지 않는다.

ROS 2 desktop이 없으면 [Humble 설치](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) 또는 [Jazzy 설치](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html)를 먼저 수행한다. 다음 명령은 사용자 환경에 의존성을 설치하고 새 워크스페이스를 만드는 준비 절차이며 이 패키지가 자동 실행하지 않는다.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
source /opt/ros/humble/setup.bash
# rosdep을 처음 설치한 컴퓨터에서만 sudo rosdep init 실행
rosdep update
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$HOME/IsaacSim-ros_workspaces-5.1"
cd "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws"
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build
source install/local_setup.bash
```

태그의 확인된 커밋은 `50de00358f220d790d17050c6368cfe9a9cb9f51`이다. 이미 같은 폴더가 있다면 clone을 반복하지 말고 그 폴더의 버전과 빌드 결과를 확인한다. Jazzy에서 `topic_based_ros2_control` rosdep 키가 없으면 공식 설치 문서에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control` 후 재시도한다.

**터미널 A — Isaac Sim:** 일반 `/opt/ros` Python 환경을 source하지 않은 새 터미널에서 실행한다. Isaac Sim은 Python 3.11, Ubuntu의 ROS Python은 3.10/3.12이므로 기본 메시지를 DDS로 교환하는 이 실습은 내부 ROS 라이브러리를 사용한다. 같은 배포판을 A/B 양쪽에서 선택한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
# 새 터미널에서 한 번만 추가한다.
export LD_LIBRARY_PATH="$ISAAC_SIM_PATH/exts/isaacsim.ros2.bridge/$ROS_DISTRO/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

`Window > Extensions`에서 `isaacsim.ros2.bridge`를 검색하여 Enabled를 켠다. 5.1 자산 서버에 접근할 수 있어야 기본 장면을 불러올 수 있다. 로컬 자산팩을 쓰는 경우 Content 창에서 그 팩의 `Isaac` 폴더를 사용한다.

**터미널 B 및 이후 모든 ROS 터미널:** 매번 아래를 실행한 뒤 본문 ROS 명령을 실행한다.

```bash
source /opt/ros/humble/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

같은 컴퓨터에서는 Fast DDS 기본 설정을 쓴다. 다른 컴퓨터/컨테이너라면 위 워크스페이스의 `fastdds.xml` 절대 경로를 `FASTRTPS_DEFAULT_PROFILES_FILE`로 **A와 B 모두** 지정하고 통신 가능한 네트워크를 사용한다. 배포판/Domain ID가 다르면 노드가 발견되지 않는다.

## Nav2 준비와 핵심 개념

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-pointcloud-to-laserscan
ros2 pkg prefix carter_navigation
ros2 pkg prefix iw_hub_navigation
ros2 pkg prefix isaac_ros_navigation_goal
```

- **USD Stage**는 로봇, 환경, 센서, 그래프를 합성한 장면이다. **Prim**은 `/World/Nova_Carter_ROS` 같은 경로로 식별되는 장면 요소다. USD reference는 원본 자산을 재사용하고 현재 장면에 수정값을 저장한다.
- **Occupancy map**은 픽셀별 장애물/빈 공간/미관측 영역이다. `resolution`은 m/pixel, `origin`은 지도 좌하단의 위치·회전이다. PNG만 옮기면 이 좌표 정보가 사라지므로 YAML과 한 쌍으로 관리한다.
- **Nav2**는 지도를 불러오고 AMCL로 위치를 추정한 뒤 경로와 속도를 만든다. 시뮬레이터가 Nav2 알고리즘을 대신 실행하지 않는다.
- `/clock`은 시뮬레이션 시간, `/odom`은 이동 추정, `/tf`는 좌표계 관계다. 5.1 Carter launch는 `/front_3d_lidar/lidar_points`를 `pointcloud_to_laserscan`에 연결해 `/scan`을 만든다. 원문 개념표의 `/point_cloud` 이름과 실제 5.1 launch의 토픽명이 다르므로 `ros2 topic list -t`로 실제 이름을 확인한다.

## 1. 창고 점유 지도 생성

1. `Window > Examples > Robotics Examples > ROS2 > Navigation > Nova Carter`에서 **Load Sample Scene**을 누른다. 해당 공식 자산은 자산 루트 아래 `Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd`다.
2. Viewport의 Camera/Perspective 드롭다운을 **Top**으로 바꾼다. `Tools > Robotics > Occupancy Map`을 연다. 메뉴가 없으면 `isaacsim.asset.gen.omap` 확장을 켠다.
3. Origin을 `(0,0,0)`으로, Lower Bound의 Z를 `0.1`, Upper Bound의 Z를 `0.62`로 설정한다. 0.62 m는 Carter LiDAR 높이에 맞춘 값이다. Cell Size는 `0.05` m로 설정한다.
4. Stage의 `warehouse_with_forklifts` prim을 선택하고 **BOUND SELECTION**을 눌러 X/Y 경계를 잡는다. 선택 후 Z 값이 바뀌었다면 다시 `0.1/0.62`로 맞춘다. Origin이 벽이나 물체 안이면 빈 바닥 위치로 옮긴다.
5. 로봇이 지도에 고정 장애물로 찍히지 않게 `Nova_Carter_ROS` prim을 현재 실습 장면에서 삭제한다. **CALCULATE → VISUALIZE IMAGE**를 누른다.
6. Rotate Image = **180 degrees**, Coordinate Type = **ROS Occupancy Map Parameters File (YAML)**를 선택하고 **RE-GENERATE IMAGE**를 누른다.
7. 이 패키지에 `output/` 디렉터리를 만들고 YAML 전체를 `output/carter_warehouse_navigation.yaml`에, **Save Image**로 PNG를 `output/carter_warehouse_navigation.png`에 저장한다. YAML의 `image:`가 같은 PNG 파일명인지 확인한다. 기존 결과는 다른 이름으로 저장한다.
8. 흰 공간이 통로, 검은 영역이 선반/벽인지 Top View와 비교한다. 로봇 모양의 고정 장애물이 남으면 로봇 삭제 후 다시 계산한다. 맵 생성에 쓰이는 것은 충돌 형상이므로 보이는 물체가 지도에 없으면 Collider를 확인한다.

## 2. Nav2와 RViz 실행

1. **Nova Carter** 예제를 다시 불러와 삭제한 로봇을 복원하고 **Play**를 누른다.
2. ROS 터미널에서 아래를 실행한다. 처음에는 공식 기본 지도, 다음에는 직접 생성한 지도 순으로 진행한다. 두 launch를 동시에 켜지 않는다.

```bash
ros2 launch carter_navigation carter_navigation.launch.py use_sim_time:=true
# 첫 launch를 Ctrl+C로 끝내고, 생성한 YAML 절대 경로로 실행
ros2 launch carter_navigation carter_navigation.launch.py map:=/absolute/path/to/this-package/output/carter_warehouse_navigation.yaml use_sim_time:=true
```

3. RViz에서 지도와 LiDAR 점들이 벽에 겹치는지 확인한다. 어긋나면 **2D Pose Estimate**를 선택하고 로봇 위치에서 방향 쪽으로 드래그한다. **Navigation2 Goal** 또는 **2D Goal Pose**를 선택해 빈 통로에 목표와 방향을 지정한다.
4. 전역 경로 표시만으로 성공을 판단하지 않는다. Isaac Sim 로봇이 이동하고 도착 후 멈추며 RViz 로봇 위치가 같은 목표에 도달하는지 확인한다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /odom --once
ros2 topic hz /scan
ros2 action list -t
ros2 run tf2_ros tf2_echo map base_link
```

`ros2 topic hz`와 `tf2_echo`는 관측 후 Ctrl+C로 종료한다. `map → odom → base_link`가 이어져야 센서 관측을 지도에 놓을 수 있다.

## 3. 로봇 모델과 TF를 게시하는 두 방식

기본 장면은 Isaac Sim의 TF publisher들이 로봇 좌표계를 직접 보낸다. RViz에 메시 형상을 표시하려면 Linux/Humble에서 `nova_carter_description`이 추가로 필요하다. 공식 5.1 문서가 지정한 NVIDIA ROS release-3 저장소를 등록한 환경에서 다음을 실행한다. 저장소가 미등록이면 아래 출처의 **Installing the Nova Carter Description Package** 절에 있는 locale, NVIDIA GPG key, Ubuntu 코드명별 repository 등록을 먼저 수행한다.

```bash
# Linux/Ubuntu 22.04 + Humble의 NVIDIA release-3 repository가 없는 경우 먼저 준비
sudo apt install locales gnupg wget software-properties-common
sudo locale-gen en_US.UTF-8
sudo add-apt-repository universe
wget -qO /tmp/isaac-ros-repos.key https://isaac.download.nvidia.com/isaac-ros/repos.key
sudo apt-key add /tmp/isaac-ros-repos.key
# 아래 repository 행은 최초 등록 시 한 번만 실행
printf 'deb https://isaac.download.nvidia.com/isaac-ros/release-3 %s release-3.0\n' "$(lsb_release -cs)" | sudo tee /etc/apt/sources.list.d/isaac-ros-release3.list
sudo apt update
sudo apt install ros-humble-nova-carter-description
ros2 launch carter_navigation nova_carter_description_isaac_sim.launch.py
```

설명 패키지 없이 기본 주행은 가능하다. TF 방식을 비교하는 확장 실습에서는 기본 Nav2/description launch를 종료하고 다음 순서를 수행한다.

1. `ROS2 > Navigation > Nova Carter Joint States`를 불러온다. 자산은 `Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation_joint_states.usd`다.
2. **Play**, 위 description launch, 별도 터미널에서 `ros2 launch carter_navigation carter_navigation.launch.py` 순으로 시작한다.
3. 로봇 아래 `joint_states` Action Graph와 `odometry` Action Graph를 연다. 관절 위치는 `/joint_states`로 나가고 `robot_state_publisher`가 URDF의 고정 연결과 관절값으로 TF를 만든다. `odom → base_link`는 여전히 시뮬레이터가 보낸다.
4. Hawk 카메라의 mount→left/right 정적 변환은 기기별 보정값이라 카메라 그래프가 따로 보낸다는 점을 확인한다. 두 장면을 동시에 실행하면 같은 TF에 게시자가 중복되므로 한 장면씩 실행한다.

## 4. iw.hub와 동적 장애물

1. 앞의 launch를 종료하고 `ROS2 > Navigation > iw_hub` 예제를 불러온다. 자산은 `Isaac/Samples/ROS2/Scenario/iw_hub_warehouse_navigation.usd`다.
2. **Play** 후 `ros2 launch iw_hub_navigation iw_hub_navigation.launch.py`를 실행한다.
3. 2D Pose Estimate로 필요시 보정하고 Navigation2 Goal을 지정한다. 지도에 포함되지 않은 팔레트를 로봇이 센서로 발견하여 우회하는지 관찰한다. 창고용 Carter 지도/파라미터를 iw.hub에 그대로 쓰지 않는다.

## 5. 프로그램과 Action Graph로 목표 보내기

### 공식 goal generator

Nova Carter 창고 장면과 Nav2를 실행한 뒤 다음을 실행한다.

```bash
ros2 launch isaac_ros_navigation_goal isaac_ros_navigation_goal.launch.py
```

워크스페이스의 `src/navigation/isaac_ros_navigation_goal/launch/isaac_ros_navigation_goal.launch.py`는 실제 `SetNavigationGoal` 노드를 시작한다. 다음 중 한 변수만 바꾸고 `colcon build --packages-select isaac_ros_navigation_goal` 및 `source install/local_setup.bash` 후 다시 실행한다.

| 파라미터 | 의미와 실습 |
|---|---|
| `goal_generator_type` | `RandomGoalGenerator`는 지도 빈 공간에서 추출, `GoalReader`는 파일 순서대로 실행 |
| `iteration_count` | 먼저 `1`로 바꿔 목표 한 개만 실행 |
| `map_yaml_path` | 생성한 지도 YAML의 절대 경로 |
| `obstacle_search_distance_in_meters` | 목표 주변 장애물 제외 반경, 기본 `0.2` m |
| `action_server_name` | `navigate_to_pose`: 비동기 목표/진행/결과를 교환하는 action |
| `goal_text_file_path` | GoalReader 입력. 각 줄은 `x y qx qy qz qw`; RViz에서 확인한 빈 위치 사용 |
| `initial_pose` | `[x,y,z,qx,qy,qz,qw]`; 임의 0 대신 실제 시작 위치를 사용 |

목표 수 소진, goal 파일 끝, 서버 거절 또는 무작위 목표 생성 실패 시 종료한다. 종료 자체가 모든 목표 도착의 증거는 아니므로 RViz/로봇 위치도 본다.

### Waypoint Follower Action Graph

이 부분은 **Nav2 Python 메시지/API를 Isaac Sim 프로세스 안에서 사용**하므로 내부 최소 라이브러리만으로는 실행되지 않는다. 공식 워크스페이스에서 `./build_ros.sh -d humble -v 22.04`로 Python 3.11 ROS 빌드를 만들고, 그 빌드의 `build_ws/humble/humble_ws/install/local_setup.bash`와 `build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash`를 새 A 터미널에 source한 뒤 Isaac Sim을 시작한다. 필요한 Nav2 패키지도 같은 Python 3.11 환경에 포함되어야 한다. 외부 Nav2는 기존 B 터미널을 사용한다.

1. Nova Carter 창고 장면을 로드하고 `ROS2 > Navigation > Add Waypoint Follower`를 선택한다.
2. Graph Path = `/World/ROS_Nav2_Waypoint_Follower`, Frame ID = `map`, Navigation Mode = **Waypoint**로 하고 **Load Waypoint Follower ActionGraph**를 누른다.
3. Play와 Nav2 launch 후 `/World/Waypoints/waypoint_1`을 빈 통로의 XY 위치로 옮긴다. 그래프의 **OnImpulseEvent → Send Impulse**를 눌러 한 번 전송하고 도착을 확인한다.
4. 다음 실험은 **Patrolling**, Waypoint Count = `2`로 새 장면에서 만든다. `waypoint_1`, `waypoint_2`를 서로 다른 통로로 옮겨 Send Impulse를 누른다. AMCL 기반 위치추정에서 두 지점을 반복 방문한다.

## 관찰과 문제 해결

성공 기준은 지도/scan 정렬, TF 연결, 경로 생성, 실제 도착, `/clock` 증가다. 영상은 기본 비활성일 수 있다. 로봇의 `_hawk` 그래프에서 `_camera_render_product` 노드를 Enabled로 하고 RViz Image의 `Topic > Reliability Policy`를 **Best Effort**로 설정한다. 빈 창고에서 위치추정이 흔들리면 먼저 `/scan` 주기와 시뮬레이션 성능을 확인한다. 메시에 보이지만 충돌 형상이 없는 물체는 점유 지도에 나타나지 않는다. 로봇이 멈춰 있으면 Play, `/clock`, `/scan`, launch 에러, Domain ID 순으로 확인한다.

한 변수 실험: 다른 값은 고정하고 Cell Size만 `0.05 → 0.10` m로 바꿔 지도를 다시 만든다. 좁은 통로 표현과 픽셀 수가 어떻게 바뀌는지 비교한다.

## 출처와 검증 범위

- [Isaac Sim 5.1 ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html): 지도, Carter 세 방식, iw.hub, 자동 목표, Waypoint/Patrolling.
- [5.1 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html#configuring-options-and-enabling-internal-ros-libraries).
- [5.1 Mapping](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html).
- [공식 ROS 워크스페이스 고정 버전](https://github.com/isaac-sim/IsaacSim-ros_workspaces/tree/50de00358f220d790d17050c6368cfe9a9cb9f51).

공식 문서와 설치된 5.1 sample/launch 소스에 대조했다. GPU 시뮬레이션·DDS·Nav2 도착은 이 작성 환경에서 실행하지 않았으며 `verification: not_run`이다.
