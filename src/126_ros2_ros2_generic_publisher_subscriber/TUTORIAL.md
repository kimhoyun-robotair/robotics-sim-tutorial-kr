# 126. ROS Pose 메시지를 큐브의 위치와 방향으로 바꾸기

## 이번에 배우는 것

**Generic Publisher와 Subscriber로 큐브의 위치·방향을 주고받고, ROS 메시지 필드가 USD 변환값에 연결되는 과정을 살펴봅니다.**

Pose 전용 노드를 따로 만들지 않아도 메시지 타입을 지정하면 그 필드에 맞는 포트를 만들 수 있습니다. 이것이 이번 Generic 노드의 역할입니다. 명령을 받은 값과 실제로 적용된 값을 구분하기 위해 입력 토픽과 관측 토픽을 따로 사용합니다.

| 구성 | 값의 흐름 | 의미 |
|---|---|---|
| `/object_pose` | 외부 ROS → Subscriber | 큐브에 적용할 Pose 명령 |
| `/World/Cube` | Write → USD 속성 → Read | 위치와 방향을 저장한 장면 객체 |
| `/object_pose_observed` | Publisher → 외부 ROS | 큐브에서 읽은 현재 Pose |
| `setup_stage.py` | Script Editor → `/GenericPose` | 큐브와 왕복 그래프 생성 |

큐브는 한 변이 0.5 m이며 강체가 없습니다. 중력에 의해 떨어지는 물체 대신 명령에 따라 변환값이 바뀌는 도형을 관찰합니다.

## 1. Pose 왕복 그래프 실행하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0**과 지원 GPU를 준비하세요. 아래는 Bash 명령입니다. 시뮬레이터와 외부 ROS를 같은 컴퓨터에서 시작합니다.

시스템 ROS를 source하지 않은 **터미널 A**에서 내부 Python 3.11용 라이브러리를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **File > New**로 빈 Stage를 만들고 Stop 상태로 둡니다.
2. **Window > Script Editor**에서 이 폴더의 `setup_stage.py` 전체를 붙여 넣고 실행합니다. 시스템 `python3`에서 실행하는 파일이 아닙니다.
3. `Full Pose graph ready.` 출력과 `/GenericPose`, `/World/Cube` 생성을 확인합니다. Cube를 선택하고 **F**를 누른 뒤 Play하세요.

**터미널 B**에서 명령을 보냅니다. ROS 메시지 정의도 먼저 확인해 보세요.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 interface show geometry_msgs/msg/Pose
ros2 topic pub --once /object_pose geometry_msgs/msg/Pose '{position: {x: 1.0, y: 2.0, z: 3.0}, orientation: {w: 1.0}}'
ros2 topic echo /object_pose_observed --once
```

### 실행 결과 확인하기

Cube의 Translate가 `(1,2,3)` m로 바뀌고 관측 메시지에도 같은 위치가 나오는지 봅니다. 회전은 `(x,y,z,w)=(0,0,0,1)`입니다. **`orientation.w=1`을 생략하지 마세요.** 전부 0인 quaternion은 회전 없는 상태를 표현하지 못합니다.

처음 관측에 이전 값 `(0,0,0.5)`가 보이면 다시 읽거나 연속 echo로 갱신을 확인하세요. 같은 Tick의 읽기와 쓰기가 언제 평가되는지에 따라 적용값을 다음 프레임에서 관측할 수 있습니다. 결과 파일은 자동 저장하지 않으며 echo 종료 후에도 GUI는 계속 실행됩니다.

## 2. 동적 포트와 quaternion 연결 살펴보기

**Window > Graph Editors > Action Graph**에서 `/GenericPose`를 엽니다. Pub/Sub의 타입 설정은 `geometry_msgs`, `msg`, `Pose`입니다. 패키지 하위 폴더 이름은 `msg`입니다.

### 코드에서 볼 부분

설정 파일은 메시지 타입을 지정한 뒤 앱 업데이트를 한 번 기다리고 동적 포트에 연결합니다.

```python
await omni.kit.app.get_app().next_update_async()
```

타입에 맞는 `position:x`, `orientation:w` 등의 포트가 만들어질 시간을 주는 단계입니다. 파일 전체는 `asyncio.ensure_future(setup())`로 앱의 비동기 작업에 예약됩니다. 이미 실행 중인 앱이 있으므로 `SimulationApp`을 새로 만들지 않습니다.

위치는 세 숫자로 나누거나 합치면 됩니다.

```text
Read xformOp:translate → BreakVector3 → Pub position:x/y/z
Sub position:x/y/z → MakeVector3 → Write xformOp:translate
```

방향은 슬롯 순서를 더 주의해야 합니다. ROS quaternion 필드는 `(x,y,z,w)`이고, 여기서 사용하는 OG quaternion 저장 순서는 `[w,x,y,z]`입니다. `BreakVector4`의 X/Y/Z/W라는 이름은 네 배열 슬롯을 뜻합니다.

| Vector4 슬롯 | 연결하는 ROS quaternion 필드 |
|---|---|
| X | `orientation:w` — 실수부 |
| Y | `orientation:x` |
| Z | `orientation:y` |
| W | `orientation:z` |

실제 코드도 이 대응을 명시합니다.

```python
for slot, ros_axis in [('x','w'),('y','x'),('z','y'),('w','z')]:
    connections.extend([('BreakOrientation.outputs:'+slot,'Pub.inputs:orientation:'+ros_axis),
                        ('Sub.outputs:orientation:'+ros_axis,'MakeOrientation.inputs:'+slot)])
