# 커스텀 인터페이스, ROS 2 Launch와 Simulation Control

이 장에서는 미리 준비된 카메라·조인트 노드를 넘어 임의의 메시지와 서비스를 Action Graph에 연결하고, Isaac Sim을 ROS 2에서 기동·제어하는 방법을 다룬다. 기준 환경은 Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0이다.

> **버전 경계**  
> Isaac Sim 5.1의 내장 Python은 3.11이고 Ubuntu 24.04용 ROS 2 Jazzy는 Python 3.12를 사용한다. DDS로 통신하는 별도 ROS 프로세스는 문제가 없지만, Isaac Sim 프로세스 안에서 `rclpy`와 커스텀 Python 메시지를 import하려면 같은 패키지를 Python 3.11용으로 다시 빌드해야 한다.

## 1. 인터페이스를 선택하는 기준

| 요구 | 권장 수단 | 이유 |
|---|---|---|
| 연속 센서·상태 스트림 | Topic | 비동기 스트림과 QoS를 사용할 수 있다 |
| 짧고 즉시 끝나는 요청 | Service | 요청과 응답이 한 쌍이다 |
| 진행률·취소가 필요한 작업 | Action | 피드백과 취소를 지원한다 |
| 임의 메시지를 그래프로 연결 | Generic Publisher/Subscriber | 메시지마다 전용 노드를 만들 필요가 없다 |
| 임의 서비스를 그래프로 연결 | Generic Server/Client | `.srv` 정의에서 포트를 동적으로 만든다 |
| 시뮬레이터 상태·월드·entity 제어 | Simulation Control | 표준 `simulation_interfaces`를 사용한다 |
| 복잡한 계산·상태 머신 | 커스텀 Python OmniGraph 노드 | 상태와 수명 주기를 코드로 관리할 수 있다 |

