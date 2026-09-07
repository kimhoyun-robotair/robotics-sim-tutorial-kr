# 로봇 생성과 위치

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** ROS 2 Launch

## 학습 목표

- `robot_description` 토픽으로 엔티티를 생성한다.
- Gazebo 엔티티 이름, ROS 네임스페이스, TF 접두사, 초기 위치와 자세를 구분한다.
- 생성 높이와 요 각도를 계산한다.
- 생성 실패가 컨트롤러 시작 단계로 전파되지 않게 한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## 로봇 설명에서 엔티티까지

`robot_state_publisher`는 Xacro를 펼친 URDF를 `robot_description` 파라미터와 토픽으로 제공한다. `ros_gz_sim create`는 이 로봇 설명을 읽어 Gazebo 엔티티를 생성한다.

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
| Gazebo 엔티티 | `tutorial_bot` | Gazebo 월드 안의 모델 식별 |
| ROS 네임스페이스 | `/robot1` | 노드, 토픽, 서비스 이름 범위 |
| TF 접두사 | `robot1/` | `robot1/base_link` 같은 좌표계 이름 |
| URDF 로봇 이름 | `tutorial_bot` | 로봇 설명 문서의 루트 이름 |

이 네 값은 자동으로 같은 의미가 되지 않는다. 다중 로봇에서는 엔티티, 네임스페이스, TF 접두사를 모두 고유하게 지정해야 한다. 단일 로봇에서는 네임스페이스 `/`, 빈 TF 접두사를 사용할 수 있다.

## CLI로 직접 생성하기

먼저 월드 서버를 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
gz sim -s -r \
  "$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/training.sdf"
```

두 번째 터미널에서 로봇 설명 발행 노드를 실행한다.

```bash
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro "$robot")"
```

세 번째 터미널에서 생성한다.

```bash
ros2 run ros_gz_sim create \
  -name tutorial_bot \
  -topic robot_description \
  -x 0.0 -y 0.0 -z 0.12 -Y 0.0
```

`-Y`는 요 각도이며 rad 단위를 사용한다. roll과 pitch가 필요하면 `-R`, `-P`를 사용한다. 실제 사용 가능한 인자는 설치된 도구에서 `ros2 run ros_gz_sim create --help`로 확인한다.

## 토픽 대신 파일로 생성하기

검사용으로 펼친 URDF 또는 SDF 파일을 직접 사용할 수도 있다. 이 방법은 앞의 토픽 방식과 **택일**한다. 앞 실습의 Gazebo와 설명 발행 노드를 종료하고 첫 번째 터미널의 월드만 다시 실행한다. 두 로봇을 동시에 띄우면 센서 토픽이 겹친다.

```bash
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"
xacro "$robot" > /tmp/tutorial_bot.urdf
ros2 run ros_gz_sim create \
  -name tutorial_bot_file \
  -file /tmp/tutorial_bot.urdf \
  -x 1.0 -y 0.0 -z 0.12
