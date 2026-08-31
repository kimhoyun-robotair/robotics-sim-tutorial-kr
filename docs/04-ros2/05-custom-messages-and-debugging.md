# Custom message, generic node와 계층별 debugging

이 튜토리얼에서는 표준 bridge node에 없는 인터페이스를 추가하다. 핵심은 `.msg/.srv/.action` 정의를 Isaac Sim의 Python 3.11 환경과 외부 Jazzy의 Python 3.12 환경에 각각 빌드하되, 두 프로세스는 DDS로만 연결하는 것이다.

## 1. 먼저 custom interface가 정말 필요한지 결정하다

다음 순서로 선택하다.

1. 의미가 맞는 표준 ROS interface가 있으면 그대로 사용하다.
2. 표준 type이지만 전용 bridge node가 없으면 ROS 2 Generic Publisher/Subscriber를 사용하다.
3. custom type이 필요하면 interface package를 양쪽 환경에 빌드하고 generic node를 사용하다.
4. 변환·state·고유 sensor 계산이 필요하면 custom Python OmniGraph node 또는 독립 ROS node를 만들다.
5. 매우 높은 rate와 큰 buffer가 필요할 때만 C++ node를 검토하다.

공식 5.1 Custom C++ OmniGraph 예제는 Humble 중심 제약이 있으므로 Ubuntu 24.04/Jazzy에서는 독립 ROS 2 C++ node 또는 Python node를 우선하고 porting test를 별도로 수행하다.

## 2. 작은 interface package를 만들다

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
mkdir -p "$HOME/isaacsim-course/ros2_ws/src"
cd "$HOME/isaacsim-course/ros2_ws/src"
ros2 pkg create course_interfaces --build-type ament_cmake
mkdir -p course_interfaces/msg course_interfaces/srv
```

`course_interfaces/msg/RobotHealth.msg`를 작성하다.

```text
builtin_interfaces/Time stamp
string robot_name
float32 battery_ratio
float32 real_time_factor
uint32 dropped_sensor_frames
string[] warnings
```

`course_interfaces/srv/SetScenario.srv`를 작성하다.

```text
string scenario_name
uint32 seed
---
bool accepted
string reason
```

`CMakeLists.txt`의 핵심을 구성하다.

```cmake
cmake_minimum_required(VERSION 3.8)
project(course_interfaces)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RobotHealth.msg"
  "srv/SetScenario.srv"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
```

`package.xml`에 다음 의존성을 추가하다.

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<depend>builtin_interfaces</depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

시스템 Jazzy/Python 3.12용으로 빌드하고 정의를 검사하다.

```bash
# [ROS]
cd "$HOME/isaacsim-course/ros2_ws"
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select course_interfaces
source install/local_setup.bash

ros2 interface show course_interfaces/msg/RobotHealth
ros2 interface show course_interfaces/srv/SetScenario
```

## 3. 외부 publisher로 type을 먼저 검증하다

`course_health_pub.py`를 일반 `ament_python` package에 넣거나 임시로 실행하다.

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from course_interfaces.msg import RobotHealth


class HealthPublisher(Node):
    def __init__(self):
        super().__init__("course_health_publisher")
        self.pub = self.create_publisher(RobotHealth, "/robot/health", 10)
        self.timer = self.create_timer(0.5, self.publish_health)

    def publish_health(self):
        msg = RobotHealth()
        msg.stamp = self.get_clock().now().to_msg()
        msg.robot_name = "demo_bot"
        msg.battery_ratio = 0.82
        msg.real_time_factor = 0.95
        msg.dropped_sensor_frames = 0
        msg.warnings = []
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = HealthPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
```

```bash
# [DBG]
source /opt/ros/jazzy/setup.bash
source "$HOME/isaacsim-course/ros2_ws/install/local_setup.bash"
ros2 topic type /robot/health
ros2 topic echo /robot/health --once
```

Isaac Sim을 연결하기 전에 외부 publisher/subscriber끼리 통신하게 해야 interface 정의와 일반 workspace 문제를 분리할 수 있다.

## 4. 같은 interface를 Isaac Sim Python 3.11에 제공하다

Python 3.12 `install/`을 `[SIM]`에서 source하면 안 되다. 동일 source package를 NVIDIA `IsaacSim-ros_workspaces`의 Python 3.11 build context에 포함하고 공식 build script를 사용하다.

