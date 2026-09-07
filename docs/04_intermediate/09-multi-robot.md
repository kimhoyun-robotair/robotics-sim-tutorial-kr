# 다중 로봇 네임스페이스와 TF

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 센서 심화

## 학습 목표

- 두 엔티티의 Gazebo 이름과 ROS 네임스페이스를 분리한다.
- Xacro 인자로 모델 이름, 토픽, TF 접두사를 전달한다.
- 컨트롤러 관리자, 센서 토픽, TF 좌표계를 로봇별로 격리한다.
- 한 로봇의 속도 명령이 다른 로봇을 움직이지 않는지 검증한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## 격리해야 하는 범위

`/robot1`, `/robot2` 네임스페이스만 추가해서는 충분하지 않다. 다음 항목이 모두 고유해야 한다.

| 범위 | robot1 | robot2 | 공유 여부 |
|---|---|---|---|
| Gazebo 엔티티 | `robot1` | `robot2` | 분리 |
| ROS 네임스페이스 | `/robot1` | `/robot2` | 분리 |
| TF 접두사 | `robot1/` | `robot2/` | 분리 |
| 컨트롤러 관리자 | `/robot1/controller_manager` | `/robot2/controller_manager` | 분리 |
| 속도 명령 | `/robot1/diff_drive_controller/cmd_vel` | `/robot2/diff_drive_controller/cmd_vel` | 분리 |
| 오도메트리 | `/robot1/odom` | `/robot2/odom` | 분리 |
| 시뮬레이션 시계 | `/clock` | `/clock` | 하나만 공유 |

## 로봇 설정을 데이터로 표현하기

실제 launch 파일은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/multi_robot.launch.py`이다. 엔티티별 값을 변경할 수 없는 데이터 클래스로 묶는다.

```python
@dataclass(frozen=True, slots=True)
class _RobotSpec:
    entity_name: str
    namespace: str
    tf_prefix: str
    y: str

first = _RobotSpec("robot1", "/robot1", "robot1/", "1.0")
second = _RobotSpec("robot2", "/robot2", "robot2/", "-1.0")
```

이름과 네임스페이스가 같으면 생성 전에 실패시킨다.

```python
if first.entity_name == second.entity_name:
    raise _LaunchContractError("Entity name collision")
if first.namespace == second.namespace:
    raise _LaunchContractError("ROS namespace collision")
```

## Xacro 인자와 TF 접두사

같은 Xacro를 두 번 실행하되 로봇별 값을 전달한다.

```python
robot_description = ParameterValue(
    Command([
        "xacro ", str(xacro_path),
        " control_backend:=gz_ros2_control",
        " controller_parameters_file:=", str(controller_config),
        " model_name:=", spec.entity_name,
        " ros_namespace:=", spec.namespace,
        " tf_prefix:=", spec.tf_prefix,
        " lidar_topic:=", f"{spec.namespace}/lidar",
        " camera_topic:=", f"{spec.namespace}/camera",
        " imu_topic:=", f"{spec.namespace}/imu",
    ]),
    value_type=str,
)
```

`robot_state_publisher`에도 같은 네임스페이스와 `frame_prefix`를 전달한다.

```python
state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    namespace=spec.namespace,
    parameters=[{
        "robot_description": robot_description,
        "frame_prefix": spec.tf_prefix,
        "use_sim_time": True,
    }],
)
```

URDF 링크 이름 자체는 `base_link`, `lidar_link`로 유지하고 실행 중 발행하는 TF가 `robot1/base_link`, `robot1/lidar_link`가 된다. 센서의 `gz_frame_id`도 같은 접두사를 사용해야 RViz가 센서 데이터를 TF에 맞춰 배치할 수 있다.

## 컨트롤러 관리자 네임스페이스

컨트롤러를 불러오는 spawner가 어느 로봇의 관리자를 사용할지 명시한다.

```python
manager = f"{spec.namespace}/controller_manager"
spawner_args = [
    "--controller-manager", manager,
    "--controller-manager-timeout", "60",
    "--switch-timeout", "30",
    "--param-file", str(controller_config),
]

