# 123. 같은 지도에서 세 로봇의 관측과 목표를 구분하기

## 이번에 배우는 것

**Hospital 장면의 Carter 세 대에 각각 목표를 보내고, namespace가 센서와 주행 요청을 어떻게 분리하는지 확인합니다.**

같은 로봇을 세 번 배치하는 것만으로 다중 로봇 시스템이 완성되지는 않습니다. 모든 로봇이 같은 odometry와 목표 이름을 쓰면 어느 로봇의 데이터인지 알 수 없습니다. 이름 앞에 붙이는 **namespace**가 이 통신 경로를 나눕니다.

| 항목 | carter1 | carter2 | carter3 |
|---|---|---|---|
| 이동 관측 | `/carter1/odom` | `/carter2/odom` | `/carter3/odom` |
| 주행 요청 | `/carter1/navigate_to_pose` | `/carter2/navigate_to_pose` | `/carter3/navigate_to_pose` |
| 초기 위치 설정 | `/carter1/initialpose` | `/carter2/initialpose` | `/carter3/initialpose` |
| 시간 기준 | 공통 `/clock` | 공통 `/clock` | 공통 `/clock` |

세 로봇은 같은 시뮬레이션 시간을 사용하지만, 위치추정과 목표는 각자 관리합니다. 이 폴더는 공식 GUI 장면과 외부 ROS launch를 사용하는 안내이며 로컬 자동 실행기는 없습니다.

## 1. Hospital 장면과 세 개의 Nav2 실행하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0**과 지원 GPU를 기준으로 진행합니다. ROS desktop, 초기화된 `rosdep`, `colcon`이 필요합니다. 처음이라면 저장소 루트의 Bash에서 공식 워크스페이스를 빌드하세요. 같은 5.1.0 빌드가 이미 있으면 설치 결과를 source합니다.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
export LESSON_DIR="$PWD/src/123_ros2_ros2_multi_navigation"
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-pointcloud-to-laserscan
colcon build
source install/local_setup.bash
ros2 pkg prefix carter_navigation
```

시뮬레이터는 시스템 ROS를 source하지 않은 **새 Bash**에서 실행합니다. 이쪽은 Isaac Sim의 Python 3.11용 내부 ROS 라이브러리를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Window > Examples > Robotics Examples > ROS2 > Navigation > Multiple Robots > Hospital Scene**에서 **Load Sample Scene**을 누릅니다.
2. 공식 자산 `Isaac/Samples/ROS2/Scenario/multiple_robot_carter_hospital_navigation.usd`가 로드되고 세 로봇이 보이면 Play합니다.
3. 앞의 ROS 터미널에서 다음 launch를 실행합니다.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch carter_navigation multiple_robot_carter_navigation_hospital.launch.py
```

### 실행 결과 확인하기

RViz 창 세 개가 열립니다. 각 창의 **Displays > Map > Topic**에서 `carter1`, `carter2`, `carter3` 중 어느 namespace인지 확인하세요. 창의 화면상 위치로 번호를 추측하지 않습니다.

각 창에서 scan과 지도 벽이 겹치는지 보고, 필요하면 해당 창의 **2D Pose Estimate**로 그 로봇의 실제 위치와 방향을 지정합니다. 로봇마다 시작 위치가 다르므로 같은 초기 pose를 세 번 복사하지 않습니다.

