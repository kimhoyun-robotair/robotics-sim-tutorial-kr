# 프로젝트: 시뮬레이션 통합 검증

> **프로젝트 목표:** 시스템 플러그인과 통신·발행 주기 검사를 새 설치 경로에서 함께 실행하고, 정상 동작과 오류 처리 결과를 확인한다.
> **선행 학습:** [CI 재현성](05-ci-reproducibility.md)

## 프로젝트의 완료 상태

앞 장에서 만든 기능을 새 환경에서 함께 검증한다. 이전 빌드 파일이나 다른 Gazebo 프로세스의 메시지가 결과에 섞이지 않도록 새 설치 경로와 독립된 통신 그룹을 사용한다. 명령이 끝났다는 사실뿐 아니라 실제 메시지 값과 실행한 프로세스의 종료 기록도 확인한다.

<figure class="course-figure" id="advanced-production-stack" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/production-stack.svg" alt="새 설치 파일을 중심으로 모델 상태, 통신, 물리 주기, 서버 종료 검사를 묶는 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 네 가지 실행 검사는 같은 커밋에서 새로 빌드한 설치 파일을 사용한다.</figcaption>
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

## 1단계: 깨끗한 설치 만들기

저장소 최상위에서 시작하고 이 장의 명령은 같은 터미널에서 순서대로 실행한다. 이전 설치 환경이 남지 않도록 새 터미널을 사용한다. [설치 장](../02_getting-started/02_installation-jazzy.md)의 의존성 설치가 선행되어야 한다.

```bash
export TUTORIAL_REPO="$PWD"
source /opt/ros/jazzy/setup.bash
cd "$TUTORIAL_REPO/examples/ros2_ws"

build_dir="$(mktemp -d)"
install_dir="$(mktemp -d)"
log_dir="$(mktemp -d)"

colcon --log-base "$log_dir" build \
  --build-base "$build_dir" \
  --install-base "$install_dir" \
  --packages-up-to \
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

`source "$install_dir/setup.bash"`가 설치된 환경 설정을 적용하면 `GZ_SIM_SYSTEM_PLUGIN_PATH`에 `tutorial_bot_plugins/lib`가 들어간다. 아래 파일 확인이나 경로 검색이 실패하면 다음 단계로 넘어가기 전에 빌드 로그를 확인한다.

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
cd "$TUTORIAL_REPO"
```

플러그인 테스트는 단순 생성 여부만 보지 않는다.

| 테스트 축 | 확인 내용 |
| --- | --- |
| 거리 | 첫 자세는 기준점, 다음 자세부터 평면 거리 누적 |
| 모델 생성·제거 | 제거 후 누적 중단, 재생성 후 거리 0부터 기록 |
| 활성화·초기화 | 콜백이 보관한 명령을 갱신 스레드가 적용 |
| 동시 요청 | 동시에 들어온 초기화의 응답과 플러그인 생존 |
| 물리 계산 주기 | 서로 다른 계산 간격에서 시뮬레이션 시간 기반 발행 |
| 난수 상태 분리 | 플러그인이 다른 코드의 전역 난수 상태를 바꾸지 않음 |

## 3단계: 네 가지 실행 시나리오 확인하기

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

각 검사 로그 뒤에 다음 문장이 출력돼야 한다.

```text
advanced-checker=PASS scenarios=4
```

각 시나리오의 완료 조건은 다음과 같다.

| 시나리오 | 자극 | 실제 관측 | 성공 기준 |
| --- | --- | --- | --- |
| `distance` | 모델 자세를 x=1로 변경 | 거리 토픽 | 0과 양수 표본을 모두 관측 |
| `transport` | 비활성화, 이동, 활성화, 초기화 | 상태와 거리 | 비활성화 중 거리 유지, 재활성화 후 누적, 초기화 후 0 |
| `physics` | 두 월드를 각각 2초 실행 | 통계와 거리 | 목표 시뮬레이션 시간 도달, 표본 비율 3–5 |
| `nominal` | `cmd_vel`, 브리지, 초기화 | Gazebo 거리와 ROS 자세 | 양쪽에서 이동 확인, 초기화, 프로세스 종료 확인 |

`trap ... EXIT`는 코드 블록 직후가 아니라 현재 셸이 끝날 때 임시 디렉터리를 삭제한다. 4·5단계는 같은 터미널에서 이어서 실행한다. 검증 결과를 보관하려면 삭제용 `trap`을 설정하지 않고 별도 결과 디렉터리를 지정한다.

