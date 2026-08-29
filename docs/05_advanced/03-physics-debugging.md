# 물리와 주기 디버깅

> **목표:** physics step, 발행 주기, simulation time을 분리하고 동일한 simulation 구간의 실제 표본 수를 비교한다.
> **선행 학습:** [Transport 인터페이스](02-transport-interfaces.md)

## 세 가지 시간 값을 분리하기

`max_step_size`는 physics가 한 번 갱신될 때 증가하는 simulation time이고, `real_time_factor`는 simulation time이 wall time에 대해 얼마나 빠르게 진행되기를 원하는지 나타내는 목표값이다. 플러그인의 `publish_period`는 진단 메시지 사이의 simulation time 간격이다. host FPS와 실제 real-time factor는 CPU 부하에 따라 흔들리므로 테스트의 기준으로 사용하지 않는다.

physics step을 \(h\), 발행 주기를 \(T_p\), 검증할 simulation 구간을 \(T\)라 두면 대략 다음 관계가 성립한다.

\[
N_{update} \approx \frac{T}{h}, \qquad
N_{publish} \approx \frac{T}{T_p}
\]

이 저장소는 같은 2초를 서로 다른 두 world로 실행한다.

| world | `max_step_size` | iterations | simulation 구간 | `publish_period` | 예상 표본 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `advanced-fast.sdf` | 0.001 s | 2000 | 2.0 s | 0.05 s | 약 40개 |
| `advanced-slow.sdf` | 0.004 s | 500 | 2.0 s | 0.20 s | 약 10개 |

<figure class="course-figure" id="advanced-sim-time-debug" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/sim-time-debug.svg" alt="같은 2초 simulation에서 0점05초와 0점2초 publish 주기의 메시지 수를 비교하는 막대 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 같은 simulation time에서 발행 주기가 네 배 차이면 실제 메시지 수도 약 네 배 차이가 난다.</figcaption>
</figure>

## 재현 가능한 world 구성하기

빠른 발행 world의 physics와 플러그인 설정은 다음과 같다. `type="ignored"`는 특정 physics engine 이름에 검증이 종속되지 않도록 하는 SDF 표현이다.

```xml
<world name="advanced_fast">
  <gravity>0 0 0</gravity>
  <physics name="deterministic_step" type="ignored">
    <max_step_size>0.001</max_step_size>
    <real_time_factor>1</real_time_factor>
  </physics>
  <plugin filename="gz-sim-physics-system"
          name="gz::sim::systems::Physics"/>
  <plugin filename="libTutorialBotDiagnosticsSystem.so"
          name="gz::sim::systems::TutorialBotDiagnostics">
    <model_name>tutorial_bot</model_name>
    <distance_topic>/tutorial_bot/fast/diagnostics/distance</distance_topic>
    <publish_period>0.05</publish_period>
    <world_stats_topic>/world/advanced_fast/stats</world_stats_topic>
    <final_stats_iteration>2000</final_stats_iteration>
  </plugin>
  <model name="tutorial_bot">
    <static>true</static>
    <link name="base_link"/>
  </model>
</world>
```

느린 발행 world에서는 다음 값만 달라진다.

```xml
<physics name="deterministic_step" type="ignored">
  <max_step_size>0.004</max_step_size>
  <real_time_factor>1</real_time_factor>
</physics>

<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <distance_topic>/tutorial_bot/slow/diagnostics/distance</distance_topic>
  <publish_period>0.20</publish_period>
  <world_stats_topic>/world/advanced_slow/stats</world_stats_topic>
  <final_stats_iteration>500</final_stats_iteration>
</plugin>
```

`final_stats_iteration`은 플러그인이 마지막 `UpdateInfo`를 `WorldStatistics`로 발행하게 하는 이 튜토리얼 전용 파라미터이다. 일반 world에서는 기본 `/world/<world_name>/stats`를 관측해도 되지만, 종료 직전의 정확한 iteration을 테스트 증거로 남기기 위해 사용한다.

## simulation time으로 발행 제한하기

플러그인은 wall clock이 아니라 `UpdateInfo::simTime`을 저장한다. simulation이 되감기면 새 기준으로 다시 발행하도록 `simTime < lastPublishTime`도 처리한다.

