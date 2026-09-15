# 101. t084 · Franka 네 블록 쌓기 해부

권장 학습 순서 **101** · 환경 구축과 로봇 행동 · 출처 ID `t084`

로컬 `block_stacking_behavior.py`에는 공식 5.1의 전체 reactive block-stacking behavior가 있다. `run.py`는 Franka와 폭 0.0515m인 Red/Blue/Yellow/Green 네 블록, 지면을 생성하고 해당 behavior를 연결한다. 다른 튜토리얼에서 로봇 설정을 복사할 필요가 없다.

## 이 실습의 의도

블록 위치와 gripper의 점유 상태를 계속 관찰해 집기·놓기·home을 선택하는 반응형 탑 쌓기를 해부한다. 네 블록은 색 이름으로 쌓기 순서를 정하고 물리적으로 집어 옮기도록 구성했으며, 목표 탑이 흐트러지면 현재 배치를 다시 판단하는 과정을 확인한다. 기본 실행은 탑 쌓기를 자동 시작하고 완료 뒤 home 행동을 선택하지만 앱은 창을 닫거나 지정한 step 한도에 도달할 때까지 유지한다.

## 실행 후 확인할 것

- **초기 장면:** `/World/Franka` 앞 `/World/Obs/`의 Red/Blue/Yellow/GreenCube가 x=0.3~0.7, y=-0.4에 나란히 있는지 본다. 화면에 네 블록이 존재하는 것에서 더 나아가 실제 gripper가 하나씩 집고 놓는지 확인한다.
- **목표 탑:** `(x,y)=(0.25,0.3)` 부근에 아래부터 **Blue → Yellow → Green → Red** 순서의 네 층이 물리적으로 지지되는지 확인한다. 색 순서가 다른 네 블록 탑은 `is_complete` 조건을 충족하지 않는다.
- **회복 반응:** 아직 집지 않은 블록을 도달 가능한 빈 위치로 옮겨 추종을 확인하고, 완성한 탑의 위 블록을 옮겨 다시 쌓는지 본다. 블록이 base에서 너무 가깝거나 멀 때 출력되는 `block too close to robot base`/`block too far away`와 home 선택은 명시된 작업영역 제한이다.
- **진단과 실제 물리:** `<placing block>` 로그는 손끝이 놓기 목표에 가까워졌다는 표시다. 놓은 후 블록이 남아 지지되는지 화면으로 확인한다. `in tower` 등의 상세 문자열은 `diagnostics_message`에 저장되며 이 로컬 실행기에 자동 표시하는 UI는 없다.
- **선점과 접촉의 경계:** 잡기·놓기의 lock 구간에서는 외부 변화에 즉시 행동이 바뀌지 않을 수 있다. 선택한 블록의 RMPflow avoidance를 억제하는 것은 접촉을 허용하기 위한 동작 생성 설정이며 물리 collider 삭제가 아니다. 짧은 step 종료를 네 층 완성으로 해석하지 않는다.

## 탑 쌓기 관찰과 코드 읽기

1. `run.py --interactive`으로 시작하고 Play를 누른다. 블록을 모아 지정된 순서의 tower를 만드는지 관찰한다. 최초 배치는 x=0.3~0.7, y=-0.4이다. 목표 tower의 위치는 behavior 끝의 `make_decider_network()`에서 확인한다.
2. robot가 아직 집지 않은 블록을 Move 도구로 조금 옮긴다. 현재 world의 위치를 다시 읽어 추적하는지 확인한다. 이후 이미 쌓은 위 블록 하나를 tower 옆으로 옮겨 재정렬 반응을 확인한다.
3. `BlockPickAndPlaceDispatch`를 읽는다. tower가 완성되면 home, gripper가 비었으면 pick, 블록이 있으면 place를 선택한다. 어떤 블록을 집을지와 어디에 놓을지는 다음 계층에서 결정하고 atomic action에 parameters로 전달한다.
4. `make_pick_rlds()`의 등록 순서를 확인한다. RLDS는 마지막에 등록한 높은 우선순위부터 runnable 조건을 검사한다. gripper가 닫혀 있으면 open, 블록이 손가락 사이에 있으면 pick, 아니면 reach로 이어지는 논리를 역순 탐색으로 읽는다.
5. Pick/Place의 `DfStateSequence`에서 lock, gripper 동작, lift, logical-state 쓰기, unlock 순서를 찾는다. 일시적인 상태 변화로 상위 dispatch가 잡기 도중 선점하지 않도록 꼭 필요한 구간을 atomic하게 만든다.
6. `BuildTowerContext`의 perception, block tower, gripper occupancy, suppression, diagnostics monitor를 읽는다. pick 동작이 '잡았다'는 belief를 먼저 쓸 수 있지만 후속 monitor가 실제 위치와 비교하여 유지/교정한다.

