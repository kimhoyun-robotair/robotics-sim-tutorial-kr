# Transport 인터페이스

> **목표:** publish/subscribe와 request/reply endpoint의 타입을 코드로 구성하고, Transport callback thread와 simulation update thread의 소유권 경계를 검증한다.
> **선행 학습:** [ECS System Plugin](01-ecs-system-plugin.md)

## Gazebo Transport와 ROS 2의 경계

Gazebo Transport는 Gazebo 프로세스가 직접 사용하는 통신 계층이고 ROS 2는 DDS 기반의 별도 통신 계층이다. 이 예제의 System Plugin은 `rclcpp`에 의존하지 않고 `gz::transport::Node`만 사용한다. 덕분에 ROS graph가 없어도 server-only 테스트를 실행할 수 있다. ROS 2에서 데이터가 필요할 때는 플러그인 안에 ROS 노드를 숨기지 않고 `ros_gz_bridge`를 경계에 둔다.

진단 인터페이스의 계약은 다음과 같다.

| 종류 | 이름 | Gazebo 메시지 | 방향 |
| --- | --- | --- | --- |
| topic | `/tutorial_bot/diagnostics/distance` | `gz.msgs.Double` | plugin → client |
| topic | `/tutorial_bot/diagnostics/status` | `gz.msgs.StringMsg` | plugin → client |
| topic | `/tutorial_bot/diagnostics/enable` | `gz.msgs.Boolean` | client → plugin |
| service | `/tutorial_bot/diagnostics/reset` | `gz.msgs.Empty` → `gz.msgs.Boolean` | request/reply |

SDF에서 인스턴스마다 endpoint를 바꿀 수 있다. 같은 클래스를 두 번 로드할 때에는 topic과 service가 충돌하지 않도록 모두 별도 이름으로 지정한다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>lifecycle_bot</model_name>
  <distance_topic>/lifecycle_bot/diagnostics/distance</distance_topic>
  <status_topic>/lifecycle_bot/diagnostics/status</status_topic>
  <enable_topic>/lifecycle_bot/diagnostics/enable</enable_topic>
  <reset_service>/lifecycle_bot/diagnostics/reset</reset_service>
  <publish_period>0.1</publish_period>
</plugin>
```

## Configure에서 endpoint 만들기

publisher의 protobuf 타입은 C++ 템플릿 인자로 정해진다. subscriber와 service callback의 함수 시그니처도 endpoint 타입의 일부이다.

```cpp
distancePublisher_ = node_.Advertise<gz::msgs::Double>(distanceTopic_);
statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);

node_.Subscribe(
  enableTopic_, &TutorialBotDiagnostics::OnEnable, this);
node_.Advertise(
  resetService_, &TutorialBotDiagnostics::OnReset, this);
```

메시지를 발행할 때에는 protobuf 필드를 채운 뒤 저장해 둔 publisher를 사용한다.

```cpp
gz::msgs::StringMsg status;
status.set_data(StateName(state_));
statusPublisher_.Publish(status);

gz::msgs::Double distance;
distance.set_data(distance_);
distancePublisher_.Publish(distance);
```

## callback에서 ECS를 직접 바꾸지 않기

Transport callback은 simulation update와 다른 thread에서 실행될 수 있다. callback이 `distance_`, `previousPose_`, `modelEntity_`를 직접 바꾸면 physics step의 읽기와 경합한다. 구현은 callback이 작은 명령만 mutex로 보호한 mailbox에 넣고, 다음 `PostUpdate`가 이를 가져가도록 한다.

```cpp
void TutorialBotDiagnostics::OnEnable(
  const gz::msgs::Boolean & message)
{
  std::lock_guard<std::mutex> lock(commandMutex_);
  pendingEnable_ = message.data();
}

