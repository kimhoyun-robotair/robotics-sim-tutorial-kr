# 관절, 차동 구동, Ackermann 제어 실전

이 장에서는 ROS 2 명령을 articulation의 joint drive까지 전달하는 과정을 구현한다. 동일한 `Articulation Controller`를 쓰더라도 이동 로봇은 차체 속도를 바퀴 속도로 변환해야 하고, 매니퓰레이터는 joint name과 명령 배열의 대응을 보존해야 한다.

## 제어 파이프라인의 공통 구조

```text
ROS 메시지 → ROS 2 Subscriber → 운동학 Controller → Articulation Controller → PhysX joint drive
```

`Articulation Controller`는 로봇의 관절 target을 전달한다. 안정성은 USD의 joint drive stiffness, damping, 최대 힘, 관성, 물리 timestep에 의해 결정된다. 메시지 수신이 정상이어도 drive 설정이 틀리면 로봇은 움직이지 않거나 발산한다.

## 1. TurtleBot 차동 구동을 만들다

URDF를 가져올 때 다음을 확인한다.

- Import mode는 `Referenced Model`을 사용한다.
- base는 `Moveable Base`로 설정한다.
- 왼쪽과 오른쪽 wheel joint의 drive target은 `Velocity`로 설정한다.
- velocity drive의 stiffness는 0, damping은 0보다 큰 값으로 둔다.

Action Graph에 다음 노드를 배치한다.

| 노드 | 핵심 입력/출력 |
|---|---|
| `On Playback Tick` | 매 simulation frame에 실행한다. |
| `ROS 2 Context` | `Use Domain ID Env Var=True`로 둔다. |
| `ROS 2 Subscribe Twist` | `topicName=/cmd_vel`로 둔다. |
| `Scale To/From Stage Unit` | ROS의 m/s를 Stage 단위로 변환한다. |
| `Break 3-Vector` 2개 | linear.x와 angular.z를 꺼낸다. |
| `Differential Controller` | 차체 속도를 좌우 바퀴 rad/s로 바꾼다. |
| `Articulation Controller` | 바퀴 joint에 velocity command를 적용한다. |

차동 구동의 기본식은 다음과 같다.

\[
\omega_L = \frac{v - \omega_z L/2}{r}, \qquad
\omega_R = \frac{v + \omega_z L/2}{r}
\]

여기서 `r`은 wheel radius, `L`은 wheel separation이다. Stage에서 실제 wheel mesh의 크기를 재지 말고 URDF와 joint 축을 기준으로 확인한다.

`Articulation Controller`에 wheel joint 이름을 명시해 순서 오류를 막는다.

```text
jointNames = [wheel_left_joint, wheel_right_joint]
```

외부 Jazzy 터미널에서 전진과 회전을 시험한다.

```bash
source /opt/ros/jazzy/setup.bash

# 2초 동안 전진한다. --once만 쓰면 마지막 명령이 계속 유지될 수 있다.
timeout 2 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.15}, angular: {z: 0.0}}' || true

# 반드시 정지 명령을 보낸다.
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.0}}'

# 제자리 회전한다.
timeout 2 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.5}}' || true
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

### 명령 watchdog을 추가하다

공식 학습 그래프는 마지막 `/cmd_vel`을 유지할 수 있다. 실제 프로젝트는 외부 노드에서 timeout을 적용한다.

```python
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class SafeCmdVel(Node):
    def __init__(self):
        super().__init__('safe_cmd_vel')
        self.sub = self.create_subscription(Twist, '/cmd_vel_raw', self.on_cmd, 10)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.last = self.get_clock().now()
        self.command = Twist()
        self.timer = self.create_timer(0.05, self.on_timer)

    def on_cmd(self, msg):
        self.command = msg
        self.last = self.get_clock().now()

    def on_timer(self):
        age = (self.get_clock().now() - self.last).nanoseconds * 1e-9
        self.pub.publish(self.command if age < 0.25 else Twist())


rclpy.init()
node = SafeCmdVel()
rclpy.spin(node)
node.destroy_node()
rclpy.shutdown()
```

## 2. Franka 관절 제어를 만들다

Content Browser에서 `Isaac Sim > Robots > FrankaRobotics > FrankaPanda > franka.usd`를 연다. 다음 Action Graph를 만든다.

- `On Playback Tick`
- `Isaac Read Simulation Time`
- `ROS 2 Publish Joint State`
- `ROS 2 Subscribe Joint State`
- `Articulation Controller`

publisher의 `targetPrim`과 controller의 `targetPrim`을 실제 articulation root에 지정한다. 공식 샘플의 기본값은 `/panda`이지만 Stage에 배치한 경로를 그대로 사용해야 한다.

```text
SubscribeJointState.outputs:jointNames
  → ArticulationController.inputs:jointNames
SubscribeJointState.outputs:positionCommand
  → ArticulationController.inputs:positionCommand
SubscribeJointState.outputs:velocityCommand
  → ArticulationController.inputs:velocityCommand
SubscribeJointState.outputs:effortCommand
  → ArticulationController.inputs:effortCommand
```

같은 관절에 position, velocity, effort 명령을 동시에 채우지 않는다. 한 제어 모드만 선택하고 나머지는 빈 배열로 둔다.

현재 joint name을 확인한다.

```bash
ros2 topic echo /joint_states --once
```

첫 번째 관절에 작은 position 목표를 보낸다. 전체 배열의 길이보다 `name`을 명시하는 방식이 안전하다.

```bash
ros2 topic pub --once /joint_command sensor_msgs/msg/JointState \
  "{name: ['panda_joint1'], position: [0.25]}"
