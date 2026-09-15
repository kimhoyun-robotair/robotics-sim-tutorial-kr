# 129. 내가 정의한 ROS 메시지를 Isaac Sim에서 보내기

## 이번에 배우는 것

**같은 `.msg` 정의를 시뮬레이터와 외부 ROS 환경에 맞게 빌드하고, Isaac Sim의 Python에서 만든 메시지를 외부 터미널로 받습니다.**

메시지 정의가 같아도 Python에서 가져올 수 있는 빌드 결과는 실행 환경에 따라 다릅니다. Isaac Sim 5.1은 Python 3.11을 사용하고 Ubuntu 24.04의 시스템 Jazzy는 Python 3.12를 사용합니다. 이번에는 이 두 환경이 같은 메시지를 DDS로 주고받게 합니다.

| 구성 | 사용하는 환경 | 만들어지는 것 |
|---|---|---|
| `ros_ws/src/custom_message` | 공통 소스 | `SampleMsg.msg`, CMake, 패키지 정의 |
| 공식 `build_ros.sh` | Docker 기반 Python 3.11 빌드 | Isaac Sim에서 import할 ROS와 메시지 |
| 로컬 `ros_ws`의 colcon 빌드 | 시스템 ROS Python | 외부 CLI가 읽을 메시지 |
| `run.py` | Isaac Sim `python.sh` | `/custom_sample` 반복 발행 |

이 예제는 로봇이나 USD 물체를 만들지 않습니다. 화면보다 메시지 생성·수신을 관찰하는 실습입니다.

## 1. 같은 메시지를 두 환경에서 빌드하기

아래는 **Linux Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0** 기준입니다. 지원 GPU, 동작하는 Docker, ROS 개발 도구와 `colcon`이 필요합니다. 원문의 사용자 Python 메시지 과정은 Windows/WSL에서 지원되지 않습니다.

저장소 루트의 Bash에서 경로를 보관하고, 실습용 공식 워크스페이스를 준비하세요.

```bash
export LESSON_DIR="$PWD/src/129_ros2_ros2_custom_message_python"
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
```

공식 `jazzy_ws/src/custom_message`에는 같은 이름의 예제가 있습니다. 새 실습 checkout의 해당 패키지를 로컬 정의와 맞춥니다. 같은 이름의 패키지를 다른 경로에 하나 더 넣으면 colcon이 중복 패키지로 판단하므로 기존 경로를 사용하세요.

```bash
cp "$LESSON_DIR/ros_ws/src/custom_message/msg/SampleMsg.msg" "$ROS_WS_REPO/jazzy_ws/src/custom_message/msg/SampleMsg.msg"
cp "$LESSON_DIR/ros_ws/src/custom_message/CMakeLists.txt" "$ROS_WS_REPO/jazzy_ws/src/custom_message/CMakeLists.txt"
cp "$LESSON_DIR/ros_ws/src/custom_message/package.xml" "$ROS_WS_REPO/jazzy_ws/src/custom_message/package.xml"
cd "$ROS_WS_REPO"
./build_ros.sh -d jazzy -v 24.04
```

기존 checkout을 재사용할 때는 자신의 패키지 변경을 먼저 보존하세요. 이 빌드 도구는 `build_ws/jazzy`의 기존 생성물을 다시 만듭니다. 새 checkout에서 시작하면 이전 빌드와 혼동하지 않고 결과를 확인할 수 있습니다.

### 설정에서 볼 부분

`SampleMsg.msg`는 다음 두 필드입니다.

```text
std_msgs/String my_string
int64 my_num
```

`my_string`은 문자열을 담은 **중첩 메시지**이므로 Python에서는 `message.my_string.data`에 씁니다. `my_num`은 부호 있는 64비트 정수입니다.

CMake의 핵심은 다음 호출입니다.

```cmake
rosidl_generate_interfaces(${PROJECT_NAME} "msg/SampleMsg.msg" DEPENDENCIES std_msgs)
```

이 빌드는 Python 클래스뿐 아니라 메시지 직렬화에 필요한 타입 지원도 생성합니다. 일반 Python 경로만 바꾸어서는 이미 다른 Python 버전으로 만들어진 바이너리를 호환되게 만들 수 없습니다.

### 실행 결과 확인하기

외부 수신기를 준비할 **시스템 ROS 터미널**에서 저장소 루트로 이동하여 로컬 메시지 패키지도 빌드합니다.

```bash
export LESSON_DIR="$PWD/src/129_ros2_ros2_custom_message_python"
source /opt/ros/jazzy/setup.bash
cd "$LESSON_DIR/ros_ws"
colcon build --packages-select custom_message
source install/local_setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 interface show custom_message/msg/SampleMsg
ros2 topic echo /custom_sample custom_message/msg/SampleMsg
```

인터페이스에 두 필드가 나타나는지 확인합니다. echo는 발행자가 시작할 때까지 기다리게 둡니다. 여기까지는 외부 타입과 수신기를 준비한 상태입니다.

## 2. Isaac Sim에서 메시지 만들고 발행하기