```bash
# 빌드용 터미널: source package를 Python 3.11 workspace 쪽 src에도 둔다.
cp -a "$HOME/isaacsim-course/ros2_ws/src/course_interfaces" \
  "$HOME/IsaacSim-ros_workspaces/jazzy_ws/src/"

cd "$HOME/IsaacSim-ros_workspaces"
./build_ros.sh -d jazzy -v 24.04
```

새 `[SIM]` 터미널에서 Python 3.11 산출물을 source한 뒤 실행하다.

```bash
# [SIM]
source "$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash"
source "$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=17

~/isaacsim/python.sh -c \
  'from course_interfaces.msg import RobotHealth; print(RobotHealth)'
~/isaacsim/isaac-sim.sh
```

`course_interfaces`를 import하지 못하면 다음을 기록하다.

```bash
# [SIM]
~/isaacsim/python.sh -c 'import sys; print("\n".join(sys.path))'
printenv | grep -E '^(AMENT|COLCON|PYTHONPATH|LD_LIBRARY_PATH)='
```

## 5. Generic Publisher/Subscriber를 사용하다

Action Graph에서 `ROS 2 Generic Publisher` 또는 `ROS 2 Generic Subscriber`를 추가하다. Property의 type을 다음 세 필드로 지정하다.

```text
messagePackage   = course_interfaces
messageSubfolder = msg
messageName      = RobotHealth
topicName        = /robot/health
```

유효한 type이 발견되면 node의 input/output port가 message field에 맞추어 재구성되다. type을 바꾼 직후 port가 갱신되지 않으면 Stage를 저장하고 graph를 다시 열다. publisher에는 trigger, context와 각 field 값을 연결하고 subscriber에는 trigger/context를 연결한 뒤 output을 downstream logic으로 보내다.

표준 message smoke test는 CLI로도 가능하다.

```bash
# [ROS]
ros2 topic pub --once /robot/health course_interfaces/msg/RobotHealth \
  "{robot_name: demo_bot, battery_ratio: 0.7, real_time_factor: 1.0, dropped_sensor_frames: 2, warnings: ['camera_late']}"
```

Generic Service Server/Client도 `messagePackage / messageSubfolder / messageName`을 각각 `course_interfaces / srv / SetScenario`로 지정하다. server request와 response execution을 분리하고 한 요청에 response를 정확히 한 번 보내다.

## 6. custom Python OmniGraph node의 경계를 정하다

custom node는 sensor acquisition/변환처럼 Stage와 graph execution에 가까운 작업에 적합하다. ROS application logic, database 접근과 오래 걸리는 network 요청은 외부 ROS node에 두다.

```text
course.ros_health/
├── config/extension.toml
└── course/ros_health/
    ├── __init__.py
    ├── nodes/
    │   ├── OgnHealthGate.ogn
    │   └── OgnHealthGate.py
    └── extension.py
```

`.ogn`에는 데이터 계약만 선언하다.

```json
{
  "Health Gate": {
    "version": 1,
    "description": "Reject stale health samples",
    "language": "python",
    "inputs": {
      "execIn": {"type": "execution"},
      "batteryRatio": {"type": "float", "default": 1.0},
      "minimumRatio": {"type": "float", "default": 0.2}
    },
    "outputs": {
      "execOut": {"type": "execution"},
      "healthy": {"type": "bool"}
    }
  }
}
```

compute는 block하지 않고 입력에서 출력을 계산하다.

```python
class OgnHealthGate:
    @staticmethod
    def compute(db):
        db.outputs.healthy = db.inputs.batteryRatio >= db.inputs.minimumRatio
        db.outputs.execOut = db.inputs.execIn
        return True
```

`rclpy` subscription을 node 안에 직접 넣어야 한다면 매 frame node/context를 만들지 않다. internal state에서 한 번 생성하고 executor를 짧게 spin하며 graph reset과 extension shutdown에서 subscription, node와 context를 명시적으로 정리하다. callback thread에서 USD Stage를 직접 수정하지 말고 thread-safe queue로 simulation thread에 넘기다.

## 7. namespace와 여러 robot

다음처럼 topic을 robot별로 격리하다.

```text
/robot_01/cmd_vel
/robot_01/joint_states
/robot_01/front_camera/image_raw
/robot_02/cmd_vel
```

Action Graph의 `nodeNamespace` 또는 launch remap을 사용하다. graph prim 위치를 이용한 automatic namespace는 편리하지만 복잡한 hierarchy의 모든 node에 정확히 적용되지 않는 5.1 known issue가 있으므로 결과를 검사하다.

