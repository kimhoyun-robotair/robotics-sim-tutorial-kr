# 99. 상태를 기다릴 때와 조건을 다시 판단할 때

## 이번에 배우는 것

**Franka의 왕복 이동, 목표 구 추종, 위치별 분기를 비교하며 상태 기계·모니터·decider의 역할을 구분합니다.**

“목표에 도달하면 다음으로 이동”과 “현재 상황에 맞는 행동을 선택”은 서로 다른 제어 흐름입니다. Cortex에서는 순서를 다루는 상태 기계와 조건을 판단하는 decider를 함께 사용할 수 있습니다. 판단에 필요한 값은 모니터가 먼저 갱신합니다.

| 실행 | 실제 파일 | 확인할 질문 |
|---|---|---|
| 두 목표 왕복 | `run.py` + `simple_state_machine.py` | 언제 다음 상태로 넘어가나요? |
| 구 추종 | `follow.py` | 관찰값이 그리퍼 동작에 어떻게 쓰이나요? |
| 위치별 출력 | `run.py` + `simple_decider_network.py` | 매번 어떤 가지를 선택하나요? |

`run.py` 장면의 네 블록은 장애물입니다. 이번 행동은 블록 쌓기가 아닙니다.

## 1. 두 목표를 왕복하는 상태 기계 실행하기

Isaac Sim 5.1, 지원 NVIDIA RTX GPU와 Franka 자산을 준비합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/99_digital_twin_cortex_2_decider_networks/run.py --behavior simple_state_machine
```

자동 Play 후 손끝이 두 목표를 번갈아 향합니다. 창을 닫으면 종료하며, `--steps 1800`을 추가하면 지정 단계에서 끝납니다. `--headless`의 기본 한도는 1800단계입니다. GUI에서 Play 시점을 고르려면 `--interactive`를 쓰세요.

### 코드에서 볼 부분

`simple_state_machine.py`의 목표는 다음 두 점입니다. 좌표 단위는 m입니다.

```python
p1 = np.array([0.2, -0.2, 0.01])
p2 = np.array([0.6, 0.3, 0.6])
```

`ReachState.enter()`가 목표를 한 번 보내고, `step()`은 현재 손끝과의 거리를 확인합니다.

```python
if np.linalg.norm(self.target_p - self.context.robot.arm.get_fk_p()) < 0.01:
    return None
