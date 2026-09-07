# 물리와 주기 디버깅

> **목표:** 물리 계산 간격, 발행 주기, 시뮬레이션 시간을 분리하고 동일한 시뮬레이션 구간의 실제 표본 수를 비교한다.
> **선행 학습:** [Transport 인터페이스](02-transport-interfaces.md)

## 세 가지 시간 값을 분리하기

`max_step_size`는 물리 계산 한 번이 진행시키는 시뮬레이션 시간이다. `real_time_factor`는 실제 1초 동안 시뮬레이션이 몇 초 진행되기를 원하는지 정하는 목표값이다. 예를 들어 1은 실제 시간과 같은 속도가 목표라는 뜻이며, 컴퓨터가 느리면 이 속도를 달성하지 못할 수 있다. 플러그인의 `publish_period`는 메시지 발행 간격을 시뮬레이션 시간으로 지정한다. 화면의 초당 프레임 수(FPS)와 구분한다.

물리 계산 간격을 \(h\), 발행 주기를 \(T_p\), 검증할 시뮬레이션 구간을 \(T\)라 두면 대략 다음 관계가 성립한다.

\[
N_{update} \approx \frac{T}{h}, \qquad
N_{publish} \approx \frac{T}{T_p}
\]

이 저장소는 같은 2초를 서로 다른 두 월드로 실행한다.

| 월드 | `max_step_size` | 계산 횟수 | 시뮬레이션 구간 | `publish_period` | 예상 표본 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `advanced-fast.sdf` | 0.001 s | 2000 | 2.0 s | 0.05 s | 약 40개 |
| `advanced-slow.sdf` | 0.004 s | 500 | 2.0 s | 0.20 s | 약 10개 |

<figure class="course-figure" id="advanced-sim-time-debug" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/sim-time-debug.svg" alt="가상 시간 2초 동안 발행 주기 0.05초와 0.2초의 메시지 수를 비교하는 막대 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 같은 시뮬레이션 시간 동안 발행 주기가 네 배 차이 나면 메시지 수도 약 네 배 차이 난다.</figcaption>
</figure>

## 재현 가능한 월드 구성하기

다음은 빠른 발행 월드의 핵심 설정이다. Gazebo Sim은 Physics 시스템이 물리 엔진 플러그인을 로드하므로 이 예제는 SDF의 엔진 종류에 `type="ignored"`를 쓴다. 물리 계산을 끈다는 뜻이 아니다. 전체 파일은 `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/advanced-fast.sdf`에 있으며, 상태·활성화·초기화용 토픽과 서비스 이름도 각각 지정되어 있다.

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

느린 발행 월드에서는 다음 값만 달라진다.

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

`final_stats_iteration`은 플러그인이 마지막 `UpdateInfo`를 `WorldStatistics`로 발행하게 하는 이 튜토리얼 전용 파라미터이다. 일반 월드에서는 기본 `/world/<world_name>/stats`를 관측해도 되지만, 종료 직전의 정확한 계산 횟수을 테스트 증거로 남기기 위해 사용한다.

## 시뮬레이션 시간으로 발행 제한하기

플러그인은 실제 경과 시간 대신 `UpdateInfo::simTime`을 저장한다. 시뮬레이션 시간이 이전으로 돌아가면 새 기준으로 다시 발행하도록 `simTime < lastPublishTime`도 처리한다.

```cpp
const bool periodElapsed = !lastPublishTime_.has_value() ||
  simTime < *lastPublishTime_ ||
  simTime - *lastPublishTime_ > publishPeriod_;
if (!stateChanged_ && !periodElapsed) {
  return;
}

gz::msgs::Double distance;
distance.set_data(distance_);
distancePublisher_.Publish(distance);
lastPublishTime_ = simTime;
```

이 발췌는 발행 시각을 결정하는 부분이다. 실제 `Publish` 함수는 상태 변경 직후에도 메시지를 발행한다. 또 비교식이 `>`이므로 시간 차이가 주기와 정확히 같으면 다음 물리 계산까지 기다린다. 예를 들어 주기 0.05초·계산 간격 0.001초라면 정상 상태의 발행 간격이 0.051초가 될 수 있고, 차이는 실행 시간이 길수록 누적된다. 따라서 검증은 정확히 40개와 10개를 요구하지 않고 비율 3–5와 종료 시뮬레이션 시간을 함께 확인한다.

