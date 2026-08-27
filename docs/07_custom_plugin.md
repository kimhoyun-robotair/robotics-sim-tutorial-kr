# 7. 커스텀 Gazebo ModelPlugin 개발

이 장에서는 Gazebo Classic 11의 C++ `ModelPlugin`을 직접 만들고 ROS 2 Humble
토픽으로 결과를 내보낸다. 완성할 플러그인은 Gazebo가 알고 있는 로봇의 실제
`world pose`를 일정 주기로 누적해 `nav_msgs/msg/Path`로 발행한다. RViz에서 이
경로와 바퀴 오도메트리 경로를 겹쳐 보면 미끄러짐이나 잘못된 바퀴 반지름이
오도메트리에 어떤 오차를 만드는지 바로 확인할 수 있다.

> **버전 범위**
>
> 이 코드는 **Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic 11** 전용이다.
> Gazebo Classic은 2025년 1월 지원이 종료되었다. 기존 Humble 시스템을 학습하고
> 유지보수하기 위한 예제로 사용하고, 새 장기 프로젝트라면 최신 Gazebo의 System
> Plugin과 `ros_gz`로 옮기는 계획도 함께 세우자.

## 7.1 무엇을 만들 것인가

이번 장에서 다루는 데이터 흐름은 다음과 같다.

```mermaid
flowchart LR
  A["Gazebo 물리 엔진"] -->|WorldUpdateBegin| B["GroundTruthPathPlugin"]
  B -->|WorldPose 읽기| C["bounded nav_msgs/Path"]
  C -->|ROS 2 publish| D["RViz Path display"]
```

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

플러그인의 출력은 제어용 오도메트리가 아니다. 두 경로의 역할을 먼저 구분하자.

| 데이터 | 계산 근거 | 일반적인 용도 |
|---|---|---|
| Wheel odom | 바퀴 회전량과 로봇 기구학 | 로봇이 실전에서 추정할 수 있는 이동량, 제어·항법 입력 |
| 이번 플러그인의 ground truth | Gazebo 물리 엔진의 모델 `WorldPose()` | 시뮬레이터 안에서만 아는 정답, 오도메트리 검증 |

ground truth를 항법 입력으로 사용하면 시뮬레이션 성능이 지나치게 좋아진다. 이
토픽은 알고리즘 검증과 디버깅에만 사용하고 실제 로봇으로 이식할 경로에는 넣지
않는다.

## 7.2 Gazebo 플러그인의 종류와 실행 위치

Gazebo Classic 플러그인은 접근하려는 대상에 따라 종류가 나뉜다.

| 종류 | 접근 범위 | 대표적인 쓰임 |
|---|---|---|
| `ModelPlugin` | 한 모델과 그 링크·조인트 | 구동, 모델 상태 관찰, 이번 실습 |
| `WorldPlugin` | world 전체 | 모델 생성, 전역 실험 제어 |
| `SensorPlugin` | 한 센서 | 센서 데이터 후처리, 노이즈 모델 |
| `SystemPlugin` | `gzserver` 프로세스 | 초기화와 전역 기능 |
| `VisualPlugin` | 렌더링 visual | GUI에만 보이는 표현 변경 |
| `GUIPlugin` | Gazebo GUI | 패널과 사용자 인터페이스 |

이번 플러그인은 URDF에서 모델 전체에 붙는 `ModelPlugin`이다. 그래서 `Load()`가
받은 `gazebo::physics::ModelPtr`로 모델의 world pose를 직접 읽을 수 있다.

중요한 점은 플러그인이 별도 실행 파일이 아니라는 것이다. 빌드 결과인
`libground_truth_path_plugin.so`는 `gzserver`가 `dlopen()`으로 불러와 같은
프로세스 안에서 실행한다. 플러그인의 충돌이나 ABI 불일치는 Gazebo 서버 전체의
종료로 이어질 수 있다.

## 7.3 설정 계약

URDF의 `<plugin>` 아래에 다음 SDF 파라미터를 넣을 수 있다.

| 파라미터 | 기본값 | 제약과 의미 |
|---|---:|---|
| `update_rate` | `10.0` | simulation time 기준 발행 주파수(Hz), 유한한 양수 |
| `topic` | `ground_truth_path` | ROS 2 토픽 이름, 상대 이름 권장 |
| `frame` | `world` | `Path.header.frame_id`, 빈 문자열 금지 |
| `max_points` | `2000` | 최근에 보관할 pose 수, 양의 정수 |

