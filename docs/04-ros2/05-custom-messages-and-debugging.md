# 커스텀 메시지, Generic 노드와 계층별 디버깅

이 튜토리얼에서는 표준 Bridge 노드에 없는 인터페이스를 추가한다. 핵심은 `.msg/.srv/.action` 정의를 Isaac Sim의 Python 3.11 환경과 외부 Jazzy의 Python 3.12 환경에 각각 빌드하되, 두 프로세스는 DDS로만 연결하는 것이다.

## 1. 먼저 사용자 정의 인터페이스가 정말 필요한지 결정한다

다음 순서로 선택한다.

1. 의미가 맞는 표준 ROS 인터페이스가 있으면 그대로 사용한다.
2. 표준 타입이지만 전용 Bridge 노드가 없으면 ROS 2 Generic Publisher/Subscriber를 사용한다.
3. 사용자 정의 타입이 필요하면 인터페이스 패키지를 양쪽 환경에 빌드하고 Generic 노드를 사용한다.
4. 변환·상태·고유 센서 계산이 필요하면 사용자 정의 Python OmniGraph 노드 또는 독립 ROS 노드를 만든다.
5. 매우 높은 실행 빈도와 큰 버퍼가 필요할 때만 C++ 노드를 검토한다.

공식 5.1 Custom C++ OmniGraph 예제는 Humble 중심 제약이 있으므로 Ubuntu 24.04/Jazzy에서는 독립 ROS 2 C++ 노드 또는 Python 노드를 우선하고 이식 시험를 별도로 수행한다.

## 2. 작은 인터페이스 패키지를 만든다

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
mkdir -p "$HOME/isaacsim-course/ros2_ws/src"
cd "$HOME/isaacsim-course/ros2_ws/src"
ros2 pkg create course_interfaces --build-type ament_cmake
mkdir -p course_interfaces/msg course_interfaces/srv
```

`course_interfaces/msg/RobotHealth.msg`를 작성한다.

```text
builtin_interfaces/Time stamp
string robot_name
float32 battery_ratio
float32 real_time_factor
uint32 dropped_sensor_frames
string[] warnings
```

`course_interfaces/srv/SetScenario.srv`를 작성한다.

```text
string scenario_name
uint32 seed
---
bool accepted
string reason
```

`CMakeLists.txt`의 핵심을 구성한다.

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

`package.xml`에 다음 의존성을 추가한다.

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<depend>builtin_interfaces</depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

시스템 Jazzy/Python 3.12용으로 빌드하고 정의를 검사한다.

```bash
# [ROS]
cd "$HOME/isaacsim-course/ros2_ws"
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select course_interfaces
source install/local_setup.bash

ros2 interface show course_interfaces/msg/RobotHealth
ros2 interface show course_interfaces/srv/SetScenario
```

## 3. 외부 발행 노드로 타입을 먼저 검증한다

`course_health_pub.py`를 일반 `ament_python` 패키지에 넣거나 임시로 실행한다.

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

Isaac Sim을 연결하기 전에 외부 발행 노드와 구독 노드끼리 통신하게 해야 인터페이스 정의와 일반 워크스페이스 문제를 분리할 수 있다.

## 4. 같은 인터페이스를 Isaac Sim Python 3.11에 제공한다

Python 3.12 `install/`을 `[SIM]`에서 불러오면 안 된다. 동일 소스 패키지를 NVIDIA `IsaacSim-ros_workspaces`의 Python 3.11 빌드 환경에 포함하고 공식 빌드 스크립트를 사용한다.

```bash
# 빌드용 터미널: source package를 Python 3.11 workspace 쪽 src에도 둔다.
cp -a "$HOME/isaacsim-course/ros2_ws/src/course_interfaces" \
  "$HOME/IsaacSim-ros_workspaces/jazzy_ws/src/"

cd "$HOME/IsaacSim-ros_workspaces"
./build_ros.sh -d jazzy -v 24.04
```

새 `[SIM]` 터미널에서 Python 3.11 산출물을 불러온 뒤 실행한다.

```bash
# [SIM]
source "$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash"
source "$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=17

~/isaacsim/python.sh -c \
  'from course_interfaces.msg import RobotHealth; print(RobotHealth)'
~/isaacsim/isaac-sim.sh
```

`course_interfaces`를 import하지 못하면 다음을 기록한다.

```bash
# [SIM]
~/isaacsim/python.sh -c 'import sys; print("\n".join(sys.path))'
printenv | grep -E '^(AMENT|COLCON|PYTHONPATH|LD_LIBRARY_PATH)='
```

## 5. Generic Publisher/Subscriber를 사용한다

Action Graph에서 `ROS 2 Generic Publisher` 또는 `ROS 2 Generic Subscriber`를 추가한다. Property의 타입을 다음 세 필드로 지정한다.

```text
messagePackage   = course_interfaces
messageSubfolder = msg
messageName      = RobotHealth
topicName        = /robot/health
```

유효한 타입이 발견되면 노드의 입출력 포트가 메시지 필드에 맞추어 재구성된다. 타입을 바꾼 직후 포트가 갱신되지 않으면 Stage를 저장하고 그래프를 다시 연다. 발행 노드에는 실행 신호, 컨텍스트와 각 필드 값을 연결하고 구독 노드에는 실행 신호·컨텍스트를 연결한 뒤 출력을 후속 처리 로직으로 보낸다.

표준 메시지 기본 동작 확인은 CLI로도 가능하다.

```bash
# [ROS]
ros2 topic pub --once /robot/health course_interfaces/msg/RobotHealth \
  "{robot_name: demo_bot, battery_ratio: 0.7, real_time_factor: 1.0, dropped_sensor_frames: 2, warnings: ['camera_late']}"
