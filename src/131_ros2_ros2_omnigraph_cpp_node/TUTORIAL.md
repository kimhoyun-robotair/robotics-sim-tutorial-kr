# 131. C++ OmniGraph 노드에서 사용자 ROS 메시지 발행하기

## 이번에 배우는 것

**그래프의 중심·반지름 입력을 Sphere 메시지로 보내는 C++ 노드를 빌드하고, 발행 횟수와 외부 수신값을 비교합니다.**

Python 노드와 달리 C++ 노드는 컴파일된 확장을 Isaac Sim에 로드해야 합니다. 사용자 메시지의 헤더와 타입 지원 라이브러리, OGN에서 생성한 데이터베이스 헤더도 빌드에 연결해야 합니다. 이번에는 작은 메시지 하나로 이 연결을 따라갑니다.

| 로컬 파일 | 맡는 일 | 따로 필요한 것 |
|---|---|---|
| `ros_ws/src/tutorial_interfaces` | `Sphere.msg` 인터페이스 정의 | ROS colcon 빌드 |
| `nodes/ROS2CustomMessageNode.ogn` | 중심·반지름 입력과 발행 횟수 출력 | OGN 코드 생성 |
| `nodes/ROS2CustomMessageNode.cpp` | ROS C API로 메시지 발행 | ROS 헤더·라이브러리 |
| `prepare_build.py` | 로컬 소스와 외부 빌드 경로 연결 | Kit 템플릿과 공식 샘플 확장 |

**이 실습은 공식 5.1 C++ 샘플이 지정한 Ubuntu 22.04/ROS 2 Humble 환경에서 진행합니다.** 저장소의 기본 Ubuntu 24.04/Jazzy 예시와 다른 예외입니다. 배포판 이름만 바꾸어 이 C++ 샘플을 검증된 Jazzy 절차로 취급하지 않습니다.

## 1. 메시지와 외부 C++ 확장 빌드하기

Linux, Isaac Sim 5.1.0, 지원 GPU, Humble 개발 환경, C++17 도구와 `colcon`이 필요합니다. 저장소 루트의 Bash에서 실습 경로를 보관하고 메시지를 빌드하세요.

```bash
export LESSON_DIR="$PWD/src/131_ros2_ros2_omnigraph_cpp_node"
source /opt/ros/humble/setup.bash
cd "$LESSON_DIR/ros_ws"
colcon build --packages-select tutorial_interfaces
source install/local_setup.bash
ros2 interface show tutorial_interfaces/msg/Sphere
```

출력 정의는 다음과 같습니다.

```text
geometry_msgs/Point center
float64 radius
```

이번 C++ 코드는 시스템 Humble의 **C 라이브러리**와 연결합니다. 129번처럼 사용자 메시지를 Isaac Sim Python에 import하기 위한 Python 3.11 빌드와는 준비 방식이 다릅니다.

공식 문서가 지정한 Kit 템플릿을 새 위치에 준비하고 기본 개발 앱까지 확인합니다.

```bash
export KIT_TEMPLATE="$HOME/kit-extension-template-cpp-107.3"
git clone --branch release/107.3.0 https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp.git "$KIT_TEMPLATE"
cd "$KIT_TEMPLATE"
./build.sh
./_build/linux-x86_64/release/omni.app.kit.dev.sh
```

개발 앱을 닫고 [5.1 공식 ROS C++ 샘플 ZIP](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/5418eff6891a41d71ac8b5f687bf1cbd/omni.example.cpp.omnigraph_node_ros.zip)을 다운로드하세요. 압축 안의 `omni.example.cpp.omnigraph_node_ros` 폴더를 템플릿의 `source/extensions/` 아래에 둡니다.

```bash
python3 "$LESSON_DIR/prepare_build.py" \
  --template "$KIT_TEMPLATE" \
  --ros-install /opt/ros/humble \
  --interface-install "$LESSON_DIR/ros_ws/install/tutorial_interfaces"
cd "$KIT_TEMPLATE"
./build.sh
```

