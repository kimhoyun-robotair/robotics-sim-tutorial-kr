# ECS 시스템 플러그인

> **목표:** `TutorialBotDiagnostics`의 헤더와 구현을 따라가며 ECS를 읽는 지점, 시스템의 호출 순서, SDF 삽입, 빌드와 로드 검증 방법을 익힌다.
> **선행 학습:** [고급 과정 개요](index.md)

## 완성할 플러그인

Gazebo Harmonic의 시뮬레이션 상태는 ECS(Entity-Component-System)로 구성된다. Entity는 모델이나 링크를 가리키는 정수 식별자이고, 컴포넌트는 이름·자세·속도 같은 데이터를 보관한다. 시스템은 매 시뮬레이션 계산 단계에서 컴포넌트를 읽거나 갱신하는 플러그인이다.

이 장의 `TutorialBotDiagnostics`는 `tutorial_bot`의 월드 자세를 관측하고 이동한 평면 거리를 누적한다. 구동 명령이나 물리 상태를 바꾸지 않으므로 상태를 읽는 플러그인의 첫 예제로 사용한다. 첫 유효 자세는 거리로 더하지 않고 기준점으로만 저장한다. 이후 두 위치가 \((x_{k-1},y_{k-1})\), \((x_k,y_k)\)라면 다음처럼 계산한다.

\[
\begin{aligned}
\Delta d_k &= \sqrt{(x_k-x_{k-1})^2+(y_k-y_{k-1})^2},\\
d_k &= d_{k-1}+\Delta d_k.
\end{aligned}
\]

관련 파일은 다음처럼 나뉜다.

```text
tutorial_bot_plugins/
├── include/tutorial_bot_plugins/tutorial_bot_diagnostics.hpp
├── src/tutorial_bot_diagnostics.cpp
├── config/diagnostics-contract.yaml
├── CMakeLists.txt
└── package.xml
tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf
```

## 시스템 인터페이스를 헤더에 선언하기

아래는 헤더에서 호출 인터페이스와 거리 계산에 필요한 멤버만 발췌한 것이다. 전체 선언은 `examples/ros2_ws/src/tutorial_bot_plugins/include/tutorial_bot_plugins/tutorial_bot_diagnostics.hpp`에 있다. `System`을 기본 클래스로 두고 사용할 인터페이스를 함께 상속한다.

```cpp
#include <gz/math/Pose3.hh>
#include <gz/sim/System.hh>
#include <gz/transport/Node.hh>
#include <memory>
#include <optional>
#include <string>

namespace gz::sim::systems
{
class TutorialBotDiagnostics final :
  public System,
  public ISystemConfigure,
  public ISystemPostUpdate
{
public:
  void Configure(
    const Entity & entity,
    const std::shared_ptr<const sdf::Element> & sdf,
    EntityComponentManager & ecm,
    EventManager & eventManager) override;

  void PostUpdate(
    const UpdateInfo & info,
    const EntityComponentManager & ecm) override;

private:
  std::string modelName_{"tutorial_bot"};
  Entity modelEntity_{kNullEntity};
  std::optional<gz::math::Pose3d> previousPose_;
  double distance_{0.0};
  gz::transport::Node node_;
};
}
```

Gazebo 시스템이 선택할 수 있는 주요 호출 지점은 다음과 같다.

| 인터페이스 | 호출 시점 | 알맞은 작업 | 이 예제의 선택 |
| --- | --- | --- | --- |
| `ISystemConfigure` | 플러그인을 개체에 연결할 때 한 번 | SDF 파라미터 파싱, 발행자와 서비스 준비 | 사용 |
| `ISystemPreUpdate` | 물리 상태 갱신 전 | 힘·속도·명령 컴포넌트 기록 | 사용하지 않음 |
| `ISystemUpdate` | 물리 계산 단계와 함께 갱신할 때 | 직접적인 동역학 계산 | 사용하지 않음 |
| `ISystemPostUpdate` | 물리 상태 갱신 후 | 확정된 상태 읽기, 센서·진단 발행 | 사용 |
| `ISystemReset` | 월드 초기화 요청을 처리할 때 | 플러그인 내부 상태와 기준점 초기화 | 사용하지 않음 |

구동 명령을 추가한다면 `ISystemPreUpdate`, 월드 초기화에 대응한다면 `ISystemReset`을 각각 상속한다. 선택한 메서드의 구현과 등록 매크로 항목도 함께 추가해야 한다. 아래 선언만 붙이면 구현이 없어 빌드에 실패한다. 이 진단 플러그인은 자세를 읽기만 하므로 두 인터페이스를 사용하지 않는다.

