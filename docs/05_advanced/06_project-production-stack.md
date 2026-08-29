# 프로젝트: Production-style Simulation Stack

> **프로젝트 목표:** System Plugin, Transport, physics cadence, headless harness, CI 계약을 fresh install과 하나의 검증 matrix로 연결한다.
> **선행 학습:** [CI 재현성](05-ci-reproducibility.md)

## 프로젝트의 완료 상태

이 프로젝트는 새 기능 하나를 더 만드는 단계가 아니다. 앞 장에서 만든 조각이 source tree의 우연한 파일이나 실행 중인 다른 Gazebo process에 의존하지 않는지 확인하는 통합 단계이다. 모든 scenario는 같은 install base를 사용하고 process exit뿐 아니라 실제 관측값과 cleanup receipt를 판정한다.

<figure class="course-figure" id="advanced-production-stack" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/production-stack.svg" alt="fresh install을 중심으로 lifecycle Transport physics headless cleanup checker가 결합되는 production stack 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 전체 checker는 네 runtime 축을 같은 fresh install과 source SHA에 묶어 검증한다.</figcaption>
</figure>

완성된 경로에서 중요한 파일은 다음과 같다.

```text
examples/ros2_ws/src/
├── tutorial_bot_plugins/
│   ├── include/tutorial_bot_plugins/tutorial_bot_diagnostics.hpp
│   ├── src/tutorial_bot_diagnostics.cpp
│   ├── config/diagnostics-contract.yaml
│   └── test/test_diagnostics_*.cpp
├── tutorial_bot_gazebo/worlds/
│   ├── advanced-diagnostics.sdf
│   ├── advanced-fast.sdf
│   └── advanced-slow.sdf
└── tutorial_bot_tests/test_advanced_*.py
scripts/
├── check_advanced_contract.py
├── check_advanced_course.sh
├── check_advanced_headless.sh
└── ci/run_ros_gazebo_container.sh
```

## 1단계: 깨끗한 install 만들기

이전 build 결과가 새 source 오류를 가리지 않도록 고급 과정 package를 새 경로에 빌드한다.

```bash
cd examples/ros2_ws
source /opt/ros/jazzy/setup.bash

build_dir="$(mktemp -d)"
install_dir="$(mktemp -d)"
log_dir="$(mktemp -d)"

colcon --log-base "$log_dir" build \
  --build-base "$build_dir" \
  --install-base "$install_dir" \
  --packages-select \
    tutorial_bot_plugins \
    tutorial_bot_description \
    tutorial_bot_control \
    tutorial_bot_gazebo \
    tutorial_bot_bringup \
    tutorial_bot_tests \
  --cmake-args -DBUILD_TESTING=ON

source "$install_dir/setup.bash"
export TUTORIAL_INSTALL_BASE="$install_dir"
```

`source install/setup.bash` 뒤 DSV hook이 구성돼 있으면 `GZ_SIM_SYSTEM_PLUGIN_PATH`에 `tutorial_bot_plugins/lib`가 들어간다. 확인되지 않으면 다음처럼 계약을 즉시 실패시킨다.

```bash
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
printf '%s\n' "$GZ_SIM_SYSTEM_PLUGIN_PATH" | tr ':' '\n' | grep tutorial_bot_plugins/lib
```

## 2단계: 단위와 통합 테스트 실행하기

```bash
colcon --log-base "$log_dir/test" test \
  --build-base "$build_dir" \
  --install-base "$install_dir" \
  --executor sequential \
  --packages-select tutorial_bot_plugins tutorial_bot_tests

colcon test-result --test-result-base "$build_dir" --verbose
```

플러그인 테스트는 단순 생성 여부만 보지 않는다.

| 테스트 축 | 확인 내용 |
| --- | --- |
| distance | 첫 자세는 기준점, 다음 자세부터 평면 거리 누적 |
| model lifecycle | 제거 후 동결, 재생성 후 0 기준점 |
| enable/reset | callback mailbox와 update thread 적용 |
| concurrency | 동시에 들어온 reset의 응답과 plugin 생존 |
| physics cadence | 서로 다른 step에서 simulation time 기반 발행 |
| RNG isolation | 플러그인이 전역 난수 상태를 오염시키지 않음 |

