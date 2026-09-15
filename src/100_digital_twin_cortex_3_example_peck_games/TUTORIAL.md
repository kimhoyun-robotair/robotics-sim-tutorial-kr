# 100. 목표가 막히면 로봇은 언제 생각을 바꿀까요?

## 이번에 배우는 것

**같은 Franka 장면에서 세 가지 peck 행동을 비교하고, 장애물 회피와 목표 재선택이 서로 다른 역할임을 확인합니다.**

Peck은 손끝을 아래쪽 목표에 가져갔다가 들어 올리는 동작입니다. 로봇이 이미 목표를 향해 움직일 때 그 자리에 블록이 들어오면 어떤 반응이 필요할까요? 물체와 부딪치지 않는 것만으로는 작업을 계속할 수 없을 때가 있습니다.

| `--behavior` 값 | 목표를 고르는 방식 | 환경 변화에 대한 반응 |
|---|---|---|
| `peck_state_machine` | 상태 진입 때 빈 바닥 지점 선택 | 접근 중 막혀도 기존 목표 유지 |
| `peck_decider_network` | 빈 지점 선택 후 계속 감시 | 목표가 막히면 다른 지점 선택 |
| `peck_game` | 움직임이 감지된 블록 선택 | 새로 움직인 블록을 목표로 갱신 |

네 색 블록은 모두 실제 물리 물체이며, 로봇의 동작 생성기에도 장애물로 등록되어 있습니다.

## 1. 목표를 유지하는 peck 실행하기

Isaac Sim 5.1, 지원 NVIDIA RTX GPU와 Franka 자산이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/100_digital_twin_cortex_3_example_peck_games/run.py --behavior peck_state_machine --interactive
```

1. 창이 열리면 Play를 누릅니다.
2. 블록을 건드리지 않고 손끝이 바닥 쪽으로 내려갔다가 올라오는 모습을 관찰합니다.
3. Stage에서 `/World/Obs/RedCube`를 선택해 현재 손끝 목표 가까이 옮겨 봅니다. 목표는 `/World/motion_commander_target`으로 확인할 수 있습니다.
4. 블록이 목표를 가렸을 때 기존 목표 도달을 계속 시도하는지 봅니다. 손끝이나 다른 블록과 겹치게 순간 이동시키기보다 목표 주변의 빈 위치로 이동하세요.

창을 닫으면 종료합니다. 관찰 시간을 제한하려면 `--steps 1800`을 추가할 수 있지만, 사람이 블록을 움직이는 비교에서는 생략하는 편이 좋습니다. `--headless`는 기본 1800단계이며 `--interactive`와 함께 사용할 수 없습니다.

### 코드에서 볼 부분

`PeckState.enter()`는 X가 0.3~0.7 m, Y가 -0.4~0.4 m인 범위에서 목표를 뽑습니다. Z는 0.01 m입니다. 등록 장애물 중심과 0.2 m 미만으로 가까운 후보는 다시 뽑습니다.

```python
target_p = self.sample_target_p_away_from_obs()
self.target = PosePq(target_p, target_q)
approach_params = ApproachParams(
    direction=np.array([0.0, 0.0, -0.1]), std_dev=0.04
)
```

`PosePq`는 위치와 방향을 묶고, `ApproachParams`는 목표에 접근할 방향을 알려 줍니다. 여기서는 위에서 아래로 접근합니다. 목표를 뽑는 일은 진입 때만 하고, `step()`은 손끝과 기존 목표 거리가 0.01 m 미만인지 확인합니다.

### 실행 결과 확인하기

원래 빈 곳이던 목표가 블록으로 가려지면 동작 생성기는 충돌을 피하려고 합니다. 그러나 상태 기계는 아직 목표에 도달하지 못했으므로 같은 단계에 머물 수 있습니다. **이 정체가 이번 비교에서 관찰하려는 상황**입니다. 물리를 진행하는 루프가 멈춘 것과 구분하세요.

## 2. 목표를 다시 고르는 행동과 비교하기

앞 창을 닫고 behavior만 바꿔 실행합니다.

```bash
~/isaacsim/python.sh src/100_digital_twin_cortex_3_example_peck_games/run.py --behavior peck_decider_network --interactive
```

Play 후 앞과 같이 현재 목표 주변으로 블록을 옮깁니다. 목표가 매 실행 무작위이므로 같은 절대 좌표를 가리는 것이 아니라 **그 실행의 현재 목표**를 가리세요.

### 코드에서 볼 부분

이번 context는 실행 중에도 목표 근처의 장애물을 검사합니다.

```python
if self.active_target_p is not None and self.is_near_obs(self.active_target_p):
    self.is_done = True
```

상위 decider는 이 값을 보고 다음 행동을 고릅니다.

```python
if self.context.is_done:
    return DfDecision("choose_target")
else:
    return DfDecision("peck")