**시스템 `/opt/ros`를 source하지 않은 새 Bash**를 열고 저장소 루트로 이동합니다. 이쪽에는 Python 3.11로 빌드한 두 워크스페이스를 source하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
source "$ROS_WS_REPO/build_ws/jazzy/jazzy_ws/install/local_setup.bash"
source "$ROS_WS_REPO/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
"$ISAAC_SIM/python.sh" src/129_ros2_ros2_custom_message_python/run.py --number 23
```

### 코드에서 볼 부분

`run.py`는 SimulationApp을 만든 뒤 브리지를 활성화하고 `rclpy`와 사용자 메시지를 가져옵니다.

```python
publisher = node.create_publisher(SampleMsg, '/custom_sample', 10)
message = SampleMsg()
message.my_string.data = 'hello from Isaac Sim 5.1'
message.my_num = args.number
```

`10`은 publisher 큐 깊이입니다. 반복문에서는 30번의 앱 업데이트마다 발행합니다.

```python
if frame % 30 == 0:
    publisher.publish(message)
rclpy.spin_once(node, timeout_sec=0.0)
app.update()
```

`spin_once(..., timeout_sec=0.0)`는 메시지를 기다리느라 앱 업데이트를 붙잡지 않도록 바로 반환합니다. 여기에는 `World`나 `world.step()`이 없습니다. **30 app update 간격을 30 Hz나 30 물리 단계로 읽지 마세요.** 실제 발행 간격은 앱의 업데이트 속도에 영향을 받습니다.

### 실행 결과 확인하기

시뮬레이터 터미널의 `Constructed custom message:`는 import와 필드 대입이 끝났다는 뜻입니다. 외부 echo에서 다음 값을 받아야 통신까지 확인한 것입니다.

```yaml
my_string:
  data: hello from Isaac Sim 5.1
my_num: 23
```

GUI는 창을 닫을 때까지 유지됩니다. 유한 실행은 `--steps 1200`을 추가하고, 창 없이 실행하려면 `--headless`를 사용하세요. Headless에서 `--steps`를 생략하면 기본 `--frames 1200`이 적용됩니다. `--frames`는 GUI 종료 횟수를 정하지 않으며 `--steps`가 있으면 그 값이 우선합니다.

### Script Editor의 import 확인과 비교하기

standalone을 종료한 뒤 같은 Python 3.11 환경에서 `"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge`로 GUI를 시작합니다. **Window > Script Editor**에서 다음을 실행하세요.

```python
from custom_message.msg import SampleMsg
sample = SampleMsg()
sample.my_string.data = 'Isaac Sim custom type'
sample.my_num = 23
print(sample)
```

이 방식은 메시지 import와 필드 대입을 확인합니다. Publisher를 만들지 않았으므로 외부 echo에 새 메시지가 오는 것을 기대하지 않습니다. 같은 타입이라도 **Python 객체 생성과 ROS 발행은 별도 동작**이라는 차이를 확인하세요.

## 3. 정의·빌드·전송의 관계 정리

```text
같은 SampleMsg.msg
  ├─ Python 3.11 빌드 → Isaac Sim rclpy → 발행
  └─ 시스템 ROS 빌드 → 외부 ROS CLI  ← 수신
```

**양쪽에서 같은 메시지 정의를 사용하고, 각 프로세스는 자신의 실행 환경에 맞는 빌드 결과를 읽습니다.** `.msg` 필드를 바꾸면 양쪽을 다시 빌드해야 하지만, `--number`처럼 값만 바꾸면 메시지 구조는 같으므로 다시 빌드할 필요가 없습니다.

## 4. 간단한 확인 실험

열려 있는 Isaac Sim을 종료하고 2절의 `run.py` 명령에서 **`--number 23`만 `--number 24`**로 바꾸어 다시 실행해 보세요. 외부 echo는 그대로 유지합니다.

문자열은 같고 `my_num`만 24로 바뀌어야 합니다. 이 실험은 타입 생성 과정을 건드리지 않고 실행 시 입력값이 메시지 필드까지 도달하는지 확인합니다.

## 실행할 때 막히면

- **`No module named custom_message`**: 실행하는 터미널에 맞는 설치 결과를 source했는지 확인하세요. 시뮬레이터는 `build_ws/jazzy/...`의 Python 3.11 빌드입니다.
- **`_rclpy_pybind11` 또는 undefined symbol 오류**: 시스템 Python 3.12용 ROS가 Isaac Sim 환경에 섞였는지 확인하세요. 새 Bash에서 3.11 빌드만 source합니다.
- **duplicate package 오류**: 공식 `jazzy_ws/src`에 `custom_message`가 두 군데 들어갔는지 확인하세요.
- **구성 로그는 있는데 echo가 안 나옴**: Domain ID·RMW·양쪽 메시지 정의를 확인하고 짧은 `--steps` 제한을 제거하여 discovery 시간을 확보하세요.
- **GUI가 비어 보임**: 이 스크립트는 메시지만 발행합니다. 결과는 외부 ROS 터미널에서 확인합니다.

Ubuntu 22.04/Humble은 `humble_ws`, `build_ws/humble`, `-d humble -v 22.04`를 사용하며 외부 Python은 3.10입니다. 이 경우에도 Isaac Sim용 빌드는 Python 3.11입니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Python Custom Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_message_python.html)에 대응합니다. [ROS 설치의 사용자 패키지 경로](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)와 [고정 버전 build_ros.sh](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/build_ros.sh)를 참고하세요.

원문의 import·필드 대입 확인에 로컬 반복 발행과 외부 수신을 연결했습니다. Docker 빌드, Isaac Sim 실행, DDS 수신은 이번 개정에서 수행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
