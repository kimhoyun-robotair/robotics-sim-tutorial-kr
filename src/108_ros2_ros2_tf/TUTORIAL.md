# 108. TF 변환 트리와 오도메트리를 함께 읽기

권장 학습 순서 **108** · ROS 2 연결과 기본 통신 · 출처 ID `t015`

예상 결과는 `/tf`에 센서·로봇 링크의 부모/자식 관계가, `/odom`에는 시작 자세 기준 위치와 3차원 속도가 나타나는 것이다. 원문 완성 TurtleBot scene을 시작점으로 삼고 각 그래프를 실제로 수정한다. `inspect_tf.py`는 외부 ROS 메시지를 읽어 odometry의 부모/자식 frame이 TF에도 있는지 검사한다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. Standalone `run.py`는 이 확장을 직접 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## 이 실습에서 필요한 Stage 준비

Isaac Sim Content Browser에서 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd**를 연다. 로봇·두 카메라·Lidar와 ROS 그래프가 들어 있어 다른 패키지를 먼저 실행할 필요가 없다. `output/tf_01.usd` 같은 새 이름으로 저장해 실습한다. 외부 ROS 터미널에는 `tf2_tools`, `tf2_ros`, `rclpy`, `tf2_msgs`, `nav_msgs`가 필요하다.

## 카메라와 로봇의 변환 발행

1. **Window > Graph Editors > Action Graph**에서 카메라의 **ROS2 Publish Transform Tree**를 찾는다. 없으면 새 그래프에 On Playback Tick, Context, Isaac Read Simulation Time, ROS2 Publish Transform Tree를 놓는다. Tick.tick → execIn, Context.context → context, Time.simulationTime → timeStamp를 연결한다.
2. Stage Tree에서 두 카메라의 실제 prim 경로를 확인하고 publisher.targetPrims에 각각 추가한다. 원문 예시 이름은 `Camera_1`, `Camera_2`다. parentPrim을 비워 world 기준으로 발행한다. topicName은 `/tf`다.
3. Play 후 `ros2 topic echo /tf`를 실행한다. 카메라 위치를 Gizmo로 조금 옮기고 translation 변화와 frame 이름을 관찰한다.
4. Stop한다. 다른 TF publisher에 로봇 articulation root(`/World/turtlebot3_burger`)를 targetPrims로 추가하면 articulation 내부 링크가 함께 발행된다. Root가 `/base_footprint`에만 있다면 **Raw USD Properties > Articulation Root**를 제거하고 부모 robot prim에 **Add > Physics > Articulation Root**를 추가한 뒤 Save/Reload한다.
5. 상대 좌표 실험에서는 parentPrim을 카메라 prim으로 지정한다. Stop/Play 후 같은 로봇 pose가 카메라 기준으로 달라지는지 본다. frame의 원점과 방향을 바꾼 것이므로 물리 로봇을 실제로 이동시킨 것과 구분한다.

## 오도메트리 그래프 구성

새로 만든다면 위 중복 로봇 TF publisher는 비활성화해 한 child frame에 중복 부모가 생기지 않게 한다. 완성 scene의 그래프를 사용하면 아래 연결을 하나씩 비교한다.

