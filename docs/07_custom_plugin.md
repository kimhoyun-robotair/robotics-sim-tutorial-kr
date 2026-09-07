# 7. Gazebo ModelPlugin 직접 만들기

이 장에서는 Gazebo Classic 11 안에서 실행되는 C++ `ModelPlugin`을 살펴보고,
ROS 2 Humble 토픽으로 로봇의 이동 경로를 내보낸다. 완성할 플러그인은 Gazebo가 알고 있는 로봇의 실제
위치와 자세(pose)를 일정 주기로 누적해 `nav_msgs/msg/Path`로 발행한다. RViz에서 이
경로와 바퀴 오도메트리 경로를 겹쳐 보면 미끄러짐이나 잘못된 바퀴 반지름이
오도메트리에 어떤 오차를 만드는지 바로 확인할 수 있다.

> **버전 범위**
>
> 이 코드는 **Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic 11** 전용이다.
> Gazebo Classic은 [2025년 1월 지원이 종료되었다](https://github.com/ros-simulation/gazebo_ros_pkgs#deprecation). 기존 Humble 시스템을 학습하고
> 유지보수하기 위한 예제로 사용하고, 새 장기 프로젝트라면 최신 Gazebo의 System
> Plugin과 `ros_gz`로 옮기는 계획도 함께 세워야 한다.

[환경 설정](01_setup.md)을 마치고 이 저장소의 `Humble` 브랜치를
`~/robotics-sim-tutorial-kr`에 내려받았다고 가정한다. 먼저 7.5절에서 제공된 코드를
빌드하고 7.7절에서 실행해 본 뒤, 7.3~7.4절의 구현을 읽어도 좋다.
아래 C++·CMake 예제는 역할을 설명하기 위한 발췌 코드다. 파일 전체를 대체하지 말고
저장소의 완성된 소스와 대조한다.

## 7.1 무엇을 만들 것인가

이번 장에서 다루는 데이터 흐름은 다음과 같다.

1. Gazebo가 물리 계산을 갱신할 때 플러그인의 콜백을 호출한다.
2. 플러그인이 모델의 `WorldPose()`를 읽고 최근 2,000개 기록을 보관한다.
3. 보관한 기록을 하나의 `nav_msgs/msg/Path`로 발행한다.
4. RViz가 이 토픽을 구독해 이동 경로를 그린다.

플러그인 파일은 `ros2_ws/src/gazebo_tutorial_plugins`에 있다.

```text
gazebo_tutorial_plugins/
├── CMakeLists.txt
├── package.xml
├── include/gazebo_tutorial_plugins/
│   └── path_recorder_config.hpp
├── src/
│   └── ground_truth_path_plugin.cpp
├── test/
│   └── test_path_recorder_config.cpp
└── urdf/
    └── ground_truth_path_plugin.gazebo.xacro
```

플러그인 출력은 제어용 오도메트리로 사용하지 않는다. 두 경로의 역할을 먼저 구분해야 한다.

| 데이터 | 계산 근거 | 일반적인 용도 |
|---|---|---|
| 바퀴 오도메트리 | 바퀴 회전량과 로봇 기구학 | 로봇이 실전에서 추정할 수 있는 이동량, 제어·항법 입력 |
| 이번 플러그인의 참값 | Gazebo 물리 엔진의 모델 `WorldPose()` | 시뮬레이터 안에서만 아는 정답, 오도메트리 검증 |

참값을 항법 입력으로 사용하면 시뮬레이션 성능이 지나치게 좋아진다. 이
토픽은 알고리즘 검증과 디버깅에만 사용하고 실제 로봇으로 이식할 경로에는 넣지
않는다.

## 7.2 Gazebo 플러그인의 종류와 실행 위치

Gazebo Classic 플러그인은 접근하려는 대상에 따라 종류가 나뉜다.

| 종류 | 접근 범위 | 대표적인 쓰임 |
|---|---|---|
| `ModelPlugin` | 한 모델과 그 링크·조인트 | 구동, 모델 상태 관찰, 이번 실습 |
| `WorldPlugin` | 월드 전체 | 모델 생성, 전역 실험 제어 |
| `SensorPlugin` | 한 센서 | 센서 데이터 후처리, 노이즈 모델 |
| `SystemPlugin` | `gzserver` 프로세스 | 초기화와 전역 기능 |
| `VisualPlugin` | 화면에 그리는 시각 요소 | GUI에만 보이는 표현 변경 |
| `GUIPlugin` | Gazebo GUI | 패널과 사용자 인터페이스 |

이번 플러그인은 URDF에서 모델 전체에 붙는 `ModelPlugin`이다. 그래서 `Load()`가
받은 `gazebo::physics::ModelPtr`로 모델의 월드 좌표계에서의 위치와 자세를 직접 읽을 수 있다.

중요한 점은 플러그인이 별도 실행 파일이 아니라는 것이다. 빌드 결과인
`libground_truth_path_plugin.so`는 `gzserver`가 `dlopen()`으로 불러와 같은
프로세스 안에서 실행한다. 플러그인의 충돌이나 ABI 불일치는 Gazebo 서버 전체의
종료로 이어질 수 있다.

## 7.3 설정과 허용 범위

URDF의 `<plugin>` 아래에 다음 SDF 파라미터를 넣을 수 있다.

| 파라미터 | 기본값 | 제약과 의미 |
|---|---:|---|
| `update_rate` | `10.0` | 시뮬레이션 시간 기준 발행 주파수(Hz), 유한한 양수 |
| `topic` | `ground_truth_path` | ROS 2 토픽 이름, 상대 이름 권장 |
| `frame` | `world` | `Path.header.frame_id`. 좌표 변환 기능이 없으므로 `world`만 허용 |
| `max_points` | `2000` | 최근에 보관할 위치와 자세 수, 양의 정수 |

### 기본값과 유효성 규칙

표의 값은 문서에만 적어 둔 값이 아니라
`include/gazebo_tutorial_plugins/path_recorder_config.hpp`의 실제 기본값이다. 같은 구조체가
값의 범위도 검사하므로 URDF와 C++ 사이의 기본값과 허용 범위를 한 곳에서 관리한다.

```cpp
struct PathRecorderConfig
{
  double update_rate{10.0};
  std::string topic{"ground_truth_path"};
  std::string frame{"world"};
  std::size_t max_points{2000U};

  [[nodiscard]] bool IsValid() const noexcept
  {
    return std::isfinite(update_rate) && update_rate > 0.0 &&
           !topic.empty() && frame == "world" && max_points > 0U;
  }

  [[nodiscard]] std::chrono::nanoseconds PublishPeriod() const noexcept
  {
    using Nanoseconds = std::chrono::nanoseconds;
    using Rep = Nanoseconds::rep;
    constexpr long double kNanosecondsPerSecond = 1'000'000'000.0L;

    const long double count = kNanosecondsPerSecond /
      static_cast<long double>(update_rate);
    if (count >= static_cast<long double>(std::numeric_limits<Rep>::max())) {
      return Nanoseconds::max();
    }
    if (count <= 1.0L) {
      return Nanoseconds{1};
    }
    return Nanoseconds{static_cast<Rep>(count)};
  }
};
```

`PublishPeriod()`는 Hz를 나노초 주기로 변환하고 극단적으로 큰 주파수도 최소 1 ns로
제한한다. 이 주기를 `SimulationRateGate`에 전달해 물리 계산 단계 수가 아닌 시뮬레이션 시간을 기준으로 발행한다.

### SDF 파라미터 파싱

Gazebo는 URDF의 `<gazebo><plugin>...</plugin></gazebo>` 블록을 생성 과정에서 SDF로
변환한다. 따라서 `ModelPlugin::Load()`의 두 번째 인자는 `sdf::ElementPtr`이다. 실제
`ReadConfig()`는 요소가 있을 때만 덮어쓰고, 생략한 값에는 구조체 기본값을 유지한다.

```cpp
static gazebo_tutorial_plugins::PathRecorderConfig ReadConfig(
  const sdf::ElementPtr & sdf)
{
  gazebo_tutorial_plugins::PathRecorderConfig config;

  if (sdf->HasElement("update_rate")) {
    config.update_rate = sdf->Get<double>("update_rate");
  }
  if (sdf->HasElement("topic")) {
    config.topic = sdf->Get<std::string>("topic");
  }
  if (sdf->HasElement("frame")) {
    config.frame = sdf->Get<std::string>("frame");
  }
  if (sdf->HasElement("max_points")) {
    const int max_points = sdf->Get<int>("max_points");
    config.max_points = max_points > 0 ? static_cast<std::size_t>(max_points) : 0U;
  }

  return config;
}
```

`sdf->Get<T>()`의 템플릿 타입은 XML 텍스트를 변환할 C++ 타입이다. `max_points`를 먼저
부호 있는 정수로 읽는 이유는 `-1`을 큰 `std::size_t`로 바꾸지 않고 잘못된 값으로
거부하기 위해서이다. `Load()`는 실제로 다음 순서로 파싱과 유효성 검사를 수행한다.

```cpp
gazebo_tutorial_plugins::PathRecorderConfig config;
try {
  config = ReadConfig(sdf);
} catch (const std::exception & error) {
  gzerr << "[GroundTruthPathPlugin] SDF 파라미터 읽기에 실패한다: "
        << error.what() << "\n";
  return;
}
if (!config.IsValid()) {
  gzerr << "[GroundTruthPathPlugin] 잘못된 설정이다: update_rate="
        << config.update_rate << ", topic='" << config.topic
        << "', frame='" << config.frame << "', max_points="
        << config.max_points << ". 플러그인을 시작하지 않는다.\n";
  return;
}
```

변환 예외나 범위 오류가 발생하면 `gzerr`를 남긴 뒤 플러그인 초기화를 중단한다. 모델
자체는 생성되지만 `/ground_truth_path`는 생기지 않으므로 Gazebo 서버 로그를 함께
확인해야 한다.

`frame`은 좌표 변환 기능이 아니라 메시지에 붙이는 좌표계 이름이다. 코드는
`WorldPose()`를 그대로 넣으므로 `world`만 허용한다. 실제 변환 없이
`frame`만 `odom`이나 `map`으로 바꾸면 숫자와 좌표계가 맞지 않는 메시지가 된다.
이런 설정은 초기화 단계에서 거부한다.

`<ros>` 블록은 `gazebo_ros::Node`가 해석한다. 예를 들어 `topic`을 상대 이름으로
두고 네임스페이스를 `/diffbot`으로 지정하면 실제 토픽은
`/diffbot/ground_truth_path`가 된다. 여러 로봇을 띄울 때는 로봇마다 네임스페이스를
다르게 지정한다.

## 7.4 구현 읽기

### ModelPlugin 수명 주기

Gazebo Classic이 호출하는 순서를 먼저 알면 각 코드가 필요한 이유를 이해하기 쉽다.

| 단계 | 호출 시점 | 이 플러그인의 작업 |
|---|---|---|
| 생성자 | 공유 라이브러리에서 인스턴스를 만들 때 | 콜백과 분리해 둘 상태 객체를 생성한다 |
| `Load(model, sdf)` | URDF/SDF 모델을 월드에 삽입할 때 한 번 | 설정 파싱, ROS 노드·발행자 생성, 갱신 이벤트 연결을 수행한다 |
| `OnUpdate(state, info)` | 물리 엔진의 `WorldUpdateBegin`마다 반복 | 설정한 발행 간격이 지나면 모델의 위치와 자세를 Path에 추가한다 |
| 소멸자 | 모델 제거 또는 `gzserver` 종료 시 | 콜백을 비활성화하고 이벤트·ROS·Gazebo 자원을 해제한다 |

`Load()`가 성공하기 전에는 갱신 콜백을 연결하지 않는다. 반대로 종료할 때는 먼저
`active=false`로 바꾸고 이벤트 연결을 끊은 뒤 상태를 해제한다. 이 순서가 로딩 실패와
종료 중 콜백 경합을 모두 막는다.

### ModelPlugin 등록

`src/ground_truth_path_plugin.cpp`의 클래스는 `gazebo::ModelPlugin`을 상속하고
마지막에 다음 매크로로 등록한다.

```cpp
class GroundTruthPathPlugin final : public ModelPlugin
```

공유 라이브러리 끝에서는 실제 등록 매크로를 호출한다.

```cpp
GZ_REGISTER_MODEL_PLUGIN(GroundTruthPathPlugin)
```

이 매크로가 Gazebo의 플러그인 팩터리 심볼을 공유 라이브러리에 만든다. 클래스만
작성하고 등록 매크로를 빼면 라이브러리는 발견되더라도 인스턴스를 만들 수 없다.

실제 소스는 생성자, 소멸자, `Load()`, 상태와 이벤트 연결 멤버를 이 클래스에
구현한다.

### ROS 2 노드와 발행자 생성

`Load()`는 모델이 삽입될 때 한 번 호출된다. 직접 `rclcpp::init()`을 호출하거나
콜백 처리를 위한 별도 스레드를 만드는 대신 실제 소스에서 다음 API를 사용한다.

```cpp
auto ros_node = gazebo_ros::Node::Get(sdf);
if (!ros_node) {
  gzerr << "[GroundTruthPathPlugin] gazebo_ros::Node 생성에 실패한다. "
        << "같은 namespace에 중복된 plugin name이 있는지 확인해야 한다.\n";
  return;
}
auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();
auto publisher = ros_node->create_publisher<nav_msgs::msg::Path>(config.topic, qos);
```

`gazebo_ros::Node::Get()`은 `<ros>`의 네임스페이스와 이름 재지정을 적용하고 노드를
`gazebo_ros`가 관리하는 공용 실행기에 등록한다. 이번 플러그인은 발행만 하므로
사용자 스레드나 `spin_some()`이 필요 없다.

발행자는 `reliable + transient_local`이다. 따라서 RViz를 늦게 켜도 마지막으로
완성된 Path를 바로 받을 수 있다. 전체 Path 메시지 하나만 보관하도록 저장 개수(depth)는
1로 제한했다.

### 물리 갱신 이벤트와 시뮬레이션 시간

`Load()`의 마지막 단계에서 월드 갱신 이벤트를 연결한다.

```cpp
update_connection_ = event::Events::ConnectWorldUpdateBegin(
  [weak_state](const common::UpdateInfo & info) {
    if (const auto locked_state = weak_state.lock()) {
      GroundTruthPathPlugin::OnUpdate(*locked_state, info);
    }
  });
```

`OnUpdate()`는 Gazebo의 물리 갱신 스레드에서 실행된다. 발행 주기와 메시지 시각은
컴퓨터의 실제 시계나 `std::chrono::steady_clock`이 아니라
`gazebo::common::UpdateInfo::simTime`을 사용한다. 따라서 다음 동작이 자연스럽다.

- Gazebo를 일시 정지하면 새 위치와 자세가 쌓이지 않는다.
- 실시간 비율(RTF)이 1보다 작거나 커도 시뮬레이션 시간 기준 발행 간격을 유지한다.
- `/reset_simulation`으로 시간이 뒤로 가면 기존 Path를 비우고 새 시간축에서 다시
  시작한다.

각 `PoseStamped`와 Path 헤더에는 같은 Gazebo 시뮬레이션 시각이 들어간다. `/clock`
콜백의 도착 순서에 의존하는 `ros_node_->now()`를 사용하지 않은 이유다.

월드 좌표계에서의 위치와 자세를 ROS 메시지로 옮겨 발행하는 실제 핵심 코드는 다음과 같다.

```cpp
const auto world_pose = state.model->WorldPose();
geometry_msgs::msg::PoseStamped pose;
pose.header.frame_id = state.config.frame;
pose.header.stamp.sec = static_cast<std::int32_t>(info.simTime.sec);
pose.header.stamp.nanosec = static_cast<std::uint32_t>(info.simTime.nsec);
pose.pose.position.x = world_pose.Pos().X();
pose.pose.position.y = world_pose.Pos().Y();
pose.pose.position.z = world_pose.Pos().Z();
pose.pose.orientation.x = world_pose.Rot().X();
pose.pose.orientation.y = world_pose.Rot().Y();
pose.pose.orientation.z = world_pose.Rot().Z();
pose.pose.orientation.w = world_pose.Rot().W();

if (state.path.poses.size() >= state.config.max_points) {
  state.path.poses.erase(state.path.poses.begin());
}
state.path.poses.emplace_back(std::move(pose));
state.path.header.frame_id = state.config.frame;
state.path.header.stamp = state.path.poses.back().header.stamp;
state.path_publisher->publish(state.path);
```

위치와 쿼터니언은 Gazebo `ignition::math::Pose3d`의 각 성분을 ROS 메시지에 그대로
대응한다.

### 유한한 메모리 사용

갱신할 때마다 무한히 위치와 자세를 누적하면 장시간 시뮬레이션에서 메모리와 DDS 직렬화
비용이 계속 증가한다. 이 구현은 `max_points`를 넘기기 직전에 가장 오래된 점을
제거한다.

```cpp
if (state.path.poses.size() >= state.config.max_points) {
  state.path.poses.erase(state.path.poses.begin());
}
state.path.poses.emplace_back(std::move(pose));
```

기본값은 2,000점이다. 10 Hz라면 최근 200초를 표시한다. 더 긴 실험에서는 무작정
수를 늘리기보다 발행 주파수를 낮추거나 별도의 rosbag에 `PoseStamped`를 저장하는
편이 효율적이다.

### 수명 주기와 스레드 안전성

ROS 실행기와 Gazebo 물리 계산 스레드가 같은 객체를 동시에 만질 수 있으므로 수명
종료 순서가 중요하다. 구현은 다음 순서를 지킨다.

1. 콜백은 플러그인의 `this` 대신 `weak_ptr<GroundTruthPathState>`를 캡처한다.
2. 콜백 시작 시 `weak_ptr::lock()`에 성공한 경우에만 상태를 사용한다. 이미 시작한
   콜백은 그 `shared_ptr`로 상태 수명을 끝까지 유지한다.
3. 소멸자는 원자 변수인 `active`를 `false`로 만들고 `event::ConnectionPtr`을 해제한다.
4. 뮤텍스 잠금을 얻은 뒤 발행자, ROS 노드, 모델 포인터를 해제한다.

실제 소멸자는 이 순서를 다음과 같이 구현한다.

```cpp
~GroundTruthPathPlugin() override
{
  auto state = std::move(state_);
  if (!state) {
    return;
  }

  state->active.store(false, std::memory_order_release);
  update_connection_.reset();

  std::lock_guard<std::mutex> lock(state->mutex);
  state->path_publisher.reset();
  state->ros_node.reset();
  state->model.reset();
}
```

`OnUpdate()`도 뮤텍스 잠금 바깥과 안에서 `active`를 두 번 확인한다. 소멸자가 먼저
잠금을 얻거나 이벤트 처리 시스템에 콜백 호출이 남아 있어도 플러그인 객체의 해제된
메모리를 참조하지 않는다. 이 패턴은 나중에 ROS 구독자나 서비스를 추가할 때
특히 중요하다. ROS 콜백에서 Gazebo 모델을 직접 수정하기보다는 명령을 뮤텍스로
보호한 변수나 대기열에 넣고, 다음 물리 갱신에서 적용하는 구조가 안전하다.

## 7.5 빌드와 단위 테스트

### CMake에서 ModelPlugin 공유 라이브러리 만들기

Gazebo가 `dlopen()`할 대상은 실행 파일이 아니라 `SHARED` 공유 라이브러리이다. 저장소의
`CMakeLists.txt`는 실제로 다음 대상을 만들고 필요한 ROS 2·Gazebo 의존성을 연결한다.

```cmake
find_package(ament_cmake REQUIRED)
find_package(gazebo_dev REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)

link_directories(${gazebo_dev_LIBRARY_DIRS})

add_library(ground_truth_path_plugin SHARED
  src/ground_truth_path_plugin.cpp
)
target_include_directories(ground_truth_path_plugin
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(ground_truth_path_plugin
  gazebo_dev
  gazebo_ros
  geometry_msgs
  nav_msgs
  rclcpp
)
```

대상 이름이 `ground_truth_path_plugin`이므로 Linux 빌드 결과 이름은
`libground_truth_path_plugin.so`가 된다. 이는 뒤에서 URDF `<plugin filename>`에 적는
이름과 정확히 일치해야 한다. 설치 규칙은 라이브러리와 Xacro 매크로를 각각 `lib`와 패키지
공유 자원 경로에 배치한다.

```cmake
install(
  TARGETS ground_truth_path_plugin
  EXPORT export_ground_truth_path_plugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(
  DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

ament_export_targets(export_ground_truth_path_plugin HAS_LIBRARY_TARGET)
ament_export_dependencies(gazebo_dev gazebo_ros geometry_msgs nav_msgs rclcpp)
ament_package()
```

### 의존성 설치와 빌드

의존 패키지를 설치한다. 이미 설치했다면 `apt`는 변경 없이 끝난다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-nav-msgs \
  ros-humble-ament-cmake-gtest
```

작업 공간에서 의존성을 확인하고 전체 패키지를 빌드한다. 뒤의 실행 실습에는
플러그인뿐 아니라 로봇 설명·실행·보조 노드 패키지도 필요하기 때문이다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --event-handlers console_direct+
source install/setup.bash
```

### 빌드 결과 확인

빌드 로그 끝의 `Summary`에 실패한 패키지가 없는지 확인한다. 다음 명령에서
첫 번째 출력은 이 작업 공간의 설치 경로, 두 번째 출력은 `.so` 파일의 경로여야 한다.

```bash
ros2 pkg prefix gazebo_tutorial_plugins
find "$(ros2 pkg prefix gazebo_tutorial_plugins)/lib" \
  -maxdepth 1 -name 'libground_truth_path_plugin.so' -print
```

### 단위 테스트

단위 테스트는 Gazebo GUI를 띄우지 않고 설정과 시간 간격 검사의 순수 C++ 부분을 검사한다.

```bash
colcon test --packages-select gazebo_tutorial_plugins \
  --event-handlers console_direct+
colcon test-result --verbose
```

테스트가 보장하는 조건은 다음과 같다.

- 기본 설정은 10 Hz, 즉 100 ms 주기다.
- 0 Hz, NaN, 빈 토픽, `world`가 아닌 프레임, 0개의 최대 점 수는 거부한다.
- 물리 갱신 콜백 횟수가 아니라 시뮬레이션 시간 간격으로 발행한다.
- 시뮬레이션 시간이 뒤로 가면 초기화 직후 위치와 자세를 즉시 발행한다.

이 테스트는 Gazebo에서 로봇을 실제로 실행하는 통합 검사를 대체하지 않는다. 실제 Humble
환경에서는 다음 절의 토픽과 RViz 확인까지 수행해야 플러그인 로딩과 메시지 조건을
확인했다고 할 수 있다.

## 7.6 URDF/Xacro에 삽입하기

### URDF에 직접 넣기

직접 만든 로봇에 붙일 때는 URDF의 최상위 `<robot>` 안, 닫는 `</robot>` 앞에 다음
블록을 추가한다. 저장소의 기본 로봇에는 이미 연결되어 있으므로 중복으로 넣지 않는다. 특정 링크에 붙이는 센서 플러그인과 달리 `reference` 속성은 없다.

```xml
<gazebo>
  <plugin name="ground_truth_path" filename="libground_truth_path_plugin.so">
    <ros>
      <namespace>/diffbot</namespace>
    </ros>
    <update_rate>10.0</update_rate>
    <topic>ground_truth_path</topic>
    <frame>world</frame>
    <max_points>2000</max_points>
  </plugin>
</gazebo>
```

이 설정의 최종 토픽은 `/diffbot/ground_truth_path`다. `<topic>`에 처음부터 `/`로
시작하는 절대 이름을 쓰면 네임스페이스를 우회하므로 다중 로봇 실습에서는 상대 이름을
권장한다.

이름 재지정도 사용할 수 있다.

```xml
<ros>
  <namespace>/diffbot</namespace>
  <remapping>ground_truth_path:=truth_path</remapping>
</ros>
```

이 경우 최종 토픽은 `/diffbot/truth_path`다. `topic` SDF 파라미터와 이름 재지정을
동시에 자주 바꾸면 추적하기 어려우므로, 팀 프로젝트에서는 한 방식을 정해 사용한다.

### 제공된 Xacro 매크로 사용하기

여러 로봇에 같은 `<plugin>` 블록을 복사하면 토픽이나 기본값을 바꿀 때 파일마다 수정해야
한다. 저장소는 플러그인 패키지의
`urdf/ground_truth_path_plugin.gazebo.xacro`에 다음 매크로를 별도 파일로 둔다.

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:macro
    name="ground_truth_path_plugin"
    params="ros_namespace:='/' topic:='ground_truth_path' frame:='world' update_rate:=10.0 max_points:=2000">
    <gazebo>
      <plugin name="ground_truth_path" filename="libground_truth_path_plugin.so">
        <ros>
          <namespace>${ros_namespace}</namespace>
        </ros>
        <update_rate>${update_rate}</update_rate>
        <topic>${topic}</topic>
        <frame>${frame}</frame>
        <max_points>${max_points}</max_points>
      </plugin>
    </gazebo>
  </xacro:macro>
</robot>
```

설명 패키지의 로봇 Xacro는 구현을 복사하지 않고 파일을 포함한 뒤 필요한 값만
인자로 전달한다. `diffbot.urdf.xacro`도 같은 파일 포함 방식과 매크로 호출 방식을 사용한다.

```xml
<xacro:include
  filename="$(find gazebo_tutorial_plugins)/urdf/ground_truth_path_plugin.gazebo.xacro"/>

<xacro:ground_truth_path_plugin
  ros_namespace="/diffbot"
  topic="ground_truth_path"
  frame="world"
  update_rate="10.0"
  max_points="2000"/>
```

`xacro:include`는 매크로 정의를 읽을 뿐 플러그인을 자동으로 추가하지 않는다. 반드시
`<xacro:ground_truth_path_plugin .../>`을 `<robot>` 안에서 호출해야 최종 URDF에
`<gazebo><plugin>`이 생성된다. 로봇마다 네임스페이스와 토픽만 다르게 전달하면 같은 매크로를
재사용할 수 있다.

### 생성된 URDF 확인

이 저장소의 로봇에는 매크로가 이미 들어 있다. 위 XML은 구조 설명용이므로
같은 플러그인을 한 번 더 추가하지 않는다. 다음 명령을 작업 공간에서 실행해
실제 URDF에 들어간 설정을 확인한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
xacro src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro \
  > /tmp/diffbot.urdf
rg -n -A12 'libground_truth_path_plugin.so' /tmp/diffbot.urdf
```

`filename="libground_truth_path_plugin.so"`, `<frame>world</frame>`,
`<topic>ground_truth_path</topic>`이 보여야 한다. 기본 로봇은 루트 네임스페이스를
사용하므로 최종 출력 토픽은 `/ground_truth_path`다. 앞서 소개한 `/diffbot`은
네임스페이스 설정을 설명하기 위한 별도 예다.

소스나 Xacro를 수정했다면 실행 중인 시뮬레이션을 `Ctrl+C`로 종료하고 다시 빌드한다.
플러그인은 로봇 생성 시 한 번 읽히므로 파일만 저장해도 실행 중인 로봇에 반영되지는 않는다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 7.7 토픽 확인과 RViz 시각화

### 실행

첫 번째 터미널에서 플러그인을 포함한 diffbot과 기본 RViz 설정을 함께 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py rviz:=true
```

두 번째 터미널에서 ROS 환경을 불러오고 직진 명령을 보낸다. 기본 모델은
명령 발행을 끝내도 마지막 속도를 계속 사용할 수 있으므로 정지 명령까지 실행한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 topic pub --rate 10 --times 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.15}, angular: {z: 0.0}}"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

로봇이 잠깐 전진한 뒤 멈추고, RViz의 빨간색·초록색 경로가 늘어나면 정상이다.
발행 횟수는 실제 시간 기준이므로 컴퓨터 부하가 크면 이동 거리는 달라질 수 있다.

### 토픽 이름·자료형·발행 상태 확인

같은 두 번째 터미널에서 아래 명령을 한 줄씩 실행한다.

```bash
ros2 topic list -t | rg 'ground_truth_path|wheel_odom_path'
ros2 topic info /ground_truth_path --verbose
ros2 topic echo /ground_truth_path --once --field header \
  --qos-reliability reliable --qos-durability transient_local
ros2 topic hz /ground_truth_path
```

두 경로의 자료형은 `nav_msgs/msg/Path`여야 한다. 참값 경로의 헤더에는
`frame_id: world`가, 토픽 상세 정보에는 `RELIABLE`과 `TRANSIENT_LOCAL`이 나타난다.
`hz` 명령은 계속 실행되므로 측정값이 나오면 `Ctrl+C`로 종료한다.
플러그인은 **시뮬레이션 시간 기준 10 Hz**로 발행한다. `ros2 topic hz`는 기본적으로
실제 경과 시간으로 측정하므로 RTF가 0.5라면 약 5 Hz로 보일 수 있다.
일시 정지 상태에서는 새 메시지가 오지 않아 주파수도 표시되지 않을 수 있다.

### RViz를 수동으로 구성하기

기본 실행 파일은 RViz를 자동으로 실행한다. 플러그인을 다른 실행 구성에 붙여 RViz가 열리지
않은 경우에는 다음 명령으로 별도 실행한다.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

RViz에서 다음과 같이 설정한다.

1. **Global Options → Fixed Frame**을 `world`로 설정한다.
2. **Add → By display type → Path**를 선택한다.
3. Path의 **Topic**을 `/ground_truth_path`로 지정한다.
4. 잘 보이도록 Line Style, Line Width, Color를 조정한다.

기본 `diffbot.launch.py`가 연 RViz에는 빨간색 Ground Truth Path와 초록색 Wheel Odom
Path가 이미 등록되어 있다. 이 설정의 Fixed Frame은 `odom`이며 실행 파일이 로봇의 초기
위치와 방향을 반영한 `world → odom` 고정 TF도 함께 제공한다. 위 수동 설정은 플러그인만
다른 실행 구성에 붙였을 때 사용한다.

발행자가 `transient_local`이므로 RViz를 나중에 실행해도 마지막 Path가 나타난다.
나타나지 않으면 Path 표시 항목의 Reliability를 `Reliable`, Durability를
`Transient Local`로 맞추고 RViz를 다시 연다.

### 바퀴 오도메트리와 참값 겹쳐 보기

기본 실행 파일은 `odom_to_path` 노드를 이미 시작한다. 따라서 기본 실습에서는
아래 명령을 추가로 실행하지 않는다. **직접 만든 실행 구성에 이 노드가 없을 때만**
새 터미널에서 ROS 환경을 불러온 뒤 실행한다. 같은 노드와 토픽을 중복 실행하면
경로가 번갈아 표시되어 원인을 찾기 어려워진다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 run gazebo_tutorial_tools odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_points:=2000
```

RViz에 Path 표시 항목을 하나 더 추가해 `/wheel_odom_path`를 다른 색으로
표시한다. 비교 전에 다음 두 가지를 확인한다.

- 차동 구동 플러그인의 `/odom`이 Gazebo 월드 좌표계에서의 위치와 자세가 아니라 바퀴 엔코더
  적분을 사용해야 의미 있는 비교가 된다.
- 바퀴 Path의 `header.frame_id`가 `odom`이라면 RViz가 `world`에서 `odom`으로 가는
  올바른 TF를 알아야 한다.

기본 실행 파일은 인자 `x`, `y`, `yaw`를 반영한 `world → odom` 고정 TF를
자동으로 발행한다. 이미 다른 노드가 이 TF를 소유한다면 중복 발행을 피한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  publish_world_odom_tf:=false
```

직접 구성한 실습에서 로봇을 월드 원점, yaw 0으로 생성했고 `odom` 원점도 그
위치와 정확히 일치할 때만 아래의 고정 TF를 사용할 수 있다. 이동과 회전이 모두 0인 변환이다.

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 --roll 0 --pitch 0 --yaw 0 \
  --frame-id world --child-frame-id odom
```

생성 위치와 자세나 odom 초기점이 다르면 위 명령을 그대로 쓰면 안 된다. 실제 두 좌표계의
변환을 계산해 넣거나 공통 좌표계로 위치와 자세를 변환하는 노드를 사용한다. 프레임 이름만
같게 바꿔서는 좌표 변환이 되지 않는다.

미끄러운 바닥에서 급회전하거나 바퀴 반지름을 일부러 조금 틀리게 설정하면 두
Path가 점점 벌어진다. 이 차이가 바퀴 오도메트리의 누적 오차다. 실습을 마치면 직접 실행한 보조 노드와
첫 번째 터미널의 실행을 각각 `Ctrl+C`로 종료한다.

## 7.8 공유 라이브러리와 `GAZEBO_PLUGIN_PATH`

URDF의 `filename="libground_truth_path_plugin.so"`는 실행 파일 경로를 뜻하지 않는다.
Gazebo는 `GAZEBO_PLUGIN_PATH`에 등록된 디렉터리를 차례로 검색해 이 파일을 찾는다.

이 패키지의 `package.xml`에는 다음 설정이 필요하다. 아래는 `<export>` 부분만
발췌한 예제다.

```xml
<export>
  <build_type>ament_cmake</build_type>
  <gazebo_ros plugin_path="${prefix}/../../lib" />
</export>
```

여기서 `${prefix}`는 `ros2 pkg prefix`가 출력하는 설치 루트가 아니라
`<설치 루트>/share/gazebo_tutorial_plugins`다. 따라서 `../../lib`로 올라가야
빌드한 `.so`가 설치된 `<설치 루트>/lib`를 가리킨다. 또한 이 속성의 이름은
**`plugin_path`**다. `gazebo_plugin_path`로 적으면 Humble의 경로 검색 코드가
읽지 않는다. 이는 [공식 `gazebo_ros_paths.py` 구현](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_ros/scripts/gazebo_ros_paths.py)에서 확인할 수 있다.

`gazebo_ros`의 실행 파일은 패키지의 이 설정을 읽어 **자식 `gzserver` 프로세스의**
검색 경로를 구성한다. 부모 터미널에서 `printenv GAZEBO_PLUGIN_PATH`를 실행했을 때
사용자 패키지 경로가 없다고 해서 이 설정이 실패했다고 단정할 수는 없다.
다음 명령으로 실제 설치 파일부터 확인한다.

```bash
plugin_prefix="$(ros2 pkg prefix gazebo_tutorial_plugins)"
ls -l "${plugin_prefix}/lib/libground_truth_path_plugin.so"
ldd "${plugin_prefix}/lib/libground_truth_path_plugin.so"
```

파일이 존재하고 `ldd` 출력에 `not found`가 없어야 한다. `gazebo_ros`의 실행 파일을
거치지 않고 직접 `gzserver`를 실행하는 별도 구성에서는 다음과 같이 경로를 추가한다.
기존 경로를 덮어쓰지 않도록 작성했다.

```bash
plugin_prefix="$(ros2 pkg prefix gazebo_tutorial_plugins)"
export GAZEBO_PLUGIN_PATH="${plugin_prefix}/lib${GAZEBO_PLUGIN_PATH:+:${GAZEBO_PLUGIN_PATH}}"
```

기본 튜토리얼에서 매번 수동 설정이 필요하다면 올바른 작업 공간의 환경을 불러왔는지,
`package.xml`의 속성 이름과 상대 경로가 맞는지 먼저 확인한다.

## 7.9 ABI가 중요한 이유

`.so`는 `gzserver` 안으로 직접 로드되므로 다음 항목의 ABI가 맞아야 한다.

- Gazebo Classic 주 버전: 이 장에서는 `libgazebo.so.11`
- ROS 2 배포판과 `gazebo_ros`: 이 장에서는 Humble
- 연동되는 Ignition Math, sdformat, protobuf 버전
- CPU 아키텍처와 C++ 표준 라이브러리 ABI

다른 Ubuntu나 ROS 배포판에서 빌드한 `.so`만 복사해서 사용하는 방식은 피한다. 소스
패키지를 대상 Humble 작업 공간에서 다시 빌드한다. 로딩 전 다음 정보를 확인하면
ABI 문제를 빠르게 좁힐 수 있다.

```bash
gazebo --version
printenv ROS_DISTRO

plugin_so="$(ros2 pkg prefix gazebo_tutorial_plugins)/lib/libground_truth_path_plugin.so"
file "$plugin_so"
ldd "$plugin_so" | rg 'not found|gazebo|rclcpp|nav_msgs'
```

`not found`가 한 줄이라도 나오면 실행하지 말고 해당 의존성을 설치하거나 작업 공간 환경을
바르게 불러온다. `libgazebo.so.11`이 아닌 다른 주 버전을 가리키면 같은
Humble/Gazebo 11 환경에서 `colcon build --cmake-clean-cache`로 다시 구성한다.

## 7.10 문제 해결

### `Failed to load plugin ... cannot open shared object file`

1. 현재 터미널에서 `/opt/ros/humble/setup.bash`와 작업 공간
   `install/setup.bash`를 차례로 불러온다.
2. `ros2 pkg prefix gazebo_tutorial_plugins`가 기대한 작업 공간 환경을 가리키는지 본다.
3. 그 설치 경로의 `lib`에 `.so`가 실제로 있는지 확인한다.
4. `package.xml`의 `plugin_path`가 설치된 `lib`를 가리키는지 확인한다.
   직접 `gzserver`를 실행했다면 `GAZEBO_PLUGIN_PATH`도 확인한다.
5. URDF의 `filename` 철자와 `lib` 접두사, `.so` 확장자를 확인한다.

경로를 수정한 뒤 이미 실행 중인 `gzserver`에는 환경이 소급 적용되지 않는다. 서버를
완전히 종료하고 같은 셸에서 다시 실행한다.

### `undefined symbol`, `wrong ELF class`, Gazebo 즉시 종료

대부분 ABI 또는 아키텍처 문제다. `file`, `ldd`, `gazebo --version` 결과를 비교하고
대상 Humble 환경에서 다시 빌드한다. `LD_LIBRARY_PATH`로 임의의 다른 ROS 배포판
라이브러리를 섞어 해결하려고 하지 않는다.

Gazebo 로그를 자세히 보려면 기존 시뮬레이션을 종료하고 `verbose:=true`로 다시 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py verbose:=true
```

### 라이브러리는 로드되지만 토픽이 없다

- 플러그인 블록이 `<robot>` 최상위의 `<gazebo>` 안에 있는지 확인한다.
- 튜토리얼의 `gazebo_ros` 실행 구성을 사용했는지 확인한다. 일반 `gazebo`를 썼다면
  플러그인 검색 경로, ROS 인자, `/clock` 구성이 같은지 별도로 점검해야 한다.
- `update_rate`, `topic`, `frame`, `max_points`가 유효한지 서버 로그를 본다.
- 네임스페이스와 이름 재지정이 적용된 최종 이름을 `ros2 topic list -t`로 찾는다.
- Xacro가 조건문으로 플러그인 블록을 제외하지 않았는지 생성 URDF를 확인한다.

```bash
xacro ~/robotics-sim-tutorial-kr/ros2_ws/src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro \
  > /tmp/robot.urdf
rg -n 'ground_truth_path|libground_truth_path_plugin' /tmp/robot.urdf
```

### 토픽은 있지만 Path가 늘지 않는다

- Gazebo가 일시 정지 상태인지 확인한다.
- 키보드 조종 노드의 `cmd_vel`이 실제 로봇 네임스페이스로 가는지 확인한다.
- 플러그인이 움직이는 로봇 모델 안에 들어갔는지 확인한다.
- `/clock`과 Path 시각이 증가하는지 비교한다.

```bash
ros2 topic echo --once /clock
ros2 topic echo --once /ground_truth_path
```

### RViz에서 `No transform` 또는 경로가 엉뚱한 위치에 보인다

먼저 Path의 `header.frame_id`와 각 `PoseStamped`의 `header.frame_id`를 확인한다. 기본 출력은
`world`다. RViz Fixed Frame도 `world`로 두면 추가 TF 없이 동일 좌표계로 표시할 수
있다. 바퀴 오도메트리 Path를 함께 표시할 때만 실제 `world ↔ odom` TF가 필요하다.

`frame` 파라미터를 바꿔 경고를 숨기지 않는다. 좌표 변환이 필요한 경우 tf2로 위치와 자세를
변환해야 한다.

### 초기화 뒤 이전 궤적이 남는다

이 구현은 시뮬레이션 시간이 **뒤로 갈 때** 기존 궤적을 비운다. `reset_world`가
모델 위치와 자세만 초기화하고 시뮬레이션 시간을 유지하는 설정이라면 시간 역행이 없을 수
있다. 실험 단위를 명확히 나누려면 `reset_simulation`을 사용하거나, 다음 확장 과제로
명시적인 경로 초기화 서비스를 추가한다.

## 7.11 확장 과제

기본 플러그인이 안정적으로 동작한 뒤 다음 순서로 기능을 확장한다.

1. 누적 이동 거리와 참값 속도를 별도 토픽으로 발행한다.
2. ROS 2 서비스로 Path를 지우되, 서비스 콜백에서는 요청 표시만 세우고 실제
   벡터 변경은 다음 `OnUpdate()`에서 수행한다.
3. `PoseStamped` 스트림과 개수를 제한한 Path 출력을 선택하는 SDF 옵션을 추가한다.
4. 여러 로봇을 서로 다른 네임스페이스로 생성하고 토픽 격리가 되는지 검사한다.
5. 화면 없이 실행하는 통합 검사에서 로봇을 일정 거리 이동시킨 뒤, Path의 마지막
   기록과 Gazebo에서 조회한 모델 위치를 허용 오차 안에서 비교한다.

구독자나 서비스를 추가할수록 ROS 실행기 스레드와 물리 계산 스레드의 경계가
중요해진다. 콜백에서 오랫동안 잠금을 잡거나 Gazebo 물리 계산 API를 직접 호출하면
시뮬레이션이 멈추거나 교착될 수 있다. **ROS 콜백은 명령을 전달하고, Gazebo
갱신 콜백이 상태를 적용한다**는 원칙을 유지하면 기능이 커져도 구조를 이해하기
쉽다.

## 참고 자료

- [Gazebo Classic ModelPlugin 튜토리얼](https://classic.gazebosim.org/tutorials?tut=plugins_model)
- [Gazebo Classic ROS 플러그인 개요](https://classic.gazebosim.org/tutorials?tut=ros_gzplugins)
- [ROS 2 Humble `nav_msgs/msg/Path`](https://docs.ros.org/en/humble/p/nav_msgs/msg/Path.html)
- [Gazebo Classic ROS 2 패키지 마이그레이션 안내](https://gazebosim.org/docs/latest/migrating_gazebo_classic_ros2_packages/)
