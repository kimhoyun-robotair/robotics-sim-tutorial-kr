# 100. t083 · Peck games로 배우는 반응형 행동

권장 학습 순서 **100** · 환경 구축과 로봇 행동 · 출처 ID `t083`

같은 Franka와 네 블록 환경에서 세 가지 behavior를 비교한다. `peck_state_machine.py`, `peck_decider_network.py`, `peck_game.py`를 모두 로컬에 포함했다. 원본이 보여 주는 상태 기계의 반응성 한계를 관측한 뒤 이를 개선하는 decider 구조를 읽는 실습이다.

## 이 실습의 의도

한 번 정한 손끝 목표를 끝까지 시도하는 행동과 환경 변화를 감시해 목표를 다시 고르는 행동의 차이를 비교한다. 네 색 블록은 사용자가 옮길 수 있는 물리 물체이자 RMPflow 장애물이며, 바닥 peck 목표를 가려 상위 판단의 필요성을 드러낸다. 기본 실행은 `peck_state_machine` 하나를 선택하므로 반응성 비교와 최근 이동 블록 추종은 behavior를 바꿔 각각 실행한다.

## 실행 후 확인할 것

- **기본 peck 반복:** 물체를 옮기지 않은 장면에서는 손끝이 블록에서 떨어진 바닥 목표(z=0.01)를 향하고 약간 올라온 뒤 다른 목표를 고르는지 본다. 목표 x=0.3~0.7, y=-0.4~0.4는 난수로 정하므로 매 실행 같은 위치를 기대하지 않는다.
- **의도된 정체 상황:** `peck_state_machine`이 접근하는 목표를 `/World/Obs/RedCube` 등으로 가리면 손끝이 장애물을 피하면서 기존 목표 도달을 계속 시도할 수 있다. 진입 때만 목표를 고르는 이 behavior의 반응성 한계를 관찰하는 조건이다.
- **재선택 비교:** `peck_decider_network`로 바꿔 같은 가림을 만들면 현재 목표와 등록 장애물의 거리가 0.2 미만일 때 monitor가 `is_done`을 바꾸고 새로운 목표를 선택하는지 본다. 목표에 도달했을 때의 완료와 목표가 막혔을 때의 선점을 구분한다.
- **블록 peck game:** `peck_game`에서는 한 블록을 1cm 넘게 옮겨 활성 목표를 만들고, 이어 다른 블록을 옮겨 추종 대상이 바뀌는지 확인한다. 블록 중심보다 z가 0.0325 높은 목표에 손끝이 1cm 미만으로 접근하면 활성 상태를 해제한다. 여러 블록을 동시에 이동시키지 않고 순차적으로 시험한다.
- **대기와 lift 해석:** `peck_game`에서 이동한 블록이 없으면 home으로 가고, 손끝이 비활성 블록의 0.07 이내에 있으면 먼저 lift한다. 정지한 장면에서 계속 바닥을 peck하지 않아도 정상이며, `diagnostics_message`는 로컬 context에 저장되지만 이 실행기가 매번 콘솔에 출력하지는 않는다.

## 동일한 장면에서 세 behavior 비교

```bash
"$HOME/isaacsim/python.sh" run.py --behavior peck_state_machine --interactive
"$HOME/isaacsim/python.sh" run.py --behavior peck_decider_network --interactive
"$HOME/isaacsim/python.sh" run.py --behavior peck_game --interactive
```