```

구독 방향을 MakeVector4로 모은 다음 **To Float의 Role=Quaternion**을 거쳐 `xformOp:orient`에 씁니다. USD 속성의 `quatf` 타입에 맞추기 위한 변환입니다. 데이터 선과 함께 Subscriber의 `execOut`이 Write 노드에 연결되어야 새 메시지가 도착했을 때 쓰기가 실행됩니다.

### 실행 결과 확인하기

위치를 유지하고 Z축 90도 회전 명령을 보내 보세요.

```bash
ros2 topic pub --once /object_pose geometry_msgs/msg/Pose '{position: {x: 1, y: 2, z: 3}, orientation: {x: 0, y: 0, z: 0.70710678, w: 0.70710678}}'
ros2 topic echo /object_pose_observed --once
```

관측 토픽의 z와 w가 각각 약 `0.7071`인지 확인합니다. 정육면체는 90도 돌려도 외형이 같을 수 있으므로 **Viewport 모양보다 관측 quaternion과 USD orient 값**을 확인하세요.


### 같은 Publisher로 큐브 낙하 관찰하기

명령으로 위치를 바꾸는 왕복과 물리 계산이 바꾸는 위치를 비교하려면 별도 새 Stage에서 다음을 수행하세요.

1. `setup_stage.py`를 다시 실행하고 Stop 상태에서 `/World/Cube`를 선택합니다.
2. **Add > Physics > Rigid Body with Colliders**를 적용하고 Translate Z를 **2 m**로 정합니다.
3. **Create > Physics > Ground Plane**을 추가합니다.
4. `/GenericPose`에서 Subscriber와 두 Write Prim Attribute 노드로 이어지는 쓰기 경로를 제거하고, Read → Publisher 경로는 유지합니다.
5. 외부 ROS 터미널에서 `ros2 topic echo /object_pose_observed`를 시작하고 Isaac Sim에서 Play합니다.

이번에는 외부 Pose 명령을 보내지 않아도 관측의 Z가 줄어듭니다. 한 변이 0.5 m인 큐브가 지면에 놓이면 중심 높이는 대략 0.25 m입니다. 읽는 Publisher의 역할은 같지만 **USD 위치를 바꾸는 주체가 외부 명령에서 물리 엔진으로 바뀐 것**입니다. 실험 뒤에는 새 Stage에서 원래 setup을 다시 실행하여 강체 없는 Pose 왕복으로 돌아오세요.

### 같은 Generic 노드로 관절 상태 발행하기

Pose 왕복을 확인했다면 별도 새 Stage에서 원문의 JointState 예제도 비교할 수 있습니다.

1. **Window > Examples > Robotics Examples > Import Robots > Franka URDF**에서 LOAD → CONFIGURE를 진행합니다. 설치된 Franka URDF와 메시 자산이 필요합니다.
2. 새 Action Graph에 Tick, Articulation State, ROS2 Context, Generic ROS2 Publisher, Isaac Read Simulation Time, Isaac Time Splitter를 추가합니다.
3. Articulation State의 targetPrim을 `/panda`, Publisher 타입을 `sensor_msgs / msg / JointState`, topicName을 `joint_states`로 설정합니다. Tick은 상태 읽기와 Publisher의 실행 입력에, Context는 Publisher에 연결합니다.
4. jointNames → name, jointPositions → position, jointVelocities → velocity, measuredJointEfforts → effort를 연결합니다. Time Splitter로 나눈 초·나노초를 header stamp에 넣습니다.
5. Play 후 예제의 MOVE를 누르고 `ros2 topic echo /joint_states`에서 관절 이름과 위치 변화를 확인합니다. 관찰 후 Ctrl+C로 끝냅니다.

Pose의 scalar 포트와 달리 관절 상태는 배열입니다. 같은 인덱스의 이름·위치·속도가 같은 관절을 가리키는지가 핵심이며, 로컬 `setup_stage.py`가 이 두 번째 그래프까지 만드는 것은 아닙니다.

## 3. 명령·장면·관측의 관계 정리

```text
외부 Pose 명령 → 필드를 벡터/quaternion으로 합침
  → USD 속성에 쓰기 → 같은 속성을 읽기
    → ROS 필드로 나눔 → 외부 Pose 관측
