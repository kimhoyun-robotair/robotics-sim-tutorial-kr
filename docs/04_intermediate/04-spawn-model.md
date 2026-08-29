# Robot Spawn과 위치

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** ROS 2 Launch

## 학습 목표

- `robot_description` topic으로 entity를 생성한다.
- Gazebo entity 이름, ROS namespace, TF prefix, 초기 pose를 구분한다.
- spawn 높이와 yaw를 계산한다.
- spawn 실패가 controller 시작 단계로 전파되지 않게 한다.

## description에서 entity까지

`robot_state_publisher`는 Xacro를 펼친 URDF를 `robot_description` parameter와 topic으로 제공한다. `ros_gz_sim create`는 이 description을 읽어 Gazebo entity를 생성한다.

```python
state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    parameters=[{
        "robot_description": robot_description,
        "use_sim_time": True,
    }],
)

spawn = Node(
    package="ros_gz_sim",
    executable="create",
    arguments=[
        "-name", "tutorial_bot",
        "-topic", "robot_description",
        "-x", "0.0", "-y", "0.0", "-z", "0.12",
        "-Y", "0.0",
    ],
)
```

Gazebo Harmonic에서는 `ros_gz_sim create`를 사용한다. 구형 `spawn_entity.py` 예제와 실행 방식을 섞지 않는다.

## 네 종류의 이름

| 값 | 예 | 영향을 주는 범위 |
|---|---|---|
| Gazebo entity | `tutorial_bot` | Gazebo world 안의 model 식별 |
| ROS namespace | `/robot1` | node, topic, service 이름 범위 |
| TF prefix | `robot1/` | `robot1/base_link` 같은 frame 이름 |
| URDF robot name | `tutorial_bot` | description 문서의 root 이름 |

이 네 값은 자동으로 같은 의미가 되지 않는다. 다중 로봇에서는 entity, namespace, TF prefix를 모두 고유하게 지정해야 한다. 단일 로봇에서는 namespace `/`, 빈 TF prefix를 사용할 수 있다.

## CLI로 직접 spawn하기

먼저 world server를 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gz sim -s -r \
  "$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/training.sdf"
```

두 번째 terminal에서 description publisher를 실행한다.

```bash
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro "$robot")"
```

세 번째 terminal에서 spawn한다.

```bash
ros2 run ros_gz_sim create \
  -name tutorial_bot \
  -topic robot_description \
  -x 0.0 -y 0.0 -z 0.12 -Y 0.0
```

`-Y`는 yaw이며 rad 단위를 사용한다. roll과 pitch가 필요하면 `-R`, `-P`를 사용한다. 실제 사용 가능한 인자는 설치된 도구에서 `ros2 run ros_gz_sim create --help`로 확인한다.

## topic 대신 파일로 spawn하기

검사용으로 펼친 URDF 또는 SDF 파일을 직접 사용할 수도 있다.

```bash
xacro "$robot" > /tmp/tutorial_bot.urdf
ros2 run ros_gz_sim create \
  -name tutorial_bot_file \
  -file /tmp/tutorial_bot.urdf \
  -x 1.0 -y 0.0 -z 0.12
