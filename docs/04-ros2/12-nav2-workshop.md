# Nav2 자율주행 워크숍

이 장에서는 Isaac Sim의 로봇·센서·정답 위치·자세·속도 데이터(odometry)를 ROS 2 Jazzy Nav2에 연결한다. 공식 Nova Carter 예제를 먼저 통과한 뒤 직접 만든 이동 로봇으로 확장한다.

## Nav2가 요구하는 연동 규칙

Nav2가 시뮬레이터 이름을 알 필요는 없다. 다음 ROS 연동 규칙만 일관되면 된다.

| 데이터 | 대표 토픽/프레임 | 생산자 |
|---|---|---|
| 시뮬레이션 시계 | `/clock` | Isaac Sim Clock 그래프 |
| 동적/정적 좌표계 | `/tf`, `/tf_static` | Isaac Sim TF 발행 노드 또는 `robot_state_publisher` |
| 바퀴/정답 위치·자세·속도 데이터(odometry) | `/odom`, `odom → base_link` | Isaac Compute Odometry 그래프 |
| 지도 | `/map`, `map → odom` | 지도 서버 + AMCL 또는 SLAM |
| 장애물 | `/scan` 또는 점군 | RTX LiDAR와 변환 노드 |
| 속도 명령 | `/cmd_vel` | Nav2 제어기 서버 |

최소 TF 트리는 다음과 같다.

```text
map → odom → base_link → base_scan
```

`map → odom`은 위치 추정이, `odom → base_link`는 odometry가, `base_link → base_scan`은 로봇 구조 설명 또는 센서 TF 발행 노드가 담당한다. 같은 좌표 변환을 두 노드가 동시에 발행하지 않게 한다.

## 1. Jazzy Nav2를 설치한다

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-pointcloud-to-laserscan \
  ros-jazzy-tf2-tools
```

공식 Isaac Sim 워크스페이스도 불러온다. [설치 장](01-install-bridge-workspace.md)에서 지정한 `IsaacSim-5.1.0` 태그를 빌드해야 아래 장면과 설정이 맞는다.

```bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 pkg prefix carter_navigation
ros2 pkg prefix isaac_ros_navigation_goal
```

## 2. 공식 Nova Carter 장면을 실행한다

1. `Window > Examples > Robotics Examples`를 연다.
2. `ROS2 > Navigation > Nova Carter` 예제를 로드한다.
3. Play를 누른다.
4. 외부 Jazzy 터미널에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 launch carter_navigation carter_navigation.launch.py
```

RViz2에서 지도가 보이고 로봇 위치·자세가 맞는지 확인한다. 필요하면 `2D Pose Estimate`로 초기 위치·자세를 지정한 뒤 `Nav2 Goal`을 준다.

실행 중 인터페이스를 점검한다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /chassis/odom --once
ros2 topic info /front_3d_lidar/lidar_points -v
ros2 topic hz /scan
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link front_3d_lidar
ros2 lifecycle nodes
```

### 공식 Nova Carter와 커스텀 로봇의 이름을 구분한다

앞의 `/odom`, `base_scan`은 일반적인 예시 이름이다. **5.1.0 Nova Carter 샘플**은 다음 이름을 사용한다.

| 용도 | 실제 이름 |
|---|---|
| 차체 odometry | `/chassis/odom` |
| 전방 3D 점군 | `/front_3d_lidar/lidar_points` |
| 3D LiDAR TF | `front_3d_lidar` |
| 전방/후방 2D 스캔 | `/front_2d_lidar/scan`, `/back_2d_lidar/scan` |
| AMCL용 변환 스캔 | `/scan` |

`carter_navigation.launch.py`는 점군 변환 노드도 띄운다. `/scan`이 없으면 먼저 원본 점군을 확인하고, 같은 이름으로 변환 노드를 중복 실행하지 않는다. `controller_server`의 odometry도 추측하지 말고 실제 파라미터와 구독 토픽으로 확인한다.

```bash
ros2 node info /controller_server
ros2 node info /pointcloud_to_laserscan
ros2 param get /velocity_smoother odom_topic
ros2 topic info /cmd_vel -v
```

위 이름은 [공식 5.1.0 launch](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/launch/carter_navigation.launch.py)와 [공식 파라미터](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/params/carter_navigation_params.yaml)에서 확인했다. Jazzy 예제의 `cmd_vel`은 `geometry_msgs/msg/Twist`를 기준으로 한다. 다른 Nav2 버전의 `TwistStamped` 설정을 가져오면 구독 노드 타입과 먼저 맞춘다.

## 3. 점유 지도를 생성한다

Isaac Sim의 `Tools > Robotics > Occupancy Map`을 연다.

1. 환경 prim을 선택한다.
2. Origin을 `(0, 0, 0)`으로 둔다.
3. Nova Carter LiDAR 높이에 맞춰 lower bound Z를 `0.1`, upper bound Z를 `0.62`로 설정한다.
4. `BOUND SELECTION`을 눌러 XY 범위를 환경에 맞춘다.
5. 지도 생성용으로 `Save As`한 복사본에서만 로봇 prim을 삭제하거나 제외한다. 주행용 원본에는 로봇을 남긴다.
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

`origin`은 이미지 왼쪽 아래 픽셀의 월드 위치·자세이다. 보기 좋게 자른 이미지에 임의 원점을 넣으면 RViz 지도와 Stage 위치가 어긋난다.

지도 서버만 따로 시험할 수 있다.

```bash
ros2 run nav2_map_server map_server --ros-args \
  -p yaml_filename:=/절대/경로/warehouse_map.yaml \
  -p use_sim_time:=true
