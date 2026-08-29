# ECS System Plugin

> **목표:** `TutorialBotDiagnostics`의 헤더와 구현을 따라가며 ECS를 읽는 지점, System 생명주기, SDF 삽입, 빌드와 로드 검증 방법을 익힌다.
> **선행 학습:** [고급 과정 개요](index.md)

## 완성할 플러그인

Gazebo Harmonic의 시뮬레이션 상태는 ECS(Entity-Component-System)로 구성된다. Entity는 모델이나 링크를 가리키는 정수 식별자이고, component는 이름·자세·속도 같은 데이터를 보관한다. System은 매 simulation step에서 component를 읽거나 갱신하는 플러그인이다.

이 장의 `TutorialBotDiagnostics`는 `tutorial_bot`의 월드 자세를 관측하고 이동한 평면 거리를 누적한다. 구동 명령이나 물리 상태를 바꾸지 않으므로 관측용 System의 작은 예제로 적합하다. 첫 유효 자세는 거리로 더하지 않고 기준점으로만 저장한다. 이후 두 위치가 \((x_{k-1},y_{k-1})\), \((x_k,y_k)\)라면 다음처럼 계산한다.

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

## System 인터페이스를 헤더에 선언하기

실제 헤더의 핵심은 다음과 같다. `System`을 기본 클래스로 두고 사용할 생명주기 인터페이스를 함께 상속한다.

```cpp
#include <gz/sim/System.hh>
#include <gz/transport/Node.hh>

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

Gazebo System이 선택할 수 있는 주요 호출 지점은 다음과 같다.

| 인터페이스 | 호출 시점 | 알맞은 작업 | 이 예제의 선택 |
| --- | --- | --- | --- |
| `ISystemConfigure` | 플러그인을 entity에 연결할 때 한 번 | SDF 파라미터 파싱, publisher와 service 준비 | 사용 |
| `ISystemPreUpdate` | physics update 전 | 힘·속도·명령 component 기록 | 사용하지 않음 |
| `ISystemUpdate` | physics 단계와 함께 갱신할 때 | 직접적인 동역학 계산 | 사용하지 않음 |
| `ISystemPostUpdate` | physics update 후 | 확정된 상태 읽기, 센서·진단 발행 | 사용 |
| `ISystemReset` | world reset 요청을 처리할 때 | 플러그인 내부 상태와 기준점 초기화 | 사용하지 않음 |

`PreUpdate`가 필요하다면 헤더에 `public ISystemPreUpdate`와 아래 메서드를 추가하고 등록 매크로에도 같은 인터페이스를 넣는다. 단, 이 진단 플러그인은 자세를 쓰지 않고 읽기만 하므로 `PostUpdate`가 더 명확하다.

```cpp
void PreUpdate(
  const UpdateInfo & info,
  EntityComponentManager & ecm) override;

void Reset(
  const UpdateInfo & info,
  EntityComponentManager & ecm) override;
```

Transport의 `/tutorial_bot/diagnostics/reset`은 이 플러그인만 초기화하는 사용자 service이고 `ISystemReset`은 Gazebo world reset 생명주기이다. 이름이 비슷하지만 호출 원인이 다르다. world reset에도 누적 거리를 지워야 하는 제품 요구사항이 있다면 `ISystemReset`을 상속하고 `distance_`, `previousPose_`, `modelEntity_`, 발행 기준 시간을 명시적으로 초기화한다.

## Configure에서 SDF를 읽기

`Configure`는 `<plugin>` 아래의 사용자 파라미터를 읽는다. 저장소 구현은 기본값을 제공한 뒤 모델 이름과 발행 주기를 검증한다. 유한한 양수가 아닌 주기는 조용히 보정하지 않고 `INVALID_CONFIG` 상태로 남긴다.

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

모델 이름은 component 조합으로 entity를 찾는 데 사용한다. 모델이 아직 spawn되지 않았으면 server를 종료하지 않고 다음 step에서 다시 찾는다.

```cpp
const Entity candidate = ecm.EntityByComponents(
  components::Model(), components::Name(modelName_));
if (candidate == kNullEntity) {
  SetState(State::WaitingForModel);
  return;
}

modelEntity_ = candidate;
previousPose_.reset();
distance_ = 0.0;
```

실제 `PostUpdate`는 entity 제거 확인, 재결합, Transport 명령 적용, 자세 관측, 발행 순서로 실행한다. `worldPose` 결과에서 x와 y만 누적하므로 제자리 회전이나 z축 움직임은 평면 거리에 포함되지 않는다.

```cpp
void TutorialBotDiagnostics::PostUpdate(
  const UpdateInfo & info,
  const EntityComponentManager & ecm)
{
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
      if (enabled_ && previousPose_.has_value()) {
        distance_ += std::hypot(
          pose.Pos().X() - previousPose_->Pos().X(),
          pose.Pos().Y() - previousPose_->Pos().Y());
      }
      previousPose_ = pose;
    }
  }
  Publish(info.simTime);
}
```

<figure class="course-figure" id="advanced-ecs-lifecycle" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/ecs-lifecycle.svg" alt="WAITING FOR MODEL READY DISABLED MODEL REMOVED와 재결합 기준점을 보여 주는 ECS 생명주기 상태도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 모델이 제거되면 거리를 동결하고, 재등장한 entity는 거리 0의 새 기준점으로 결합한다.</figcaption>
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

이 저장소의 CI container는 Harmonic ABI를 `gz-sim8`, `gz-plugin2`, `gz-msgs10`, `gz-transport13`으로 고정한다. 따라서 실제 `tutorial_bot_plugins/CMakeLists.txt`도 같은 숫자 ABI package와 target을 사용한다.

```cmake
find_package(ament_cmake REQUIRED)
find_package(gz-msgs10 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-sim8 REQUIRED)
find_package(gz-transport13 REQUIRED)

