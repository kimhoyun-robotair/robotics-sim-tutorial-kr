# ECS System Plugin

> **목표:** `TutorialBotDiagnostics`가 ECS를 읽는 지점과 모델 생명주기를 설명하고 설치 계약을 검증합니다.
> **선행 학습:** [고급 과정 개요](index.md)

## ECS에서 읽고 System에서 계산하기

Entity는 숫자 식별자이고 component가 pose·name 같은 데이터를 보관합니다. System은 `ISystemConfigure`에서 설정을 파싱하고, `ISystemPostUpdate`에서 `EntityComponentManager`의 `Name`과 `WorldPose`를 읽습니다. 진단 플러그인은 DiffDrive 명령을 복제하지 않고, 관측된 위치 사이의 평면 거리만 누적합니다.

첫 유효 표본은 거리가 아니라 기준점입니다. 이후 두 위치가 \((x_{k-1},y_{k-1})\), \((x_k,y_k)\)라면 누적값은 다음과 같습니다.

\[
\begin{aligned}
\Delta d_k &= \sqrt{(x_k-x_{k-1})^2+(y_k-y_{k-1})^2},\\
d_k &= d_{k-1}+\Delta d_k.
\end{aligned}
\]

<figure class="course-figure" id="advanced-ecs-lifecycle" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/ecs-lifecycle.svg" alt="WAITING FOR MODEL READY DISABLED MODEL REMOVED와 재결합 기준점을 보여 주는 ECS 생명주기 상태도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 모델이 제거되면 거리를 동결하고, 재등장한 entity는 거리 0의 새 기준점으로 결합합니다.</figcaption>
</figure>

## 설치된 계약 검증

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
contract="$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/share/tutorial_bot_plugins/config/diagnostics-contract.yaml"
test -f "$contract"
python3 scripts/check_advanced_contract.py --contract "$contract" --evidence /tmp/tutorial-bot-contract.json
rm -f /tmp/tutorial-bot-contract.json
```

출력에는 plugin class·library·interface, 다섯 상태와 topic/service 타입이 나타납니다. checker가 YAML을 파싱하므로 설명 문구만 맞고 실제 계약이 다른 경우에는 exit 64입니다.

## 생명주기 판정

- 모델이 아직 없으면 `WAITING_FOR_MODEL`이며 server는 계속 실행됩니다.
- 첫 pose는 `READY`, distance 0의 기준점입니다.
- disable은 누적을 멈추되 reset 요청을 허용합니다.
- entity가 사라지면 `MODEL_REMOVED`, 재등장하면 fresh baseline입니다.
- 유한한 양수가 아닌 주기는 `INVALID_CONFIG`이고 distance publisher를 만들지 않습니다.

## 문제 해결

`WAITING_FOR_MODEL`이 계속되면 SDF의 `<model_name>`과 실제 entity 이름을 비교합니다. 제거 뒤 거리가 급증하면 이전 entity의 마지막 pose를 재사용한 것이므로 결합 시 기준점을 초기화합니다. 설정 오류인데 distance가 발행되면 publisher 생성 순서를 config 검증 뒤로 옮깁니다.

## 출처

- [Gazebo Sim System plugins](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Sim Entity Component Manager](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1EntityComponentManager.html)

[이전: 고급 과정 개요](index.md) · [다음: Transport 인터페이스](02-transport-interfaces.md)
