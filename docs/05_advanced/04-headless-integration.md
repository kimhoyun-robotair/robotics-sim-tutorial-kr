# Headless 통합 테스트

> **목표:** 설치된 package 경로에서 server-only stack을 실행하고 성공·계약 오류·runtime fault·timeout·cleanup을 분리합니다.
> **선행 학습:** [물리와 주기 디버깅](03-physics-debugging.md)

## 성공 문구보다 강한 증거

nominal 검사는 Gazebo server, Transport subscriber, ROS–Gazebo bridge를 실제로 시작합니다. 속도 명령 뒤 plugin distance와 ROS pose 변위를 각각 확인하고 reset 뒤 거리가 0으로 돌아오는지 파싱합니다. server log의 `PASS` 문자열만으로는 합격하지 않습니다.

<figure class="course-figure" id="advanced-headless-exit-taxonomy" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/headless-exit-taxonomy.svg" alt="headless checker의 nominal usage missing model missing plugin timeout cleanup 종료 코드를 구분한 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 종료 코드는 원인을 분류하고, scenario·표본·cleanup 파일이 실제 관측을 증명합니다.</figcaption>
</figure>

## nominal 실행

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario nominal --evidence "$run_dir"
python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2])); assert s["status"] == "PASS" and s["plugin_distance"] >= 0.1 and c["status"] == "clean"; print("headless=PASS cleanup=clean")' "$run_dir/scenario.json" "$run_dir/cleanup.json"
```

## 종료 taxonomy

| 종료 | 의미 | 필수 관측 |
|---:|---|---|
| 0 | nominal 성공 | 실제 distance·pose·reset 표본 |
| 64 | 사용법 또는 설치 계약 오류 | 잘못된 인자나 누락된 설치 경로 |
| 20 | 모델 미발견 | <span style="white-space: nowrap;">`WAITING_FOR_MODEL`</span> |
| 21 | plugin 누락 | 실제 load 실패 로그 |
| 124 | 내부 deadline | deadline source와 seconds |
| 130 | SIGINT | signal 종료와 zero survivor |
| 70 | cleanup 실패 | survivor 또는 PID identity 불일치 |

checker는 자신이 만든 process group의 PID와 시작 tick을 기록합니다. 종료 시 INT, bounded wait, TERM 순으로 정리하며 다른 Gazebo·ROS 프로세스에는 손대지 않습니다.

## 문제 해결

timeout이면 먼저 readiness 조건이 어떤 파일에 기록되지 않았는지 확인합니다. cleanup exit 70이면 PID 재사용 여부와 process group 등록 시점을 확인합니다. plugin-missing fault가 0이면 server banner가 아니라 실제 load 오류를 검사하는지 확인합니다.

## 출처

- [Gazebo Sim headless server usage](https://gazebosim.org/docs/harmonic/server_config/)
- [Python subprocess process management](https://docs.python.org/3/library/subprocess.html)

[이전: 물리와 주기 디버깅](03-physics-debugging.md) · [다음: CI 재현성](05-ci-reproducibility.md)
