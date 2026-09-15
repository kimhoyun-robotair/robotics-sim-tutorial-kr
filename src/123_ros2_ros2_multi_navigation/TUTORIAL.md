# 123. Multiple Robot ROS2 Navigation — 세 로봇의 이름과 목표를 분리하기

권장 학습 순서 **123** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t024`

공식 Hospital/Office GUI 장면과 Nav2 launch를 사용하는 독립 실습이다. 한 지도 안에서 Carter 세 대를 각각 조작하고, namespace가 토픽과 action 서버를 분리하는 원리를 확인한다. 공식 장면/ROS 노드는 외부 의존성이며 이 폴더에 재배포하지 않는다.

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

## Nav2와 이름 공간

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-pointcloud-to-laserscan
ros2 pkg prefix carter_navigation
ros2 pkg prefix isaac_ros_navigation_goal
```

USD Stage는 환경과 로봇을 담는 장면, prim은 장면 안의 경로로 식별되는 요소다. 같은 Nova Carter USD를 reference해 세 로봇을 만들 수 있지만 ROS 이름까지 같으면 어느 로봇의 센서/속도인지 구분하지 못한다. 각 `Nova_Carter_ROS_X` 아래 Action Graph의 `node_namespace`는 `carter1`, `carter2`, `carter3`으로 설정되어 있다. launch의 namespace도 일치해야 한다. 토픽 이름 공간과 TF 메시지 안의 `frame_id`는 다른 개념이며 이름 공간만 바꿨다고 frame 문자열이 자동으로 변경되는 것은 아니다.

## 1. Hospital과 Office 지도 만들기

1. 새 Stage에서 Content의 `Isaac Sim > Environments > Hospital`을 열어 `hospital.usd`를 드래그한다. Office는 별도 새 Stage에서 `Isaac Sim > Environments > Office > office.usd`를 사용한다. 각 환경 prim의 Translate는 `(0,0,0)`으로 맞춘다.
2. Camera를 **Top**으로 변경하고 환경 prim을 선택해 `F`로 맞춘다. `Tools > Robotics > Occupancy Map`에서 Origin `(0,0,0)`, Lower Z `0.1`, Upper Z `0.62`, Cell Size `0.05`로 설정한다.
3. 환경 prim 선택 후 **BOUND SELECTION**으로 X/Y 경계를 잡고 Z를 다시 확인한다. Origin이 물체 안이면 같은 높이의 빈 바닥으로 옮긴다. 로봇은 아직 추가하지 않는다.
4. **CALCULATE → VISUALIZE IMAGE**, Rotate Image **180 degrees**, Coordinate Type **ROS Occupancy Map Parameters File (YAML)**, **RE-GENERATE IMAGE**를 차례로 누른다.
5. 이 패키지의 `output/`에 Hospital은 `carter_hospital_navigation.yaml/.png`, Office는 `carter_office_navigation.yaml/.png`로 새 파일을 저장한다. YAML `image:`와 PNG 파일명이 같아야 한다.
6. 공식 launch의 기본 지도를 직접 생성 결과로 교체해 실험하려면 실습용 ROS 워크스페이스 `src/navigation/carter_navigation/maps/`의 같은 이름 파일을 먼저 백업하고 그 사본만 교체한다. 그 후 `colcon build --packages-select carter_navigation`과 `source install/local_setup.bash`를 수행한다. 원본 기준 실험은 제공된 지도를 그대로 사용한다.

점유 지도는 렌더링 색상이 아니라 충돌 형상과 지정 높이를 이용한다. `resolution`은 m/pixel이고 `origin`은 지도 픽셀을 세계 좌표로 옮기는 기준이다.

## 2. 세 로봇을 각각 이동시키기

1. `Window > Examples > Robotics Examples > ROS2 > Navigation > Multiple Robots > Hospital Scene`의 **Load Sample Scene**을 누른다. 공식 자산 경로는 `Isaac/Samples/ROS2/Scenario/multiple_robot_carter_hospital_navigation.usd`다.
2. **Play** 후 ROS 터미널에서 Hospital launch를 실행한다.

```bash
ros2 launch carter_navigation multiple_robot_carter_navigation_hospital.launch.py
```

3. RViz 창 세 개가 준비될 때까지 기다린다. 각 창 `Displays > Map > Topic`에서 `/carter1`, `/carter2`, `/carter3` 중 어느 로봇인지 확인한다. 창 위치만 보고 로봇 번호를 추측하지 않는다.
4. 각 로봇의 초기 위치는 워크스페이스 `carter_navigation/params/hospital/` 아래 파라미터에 들어 있다. scan과 지도가 어긋나면 **해당 창에서만 2D Pose Estimate**로 실제 로봇 위치와 방향을 지정한다.
5. `/carter1` 창의 **2D Nav Goal/Navigation2 Goal**로 가까운 빈 통로에 목표를 준다. carter1이 움직이고 나머지는 대기하는지 확인한다. 다음 carter2, carter3 순으로 각각 다른 목표를 보낸다.
6. 모두 도착한 다음, 서로 다른 통로의 목표 세 개를 연달아 보내 동시에 주행하게 한다. 같은 장소로 목표를 주어 정체를 만드는 실험은 기본 도착 확인 후 수행한다.
7. Office 실습은 Hospital launch를 Ctrl+C로 종료한 뒤 `Multiple Robots > Office Scene`을 로드한다. 자산은 `Isaac/Samples/ROS2/Scenario/multiple_robot_carter_office_navigation.usd`, 파라미터는 `params/office/`다.

