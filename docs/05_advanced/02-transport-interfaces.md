# Transport 인터페이스

> **목표:** 토픽과 서비스의 메시지 타입을 정의하고, 통신 콜백과 시뮬레이션 코드가 같은 상태를 동시에 바꾸지 않도록 구성한다.
> **선행 학습:** [ECS 시스템 플러그인](01-ecs-system-plugin.md)

## Gazebo Transport와 ROS 2의 경계

Gazebo Transport는 Gazebo 프로세스가 직접 사용하는 통신 계층이고 ROS 2는 DDS 기반의 별도 통신 계층이다. 이 예제의 시스템 플러그인은 `rclcpp`에 의존하지 않고 `gz::transport::Node`만 사용한다. 따라서 ROS 노드를 실행하지 않아도 Gazebo 서버만으로 시험할 수 있다. ROS 2에 데이터를 전달할 때는 별도의 `ros_gz_bridge` 노드를 사용한다.

진단 인터페이스의 계약은 다음과 같다.

| 종류 | 이름 | Gazebo 메시지 | 방향 |
| --- | --- | --- | --- |
| 토픽 | `/tutorial_bot/diagnostics/distance` | `gz.msgs.Double` | 플러그인 → 클라이언트 |
| 토픽 | `/tutorial_bot/diagnostics/status` | `gz.msgs.StringMsg` | 플러그인 → 클라이언트 |
| 토픽 | `/tutorial_bot/diagnostics/enable` | `gz.msgs.Boolean` | 클라이언트 → 플러그인 |
| 서비스 | `/tutorial_bot/diagnostics/reset` | `gz.msgs.Empty` → `gz.msgs.Boolean` | 요청·응답 |

SDF에서 인스턴스마다 통신 지점을 바꿀 수 있다. 같은 클래스를 두 번 로드할 때에는 토픽과 서비스가 충돌하지 않도록 모두 별도 이름으로 지정한다.

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

## Configure에서 통신 지점 만들기

Gazebo 메시지는 Protobuf라는 형식으로 정의된다. 아래에서 `Advertise<gz::msgs::Double>`은 실수 메시지 발행자를 만든다. 구독자와 서비스 콜백 함수의 인자·반환 타입도 메시지 정의와 맞아야 한다.

```cpp
distancePublisher_ = node_.Advertise<gz::msgs::Double>(distanceTopic_);
statusPublisher_ = node_.Advertise<gz::msgs::StringMsg>(statusTopic_);

node_.Subscribe(
  enableTopic_, &TutorialBotDiagnostics::OnEnable, this);
node_.Advertise(
  resetService_, &TutorialBotDiagnostics::OnReset, this);
```

메시지를 발행할 때에는 protobuf 필드를 채운 뒤 저장해 둔 발행자를 사용한다.

```cpp
gz::msgs::StringMsg status;
status.set_data(StateName(state_));
statusPublisher_.Publish(status);

gz::msgs::Double distance;
distance.set_data(distance_);
distancePublisher_.Publish(distance);
```

## 콜백에서 ECS를 직접 바꾸지 않기

Transport 콜백은 시뮬레이션 갱신 코드와 다른 스레드에서 실행될 수 있다. 양쪽에서 `distance_`, `previousPose_`, `modelEntity_`를 동시에 바꾸면 읽는 도중 값이 달라지는 문제가 생긴다. 그래서 콜백은 명령만 임시로 저장하고 다음 `PostUpdate`가 적용하게 한다. `std::mutex`는 이 임시 저장 공간에 한 번에 한 스레드만 접근하게 하는 잠금 장치다.

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

`ApplyPendingCommands`는 잠금을 잡고 대기 중인 명령을 복사한 뒤 저장 공간을 비운다. 잠금을 풀고 실제 상태를 변경하므로 통신 스레드를 오래 기다리게 하지 않는다. 갱신 전에 활성화 명령이 여러 번 오면 마지막 값만 적용하고, 초기화 요청 여러 건은 한 번의 초기화로 합친다.

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
    stateChanged_ = true;
  }
  if (reset) {
    distance_ = 0.0;
    previousPose_.reset();
    stateChanged_ = true;
  }
}
```

<figure class="course-figure" id="advanced-transport-boundary" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/transport-boundary.svg" alt="통신 콜백이 명령을 임시 저장하고 시뮬레이션 갱신 코드가 상태에 적용하는 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. Transport 콜백은 명령을 임시 저장하고, 시뮬레이션 갱신 코드가 실제 상태에 적용한다.</figcaption>
</figure>

초기화 응답의 `true`는 누적값이 이미 0이 되었다는 뜻이 아니라, 현재 결합된 모델이 있어 초기화 명령을 수락했다는 뜻이다. 명령은 다음 `PostUpdate`에서 적용된다. 이런 비동기 의미까지 인터페이스 계약에 적어야 클라이언트가 잘못된 완료 조건을 세우지 않는다.

## CLI로 활성화와 초기화 시험하기

[ECS 플러그인 장](01-ecs-system-plugin.md)의 서버를 터미널 A에서 실행해 둔다. 터미널 B에서 상태를 계속 관찰한다.

```bash
source /opt/ros/jazzy/setup.bash
export GZ_PARTITION=tutorial_bot_advanced_manual
gz topic -e -t /tutorial_bot/diagnostics/status
```

터미널 C에서는 같은 환경을 설정하고 명령을 하나씩 보낸다.

```bash
source /opt/ros/jazzy/setup.bash
export GZ_PARTITION=tutorial_bot_advanced_manual
gz topic -l | grep /tutorial_bot/diagnostics
gz service -l | grep /tutorial_bot/diagnostics/reset
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: false'
```

터미널 B에 `DISABLED`가 표시되면 거리 누적이 멈춘 것이다. 터미널 C에서 다시 활성화한다.

```bash
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: true'
```

`READY`로 돌아오면 초기화를 요청한다. `--timeout 1000`의 단위는 밀리초로, 최대 1초 동안 응답을 기다린다.

```bash
gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

