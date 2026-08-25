# Transport 인터페이스

> **목표:** publish/subscribe와 request/reply endpoint의 타입을 확인하고 callback thread와 update thread의 경계를 검증합니다.
> **선행 학습:** [ECS System Plugin](01-ecs-system-plugin.md)

## endpoint 계약

진단 System은 거리 `gz.msgs.Double`과 상태 `gz.msgs.StringMsg`를 발행합니다. `/tutorial_bot/diagnostics/enable`은 `gz.msgs.Boolean`을 구독하고, `/tutorial_bot/diagnostics/reset`은 `gz.msgs.Empty` 요청에 `gz.msgs.Boolean`로 응답합니다. ROS 2 의존성은 plugin에 넣지 않습니다.

<figure class="course-figure" id="advanced-transport-boundary" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/transport-boundary.svg" alt="Transport callback이 mailbox를 거쳐 simulation update에서 ECS 상태에 적용되는 thread 경계도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. Transport callback은 명령만 mailbox에 기록하고 ECS 상태 전이는 simulation update가 소유합니다.</figcaption>
</figure>

## 왜 thread 경계가 필요한가

Transport callback은 simulation update와 다른 thread에서 실행될 수 있습니다. callback이 누적 거리나 ECS entity를 직접 변경하면 읽기·쓰기 순서가 실행마다 달라집니다. 구현은 callback에서 작은 command를 동기화해 보관하고, 다음 `PostUpdate`에서 한 번만 꺼내 적용합니다. reset 응답은 적용 결과를 기다려 bound model이면 `true`, unbound이면 `false`를 반환합니다.

## 실제 endpoint 실행

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario transport --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["status"] == "PASS"; print("transport=PASS")' "$run_dir/scenario.json"
```

checker는 enable false/true와 reset을 실제 endpoint에 보내고, 잘못된 request type이 상태를 바꾸지 않는지도 확인합니다. 단순 endpoint 목록이나 `PASS` banner만으로는 성공하지 않습니다.

## 문제 해결

service가 보이지만 timeout이면 request·response protobuf 타입을 계약과 비교합니다. disable 뒤 거리가 계속 늘면 callback에서 상태를 직접 변경했거나 update에서 mailbox를 소비하지 않은 것입니다. 동시 reset이 불안정하면 응답 완료와 command 적용 사이의 condition을 한 소유권 경계에서 추적합니다.

## 출처

- [Gazebo Transport publish/subscribe](https://gazebosim.org/api/transport/13/messages.html)
- [Gazebo Transport request/reply](https://gazebosim.org/api/transport/13/requestresponse.html)

[이전: ECS System Plugin](01-ecs-system-plugin.md) · [다음: 물리와 주기 디버깅](03-physics-debugging.md)
