# 프로젝트: Production-style Simulation Stack

> **프로젝트 목표:** 다섯 장의 계약을 fresh install과 하나의 advanced matrix로 연결하고 모든 runtime 증거의 source·cleanup 일관성을 확인합니다.
> **선행 학습:** [CI 재현성](05-ci-reproducibility.md)

## 완성 구조

이 프로젝트는 새 기능을 더하지 않습니다. 이미 구현한 diagnostics System, Transport endpoints, physics cadence, headless harness를 같은 설치 산출물에서 조립합니다. 각 scenario의 완료 조건은 process exit뿐 아니라 parsed observable과 cleanup receipt입니다.

<figure class="course-figure" id="advanced-production-stack" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/production-stack.svg" alt="fresh install을 중심으로 lifecycle Transport physics headless cleanup checker가 결합되는 production stack 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 전체 checker는 네 runtime 축을 같은 fresh install과 source SHA에 묶어 검증합니다.</figcaption>
</figure>

## 전체 advanced checker 실행

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario distance --evidence "$run_dir/distance"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario transport --evidence "$run_dir/transport"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario physics --sim-seconds 2.0 --worlds advanced-fast.sdf,advanced-slow.sdf --evidence "$run_dir/physics"
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario nominal --evidence "$run_dir/nominal"
python3 -c 'import json,sys; paths=sys.argv[1:]; assert all(json.load(open(p))["status"] in {"PASS", "pass"} for p in paths); print("advanced-checker=PASS scenarios=4")' "$run_dir/distance/scenario.json" "$run_dir/transport/scenario.json" "$run_dir/physics/scenario.json" "$run_dir/nominal/scenario.json"
```

예상 출력은 `advanced-checker=PASS scenarios=4`입니다. 각 checker가 설치된 plugin library와 world를 직접 사용하며, 임시 evidence는 command 종료 시 제거됩니다. 검토용 실행에서는 trap 제거가 아니라 evidence directory를 영구 경로로 지정해 보존합니다.

## 완료 조건

- distance가 이동 뒤 증가하고 reset 뒤 0입니다.
- enable·reset endpoint가 올바른 protobuf 타입과 thread 경계를 지킵니다.
- 동일 2초 simulation의 fast/slow 표본 비율이 3–5입니다.
- headless nominal에서 plugin distance와 ROS pose가 모두 움직입니다.
- 모든 scenario의 cleanup receipt가 zero survivor입니다.
- 모든 runtime 입력은 같은 install base와 source SHA에서 왔습니다.

## 고장 주입으로 확인하기

missing model은 20, missing plugin은 21, 내부 timeout은 124, cleanup identity fault는 70이어야 합니다. 잘못된 route나 설치 인자는 계약 오류 64입니다. 의도한 fault가 0이면 checker가 실제 표본 대신 문구만 믿는지 점검합니다.

SIGINT 복구에서는 `sigint-hold` readiness 뒤 process group에 INT를 보내고 DUT 130과 zero survivor를 함께 확인합니다. 다음 실행이 같은 partition·port를 바로 재사용할 수 있어야 cleanup이 완료된 것입니다.

## 문제 해결

scenario 하나만 실패하면 해당 directory의 `scenario.json`, topic log, server log, `cleanup.json` 순으로 확인합니다. 여러 scenario가 동시에 실패하면 install base와 plugin path를 먼저 확인합니다. 이전 evidence와 source SHA가 다르면 결과를 섞지 말고 fresh build부터 다시 실행합니다.

## 출처

- [Gazebo Sim systems API](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Transport API](https://gazebosim.org/api/transport/13/tutorials.html)
- [GitHub Actions artifacts](https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts)

[이전: CI 재현성](05-ci-reproducibility.md) · [과정 처음으로](index.md)