`frame`은 좌표 변환 기능이 아니라 메시지에 붙이는 좌표계 이름이다. 코드는
`WorldPose()`를 그대로 넣으므로 기본값 `world`가 정확하다. 실제 변환 없이
`frame`만 `odom`이나 `map`으로 바꾸면 숫자는 그대로인데 이름만 달라진 잘못된
메시지가 된다.

`<ros>` 블록은 `gazebo_ros::Node`가 해석한다. 예를 들어 `topic`을 상대 이름으로
두고 namespace를 `/diffbot`으로 지정하면 실제 토픽은
`/diffbot/ground_truth_path`가 된다. 여러 로봇을 띄울 때는 로봇마다 namespace를
다르게 지정한다.

## 7.4 구현 읽기

### ModelPlugin 등록

`src/ground_truth_path_plugin.cpp`의 클래스는 `gazebo::ModelPlugin`을 상속하고
마지막에 다음 매크로로 등록된다.

```cpp
GZ_REGISTER_MODEL_PLUGIN(GroundTruthPathPlugin)
```

이 매크로가 Gazebo의 플러그인 팩터리 심볼을 공유 라이브러리에 만든다. 클래스만
작성하고 등록 매크로를 빼면 라이브러리는 발견되더라도 인스턴스를 만들 수 없다.

### ROS 2 노드와 publisher 생성

`Load()`는 모델이 삽입될 때 한 번 호출된다. 직접 `rclcpp::init()`을 호출하거나
별도 spin thread를 만드는 대신 다음 API를 사용한다.

```cpp
auto ros_node = gazebo_ros::Node::Get(sdf);
auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();
auto publisher =
  ros_node->create_publisher<nav_msgs::msg::Path>(config.topic, qos);
```

`gazebo_ros::Node::Get()`은 `<ros>`의 namespace와 remapping을 적용하고 노드를
`gazebo_ros`가 관리하는 공용 executor에 등록한다. 이번 플러그인은 publish만 하므로
사용자 스레드나 `spin_some()`이 필요 없다.

publisher는 `reliable + transient_local`이다. 따라서 RViz를 늦게 켜도 마지막으로
완성된 Path를 바로 받을 수 있다. 전체 Path 메시지 하나만 보관하도록 history depth는
1로 제한했다.

### 물리 update event와 simulation time

`Load()`의 마지막 단계에서 world update event를 연결한다.

```cpp
update_connection_ = gazebo::event::Events::ConnectWorldUpdateBegin(
  [weak_state](const gazebo::common::UpdateInfo & info) {
    if (const auto state = weak_state.lock()) {
      GroundTruthPathPlugin::OnUpdate(*state, info);
    }
  });
```

`OnUpdate()`는 Gazebo의 물리 update thread에서 실행된다. 발행 주기와 메시지 stamp는
wall clock이나 `std::chrono::steady_clock`이 아니라
`gazebo::common::UpdateInfo::simTime`을 사용한다. 따라서 다음 동작이 자연스럽다.

- Gazebo를 pause하면 새 pose가 쌓이지 않는다.
- real-time factor가 1보다 작거나 커도 simulation time 10 Hz를 유지한다.
- `/reset_simulation`으로 시간이 뒤로 가면 기존 Path를 비우고 새 시간축에서 다시
  시작한다.

각 `PoseStamped`와 Path 헤더에는 같은 Gazebo simulation stamp가 들어간다. `/clock`
callback의 도착 순서에 의존하는 `ros_node_->now()`를 사용하지 않은 이유다.

### 유한한 메모리 사용

매 update마다 무한히 pose를 누적하면 장시간 시뮬레이션에서 메모리와 DDS 직렬화
비용이 계속 증가한다. 이 구현은 `max_points`를 넘기기 직전에 가장 오래된 점을
제거한다.

```cpp
if (state.path.poses.size() >= state.config.max_points) {
  state.path.poses.erase(state.path.poses.begin());
}
state.path.poses.emplace_back(std::move(pose));
```

기본값은 2,000점이다. 10 Hz라면 최근 200초를 표시한다. 더 긴 실험에서는 무작정
수를 늘리기보다 update rate를 낮추거나 별도의 rosbag에 `PoseStamped`를 저장하는
편이 효율적이다.

### 수명 주기와 thread 안전성

ROS executor와 Gazebo physics thread가 같은 객체를 동시에 만질 수 있으므로 수명
종료 순서가 중요하다. 구현은 다음 순서를 지킨다.