```cpp
void PreUpdate(
  const UpdateInfo & info,
  EntityComponentManager & ecm) override;

void Reset(
  const UpdateInfo & info,
  EntityComponentManager & ecm) override;
```

Transport의 `/tutorial_bot/diagnostics/reset`은 이 플러그인만 초기화하는 사용자 서비스이고 `ISystemReset`은 Gazebo 월드 초기화 생명주기이다. 이름이 비슷하지만 호출 원인이 다르다. 월드 초기화에도 누적 거리를 지워야 하는 제품 요구사항이 있다면 `ISystemReset`을 상속하고 `distance_`, `previousPose_`, `modelEntity_`, 발행 기준 시간을 명시적으로 초기화한다.

## Configure에서 SDF를 읽기

`Configure`는 `<plugin>` 아래의 설정을 읽는다. 다음은 이름과 발행 주기를 검사하는 부분을 발췌한 것이다. 전체 구현에서는 상태·활성화 토픽, 초기화 서비스, 통계 발행 설정도 읽는다. 발행 주기가 0·음수·무한대·`nan`이면 `INVALID_CONFIG`로 표시하고 거리 발행자를 만들지 않는다.

```cpp
void TutorialBotDiagnostics::Configure(
  const Entity &,
  const std::shared_ptr<const sdf::Element> & sdf,
  EntityComponentManager &,
  EventManager &)
{
  if (sdf->HasElement("model_name")) {
    modelName_ = sdf->Get<std::string>("model_name");
  }
  if (sdf->HasElement("distance_topic")) {
    distanceTopic_ = sdf->Get<std::string>("distance_topic");
  }

  const double periodSeconds =
    sdf->Get<double>("publish_period", 0.1).first;
  if (modelName_.empty() || !std::isfinite(periodSeconds) || periodSeconds <= 0.0) {
    SetState(State::InvalidConfig);
    statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
    return;
  }

  publishPeriod_ = std::chrono::duration_cast<std::chrono::steady_clock::duration>(
    std::chrono::duration<double>(periodSeconds));
  distancePublisher_ = node_.Advertise<gz::msgs::Double>(distanceTopic_);
  statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);
  node_.Subscribe(enableTopic_, &TutorialBotDiagnostics::OnEnable, this);
  node_.Advertise(resetService_, &TutorialBotDiagnostics::OnReset, this);
}
```

## PostUpdate에서 모델을 찾고 거리를 누적하기

모델 이름은 컴포넌트 조합으로 개체를 찾는 데 사용한다. 모델이 아직 생성되지 않았으면 서버를 종료하지 않고 다음 단계에서 다시 찾는다.

```cpp
const Entity candidate = ecm.EntityByComponents(
  components::Model(), components::Name(modelName_));
if (candidate == kNullEntity) {
  if (state_ != State::ModelRemoved) {
    SetState(State::WaitingForModel);
  }
  return;
}

modelEntity_ = candidate;
previousPose_.reset();
distance_ = 0.0;
```

다음은 실제 `PostUpdate` 구현이다. 설정 오류 확인, 모델 제거 확인, 다시 생성된 모델 연결, Transport 명령 적용, 자세 관측, 발행 순서로 실행한다. `worldPose` 결과에서 x와 y만 누적하므로 제자리 회전이나 z축 움직임은 평면 거리에 포함되지 않는다.

```cpp
void TutorialBotDiagnostics::PostUpdate(
  const UpdateInfo & info,
  const EntityComponentManager & ecm)
{
  if (state_ == State::InvalidConfig) {
    Publish(info.simTime);
    return;
  }

  if (modelEntity_ != kNullEntity && !ecm.HasEntity(modelEntity_)) {
    modelEntity_ = kNullEntity;
    previousPose_.reset();
    SetState(State::ModelRemoved);
  } else if (modelEntity_ == kNullEntity) {
    BindOrWait(ecm);
  }

  ApplyPendingCommands(modelEntity_ != kNullEntity);

  if (modelEntity_ != kNullEntity) {
    const auto poseComponent = ecm.Component<components::Pose>(modelEntity_);
    if (poseComponent != nullptr) {
      const auto pose = worldPose(modelEntity_, ecm);
      const bool poseIsFinite =
        std::isfinite(pose.Pos().X()) && std::isfinite(pose.Pos().Y());
      if (enabled_ && poseIsFinite && previousPose_.has_value()) {
        distance_ += std::hypot(
          pose.Pos().X() - previousPose_->Pos().X(),
          pose.Pos().Y() - previousPose_->Pos().Y());
      }
      if (enabled_ && poseIsFinite) {
        previousPose_ = pose;
        SetState(State::Ready);
      } else if (!enabled_) {
        previousPose_.reset();
        SetState(State::Disabled);
      }
    }
  }

  Publish(info.simTime);
  if (worldStatsPublisher_ && info.iterations == finalStatsIteration_) {
    worldStatsPublisher_.Publish(gz::sim::convert<gz::msgs::WorldStatistics>(info));
  }
}
```