```

`is_done`은 정상 도달 후에도, 목표가 막혔을 때도 설정됩니다. 현재 peck을 더 진행할 이유가 없어지면 새 목표 선택으로 돌아가는 구조입니다. 안쪽에는 여전히 닫기 → peck → lift의 상태 기계가 있지만, 바깥 판단이 환경 변화에 반응합니다.

세 번째 행동은 빈 바닥을 찾는 대신 움직인 블록을 추종합니다. 앞 창을 닫고 실행하세요.

```bash
~/isaacsim/python.sh src/100_digital_twin_cortex_3_example_peck_games/run.py --behavior peck_game --interactive
```

Play 후 블록 하나를 1 cm 넘게 옮깁니다. 첫 peck을 마치고 손끝이 들어 올려지거나 home으로 돌아간 다음 다른 블록을 옮겨 보세요. 진행 도중 다른 블록으로 바꾸는 비교에는 아래에 설명한 회피 대상 갱신의 제한이 있습니다. 움직임 감지 기준은 저장된 이전 위치와의 거리입니다. 여러 블록을 한꺼번에 옮기면 순회 순서가 선택에 영향을 줄 수 있으므로 하나씩 비교하세요.

### 실행 결과 확인하기

| 조건 | `peck_game`의 판단 |
|---|---|
| 손끝이 비활성 블록 중심의 0.07 m 이내 | 먼저 lift |
| 활성 블록이 있음 | 그 블록 위를 peck |
| 활성 블록도 근접 위험도 없음 | home으로 이동 |

목표는 블록 중심보다 Z가 0.0325 m 높습니다. 손끝이 그 점의 1 cm 이내에 오면 활성 상태를 해제합니다. 이 판정은 접촉 센서의 충돌 검출이 아니라 위치 거리 판정입니다.

`PeckAction.enter()`는 그때 선택된 블록을 `self.block`에 저장하고 동작 생성용 회피를 끕니다. `exit()`은 저장한 그 블록의 회피를 복구합니다. 물리 Collider를 지우는 것이 아닙니다.

**peck 도중 다른 블록이 활성화되어도 같은 `peck` 가지가 유지되면 `enter()`가 다시 호출되지 않습니다.** 목표 좌표는 새 블록을 따라가지만 회피를 꺼 둔 대상은 이전 블록에 남을 수 있습니다. 따라서 목표 전환과 새 블록에 실제로 접근하는 성공을 따로 관찰하세요. 새 블록 앞에서 멈추는 경우에는 앱을 다시 실행하고, 한 블록의 peck과 lift를 끝낸 뒤 다음 블록을 움직여 각 동작을 확인합니다.

또한 `diagnostics_message`는 context에 저장되지만 이 실행기는 해당 문자열을 매번 콘솔에 표시하지 않습니다. 실제 목표 변화와 손끝 운동을 함께 관찰하세요.

## 3. 회피와 재계획의 차이 정리

```text
상태 기계: 선택한 목표 → 회피하며 접근 → 도달할 때까지 대기
반응형 선택: 목표 주변 감시 → 막힘 발견 → 다른 목표 → 다시 접근
블록 게임: 위치 변화 감시 → 활성 블록 갱신 → peck 또는 lift
```

회피는 “현재 목표로 가는 동안 어디로 움직일지”를 다룹니다. 목표 재선택은 “이 목표를 계속 수행할지”를 다룹니다. 두 층이 연결되어야 장애물이 바뀐 뒤에도 작업을 이어 갈 수 있습니다.

## 4. 간단한 확인 실험

**`--behavior`만** `peck_state_machine`과 `peck_decider_network` 사이에서 바꾸며 목표 가림을 반복하세요. 블록 개수와 크기, 접근 조건은 유지합니다.

첫 실행에서는 기존 목표가 유지되는지, 두 번째에서는 목표가 새 위치로 옮겨지는지 기록합니다. 난수 목표 때문에 궤적을 픽셀 단위로 맞추는 비교는 적절하지 않습니다. 비교할 대상은 **가려진 목표를 계속 유지하는지**입니다.

## 실행할 때 막히면

- **`peck_game`이 home에서 기다림**: 움직인 블록이 아직 없을 수 있습니다. 블록 하나를 1 cm 넘게 옮겨 보세요.
- **첫 behavior가 목표 앞에서 오래 머묾**: 블록을 원래 위치로 돌려 목표를 열어 보세요. 다시 진행한다면 가림에 따른 정체를 관찰한 것입니다.
- **두 번째 behavior의 목표가 계속 바뀜**: 장애물이 목표 주변을 반복해서 막고 있는지 확인하세요. 모든 후보 영역을 블록으로 채우면 목표 선택이 어려워집니다.
- **도중에 목표 블록을 바꾼 뒤 새 블록 앞에서 멈춤**: 같은 peck 가지에서는 회피 제외 대상이 자동 재설정되지 않는 코드 제한이 있습니다. 앱을 다시 실행한 뒤 한 peck이 끝나 lift/home으로 전환될 때까지 기다리고 다음 블록을 움직여 비교하세요.
- **로그로 활성 블록을 찾을 수 없음**: 자동 출력하지 않는 진단 문자열과 실제 콘솔 출력을 구분하세요. 화면의 목표와 블록 이동으로 확인합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Behavior Examples: Peck Games](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_3_example_peck_games.html)에 대응합니다. 세 behavior는 NVIDIA 예제이며, 로컬 `run.py`가 동일한 Franka·블록 장면에서 선택해 실행합니다. 출처와 라이선스는 `NOTICE.md`, `LICENSE-NVIDIA-EXAMPLES`에 있습니다.

목표 가림과 블록 이동에 대한 반응은 GUI에서 확인할 기준입니다. 특히 peck 중 목표 교체에는 본문의 회피 대상 갱신 제한이 있습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
