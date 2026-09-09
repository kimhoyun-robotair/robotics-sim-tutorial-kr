# MoveIt 2 매니퓰레이션 워크숍

이 장에서는 Isaac Sim의 Franka articulation을 ROS 2 Jazzy MoveIt 2에 연결하고, 커스텀 매니퓰레이터로 확장하는 기준을 정리한다.

## MoveIt과 Isaac Sim의 역할

| 구성요소 | 역할 |
|---|---|
| Isaac Sim | 물리, 충돌, 관절 drive, 센서, 실제 실행 대상이다. |
| `robot_state_publisher` | URDF와 `/joint_states`로 로봇 TF를 만든다. |
| MoveIt `move_group` | Planning Scene, 기구학, 충돌 검사, 궤적 계획을 수행한다. |
| 제어기 인터페이스 | 계획된 궤적을 Isaac Sim 관절 명령으로 전달한다. |

MoveIt의 충돌 형상과 Isaac Sim의 충돌 형상은 서로 자동 동기화되지 않는다. 같은 URDF를 출발점으로 삼고, 어느 쪽을 수정했는지 버전으로 관리해야 한다.

## 1. 의존성과 공식 워크스페이스를 확인한다

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y ros-jazzy-moveit

source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 pkg prefix isaac_moveit
```

## 2. 공식 Franka MoveIt 예제를 실행한다

1. `Window > Examples > Robotics Examples`를 연다.
2. `ROS2 > MoveIt > Franka MoveIt`을 로드한다.
3. Play를 누른다.
4. 외부 Jazzy 터미널에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
ros2 launch isaac_moveit isaac_moveit.launch.py
```

RViz2 MotionPlanning 패널에서 다음 순서로 시험한다.

1. Planning Group을 `hand`로 선택한다.
2. Goal State를 `open`으로 선택한다.
3. `Plan`, `Execute`를 누른다.
4. Planning Group을 `panda_arm`으로 바꾼다.
5. interactive marker 또는 `<random valid>` 목표를 선택한다.
6. `Plan`, `Execute`를 누른다.

일부 시스템에서 그리퍼의 `close` 실행이 늦거나 다음 명령 때 실행되는 공식 문서에 기록된 현상이 있다. 먼저 로봇 팔의 작은 움직임과 그리퍼 열기로 통신 경로를 검증한다.

## 3. ROS 인터페이스를 관찰한다

```bash
ros2 topic hz /joint_states
ros2 topic echo /joint_states --once
ros2 action list -t | grep trajectory
ros2 node list | grep -E 'move_group|robot_state_publisher'
ros2 run tf2_ros tf2_echo panda_link0 panda_hand
```

계획은 성공하지만 로봇이 움직이지 않는다면 경로 계획기보다 제어기/액션 연결을 먼저 본다.

```bash
ros2 action info /panda_arm_controller/follow_joint_trajectory
```

실제 액션 이름은 `ros2 action list` 출력에 맞춘다.

## 4. Isaac Sim 관절 그래프의 연동 규칙

공식 예제는 다음 두 방향으로 데이터를 주고받는다.

```text
Isaac articulation state → /joint_states → MoveIt
MoveIt trajectory/controller command → Isaac articulation controller
```

관절 이름, 순서, 한계, 단위가 일치해야 한다.

- 회전 관절 position: rad
- 직동 관절 position: m
- velocity: rad/s 또는 m/s
- effort: N·m 또는 N

Isaac Sim에서 `isaac:nameOverride`를 사용했다면 MoveIt URDF의 관절/링크 이름도 ROS에 보이는 이름과 맞아야 한다.

## 5. 커스텀 매니퓰레이터를 추가한다

### 5.1 로봇 자산을 준비한다

1. URDF/MJCF를 USD로 가져온다.
2. 하나의 올바른 articulation 루트를 지정한다.
3. 관절 축, 관절 하한·상한, 질량/관성, 충돌을 검증한다.
4. position drive의 stiffness/damping을 Gain Tuner로 조정한다.
5. `/joint_states`를 발행하고 각 관절을 개별 명령으로 움직인다.

### 5.2 MoveIt 설정을 만든다

MoveIt Setup Assistant에서 같은 URDF를 사용해 다음을 만든다.

- 자기 충돌 검사 행렬
- 계획 그룹과 기구학 체인
- 말단 장치 그룹
- 이름을 붙인 목표 상태
- 가상 관절 또는 월드에 고정하는 관절
- 기구학 해석기
- 제어기 설정

SRDF 개념 예제이다.

```xml
<robot name="my_arm">
  <group name="arm">
    <chain base_link="base_link" tip_link="tool0"/>
  </group>
  <group_state name="home" group="arm">
    <joint name="joint_1" value="0.0"/>
    <joint name="joint_2" value="-0.8"/>
  </group_state>
  <end_effector name="tool" parent_link="tool0" group="gripper"/>
</robot>
```

### 5.3 제어기 경로를 정한다