별도 ROS 터미널에도 아래 환경을 적용하고 관측값을 확인합니다.

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1.0/jazzy_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 action list -t
ros2 topic echo /carter1/odom --once
ros2 topic echo /carter2/odom --once
ros2 topic echo /carter3/odom --once
```

각 namespace에 `navigate_to_pose`가 나타나고 세 odometry가 각자의 위치를 표현하는지 확인하세요. 이름 목록만 있는 상태보다 실제 메시지를 받는 상태가 더 많은 것을 확인해 줍니다.

## 2. 로봇을 하나씩 움직이며 이름 연결 살펴보기

1. 아직 어느 로봇에도 목표를 주지 않은 상태에서 **carter1 RViz 창에만** 가까운 빈 통로의 목표를 지정합니다.
2. Isaac Sim에서 carter1이 움직이고 다른 두 로봇은 대기하는지 봅니다. 목표 도착 후 정지할 때까지 기다리세요.
3. 같은 방식으로 carter2와 carter3를 각각 시험합니다.
4. 세 로봇의 개별 주행을 확인한 뒤 서로 다른 통로의 목표를 차례로 지정하여 동시에 움직여 보세요.

### 설정에서 볼 부분

공식 Hospital launch는 다음 목록으로 로봇별 실행 구성을 만듭니다.

```python
robots = [{"name": "carter1"}, {"name": "carter2"}, {"name": "carter3"}]
```

각 이름에 맞는 Nav2, RViz, 점군 변환 노드를 띄웁니다. 초기 위치를 포함한 파라미터 파일도 각각 다릅니다.

```text
params/hospital/multi_robot_carter_navigation_params_1.yaml
params/hospital/multi_robot_carter_navigation_params_2.yaml
params/hospital/multi_robot_carter_navigation_params_3.yaml
```

Isaac Sim 로봇 아래 Action Graph의 namespace와 외부 launch의 namespace가 일치해야 합니다. 또 **토픽 경로와 메시지 안의 `frame_id` 문자열은 별개**입니다. 토픽 이름에 `/carter1`을 붙였다고 TF의 모든 프레임 문자열까지 자동으로 바뀌는 것은 아닙니다. 제공된 장면과 launch를 한 쌍으로 쓰는 이유입니다.

### 다른 환경과 직접 만든 지도 사용하기

Hospital launch를 Ctrl+C로 종료하고 **Multiple Robots > Office Scene**을 로드한 뒤 Play하세요.

```bash
ros2 launch carter_navigation multiple_robot_carter_navigation_office.launch.py
```

Office는 `multiple_robot_carter_office_navigation.usd` 장면과 `params/office/` 설정을 사용합니다. Hospital 지도에 Office 센서를 맞추려 하지 않습니다.

직접 만든 지도와 비교하려면 아래 과정을 따르세요. 수동 주행과 자동 목표 launch는 먼저 종료하고 생성용 새 Stage를 준비합니다.

1. Content에서 Hospital은 `Isaac/Environments/Hospital/hospital.usd`, Office는 `Isaac/Environments/Office/office.usd`를 로드합니다. 환경의 Translate는 `(0,0,0)`으로 맞추고 로봇은 넣지 않습니다.
2. Top View에서 환경 prim을 선택하고 F로 프레이밍합니다. **Tools > Robotics > Occupancy Map**에서 Origin `(0,0,0)`, Lower Z `0.1`, Upper Z `0.62`, Cell Size `0.05 m`를 정합니다.
3. **BOUND SELECTION**으로 XY 경계를 잡고 Z 범위를 다시 확인합니다. Origin이 장애물 안이라면 빈 바닥으로 옮깁니다.
4. **CALCULATE → VISUALIZE IMAGE**를 누릅니다. Rotate Image는 **180 degrees**, Coordinate Type은 **ROS Occupancy Map Parameters File (YAML)**로 정하고 **RE-GENERATE IMAGE**를 누릅니다.
5. ROS 터미널에서 `mkdir -p "$LESSON_DIR/output"`으로 출력 폴더를 만듭니다. Hospital은 `carter_hospital_navigation.yaml/.png`, Office는 `carter_office_navigation.yaml/.png`로 저장합니다. YAML의 `image`는 짝인 PNG를 가리켜야 합니다.
6. 해당 **Multiple Robots** 장면을 다시 로드하고 Play합니다. 아래처럼 생성한 지도의 절대 경로를 전달해 세 로봇의 scan과 지도 정렬을 다시 확인합니다.

```bash
ros2 launch carter_navigation multiple_robot_carter_navigation_hospital.launch.py \
  map:="$LESSON_DIR/output/carter_hospital_navigation.yaml"