```bash
ros2 launch carter_navigation multiple_robot_carter_navigation_office.launch.py
ros2 topic list -t
ros2 action list -t
ros2 topic echo /carter1/odom --once
ros2 topic echo /carter2/odom --once
ros2 topic echo /carter3/odom --once
```

세 namespace의 `navigate_to_pose` action 서버와 서로 다른 odometry를 확인한다. `/clock`은 공통 시뮬레이션 시간이고 Nav2의 `use_sim_time`이 true여야 한다.

## 3. 프로그램에서 세 목표 생성기를 시작하기

이 절은 공식 `isaac_ros_navigation_goal`을 실제로 세 번 실행하는 실습이다. 별도 구현을 먼저 공부할 필요 없이 한 launch 파일 안에서 각 로봇 설정을 읽는다.

1. 실습 워크스페이스의 `src/navigation/isaac_ros_navigation_goal/launch/isaac_ros_navigation_goal.launch.py`를 `three_goals.launch.py`로 복사한다.
2. 기존 `navigation_goal_node`의 `namespace="carter1"`을 지정하고, 같은 `Node(...)` 블록을 복제해 변수명을 `goal2`, `goal3`, namespace를 `carter2`, `carter3`으로 한다.
3. 각 블록에 `remappings=[("/initialpose", "/carter1/initialpose")]`를 추가하되 숫자를 해당 로봇에 맞춘다. **5.1 SetNavigationGoal 소스는 초기 위치 게시에 절대 토픽 `/initialpose`를 사용하므로 namespace만 지정해서는 초기 위치가 분리되지 않는다.**
4. `map_yaml_path`는 Hospital/Office에 맞는 **같은** 지도 YAML의 절대 경로, `iteration_count=1`, `goal_generator_type="RandomGoalGenerator"`, `action_server_name="navigate_to_pose"`, `obstacle_search_distance_in_meters=0.2`로 한다. `initial_pose`는 각 로봇의 해당 환경 파라미터 위치를 읽어 `[x,y,0,qx,qy,qz,qw]`로 넣는다. 초기 yaw만 있으면 `qx=qy=0`, `qz=sin(yaw/2)`, `qw=cos(yaw/2)`다.
5. 마지막 반환을 `LaunchDescription([navigation_goal_node, goal2, goal3])`로 바꾼다. 빌드 후 source한다.

```bash
cd "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws"
colcon build --packages-select isaac_ros_navigation_goal
source install/local_setup.bash
ros2 launch isaac_ros_navigation_goal three_goals.launch.py
```

6. 이미 Play와 해당 환경 Nav2 launch가 실행 중인 상태에서 호출한다. 각 로봇이 목표 한 개를 수락하고 도착하는지 확인한다. 목표 수가 소진되거나 거절되면 생성기가 종료한다.
7. GoalReader 확장은 각 로봇마다 별도 텍스트 파일을 만들고 한 줄에 `x y qx qy qz qw`를 적는다. `goal_text_file_path`를 그 파일로, `goal_generator_type="GoalReader"`로 변경한다. 좌표는 RViz에서 확인한 빈 공간을 사용한다. `iteration_count`는 파일의 목표 수 이하로 둔다.

## 4. Python으로 장면 불러오는 대안

GUI 대신 설치된 공식 standalone 예제를 사용할 때는 다음 파일의 `--help`부터 확인한다. 이 경로는 Isaac Sim 설치에 포함되어 있으며 이 패키지의 공통 코드가 아니다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/standalone_examples/api/isaacsim.ros2.bridge/carter_multiple_robot_navigation.py" --help
```

이 API 예제는 사용자 루프가 simulation timestep과 ROS 게시 주기를 제어하는 방식이다. GUI와 동시에 실행하지 않는다. 실제 제공 인자는 `--help`에 따라 선택하고 동일 Hospital/Office Nav2 launch를 사용한다.

## 확인, 한 변수 실험, 문제 해결

성공은 로봇별 action 서버 발견, 각각 다른 odometry, 의도한 로봇만 목표 수락, 세 로봇의 실제 도착으로 판단한다. 한 변수 실험은 carter2의 목표만 변경하고 나머지 경로가 재지정되지 않는지 보는 것이다.

CPU 부하가 높으면 센서와 Nav2가 맞물리지 않아 충돌/위치추정 실패가 생길 수 있다. 각 로봇 `ros_lidars` 그래프의 `publish_front_3d_lidar_scan` 노드에서 **Publish Full Scan**을 켜고 다시 관찰한다. 카메라는 기본 비활성이다. `_hawk` 그래프의 `_camera_render_product`를 켜면 부하도 늘어난다. RViz Image는 **Best Effort**로 맞춘다. 원문은 실험적 Fabric 실행도 제안하지만 기본 실습은 지원되는 일반 실행을 사용하며 사용자 설정을 초기화하지 않는다.

## 출처와 검증 범위

- [Isaac Sim 5.1 Multiple Robot ROS2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html): Hospital/Office 지도, namespace, 세 RViz 창, 자동 목표, 성능 조정.
- [5.1 ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html).
- [5.1 SetNavigationGoal 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/humble_ws/src/navigation/isaac_ros_navigation_goal/isaac_ros_navigation_goal/set_goal.py): `/initialpose` remap 보완 근거.

문서/설치 소스와 대조했으며 GPU, DDS, Nav2는 실행하지 않았다. `verification: not_run`이다.