diff_drive_spawner = Node(
    package="controller_manager",
    executable="spawner",
    namespace=spec.namespace,
    arguments=["diff_drive_controller", *spawner_args],
)
```

실제 `examples/ros2_ws/src/tutorial_bot_control/config/multi_robot_controllers.yaml`도 전체 경로를 명시한 컨트롤러 관리자 키를 사용한다.

```yaml
/robot1/controller_manager:
  ros__parameters:
    update_rate: 100
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

/robot1/diff_drive_controller:
  ros__parameters:
    left_wheel_names: [left_wheel_joint]
    right_wheel_names: [right_wheel_joint]
    tf_frame_prefix_enable: false
    base_frame_id: robot1/base_link
    odom_frame_id: robot1/odom
    enable_odom_tf: true
```

robot2 블록도 네임스페이스와 좌표계 접두사만 `robot2`로 바꾸고 바퀴 치수는 같게 둔다.

Jazzy DiffDrive는 기본적으로 네임스페이스를 TF 프레임 앞에 자동으로 붙인다. 여기서는 `robot1/base_link`처럼 전체 이름을 직접 적었으므로 `tf_frame_prefix_enable: false`로 자동 접두사를 끈다. 그렇지 않으면 `robot1/robot1/base_link`가 되어 센서 TF와 끊어진다. [Jazzy DiffDrive 파라미터 설명](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)을 참고한다.

## 브리지 YAML 분리

센서 브리지 역시 ROS와 Gazebo 이름을 로봇별로 선언한다.

```yaml
- ros_topic_name: "/robot1/scan"
  gz_topic_name: "/robot1/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA

- ros_topic_name: "/robot2/scan"
  gz_topic_name: "/robot2/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
  qos_profile: SENSOR_DATA
```

`/clock` 블록은 한 번만 둔다. 로봇별 브리지 프로세스가 각각 `/clock`을 만들면 발행 노드가 중복될 수 있다.

<figure class="course-figure" id="intermediate-namespace-isolation">
  <img src="../../assets/intermediate/namespace-isolation.svg" alt="robot1과 robot2의 entity topic controller TF frame 격리도" loading="lazy">
  <figcaption>그림 1. 두 로봇은 시계만 공유하고 엔티티, 토픽, 컨트롤러, TF 좌표계를 분리한다.</figcaption>
</figure>

## 실행

두 로봇을 GUI가 없는 월드에 띄운다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup multi_robot.launch.py
```

다른 터미널에서 실행 목록을 확인한다.

```bash
gz model --list
ros2 node list | grep -E '^/robot[12]/'
ros2 control list_controllers --controller-manager /robot1/controller_manager
ros2 control list_controllers --controller-manager /robot2/controller_manager
ros2 topic echo /robot1/scan --once --field header.frame_id
ros2 topic echo /robot2/scan --once --field header.frame_id
```

좌표계 ID는 각각 `robot1/lidar_link`, `robot2/lidar_link`여야 한다.

## robot1만 키보드 조종으로 움직이기

Jazzy DiffDrive 컨트롤러는 시간 정보가 포함된 속도 명령을 받는다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p use_sim_time:=true \
  -p frame_id:=robot1/base_link \
  -r cmd_vel:=/robot1/diff_drive_controller/cmd_vel
```

주행 전후 두 오도메트리를 비교한다.

```bash
ros2 topic echo /robot1/odom --once --field pose.pose.position
ros2 topic echo /robot2/odom --once --field pose.pose.position
```

robot1의 위치만 바뀌고 robot2는 정지한 상태를 유지해야 한다. 첫 조종 노드를 `Ctrl+C`로 종료한 뒤 robot2도 같은 방법으로 확인한다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -p use_sim_time:=true \
  -p frame_id:=robot2/base_link \
  -r cmd_vel:=/robot2/diff_drive_controller/cmd_vel
```