```

Office는 Office launch와 Office YAML을 짝지으세요. `map` 인자로 파일을 전달하므로 원본 maps를 덮어쓰거나 패키지를 다시 빌드할 필요가 없습니다.

### 로봇별 자동 목표 생성기 구성하기

수동 목표로 세 로봇을 구분한 뒤에는 외부 목표 생성기도 같은 방식으로 세 개 구성할 수 있습니다.

1. 실습 ROS 워크스페이스의 `src/navigation/isaac_ros_navigation_goal/launch/isaac_ros_navigation_goal.launch.py`를 같은 폴더의 `three_goals.launch.py`로 복사합니다.
2. `navigation_goal_node = Node(...)` 블록을 세 개 만들고 변수명을 `goal1`, `goal2`, `goal3`으로 정합니다. 각 블록에 `namespace="carter1"`처럼 해당 이름을 지정합니다.
3. 각 블록의 `remappings`에 `[("/initialpose", "/carter1/initialpose")]`를 넣고 로봇 번호를 맞춥니다. 초기 위치 publisher가 절대 이름을 쓰기 때문에 필요합니다.
4. 각 `map_yaml_path`는 같은 Hospital 지도, `iteration_count`는 1, `action_server_name`은 상대 이름 `navigate_to_pose`로 둡니다. `initial_pose`는 각 로봇의 Hospital 파라미터와 실제 위치를 사용하여 `[x,y,z,qx,qy,qz,qw]`로 설정합니다. yaw만 있다면 `qx=qy=0`, `qz=sin(yaw/2)`, `qw=cos(yaw/2)`입니다.
5. 반환을 `LaunchDescription([goal1, goal2, goal3])`로 바꾸고 아래 명령으로 빌드·실행합니다.

```bash
cd "$HOME/IsaacSim-ros_workspaces-5.1.0/jazzy_ws"
colcon build --packages-select isaac_ros_navigation_goal
source install/local_setup.bash
ros2 launch isaac_ros_navigation_goal three_goals.launch.py
```

Hospital 장면과 세 Nav2는 이미 실행 중이어야 합니다. 목표 생성기마다 자기 action 서버에 요청하는지, 각각 실제로 도착하는지 확인하세요. 무작위 목표 선택 실패나 거절로도 생성기가 종료할 수 있습니다. 정해진 순서를 원하면 각 노드에 별도의 GoalReader 파일을 지정하며 각 줄의 형식은 `x y qx qy qz qw`입니다.


### Python에서 Hospital 또는 Office 장면 열기

GUI 예제 대신 설치된 standalone을 사용할 수도 있습니다. 실행 중인 Isaac Sim을 종료하고 **1절의 시뮬레이터용 환경을 설정한 터미널**에서 다음을 실행하세요.

```bash
"$ISAAC_SIM/python.sh" \
  "$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/carter_multiple_robot_navigation.py" \
  --environment hospital
```

설치된 5.1 파일의 지원 옵션은 `--environment hospital` 또는 `--environment office`입니다. 장면을 읽은 뒤 코드가 Play하고 앱 업데이트를 반복합니다. 해당 환경의 Nav2 launch는 ROS 터미널에서 별도로 실행하며, 창을 닫으면 standalone도 종료합니다. GUI 장면과 같은 namespace·센서·목표 확인을 반복해 보세요. 이 예제에는 임의의 `--steps` 종료 옵션을 추가하지 않습니다.

카메라 영상도 보고 싶다면 로봇의 `_hawk` 그래프에서 `_camera_render_product`를 켜고 RViz Image의 Reliability Policy를 **Best Effort**로 맞추세요. 세 로봇의 카메라를 한꺼번에 켜면 렌더링과 통신 부하가 증가하므로 기본 LiDAR 주행과 구분해 관찰합니다.

## 3. 공유할 것과 분리할 것 정리

```text
공통 장면·공통 시간·같은 지도
  ├─ carter1 센서 → carter1 위치추정 → carter1 목표/속도
  ├─ carter2 센서 → carter2 위치추정 → carter2 목표/속도
  └─ carter3 센서 → carter3 위치추정 → carter3 목표/속도
