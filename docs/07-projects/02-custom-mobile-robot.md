# 프로젝트 2: 커스텀 이동 로봇과 ROS 2

## 목표

간단한 differential-drive 로봇을 Xacro로 정의하고 URDF를 거쳐 USD로 import하다. articulation과 wheel drive를 검증한 뒤 ROS 2 Jazzy의 `/cmd_vel`, `/odom`, `/tf`, `/joint_states`를 연결하다.

## 요구사항

- `base_link`, 좌우 wheel, caster, camera 또는 IMU를 포함하다.
- collision은 visual보다 단순한 primitive 또는 convex shape를 사용하다.
- 모든 움직이는 link에 양의 mass와 타당한 inertia를 제공하다.
- ROS namespace를 parameter로 바꾸어 두 대를 동시에 spawn할 수 있게 하다.

## 1단계: Xacro를 URDF로 전개하다

```bash
source /opt/ros/jazzy/setup.bash
ros2 run xacro xacro \
  project-2/robot/mobile_bot.urdf.xacro \
  robot_name:=course_bot \
  > project-2/build/course_bot.urdf
check_urdf project-2/build/course_bot.urdf
```

Xacro 자체를 USD가 이해한다고 가정하지 않다. 먼저 macro를 해석해 결정된 URDF를 만들고, 그 파일과 Xacro parameter를 함께 추적하다.

## 2단계: import와 articulation 검증

1. URDF Importer를 열고 root joint, fixed base 여부, drive type, density 옵션을 의도대로 선택하다.
2. 생성된 USD를 원본 asset layer로 저장하고 scene에서는 reference로 사용하다.
3. Physics Inspector 또는 articulation API로 joint name·순서·limit를 출력하다. 5.1 메뉴는 `Tools > Physics > Physics Inspector`이다.
4. 각 wheel에 작은 velocity target을 주어 회전 방향을 확인하다.
5. 0 command에서 robot이 흔들리거나 가라앉으면 collider, inertia, gain을 먼저 고치다.

```python
# importer 결과의 articulation wrapper를 초기화한 뒤 실행하는 fragment이다.
articulation.initialize()
print(articulation.dof_names)
assert set(articulation.dof_names) >= {"left_wheel_joint", "right_wheel_joint"}
```

## 3단계: Action Graph를 연결하다

graph에는 다음 흐름을 구성하다.

```text
On Playback Tick → ROS2 Subscribe Twist → Differential Controller
                 → Articulation Controller
Read Simulation Time → ROS2 Publish Clock
Isaac Compute Odometry → ROS2 Publish Odometry
                       → ROS2 Publish Raw Transform Tree
Articulation State → ROS2 Publish Joint State
```

`Isaac Compute Odometry`, `ROS2 Publish Odometry`, `ROS2 Publish Raw Transform Tree`는 각각 독립 node이다. `Articulation State`는 `isaacsim.core.nodes` extension에서 제공하다.

wheel radius와 wheel separation은 USD geometry를 눈대중으로 읽지 말고 Xacro의 단일 parameter source에서 가져오다. topic과 frame은 namespace 아래에 두되 `/clock`은 일반적으로 global로 유지하다.

## 4단계: ROS 2에서 시험하다

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic list
ros2 topic pub --rate 10 /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.3}}"
```

다른 terminal에서 확인하다.

```bash
ros2 topic hz /robot1/odom
ros2 topic echo /robot1/joint_states --once
ros2 run tf2_ros tf2_echo odom robot1/base_link
```

## 자동 검증

30초 동안 직진 command를 주었을 때 다음을 계산하다.

- 진행 거리 오차가 설정한 tolerance 이내이다.
- yaw drift가 threshold 이내이다.
- odometry timestamp가 단조 증가하다.
- TF tree에 cycle과 다중 parent가 없다.
- stop command 후 wheel 속도가 제한 시간 안에 감소하다.

## 완료 조건

- 같은 USD reference를 `/World/robot1`, `/World/robot2`에 두고 namespace가 충돌하지 않다.
- robot의 ROS graph를 screenshot이 아니라 graph 생성 script 또는 USD로 제출하다.
- wheel slip이 클 때 friction과 controller gain 중 무엇을 바꿨는지 실험 근거를 남기다.

## 출처

- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [URDF Import: TurtleBot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html)
- [Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)
- [Automatic ROS 2 Namespace Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)