Cortex의 `CortexObject`는 USD 객체와 관측/belief 정보를 다루고, `MotionCommand`는 손끝 pose와 posture를 commander에 보낸다. RMPflow 장애물 억제는 집을 블록과 접촉하도록 선택적으로 avoidance를 끄는 정책이다. 물리 collision 자체와 planner의 obstacle suppression을 혼동하지 않는다. 모든 행동은 기본적으로 선점 가능하며 lock은 명시적인 예외이다.

한 변수 실험: `make_decider_network()`의 tower x좌표만 0.25에서 0.30으로 바꾸고 새 실행에서 tower 위치를 비교한다. 작업영역 밖으로 크게 옮기면 도달하지 못할 수 있다. 성공은 단순 step 종료가 아니라 올바른 순서의 tower 및 이동시킨 블록에 대한 회복이다. 블록을 gripper 안으로 순간 이동시키면 물리적으로 불가능한 겹침이 생길 수 있으므로 초기에는 빈 위치로 이동한다.

## 독립 실행 환경

이 디렉터리를 단독으로 복사하여 사용할 수 있다. Isaac Sim **5.1.0** 설치, 지원 RTX GPU/드라이버 및 해당 로봇 자산 접근이 필요하다. `isaacsim.cortex.framework`는 설치된 SDK이며 다른 로컬 튜토리얼 패키지를 import하지 않는다. Python/Kit 초기화와 scene 구성은 각 실행기에 들어 있다. USD Stage는 장면 전체, prim은 `/World/Franka` 같은 경로로 찾는 장면 객체이고, transform은 위치·회전·스케일이다.

```bash
cd /path/to/101_digital_twin_cortex_4_franka_block_stacking
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py
```

기본은 창을 띄우고 자동 Play하며 사용자가 창을 닫을 때까지 계속 실행한다. 사람이 물체를 이동하는 실습은 `--interactive`를 추가하고 창에서 Play를 누른다. `--steps 1800`처럼 양수를 명시하면 interactive 여부와 관계없이 해당 physics step에 도달했을 때 종료한다. 화면 없는 실행은 `--headless`이며 `--steps` 생략 시 1800 step으로 종료한다. `--headless`와 `--interactive`는 동시에 사용할 수 없다. 새 데이터를 저장하는 튜토리얼이 아니며 성공은 위에 명시한 동작 관찰로 판단한다.

## 버전·검증·출처

- [Isaac Sim 5.1 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_4_franka_block_stacking.html)의 모든 주요 하위 실습을 위 단계에 연결했다. 실행 코드는 설치본 5.1의 API와 대조했다.
- NVIDIA 예제를 포함한 파일은 원래 Apache-2.0 copyright header와 `LICENSE-NVIDIA-EXAMPLES`를 보존한다. 변경 내역은 `NOTICE.md`에 있다. 설치본 원본은 `standalone_examples/api/isaacsim.cortex.framework/` 및 `exts/isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/`다.
- 작성 시 compile과 CLI help를 확인했다. GPU의 실제 로봇 동작과 GUI 상호작용은 실행하지 않았으며 `tutorial.json`은 `not_run`이다. 일반 Python에서 `omni`/`isaacsim` import가 없는 것은 `python.sh` 런타임을 쓰지 않았기 때문일 수 있다.