1. callback은 플러그인의 `this` 대신 `weak_ptr<GroundTruthPathState>`를 캡처한다.
2. callback 시작 시 `weak_ptr::lock()`에 성공한 경우에만 상태를 사용한다. 이미 시작한
   callback은 그 `shared_ptr`로 상태 수명을 끝까지 유지한다.
3. destructor는 atomic `active`를 `false`로 만들고 `event::ConnectionPtr`을 해제한다.
4. mutex를 얻은 뒤 publisher, ROS node, model 포인터를 해제한다.

`OnUpdate()`도 mutex 바깥과 안에서 `active`를 두 번 확인한다. destructor가 먼저
lock을 얻거나 event 시스템에 callback 호출이 남아 있어도 플러그인 객체의 해제된
메모리를 참조하지 않는다. 이 패턴은 나중에 ROS subscriber나 service를 추가할 때
특히 중요하다. ROS callback에서 Gazebo 모델을 직접 수정하기보다는 명령을 mutex로
보호된 변수나 queue에 넣고, 다음 physics update에서 적용하는 구조가 안전하다.

## 7.5 빌드와 단위 테스트

의존 패키지를 설치한다. 이미 설치했다면 `apt`는 변경 없이 끝난다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-nav-msgs \
  ros-humble-ament-cmake-gtest
```

워크스페이스 루트에서 의존성을 확인하고 패키지만 빌드한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install \
  --packages-select gazebo_tutorial_plugins \
  --event-handlers console_direct+
source install/setup.bash
```

빌드 결과는 다음 명령으로 확인한다.

```bash
ros2 pkg prefix gazebo_tutorial_plugins
find "$(ros2 pkg prefix gazebo_tutorial_plugins)/lib" \
  -maxdepth 1 -name 'libground_truth_path_plugin.so' -print
```

단위 테스트는 Gazebo GUI를 띄우지 않고 설정과 시간 gate의 순수 C++ 부분을 검사한다.

```bash
colcon test --packages-select gazebo_tutorial_plugins \
  --event-handlers console_direct+
colcon test-result --verbose
```

테스트가 보장하는 계약은 다음과 같다.

- 기본 설정은 10 Hz, 즉 100 ms 주기다.
- 0 Hz, NaN, 빈 토픽·프레임, 0개의 최대 점 수는 거부한다.
- physics callback 횟수가 아니라 simulation time 간격으로 발행한다.
- simulation time이 뒤로 가면 reset 직후 pose를 즉시 발행한다.

이 테스트는 Gazebo와 ROS를 링크하는 통합 테스트를 대체하지 않는다. 실제 Humble
환경에서는 다음 절의 토픽과 RViz 확인까지 수행해야 플러그인 로딩과 메시지 계약을
검증한 것이다.

## 7.6 URDF/Xacro에 삽입하기

### URDF에 직접 넣기

2륜 로봇이나 4륜 로버 URDF의 최상위 `<robot>` 안, 닫는 `</robot>` 앞에 다음
블록을 추가한다. 특정 링크에 붙이는 센서 플러그인과 달리 `reference` 속성은 없다.

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
시작하는 절대 이름을 쓰면 namespace를 우회하므로 다중 로봇 실습에서는 상대 이름을
권장한다.

remapping도 사용할 수 있다.

```xml
<ros>
  <namespace>/diffbot</namespace>
  <remapping>ground_truth_path:=truth_path</remapping>
</ros>
```

이 경우 최종 토픽은 `/diffbot/truth_path`다. `topic` SDF 파라미터와 remapping을
동시에 자주 바꾸면 추적하기 어려우므로, 팀 프로젝트에서는 한 방식을 정해 사용한다.

### 제공된 Xacro 매크로 사용하기

설명 패키지의 Xacro에서 매크로 파일을 include하고 한 번 호출할 수도 있다.

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

URDF를 수정한 뒤에는 설명 패키지와 플러그인 패키지를 다시 빌드하고 overlay를 다시
source한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install \
  --packages-select gazebo_tutorial_plugins YOUR_DESCRIPTION_PACKAGE
