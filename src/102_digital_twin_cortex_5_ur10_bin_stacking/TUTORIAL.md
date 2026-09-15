# 102. t085 · UR10 suction gripper로 bin 뒤집어 쌓기

권장 학습 순서 **102** · 환경 구축과 로봇 행동 · 출처 ID `t085`

공식 UR10 bin-stacking main과 behavior를 이 폴더 안에 포함했다. `run.py`가 conveyor 작업대, warehouse, UR10 suction gripper를 준비하고 새 bin을 공급한다. `bin_stacking_behavior.py`가 집기·뒤집기·놓기의 결정을 수행한다.

필요한 5.1 자산은 `/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd`, `/Isaac/Props/KLT_Bin/small_KLT.usd`, `/Isaac/Environments/Simple_Warehouse/warehouse.usd`다. asset root 접근이 끊기면 로봇/그리퍼 없는 화면에서 동작 검증을 계속하지 않는다.

1. `run.py --interactive`을 실행하고 Play를 누른다. bin이 conveyor 끝으로 오면 UR10이 집고, 필요한 bin은 flip station에서 뒤집어 pallet에 놓는지 본다.
2. 콘솔의 `active bin`, `is_grasp_reached`, `is_attached`, `needs_flip` 값을 순서대로 기록한다. 현재 집고 있는 bin과 아직 conveyor에 있는 bin을 구분한다.
3. `Dispatch.decide()`를 읽는다. stack complete 또는 active bin 없음은 home, 미부착은 pick, 뒤집기 필요는 flip, 그 외는 place이다. `BinStackingContext`가 이 논리값을 감시한다.
4. `PickBin`, `FlipBin`, `PlaceBin`의 sequence를 읽으며 lock/unlock 사이 suction open/close와 lift 순서를 찾는다. pose 목표에 가까운 것만으로 suction attachment 성공을 뜻하지 않는다.
5. Stage의 `/World/Ur10Table/Obstacles`에서 `FlipStationSphere`, `NavigationDome`, `NavigationBarrier`, `NavigationFlipStation`의 visibility를 켜서 보이지 않던 동작 생성 장애물 영역을 확인한다. 관찰 후 다시 숨긴다.
6. `ObstacleMonitor.is_obstacle_required()`와 activate/deactivate autotoggle이 접근/이동 phase에 따라 장애물을 켜고 끄는 과정을 읽는다. flip station에 닿아야 하는 순간까지 장애물로 피하면 작업을 수행할 수 없다.
7. `ReachToPlace.step()`의 bin xy 오차 보정과 아래쪽 `ApproachParams`를 읽는다. 작은 정렬 오차를 목표에 조금씩 반영하고 충돌 피드백 때문에 밀려나면 재접근한다. 원문의 성공률 설명을 이 실행에서 측정한 성공률로 표시하지 않는다.

USD scene은 conveyor와 pallet의 시각/물리 구성을 제공한다. `CortexRigidPrim`은 bin rigid body를 감싸고 `CortexUr10`은 arm/suction commander를 제공한다. 본 로컬 task는 실제 bin reference를 spawn하여 pose와 초기 속도를 준다. `needs_flip`은 바닥 방향을 나타내는 논리 상태이며 단순한 물체 색 분류가 아니다.

한 변수 실험: `random_bin_spawn_transform()`의 x 범위만 ±0.15에서 ±0.05로 좁혀 초기 grasp 위치 분산을 비교한다. 초기 velocity 또는 flip 확률은 그대로 둔다. 성공 기준은 여러 bin의 물리적 pallet 적재이며 루프 생존이나 console 값만으로 성공을 확정하지 않는다. suction 실패 시 bin mesh/충돌, grasp 위치와 stage 로딩 상태를 확인한다.

## 독립 실행 환경

이 디렉터리를 단독으로 복사하여 사용할 수 있다. Isaac Sim **5.1.0** 설치, 지원 RTX GPU/드라이버 및 해당 로봇 자산 접근이 필요하다. `isaacsim.cortex.framework`는 설치된 SDK이며 다른 로컬 튜토리얼 패키지를 import하지 않는다. Python/Kit 초기화와 scene 구성은 각 실행기에 들어 있다. USD Stage는 장면 전체, prim은 `/World/Franka` 같은 경로로 찾는 장면 객체이고, transform은 위치·회전·스케일이다.

```bash
cd /path/to/102_digital_twin_cortex_5_ur10_bin_stacking
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py
```

기본은 창을 띄우고 자동 Play하며 사용자가 창을 닫을 때까지 계속 실행한다. 사람이 물체를 이동하는 실습은 `--interactive`를 추가하고 창에서 Play를 누른다. `--steps 1800`처럼 양수를 명시하면 interactive 여부와 관계없이 해당 physics step에 도달했을 때 종료한다. 화면 없는 실행은 `--headless`이며 `--steps` 생략 시 1800 step으로 종료한다. `--headless`와 `--interactive`는 동시에 사용할 수 없다. 새 데이터를 저장하는 튜토리얼이 아니며 성공은 위에 명시한 동작 관찰로 판단한다.

## 버전·검증·출처

- [Isaac Sim 5.1 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking.html)의 모든 주요 하위 실습을 위 단계에 연결했다. 실행 코드는 설치본 5.1의 API와 대조했다.
- NVIDIA 예제를 포함한 파일은 원래 Apache-2.0 copyright header와 `LICENSE-NVIDIA-EXAMPLES`를 보존한다. 변경 내역은 `NOTICE.md`에 있다. 설치본 원본은 `standalone_examples/api/isaacsim.cortex.framework/` 및 `exts/isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/`다.
- 작성 시 compile과 CLI help를 확인했다. GPU의 실제 로봇 동작과 GUI 상호작용은 실행하지 않았으며 `tutorial.json`은 `not_run`이다. 일반 Python에서 `omni`/`isaacsim` import가 없는 것은 `python.sh` 런타임을 쓰지 않았기 때문일 수 있다.
