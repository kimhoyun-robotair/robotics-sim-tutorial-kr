# Nav2 자율주행 워크숍

이 장에서는 Isaac Sim의 로봇·센서·ground-truth odometry를 ROS 2 Jazzy Nav2에 연결한다. 공식 Nova Carter 예제를 먼저 통과한 뒤 커스텀 이동 로봇으로 치환한다.

## Nav2가 요구하는 계약

Nav2가 시뮬레이터 이름을 알 필요는 없다. 다음 ROS 계약만 일관되면 된다.

| 데이터 | 대표 토픽/frame | 생산자 |
|---|---|---|
| simulation clock | `/clock` | Isaac Sim Clock graph |
| 동적/정적 좌표계 | `/tf`, `/tf_static` | Isaac Sim TF publisher 또는 `robot_state_publisher` |
| wheel/ground-truth odometry | `/odom`, `odom → base_link` | Isaac Compute Odometry graph |
| 지도 | `/map`, `map → odom` | map server + AMCL 또는 SLAM |
| 장애물 | `/scan` 또는 point cloud | RTX LiDAR와 변환 노드 |
| 속도 명령 | `/cmd_vel` | Nav2 controller server |

최소 TF tree는 다음과 같다.

```text
map → odom → base_link → base_scan
```

`map → odom`은 localization이, `odom → base_link`는 odometry가, `base_link → base_scan`은 robot description 또는 sensor TF publisher가 담당한다. 같은 transform을 두 노드가 동시에 발행하지 않게 한다.

## 1. Jazzy Nav2를 설치하다

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-pointcloud-to-laserscan \
  ros-jazzy-tf2-tools
```

공식 Isaac Sim 워크스페이스도 source한다.

```bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 pkg prefix carter_navigation
ros2 pkg prefix isaac_ros_navigation_goal
```

## 2. 공식 Nova Carter 장면을 실행하다

1. `Window > Examples > Robotics Examples`를 연다.
2. `ROS2 > Navigation > Nova Carter` 예제를 로드한다.
3. Play를 누른다.
4. 외부 Jazzy 터미널에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 launch carter_navigation carter_navigation.launch.py
```

RViz2에서 map이 보이고 robot pose가 맞는지 확인한다. 필요하면 `2D Pose Estimate`로 초기 pose를 지정한 뒤 `Nav2 Goal`을 준다.

실행 중 인터페이스를 점검한다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /odom --once
ros2 topic hz /scan
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link base_scan
ros2 lifecycle nodes
```

## 3. 점유 지도를 생성하다

Isaac Sim의 `Tools > Robotics > Occupancy Map`을 연다.

1. 환경 prim을 선택한다.
2. Origin을 `(0, 0, 0)`으로 둔다.
3. Nova Carter LiDAR 높이에 맞춰 lower bound Z를 `0.1`, upper bound Z를 `0.62`로 설정한다.
4. `BOUND SELECTION`을 눌러 XY 범위를 환경에 맞춘다.
5. robot prim을 지도 계산 범위에서 삭제하거나 제외한다.
6. `CALCULATE`, `VISUALIZE IMAGE`를 차례로 누른다.
7. ROS Occupancy Map YAML 좌표계를 선택하고 필요하면 이미지를 180도 회전한다.
8. PNG와 YAML을 같은 디렉터리에 저장한다.

YAML의 전형적인 구조는 다음과 같다.

```yaml
image: warehouse_map.png
mode: trinary
resolution: 0.05
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

`origin`은 이미지 왼쪽 아래 pixel의 world pose이다. 보기 좋게 자른 이미지에 임의 origin을 넣으면 RViz 지도와 Stage 위치가 어긋난다.

지도 server만 따로 시험할 수 있다.

```bash
ros2 run nav2_map_server map_server --ros-args \
  -p yaml_filename:=/절대/경로/warehouse_map.yaml \
  -p use_sim_time:=true
ros2 lifecycle set /map_server configure
ros2 lifecycle set /map_server activate
ros2 topic echo /map --once --field info
```

## 4. 커스텀 로봇을 Nav2에 연결하다

### Isaac Sim 쪽 체크리스트

- base는 moveable articulation이다.
- wheel drive와 `/cmd_vel` differential graph가 정상이다.
- `/clock`, `/odom`, `odom → base_link`가 simulation time으로 발행된다.
- `base_link → base_scan`과 나머지 robot TF가 존재한다.
- 2D `LaserScan`의 angle, range, frame ID가 올바르다.
- `cmd_vel`이 끊기면 정지하는 watchdog이 있다.

### ROS 2 쪽 최소 launch

다음은 기존 Nav2 bringup을 커스텀 map과 parameter로 실행하는 launch 파일의 핵심이다.

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav2 = FindPackageShare('nav2_bringup')
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([nav2, 'launch', 'bringup_launch.py'])
            ),
            launch_arguments={
                'map': '/absolute/path/to/warehouse_map.yaml',
                'params_file': '/absolute/path/to/nav2_params.yaml',
                'use_sim_time': 'true',
                'autostart': 'true',
            }.items(),
        )
    ])