```

메뉴 단축 경로 `Tools > Robotics > ROS 2 OmniGraphs > JointStates`는 publisher, subscriber, 선택적인 articulation controller를 자동 생성한다.

### OmniGraph를 Python으로 구성하다

Script Editor에서 실행한다. `SimulationApp`을 만들지 않는다.

```python
import omni.graph.core as og

og.Controller.edit(
    {"graph_path": "/World/ROS_Joints", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("Tick", "omni.graph.action.OnPlaybackTick"),
            ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("Pub", "isaacsim.ros2.bridge.ROS2PublishJointState"),
            ("Sub", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
            ("Control", "isaacsim.core.nodes.IsaacArticulationController"),
        ],
        og.Controller.Keys.CONNECT: [
            ("Tick.outputs:tick", "Pub.inputs:execIn"),
            ("Tick.outputs:tick", "Sub.inputs:execIn"),
            ("Tick.outputs:tick", "Control.inputs:execIn"),
            ("Time.outputs:simulationTime", "Pub.inputs:timeStamp"),
            ("Sub.outputs:jointNames", "Control.inputs:jointNames"),
            ("Sub.outputs:positionCommand", "Control.inputs:positionCommand"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("Pub.inputs:targetPrim", ["/panda"]),
            ("Sub.inputs:topicName", "/joint_command"),
            ("Control.inputs:targetPrim", ["/panda"]),
        ],
    },
)
```

`targetPrim`의 값 표현은 생성된 node attribute 타입에 따라 UI에서 지정하는 편이 더 확실하다. 실행 후 Property 패널에서 경로를 재확인한다.

## 3. `isaac:nameOverride`로 ROS 이름을 안정화하다

USD prim 이름에 ROS frame/joint naming 규칙과 맞지 않는 문자가 있거나 importer가 이름을 변경했다면 `isaac:nameOverride` attribute로 ROS에 보낼 이름을 지정한다. 이 override는 USD prim path 자체를 바꾸지 않는다.

Script Editor 예제이다.

```python
import omni.usd
from pxr import Sdf

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath('/panda/panda_link0')
attr = prim.CreateAttribute('isaac:nameOverride', Sdf.ValueTypeNames.String)
attr.Set('base_link')
```

재생을 Stop한 상태에서 설정하고 Stage를 저장한 다음 다시 Play한다.

## 4. Ackermann 차량을 제어하다

공식 5.1 예제는 Leatherback과 `AckermannDriveStamped`를 사용한다.

```bash
sudo apt install -y ros-jazzy-ackermann-msgs
```

Action Graph의 핵심 노드는 다음과 같다.

- `ROS 2 Subscribe AckermannDrive`
- `Ackermann Controller`
- steering용 `Articulation Controller`
- wheel용 `Articulation Controller`

공식 Leatherback 기준 파라미터는 다음과 같다.

| 입력 | 값 |
|---|---:|
| `frontWheelRadius`, `backWheelRadius` | 0.052 m |
| `wheelBase` | 0.32 m |
| `trackWidth` | 0.24 m |
| `maxWheelRotation` | 0.7854 rad |
| `maxWheelVelocity` | 20.0 rad/s |
| `maxAcceleration` | 1.0 m/s² |
| `maxSteeringAngleVelocity` | 1.0 rad/s |

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDriveStamped \
  "{drive: {speed: 1.0, steering_angle: 0.25}}"
```

키보드 teleop의 `Twist`를 Ackermann 명령으로 변환하려면 공식 워크스페이스를 source하고 실행한다.

```bash
ros2 launch cmdvel_to_ackermann cmdvel_to_ackermann.launch.py \
  acceleration:=0.5 steering_velocity:=0.5
```

## 5. namespace로 여러 로봇을 분리하다

각 로봇의 Action Graph를 해당 robot prim 아래에 배치하고 `nodeNamespace`를 `robot1`, `robot2`처럼 설정한다. 자동 namespace 생성 기능은 graph prim의 조상 prim 경로를 사용할 수 있으므로 Stage hierarchy를 의도적으로 설계한다.

```bash
ros2 topic list | grep -E '^/robot[12]/'
ros2 topic pub --once /robot1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1}}'
```

TF frame 이름도 robot namespace 또는 prefix로 충돌을 피해야 한다. 토픽만 분리하고 두 로봇이 모두 `base_link`를 발행하면 TF tree가 깨진다.

## 제어 검증 체크리스트

```bash
ros2 topic info /cmd_vel -v
ros2 topic hz /joint_states
ros2 topic echo /joint_states --once
```

- [ ] joint 축과 wheel 순서가 맞다.
- [ ] velocity drive의 stiffness가 0이다.
- [ ] position/velocity/effort 중 한 명령 모드만 사용한다.
- [ ] command timeout 시 0 명령을 보낸다.
- [ ] 다중 로봇에서 토픽과 TF frame이 모두 분리된다.

## 출처

- [Isaac Sim 5.1.0 — Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)
- [Isaac Sim 5.1.0 — ROS2 Joint Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html)
- [Isaac Sim 5.1.0 — NameOverride Attribute](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_name_override.html)
- [Isaac Sim 5.1.0 — ROS 2 Ackermann Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_ackermann_controller.html)
- [Isaac Sim 5.1.0 — Automatic ROS 2 Namespace Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)