두 가지 패턴 중 하나를 선택한다.

1. NVIDIA 공식 워크스페이스의 토픽 기반 ROS 2 control 구성을 사용한다.
2. MoveIt 궤적을 받는 외부 어댑터가 `JointState` 명령 또는 사용자 명령으로 변환한다.

Jazzy에서 토픽 기반 제어기 의존성이 필요하면 설치한다.

```bash
sudo apt install -y ros-jazzy-topic-based-ros2-control
```

MoveIt 제어기 YAML의 개념 예제이다. 실제 플러그인/타입은 사용하는 어댑터가 제공하는 값으로 바꾼다.

```yaml
moveit_simple_controller_manager:
  controller_names:
    - arm_controller

  arm_controller:
    type: FollowJointTrajectory
    action_ns: follow_joint_trajectory
    default: true
    joints:
      - joint_1
      - joint_2
      - joint_3
      - joint_4
      - joint_5
      - joint_6
```

## 6. Planning Scene에 환경을 반영한다

Isaac Sim Stage의 상자와 선반가 MoveIt Planning Scene에 자동으로 나타나지 않는다. 고정 장애물은 MoveIt 충돌 물체로 별도 발행한다.

```python
import rclpy
from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive

rclpy.init()
node = rclpy.create_node('add_collision_box')
pub = node.create_publisher(CollisionObject, '/collision_object', 10)

obj = CollisionObject()
obj.header.frame_id = 'world'
obj.id = 'work_table'

box = SolidPrimitive()
box.type = SolidPrimitive.BOX
box.dimensions = [1.2, 0.8, 0.1]

pose = Pose()
pose.position.x = 0.6
pose.position.z = 0.75
pose.orientation.w = 1.0

obj.primitives = [box]
obj.primitive_poses = [pose]
obj.operation = CollisionObject.ADD

for _ in range(10):
    pub.publish(obj)
    rclpy.spin_once(node, timeout_sec=0.1)

node.destroy_node()
rclpy.shutdown()
```

실제 USD 물체 위치·자세를 서비스나 사용자 정의 Bridge로 읽어 자동 생성할 수도 있다. 단위, 축, 기준 프레임을 명시적으로 변환한다.

## 7. 실행 전 안전 검증

목표 위치·자세를 바로 실행하지 말고 다음 단계를 자동화한다.

1. 현재 상태가 최신인지 확인한다.
2. 계획이 성공했는지 확인한다.
3. 궤적 관절 이름이 articulation과 일치하는지 확인한다.
4. position/velocity 한계를 검사한다.
5. 시뮬레이션을 일시 정지·초기화할 수 있는 stop 경로를 준비한다.

```bash
ros2 topic hz /joint_states
ros2 topic delay /joint_states
ros2 param get /move_group use_sim_time
```

관절 상태가 시뮬레이션 시간을 사용하지 않거나 오래되면 MoveIt이 현재 상태를 찾지 못한다.

## 8. 흔한 실패

| 증상 | 원인과 조치 |
|---|---|
| RViz 로봇이 검게 보이거나 창이 깨진다. | Mesa/그래픽 환경을 점검한다. 공식 문서의 Mesa 업데이트 절차는 시스템 변경이므로 환경 정책에 맞춰 적용한다. |
| 계획 성공, 실행 무반응 | FollowJointTrajectory 액션 이름과 제어기 상태를 확인한다. |
| `Failed to fetch current robot state` | `/joint_states` 타임스탬프, `use_sim_time`, 관절 이름을 확인한다. |
| 목표에 도달하지 못하고 진동 | USD drive gain, effort 한계, 물리 시간 간격(dt)를 조정한다. |
| 장애물을 뚫고 지나간다. | MoveIt과 USD 충돌 형상이 다른지 확인한다. |
| IK가 자주 실패한다. | 시작·말단 링크, 관절 한계, SRDF group, 기구학 플러그인을 확인한다. |

## 완료 기준

- [ ] 공식 Franka에서 그리퍼와 로봇 팔을 각각 Plan/Execute했다.
- [ ] `/joint_states`의 이름과 MoveIt 로봇 모델이 일치한다.
- [ ] 직접 만든 로봇 팔의 초기 자세를 실행했다.
- [ ] Stage의 작업대를 MoveIt 충돌 물체로 반영했다.
- [ ] 계획 실패와 실행 실패를 별도 로그로 구분한다.

## 출처

- [Isaac Sim 5.1.0 — MoveIt 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_moveit.html)
- [Isaac Sim 5.1.0 — ROS2 Joint Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html)
- [Isaac Sim ROS Workspaces — isaac_moveit](https://github.com/isaac-sim/IsaacSim-ros_workspaces)
- [MoveIt 2 — Setup Assistant](https://moveit.picknik.ai/main/doc/examples/setup_assistant/setup_assistant_tutorial.html)
- [MoveIt 2 — Controller Configuration](https://moveit.picknik.ai/main/doc/examples/controller_configuration/controller_configuration_tutorial.html)