source install/setup.bash
```

`YOUR_DESCRIPTION_PACKAGE`는 이 저장소에서 실습 중인 2륜 또는 4륜 로봇 설명 패키지
이름으로 바꾼다. 이후 해당 로봇의 Gazebo launch를 평소와 같은 방법으로 실행한다.
`gazebo_ros::Node::Get()` 자체도 ROS 초기화와 공용 executor 등록을 처리하지만, 이
튜토리얼에서는 `/clock`, spawn service, 종료 처리를 같은 방식으로 재현하기 위해
`gazebo_ros`가 제공하는 launch를 사용한다.

저장소의 `diffbot.urdf.xacro`에는 이 매크로가 이미 포함되어 있다. 전체 workspace를
빌드했다면 다음 한 줄로 플러그인, wheel odom Path, RViz를 함께 실행할 수 있다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

이 기본 모델은 root namespace를 사용하므로 플러그인 출력은
`/ground_truth_path`다. 앞의 `/diffbot` 예제는 여러 로봇을 띄울 때 적용할 namespace
패턴이다.

## 7.7 토픽 확인과 RViz 시각화

Gazebo가 실행되고 로봇이 spawn된 상태에서 최종 토픽 이름을 확인한다.

```bash
source ~/gazebo-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 topic list -t | rg 'ground_truth_path|truth_path'
ros2 topic info --verbose /ground_truth_path
ros2 topic echo --once /ground_truth_path
ros2 topic hz /ground_truth_path
```

예상 타입은 `nav_msgs/msg/Path`이며, 시뮬레이션을 재생한 동안 측정 주파수는 약
10 Hz다. pause 상태에서는 `ros2 topic hz`가 새 메시지를 받지 못하는 것이 정상이다.

keyboard teleop으로 로봇을 직진, 회전, 제자리 회전시키며 경로가 늘어나는지 본다.
그 다음 RViz를 연다.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

RViz에서 다음과 같이 설정한다.

1. **Global Options → Fixed Frame**을 `world`로 설정한다.
2. **Add → By display type → Path**를 선택한다.
3. Path의 **Topic**을 `/ground_truth_path`로 지정한다.
4. 잘 보이도록 Line Style, Line Width, Color를 조정한다.

기본 `diffbot.launch.py`가 연 RViz에는 빨간색 Ground Truth Path와 초록색 Wheel Odom
Path가 이미 등록되어 있다. 이 설정의 Fixed Frame은 `odom`이며 launch가 spawn
pose를 반영한 `world → odom` static TF도 함께 제공한다. 위 수동 설정은 플러그인만
다른 launch에 붙였을 때 사용한다.

publisher가 `transient_local`이므로 RViz를 나중에 실행해도 마지막 Path가 나타난다.
나타나지 않으면 Path display의 Reliability를 `Reliable`, Durability를
`Transient Local`로 맞추고 RViz를 다시 연다.

### Wheel odom과 ground truth 겹쳐 보기

이 저장소의 `odom_to_path` 노드로 wheel odom도 Path로 바꾼다.

```bash
ros2 run gazebo_tutorial_tools odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_points:=2000
```

RViz에 Path display를 하나 더 추가해 `/wheel_odom_path`를 다른 색으로
표시한다. 비교 전에 다음 두 가지를 확인한다.

- Differential Drive 플러그인의 `/odom`이 Gazebo world pose가 아니라 wheel/encoder
  적분을 사용해야 의미 있는 비교가 된다.
- wheel Path의 `header.frame_id`가 `odom`이라면 RViz가 `world`에서 `odom`으로 가는
  올바른 TF를 알아야 한다.

기본 bringup은 launch 인자 `x`, `y`, `yaw`를 반영한 `world → odom` static TF를
자동으로 발행한다. 이미 다른 노드가 이 TF를 소유한다면 중복 발행을 피한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  publish_world_odom_tf:=false
```

직접 구성한 실습에서 로봇을 world 원점, yaw 0으로 spawn했고 `odom` 원점도 그
위치와 정확히 일치할 때만 다음 identity static TF를 사용할 수 있다.

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 --roll 0 --pitch 0 --yaw 0 \
  --frame-id world --child-frame-id odom