```

파일 방식은 Gazebo entity만 만들며 `robot_state_publisher`를 대신하지 않는다. RViz와 TF까지 사용할 때는 description publisher도 실행해야 한다. 실제 통합 예제는 topic 방식을 사용해 Gazebo와 ROS가 같은 description을 공유한다.

<figure class="course-figure" id="intermediate-spawn-pose">
  <img src="../../assets/intermediate/spawn-pose.svg" alt="world 좌표계에서 로봇의 위치와 yaw로 표현한 spawn pose" loading="lazy">
  <figcaption>그림 1. spawn pose는 world 기준 위치와 yaw이며 entity 이름과 ROS namespace는 별도 계약이다.</figcaption>
</figure>

## 계산 예제: 바닥과 겹치지 않는 높이

<div class="course-worked" data-worked-example="spawn-pose">
본체 collision 높이가 0.20 m이고 바닥 여유를 0.02 m로 두면 중심의 최소 spawn 높이는 \(z_{min}=0.20/2+0.02=0.12\,\mathrm{m}\)이다. 따라서 `-z 0.12`는 collision이 바닥 아래에서 시작하지 않게 한다. yaw \(\psi\)에서 로봇의 전방 단위 벡터는 \((\cos\psi,\sin\psi)\)이다. 예를 들어 `-Y 1.5708`은 +x 전방을 +y 방향으로 돌린다.
</div>

4륜 rover는 `base_footprint`가 지면 기준이고 몸체 중심이 그 위 0.17 m에 있으므로 실제 launch는 `-z 0.02`의 작은 여유만 둔다. spawn 높이는 root frame 이름이 아니라 가장 낮은 collision과 model 내부 joint offset을 기준으로 계산한다.

## 결과 확인

Gazebo model 목록과 ROS description을 서로 확인한다.

```bash
gz model --list
ros2 topic echo /robot_description --once
ros2 run tf2_ros tf2_echo base_link lidar_link
```

`gz model --list`에 `tutorial_bot`이 한 번만 나타나고 fixed sensor TF가 출력되면 description과 entity 생성이 이어진 것이다.

Gazebo 쪽 pose는 service 또는 model 명령으로 확인한다.

```bash
gz model -m tutorial_bot --pose
```

## launch에서 실패를 전파하기

spawn이 실패했는데 controller spawner를 계속 시작하면 뒤에 나타난 service timeout이 진짜 원인을 가린다. 현재 launch는 `OnProcessExit`로 return code를 검사한다.

```python
RegisterEventHandler(
    OnProcessExit(
        target_action=spawn,
        on_exit=_after_success(
            controller_manager_ready,
            "robot spawn",
        ),
    )
)
```

같은 entity 이름을 두 번 사용하거나 description이 잘못되면 launch 전체를 즉시 종료하는 것이 의도한 동작이다.

## 4륜 rover spawn 확인

4륜 모델은 전용 launch가 Xacro 선택과 spawn을 함께 처리한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py \
  drive_mode:=diff model_name:=warehouse_rover gui:=false
```

다른 terminal에서 entity와 topic 이름이 `model_name`을 따라갔는지 확인한다.

```bash
gz model --list
gz topic -l | grep '/model/warehouse_rover/'
ros2 topic list | grep -E '^/(cmd_vel|odom|joint_states|wheel_odom_path)$'
```

Gazebo 내부 topic은 entity 이름을 포함하지만 launch의 bridge가 ROS 쪽을 공통 `/cmd_vel`, `/odom` 이름으로 remap한다.

## 문제 해결

- `robot_description`을 찾지 못하면 `ros2 topic info /robot_description -v`로 publisher와 QoS를 확인한다.
- entity가 생기지 않으면 `create` process의 return code와 Gazebo server에 UserCommands System이 있는지 확인한다.
- 같은 이름이 이미 있으면 기존 entity를 제거하거나 새 `-name`을 사용한다.
- 로봇이 바닥에 끼면 collision의 최저 z와 root link offset을 다시 계산한다.
- spawn 직후 로봇이 튀면 바닥·fixture와 collision이 겹치지 않는지 확인한다.
- RViz에는 보이지만 Gazebo에 없으면 RobotModel 표시와 Gazebo entity를 혼동한 것이다.

## 정리

spawn은 Xacro/URDF description을 Harmonic entity로 바꾸는 경계이다. entity 이름, namespace, TF prefix, 초기 pose를 별도로 관리하고 spawn 성공을 확인한 뒤 controller와 bridge를 시작해야 한다.

[이전: ROS 2 Launch](03-ros2-launch.md) · [다음: ros_gz_bridge 심화](05-bridge-yaml.md)