먼저 현재 환경이 인식하는 인터페이스를 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 interface list --only-msgs | less
ros2 interface list --only-srvs | less
ros2 interface show geometry_msgs/msg/Pose
ros2 interface show std_srvs/srv/SetBool
```

## 2. Generic Publisher와 Subscriber

`ROS2 Publisher`와 `ROS2 Subscriber`는 Property 패널의 세 필드로 타입을 정한다.

| 필드 | `geometry_msgs/msg/Pose` 예 |
|---|---|
| `messagePackage` | `geometry_msgs` |
| `messageSubfolder` | `msg` |
| `messageName` | `Pose` |

타입이 유효하면 노드의 포트가 자동으로 다시 구성된다. 중첩 메시지는 개별 포트로 펼쳐지고, 중첩 메시지 배열은 JSON 문자열을 담는 token 배열로 노출된다. 타입 변경만으로는 타임라인을 재생할 필요가 없다.

### 2.1 큐브 자세 발행 실습

1. `Create > Shape > Cube`로 `/World/Cube`를 만든다.
2. `Window > Graph Editors > Action Graph`에서 그래프를 만든다.
3. `On Playback Tick`, `ROS2 Context`, `Read Prim Attribute` 두 개, `ROS2 Publisher`를 추가한다.
4. 두 `Read Prim Attribute`의 prim을 `/World/Cube`로 정하고 속성을 각각 `xformOp:translate`, `xformOp:orient`로 정한다.
5. Publisher 타입은 `geometry_msgs/msg/Pose`, topic은 `/object_pose`로 정한다.
6. 위치와 방향 출력을 Publisher의 position·orientation 포트에 연결한다.

그래프를 재생하고 확인한다.

```bash
ros2 topic info /object_pose --verbose
ros2 topic echo /object_pose --once
ros2 topic hz /object_pose
```

매 렌더 프레임마다 발행할 이유가 없다면 `Isaac Simulation Gate`를 넣어 발행 주기를 제한한다. 센서와 제어 주기를 독립적으로 설정하면 부하와 지연을 예측하기 쉽다.

### 2.2 JSON token 배열

예를 들어 `geometry_msgs/msg/Polygon`의 `Point32[] points`는 다음과 같은 token 배열로 넣는다.

```text
[
  "{\"x\": 0.0, \"y\": 0.0, \"z\": 0.0}",
  "{\"x\": 1.0, \"y\": 0.0, \"z\": 0.0}",
  "{\"x\": 1.0, \"y\": 1.0, \"z\": 0.0}"
]
```

수신 측에서 타입이 맞는지 바로 검증한다.

```bash
ros2 topic type /polygon
ros2 topic echo /polygon --once
```

## 3. Generic Service Server와 Client

Generic Server는 `ROS2 Service Server Request`와 `ROS2 Service Server Response`를 한 쌍으로 사용한다.

- Request의 `serverHandle`을 Response의 `serverHandle`에 연결한다.
- Request의 `onReceived`를 계산 노드로 연결하고, 계산 완료를 Response의 실행 입력에 연결한다.
- 두 노드에 동일한 package/subfolder/name을 입력한다.
- 응답은 요청을 받은 뒤에만 보낸다. 프레임 tick에서 응답을 무조건 호출하면 요청-응답 대응이 깨진다.

`std_srvs/srv/SetBool` 예에서는 두 노드 모두 다음처럼 설정한다.

```text
messagePackage   = std_srvs
messageSubfolder = srv
messageName      = SetBool
serviceName      = /enable_sensor
```

외부에서 호출한다.

```bash
ros2 service type /enable_sensor
ros2 service call /enable_sensor std_srvs/srv/SetBool "{data: true}"
```

Generic Client도 `ROS2 Service Client Request`와 `ROS2 Service Client Response`를 조합한다. 요청 실행은 버튼·조건·상태 변화에 연결해야 하며 매 프레임 호출하지 않는다. 서비스에는 타임아웃, 재시도, 실패 시 안전 상태를 설계한다.

## 4. Prim 속성을 ROS 2 서비스로 다루기

`ROS2 Service Prim` 노드는 다음 네 서비스를 제공한다.

| 서비스 타입 | 용도 |
|---|---|
| `isaac_ros2_messages/srv/GetPrims` | 하위 prim 경로와 타입 조회 |
| `isaac_ros2_messages/srv/GetPrimAttributes` | 한 prim의 속성 이름과 타입 조회 |
| `isaac_ros2_messages/srv/GetPrimAttribute` | 속성 한 개 읽기 |
| `isaac_ros2_messages/srv/SetPrimAttribute` | 속성 한 개 쓰기 |

호출하는 터미널에는 `isaac_ros2_messages`가 있는 워크스페이스를 source해야 한다. 속성 값은 **키가 없는 JSON 값**이다. 벡터·행렬·쿼터니언은 숫자 배열로 표현한다.

```bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/setup.bash

ros2 service call /get_prims \
  isaac_ros2_messages/srv/GetPrims "{path: /World}"

ros2 service call /get_prim_attributes \
  isaac_ros2_messages/srv/GetPrimAttributes "{path: /World/Cube}"

ros2 service call /get_prim_attribute \
  isaac_ros2_messages/srv/GetPrimAttribute \
  "{path: /World/Cube, attribute: xformOp:translate}"

ros2 service call /set_prim_attribute \
  isaac_ros2_messages/srv/SetPrimAttribute \
  "{path: /World/Cube, attribute: xformOp:translate, value: '[1.0, 2.0, 0.5]'}"
```

이 기능은 빠른 실험과 원격 디버깅에 유용하지만, 임의 클라이언트가 물리·센서 속성을 바꾸면 재현성과 안전성이 무너질 수 있다. 제품 파이프라인에서는 허용 목록, namespace, 인증된 네트워크, 변경 로그를 둔다.

## 5. 커스텀 메시지의 이중 빌드

### 5.1 패키지 만들기

외부 Jazzy 노드용 워크스페이스에서 다음 패키지를 만든다고 가정한다.

```bash
mkdir -p ~/sim_interfaces_ws/src
cd ~/sim_interfaces_ws/src
ros2 pkg create sim_interfaces --build-type ament_cmake \
  --dependencies std_msgs rosidl_default_generators