```

spawn pose나 odom 초기점이 다르면 위 명령을 그대로 쓰면 안 된다. 실제 두 좌표계의
변환을 계산해 넣거나 공통 좌표계로 pose를 변환하는 노드를 사용한다. 프레임 이름만
같게 바꾸는 것은 변환이 아니다.

미끄러운 바닥에서 급회전하거나 wheel radius를 일부러 조금 틀리게 설정하면 두
Path가 점점 벌어진다. 이 차이가 wheel odom의 누적 오차다.

## 7.8 공유 라이브러리와 `GAZEBO_PLUGIN_PATH`

URDF의 `filename="libground_truth_path_plugin.so"`는 실행 파일 경로가 아니다.
Gazebo는 `GAZEBO_PLUGIN_PATH`에 등록된 디렉터리를 차례로 검색해 이 파일을 찾는다.

이 패키지의 `package.xml`에는 다음 export가 들어 있다.

```xml
<gazebo_ros gazebo_plugin_path="${prefix}/lib" />
```

정상적으로 빌드한 뒤 `install/setup.bash`를 source하면 `gazebo_ros`가 패키지의
`lib` 경로를 Gazebo 검색 경로에 추가한다. 현재 상태는 다음처럼 확인한다.

```bash
echo "$GAZEBO_PLUGIN_PATH" | tr ':' '\n'
ros2 pkg prefix gazebo_tutorial_plugins
```

환경 hook을 사용하지 않는 특수한 실행 셸에서는 임시로 경로를 **앞에 추가**할 수
있다. 기존 경로를 덮어쓰지 않는 것이 중요하다.

```bash
plugin_prefix="$(ros2 pkg prefix gazebo_tutorial_plugins)"
export GAZEBO_PLUGIN_PATH="${plugin_prefix}/lib${GAZEBO_PLUGIN_PATH:+:${GAZEBO_PLUGIN_PATH}}"
```

이 수동 export가 늘 필요하다면 launch를 실행하는 셸에서 workspace를 source하지
않았거나, 다른 overlay를 나중에 source해 환경이 바뀐 경우가 많다. 원인을 고친 뒤
수동 설정은 제거하는 편이 재현성이 좋다.

## 7.9 ABI가 중요한 이유

`.so`는 `gzserver` 안으로 직접 로드되므로 다음 항목의 ABI가 맞아야 한다.

- Gazebo Classic major version: 이 장에서는 `libgazebo.so.11`
- ROS 2 배포판과 `gazebo_ros`: 이 장에서는 Humble
- 연동되는 Ignition Math, sdformat, protobuf 버전
- CPU 아키텍처와 C++ 표준 라이브러리 ABI

다른 Ubuntu나 ROS 배포판에서 빌드한 `.so`만 복사해서 사용하는 방식은 피한다. 소스
패키지를 대상 Humble workspace에서 다시 빌드한다. 로딩 전 다음 정보를 확인하면
ABI 문제를 빠르게 좁힐 수 있다.

```bash
gazebo --version
printenv ROS_DISTRO