bool TutorialBotDiagnostics::OnReset(
  const gz::msgs::Empty &, gz::msgs::Boolean & response)
{
  std::lock_guard<std::mutex> lock(commandMutex_);
  response.set_data(resetBound_);
  if (resetBound_) {
    pendingReset_ = true;
  }
  return true;
}
```

`PostUpdate`에서 호출하는 소비 함수는 lock을 잡은 동안 명령을 복사하고 mailbox를 비운다. 실제 simulation 상태 변경은 lock을 해제한 뒤 update thread에서 수행한다.

```cpp
void TutorialBotDiagnostics::ApplyPendingCommands(const bool modelBound)
{
  std::optional<bool> enable;
  bool reset = false;
  {
    std::lock_guard<std::mutex> lock(commandMutex_);
    resetBound_ = modelBound;
    enable = pendingEnable_;
    reset = pendingReset_;
    pendingEnable_.reset();
    pendingReset_ = false;
  }

  if (enable.has_value() && enabled_ != *enable) {
    enabled_ = *enable;
    previousPose_.reset();
  }
  if (reset) {
    distance_ = 0.0;
    previousPose_.reset();
  }
}
```

<figure class="course-figure" id="advanced-transport-boundary" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/transport-boundary.svg" alt="Transport callback이 mailbox를 거쳐 simulation update에서 ECS 상태에 적용되는 thread 경계도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. Transport callback은 명령만 mailbox에 기록하고 ECS 상태 전이는 simulation update가 소유한다.</figcaption>
</figure>

reset 응답의 `true`는 누적값이 이미 0이 되었다는 뜻이 아니라, 현재 결합된 모델이 있어 reset 명령을 수락했다는 뜻이다. 명령은 다음 `PostUpdate`에서 적용된다. 이런 비동기 의미까지 인터페이스 계약에 적어야 client가 잘못된 완료 조건을 세우지 않는다.

## CLI로 endpoint 시험하기

server를 실행한 터미널과 같은 `GZ_PARTITION`에서 목록과 메시지를 확인한다.

```bash
gz topic -l | grep /tutorial_bot/diagnostics
gz service -l | grep /tutorial_bot/diagnostics/reset

gz topic -e -t /tutorial_bot/diagnostics/status
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: false'
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: true'

gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

잘못된 타입을 일부러 보내면 endpoint 계약 검사가 가능하다. `gz.msgs.StringMsg` 요청이 거부되고 enable 상태가 그대로여야 한다.

```bash
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.StringMsg -p 'data: "false"'
```

## ROS 2에서 관측하기

거리와 상태 topic은 bridge에서 ROS 표준 메시지로 변환할 수 있다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /tutorial_bot/diagnostics/distance@std_msgs/msg/Float64@gz.msgs.Double \
  /tutorial_bot/diagnostics/status@std_msgs/msg/String@gz.msgs.StringMsg
```

다른 ROS 2 터미널에서 다음처럼 확인한다.

```bash
ros2 topic echo /tutorial_bot/diagnostics/distance
ros2 topic echo /tutorial_bot/diagnostics/status
```

reset은 request/reply 계약까지 포함하므로 이 과정에서는 Gazebo Transport service로 유지한다. ROS service가 제품 요구사항이라면 `ros_gz_bridge`가 지원하는 service pair인지 확인하거나, 별도의 작은 ROS adapter node에서 Gazebo Transport 요청을 호출하도록 경계를 명시한다.

## 자동 검증

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario transport --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["status"] == "PASS"; print("transport=PASS")' "$run_dir/scenario.json"
```

checker는 enable false/true와 reset을 실제 endpoint에 보내고, 잘못된 request type이 상태를 바꾸지 않는지도 확인한다. 단순 endpoint 목록이나 `PASS` 문자열만으로는 성공으로 판정하지 않는다.

## 문제 해결

| 증상 | 원인 후보 | 확인 방법 |
| --- | --- | --- |
| topic이 보이지 않음 | plugin load 실패, 다른 partition | server log와 `GZ_PARTITION`을 확인한다. |
| service timeout | request·response 타입 불일치 | 계약의 protobuf 타입과 CLI 인자를 비교한다. |
| disable 뒤 거리 증가 | callback에서 직접 변경, mailbox 미소비 | `ApplyPendingCommands` 호출 순서를 확인한다. |
| bridge 뒤 ROS topic 없음 | bridge 타입 문자열 오류 | `ros2 node info /parameter_bridge`와 양쪽 topic 목록을 본다. |
| 동시 reset 불안정 | callback/update 소유권 혼합 | ThreadSanitizer 테스트와 mutex 보호 범위를 확인한다. |

## 출처

- [Gazebo Transport publish/subscribe](https://gazebosim.org/api/transport/13/messages.html)
- [Gazebo Transport request/reply](https://gazebosim.org/api/transport/13/requestresponse.html)
- [ros_gz_bridge Jazzy API](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)

[이전: ECS System Plugin](01-ecs-system-plugin.md) · [다음: 물리와 주기 디버깅](03-physics-debugging.md)
