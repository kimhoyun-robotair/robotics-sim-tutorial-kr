# 물리와 주기 디버깅

> **목표:** physics step, publish period, simulation time을 분리하고 동일 simulation 구간의 표본 수를 비교합니다.
> **선행 학습:** [Transport 인터페이스](02-transport-interfaces.md)

## 결정적인 시간축

host FPS와 real-time factor는 CPU 부하에 따라 달라집니다. 검증 기준은 `/world/<name>/stats`의 `simTime`입니다. physics step을 \(h\), publish period를 \(T_p\), simulation 구간을 \(T\)라 두면 update 수는 대략 \(T/h\), 발행 수는 대략 \(T/T_p\)입니다. 두 수를 섞으면 느린 host에서만 실패하는 테스트가 됩니다.

<figure class="course-figure" id="advanced-sim-time-debug" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/sim-time-debug.svg" alt="같은 2초 simulation에서 0점05초와 0점2초 publish 주기의 메시지 수를 비교하는 막대 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 같은 simulation time에서 publish period가 네 배이면 실제 메시지 수도 약 네 배 차이 납니다.</figcaption>
</figure>

## 비교 실험

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario physics --sim-seconds 2.0 --worlds advanced-fast.sdf,advanced-slow.sdf --evidence "$run_dir"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert 3 <= d["ratio"] <= 5; print("time=%.1f ratio=%.2f" % (d["sim_seconds"], d["ratio"]))' "$run_dir/scenario.json"
```

두 world는 설치된 share 경로에서 읽습니다. checker는 `simTime`이 단조 증가하고 2.0초에 도달했는지, 실제 distance 메시지 수의 비율이 3–5인지 함께 검사합니다.

## 디버깅 순서

1. stats의 마지막 `simTime`을 확인합니다.
2. world의 physics step과 실제 update 수를 비교합니다.
3. plugin의 publish period가 유한한 양수인지 확인합니다.
4. topic 로그의 실제 표본 수와 timestamp 단조성을 확인합니다.

## 문제 해결

표본 수가 모두 0이면 plugin 경로와 topic 이름부터 확인합니다. 비율은 맞지만 종료 시간이 다르면 iteration 수와 physics step의 곱을 확인합니다. `nan`, 0, 음수 주기는 의도된 exit 64와 `INVALID_CONFIG`여야 하며 자동 보정해서는 안 됩니다.

## 출처

- [Gazebo Sim server configuration](https://gazebosim.org/api/sim/8/server_config.html)
- [SDFormat physics specification](https://sdformat.org/spec?ver=1.10&elem=physics)

[이전: Transport 인터페이스](02-transport-interfaces.md) · [다음: Headless 통합 테스트](04-headless-integration.md)