### 설정에서 볼 부분

`prepare_build.py`는 외부 샘플의 두 노드 파일을 로컬 구현으로 교체하고 `deps/kit-sdk-deps.packman.xml`에 경로를 넣습니다.

| 의존성 연결 | 실제 내용 |
|---|---|
| `system_ros` | `/opt/ros/humble`의 include/lib |
| `additional_ros_workspace` → `additional_ros` | 빌드한 `tutorial_interfaces`의 include/lib를 가리키는 packman 의존성과 링크 이름 |
| 공식 `premake5.lua` | 이 경로를 사용하여 C++ 확장 빌드 |

원본 파일은 `.original`로 백업합니다. 반복 실행으로 백업을 덮어쓰지 않도록 이미 백업이나 의존성이 있으면 중단합니다. 기존 개발 checkout에서는 현재 변경을 먼저 확인하고, 새 실습 checkout에서 진행하는 편이 결과를 구분하기 쉽습니다.

### 실행 결과 확인하기

`Prepared local Sphere implementation...`은 **파일 배치와 경로 설정 완료**입니다. 컴파일 성공을 뜻하지 않습니다. 이어지는 `./build.sh`가 완료되어야 확장 바이너리가 만들어집니다. `ROS2CustomMessageNodeDatabase.h`는 이 빌드에서 생성되므로 C++ 파일 하나를 시스템 `g++`로 실행하는 방식은 아닙니다.

## 2. 확장을 로드하고 실제 Sphere 메시지 받기

**시스템 ROS를 source하지 않은 새 Bash**에서 저장소 루트로 이동합니다. 여기에는 메시지 워크스페이스의 local overlay만 추가합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export LESSON_DIR="$PWD/src/131_ros2_ros2_omnigraph_cpp_node"
source "$LESSON_DIR/ros_ws/install/local_setup.bash"
export ROS_DISTRO=humble
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Window > Extensions > 메뉴 > Settings > Extension Search Paths**에 `$HOME/kit-extension-template-cpp-107.3/_build/linux-x86_64/release/exts`의 실제 절대 경로를 추가합니다.
2. **Custom ROS2 OGN Example Extension**을 Enable합니다.
3. 새 Stage에서 **Window > Graph Editors > Action Graph**를 열고 그래프를 만듭니다.
4. **On Playback Tick**, **ROS2 Publish Custom Message**를 추가하고 Tick을 Exec In에 연결합니다.
5. Publish Center를 `(1,2,3)`, Publish Radius를 `0.5`로 설정하고 Play하세요.

