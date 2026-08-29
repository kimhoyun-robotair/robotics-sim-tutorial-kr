# 다중 로봇 namespace와 TF

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 센서 심화

## 학습 목표

- 두 entity의 Gazebo 이름과 ROS namespace를 분리한다.
- Xacro 인자로 model name, topic, TF prefix를 전달한다.
- controller manager, sensor topic, TF frame을 로봇별로 격리한다.
- 한 로봇의 velocity command가 다른 로봇을 움직이지 않는지 검증한다.

## 격리해야 하는 범위

`/robot1`, `/robot2` namespace만 추가해서는 충분하지 않다. 다음 항목이 모두 고유해야 한다.

| 범위 | robot1 | robot2 | 공유 여부 |
|---|---|---|---|
| Gazebo entity | `robot1` | `robot2` | 분리 |
| ROS namespace | `/robot1` | `/robot2` | 분리 |
| TF prefix | `robot1/` | `robot2/` | 분리 |
| controller manager | `/robot1/controller_manager` | `/robot2/controller_manager` | 분리 |
| velocity command | `/robot1/diff_drive_controller/cmd_vel` | `/robot2/diff_drive_controller/cmd_vel` | 분리 |
| odometry | `/robot1/odom` | `/robot2/odom` | 분리 |
| simulation clock | `/clock` | `/clock` | 하나만 공유 |

## robot spec를 데이터로 표현하기

실제 launch 파일은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/multi_robot.launch.py`이다. entity별 값을 immutable data class로 묶는다.

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

이름과 namespace가 같으면 spawn 전에 실패시킨다.

```python
if first.entity_name == second.entity_name:
    raise _LaunchContractError("Entity name collision")
if first.namespace == second.namespace:
    raise _LaunchContractError("ROS namespace collision")
```

## Xacro 인자와 TF prefix

같은 Xacro를 두 번 실행하되 robot별 값을 전달한다.

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

`robot_state_publisher`에도 같은 namespace와 `frame_prefix`를 전달한다.

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

URDF link 이름 자체는 `base_link`, `lidar_link`로 유지하고 runtime TF가 `robot1/base_link`, `robot1/lidar_link`가 된다. sensor의 `gz_frame_id`도 같은 prefix를 사용해야 message filter가 연결된다.

## controller manager namespace

controller spawner가 올바른 manager를 명시하도록 한다.

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

실제 `examples/ros2_ws/src/tutorial_bot_control/config/multi_robot_controllers.yaml`도 fully-qualified controller manager key를 사용한다.

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
    base_frame_id: robot1/base_link
    odom_frame_id: robot1/odom
    enable_odom_tf: true
```

robot2 block도 namespace와 frame prefix만 `robot2`로 바꾸고 geometry 값은 공유한다.

## bridge YAML 분리

센서 bridge 역시 ROS와 Gazebo 이름을 robot별로 선언한다.

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

`/clock` block은 한 번만 둔다. robot별 bridge process가 각각 `/clock`을 만들면 publisher가 중복될 수 있다.

<figure class="course-figure" id="intermediate-namespace-isolation">
  <img src="../../assets/intermediate/namespace-isolation.svg" alt="robot1과 robot2의 entity topic controller TF frame 격리도" loading="lazy">
  <figcaption>그림 1. 두 로봇은 clock만 공유하고 entity, topic, controller, TF frame을 분리한다.</figcaption>
</figure>

## 실행

두 로봇을 headless world에 띄운다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup multi_robot.launch.py
```

다른 terminal에서 inventory를 확인한다.

```bash
gz model --list
ros2 node list | grep -E '^/robot[12]/'
ros2 control list_controllers --controller-manager /robot1/controller_manager
ros2 control list_controllers --controller-manager /robot2/controller_manager
ros2 topic echo /robot1/scan --once --field header.frame_id
ros2 topic echo /robot2/scan --once --field header.frame_id
```

frame ID는 각각 `robot1/lidar_link`, `robot2/lidar_link`여야 한다.

## robot1만 keyboard teleop으로 움직이기

Jazzy DiffDrive controller는 stamped velocity를 받는다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args \
  -p stamped:=true \
  -p frame_id:=robot1/base_link \
  -r cmd_vel:=/robot1/diff_drive_controller/cmd_vel
```

주행 전후 두 odometry를 비교한다.

```bash
ros2 topic echo /robot1/odom --once --field pose.pose.position
ros2 topic echo /robot2/odom --once --field pose.pose.position
```

robot1 pose만 바뀌고 robot2는 오차 허용 범위 안에서 정지해야 한다. 이어 remap을 robot2로 바꾸어 반대 방향 격리도 확인한다.

## 계산 예제: 교차 영향 판정

<div class="course-worked" data-worked-example="namespace-isolation">
robot1 명령 전후 변위를 \(d_1\), 명령하지 않은 robot2 변위를 \(d_2\)라 두고 \(d_1\ge0.60\,\mathrm{m}\), \(d_2\le0.02\,\mathrm{m}\)를 요구한다. 관측값이 각각 0.69 m와 0.004 m라면 이동과 격리가 동시에 합격한다. TF에서도 `robot1/base_link`와 `robot2/base_link`가 서로의 tree에 섞이지 않아야 한다.
</div>

## 자동 검증

```bash
./scripts/check_intermediate_multi_robot.sh --launch
```

검증은 두 로봇의 live sensor와 joint state, 중복 TF parent 부재, 증가하는 단일 clock을 확인한다. 이어 robot1만 움직이고 robot2가 정지하는지 확인한 뒤 반대 경우도 검사한다.

## RViz에서 두 로봇 보기

RViz 한 process에서 두 RobotModel을 표시하려면 description topic과 TF prefix를 각각 지정해야 한다. 다음 설정을 사용한다.

- Fixed Frame: 공통 world 기준이 필요하지 않다면 `robot1/odom`을 선택한다.
- RobotModel 1: description topic `/robot1/robot_description`을 선택한다.
- RobotModel 2: description topic `/robot2/robot_description`을 선택한다.
- LaserScan 1/2: `/robot1/scan`, `/robot2/scan`, Best Effort를 사용한다.

두 odom frame 사이에 공통 transform이 없으면 한 Fixed Frame에서 두 로봇을 동시에 배치할 수 없다. 실제 fleet 시각화에서는 `map → robot1/odom`, `map → robot2/odom`을 각 localization source가 제공해야 한다.

## 문제 해결

- 같은 entity 이름 또는 namespace를 주면 launch가 시작 전에 실패하는 것이 정상이다.
- controller service가 한쪽만 보이면 spawner의 `--controller-manager` 경로를 확인한다.
- TF가 섞이면 `frame_prefix`, controller `base_frame_id`, sensor `frame_id`를 같은 prefix로 맞춘다.
- robot1 command에 robot2도 움직이면 remapping과 controller namespace를 확인한다.
- `/clock` publisher가 여러 개이면 bridge YAML 또는 process를 중복 실행했는지 확인한다.
- RViz에서 두 번째 로봇이 보이지 않으면 두 odom tree를 잇는 공통 frame 존재 여부를 확인한다.

## 정리

다중 로봇의 핵심은 process 수가 아니라 entity, topic, controller, TF의 완전한 격리이다. Xacro 인자, launch spec, bridge YAML, controller YAML이 같은 naming contract를 사용해야 한 로봇의 명령과 sensor가 다른 로봇으로 새지 않는다.

[이전: 센서 심화](08-advanced-sensors.md) · [다음: Nav2 연동](10-nav2.md)