응답은 `data: true`여야 한다. 터미널 B의 상태 출력을 `Ctrl+C`로 끝내고 거리 토픽을 출력하면 0을 확인할 수 있다. Protobuf 기본값 생략으로 0이 빈 메시지로 보일 수 있다.

```bash
gz topic -e -t /tutorial_bot/diagnostics/distance
```

잘못된 메시지 타입도 시험한다. 터미널 C에서 다음 메시지를 발행해도 `Boolean` 구독자에는 전달되지 않아 활성화 상태가 그대로여야 한다. CLI의 종료 코드만으로 거부 여부를 판정하지 말고 상태를 다시 관찰한다.

```bash
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.StringMsg -p 'data: "false"'
```

## ROS 2에서 관측하기

거리와 상태 토픽은 브리지에서 ROS 표준 메시지로 변환한다. 터미널 C에서 다음 명령을 실행해 둔다. `[`는 Gazebo에서 ROS 2로만 전달한다는 뜻이다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  '/tutorial_bot/diagnostics/distance@std_msgs/msg/Float64[gz.msgs.Double' \
  '/tutorial_bot/diagnostics/status@std_msgs/msg/String[gz.msgs.StringMsg'
```

다른 ROS 2 터미널에서 다음처럼 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /tutorial_bot/diagnostics/distance --once
ros2 topic echo /tutorial_bot/diagnostics/status --once
```

초기화는 요청·응답 계약까지 포함하므로 이 과정에서는 Gazebo Transport 서비스로 유지한다. ROS 서비스가 제품 요구사항이라면 `ros_gz_bridge`가 지원하는 서비스 타입 조합인지 확인하거나, 별도의 작은 ROS 중계 노드에서 Gazebo Transport 요청을 호출하도록 경계를 명시한다.

## 자동 검증

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario transport --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["status"] == "PASS"; print("transport=PASS")' "$run_dir/scenario.json"
```

저장소 최상위에서 실행한다. `transport`는 비활성화 중 거리 유지, 재활성화, 초기화 및 동시 요청을 확인한다. 잘못된 타입 검사는 별도 시나리오로 실행한다.

```bash
./scripts/check_advanced_course.sh \
  --scenario transport-wrong-types \
  --install-base "$TUTORIAL_INSTALL_BASE" \
  --evidence "$run_dir/wrong-types"
python3 -m json.tool "$run_dir/wrong-types/scenario.json"
```

`status`가 `PASS`이고 `plugin_alive`가 `true`여야 한다. 테스트를 마치면 수동으로 실행한 브리지와 서버도 각각 `Ctrl+C`로 종료한다.

## 문제 해결

| 증상 | 원인 후보 | 확인 방법 |
| --- | --- | --- |
| 토픽이 보이지 않음 | 플러그인 로드 실패, 다른 통신 그룹 | 서버 로그와 `GZ_PARTITION`을 확인한다. |
| 서비스 시간 초과 | 요청·응답 타입 불일치 | 계약의 protobuf 타입과 CLI 인자를 비교한다. |
| 비활성화 뒤 거리 증가 | 콜백에서 직접 변경, 명령 보관함 미소비 | `ApplyPendingCommands` 호출 순서를 확인한다. |
| 브리지 실행 후 ROS 토픽 없음 | 브리지 타입 문자열 오류 | `ros2 node info /parameter_bridge`와 양쪽 토픽 목록을 본다. |
| 동시 초기화 불안정 | 콜백과 갱신 코드가 같은 상태를 동시에 변경 | ThreadSanitizer 테스트와 뮤텍스로 보호하는 범위를 확인한다. |

## 출처

- [Gazebo Transport 발행·구독](https://gazebosim.org/api/transport/13/messages.html)
- [Gazebo Transport 요청·응답](https://gazebosim.org/api/transport/13/requestresponse.html)
- [ros_gz_bridge Jazzy API](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)

[이전: ECS 시스템 플러그인](01-ecs-system-plugin.md) · [다음: 물리와 주기 디버깅](03-physics-debugging.md)