```

중요 parameter를 로봇 치수와 토픽에 맞춘다.

```yaml
amcl:
  ros__parameters:
    use_sim_time: true
    base_frame_id: base_link
    odom_frame_id: odom
    global_frame_id: map
    scan_topic: scan

controller_server:
  ros__parameters:
    use_sim_time: true
    odom_topic: /odom

local_costmap:
  local_costmap:
    ros__parameters:
      use_sim_time: true
      global_frame: odom
      robot_base_frame: base_link
      footprint: '[[0.30, 0.22], [0.30, -0.22], [-0.30, -0.22], [-0.30, 0.22]]'
      observation_sources: scan
      scan:
        topic: /scan
        data_type: LaserScan
        clearing: true
        marking: true
        max_obstacle_height: 1.5
```

footprint는 visual mesh가 아니라 가장 바깥 collision/안전 여유를 포함해야 한다. inflation radius와 robot radius를 동시에 부정확하게 크게 잡으면 통로를 지나지 못한다.

## 5. point cloud를 LaserScan으로 바꾸다

3D RTX LiDAR만 있다면 `pointcloud_to_laserscan`을 사용한다.

```bash
ros2 run pointcloud_to_laserscan pointcloud_to_laserscan_node --ros-args \
  -r cloud_in:=/point_cloud \
  -r scan:=/scan \
  -p target_frame:=base_scan \
  -p min_height:=-0.10 \
  -p max_height:=0.30 \
  -p range_min:=0.10 \
  -p range_max:=20.0 \
  -p use_sim_time:=true
```

`min_height`와 `max_height`는 `target_frame` 기준이다. 바닥 point가 포함되면 모든 방향이 장애물로 채워지고, 너무 좁으면 사람이나 박스를 놓친다.

## 6. TF와 시간의 일관성을 검증하다

```bash
ros2 run tf2_tools view_frames
ros2 topic echo /scan --once --field header
ros2 topic echo /odom --once --field header
ros2 param get /amcl use_sim_time
ros2 param get /controller_server use_sim_time
```

`frames.pdf`에서 cycle과 끊긴 sub-tree가 없어야 한다. `/scan`의 stamp가 `/clock`보다 미래이거나 지나치게 오래되면 costmap이 `Message Filter dropping message`를 출력한다.

## 7. 다중 로봇 Nav2

공식 예제는 Hospital/Office 장면과 세 robot namespace를 사용한다.

```bash
# Hospital
ros2 launch carter_navigation \
  multiple_robot_carter_navigation_hospital.launch.py

# Office
ros2 launch carter_navigation \
  multiple_robot_carter_navigation_office.launch.py
```

각 robot에서 토픽, node, TF frame을 모두 분리한다.

```text
/robot1/cmd_vel, /robot1/odom, robot1/base_link
/robot2/cmd_vel, /robot2/odom, robot2/base_link
```

공유 `/map`을 쓰더라도 각 AMCL과 costmap namespace가 올바른 map topic을 remap해야 한다. RViz2의 Fixed Frame도 각 robot 설정에 맞춘다.

## 8. Block World Generator 실습

`Tools > Robotics > Block World Generator`에서 기존 occupancy PNG를 불러오고 `Generate`를 누르면 occupied pixel에 collision geometry가 있는 3D world를 만든다. 다음을 추가한다.

1. `Nova_Carter_ROS.usd`
2. Clock graph
3. 적절한 시작 pose

그 뒤 공식 `carter_navigation.launch.py`를 실행하고 먼저 `2D Pose Estimate`, 다음으로 Nav2 goal을 지정한다. 생성 geometry와 원본 map의 resolution/origin이 동일해야 한다.

## 실패 원인을 빠르게 가르다

| 증상 | 먼저 확인할 것 |
|---|---|
| map이 안 보인다. | map server lifecycle, YAML의 image 절대/상대 경로 |
| robot이 지도 밖에 있다. | map origin, 초기 pose, `map → odom` |
| global plan은 있지만 움직이지 않는다. | `/cmd_vel` publisher, subscriber, wheel drive |
| local costmap이 비어 있다. | `/scan` QoS, frame, timestamp, height filter |
| 열린 공간에서 localization이 흔들린다. | LiDAR feature 부족, 물체 추가, particle 수, 실시간 성능 |
| 영상이 RViz2에서 안 보인다. | Image display Reliability를 Best Effort로 설정 |

## 완료 기준

- [ ] 공식 Nova Carter가 goal에 도달했다.
- [ ] 직접 생성한 map의 origin과 Stage 좌표가 일치한다.
- [ ] `map → odom → base_link → base_scan`이 한 tree이다.
- [ ] 커스텀 robot footprint와 LiDAR height filter를 측정값으로 설정했다.
- [ ] obstacle을 추가했을 때 local costmap과 경로가 갱신된다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)
- [Isaac Sim 5.1.0 — Multiple Robot ROS2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html)
- [Isaac Sim 5.1.0 — Navigation with Block World Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation_block_world.html)
- [Nav2 Jazzy — Getting Started](https://docs.nav2.org/getting_started/index.html)
- [ROS 2 Jazzy — robot_state_publisher](https://docs.ros.org/en/jazzy/p/robot_state_publisher/)