```cpp
const bool periodElapsed = !lastPublishTime_.has_value() ||
  simTime < *lastPublishTime_ ||
  simTime - *lastPublishTime_ > publishPeriod_;
if (!stateChanged_ && !periodElapsed) {
  return;
}

distancePublisher_.Publish(distance);
lastPublishTime_ = simTime;
```

주기 경계에서 `>`와 `>=` 중 무엇을 선택하느냐에 따라 긴 실행에서 한 표본 정도 차이가 날 수 있다. 따라서 검증은 정확히 40:10을 요구하지 않고 비율 3–5와 simulation 종료 시간을 함께 확인한다.

## 수동으로 두 world 비교하기

```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH="$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib"
world_root="$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds"

export GZ_PARTITION="tutorial_physics_fast_$$"
gz topic -e --json-output -t /tutorial_bot/fast/diagnostics/distance \
  > /tmp/fast-distance.log &
fast_echo_pid=$!
gz sim -s -r --iterations 2000 "$world_root/advanced-fast.sdf"
kill "$fast_echo_pid" 2>/dev/null || true

wc -l /tmp/fast-distance.log
```

느린 world도 별도 `GZ_PARTITION`으로 같은 절차를 반복한다. 서로 다른 실행이 같은 discovery partition에 섞이면 이전 server나 subscriber가 표본 수를 오염시킬 수 있다.

## 자동 비교 실험

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario physics --sim-seconds 2.0 --worlds advanced-fast.sdf,advanced-slow.sdf --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert 3 <= d["ratio"] <= 5; print("time=%.1f ratio=%.2f" % (d["sim_seconds"], d["ratio"]))' "$run_dir/scenario.json"
```

checker는 설치된 두 world를 각각 실행하고 다음을 모두 검사한다.

- stats의 `simTime`이 단조 증가하며 1.99–2.00초에 도달한다.
- server log에 설정한 `publish_period`와 `READY` 전이가 존재한다.
- distance log가 비어 있지 않다.
- fast/slow 실제 표본 수의 비율이 3–5 범위이다.

## 잘못된 주기를 고장 주입으로 확인하기

0, 음수, `nan`은 유효한 발행 주기가 아니다. 자동 보정하면 설정 오류가 숨어 재현성이 떨어진다. checker는 world 사본의 값을 바꾸고 `INVALID_CONFIG`, distance 미발행, exit 64를 함께 확인한다.

```bash
run_dir="$(mktemp -d)"
set +e
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" \
  ./scripts/check_advanced_course.sh \
  --scenario invalid-period --publish-period 0 --evidence "$run_dir"
code=$?
set -e

test "$code" -eq 64
grep INVALID_CONFIG "$run_dir/status.log"
test ! -s "$run_dir/distance.log"
```

## 디버깅 순서

1. `/world/<name>/stats`의 마지막 `simTime`을 확인한다.
2. world의 `max_step_size × iterations`와 목표 simulation 구간을 비교한다.
3. 플러그인의 `publish_period`가 유한한 양수인지 확인한다.
4. server log에서 실제로 파싱된 주기를 확인한다.
5. topic log의 실제 표본 수와 simulation timestamp 단조성을 확인한다.
6. 마지막에만 wall time과 real-time factor를 성능 지표로 살핀다.

## 문제 해결

| 증상 | 해석 | 조치 |
| --- | --- | --- |
| 표본이 모두 0개 | plugin 또는 subscriber가 준비되지 않음 | plugin 경로, partition, topic 이름을 확인한다. |
| 비율은 맞지만 종료 시간이 다름 | iterations와 step 조합 오류 | `max_step_size × iterations`를 다시 계산한다. |
| 빠른 world만 간헐적으로 적음 | subscriber discovery 지연 | subscriber 준비 뒤 server를 시작한다. |
| 느린 host에서만 실패 | wall time을 판정 기준으로 사용 | stats의 simulation time 기준으로 바꾼다. |
| `nan` 주기로 계속 실행 | 설정 검증 누락 | `std::isfinite`와 양수 검사를 추가한다. |

## 출처

- [Gazebo Sim server configuration](https://gazebosim.org/api/sim/8/server_config.html)
- [SDFormat physics specification](https://sdformat.org/spec?ver=1.10&elem=physics)

[이전: Transport 인터페이스](02-transport-interfaces.md) · [다음: Headless 통합 테스트](04-headless-integration.md)