```

명령 토픽과 관측 토픽을 나누면 내가 보낸 값과 장면에서 읽은 값을 구분할 수 있습니다. 이 방식은 단순 메시지 되돌려 보내기와 달리 실제 USD 값을 통과합니다.

## 4. 간단한 확인 실험

낙하 또는 JointState 확장을 진행했다면 새 Stage에서 `setup_stage.py`를 다시 실행하고 Play하여 Pose 장면으로 돌아오세요. 먼저 1절의 명령을 다시 보내 `(1,2,3)`과 항등 회전을 기준 상태로 만드세요. 그 상태에서 **position.z만 3에서 4**로 바꾸어 보냅니다.

```bash
ros2 topic pub --once /object_pose geometry_msgs/msg/Pose '{position: {x: 1, y: 2, z: 4}, orientation: {w: 1}}'
```

큐브는 1 m 높아지고 관측 메시지의 z도 4가 되어야 합니다. x/y와 방향은 유지됩니다. 물리 속도 명령이 아니므로 큐브가 일정 시간 동안 이동하는 대신 위치값이 바로 바뀝니다.

## 실행할 때 막히면

- **`Use a new stage` 오류**: 기존 `/GenericPose` 또는 `/World/Cube`가 있습니다. 결과를 보존한 뒤 File > New에서 다시 실행하세요.
- **Pose 포트가 안 생김**: `geometry_msgs / msg / Pose` 철자와 브리지 활성화를 확인하세요.
- **토픽은 있지만 Cube가 안 바뀜**: Play와 Subscriber → Write 실행 선, Write의 prim/속성 이름을 확인하세요.
- **회전값이 이상함**: ROS w가 Vector4 X 슬롯으로 들어가는지 확인하세요. 같은 이름의 x끼리 연결하는 방식은 여기서 맞지 않습니다.
- **위치가 계속 되돌아옴**: `ros2 topic info /object_pose -v`로 다른 명령 발행자가 있는지 확인하세요.

Ubuntu 22.04/Humble에서는 양쪽 ROS 환경의 `jazzy`를 `humble`로 변경합니다. 관찰을 마치면 ROS 명령은 Ctrl+C로 끝내고 앱을 닫으세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Generic Publisher and Subscriber](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html)에 대응합니다. 내부 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

로컬 `setup_stage.py`의 위치·방향 왕복과 실제 포트 연결을 기준으로 설명했습니다. 강체 낙하나 JointState 확장은 별도 장면 구성입니다. 이 개정에서 GUI·DDS 왕복은 실행하지 않았으며 `tutorial.json`은 `verification: not_run`입니다.