1. On Playback Tick, Context, Read Simulation Time, **Isaac Compute Odometry**, **ROS2 Publish Odometry**, **ROS2 Publish Raw Transform Tree**를 둔다. Compute Odometry의 chassisPrim은 `/World/turtlebot3_burger`다.
2. Tick.tick → Compute.execIn, Compute.execOut → Odom/RawTF.execIn을 연결한다. Compute의 position/orientation을 Odom.position/orientation과 RawTF.translation/rotation으로 연결한다. Compute.linearVelocity/angularVelocity를 Odom의 같은 입력에 연결한다. Context와 simulationTime도 두 발행기에 연결한다.
3. Odom.topicName=`/odom`, chassisFrameId=`base_link`, odomFrameId=`odom`; RawTF.topicName=`/tf`, parentFrameId=`odom`, childFrameId=`base_link`로 맞춘다. 이것이 `odom → base_link` 한 변이다.
4. **ROS2 Publish Transform Tree**를 추가해 parentPrim=`/World/turtlebot3_burger/base_link`로 둔다. targetPrims에 `base_footprint`, `base_scan`, `caster_back_link`, `base_link/imu_link`, `wheel_left_link`, `wheel_right_link`를 각각 robot 경로 아래 실제 경로로 지정한다. Tick/Context/Time을 연결한다. 이 발행기는 base_link 아래의 링크 관계를 제공한다.
5. ground truth 전역 위치까지 필요하면 별도 Raw Transform Tree로 `world → odom`을 추가한다. parentFrameId=`world`, childFrameId=`odom`이다. Translation/Rotation은 로봇의 **시작 world pose**를 입력한다. 로봇 시작 위치가 0이 아니면 기본 0을 쓰지 않는다. 이 변은 보통 AMCL 같은 localization 노드가 담당하므로 동시에 두 발행기로 소유하지 않는다.
6. 회전의 identity를 입력할 때 GUI가 보여 주는 quaternion 성분 순서를 확인한다. ROS는 x/y/z/w이고 USD API는 real/imaginary를 구분한다. 성분 이름을 보고 w=1, x=y=z=0으로 지정하며 네 숫자 배열의 순서를 추측하지 않는다.

## 실제 ROS 결과 확인

Play 후 외부 ROS 터미널에서 실행한다.

```bash
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
python3 inspect_tf.py --seconds 10
ros2 run tf2_tools view_frames
```

마지막 명령은 현재 폴더에 PDF 등 결과 파일을 만든다. 이전 출력을 남기려면 새 출력 폴더로 이동해 실행한다. `inspect_tf.py`는 실수신한 edge 목록과 마지막 pose/twist를 출력하고, 둘 중 하나가 없거나 odom edge가 TF에 없으면 실패한다. 움직임을 보려면 다음 명령을 잠깐 실행한 뒤 반드시 0 명령을 보낸다.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}"
# Ctrl+C 후
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

## API·USD 개념과 메뉴 shortcut

TF는 frame 사이의 rigid transform이고, USD prim 경로 자체가 ROS frame 문자열과 같다는 보장은 없다. `ROS2PublishTransformTree`는 Stage의 link pose에서 트리를 만들고, `ROS2PublishRawTransformTree`는 직접 공급한 translation/quaternion으로 한 변을 만든다. `IsaacComputeOdometry`는 chassis의 시작 위치 기준 운동을 계산한다. `/odom` 메시지에는 linear/angular velocity의 x/y/z가 모두 존재한다.

**Tools > Robotics > ROS 2 OmniGraphs > TF Publisher**는 Graph Path, namespace, target prim, parent prim을 받아 그래프를 만든다. 같은 parent 기준의 target 추가라면 **Add to an existing graph/node**를 사용한다. **Odometry Publisher** shortcut에는 articulation root와 chassis prim을 구분해 넣는다.

**Window > Extensions**에서 `isaacsim.ros2.tf_viewer`를 켜고 Play한 뒤 **Window > TF Viewer**를 연다. Root frame을 실제 출력의 `world` 또는 `World`로 선택한다. Marker, 이름, RGB XYZ축, 연결선과 업데이트 주기를 하나씩 켜서 본다. 창을 닫으면 viewport overlay와 해당 표시가 정리된다.

## 하나만 바꾸기·문제 해결

TF의 parentPrim만 World에서 Camera_1으로 바꾸고 같은 pose의 수치 변화를 본다. TF_OLD_DATA가 뜨면 시계 역행 여부를 확인하고 TF Viewer의 Reset을 누른다. frame이 안 보이면 Play 상태에서 창을 닫고 다시 연 뒤 대소문자를 점검한다. `/odom`은 오지만 TF가 없으면 RawTF 실행 연결과 토픽명을 확인한다. 원문 sample에 이미 발행기가 있으므로 실습용 새 그래프와 중복되지 않게 한다.

## 출처와 검증 범위

- [공식 5.1 TF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html#transform-tree-publisher)
- [공식 5.1 상대 변환](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html#publish-relative-transforms)
- [공식 5.1 Odometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html#setting-up-odometry)
- [공식 5.1 shortcut](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html#graph-shortcuts)
- [공식 5.1 TF Viewer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html#viewing-the-transform-tree-in-isaac-sim)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