## 1단계: 정해진 계산 횟수만 실행하기

[고급 과정 개요](index.md)의 빌드와 환경 설정을 마친 터미널에서 실행한다. `TUTORIAL_INSTALL_BASE`는 그때 설정한 설치 디렉터리다.

```bash
world_root="$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds"
export GZ_PARTITION=tutorial_bot_physics_manual
gz sim -s -r --iterations 2000 "$world_root/advanced-fast.sdf"
gz sim -s -r --iterations 500 "$world_root/advanced-slow.sdf"
```

각 명령이 지정된 계산 횟수 뒤에 종료돼야 한다. 물리 계산 간격과 횟수의 곱은 두 경우 모두 2초다. 실제로 걸리는 시간은 다를 수 있다.

메시지 수를 비교하려면 발행 전에 구독자를 준비하고 실행이 끝날 때까지 수집해야 한다. 사람이 중간에 토픽 출력을 켜면 초기 표본을 놓칠 수 있으므로 아래 자동 검사에서 수집한 결과로 판정한다.

## 2단계: 발행 횟수 자동 비교

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario physics --sim-seconds 2.0 --worlds advanced-fast.sdf,advanced-slow.sdf --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert 3 <= d["ratio"] <= 5; print("time=%.1f ratio=%.2f" % (d["sim_seconds"], d["ratio"]))' "$run_dir/scenario.json"
```

저장소 최상위에서 실행한다. 실제 수집 값은 `scenario.json`의 `fast_messages`, `slow_messages`, `ratio`에 기록된다. 검증 도구는 설치된 두 월드를 각각 실행하고 다음을 검사한다.

- 수집한 통계의 `simTime`이 이전 값보다 증가하며 1.99–2.00초에 도달한다.
- 서버 로그에 설정한 `publish_period`와 `READY` 전이가 존재한다.
- 거리 로그가 비어 있지 않다.
- 빠른 월드와 느린 월드의 실제 표본 수의 비율이 3–5 범위이다.

## 잘못된 주기를 고장 주입으로 확인하기

0, 음수, `nan`은 유효한 발행 주기가 아니다. 자동 보정하면 설정 오류가 숨어 재현성이 떨어진다. 검증 도구는 월드 사본의 값을 바꾸고 `INVALID_CONFIG`, 거리 미발행, 종료 코드 64를 함께 확인한다.

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
2. 월드의 `max_step_size × iterations`와 목표 시뮬레이션 구간을 비교한다.
3. 플러그인의 `publish_period`가 유한한 양수인지 확인한다.
4. 서버 로그에서 실제로 파싱된 주기를 확인한다.
5. 토픽 로그의 실제 표본 수와 통계 메시지의 시뮬레이션 시간이 증가하는지을 확인한다.
6. 마지막에만 실제 경과 시간과 실시간 비율을 성능 지표로 살핀다.

## 문제 해결

| 증상 | 해석 | 조치 |
| --- | --- | --- |
| 표본이 모두 0개 | 플러그인 또는 구독자가 준비되지 않음 | 플러그인 경로, 통신 그룹, 토픽 이름을 확인한다. |
| 비율은 맞지만 종료 시간이 다름 | 계산 횟수와 간격 조합 오류 | `max_step_size × iterations`를 다시 계산한다. |
| 빠른 월드만 간헐적으로 적음 | 구독자 통신 대상 검색 지연 | 구독자 준비 뒤 서버를 시작한다. |
| 느린 실행 컴퓨터에서만 실패 | 실제 경과 시간을 판정 기준으로 사용 | stats의 시뮬레이션 시간 기준으로 바꾼다. |
| `nan` 주기로 계속 실행 | 설정 검증 누락 | `std::isfinite`와 양수 검사를 추가한다. |

## 출처

- [Gazebo Sim server configuration](https://gazebosim.org/api/sim/8/server_config.html)
- [SDFormat physics specification](https://sdformat.org/spec?ver=1.10&elem=physics)

[이전: Transport 인터페이스](02-transport-interfaces.md) · [다음: GUI 없는 통합 테스트](04-headless-integration.md)