plugin_so="$(ros2 pkg prefix gazebo_tutorial_plugins)/lib/libground_truth_path_plugin.so"
file "$plugin_so"
ldd "$plugin_so" | rg 'not found|gazebo|rclcpp|nav_msgs'
```

`not found`가 한 줄이라도 나오면 실행하지 말고 해당 의존성을 설치하거나 overlay를
바르게 source한다. `libgazebo.so.11`이 아닌 다른 major version을 가리키면 같은
Humble/Gazebo 11 환경에서 `colcon build --cmake-clean-cache`로 다시 구성한다.

## 7.10 문제 해결

### `Failed to load plugin ... cannot open shared object file`

1. 현재 터미널에서 `/opt/ros/humble/setup.bash`와 workspace
   `install/setup.bash`를 차례로 source한다.
2. `ros2 pkg prefix gazebo_tutorial_plugins`가 기대한 overlay를 가리키는지 본다.
3. 그 prefix의 `lib`에 `.so`가 실제로 있는지 확인한다.
4. `GAZEBO_PLUGIN_PATH`에 같은 `lib` 디렉터리가 있는지 확인한다.
5. URDF filename의 철자와 `lib` 접두사, `.so` 확장자를 확인한다.

경로를 수정한 뒤 이미 실행 중인 `gzserver`에는 환경이 소급 적용되지 않는다. 서버를
완전히 종료하고 같은 셸에서 다시 launch한다.

### `undefined symbol`, `wrong ELF class`, Gazebo 즉시 종료

대부분 ABI 또는 아키텍처 문제다. `file`, `ldd`, `gazebo --version` 결과를 비교하고
대상 Humble 환경에서 다시 빌드한다. `LD_LIBRARY_PATH`로 임의의 다른 ROS 배포판
라이브러리를 섞어 해결하려고 하지 않는다.

Gazebo 로그를 자세히 보려면 기존 launch에 `verbose:=true`를 전달하거나 다음처럼
서버 출력을 확인한다.

```bash
ros2 launch gazebo_ros gazebo.launch.py verbose:=true
```

### 라이브러리는 로드되지만 토픽이 없다

- 플러그인 블록이 `<robot>` 최상위의 `<gazebo>` 안에 있는지 확인한다.
- 튜토리얼의 `gazebo_ros` launch로 시작했는지 확인한다. plain `gazebo`를 썼다면
  plugin path, ROS 인자, `/clock` 구성이 같은지 별도로 점검해야 한다.
- `update_rate`, `topic`, `frame`, `max_points`가 유효한지 server 로그를 본다.
- namespace와 remapping이 적용된 최종 이름을 `ros2 topic list -t`로 찾는다.
- Xacro가 조건문으로 플러그인 블록을 제외하지 않았는지 생성 URDF를 확인한다.

```bash
xacro path/to/robot.urdf.xacro > /tmp/robot.urdf
rg -n 'ground_truth_path|libground_truth_path_plugin' /tmp/robot.urdf
```

### 토픽은 있지만 Path가 늘지 않는다

- Gazebo가 pause 상태인지 확인한다.
- keyboard teleop의 `cmd_vel`이 실제 로봇 namespace로 가는지 확인한다.
- 플러그인이 움직이는 로봇 모델 안에 들어갔는지 확인한다.
- `/clock`과 Path stamp가 증가하는지 비교한다.

```bash
ros2 topic echo --once /clock
ros2 topic echo --once /ground_truth_path
```

### RViz에서 `No transform` 또는 경로가 엉뚱한 위치에 보인다

먼저 Path의 `header.frame_id`와 pose의 `header.frame_id`를 확인한다. 기본 출력은
`world`다. RViz Fixed Frame도 `world`로 두면 추가 TF 없이 동일 좌표계로 표시할 수
있다. wheel odom Path를 함께 표시할 때만 실제 `world ↔ odom` TF가 필요하다.

`frame` 파라미터를 바꿔 경고를 숨기지 않는다. 좌표 변환이 필요한 경우 tf2로 pose를
변환해야 한다.

### reset 뒤 이전 궤적이 남는다

이 구현은 simulation time이 **뒤로 갈 때** 기존 궤적을 비운다. `reset_world`가
모델 pose만 초기화하고 simulation time을 유지하는 설정이라면 시간 역행이 없을 수
있다. 실험 단위를 명확히 나누려면 `reset_simulation`을 사용하거나, 다음 확장 과제로
명시적인 경로 초기화 service를 추가한다.

## 7.11 확장 과제

기본 플러그인이 안정적으로 동작한 뒤 다음 순서로 기능을 확장해 보자.

1. 누적 이동 거리와 ground-truth 속도를 별도 토픽으로 발행한다.
2. ROS 2 service로 Path를 지우되, service callback에서는 요청 flag만 세우고 실제
   vector 변경은 다음 `OnUpdate()`에서 수행한다.
3. `PoseStamped` 스트림과 bounded Path 출력을 선택하는 SDF 옵션을 추가한다.
4. 여러 로봇을 서로 다른 namespace로 spawn하고 토픽 격리가 되는지 검사한다.
5. headless Gazebo 통합 테스트에서 모델을 일정 거리 이동시킨 뒤 Path의 마지막 pose와
   `GetModelState` 결과를 허용 오차 안에서 비교한다.

subscriber나 service를 추가할수록 ROS executor thread와 physics thread의 경계가
중요해진다. callback에서 오랫동안 lock을 잡거나 Gazebo physics API를 직접 호출하면
시뮬레이션이 멈추거나 교착될 수 있다. **ROS callback은 명령을 전달하고, Gazebo
update callback이 상태를 적용한다**는 원칙을 유지하면 기능이 커져도 구조를 이해하기
쉽다.

## 참고 자료

- [Gazebo Classic ModelPlugin 튜토리얼](https://classic.gazebosim.org/tutorials?tut=plugins_model)
- [Gazebo Classic ROS 플러그인 개요](https://classic.gazebosim.org/tutorials?tut=ros_gzplugins)
- [ROS 2 Humble `nav_msgs/msg/Path`](https://docs.ros.org/en/humble/p/nav_msgs/msg/Path.html)
- [Gazebo Classic ROS 2 패키지 마이그레이션 안내](https://gazebosim.org/docs/latest/migrating_gazebo_classic_ros2_packages/)
