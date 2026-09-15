# 99. t082 · Decider network와 상태 모니터

권장 학습 순서 **99** · 환경 구축과 로봇 행동 · 출처 ID `t082`

한 폴더에 세 가지 실제 동작을 담았다. `follow.py`는 목표 구를 따라가며 도달 여부로 손가락을 여닫고, `run.py`는 로컬 `simple_state_machine.py` 또는 `simple_decider_network.py`를 로드한다. 로봇·지면·물체 생성도 이 폴더 실행기에 포함되어 있다.

```bash
"$HOME/isaacsim/python.sh" follow.py --interactive
"$HOME/isaacsim/python.sh" run.py --behavior simple_state_machine
"$HOME/isaacsim/python.sh" run.py --behavior simple_decider_network --interactive
```

1. follow 창에서 Play를 누르고 Stage의 `/World/FollowSphere`를 선택한다. Move 도구로 x/y를 조금 이동한다. 구를 멀리 옮기면 gripper가 열리고 손끝이 쫓아가며, 약 1cm 이내에 도달하면 닫힌다.
2. `FollowContext.add_monitors()`의 순서를 읽는다. `monitor_end_effector`가 `is_target_reached`를 먼저 갱신하고 `monitor_gripper`가 그 값을 사용한다. monitor 순서를 바꾸면 한 cycle 전의 판단을 사용할 수 있다.
3. `FollowState.step()`이 `self`를 반환하는 이유를 확인한다. 계속 같은 상태를 수행한다는 뜻이다. `None`은 state sequence에서 해당 상태 완료를 의미한다.
4. simple state machine을 실행하면 손끝이 두 목표 사이를 오간다. `enter/step/exit`와 상태 전이 반환값을 로컬 코드에서 찾아 화면의 전환 시점에 대응시킨다.
5. simple decider network를 실행하고 Stage에서 arm target을 선택해 Move 도구로 좌우로 옮긴다. `<left>`, `<middle>`, `<right>` 콘솔 출력 변화와 진입/이탈 횟수를 확인한다. 입력 region에 따라 같은 leaf가 계속 선택되는 경우와 다른 branch로 바뀌는 경우가 다르다.

`DfNetwork`는 `DfDecider`들의 방향성 비순환 그래프를 root에서 leaf까지 매 cycle 따라간다. `DfDecision`은 선택할 child 이름과 필요시 parameters를 전달한다. 같은 경로면 `decide()`가 반복되고, 경로가 바뀌면 이전 가지에 leaf부터 `exit()`, 새로운 가지에는 root 쪽부터 `enter()`가 호출된다. `DfRobotApiContext`는 로봇 command API와 논리 상태를 공유한다. `DfStateMachineDecider`는 상태 기계를 반응형 network 안의 한 node로 감싼다.

한 변수 실험: `follow.py`의 거리 임계값 0.01만 0.03으로 바꿔 gripper 닫힘 시점이 빨라지는지 확인한다. 목표 z는 바닥 관통을 줄이기 위해 0.02 이상으로 제한한다. 관절 위치를 드래그하는 것과 목표 구를 드래그하는 것을 구분한다. 목표가 도달 불가능하면 false 로그가 계속되는 것이 예상되는 동작이다.

## 독립 실행 환경

이 디렉터리를 단독으로 복사하여 사용할 수 있다. Isaac Sim **5.1.0** 설치, 지원 RTX GPU/드라이버 및 해당 로봇 자산 접근이 필요하다. `isaacsim.cortex.framework`는 설치된 SDK이며 다른 로컬 튜토리얼 패키지를 import하지 않는다. Python/Kit 초기화와 scene 구성은 각 실행기에 들어 있다. USD Stage는 장면 전체, prim은 `/World/Franka` 같은 경로로 찾는 장면 객체이고, transform은 위치·회전·스케일이다.

```bash
cd /path/to/99_digital_twin_cortex_2_decider_networks
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py
```

기본은 창을 띄우고 자동 Play하며 사용자가 창을 닫을 때까지 계속 실행한다. 사람이 물체를 이동하는 실습은 `--interactive`를 추가하고 창에서 Play를 누른다. `--steps 1800`처럼 양수를 명시하면 interactive 여부와 관계없이 해당 physics step에 도달했을 때 종료한다. 화면 없는 실행은 `--headless`이며 `--steps` 생략 시 1800 step으로 종료한다. `--headless`와 `--interactive`는 동시에 사용할 수 없다. 새 데이터를 저장하는 튜토리얼이 아니며 성공은 위에 명시한 동작 관찰로 판단한다.

## 버전·검증·출처

- [Isaac Sim 5.1 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_2_decider_networks.html)의 모든 주요 하위 실습을 위 단계에 연결했다. 실행 코드는 설치본 5.1의 API와 대조했다.
- NVIDIA 예제를 포함한 파일은 원래 Apache-2.0 copyright header와 `LICENSE-NVIDIA-EXAMPLES`를 보존한다. 변경 내역은 `NOTICE.md`에 있다. 설치본 원본은 `standalone_examples/api/isaacsim.cortex.framework/` 및 `exts/isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/`다.
- 작성 시 compile과 CLI help를 확인했다. GPU의 실제 로봇 동작과 GUI 상호작용은 실행하지 않았으며 `tutorial.json`은 `not_run`이다. 일반 Python에서 `omni`/`isaacsim` import가 없는 것은 `python.sh` 런타임을 쓰지 않았기 때문일 수 있다.