return self
```

`get_fk_p()`는 현재 관절 상태에서 계산한 손끝 위치입니다. 목표와의 거리가 1 cm 미만이면 상태를 끝내고 다음 목표로 넘어갑니다. 그렇지 않으면 같은 상태에 머뭅니다. 따라서 **고정된 초 간격으로 목표를 교대하는 코드가 아닙니다.**

### 실행 결과 확인하기

손끝이 낮은 첫 목표와 높은 두 번째 목표 사이를 이동하는지 확인하세요. 한 목표 근처에서 다음 방향으로 돌아서는 시점이 도달 판정과 연결됩니다. 목표가 막히거나 도달할 수 없으면 상태가 오래 유지될 수 있습니다.

종료 시 `Cortex loop ended at physics step ...`는 반복문이 끝난 이유를 알려 줄 뿐, 두 목표의 도달 횟수를 요약한 성공 보고서는 아닙니다.

## 2. 관찰값으로 그리퍼와 분기 제어하기

첫 창을 닫고 구 추종 예제를 실행합니다.

```bash
~/isaacsim/python.sh src/99_digital_twin_cortex_2_decider_networks/follow.py --interactive
```

1. Play를 누릅니다. 상태 진입 시 자홍색 `/World/FollowSphere`가 현재 손끝 위치로 옮겨집니다.
2. Stage에서 이 구를 선택하고 Move 도구로 X 또는 Y를 조금 이동합니다.
3. 손끝이 구를 따라가는 동안 그리퍼가 열리고, 가까워지면 닫히는지 봅니다. 처음에는 Z가 0.02 m 이상인 도달 가능한 위치에서 실험하세요.

### 코드에서 볼 부분

`FollowContext`의 모니터는 등록된 순서대로 실행됩니다.

```python
self.add_monitors([
    FollowContext.monitor_end_effector,
    FollowContext.monitor_gripper,
    FollowContext.monitor_diagnostics,
])
```

첫 모니터는 실제 손끝과 구의 거리를 읽어 `is_target_reached`를 갱신합니다. 두 번째는 그 결과로 그리퍼를 여닫고, 세 번째는 콘솔에 판단값을 출력합니다. 같은 위치 계산을 여러 행동에서 반복하지 않아도 되는 구조입니다.

추종 상태의 `step()`은 매번 새 구 위치를 읽고 `self`를 반환합니다. 구가 움직여도 상태를 끝낼 필요 없이 목표만 계속 갱신합니다. 다만 명령 Z는 최소 0.02 m로 제한하고 도달 판정은 원래 구 좌표를 사용합니다. 구를 그 아래에 놓으면 “명령한 점”과 “비교하는 점”이 달라질 수 있습니다.

이제 창을 닫고 조건 분기 예제를 실행하세요.

```bash
~/isaacsim/python.sh src/99_digital_twin_cortex_2_decider_networks/run.py --behavior simple_decider_network --interactive
```

Play 후 Stage에서 `/World/motion_commander_target`을 선택해 도달 가능한 범위에서 Y를 옮깁니다. 이 behavior는 위치 영역에 따라 문구를 출력하며, 자체적으로 왕복 목표를 생성하지 않습니다.

### 실행 결과 확인하기

| 실제 손끝 Y | 선택 결과 | 콘솔 문구 |
|---|---|---|
| `y <= -0.15` m | 왼쪽 가지 | `<left>` |
| `-0.15 < y < 0.15` m | 가운데 가지 | `<middle>` |
| `y >= 0.15` m | 오른쪽 가지 | `<right>` |

판단에 쓰이는 값은 목표 prim의 좌표가 아니라 `get_fk_p()[1]`입니다. 목표를 옮겨도 손끝이 아직 이동 중이라면 이전 영역으로 판단할 수 있습니다.

`Dispatch.decide()`는 가운데 여부를 먼저 검사합니다. 가운데라면 `DfDecision("print", "<middle>")`로 `print` 자식과 출력할 문자열을 함께 전달하고, 그 밖에서는 `print_left` 또는 `print_right`를 선택합니다. 음의 Y이면서 가운데 범위인 점도 `<middle>`로 판단하는 이유입니다.

네트워크는 매 cycle 루트에서 선택한 자식으로 내려갑니다. 같은 경로를 유지하면 판단만 반복하고, 가지가 바뀌면 이전 가지를 말단부터 `exit()`한 뒤 새 가지의 `enter()`를 호출합니다. `PrintAction`은 `enter()`에서 출력하므로 같은 가지에 머무는 동안 매 프레임 같은 로그가 생기지는 않습니다. 반면 구 추종의 진단 모니터는 계속 출력하므로 두 로그의 빈도가 다른 것은 자연스럽습니다.

## 3. 순서와 판단의 차이 정리

```text
왕복: 목표 A → 1 cm 이내 도달 → 목표 B → 도달 → 반복
추종: 구 위치 읽기 → 도달 여부 갱신 → 그리퍼 판단 → 새 목표 명령
분기: 실제 Y 읽기 → 가운데/왼쪽/오른쪽 선택 → 선택한 Action 실행
```

상태 기계는 현재 단계의 완료를 표현합니다. decider는 현재 논리 상태로 자식 행동을 선택합니다. `DfStateMachineDecider`를 사용하면 한 가지 안에서 순차 행동을 수행할 수도 있습니다.

## 4. 간단한 확인 실험

`follow.py`의 `monitor_end_effector()`에서 **거리 임계값만 `0.01`에서 `0.03`으로** 바꿔 보세요. 구의 높이 제한과 다른 명령은 그대로 둡니다.

같은 거리만큼 구를 옮겼을 때 이전보다 멀리 떨어진 상태에서 `is_target_reached=True`가 되고 그리퍼가 닫히는지 확인합니다. 손끝 명령의 목표 자체가 바뀌는 실험이 아니라 **도달했다고 판단하는 범위**를 넓히는 실험입니다. 확인 후 원래 값으로 돌려놓으세요.

## 실행할 때 막히면

- **구가 처음 위치에서 손끝으로 이동함**: `FollowState.enter()`의 초기 목표 설정입니다. Play 후에 구를 움직이세요.
- **구 추종에서 계속 False**: 구가 너무 낮거나 로봇 작업 영역 밖인지 확인하세요. 명령 높이 제한과 도달 판정 좌표가 다를 수 있습니다.
- **decider 실행에서 팔이 왕복하지 않음**: 출력 행동만 선택하는 모드입니다. 왕복은 `simple_state_machine`으로 실행합니다.
- **`--interactive` 실행이 정지 상태임**: Play를 누르세요. 이 옵션은 `--headless`와 함께 사용할 수 없습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Decider networks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_2_decider_networks.html)에 대응합니다. NVIDIA 예제의 세 행동을 각각 실행할 수 있도록 장면과 실행기를 묶었습니다. 출처는 `NOTICE.md`, 라이선스는 `LICENSE-NVIDIA-EXAMPLES`를 참고하세요.

세 behavior의 목표 도달·분기 전환·그리퍼 반응은 각각 관찰해야 합니다. `tutorial.json`의 검증 상태는 `not_run`이며 루프 종료가 세 행동의 성공을 뜻하지는 않습니다.
