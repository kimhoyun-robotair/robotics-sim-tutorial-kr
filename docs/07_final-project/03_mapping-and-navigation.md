# 3. 지도를 만들고 목적지까지 이동하기

이 단계는 `/scan`, `/odom`, TF가 정상인 상태에서 시작합니다.
Nav2 오류를 센서 오류와 동시에 해결하려고 하면 원인을 찾기 어렵습니다.
먼저 [센서 확인](02_sensors-and-rviz.md)을 마치세요.

## 3-1. 지도 작성용 터미널 준비

새 터미널마다 다음 두 줄로 환경을 읽습니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/robotics-sim-tutorial-kr/examples/ros2_ws/install/setup.bash
```

터미널 1에서는 기본 시뮬레이션을 실행합니다. 이미 실행 중이라면 한 번 더 실행하지 않습니다.

```bash
ros2 launch simple_rover spawn_robot.launch.py
```

터미널 2에서는 SLAM Toolbox를 실행합니다.

```bash
ros2 launch simple_rover slam.launch.py
```

SLAM은 라이다 스캔과 로봇의 이동량을 이용해 지도를 만들고 `map → odom` 변환을 제공합니다.
이때 Gazebo가 `odom → base_link`, `robot_state_publisher`가 로봇 내부 TF를 계속 담당합니다.

RViz에서 `Fixed Frame`을 `map`으로 바꾸고 `Add → Map`을 추가합니다.
Topic은 `/map`, Durability Policy는 `Transient Local`로 설정하세요.
시작 지점 주변의 벽이 지도에 그려져야 합니다. 아직 한 번도 본 적 없는 곳은 미지 영역으로 남습니다.

## 3-2. 천천히 돌아다니며 지도 채우기

터미널 3에서 실행합니다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p speed:=0.15 -p turn:=0.3 -p stamped:=false
```

`i`로 전진하고 `j`/`l`로 회전하면서 실습 공간을 천천히 둘러보세요.
처음에는 제자리에서 한 바퀴 돌고, 벽과 충분히 거리를 두며 방 안을 이동합니다.
상자 뒤편처럼 가려진 공간도 다른 위치에서 볼 수 있게 이동합니다.

잘 만들어지는 지도는 같은 벽을 여러 번 보아도 선이 크게 벌어지지 않습니다.
벽이 두 겹으로 계속 갈라지면 속도를 낮추고, `/scan`의 frame과 시뮬레이션 시간을 다시 확인하세요.
GPU가 느려 실시간보다 시뮬레이션이 늦게 진행될 때는 센서 갱신률을 무작정 올리지 않습니다.

다른 터미널에서 지도와 TF를 확인할 수 있습니다.

```bash
ros2 topic echo /map --once --qos-durability transient_local --field info
ros2 run tf2_ros tf2_echo map base_link
```

## 3-3. 지도 저장

키보드 조종에서 `k`로 멈춘 뒤 다음을 실행합니다. SLAM은 계속 실행해 둡니다.

```bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f "$HOME/maps/rover_arena" \
  --ros-args -p use_sim_time:=true -p map_subscribe_transient_local:=true
ls -l ~/maps/rover_arena.*
cat ~/maps/rover_arena.yaml
```

`rover_arena.yaml`과 `rover_arena.pgm`이 생겨야 합니다. YAML에는 이미지 이름, 해상도,
지도 원점과 점유 기준이 저장됩니다. 이 두 파일을 함께 보관하세요.
같은 이름으로 다시 저장하면 이전 지도가 바뀌므로 다른 결과를 보존하려면 파일 이름을 바꿉니다.

패키지에 들어 있는 원본 `demomap`/`warehouse`는 다른 월드에서 만든 자료입니다.
이번 `rover_arena`에 그 지도를 사용하면 장애물 위치가 맞지 않습니다. 이 단계에서 직접 만든 지도를 사용하세요.

## 3-4. 시뮬레이션을 재시작하고 저장한 지도 불러오기

터미널 3의 조종 노드를 종료하고 터미널 2의 SLAM, 터미널 1의 시뮬레이션을 차례로 `Ctrl+C`로 종료합니다.
다시 시작하여 저장된 지도로 위치를 찾는 과정을 확인합니다.

터미널 1:

```bash
ros2 launch simple_rover spawn_robot.launch.py rviz:=false
```

터미널 2:

```bash
ros2 launch simple_rover navigation.launch.py map:="$HOME/maps/rover_arena.yaml"
```