<figure class="course-figure" id="advanced-ecs-lifecycle" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/ecs-lifecycle.svg" alt="WAITING FOR MODEL READY DISABLED MODEL REMOVED와 재결합 기준점을 보여 주는 ECS 생명주기 상태도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 모델이 제거되면 누적을 멈추고, 다시 생성된 모델은 거리 0부터 새로 기록한다.</figcaption>
</figure>

## 플러그인 클래스를 등록하기

소스 파일 마지막의 등록 매크로가 공유 라이브러리에서 클래스를 찾을 수 있게 한다. 헤더에서 상속했지만 여기에 등록하지 않은 인터페이스는 Gazebo가 호출하지 않는다.

```cpp
#include <gz/plugin/Register.hh>

GZ_ADD_PLUGIN(
  gz::sim::systems::TutorialBotDiagnostics,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(
  gz::sim::systems::TutorialBotDiagnostics,
  "gz::sim::systems::TutorialBotDiagnostics")
```

## CMake로 공유 라이브러리 만들기

이 패키지는 Jazzy가 제공하는 Gazebo vendor 패키지를 사용한다. vendor 패키지는 ROS 배포판에 맞는 Gazebo 라이브러리를 제공하고 CMake에서 버전 번호 없는 이름을 쓸 수 있게 한다. Jazzy에서는 Harmonic 계열을 선택하므로 같은 ROS 환경을 불러온 뒤 빌드한다.

아래는 실제 `tutorial_bot_plugins/CMakeLists.txt`의 빌드와 환경 설정 부분이다. 계약 YAML 설치와 테스트 설정은 전체 파일을 함께 확인한다.

```cmake
cmake_minimum_required(VERSION 3.8)
project(tutorial_bot_plugins)

find_package(ament_cmake REQUIRED)
find_package(gz_msgs_vendor REQUIRED)
find_package(gz-msgs REQUIRED)
find_package(gz_plugin_vendor REQUIRED)
find_package(gz-plugin REQUIRED COMPONENTS register)
find_package(gz_sim_vendor REQUIRED)
find_package(gz-sim REQUIRED)
find_package(gz_transport_vendor REQUIRED)
find_package(gz-transport REQUIRED)

add_library(TutorialBotDiagnosticsSystem SHARED
  src/tutorial_bot_diagnostics.cpp
)
target_compile_features(TutorialBotDiagnosticsSystem PUBLIC cxx_std_17)
target_include_directories(TutorialBotDiagnosticsSystem PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(TutorialBotDiagnosticsSystem
  gz-msgs::gz-msgs
  gz-plugin::register
  gz-sim::gz-sim
  gz-transport::gz-transport
)
install(TARGETS TutorialBotDiagnosticsSystem
  LIBRARY DESTINATION lib
)
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/tutorial_bot_plugins.dsv.in"
)
ament_package()
```

`find_package(gz_sim_vendor REQUIRED)`를 먼저 호출한 뒤 `find_package(gz-sim REQUIRED)`를 사용한다. vendor 패키지 이름은 밑줄(`_`), Gazebo 라이브러리 이름은 하이픈(`-`)을 쓴다는 점에 주의한다. `package.xml`도 같은 vendor 의존성을 선언한다.

```xml
<depend>gz_msgs_vendor</depend>
<depend>gz_plugin_vendor</depend>
<depend>gz_sim_vendor</depend>
<depend>gz_transport_vendor</depend>
```

설치 후 `source install/setup.bash`만으로 Gazebo가 플러그인을 찾게 하려면 다음 DSV 환경 설정 훅을 만든다.

```text title="hooks/tutorial_bot_plugins.dsv.in"
prepend-non-duplicate;GZ_SIM_SYSTEM_PLUGIN_PATH;lib
```

상대값 `lib`는 각 패키지의 설치 디렉터리를 기준으로 해석된다. CMake의 `ament_environment_hooks(...)`가 이 파일을 설치하므로 사용자는 매번 절대 경로를 export할 필요가 없다. 수동 `export GZ_SIM_SYSTEM_PLUGIN_PATH=...`는 환경 설정 훅 문제를 분리해 볼 때 유용한 진단 방법으로 남겨 둔다.