## 3단계: runtime scenario matrix 실행하기

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario distance --evidence "$run_dir/distance"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario transport --evidence "$run_dir/transport"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario physics --sim-seconds 2.0 --worlds advanced-fast.sdf,advanced-slow.sdf --evidence "$run_dir/physics"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario nominal --evidence "$run_dir/nominal"
python3 -c 'import json,sys; paths=sys.argv[1:]; assert all(json.load(open(p))["status"] in {"PASS", "pass"} for p in paths); print("advanced-checker=PASS scenarios=4")' "$run_dir/distance/scenario.json" "$run_dir/transport/scenario.json" "$run_dir/physics/scenario.json" "$run_dir/nominal/scenario.json"
```

예상 출력은 다음 한 줄이다.

```text
advanced-checker=PASS scenarios=4
```

각 scenario의 완료 조건은 다음과 같다.

| scenario | 자극 | 실제 관측 | 성공 기준 |
| --- | --- | --- | --- |
| `distance` | model pose를 x=1로 변경 | distance topic | 0과 양수 표본을 모두 관측 |
| `transport` | disable, 이동, enable, reset | status와 distance | disable 중 동결, 재활성, reset 0 |
| `physics` | 2초씩 fast/slow world 실행 | stats와 distance | sim time 도달, 표본 비율 3–5 |
| `nominal` | `cmd_vel`, bridge, reset | Gazebo distance와 ROS pose | 양쪽 이동, reset, clean 종료 |

임시 evidence는 예제 명령 종료 시 삭제된다. 회귀 분석이나 CI artifact가 목적이라면 `trap`을 제거하고 source SHA가 포함된 영구 경로를 지정한다.

## 4단계: JSON을 직접 판정하기

사람이 로그를 눈으로 읽는 것만으로는 자동 gate가 되지 않는다. 예를 들어 nominal 결과는 필요한 field가 존재하고 수치 조건을 만족하는지 검사한다.

```bash
python3 - "$run_dir/nominal/scenario.json" "$run_dir/nominal/cleanup.json" <<'PY'
import json
import sys

scenario = json.load(open(sys.argv[1], encoding="utf-8"))
cleanup = json.load(open(sys.argv[2], encoding="utf-8"))

assert scenario["status"] == "PASS"
assert scenario["plugin_distance"] >= 0.1
assert scenario["ros_displacement"] >= 0.05
assert scenario["reset_distance"] <= 1e-6
assert cleanup["status"] == "clean"
assert cleanup["survivors"] == []
PY
```

필드 이름은 `scripts/check_advanced_headless.sh`가 만드는 실제 schema와 함께 변경해야 한다. checker와 문서에서 서로 다른 키를 기대하면 성공 결과도 사용할 수 없다.

## 5단계: 고장 주입으로 gate 시험하기

정상 scenario만 통과하면 checker가 아무것도 확인하지 않는 상태여도 알아차리기 어렵다. 다음 fault가 의도한 종료 코드와 증거를 만드는지 확인한다.

| fault | 기대 종료 | 기대 증거 |
| --- | ---: | --- |
| 존재하지 않는 model | 20 | `WAITING_FOR_MODEL` |
| 존재하지 않는 plugin library | 21 | 실제 load failure log |
| 내부 readiness deadline | 124 | deadline source와 seconds |
| SIGINT | 130 | signal 종료와 survivor 0 |
| PID identity mismatch | 70 | cleanup failure receipt |
| 잘못된 인자·설치 경로 | 64 | usage 또는 contract 오류 |

예를 들어 model lifecycle은 world service로 entity를 실제 생성하고 제거한 뒤 상태 순서를 확인한다.

```bash
./scripts/check_advanced_course.sh \
  --scenario model-lifecycle \
  --evidence "$run_dir/model-lifecycle"

python3 - "$run_dir/model-lifecycle/scenario.json" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["transitions"] == [
    "WAITING_FOR_MODEL", "READY", "MODEL_REMOVED", "READY"
]
assert result["respawn_distance"] == 0
PY
```

## 최종 완료 조건

- System은 `Configure`에서 설정을 검증하고 `PostUpdate`에서 읽기 전용 ECS 관측을 수행한다.
- plugin alias, 공유 라이브러리 이름, SDF `filename`이 일치한다.
- 설치 환경 hook 또는 명시적 plugin path로 `.so`를 찾을 수 있다.
- enable·reset callback은 mailbox만 갱신하고 simulation 상태는 update thread가 소유한다.
- physics 검사는 wall time이 아니라 simulation time과 실제 표본을 사용한다.
- headless nominal에서 plugin distance와 ROS pose가 모두 움직인다.
- 모든 scenario의 cleanup receipt가 survivor 0을 나타낸다.
- 모든 runtime 입력은 같은 install base와 source SHA에서 나온다.
- CI 실패 경로에서도 재현에 필요한 logs와 JSON이 남는다.

## 문제 해결

scenario 하나만 실패하면 해당 directory의 `scenario.json`, topic log, server log, `cleanup.json` 순서로 확인한다. 여러 scenario가 동시에 실패하면 install base, plugin path, `GZ_PARTITION`부터 확인한다. 이전 evidence와 source SHA가 다르면 결과를 섞지 않고 fresh build부터 다시 실행한다.

## 출처

- [Gazebo Sim systems API](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Transport API](https://gazebosim.org/api/transport/13/tutorials.html)
- [GitHub Actions artifacts](https://docs.github.com/actions/using-workflow-data/storing-workflow-data-as-artifacts)

[이전: CI 재현성](05-ci-reproducibility.md) · [과정 처음으로](index.md)