이 launch는 지도 서버, AMCL과 Nav2 서버를 함께 실행합니다.
`map`은 **존재하는 지도 YAML의 절대 경로**여야 합니다.
AMCL은 저장된 지도와 현재 스캔을 비교해 로봇 위치를 추정합니다.

터미널 3에서 내비게이션용 RViz를 엽니다.

```bash
rviz2 -d "$(ros2 pkg prefix simple_rover)/share/simple_rover/rviz/nav2.rviz" \
  --ros-args -p use_sim_time:=true
```

`navigation.launch.py map:=...`을 사용하면서 별도로 `amcl.launch.py`나 `slam.launch.py`를 실행하면
`map → odom`을 여러 노드가 발행할 수 있습니다. 저장한 지도 주행에서는 위 구성 하나만 사용합니다.

## 3-5. 초기 위치 지정

RViz의 지도에서 시작 위치를 찾습니다. 시뮬레이션은 `(0, 0)`에서 `+X` 방향을 보고 시작하지만,
지도 좌표 원점은 지도를 만든 과정에 따라 달라질 수 있습니다.
지도 저장 당시의 구조와 현재 라이다 모양을 대조하세요.

1. RViz 상단의 **2D Pose Estimate**를 선택합니다.
2. 지도에서 로봇이 있는 위치를 클릭하고 로봇 정면 방향으로 드래그합니다.
3. 화살표 방향을 확인한 뒤 마우스를 놓습니다.
4. 라이다 점이 지도 벽에 맞는지 확인합니다. 맞지 않으면 위치와 방향을 다시 지정합니다.

터미널에서 위치 추정 결과와 서버 상태를 확인합니다.

```bash
ros2 topic echo /amcl_pose --once
ros2 lifecycle get /amcl
ros2 lifecycle get /controller_server
ros2 lifecycle get /bt_navigator
ros2 run tf2_ros tf2_echo map base_link
```

lifecycle 상태는 `active`, TF는 최신 값이 나와야 합니다.
`map → base_link`를 찾지 못하는 상태에서 목표를 계속 보내지 말고 먼저 초기 위치를 확인합니다.

## 3-6. 가까운 목표 보내기

먼저 RViz의 **Nav2 Goal** 또는 **2D Goal Pose** 도구로 가까운 빈 공간을 클릭하고
도착 시 바라볼 방향으로 드래그합니다. 장애물이나 미지 영역에는 목표를 놓지 마세요.
경로가 나타나고 로봇이 이동한 뒤 정지하는지 확인합니다.

RViz 도구 구성에 Nav2 Goal이 없다면 아래 단일 목표 프로그램을 사용할 수 있습니다.
이 경우에도 초기 위치 지정과 `map → base_link` 확인은 먼저 완료해야 합니다.

```bash
ros2 run nav2_programming navigate_to_pose --ros-args \
  -p use_sim_time:=true -p goal:='[1.0, 0.0, 0.0]'
```

배열은 **지도 좌표계의 `[x(m), y(m), yaw(rad)]`**입니다.
위 숫자는 입력 형식을 보여주는 예시입니다. 자신의 지도에서 빈 공간인지 확인하고 좌표를 바꾸세요.
프로그램은 현재 AMCL 위치를 덮어쓰지 않으며 Nav2와 TF 준비를 기다린 뒤 목표를 한 번 보냅니다.

실행 중 상태를 보려면 다음을 사용합니다.

```bash
ros2 action list -t
ros2 topic info /cmd_vel -v
ros2 topic echo /cmd_vel --once
```