```

**namespace는 명령의 대상을 구분하며, 세 로봇의 경로를 하나의 교통 계획으로 조정하지는 않습니다.** 같은 좁은 문에 세 목표를 몰아넣으면 개별 Nav2가 모두 실행 중이어도 정체될 수 있습니다. 처음에는 분리된 통로에서 동작을 확인하세요.

원문의 자동 목표 생성기를 확장할 때도 이 원칙이 적용됩니다. 공식 `SetNavigationGoal`은 초기 위치를 절대 이름 `/initialpose`로 발행하므로, 노드 namespace만 지정해서는 분리되지 않습니다. carter1용 노드에는 `('/initialpose', '/carter1/initialpose')` remap을 추가하고 다른 로봇에도 각자의 경로를 지정해야 합니다. 수동 목표와 자동 목표를 동시에 보내면 같은 로봇의 목표가 바뀔 수 있으므로 한 방식씩 비교하세요.

## 4. 간단한 확인 실험

모두 정지한 상태에서 **carter2의 목표만** 다른 빈 위치로 바꿔 보세요. carter1과 carter3에는 새 목표를 보내지 않습니다.

- carter2의 경로와 odometry만 주행에 따라 바뀌어야 합니다.
- carter1과 carter3가 새 경로를 받는다면 RViz의 목표 토픽과 namespace 대응을 확인합니다.
- 공통 `/clock`은 계속 증가합니다. 시간 공유가 목표 공유를 의미하지 않는다는 것을 확인할 수 있습니다.

## 실행할 때 막히면

- **Jazzy 빌드 준비에서 `topic_based_ros2_control` rosdep 오류**: 공식 설치 안내에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control`을 실행한 뒤 rosdep 명령을 다시 수행하세요.
- **세 RViz 창 중 하나만 데이터가 없음**: 해당 로봇의 namespace, 파라미터 파일, 점군 변환 노드 로그를 확인하세요.
- **의도와 다른 로봇이 움직임**: 사용한 RViz의 Map과 목표 토픽을 확인하세요. 창 제목이나 위치만으로 대상을 판단하지 않습니다.
- **세 로봇의 scan이 모두 어긋남**: Hospital/Office 장면과 launch가 같은 환경인지 먼저 확인하세요.
- **부하가 커져 scan이 불안정함**: 기본 비활성 카메라는 그대로 두고 LiDAR 수신 주기를 확인하세요. 원문은 각 `ros_lidars` 그래프의 `publish_front_3d_lidar_scan`에서 Publish Full Scan 설정도 안내합니다.
- **여러 로봇이 문 앞에서 멈춤**: 통신 이름 오류인지 통로 정체인지 구분하세요. 한 대씩 통과시키는 목표로 다시 확인합니다.

Ubuntu 22.04/Humble을 사용한다면 위 명령의 `jazzy`를 `humble`로 맞추세요. 시뮬레이터와 외부 ROS의 배포판을 함께 변경합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Multiple Robot ROS2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html)에 대응합니다. [Hospital launch](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/launch/multiple_robot_carter_navigation_hospital.launch.py), [SetNavigationGoal](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/isaac_ros_navigation_goal/isaac_ros_navigation_goal/set_goal.py), [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)를 대조했습니다.

이 폴더는 외부 장면과 Nav2 패키지를 포함하지 않습니다. 개별 목표·동시 주행의 관찰 기준을 설명하며 GPU·DDS·세 로봇의 실제 도착은 이번 개정에서 실행하지 않았습니다. `tutorial.json`의 상태는 `verification: not_run`입니다.
