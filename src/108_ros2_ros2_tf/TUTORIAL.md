# 108. 로봇의 위치를 TF와 오도메트리로 함께 읽기

## 이번에 배우는 것

**같은 로봇의 위치를 TF와 Odometry로 발행하고, 두 메시지가 어떤 좌표계를 기준으로 하는지 확인합니다.**

“로봇이 1 m 이동했다”는 설명에는 기준이 필요합니다. 방의 원점에서 1 m인지, 출발점에서 1 m인지에 따라 숫자가 달라집니다. TF는 이런 **좌표계 사이의 위치·회전 관계**를 이어 줍니다. Odometry는 지정한 기준 좌표계의 자세와 차체 좌표계의 속도를 한 메시지에 담습니다. 이번 Isaac Compute Odometry는 로봇의 시작 자세를 위치 계산의 기준으로 사용합니다.

| 이번 실습의 요소 | 맡은 역할 |
|---|---|
| `turtlebot_tutorial.usd` | 로봇·카메라와 ROS 그래프가 있는 공식 장면 |
| ROS2 Publish Transform Tree | Stage의 실제 prim에서 좌표계 관계 읽기 |
| Isaac Compute Odometry | 차체의 시작 위치 기준 운동 계산 |
| ROS2 Publish Raw Transform Tree | 입력받은 위치·회전으로 TF 한 연결 만들기 |
| `inspect_tf.py` | 외부 ROS에서 `/tf`와 `/odom`을 받아 이름 관계 확인 |

`inspect_tf.py`는 장면을 만들거나 로봇을 움직이지 않습니다. GUI에서 발행기를 준비한 뒤 사용하는 관찰기입니다.

## 1. TurtleBot 장면에서 좌표계 발행하기

Isaac Sim 5.1과 지원 NVIDIA GPU, ROS 2 Humble 또는 Jazzy가 필요합니다. 아래 명령은 **저장소 루트의 Bash 터미널 두 개**에서 실행하세요. 기본 환경은 Ubuntu 24.04의 Jazzy입니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 시작합니다. Isaac Sim에 포함된 브리지 라이브러리를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

설치 경로가 다르면 `ISAAC_SIM`을 바꾸세요. Ubuntu 22.04/Humble 환경에서는 위의 `jazzy` 두 곳과 아래 source 경로를 `humble`로 바꿉니다. 라이브러리 경로 설정은 셸마다 한 번만 실행하세요.

터미널 B는 시스템 ROS의 CLI와 Python을 사용합니다. `rclpy`, `tf2_msgs`, `nav_msgs`, `tf2_ros`, `tf2_tools`가 필요합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

1. Content Browser에서 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd**를 엽니다. 이 자산에 접근할 수 있는 5.1 asset 서버 또는 로컬 asset pack이 필요합니다.
2. **File > Save As**로 별도 USD에 저장합니다. 이후 편집은 이 사본에서 진행하세요.
3. **Window > Graph Editors > Action Graph**에서 카메라용 **ROS2 Publish Transform Tree**를 찾습니다. 이미 같은 카메라를 발행하는 노드가 있다면 그 노드를 편집합니다.
4. `targetPrims`에 Stage에서 확인한 두 카메라 prim을 넣고 `parentPrim`은 비웁니다. `topicName`은 `/tf`로 맞춥니다.
5. Play하고 터미널 B에서 `ros2 topic echo /tf`를 실행합니다. 카메라의 frame 이름과 translation을 읽은 뒤 Ctrl+C로 관찰을 종료하세요.

### 설정에서 볼 부분

카메라 발행기에 필요한 연결은 다음 세 가지입니다. 노드가 없으면 같은 그래프에 추가하세요.

```text
On Playback Tick.tick ────────────→ TF.execIn
ROS2 Context.context ────────────→ TF.context
Isaac Read Simulation Time.simulationTime → TF.timeStamp
```

`execIn`은 발행할 시점, `timeStamp`는 그 자세를 관찰한 시각입니다. `targetPrims`는 Stage 안의 주소이고, 메시지의 `frame_id`는 ROS 좌표계 이름입니다. 두 문자열이 항상 같다고 가정하지 마세요.