이번에는 robot2만 움직여야 한다.

## 계산 예제: 교차 영향 판정

<div class="course-worked" data-worked-example="namespace-isolation">
robot1 명령 전후 변위를 \(d_1\), 명령하지 않은 robot2 변위를 \(d_2\)라 두고 \(d_1\ge0.60\,\mathrm{m}\), \(d_2\le0.02\,\mathrm{m}\)를 요구한다. 관측값이 각각 0.69 m와 0.004 m라면 이동과 격리가 동시에 합격한다. TF에서도 `robot1/base_link`와 `robot2/base_link`가 서로의 트리에 섞이지 않아야 한다.
</div>

## 자동 검증

```bash
./scripts/check_intermediate_multi_robot.sh --evidence /tmp/tutorial-intermediate-multi_robot --launch
```

검증은 두 로봇의 실제 센서 데이터와 조인트 상태, 중복 TF 부모 부재, 증가하는 단일 시계를 확인한다. 이어 robot1만 움직이고 robot2가 정지하는지 확인한 뒤 반대 경우도 검사한다.

## RViz에서 로봇별로 확인하기

이 launch는 `robot1/odom`, `robot2/odom` 사이의 공통 위치를 추정하지 않는다. 우선 RViz 창을 두 개 열고 각 로봇을 따로 확인하면 추가 TF 없이 실습할 수 있다. 각 창은 다음처럼 시뮬레이션 시간을 사용해 실행한다.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

| RViz 설정 | 첫 번째 창 | 두 번째 창 |
|---|---|---|
| Fixed Frame | `robot1/odom` | `robot2/odom` |
| RobotModel → Description Topic | `/robot1/robot_description` | `/robot2/robot_description` |
| RobotModel → TF Prefix | `robot1` | `robot2` |
| LaserScan → Topic | `/robot1/scan` | `/robot2/scan` |
| LaserScan → Reliability | Best Effort | Best Effort |

RobotModel의 Description Source는 `Topic`, Durability는 `Transient Local`로 설정한다. URDF 안의 링크 이름에는 접두사가 없기 때문에 **RViz RobotModel의 TF Prefix도 지정해야 한다.**

한 창에서 두 로봇을 같은 지도에 배치하려면 위치 추정 노드가 `map → robot1/odom`, `map → robot2/odom`을 제공해야 한다. 단순히 Fixed Frame을 `robot1/odom`으로 바꾸는 것만으로는 두 번째 로봇의 위치를 알 수 없다.

## 문제 해결

- 같은 엔티티 이름 또는 네임스페이스를 주면 launch가 시작 전에 실패하는 것이 정상이다.
- 컨트롤러 서비스가 한쪽만 보이면 spawner의 `--controller-manager` 경로를 확인한다.
- TF가 섞이면 `frame_prefix`, 컨트롤러 `base_frame_id`, 센서 `frame_id`를 같은 접두사로 맞춘다.
- robot1 명령에 robot2도 움직이면 이름 재지정과 컨트롤러 네임스페이스를 확인한다.
- `/clock` 발행 노드가 여러 개이면 브리지 YAML 또는 프로세스를 중복 실행했는지 확인한다.
- RViz에서 두 번째 로봇이 보이지 않으면 두 odom 트리를 잇는 공통 좌표계 존재 여부를 확인한다.

## 정리

다중 로봇의 핵심은 프로세스 수가 아니라 엔티티, 토픽, 컨트롤러, TF의 완전한 격리이다. Xacro 인자, 실행 설정, 브리지 YAML, 컨트롤러 YAML이 같은 이름 규칙을 사용해야 한 로봇의 명령과 센서가 다른 로봇으로 새지 않는다.

[이전: 센서 심화](08-advanced-sensors.md) · [다음: Nav2 연동](10-nav2.md)