```

Generic Service Server/Client도 `messagePackage / messageSubfolder / messageName`을 각각 `course_interfaces / srv / SetScenario`로 지정한다. 서버 요청과 응답 실행을 분리하고 한 요청에 응답을 정확히 한 번 보낸다.

## 6. 사용자 정의 Python OmniGraph 노드의 경계를 정한다

사용자 정의 노드는 센서 데이터 수집·변환처럼 Stage와 그래프 실행에 가까운 작업에 적합하다. ROS 애플리케이션 로직, 데이터베이스 접근과 오래 걸리는 네트워크 요청은 외부 ROS 노드에 둔다.

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

`.ogn`에는 데이터 연동 규칙만 선언한다.

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

compute는 다른 실행을 막지 않고 입력에서 출력을 계산한다.

```python
class OgnHealthGate:
    @staticmethod
    def compute(db):
        db.outputs.healthy = db.inputs.batteryRatio >= db.inputs.minimumRatio
        db.outputs.execOut = db.inputs.execIn
        return True
```

`rclpy` 구독을 노드 안에 직접 넣어야 한다면 매 프레임 노드/컨텍스트를 만들지 않는다. 내부 상태에서 한 번 생성하고 executor를 짧게 spin하며 그래프 초기화와 확장 종료에서 구독, 노드와 컨텍스트를 명시적으로 정리한다. 콜백 스레드에서 USD Stage를 직접 수정하지 말고 스레드 안전 큐로 시뮬레이션 스레드에 넘긴다.

## 7. 네임스페이스와 여러 로봇

다음처럼 토픽을 로봇별로 격리한다.

```text
/robot_01/cmd_vel
/robot_01/joint_states
/robot_01/front_camera/image_raw
/robot_02/cmd_vel
```

Action Graph의 `nodeNamespace` 또는 launch remap을 사용한다. 그래프 prim 위치를 이용한 자동 네임스페이스는 편리하지만 복잡한 계층의 모든 노드에 정확히 적용되지 않는 5.1 알려진 문제가 있으므로 결과를 검사한다.

```bash
# [DBG]
ros2 topic list | sort
ros2 node list | sort
ros2 topic info /robot_01/cmd_vel -v
```

네임스페이스를 토픽 문자열과 노드 네임스페이스 양쪽에 중복해 `/robot_01/robot_01/...`를 만들지 않는다.

## 8. 증상별 진단 표

| 증상 | 먼저 볼 것 | 다음 조치 |
|---|---|---|
| 토픽이 전혀 없음 | Timeline, 그래프 실행, Bridge 확장 | 콘솔 오류, 도메인/컨텍스트 확인 |
| 토픽은 있으나 구독 노드 0 | 도메인, 네임스페이스, 타입 | 데몬 재시작, 참여자 탐색·방화벽 확인 |
| 통신 끝점은 보이나 데이터 없음 | QoS와 그래프 실행 신호 | 발행 측·구독 측 QoS, gate/enabled 확인 |
| 사용자 정의 타입을 못 찾음 | Python 3.11 패키지 경로 | 두 워크스페이스의 인터페이스 빌드 확인 |
| RViz 센서가 간헐적 | 타임스탬프, TF, Best Effort | 주기/대역폭/RTF를 함께 측정 |
| 로봇이 폭주 | 마지막 명령과 watchdog | 속도 0 명령, drive gain/한계 확인 |
| Nav2가 extrapolation error | `/clock`, `use_sim_time`, TF 타임스탬프 | 모든 발행 노드의 시간 기준 통일 |
| Stop→Play 뒤 그래프 이상 | Stage 저장, 오래된 노드 상태 | 초기화 콜백, Stage 다시 열기 |

## 9. 재현 가능한 디버깅 명령 묶음

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

데몬 캐시가 의심될 때만 갱신한다.

```bash
ros2 daemon stop
ros2 daemon start
```

Isaac Sim 로그를 파일로 남긴다.

```bash
# [SIM]
mkdir -p "$HOME/isaacsim-course/logs"
~/isaacsim/isaac-sim.sh \
  --/log/file="$HOME/isaacsim-course/logs/isaac-ros2.log"
```

사용자가 저장한 설정 때문에 주기/그래프 동작이 달라졌다고 의심될 때 재현용으로 초기 설정을 시험한다.

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

토큰, 사내 호스트, 개인 경로와 전체 환경 변수 dump의 비밀값은 공유 전에 제거한다.

## 완료 체크포인트

- [ ] `RobotHealth.msg`를 Python 3.11과 3.12 양쪽에서 import했다.
- [ ] Generic Subscriber가 외부 발행 노드의 사용자 정의 메시지를 받았다.
- [ ] 사용자 정의 노드의 lifecycle에서 ROS·그래프 자원을 정리한다.
- [ ] 두 로봇 네임스페이스의 토픽이 충돌하지 않는다.
- [ ] 진단 순서를 도메인→참여자 탐색→타입→QoS→시간→TF→주기로 수행했다.

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
