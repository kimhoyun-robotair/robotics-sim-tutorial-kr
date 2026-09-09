# 31. TF, odometry, joint state와 6.0의 새 연결 구조

[전체 목차](../../README.md) · [이전](30-clock-qos.md) · [다음](32-ros-sensors.md)

## 이번 단계에서 할 일

로봇의 위치를 나타내는 세 종류의 메시지를 구분하고, 5.1에서 작성한 TF·관절 그래프를 6.0.1 방식으로 연결한다. `/clock` 수신을 먼저 확인해야 한다. 실제 관절 실습에는 앞 단계에서 안정적으로 서 있는 로봇 articulation이 필요하다. 통신 구조만 확인할 때는 아래의 별도 큐브 장면을 사용한다.

| 데이터 | 답하는 질문 | 대표 자료형 |
|---|---|---|
| TF | 한 좌표계에서 다른 좌표계로 어떻게 변환하는가? | `tf2_msgs/msg/TFMessage` |
| odometry | 기준 좌표계에 대한 몸체 위치와 속도는 얼마인가? | `nav_msgs/msg/Odometry` |
| joint state | 이름이 붙은 각 관절의 위치·속도·힘은 얼마인가? | `sensor_msgs/msg/JointState` |

`odom`과 `base_link`는 파일 이름이 아니라 좌표계 이름이다. 바퀴를 미터 단위 위치로 잘못 해석하지 않도록 회전 관절의 위치는 라디안, 회전 속도는 rad/s로 다룬다. `JointState.name`의 순서와 position/velocity/effort 배열의 순서는 일치해야 한다.

## 1. TF를 먼저 눈으로 확인한다

30단계의 clock 예제를 종료하고 터미널 A에서 실행한다.

```bash
"$ISAAC_SIM_PATH/python.sh" examples/07_ros_scene.py --seconds 180
```

터미널 B에서 확인한다.

```bash
ros2 topic echo /tutorial/odom --once
timeout 5s ros2 run tf2_ros tf2_echo odom tutorial_base
rviz2 --ros-args -p use_sim_time:=true
```

RViz의 **Global Options > Fixed Frame**을 `odom`으로 바꾸고 **Add > TF**와 **Add > Odometry**를 추가한다. Odometry의 Topic은 `/tutorial/odom`이다. 처음에는 원점에 있는 `tutorial_base`가 보여야 한다. 이 장면은 관절이 없는 직육면체이므로 `/joint_states`는 발행하지 않는다.

이 파일의 TF 생성은 다음과 같다. odometry와 TF에 **동일한 pose와 timestamp**를 넣는다.

```python
transform.header = odom.header
transform.child_frame_id = odom.child_frame_id
transform.transform.translation.x = odom.pose.pose.position.x
transform.transform.translation.y = odom.pose.pose.position.y
transform.transform.rotation = odom.pose.pose.orientation
tf_pub.publish(TFMessage(transforms=[transform]))
```

서로 독립적으로 적분한 pose를 TF와 odometry에 각각 넣으면 작은 오차도 누적된다. 하나의 상태에서 두 메시지를 만들거나, 로봇의 실제 물리 상태를 읽어 두 메시지에 사용한다. 기구학적 예제의 odometry를 바퀴 미끄러짐까지 검증한 물리 odometry로 해석하면 안 된다.

## 2. 6.0.1 TF 그래프를 구성한다

새 그래프를 만드는 실습은 Python 큐브 장면을 종료하고, 앞 단계에서 저장한 로봇 장면을 GUI로 연 상태에서 수행한다.

1. **Stop** 상태에서 **Window > Graph Editors > Action Graph**를 연다.
2. 새 그래프를 `/World/RobotTF`에 만든다.
3. `On Playback Tick`, `ROS2 Context`, `Isaac Read Simulation Time`, `Isaac Compute Transform Tree`, `ROS2 Publish Transform Tree`를 추가한다.
4. **Compute** 노드의 `targetPrims`에 로봇 articulation root를 지정한다. Stage에서 실제 Articulation Root API가 붙은 Prim을 확인한 뒤 선택한다.
5. 특정 Prim 기준 상대변환이 필요할 때만 `parentPrim`을 지정한다.
6. Tick의 실행 출력을 Compute 노드의 `execIn`으로 연결한다. 아래 표대로 나머지를 연결한다.