mkdir -p sim_interfaces/msg sim_interfaces/srv
```

`msg/RobotHealth.msg`를 만든다.

```text
builtin_interfaces/Time stamp
string robot_name
float32 battery_percent
float32 real_time_factor
bool emergency_stop
string[] warnings
```

`srv/ResetEpisode.srv`를 만든다.

```text
uint32 seed
string world_uri
---
bool accepted
string episode_id
string message
```

`CMakeLists.txt`의 핵심은 다음과 같다.

```cmake
find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RobotHealth.msg"
  "srv/ResetEpisode.srv"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
```

`package.xml`에는 다음 의존성을 둔다.

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

### 5.2 외부 Jazzy용 Python 3.12 빌드

```bash
cd ~/sim_interfaces_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 interface show sim_interfaces/msg/RobotHealth
```

이 결과는 별도 ROS 프로세스에서 사용한다. Isaac Sim 내부 Python에 이 `install`을 그대로 넣지 않는다.

### 5.3 Isaac Sim 내부용 Python 3.11 빌드

공식 `IsaacSim-ros_workspaces` 저장소의 `jazzy_ws/src` 아래에 같은 패키지를 복사하고, 저장소 루트에서 제공 빌드 스크립트를 사용한다.

```bash
cd ~/IsaacSim-ros_workspaces
./build_ros.sh -d jazzy -v 24.04
```

빌드가 끝나면 Isaac Sim을 Python 3.11 산출물을 source한 터미널에서 시작한다. 설치 경로는 실제 빌드 출력에 맞춘다.

```bash
source ~/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash
cd ~/isaacsim
./isaac-sim.sh
```

Script Editor에서 import를 검증한다.

```python
from sim_interfaces.msg import RobotHealth

msg = RobotHealth()
msg.robot_name = "robot_01"
msg.battery_percent = 92.5
print(msg)
```

`ModuleNotFoundError`가 나면 패키지 정의 문제가 아니라 거의 항상 잘못된 Python ABI 산출물을 source한 것이다.

## 6. 커스텀 Python OmniGraph 노드

Generic 노드로 충분하지 않은 경우에만 커스텀 노드를 만든다. 공식 5.1 패턴은 `.ogn` 스키마와 Python 구현을 분리하고, 확장 의존성에 다음을 추가한다.

```toml
[dependencies]
"isaacsim.ros2.bridge" = {}
```

최소 `.ogn` 정의는 다음과 같은 형태이다.

```json
{
  "Ros2HealthMonitor": {
    "version": 1,
    "language": "python",
    "uiName": "ROS 2 Health Monitor",
    "categories": ["Robotics"],
    "inputs": {
      "execIn": {"type": "execution"},
      "topicName": {"type": "string", "default": "/robot_health"}
    },
    "outputs": {
      "execOut": {"type": "execution"},
      "batteryPercent": {"type": "float"},
      "emergencyStop": {"type": "bool"}
    }
  }
}
```

구현은 타임라인 정지 때 ROS 자원을 해제해야 한다. 다음은 수명 주기의 핵심만 보인 예이다.

```python
import rclpy
import omni.graph.core as og
from isaacsim.core.nodes import BaseResetNode
from sim_interfaces.msg import RobotHealth


class HealthState(BaseResetNode):
    def __init__(self):
        super().__init__(initialize=False)
        self.node = None
        self.subscription = None
        self.latest = None

    def initialize(self, topic_name):
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("isaac_health_monitor")
        self.subscription = self.node.create_subscription(
            RobotHealth, topic_name, self._callback, 10
        )
        self.initialized = True

    def _callback(self, msg):
        self.latest = msg

    def custom_reset(self):
        if self.node is not None:
            if self.subscription is not None:
                self.node.destroy_subscription(self.subscription)
            self.node.destroy_node()
        self.node = None
        self.subscription = None
        self.latest = None
        self.initialized = False
        rclpy.try_shutdown()