```bash
# [DBG]
ros2 topic list | sort
ros2 node list | sort
ros2 topic info /robot_01/cmd_vel -v
```

namespace를 topic 문자열과 node namespace 양쪽에 중복해 `/robot_01/robot_01/...`를 만들지 않다.

## 8. 증상별 진단 표

| 증상 | 먼저 볼 것 | 다음 조치 |
|---|---|---|
| topic이 전혀 없음 | Timeline, graph exec, bridge extension | Console error, domain/context 확인 |
| topic은 있으나 subscriber 0 | domain, namespace, type | daemon restart, discovery/firewall 확인 |
| endpoint는 보이나 data 없음 | QoS와 graph trigger | offered/requested QoS, gate/enabled 확인 |
| custom type을 못 찾음 | Python 3.11 package path | 두 workspace의 interface build 확인 |
| RViz sensor가 간헐적 | timestamp, TF, Best Effort | rate/bandwidth/RTF를 함께 측정 |
| robot이 폭주 | last command와 watchdog | zero command, drive gain/limit 확인 |
| Nav2가 extrapolation error | `/clock`, `use_sim_time`, TF timestamp | 모든 publisher의 time source 통일 |
| Stop→Play 뒤 graph 이상 | Stage 저장, stale node state | reset callback, Stage reopen |

## 9. 재현 가능한 debugging 명령 묶음

```bash
# [DBG]
source /opt/ros/jazzy/setup.bash
source "$HOME/isaacsim-course/ros2_ws/install/local_setup.bash"

ros2 doctor --report
ros2 node list
ros2 topic list -t
ros2 service list -t
ros2 action list -t

ros2 node info /suspect_node
ros2 topic info /suspect_topic -v
ros2 topic echo /suspect_topic --once
ros2 topic hz /suspect_topic
ros2 topic bw /suspect_topic

ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo odom base_link
```

daemon cache가 의심될 때만 갱신하다.

```bash
ros2 daemon stop
ros2 daemon start
```

Isaac Sim 로그를 파일로 남기다.

```bash
# [SIM]
mkdir -p "$HOME/isaacsim-course/logs"
~/isaacsim/isaac-sim.sh \
  --/log/file="$HOME/isaacsim-course/logs/isaac-ros2.log"
```

사용자 persistent setting 때문에 rate/graph 동작이 달라졌다고 의심될 때 재현용으로 factory setting을 시험하다.

```bash
# [SIM] 사용자 설정을 초기 상태로 실행하는 진단용 옵션이다.
~/isaacsim/isaac-sim.sh --reset-user
```

## 10. 오류 보고서 템플릿

```text
Isaac Sim: 5.1.0, launch 방식:
Ubuntu / GPU driver:
ROS_DISTRO / RMW / ROS_DOMAIN_ID:
[SIM] Python과 sourced setup:
[ROS] Python과 sourced setup:
Stage와 graph prim path:
topic type / publisher QoS / subscriber QoS:
expected timestamp + frame:
actual timestamp + frame:
최소 재현 순서:
Isaac log 앞뒤 50줄:
```

토큰, 사내 host, 개인 경로와 전체 환경 변수 dump의 비밀값은 공유 전에 제거하다.

## 완료 체크포인트

- [ ] `RobotHealth.msg`를 Python 3.11과 3.12 양쪽에서 import했다.
- [ ] Generic Subscriber가 외부 publisher의 custom message를 받았다.
- [ ] custom node의 lifecycle에서 ROS/graph resource를 정리하다.
- [ ] 두 robot namespace의 topic이 충돌하지 않다.
- [ ] 진단 순서를 domain→discovery→type→QoS→time→TF→rate로 수행했다.

## 출처

- [Isaac Sim 5.1 — ROS 2 Generic Publisher and Subscriber](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html)
- [Isaac Sim 5.1 — ROS 2 Generic Server and Client](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_server_client.html)
- [Isaac Sim 5.1 — ROS 2 Python Custom Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_message_python.html)
- [Isaac Sim 5.1 — ROS 2 Python Custom OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html)
- [Isaac Sim 5.1 — ROS 2 Custom C++ OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_omnigraph_cpp_node.html)
- [Isaac Sim 5.1 — ROS 2 Installation and Python 3.11 Workspaces](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1 — Automatic ROS 2 Namespace Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)
- [Isaac Sim 5.1 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
- [Isaac Sim 5.1 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