메시지를 빌드했던 시스템 ROS 터미널에서 실행합니다.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /custom_node/sphere_msg
```

### 코드에서 볼 부분

`compute()`는 그래프 입력을 읽고 유한한 중심과 0 이상의 반지름인지 확인합니다. 최초 실행에서는 ROS Context, node, publisher를 준비합니다. 이후 발행의 핵심은 다음과 같습니다.

```cpp
message.center.x = center[0];
message.center.y = center[1];
message.center.z = center[2];
message.radius = radius;
const auto result = rcl_publish(&self.publisher, &message, nullptr);
```

`ROSIDL_GET_MSG_TYPE_SUPPORT(tutorial_interfaces, msg, Sphere)`는 이 메시지를 ROS가 직렬화할 때 사용할 타입 지원을 연결합니다. `.ogn`의 입력은 float이고 메시지 radius는 float64이므로, 메시지의 자료형이 더 넓어도 입력 단계의 정밀도가 자동으로 늘지는 않습니다.

`db.internalState`에는 그래프 인스턴스별 publisher와 횟수가 보관됩니다. 노드 해제 시 publisher → node → Context 순으로 정리합니다. 메시지 자체도 init/fini를 짝지어 처리합니다.

### 실행 결과 확인하기

echo에 center `(1,2,3)`, radius `0.5`가 나타나고 노드의 `publishedCount`가 증가하는지 확인하세요. 이 출력은 `rcl_publish`가 성공할 때 증가합니다. **발행 성공 횟수와 외부에서 받은 메시지 개수가 같다고 가정하지 않습니다.** DDS discovery, 수신 속도, 큐의 영향이 있으므로 echo도 함께 봅니다.

외부 공식 샘플의 문자열 노드도 비교하려면 Action Graph에 **ROS2 Publish String**을 추가하고 같은 Tick을 그 Exec In에 연결하세요. Play한 채 메시지 workspace를 source한 별도 ROS 터미널에서 `ros2 topic echo /custom_node/my_string`을 실행합니다. Sphere와 문자열 echo는 각각 다른 터미널에서 관찰한 뒤 Ctrl+C로 종료합니다.

Sphere는 중심과 반지름을 설명하는 데이터입니다. Viewport에 USD 구체를 만드는 노드는 아닙니다. 문자열 출력은 별도로 추가한 String 노드에서 나옵니다. echo는 Ctrl+C, 시뮬레이터는 창을 닫아 종료하세요.

## 3. 빌드 준비·발행·수신의 차이 정리

```text
Sphere.msg → ROS 헤더와 타입 지원 라이브러리
OGN + C++ + 외부 템플릿 → 컴파일된 확장
확장 로드 → 그래프 입력 → rcl_publish → DDS → 외부 echo
```

각 단계에는 다른 확인 기준이 있습니다. 준비 도구 출력은 파일 연결을, 확장 활성화는 로딩을, `publishedCount`는 로컬 발행을, echo는 수신값을 확인합니다. 어느 한 단계의 성공을 전체 과정의 성공으로 확대하지 않습니다.

## 4. 간단한 확인 실험

그래프에서 **Publish Radius만 0.5에서 0.8**로 바꾸어 보세요. 중심과 Tick 연결은 유지합니다.

외부 echo의 radius만 약 0.8로 바뀌어야 합니다. float 입력 변환 때문에 `0.8000000119...`처럼 보일 수 있습니다. 중심은 그대로이며 Viewport에 구체가 커지는 장면은 나타나지 않습니다. 이번 실험에서 바뀌는 것은 ROS 메시지의 값입니다.

## 실행할 때 막히면

- **`Missing prerequisite`**: 공식 샘플의 `premake5.lua`, packman XML, ROS include, 메시지 설치 lib 경로를 오류에 나온 순서대로 확인하세요.
- **`Backup exists`**: 같은 checkout에 준비 도구를 이미 실행했습니다. 백업을 지워 재실행하기 전에 현재 수정·빌드 상태를 확인하세요.
- **C++ 헤더를 못 찾음**: 메시지 빌드 완료와 두 의존성의 절대 경로를 확인하세요.
- **노드가 검색되지 않음**: 소스 폴더가 아니라 `_build/.../exts`를 등록했는지, 확장 활성화 로그에 오류가 없는지 확인하세요.
- **`libtutorial_interfaces...so`를 못 찾음**: 앱 터미널에 메시지 workspace의 `local_setup.bash`를 source했는지 확인하세요. `/opt/ros/humble/setup.bash` 전체를 추가하면 Python 버전 충돌이 생길 수 있습니다.
- **횟수가 멈추고 오류가 남음**: 중심의 유한성, 음수 반지름 여부를 확인하세요. 잘못된 입력은 발행 전에 거절합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Custom C++ OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_omnigraph_cpp_node.html)에 대응합니다. 공식 페이지의 Linux/Humble 지원 조건과 Kit `release/107.3.0` 지정을 따릅니다.

로컬 파일은 Sphere 구현·OGN·메시지 패키지·준비 도구입니다. Kit 템플릿과 공식 샘플의 공통 로더는 별도 다운로드해야 합니다. 이번 개정에서 ROS/Kit C++ 컴파일, 동적 로딩, 실제 통신은 수행하지 않았습니다. `tutorial.json`은 `verification: not_run`입니다.
