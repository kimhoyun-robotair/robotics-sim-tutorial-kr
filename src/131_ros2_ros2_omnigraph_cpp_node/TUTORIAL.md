# 131. ROS 2 Custom C++ OmniGraph Node

권장 학습 순서 **131** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t032`

**목표:** ROS C API를 쓰는 C++ OmniGraph 노드를 빌드해 사용자 정의 `tutorial_interfaces/msg/Sphere`를 발행합니다. Linux + ROS 2 Humble 전용 공식 workflow입니다. 로컬 파일은 **새로 작성한 Sphere 노드 구현/OGN, 메시지 패키지, 빌드 연결 도구**입니다. Kit 템플릿과 NVIDIA 예제 확장의 공통 plugin loader는 외부 빌드 전제입니다.


## 실행 전제와 원문 이름 정리

Isaac Sim 5.1.0, Ubuntu 22.04, ROS 2 Humble 개발 환경, C++17 toolchain, colcon, Kit Extension C++ template의 `release/107.3.0`가 필요합니다. 원문 본문에는 SphereMsg 언급도 있지만 실제 다운로드 예제는 `tutorial_interfaces/msg/Sphere`와 `sphere.h`를 사용합니다. 이 폴더는 실제 코드와 같은 **Sphere.msg**를 제공합니다.

## 1. 사용자 메시지 빌드

ROS용 Bash에서 이 패키지 폴더로 이동합니다.

```bash
export LESSON_DIR="$PWD"
source /opt/ros/humble/setup.bash
cd "$LESSON_DIR/ros_ws"
colcon build --packages-select tutorial_interfaces
source install/local_setup.bash
ros2 interface show tutorial_interfaces/msg/Sphere
```

출력에 `geometry_msgs/Point center`와 `float64 radius`가 있어야 합니다. 이 C++ workflow는 시스템 Humble의 **C 라이브러리**와 링크합니다. Python 메시지를 Isaac Sim에서 import하는 별도 workflow와 혼동하지 않습니다.

## 2. 정확한 외부 템플릿/샘플 준비

```bash
export KIT_TEMPLATE="$HOME/kit-extension-template-cpp-107.3"
git clone --branch release/107.3.0 https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp.git "$KIT_TEMPLATE"
cd "$KIT_TEMPLATE"
./build.sh
./_build/linux-x86_64/release/omni.app.kit.dev.sh
```

첫 빌드는 기본 Kit 개발 앱이 실행되는지 확인하는 단계입니다. 닫은 뒤 [5.1.0 공식 예제 확장 ZIP](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/5418eff6891a41d71ac8b5f687bf1cbd/omni.example.cpp.omnigraph_node_ros.zip)을 다운로드하여 `source/extensions/omni.example.cpp.omnigraph_node_ros`에 풉니다. 이 다운로드는 NVIDIA가 배포한 외부 소스이며 해당 사용 조건을 따릅니다. 이 패키지에 ZIP 원본을 재배포하지 않았습니다.

```bash
python3 "$LESSON_DIR/prepare_build.py"   --template "$KIT_TEMPLATE"   --ros-install /opt/ros/humble   --interface-install "$LESSON_DIR/ros_ws/install/tutorial_interfaces"
cd "$KIT_TEMPLATE"
./build.sh
```

도구는 원본 두 노드 파일과 packman XML을 `.original`로 백업한 후 local Sphere 노드와 절대 dependency 경로를 넣습니다. 동일 checkout에 반복 실행하면 기존 백업을 보존하기 위해 중단합니다. `premake5.lua`는 공식 예제 것을 사용하며 `system_ros`의 rcl/rmw/std_msgs/geometry_msgs와 `additional_ros`의 tutorial_interfaces include/lib 경로를 연결합니다. OGN 헤더는 이 빌드에서 생성되므로 시스템 `g++ nodes/ROS2CustomMessageNode.cpp` 하나로 컴파일되지 않습니다.

## 3. Isaac Sim에 빌드 결과 등록

**시스템 ROS를 source하지 않은 새 Bash**를 엽니다. 이 쉘에는 메시지 workspace의 local overlay만 추가합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export LESSON_DIR=/absolute/path/to/this/package
source "$LESSON_DIR/ros_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

**Window > Extensions > 메뉴 > Settings > Extension Search Paths**에 `$KIT_TEMPLATE/_build/linux-x86_64/release/exts`의 실제 절대 경로를 추가합니다. Third Party에서 **Custom ROS2 OGN Example Extension**을 Enable합니다. `libtutorial_interfaces__rosidl_typesupport_c.so`를 찾지 못하면 local_setup과 설치 lib 경로를 확인합니다. `/opt/ros/humble/setup.bash`를 여기에 source하면 Python3.10 경로가 섞일 수 있습니다.

## 4. 그래프와 수신 확인

1. 새 Stage에서 **Window > Graph Editors > Action Graph**를 열고 새 그래프를 만듭니다.
2. **On Playback Tick**, **ROS2 Publish Custom Message**, **ROS2 Publish String**를 추가합니다. Tick→두 ROS 노드 Exec In으로 연결합니다.
3. Custom Message의 Publish Center를 `(1,2,3)`, Publish Radius를 `0.5`로 설정합니다. Play합니다.
4. 시스템 ROS 터미널에서 메시지 workspace를 source한 후 확인합니다.

   ```bash
   ros2 topic echo /custom_node/sphere_msg
   ros2 topic echo /custom_node/my_string
   ```

5. Sphere center/radius가 GUI 입력과 같은지 확인합니다. 로컬 노드의 `publishedCount`는 `rcl_publish`가 성공한 횟수이지 DDS 수신 확인 횟수가 아닙니다. echo 결과도 함께 확인합니다.

## C++/USD 개념과 실험

`rcl_init`는 context, `rcl_node_init`는 ROS node, `rcl_publisher_init`는 publisher를 초기화합니다. `ROSIDL_GET_MSG_TYPE_SUPPORT`는 Sphere 직렬화/type support를 연결합니다. `db.internalState`는 graph instance에 수명을 묶고 `compute()`가 Tick마다 최신 OGN 입력을 메시지에 옮깁니다. `releaseInstance`와 destructor는 publisher→node→context 역순으로 정리합니다. ROS 메시지 init/fini는 발행 실패 때도 균형을 맞춥니다.

Sphere 메시지는 형상을 설명하는 **데이터**입니다. 이 예제가 USD sphere prim을 자동 생성하는 것은 아닙니다. USD Stage는 그래프와 입력 값을 저장하고 ROS consumer는 center/radius를 별도로 해석합니다.

한 가지 변수 실험으로 radius만 0.5→0.8로 바꿔 echo가 바뀌는지 확인합니다. 음수 radius는 로컬 구현이 거절합니다. 컴파일 중 header를 못 찾으면 message 빌드→packman 절대 경로→premake include 순서로 확인합니다. 노드가 검색되지 않으면 extension 활성화와 빌드 경로를 봅니다. 본 작업에서는 ROS/Kit C++ 빌드 환경을 실행하지 않아 컴파일/동적 로딩/통신은 아직 검증하지 않았습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_omnigraph_cpp_node.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