```

파일 방식은 Gazebo 엔티티만 만들며 `robot_state_publisher`를 대신하지 않는다. RViz와 TF까지 사용할 때는 로봇 설명 발행 노드도 실행해야 한다. 실제 통합 예제는 토픽 방식을 사용해 Gazebo와 ROS가 같은 로봇 설명을 공유한다.

<figure class="course-figure" id="intermediate-spawn-pose">
  <img src="../../assets/intermediate/spawn-pose.svg" alt="world 좌표계에서 로봇의 위치와 yaw로 표현한 spawn pose" loading="lazy">
  <figcaption>그림 1. 생성 위치와 자세는 월드 기준 위치와 요 각도이며 엔티티 이름과 ROS 네임스페이스는 별도 설정이다.</figcaption>
</figure>

## 계산 예제: 바닥과 겹치지 않는 높이

<div class="course-worked" data-worked-example="spawn-pose">
이 로봇은 `base_link` 아래 0.06 m에 반지름 0.06 m의 바퀴가 달려 있다. 가장 낮은 점은 \(z=-0.06-0.06=-0.12\,\mathrm{m}\)이다. 캐스터의 최저점도 \(-0.085-0.035=-0.12\,\mathrm{m}\)이므로 `-z 0.12`에 놓으면 바퀴와 캐스터가 바닥에 닿는다. 여유 0.01 m를 두고 떨어뜨리려면 `-z 0.13`을 사용한다. 요 각도 \(\psi\)에서 로봇의 전방 단위 벡터는 \((\cos\psi,\sin\psi)\)이다. 예를 들어 `-Y 1.5708`은 +x 전방을 +y 방향으로 돌린다.
</div>

4륜 로버는 `base_footprint`가 지면 기준이고 몸체 중심이 그 위 0.17 m에 있으므로 실제 launch는 `-z 0.02`의 작은 여유만 둔다. 생성 높이는 루트 좌표계 이름이 아니라 가장 낮은 충돌 형상과 모델 내부 조인트 상대 위치를 기준으로 계산한다.

## 결과 확인

Gazebo 모델 목록과 ROS 로봇 설명을 서로 확인한다.

```bash
gz model --list
ros2 topic echo /robot_description --once --qos-durability transient_local
ros2 run tf2_ros tf2_echo base_link lidar_link
```

토픽 방식에서는 `tutorial_bot`이 한 번 나타나야 한다. 파일 방식에서는 `tutorial_bot_file`이 나타난다. 파일 방식에서 TF를 보려면 같은 URDF로 `robot_state_publisher`를 별도 실행해야 한다. `/robot_description`은 한 번 발행된 값을 나중에 받을 수 있도록 Transient Local QoS로 조회한다. [robot_state_publisher 공식 설명](https://github.com/ros/robot_state_publisher) 참조.

Gazebo 쪽 위치와 자세는 서비스 또는 모델 명령으로 확인한다.

```bash
gz model -m tutorial_bot --pose
```

## launch에서 실패를 전파하기

생성이 실패했는데 컨트롤러 spawner를 계속 시작하면 뒤에 나타난 서비스 제한 시간 초과가 진짜 원인을 가린다. 현재 launch는 `OnProcessExit`로 종료 코드를 검사한다.

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

`create`가 0이 아닌 종료 코드를 반환하면 launch가 후속 실행을 중단한다. 다만 종료 코드만으로 모델의 올바른 배치를 보장할 수는 없으므로, 생성 뒤에는 모델 목록과 실제 위치도 확인한다.

## 4륜 로버 생성 확인

4륜 모델은 전용 launch가 Xacro 선택과 생성을 함께 처리한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py \
  drive_mode:=diff model_name:=warehouse_rover gui:=false
```

다른 터미널에서 엔티티와 토픽 이름이 `model_name`을 따라갔는지 확인한다.

```bash
gz model --list
gz topic -l | grep '/model/warehouse_rover/'
ros2 topic list | grep -E '^/(cmd_vel|odom|joint_states|wheel_odom_path)$'
```

Gazebo 내부 토픽은 엔티티 이름을 포함하지만 launch의 브리지가 ROS 쪽을 공통 `/cmd_vel`, `/odom` 이름으로 연결한다.

## 문제 해결

- `robot_description`을 찾지 못하면 `ros2 topic info /robot_description -v`로 발행 노드와 QoS를 확인한다.
- 엔티티가 생기지 않으면 `create` 프로세스의 종료 코드와 Gazebo 서버에 UserCommands 시스템 플러그인이 있는지 확인한다.
- 같은 이름이 이미 있으면 기존 엔티티를 제거하거나 새 `-name`을 사용한다.
- 로봇이 바닥에 끼면 충돌 형상의 최저 z와 루트 링크 상대 위치를 다시 계산한다.
- 생성 직후 로봇이 튀면 바닥·검사용 구조물과 충돌 형상이 겹치지 않는지 확인한다.
- RViz에는 보이지만 Gazebo에 없으면 RobotModel 표시와 Gazebo 엔티티를 혼동한 것이다.

## 정리

생성은 Xacro/URDF 로봇 설명을 Harmonic 엔티티로 바꾸는 경계이다. 엔티티 이름, 네임스페이스, TF 접두사, 초기 위치와 자세를 별도로 관리하고 생성 성공을 확인한 뒤 컨트롤러를 시작한다. 센서 브리지는 로봇 생성 전부터 기다리고 있어도 된다.

[이전: ROS 2 Launch](03-ros2-launch.md) · [다음: ros_gz_bridge 심화](05-bridge-yaml.md)