1. 첫 실행에서 Play를 누른다. 로봇이 블록을 피해 바닥을 peck하는 동안 `/World/Obs/RedCube`를 선택한다. Move 도구로 현재 손끝 목표 바로 앞을 막도록 옮긴다. 원본 state machine은 진입 때 선택한 목표를 유지하므로 도달을 계속 시도하며 막힐 수 있다. 이 비교 조건을 코드 오류로 숨기지 않는다.
2. 창을 닫고 두 번째 behavior로 같은 실험을 반복한다. logical monitor가 현재 target과 블록의 근접 상태를 갱신하면 상위 decider가 peck sequence를 선점하고 다른 목표를 선택하는지 확인한다.
3. `DfStateSequence`의 각 phase와 상위 `decide()`가 어떤 조건에서 다시 목표 선택 branch로 가는지 찾아본다. 같은 motion primitive를 감싸더라도 분기 판단 위치가 반응성을 바꾼다.
4. 세 번째 `peck_game`에서는 블록 하나를 움직여 활성 target을 만들고 다른 블록을 다시 움직인다. 마지막으로 움직인 블록으로 target이 바뀌는지 관찰한다. 손끝이 비활성 블록 가까이에 있으면 먼저 lift하여 옆으로 쓸고 가지 않도록 한다.
5. 논리 상태를 담당하는 context의 `monitor_block_movement`, `monitor_active_target_p`, `monitor_active_block`, `monitor_eff_block_proximity`, diagnostics를 읽는다. raw 위치 비교를 매 decider에 중복하지 않고 monitor가 의미 있는 상태를 만든다.

`MotionCommand`, `PosePq`, `ApproachParams`는 목표 pose와 접근 방향을 arm commander에 전달한다. RMPflow의 장애물 회피는 선택한 목표가 도달 가능하도록 목표를 바꾸는 상위 논리와 다른 역할이다. `DynamicCuboid`는 물리 rigid body이고 `register_obstacle()`는 해당 객체를 robot의 동작 생성 장애물로 등록한다. USD prim의 가시성과 장애물 등록은 같은 설정이 아니다.

한 변수 실험은 **behavior 선택만** 바꾸고 동일한 블록으로 동일한 target 가림을 재현하는 것이다. 성공 기준은 두 번째 network의 목표 재선택과 세 번째 game의 최근 이동 블록 추적이다. 랜덤 위치가 매번 같다고 가정하지 않는다. 다른 개체를 선택했는지 확인하고, 관찰 중 자동 종료가 필요 없다면 `--steps`를 생략한다.

## 독립 실행 환경

이 디렉터리를 단독으로 복사하여 사용할 수 있다. Isaac Sim **5.1.0** 설치, 지원 RTX GPU/드라이버 및 해당 로봇 자산 접근이 필요하다. `isaacsim.cortex.framework`는 설치된 SDK이며 다른 로컬 튜토리얼 패키지를 import하지 않는다. Python/Kit 초기화와 scene 구성은 각 실행기에 들어 있다. USD Stage는 장면 전체, prim은 `/World/Franka` 같은 경로로 찾는 장면 객체이고, transform은 위치·회전·스케일이다.

```bash
cd /path/to/100_digital_twin_cortex_3_example_peck_games
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py
```

기본은 창을 띄우고 자동 Play하며 사용자가 창을 닫을 때까지 계속 실행한다. 사람이 물체를 이동하는 실습은 `--interactive`를 추가하고 창에서 Play를 누른다. `--steps 1800`처럼 양수를 명시하면 interactive 여부와 관계없이 해당 physics step에 도달했을 때 종료한다. 화면 없는 실행은 `--headless`이며 `--steps` 생략 시 1800 step으로 종료한다. `--headless`와 `--interactive`는 동시에 사용할 수 없다. 새 데이터를 저장하는 튜토리얼이 아니며 성공은 위에 명시한 동작 관찰로 판단한다.

## 버전·검증·출처

- [Isaac Sim 5.1 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_3_example_peck_games.html)의 모든 주요 하위 실습을 위 단계에 연결했다. 실행 코드는 설치본 5.1의 API와 대조했다.
- NVIDIA 예제를 포함한 파일은 원래 Apache-2.0 copyright header와 `LICENSE-NVIDIA-EXAMPLES`를 보존한다. 변경 내역은 `NOTICE.md`에 있다. 설치본 원본은 `standalone_examples/api/isaacsim.cortex.framework/` 및 `exts/isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/`다.
- 작성 시 compile과 CLI help를 확인했다. GPU의 실제 로봇 동작과 GUI 상호작용은 실행하지 않았으며 `tutorial.json`은 `not_run`이다. 일반 Python에서 `omni`/`isaacsim` import가 없는 것은 `python.sh` 런타임을 쓰지 않았기 때문일 수 있다.