class OgnRos2HealthMonitor:
    @staticmethod
    def internal_state():
        return HealthState()

    @staticmethod
    def compute(db):
        state = db.per_instance_state
        if not state.initialized:
            state.initialize(db.inputs.topicName)
        rclpy.spin_once(state.node, timeout_sec=0.0)
        if state.latest is None:
            return True
        db.outputs.batteryPercent = state.latest.battery_percent
        db.outputs.emergencyStop = state.latest.emergency_stop
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        return True
```

`spin_once`에 긴 timeout을 주면 렌더·물리 thread가 멈춘다. 콜백에서는 값만 저장하고 무거운 계산은 별도 worker나 그래프 후단에서 처리한다. topic 이름이 바뀌면 기존 subscription을 해제하고 다시 만드는 로직도 넣어야 한다.

> **C++ 주의**  
> Isaac Sim 5.1의 공식 “Custom C++ OmniGraph Node” ROS 튜토리얼은 Linux + ROS 2 Humble만을 지원한다고 명시한다. 이 장의 Ubuntu 24.04 + Jazzy 기준에서는 그 예제를 그대로 빌드하지 않고 Python OGN 또는 외부 Jazzy 노드와 DDS 통신을 사용한다.

## 7. ROS 2 Launch로 Isaac Sim 기동하기

공식 ROS 워크스페이스의 `isaacsim` 패키지는 `run_isaacsim.launch.py`를 제공한다. Linux에서만 지원되며 WSL2에서는 이 패키지 방식이 지원되지 않는다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/setup.bash
ros2 launch isaacsim run_isaacsim.launch.py --show-args
```

일반 GUI와 특정 stage 자동 재생 예는 다음과 같다.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:=$HOME/isaacsim

ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:=$HOME/isaacsim \
  gui:=/absolute/path/to/world.usd \
  play_sim_on_start:=true
```

Jazzy의 일반 빌드는 Python 3.12이므로 Isaac Sim 내부에서 사용할 커스텀 패키지는 제외하고 Python 3.11 빌드를 명시한다.

```bash
ros2 launch isaacsim run_isaacsim.launch.py \
  install_path:=$HOME/isaacsim \
  exclude_install_path:=$HOME/IsaacSim-ros_workspaces/jazzy_ws/install \
  ros_installation_path:=$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash
```

공식 5.1 문서의 매개변수 표에는 `ros_distro` 설명이 Humble만 지원한다고 적혀 있으면서 같은 페이지가 Jazzy용 Python 3.11 경로 예제를 제공한다. 따라서 Ubuntu 24.04에서는 위 공식 Jazzy 경로 패턴을 따르고, `--show-args`로 설치된 `isaacsim` 패키지의 실제 인자를 먼저 확인한다. 최신 배포판의 인자를 추측해서 추가하지 않는다.

통합 launch에서는 Isaac Sim이 stage를 다 읽기 전에 Nav2나 MoveIt을 시작하지 않아야 한다. 공식 예는 “Stage loaded and simulation is playing.” 로그를 기다린다. 더 견고한 시스템은 로그 문자열 대신 준비 완료 topic/service를 별도 노드로 제공한다.

## 8. Simulation Control

Jazzy 인터페이스 패키지를 설치한다.

```bash
sudo apt update
sudo apt install ros-jazzy-simulation-interfaces
```

Isaac Sim 시작 시 자동 활성화한다.

```bash
cd ~/isaacsim
./isaac-sim.sh --/isaac/startup/ros_sim_control_extension=True
```

또는 Extension Manager에서 `isaacsim.ros2.sim_control`을 켠다. 기능 목록부터 조회한다.

```bash
ros2 service list | sort
ros2 action list
ros2 service call /get_simulator_features \
  simulation_interfaces/srv/GetSimulatorFeatures
```

### 8.1 상태와 결정론적 step

```bash
# 일시정지한다.
ros2 service call /set_simulation_state \
  simulation_interfaces/srv/SetSimulationState "{state: {state: 2}}"

# 10 frame을 진행하고 다시 PAUSED로 돌아간다.
ros2 service call /step_simulation \
  simulation_interfaces/srv/StepSimulation "{steps: 10}"

# 매 step 피드백을 받는다.
ros2 action send_goal /simulate_steps \
  simulation_interfaces/action/SimulateSteps "{steps: 20}" --feedback
```

`/step_simulation`과 `/simulate_steps`는 PAUSED 상태에서 호출해야 한다. 서비스는 끝날 때까지 block하고, action은 진행 피드백·취소가 필요할 때 적합하다. 한 frame 요청은 내부적으로 두 step을 사용할 수 있으므로 물리 step 수와 렌더 frame 수를 동일하다고 가정하지 않는다.

### 8.2 entity와 world

```bash
ros2 service call /get_entities \
  simulation_interfaces/srv/GetEntities "{filters: {filter: '^/World'}}"