`/cmd_vel`은 `geometry_msgs/msg/Twist`여야 합니다. Jazzy의 Nav2 제어기, 동작 서버,
속도 평활화 노드와 충돌 감시 노드에도 `enable_stamped_cmd_vel: false`를 명시했습니다.
[Nav2 속도 명령 형식 설명](https://docs.nav2.org/configuration/packages/configuring-velocity-smoother.html)을 참고하세요.

Nav2가 주행하는 동안 키보드 조종 노드로 같은 `/cmd_vel`에 명령을 동시에 보내지 않습니다.
목표를 취소하려면 실행한 프로그램에서 `Ctrl+C`를 누르거나 RViz 내비게이션 패널의 취소 기능을 사용합니다.

## 3-7. 여러 목적지를 순서대로 방문

먼저 지도에서 두 지점 모두 장애물이 없는지 확인합니다.
다음 예시는 `(1, 0, 0)`과 `(1, 1, 1.57)` 두 경유점입니다.

```bash
ros2 run nav2_programming follow_waypoints --ros-args \
  -p use_sim_time:=true \
  -p waypoints:='[1.0, 0.0, 0.0, 1.0, 1.0, 1.57]'
```

| 프로그램 | 동작 |
|---|---|
| `navigate_to_pose` | 목표 하나로 이동 |
| `navigate_through_poses` | 여러 자세를 경유하는 내비게이션 작업 요청 |
| `follow_waypoints` | 목표들을 순서대로 방문하고 waypoint task 실행 |

```bash
ros2 run nav2_programming navigate_through_poses --ros-args \
  -p use_sim_time:=true \
  -p waypoints:='[1.0, 0.0, 0.0, 1.0, 1.0, 1.57]' \
  -p startup_timeout_sec:=90.0 -p timeout_sec:=240.0
```

준비 시간과 주행 시간은 프로그램이 무한히 기다리는 것을 막는 **벽시계 기준 초 단위**입니다.
시뮬레이션을 오래 일시정지하면 제한시간에 도달할 수 있습니다.
배열의 길이가 3의 배수가 아니거나 NaN/무한대가 들어가면 프로그램은 목표를 보내기 전에 오류를 냅니다.

## 3-8. 설정을 이해하고 바꿔보기

`simple_rover/config/nav2_params.yaml`은 설치된 Jazzy Nav2 기본 설정 위에 덮어쓰는 rover 전용 설정입니다.
설치된 Nav2 패치 버전에 따라 서버가 추가되어도 기본 설정을 유지하도록 launch에서 병합합니다.
이 YAML을 일반 `nav2_bringup` launch에 단독으로 전달하지 말고 제공된 `navigation.launch.py`를 사용하세요.

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      robot_base_frame: base_link
      footprint: "[[0.36, 0.26], [0.36, -0.26], [-0.36, -0.26], [-0.36, 0.26]]"
      footprint_padding: 0.02
```

차체 상자만 보면 길이 0.6 m, 폭 0.4 m이지만 **바퀴까지 포함한 전체 길이는 0.7 m, 폭은 0.5 m**입니다.
앞뒤 바퀴 중심이 x=±0.25 m이고 반경이 0.1 m이므로 실제 앞뒤 끝은 x=±0.35 m까지 나옵니다.
footprint는 이 외곽을 모두 감싸도록 x=±0.36 m, y=±0.26 m의 사각형으로 지정하고,
`footprint_padding: 0.02`로 추가 여유를 둡니다.

작은 원형 반경이나 차체 상자 크기만 쓰면 바퀴 또는 모서리가 벽과 부딪힐 수 있습니다.
이 설정은 `ObstacleFootprint` critic으로 실제 사각형 외곽까지 검사합니다.
차체·바퀴 크기나 관절 위치를 바꿨다면 로컬·전역 costmap의 footprint도 함께 수정하세요.

## 선택 실습: SLAM 중 Nav2, Cartographer, AMCL 단독

SLAM으로 지도를 계속 넓히면서 Nav2를 실행하려면 터미널 1에서 시뮬레이션,
터미널 2에서 `slam.launch.py`를 유지하고 별도 터미널에서 다음을 실행합니다.

```bash
ros2 launch simple_rover navigation.launch.py
```

이때 `map` 인자를 생략하면 AMCL을 추가하지 않습니다. `/map`과 `map → odom`은 실행 중인 SLAM이 제공해야 합니다.

원본의 Cartographer 실습도 유지합니다. 기본 실습은 SLAM Toolbox로 완료한 뒤,
Cartographer를 비교하고 싶을 때만 추가 패키지를 설치하세요.

```bash
sudo apt install ros-jazzy-cartographer-ros
# SLAM Toolbox와 AMCL을 종료한 상태에서 실행
ros2 launch simple_rover cartographer.launch.py
```

Cartographer도 `odom → base_link`를 중복 발행하지 않도록 `provide_odom_frame = false`,
`published_frame = "odom"`, `use_odometry = true`로 설정했습니다.
저장된 지도에서 위치 추정만 따로 확인하려면 아래 명령을 사용합니다.

```bash
ros2 launch simple_rover amcl.launch.py map:="$HOME/maps/rover_arena.yaml"
```

이 명령은 내비게이션 제어기를 실행하지 않습니다. `navigation.launch.py map:=...`와 동시에 실행하지 마세요.

다음은 [F1Tenth 차량](04_f1tenth.md)입니다.
