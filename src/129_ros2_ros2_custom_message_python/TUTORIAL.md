# 129. ROS 2 Python Custom Messages

권장 학습 순서 **129** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t030`

**목표:** 로컬 `.msg`에서 ROS 인터페이스를 빌드하고 Isaac Sim 내부 Python에서 가져와 실제로 발행합니다. `ros_ws/src/custom_message`에 CMake, package.xml, SampleMsg 정의를 모두 포함합니다. Linux 실습이며 원문 기준 Windows/WSL custom Python workflow는 지원되지 않습니다.


**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 앱 업데이트와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 지정하면 해당 횟수 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1200회를 사용합니다. 이전 `--frames` 옵션은 `--steps` 없는 headless 실행의 횟수만 정하며, GUI 종료에는 영향을 주지 않습니다. `--steps`를 지정하면 `--frames`보다 우선하며 0과 음수는 허용하지 않습니다.

## 메시지 구조

`SampleMsg`는 `std_msgs/String my_string`과 `int64 my_num` 두 필드입니다. `my_string`은 문자열 자체가 아닌 중첩 메시지이므로 Python에서는 `message.my_string.data`에 씁니다. `my_num`은 부호 있는 64비트 정수입니다. ROS `.msg`는 Python 클래스만 만드는 파일이 아니며 DDS 직렬화와 C type support도 생성합니다.

## 준비와 두 종류의 빌드

Isaac Sim 5.1.0의 Python은 3.11입니다. Ubuntu 22.04의 Humble은 기본 3.10, Ubuntu 24.04의 Jazzy는 기본 3.12이므로 **시뮬레이터용**과 **외부 ROS용**을 각각 빌드합니다. 아래는 Ubuntu 22.04/Humble 기준이며 Docker와 ROS 개발 도구가 설치돼 있어야 합니다.

1. 이 패키지 폴더에서 절대 경로를 저장합니다.

   ```bash
   export LESSON_DIR="$PWD"
   export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
   git clone --branch IsaacSim-5.1.0 https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
   ```

2. 공식 workspace의 `humble_ws/src/custom_message`에는 같은 이름의 예제가 있으므로 **동시에 두 custom_message 패키지를 넣지 않습니다**. 이 실습을 위한 새 checkout에서 해당 패키지의 msg/CMakeLists.txt/package.xml을 로컬 파일로 교체하거나 내용이 일치하는지 확인합니다. 다른 패키지를 삭제하지 않습니다. 예:

   ```bash
   cp "$LESSON_DIR/ros_ws/src/custom_message/msg/SampleMsg.msg" "$ROS_WS_REPO/humble_ws/src/custom_message/msg/SampleMsg.msg"
   cd "$ROS_WS_REPO"
   git submodule update --init --recursive
   ./build_ros.sh -d humble -v 22.04
   ```

   이 명령은 Docker에서 Python 3.11 ROS 및 workspace를 빌드하므로 시간/디스크/네트워크가 필요합니다. Python 실행 파일 옵션 하나만 3.11로 바꾸는 것은 ROS type support의 ABI를 바꾸지 못합니다.
3. **깨끗한 시뮬레이터용 Bash**에서 시스템 `/opt/ros` 대신 아래 두 경로를 source합니다.

   ```bash
   export ISAAC_SIM="$HOME/isaacsim"
   export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
   source "$ROS_WS_REPO/build_ws/humble/humble_ws/install/local_setup.bash"
   source "$ROS_WS_REPO/build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash"
   export ROS_DOMAIN_ID=0
   export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
   # 이 패키지 폴더로 이동 후
   "$ISAAC_SIM/python.sh" run.py --number 23
   ```

4. 별도 **시스템 ROS 터미널**에서는 이 패키지 자체의 workspace를 빌드합니다.

   ```bash
   source /opt/ros/humble/setup.bash
   cd /absolute/path/to/this/package/ros_ws
   colcon build --packages-select custom_message
   source install/local_setup.bash
   export ROS_DOMAIN_ID=0
   ros2 interface show custom_message/msg/SampleMsg
   ros2 topic echo /custom_sample
   ```

   `my_string.data`와 `my_num: 23`이 실제 수신되어야 합니다. GUI는 창을 닫을 때까지 유지되므로 DDS discovery와 메시지 수신을 기다릴 수 있습니다. Jazzy는 `jazzy_ws`, `-d jazzy -v 24.04`와 `build_ws/jazzy/...`를 대응시킵니다.

## Script Editor 방식

위 Python 3.11 workspace 두 개를 source한 터미널에서 `"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge`로 시작합니다. **Window > Script Editor**에서 다음을 실행합니다.

```python
from custom_message.msg import SampleMsg
sample = SampleMsg()
sample.my_string.data = 'Isaac Sim custom type'
sample.my_num = 23
print(sample)
```

이 출력은 import/필드 대입 확인이며 DDS 수신 검증은 아닙니다. standalone `run.py`와 별도 echo를 사용하면 통신까지 확인합니다.

## API와 개념

`rosidl_generate_interfaces`는 `.msg`에서 언어별 인터페이스를 생성하고 `DEPENDENCIES std_msgs`는 중첩 타입을 찾아줍니다. `ament_export_dependencies`는 설치 후 소비자가 runtime 의존성을 찾도록 합니다. `create_publisher(SampleMsg, '/custom_sample', 10)`에서 10은 큐 깊이입니다. `publish`는 전송 요청이며 수신 보장이 아닙니다.

이 예제에는 USD 로봇이 없습니다. ROS 메시지 정의/언어 바인딩을 분리해서 배우기 위한 원문 범위이며, SimulationApp은 내부 ROS 브리지를 로드할 Kit 프로세스를 제공합니다.

## 한 가지 변수 실험과 문제 해결

`--number 24`로 다시 실행하고 echo의 정수만 바뀌는지 확인합니다. `.msg`의 필드를 바꾸는 실험은 **양쪽 빌드와 source를 모두 다시** 수행해야 합니다. `ModuleNotFoundError`는 workspace source/path를, `_rclpy_pybind11`/undefined symbol은 Python ABI와 기본 ROS 혼입을 확인합니다. 같은 이름의 message package가 두 workspace에서 서로 다른 정의로 설치되면 먼저 overlay 순서를 정리합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_message_python.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