ros2 lifecycle set /map_server configure
ros2 lifecycle set /map_server activate
ros2 topic echo /map --once --field info
```

## 4. 커스텀 로봇을 Nav2에 연결한다

### Isaac Sim 쪽 체크리스트

- 차체는 이동 가능한 articulation으로 설정한다.
- 바퀴 drive와 `/cmd_vel` 차동 구동 그래프가 정상이다.
- `/clock`, `/odom`, `odom → base_link`가 시뮬레이션 시간으로 발행된다.
- `base_link → base_scan`과 나머지 로봇 TF가 존재한다.
- 2D `LaserScan`의 각도, 거리 범위, 프레임 ID가 올바르다.
- `cmd_vel`이 끊기면 정지하는 watchdog이 있다.

### ROS 2 쪽 최소 launch

다음은 기존 Nav2 bringup을 커스텀 지도와 파라미터로 실행하는 launch 파일의 핵심이다.

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

아래 YAML은 **수정할 항목을 보여 주는 부분 예시**이다. 이 내용만 저장하면 경로 계획기와 제어기 플러그인이 빠져 Nav2가 실행되지 않는다. 공식 `carter_navigation_params.yaml` 전체를 작업 폴더에 복사하고, 실제 로봇에 해당하는 항목을 수정한다. Nova Carter를 그대로 쓰는 첫 실습에는 아래 수치를 덮어쓰지 않는다.

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
      plugins: [obstacle_layer, inflation_layer]
      obstacle_layer:
        plugin: nav2_costmap_2d::ObstacleLayer
        observation_sources: scan
        scan:
          topic: /scan
          data_type: LaserScan
          clearing: true
          marking: true
          max_obstacle_height: 1.5
      inflation_layer:
        plugin: nav2_costmap_2d::InflationLayer
        inflation_radius: 0.5
```

footprint는 화면에 보이는 메시뿐 아니라 가장 바깥쪽 충돌 형상과 안전 여유까지 포함해야 한다. 장애물 주변 확장 반경(inflation radius)과 로봇 반지름을 동시에 부정확하게 크게 잡으면 통로를 지나지 못한다.

## 5. 점군을 LaserScan으로 바꾼다

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

`min_height`와 `max_height`는 `target_frame` 기준이다. 바닥의 점가 포함되면 모든 방향이 장애물로 채워지고, 너무 좁으면 사람이나 박스를 놓친다.

## 6. TF와 시간의 일관성을 검증한다

```bash
ros2 run tf2_tools view_frames
ros2 topic echo /scan --once --field header
ros2 topic echo /chassis/odom --once --field header  # 커스텀 로봇은 실제 토픽으로 변경
ros2 param get /amcl use_sim_time
ros2 param get /controller_server use_sim_time
```