`add_library(TutorialBotDiagnosticsSystem ...)`은 Linux에서 `libTutorialBotDiagnosticsSystem.so`를 만든다. 이를 월드에 다음처럼 삽입한다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <distance_topic>/tutorial_bot/diagnostics/distance</distance_topic>
  <status_topic>/tutorial_bot/diagnostics/status</status_topic>
  <enable_topic>/tutorial_bot/diagnostics/enable</enable_topic>
  <reset_service>/tutorial_bot/diagnostics/reset</reset_service>
  <publish_period>0.1</publish_period>
</plugin>
```

## 빌드하고 직접 로드하기

저장소 최상위에서 실행한다. [고급 과정 개요](index.md)의 의존성 설치를 먼저 마친다.

```bash
export TUTORIAL_REPO="$PWD"
source /opt/ros/jazzy/setup.bash
cd "$TUTORIAL_REPO/examples/ros2_ws"
colcon build --packages-up-to tutorial_bot_plugins tutorial_bot_gazebo
source install/setup.bash
export TUTORIAL_INSTALL_BASE="$PWD/install"
cd "$TUTORIAL_REPO"

export GZ_PARTITION=tutorial_bot_advanced_manual
world="$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s -r "$world"
```

다른 터미널에서 ROS 환경을 불러오고 같은 통신 그룹을 지정한다. 아래의 출력 명령은 하나씩 실행하고 `Ctrl+C`로 끝낸 뒤 다음 명령을 실행한다. 서버를 실행한 터미널은 그대로 둔다.

```bash
source /opt/ros/jazzy/setup.bash
export GZ_PARTITION=tutorial_bot_advanced_manual
gz topic -e -t /tutorial_bot/diagnostics/status
```

`READY`를 확인했으면 출력을 끝내고 거리를 확인한다.

```bash
gz topic -e -t /tutorial_bot/diagnostics/distance
```

로봇이 정지해 있으므로 거리는 0이다. Protobuf는 기본값 필드를 생략할 수 있어 0일 때 `data: 0` 대신 빈 메시지가 출력되기도 한다. `--json-output`에서는 `{}`로 보일 수 있다. 메시지가 전혀 도착하지 않는 경우와 구분한다. 서비스를 확인하는 명령은 즉시 종료된다.

```bash
gz service -l | grep /tutorial_bot/diagnostics/reset
```

## 설치된 계약 검증

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
contract="$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/share/tutorial_bot_plugins/config/diagnostics-contract.yaml"
test -f "$contract"
python3 scripts/check_advanced_contract.py --contract "$contract" --evidence /tmp/tutorial-bot-contract.json
rm -f /tmp/tutorial-bot-contract.json
```

이 명령은 저장소 최상위에서 실행한다. `TUTORIAL_INSTALL_BASE`는 위에서 빌드한 설치 디렉터리다. 출력에는 클래스·라이브러리·인터페이스, 다섯 상태와 토픽·서비스 타입이 나타난다. 실제 YAML 값이 요구 조건과 다르면 종료 코드 64를 반환한다.

## 생명주기 판정

- 모델이 아직 없으면 `WAITING_FOR_MODEL`이며 서버는 계속 실행된다.
- 첫 자세는 `READY`, 거리 0의 기준점이다.
- 비활성화 상태에서는 누적을 멈추되 초기화 요청을 허용한다.
- 개체가 사라지면 `MODEL_REMOVED`가 되고, 재등장하면 새 기준점을 잡는다.
- 유한한 양수가 아닌 주기는 `INVALID_CONFIG`이며 거리 발행자를 만들지 않는다.

## 문제 해결

| 증상 | 확인할 항목 | 해결 방향 |
| --- | --- | --- |
| `Failed to load system plugin` | `GZ_SIM_SYSTEM_PLUGIN_PATH`, `.so` 파일명 | 설치된 `lib` 디렉터리를 경로에 추가한다. |
| 별칭을 찾지 못함 | SDF `name`, `GZ_ADD_PLUGIN_ALIAS` | 문자열을 완전히 같게 맞춘다. |
| `WAITING_FOR_MODEL` 지속 | `<model_name>`, 실제 모델 이름 | `gz model --list` 결과와 비교한다. |
| 제거 후 거리 급증 | `previousPose_` 초기화 여부 | 제거와 재결합 시 기준점을 비운다. |
| 설정 오류인데 거리 발행 | 검증과 발행자 생성 순서 | 설정 검증 뒤에 거리 발행자를 만든다. |

## 출처

- [Gazebo ROS 2 vendor 패키지 사용법](https://gazebosim.org/docs/latest/ros2_gz_vendor_pkgs/)
- [Gazebo Sim System plugins](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Sim Entity Component Manager](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1EntityComponentManager.html)

[이전: 고급 과정 개요](index.md) · [다음: Transport 인터페이스](02-transport-interfaces.md)