| Isaac Compute Transform Tree 출력 | ROS2 Publish Transform Tree 입력 |
|---|---|
| `execOut` | `execIn` |
| `parentFrames` | `parentFrames` |
| `childFrames` | `childFrames` |
| `translations` | `translations` |
| `orientations` | `orientations` |

Context의 `context`와 Read Simulation Time의 `simulationTime`을 publisher의 `context`, `timeStamp`에도 연결한다. Prim을 해석하는 일은 Compute 노드, ROS 메시지 발행은 publisher가 담당한다. 5.1처럼 publisher에 `targetPrims`를 직접 연결하는 입력은 deprecated이다. 아직 로딩된다는 이유로 새 장면에서도 그 입력을 사용하지 않는다. [6.0 ROS 그래프 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ros2_omnigraph_migration.html)

## 3. joint state 그래프를 구성한다

같은 로봇에 `Isaac Read Joint State`와 `ROS2 Publish Joint State`를 추가한다. Read 노드는 `isaacsim.sensors.physics.nodes` Extension 소속이다. Read 노드의 `prim` 입력에 articulation root를 지정하고, 실행 Tick을 Read 노드에 연결한다.

| Isaac Read Joint State 출력 | ROS2 Publish Joint State 입력 |
|---|---|
| `execOut` | `execIn` |
| `jointNames` | `jointNames` |
| `jointPositions` | `jointPositions` |
| `jointVelocities` | `jointVelocities` |
| `jointEfforts` | `jointEfforts` |
| `jointDofTypes` | `jointDofTypes` |
| `stageMetersPerUnit` | `stageMetersPerUnit` |
| `sensorTime` | `sensorTime` |

publisher의 토픽 이름은 `/joint_states`로 정하고 Context도 연결한다. 이제 Play한 뒤 다음을 실행한다.

```bash
ros2 topic echo /joint_states --once
ros2 topic info /joint_states --verbose
```

관절 이름이 실제 모델의 이름인지, position 개수가 name 개수와 같은지, 정지 상태에서 값이 갑자기 매우 커지지 않는지 확인한다. 기본 메시지 구조를 읽는 외부 Python 코드는 다음과 같다.

```python
def joint_callback(message):
    if len(message.name) != len(message.position):
        raise ValueError("관절 이름과 위치 개수가 다르다")
    for name, position in zip(message.name, message.position):
        print(f"{name}: {position:.4f}")
```

이 코드는 수신 callback의 예시이며 단독 실행 프로그램은 아니다. 이름 없는 배열 번호를 하드코딩하기 전에 이런 식으로 실제 관절 목록부터 출력한다. [공식 joint control 실습](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_manipulation.html)

## 4. TF를 누가 발행할지 한 번만 정한다

| 구간 | 일반적인 담당 |
|---|---|
| `map → odom` | AMCL·SLAM 등 위치 추정 노드 |
| `odom → base_link` | 시뮬레이터의 odometry/TF 또는 odometry 추정 노드 하나 |
| `base_link → 센서·링크` | Isaac Sim TF 또는 URDF 기반 `robot_state_publisher` 중 선택 |

동일한 child frame에 서로 다른 부모를 동시에 붙이거나, Isaac Sim과 `robot_state_publisher`가 같은 변환을 중복 발행하지 않도록 한다. joint state를 `robot_state_publisher`에 전달하는 구성이라면 로봇 내부 TF의 담당은 해당 노드로 정한다. 공식 Nova Carter에도 TF를 직접 발행하는 장면과 joint state를 발행하는 장면이 따로 있다. Jazzy에서의 기본 Nav2 실습은 35단계의 직접 TF 장면을 사용한다.

## 완료 기준과 과제

큐브 장면에서는 `tf2_echo`에 유한한 변환이 나오고, 실제 로봇 장면에서는 관절 이름과 position 배열이 일치하면 완료한다. TF가 안 보이면 먼저 frame 이름, timestamp, 중복 publisher를 확인한다. 로봇이 무너진다면 ROS subscriber를 끈 상태에서도 같은지 확인하여 물리 모델 문제와 잘못된 명령 문제를 분리한다.

과제로 관절 하나를 낮은 속도로 움직여 `JointState.position`과 GUI의 관절 각도를 비교한다. GUI가 도 단위이고 ROS가 라디안이라면 `degrees = radians * 180 / pi`로 변환한 값을 함께 기록한다.