`frames.pdf`에서 순환 경로와 끊긴 하위 트리가 없어야 한다. `/scan`의 타임스탬프가 `/clock`보다 미래이거나 지나치게 오래되면 비용 지도가 `Message Filter dropping message`를 출력한다.

## 7. 다중 로봇 Nav2

공식 예제는 Hospital/Office 장면과 세 로봇 네임스페이스를 사용한다.

```bash
# Hospital
ros2 launch carter_navigation \
  multiple_robot_carter_navigation_hospital.launch.py

# Office
ros2 launch carter_navigation \
  multiple_robot_carter_navigation_office.launch.py
```

각 로봇에서 토픽, 노드, TF 프레임을 모두 분리한다.

```text
/robot1/cmd_vel, /robot1/odom, robot1/base_link
/robot2/cmd_vel, /robot2/odom, robot2/base_link
```

공유 `/map`을 쓰더라도 각 AMCL과 비용 지도 네임스페이스가 올바른 지도 토픽을 remap해야 한다. RViz2의 Fixed Frame도 각 로봇 설정에 맞춘다.

## 8. Block World Generator 실습

`Tools > Robotics > Block World Generator`에서 기존 점유 지도 PNG를 불러오고 `Generate`를 누르면 장애물로 표시된 픽셀에 충돌 형상이 있는 3D 월드를 만든다. 다음을 추가한다.

1. `Nova_Carter_ROS.usd`
2. Clock 그래프
3. 적절한 시작 위치·자세

그 뒤 공식 `carter_navigation.launch.py`를 실행하고 먼저 `2D Pose Estimate`, 다음으로 Nav2 목표를 지정한다. 생성 형상과 원본 지도의 해상도/원점이 동일해야 한다.

## 실패 원인을 빠르게 구분한다

| 증상 | 먼저 확인할 것 |
|---|---|
| 지도가 안 보인다. | 지도 서버 수명 주기(lifecycle), YAML의 이미지 절대·상대 경로 |
| 로봇이 지도 밖에 있다. | 지도 원점, 초기 위치·자세, `map → odom` |
| 전역 경로는 있지만 움직이지 않는다. | `/cmd_vel` 발행 노드, 구독 노드, 바퀴 drive |
| 지역 비용 지도(costmap)가 비어 있다. | `/scan` QoS, 프레임, 타임스탬프, 높이 필터 |
| 열린 공간에서 위치 추정이 흔들린다. | LiDAR로 구분할 수 있는 지형 특징 부족, 물체 추가, 파티클 수, 실시간 성능 |
| 영상이 RViz2에서 안 보인다. | Image 표시 항목 Reliability를 Best Effort로 설정 |

## 샘플 성공과 안전 검증의 범위

공식 파라미터에는 샘플 실행을 위한 값도 있다. 특히 5.1.0의 `collision_monitor`에서 `FootprintApproach.min_points`가 `6000000000`이다. 충돌 모니터가 떠 있다는 사실만으로 장애물 정지 기능이 검증되었다고 판단하지 않는다. 바퀴 속도 제한, 발행 중단 시 정지, 실제 접촉 여부를 별도로 측정한다. [창고 프로젝트](../07-projects/03-warehouse-navigation.md)는 지도 생성부터 실제 액션 결과를 저장하는 세 목표 주행까지 이어진다.

## 완료 기준

- [ ] 공식 Nova Carter가 목표에 도달했다.
- [ ] 직접 생성한 지도의 원점과 Stage 좌표가 일치한다.
- [ ] `map → odom → base_link → base_scan`이 한 트리이다.
- [ ] 커스텀 로봇 footprint와 LiDAR 높이 필터를 측정값으로 설정했다.
- [ ] 장애물을 추가했을 때 지역 비용 지도(costmap)와 경로가 갱신된다.

## 출처

- [Isaac Sim 5.1.0 — ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)
- [Isaac Sim 5.1.0 — Multiple Robot ROS2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html)
- [Isaac Sim 5.1.0 — Navigation with Block World Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation_block_world.html)
- [Nav2 Jazzy — Getting Started](https://docs.nav2.org/getting_started/index.html)
- [ROS 2 Jazzy — robot_state_publisher](https://docs.ros.org/en/jazzy/p/robot_state_publisher/)