ros2 service call /spawn_entity \
  simulation_interfaces/srv/SpawnEntity \
  "{name: 'test_robot', allow_renaming: false, uri: '/absolute/path/to/robot.usd'}"

ros2 service call /get_entity_state \
  simulation_interfaces/srv/GetEntityState "{entity: '/World/test_robot'}"

ros2 service call /delete_entity \
  simulation_interfaces/srv/DeleteEntity "{entity: '/World/test_robot'}"
```

`spawn_entity`의 URI가 있으면 USD를 reference로 추가하고, 비어 있으면 Xform을 만든다. 서비스가 생성한 prim에는 추적 속성이 붙으며 `/reset_simulation`은 이 prim들을 제거한다. 기존 stage의 원본 prim까지 모두 초기화하는 명령이라고 오해하지 않는다.

월드는 stopped 또는 paused 상태에서만 바꾼다.

```bash
ros2 service call /set_simulation_state \
  simulation_interfaces/srv/SetSimulationState "{state: {state: 2}}"

ros2 service call /load_world \
  simulation_interfaces/srv/LoadWorld "{uri: '/absolute/path/to/world.usd'}"

ros2 service call /get_current_world \
  simulation_interfaces/srv/GetCurrentWorld
```

5.1의 `/load_world`는 USD 계열 파일만 지원한다. 호출 전에 실험 결과를 저장하고, 상대 경로 대신 절대 경로나 검증된 asset URI를 사용한다.

## 9. 자동 회귀 시험 패턴

다음 순서로 episode를 반복하면 GUI 조작 없이 회귀 시험을 만들 수 있다.

1. `/load_world`로 고정된 USD를 연다.
2. `/spawn_entity`로 테스트 robot과 장애물을 배치한다.
3. `/set_simulation_state`로 pause한다.
4. seed·명령을 기록하고 `/simulate_steps`를 실행한다.
5. ROS topic과 `/get_entity_state`를 수집한다.
6. 허용 오차를 검사하고 `/reset_simulation`을 호출한다.

간단한 shell 검증 예이다.

```bash
set -euo pipefail
ros2 service wait /get_simulator_features
ros2 topic list | grep -qx /clock
ros2 service type /step_simulation | \
  grep -qx simulation_interfaces/srv/StepSimulation
ros2 action info /simulate_steps
```

CI에서는 GPU, driver, Isaac Sim build, USD hash, ROS package lock, `ROS_DOMAIN_ID`, RMW 구현, physics/render step을 결과와 함께 저장한다.

## 10. 완료 점검표

- `ros2 interface show`에서 커스텀 msg/srv가 보인다.
- 외부 Jazzy Python 3.12 산출물과 Isaac Sim 내부 Python 3.11 산출물을 섞지 않는다.
- Generic service의 request와 response가 같은 server handle과 타입을 사용한다.
- 커스텀 OGN은 타임라인 정지 때 node·subscription을 해제한다.
- launch는 stage 준비 완료 뒤에 소비자 노드를 시작한다.
- Simulation Control의 step은 pause 상태에서 호출한다.
- world 교체·entity 삭제 같은 파괴적 서비스는 허용 목록과 별도 namespace로 보호한다.

## 출처

- [Isaac Sim 5.1 — ROS 2 Generic Publisher and Subscriber](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html)
- [Isaac Sim 5.1 — ROS 2 Generic Server and Client](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_server_client.html)
- [Isaac Sim 5.1 — ROS 2 Service for Manipulating Prims Attributes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_prim_service.html)
- [Isaac Sim 5.1 — ROS 2 Python Custom Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_message_python.html)
- [Isaac Sim 5.1 — ROS 2 Python Custom OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html)
- [Isaac Sim 5.1 — ROS 2 Custom C++ OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_omnigraph_cpp_node.html)
- [Isaac Sim 5.1 — ROS 2 Launch](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html)
- [Isaac Sim 5.1 — ROS 2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)
- [ROS 2 Jazzy — Creating custom msg and srv files](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html)