add_library(TutorialBotDiagnosticsSystem SHARED
  src/tutorial_bot_diagnostics.cpp
)
target_compile_features(TutorialBotDiagnosticsSystem PUBLIC cxx_std_17)
target_link_libraries(TutorialBotDiagnosticsSystem
  gz-msgs10::gz-msgs10
  gz-plugin2::gz-plugin2-register
  gz-sim8::gz-sim8
  gz-transport13::gz-transport13
)
install(TARGETS TutorialBotDiagnosticsSystem
  LIBRARY DESTINATION lib
)
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/tutorial_bot_plugins.dsv.in"
)
ament_package()
```

Jazzy의 vendor package를 기준으로 새 package를 설계하는 방법도 있다. 이 경우 먼저 `gz_sim_vendor`, `gz_plugin_vendor`를 찾고 versionless `gz-sim`, `gz-plugin` package와 target을 일관되게 사용한다. 다만 이 저장소처럼 CI image와 ABI 번호를 직접 고정한 target 안에서는 vendor 방식과 숫자 고정 방식을 섞지 않는다. 실제 `package.xml`도 CMake와 같은 네 dependency를 선언한다.

```xml
<depend>gz-msgs10</depend>
<depend>gz-plugin2</depend>
<depend>gz-sim8</depend>
<depend>gz-transport13</depend>
```

설치 후 `source install/setup.bash`만으로 Gazebo가 plugin을 찾게 하려면 다음 DSV 환경 hook을 만든다.

```text title="hooks/tutorial_bot_plugins.dsv.in"
prepend-non-duplicate;GZ_SIM_SYSTEM_PLUGIN_PATH;lib
```

상대값 `lib`는 package install prefix를 기준으로 해석된다. CMake의 `ament_environment_hooks(...)`가 이 파일을 설치하므로 사용자는 매번 절대 경로를 export할 필요가 없다. 수동 `export GZ_SIM_SYSTEM_PLUGIN_PATH=...`는 hook 문제를 분리해 볼 때 유용한 진단 방법으로 남겨 둔다.

`add_library(TutorialBotDiagnosticsSystem ...)`은 Linux에서 `libTutorialBotDiagnosticsSystem.so`를 만든다. 이를 world에 다음처럼 삽입한다.

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

```bash
cd examples/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select tutorial_bot_plugins tutorial_bot_gazebo
source install/setup.bash

export GZ_SIM_SYSTEM_PLUGIN_PATH="$PWD/install/tutorial_bot_plugins/lib"
world="$PWD/install/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s -r "$world"
```

다른 터미널에서는 같은 `GZ_PARTITION` 환경을 유지한 채 상태와 거리를 확인한다.

```bash
gz topic -e -t /tutorial_bot/diagnostics/status
gz topic -e -t /tutorial_bot/diagnostics/distance
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

출력에는 plugin class·library·interface, 다섯 상태와 topic/service 타입이 나타난다. checker가 YAML을 파싱하므로 설명 문구만 맞고 실제 계약이 다르면 exit 64로 종료한다.

## 생명주기 판정

- 모델이 아직 없으면 `WAITING_FOR_MODEL`이며 server는 계속 실행된다.
- 첫 pose는 `READY`, distance 0의 기준점이다.
- disable 상태에서는 누적을 멈추되 reset 요청을 허용한다.
- entity가 사라지면 `MODEL_REMOVED`가 되고, 재등장하면 새 기준점을 잡는다.
- 유한한 양수가 아닌 주기는 `INVALID_CONFIG`이며 distance publisher를 만들지 않는다.

## 문제 해결

| 증상 | 확인할 항목 | 해결 방향 |
| --- | --- | --- |
| `Failed to load system plugin` | `GZ_SIM_SYSTEM_PLUGIN_PATH`, `.so` 파일명 | 설치된 `lib` 디렉터리를 경로에 추가한다. |
| alias를 찾지 못함 | SDF `name`, `GZ_ADD_PLUGIN_ALIAS` | 문자열을 완전히 같게 맞춘다. |
| `WAITING_FOR_MODEL` 지속 | `<model_name>`, 실제 model 이름 | `gz model --list` 결과와 비교한다. |
| 제거 후 거리 급증 | `previousPose_` 초기화 여부 | 제거와 재결합 시 기준점을 비운다. |
| 설정 오류인데 거리 발행 | 검증과 publisher 생성 순서 | 설정 검증 뒤에 distance publisher를 만든다. |

## 출처

- [Gazebo Sim System plugins](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Sim Entity Component Manager](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1EntityComponentManager.html)

[이전: 고급 과정 개요](index.md) · [다음: Transport 인터페이스](02-transport-interfaces.md)