## 4단계: JSON을 직접 판정하기

사람이 로그를 눈으로 읽는 것만으로는 자동 검사가 되지 않는다. 예를 들어 정상 결과는 필요한 필드가 존재하고 수치 조건을 만족하는지 검사한다.

```bash
python3 - "$run_dir/nominal/scenario.json" "$run_dir/nominal/cleanup.json" <<'PY'
import json
import sys

scenario = json.load(open(sys.argv[1], encoding="utf-8"))
cleanup = json.load(open(sys.argv[2], encoding="utf-8"))

assert scenario["status"] == "PASS"
assert scenario["plugin_distance"] >= 0.1
assert scenario["ros_planar_displacement"] >= 0.05
assert scenario["post_reset_distance"] <= 1e-6
assert cleanup["status"] == "clean"
assert cleanup["survivors"] == []
assert cleanup["identity_mismatch"] is False
print("nominal 수치와 프로세스 종료 확인 완료")
PY
```

필드 이름은 `scripts/check_advanced_headless.sh`가 만드는 실제 스키마와 함께 변경해야 한다. 검증 도구와 문서에서 서로 다른 키를 기대하면 성공 결과도 사용할 수 없다.

## 5단계: 고장 주입으로 자동 검사 시험하기

정상 시나리오만 통과하면 검증 도구가 아무것도 확인하지 않는 상태여도 알아차리기 어렵다. 다음 오류가 의도한 종료 코드와 증거를 만드는지 확인한다.

| 오류 | 기대 종료 | 기대 증거 |
| --- | ---: | --- |
| 존재하지 않는 모델 | 20 | `WAITING_FOR_MODEL` |
| 존재하지 않는 플러그인 라이브러리 | 21 | 실제 라이브러리 로드 실패 로그 |
| 내부 준비 상태 확인 제한 시간 | 124 | 제한 시간을 정한 위치와 시간(초) |
| SIGINT | 130 | 신호로 종료됐다는 기록과 남은 프로세스 0개 |
| PID 식별 정보 불일치 | 70 | 프로세스 종료 처리 실패 기록 |
| 잘못된 인자·설치 경로 | 64 | 사용법 또는 설치 파일 오류 |

예를 들어 모델 생성·제거 시나리오는 월드 서비스로 개체를 실제 생성하고 제거한 뒤 상태 순서를 확인한다.

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

- 시스템은 `Configure`에서 설정을 검증하고 `PostUpdate`에서 읽기 전용 ECS 관측을 수행한다.
- 플러그인 별칭, 공유 라이브러리 이름, SDF `filename`이 일치한다.
- 설치 환경 설정 훅 또는 명시적 플러그인 검색 경로로 `.so`를 찾을 수 있다.
- 활성화·초기화 콜백은 명령 보관함만 갱신하고 실제 시뮬레이션 상태는 갱신 스레드에서 변경한다.
- 물리 계산 검사는 실제 경과 시간이 아니라 시뮬레이션 시간과 실제 표본을 사용한다.
- GUI 없는 정상 시나리오에서 플러그인 거리와 ROS 자세가 모두 변한다.
- 각 시나리오가 실행한 프로세스가 모두 종료됐다는 기록을 남긴다.
- 모든 실행 입력은 같은 설치 경로와 소스 커밋 SHA에서 나온다.
- CI 실패 경로에서도 재현에 필요한 로그와 JSON이 남는다.

## 문제 해결

시나리오 하나만 실패하면 해당 디렉터리의 `scenario.json`, 토픽 로그, 서버 로그, `cleanup.json` 순서로 확인한다. 여러 시나리오가 동시에 실패하면 설치 경로, 플러그인 검색 경로, `GZ_PARTITION`부터 확인한다. 이전 검증 결과와 소스 커밋 SHA가 다르면 결과를 섞지 않고 새 빌드부터 다시 실행한다.

## 출처

- [Gazebo Sim systems API](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Transport API](https://gazebosim.org/api/transport/13/tutorials.html)
- [GitHub Actions artifacts](https://docs.github.com/actions/using-workflow-data/storing-workflow-data-as-artifacts)

[이전: CI 재현성](05-ci-reproducibility.md) · [과정 처음으로](index.md)