`parentPrim`을 비우면 world 기준 변환을 얻습니다. 다른 prim을 지정하면 그 원점과 축을 기준으로 상대 변환을 표현합니다. 카메라를 조금 옮겼을 때 translation이 바뀌는지 확인해 보세요. 여기서는 카메라 TF만 확인하므로 아직 `inspect_tf.py`를 실행할 단계는 아닙니다. 관찰기는 `/odom`도 요구합니다.

## 2. 출발점 기준 오도메트리와 TF 연결하기

Stop한 뒤 로봇의 articulation root가 `/World/turtlebot3_burger`에 있는지 확인합니다. `/base_footprint`에만 지정되어 있다면 해당 **Raw USD Properties > Articulation Root**를 제거하고 로봇 부모 prim에 **Add > Physics > Articulation Root**를 적용한 뒤 저장하고 다시 여세요.

완성 장면의 오도메트리 그래프를 아래와 대조합니다. 새로 만든다면 동일한 `base_link`를 발행하는 기존 로봇 TF 노드는 비활성화하세요. 한 child frame을 여러 발행기가 서로 다른 부모에 연결하면 좌표계가 모호해집니다.

### 설정에서 볼 부분

1. **Isaac Compute Odometry**의 `chassisPrim`을 `/World/turtlebot3_burger`로 지정합니다.
2. Tick을 Compute의 `execIn`에 연결합니다. Compute의 `execOut`은 **ROS2 Publish Odometry**와 **ROS2 Publish Raw Transform Tree**의 `execIn`으로 연결합니다.
3. Compute의 `position`, `orientation`을 Odometry의 같은 입력과 RawTF의 `translation`, `rotation`에 연결합니다. `linearVelocity`, `angularVelocity`는 Odometry의 같은 입력으로 보냅니다.
4. 두 발행기에 Context와 Simulation Time을 연결하고 다음 이름을 설정합니다.

| 발행기 | 설정 |
|---|---|
| Odometry | `topicName=/odom`, `odomFrameId=odom`, `chassisFrameId=base_link` |
| RawTF | `topicName=/tf`, `parentFrameId=odom`, `childFrameId=base_link` |

**두 발행기가 같은 계산 결과를 사용하므로 `/odom`의 pose와 `odom → base_link` 변환을 서로 비교할 수 있습니다.** `/odom`은 속도까지 포함하며 선속도 단위는 m/s, 각속도는 rad/s입니다.

Odometry 메시지에서 `pose`는 `header.frame_id=odom` 기준이고 `twist`는 `child_frame_id=base_link` 기준입니다. 차체가 회전했다면 전진 속도 `twist.linear.x`를 world X 방향 속도로 읽지 마세요.

로봇의 다른 링크도 연결하려면 Transform Tree 발행기를 추가합니다. `parentPrim`은 `/World/turtlebot3_burger/base_link`, `targetPrims`는 로봇 아래의 `base_footprint`, `base_scan`, `caster_back_link`, `base_link/imu_link`, `wheel_left_link`, `wheel_right_link`로 지정하세요. 각 prim의 실제 경로를 Stage에서 확인하고 Tick·Context·시간도 연결합니다.

방 전체 좌표계까지 필요하면 RawTF로 `world → odom`을 추가할 수 있습니다. 이 변환에는 **로봇의 시작 world pose**를 넣습니다. 출발 위치가 원점이 아니면 translation을 0으로 두면 안 됩니다. RawTF의 회전 입력은 x/y/z/w 순서이며 회전이 없는 경우 `[0,0,0,1]`입니다. `Gf.Quatd(1,0,0,0)`의 w/x/y/z 생성자 순서와 구분하세요. AMCL 같은 위치 추정기가 같은 연결을 발행한다면 두 발행기를 동시에 사용하지 않습니다.

동일한 그래프를 메뉴로 준비하려면 **Tools > Robotics > ROS 2 OmniGraphs > TF Publisher**에서 Graph Path, target prim, parent prim을 지정합니다. 같은 부모를 쓰는 대상을 기존 노드에 더할 때는 **Add to an existing graph/node**를 선택하세요. **Odometry Publisher**에서는 로봇의 articulation root와 운동을 읽을 chassis prim을 구분해 입력하고, 생성된 frame 이름을 위 표와 대조합니다. 수동 구성과 메뉴 생성을 같은 대상에 중복 적용하지 않습니다.

### 실행 결과 확인하기

Play한 뒤 터미널 B에서 실행하세요. 지속 실행 명령은 Ctrl+C로 끝내고 다음 명령으로 넘어갑니다.

```bash
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
python3 src/108_ros2_ros2_tf/inspect_tf.py --seconds 10
```

관찰기는 10초 동안 받은 TF 연결을 집합으로 모으고 마지막 Odometry를 출력합니다.

| 출력 | 읽을 내용 |
|---|---|
| `observed_tf_edges` | `('odom', 'base_link')` 연결의 존재 |
| `odom_frame`, `child` | 각각 `odom`, `base_link`인지 |
| `pose`, `twist` | 마지막 수신 자세와 3차원 선속도·각속도 |

TF나 Odometry를 하나도 받지 못하면 `TimeoutError`, Odometry의 부모·자식 연결이 TF에 없으면 `ValueError`가 발생합니다. 이 검사는 **연결의 존재**를 확인합니다. 모든 시각의 수치 일치나 중복 발행기까지 자동 검사하지는 않습니다.

움직임도 비교하려면 다음 전진 명령을 잠깐 실행하세요. Ctrl+C 후에는 0 명령을 따로 보내 정지시킵니다.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}"
# Ctrl+C 후 실행
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

## 3. 좌표계와 운동 정보의 관계 정리

```text
world ── 시작 world pose ──→ odom ── 시작점 이후 운동 ──→ base_link
                                                          └→ 센서·바퀴 링크
```

로봇이 world의 x=3 m에서 출발해 같은 방향으로 1 m 이동했다면 world 위치는 약 4 m, 출발점 기준 위치는 약 1 m입니다. 이 차이를 연결하는 것이 `world → odom`입니다.

전체 연결을 그림으로 보려면 ROS의 `tf2_tools`가 설치된 터미널에서 `ros2 run tf2_tools view_frames`를 실행하세요. PDF 등 결과가 **현재 작업 폴더**에 생성됩니다. Isaac Sim에서는 `isaacsim.ros2.tf_viewer` 확장을 켜고 **Window > TF Viewer**에서 실제 root frame을 선택해 축과 연결선을 볼 수 있습니다.

## 4. 간단한 확인 실험

카메라 TF의 `parentPrim`을 비워 world 기준인 상태에서 **Camera_1의 Translate X만 0.1 m 늘려 보세요.** 위치를 바꾸기 전후 `/tf`의 해당 카메라 translation을 비교합니다. 다른 카메라와 로봇은 움직이지 않습니다.

카메라의 부모가 회전하지 않은 World이고 중간 변환도 없다면 TF의 x도 약 0.1 m 증가할 것으로 예상합니다. 부모가 회전한 계층에 카메라가 있다면 로컬 X 이동이 world의 다른 방향 성분에 나타날 수 있습니다. Stage의 부모 계층과 TF 기준을 함께 확인해 보세요.

## 실행할 때 막히면

- **`/odom`은 오지만 관찰기가 TF 연결 오류를 냄**: RawTF의 부모·자식 문자열과 Compute → RawTF 실행 연결을 확인하세요. `base_link`와 `/base_link`를 섞지 않습니다.
- **TF가 흔들리거나 부모가 바뀜**: 원본 장면과 실습 그래프가 같은 child를 중복 발행하는지 확인하세요.
- **`TF_OLD_DATA`가 나타남**: Stop/Play로 시간이 되돌아갔는지 확인하고 TF Viewer를 Reset하거나 수신기를 다시 시작하세요.
- **Python에서 `rclpy`가 없음**: 관찰기는 터미널 B의 시스템 `python3`로 실행합니다. 선택한 ROS 배포판의 setup 파일을 source하세요.
- **두 토픽 모두 안 보임**: Play 상태, Bridge 활성화, 두 터미널의 `ROS_DOMAIN_ID`를 차례로 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS2 Transform Trees and Odometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html)에 대응합니다. 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)의 내부 라이브러리 방식입니다.

공식 TurtleBot 장면의 그래프를 편집하고 로컬 관찰기로 TF/Odometry 이름 관계를 확인하도록 구성했습니다. `tutorial.json`은 `verification: not_run`이며, 이 문서의 수치와 출력은 실제 실행에서 대조할 기준입니다. GPU·GUI·외부 ROS 통신을 통합 실행한 결과로 제시하지 않습니다.
