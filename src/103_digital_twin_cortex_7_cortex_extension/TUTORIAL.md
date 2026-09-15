# 103. 앱 안에서 Cortex 행동의 시작과 초기화를 관리하기

## 이번에 배우는 것

**공식 Cortex GUI의 LOAD·START·RESET을 사용하고, 작은 로컬 확장의 코드에서 UI 작업과 물리 콜백의 역할을 살펴봅니다.**

독립 Python 예제는 `SimulationApp`을 만들고 자기 반복문으로 실행합니다. 이미 열린 Isaac Sim 앱의 확장은 앱의 업데이트 흐름에 작업을 연결해야 합니다. 버튼을 눌렀을 때 시간이 걸리는 장면 로딩을 예약하고, 물리가 진행될 때 Cortex의 판단과 명령을 처리합니다.

| 비교 대상 | 공식 Robotics Examples | 로컬 `KR Cortex World Lab` |
|---|---|---|
| 제공 기능 | Franka 행동 선택, 진단, UR10 예제 | 두 손끝 목표와 LOAD·RESET 구조 |
| 주요 파일 | 설치본 interactive examples | `extension/kr_cortex_lab/__init__.py` |
| 화면의 역할 | behavior 실행과 진단 | 비동기 작업 및 목표 변경 학습 |
| 현재 주의점 | RESET 버튼으로 초기화 | context의 `reset()` 미구현 제한 |

**설치된 5.1 SDK 기준으로 현재 로컬 확장은 LOAD를 정상 완료할 수 없는 초기화 제한이 있습니다.** 먼저 공식 GUI에서 실행 흐름을 경험하고, 로컬 코드는 그 구조와 제한을 함께 읽습니다. 창이 생긴 것만으로 로봇 실행이 성공했다고 판단하지 않습니다.

## 1. 공식 Cortex GUI로 행동 실행하기

Isaac Sim 5.1, 지원 NVIDIA RTX GPU와 Franka·UR10 샘플 자산이 필요합니다. 저장소 루트에서 새 앱을 시작하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. **Window > Examples > Robotics Examples**를 엽니다.
2. **Cortex > Franka Cortex Examples**를 선택합니다.
3. behavior 목록에서 block stacking을 고르고 **LOAD**, **START**를 차례로 누릅니다.
4. 블록을 집고 놓는 동안 Diagnostic monitor의 decision stack과 작업 진단을 읽습니다.
5. 초기화할 때는 **RESET**을 사용합니다. 타임라인의 Stop → Play와 예제의 전체 초기화가 같은 작업은 아닙니다.

### 설정에서 볼 부분

LOAD는 로봇과 장면, behavior를 준비하고 START는 준비된 행동을 진행시킵니다. Diagnostic monitor의 decision stack은 현재 어떤 판단 경로가 선택되었는지 보여 줍니다. 팔이 어느 방향으로 움직이는지만 보는 것보다 “지금 집기인지 놓기인지”를 이해하기 쉽습니다.

Franka 예제의 behavior 목록은 기존 로봇에 적용할 행동 정책을 고르는 곳입니다. 블록 쌓기와 peck을 바꾸면 좌표 하나가 아니라 **어떤 상황에 어떤 행동을 할지 정한 규칙**이 바뀝니다.

### 실행 결과 확인하기

집기·놓기 등 현재 동작과 decision stack이 대응하는지 확인하세요. 예제를 초기화한 뒤 같은 시작 흐름으로 돌아오는지도 봅니다. 별도의 새 세션에서 **Cortex > UR10 Palletizing**을 열어 **LOAD → START PALLETIZING**으로 실행하면 부착과 뒤집기 여부의 진단을 비교할 수 있습니다.

## 2. 로컬 확장에서 UI와 Cortex의 연결 읽기

`extension/config/extension.toml`은 `omni.ui`, `isaacsim.core.api`, `isaacsim.cortex.framework`를 의존성으로 선언하고 `kr_cortex_lab` 모듈을 로드합니다.

로컬 UI를 확인하려면 새 Isaac Sim 세션에서 **Window > Extensions**의 Extension Search Paths에 이 튜토리얼 폴더의 절대 경로를 추가합니다. 그 아래 `extension/config/extension.toml`을 가진 확장을 발견하면 **KR Cortex World Lab**을 검색해 활성화하세요. LOAD는 새 Stage를 만드는 작업이므로 먼저 작업 중인 장면을 저장합니다.

### 코드에서 볼 부분

버튼은 장면 로딩을 동기적으로 끝날 때까지 붙잡지 않고 비동기 작업으로 예약합니다.

```python
if self.pending is not None and not self.pending.done():
    return
self.pending = asyncio.ensure_future(operation())
```

진행 중인 LOAD나 RESET이 있으면 새 클릭을 무시합니다. `await`로 초기화가 끝나기를 기다리는 동안 앱은 다른 업데이트를 처리할 수 있습니다. 05번의 Script Editor처럼 이미 켜진 앱 안에서 `SimulationApp`을 다시 만들지 않습니다.

의도한 초기화 순서는 다음과 같습니다.

```text
새 Stage → CortexWorld와 물리 context 초기화 → Franka 생성
         → context와 network 등록 → reset_async()
         → kr_cortex_step 콜백 등록 → play_async()
```

다만 현재 코드는 다음 context를 직접 생성합니다.

```python
self.context = DfRobotApiContext(robot)
```

설치된 5.1 SDK의 `DfRobotApiContext`는 `reset()`을 구현하지 않습니다. 상속한 `DfLogicalState.reset()`은 `NotImplementedError`를 내며, `add_decider_network()`가 내부에서 `reset_cortex()`를 호출할 때 이 경로에 도달합니다. 이는 Play를 더 기다리거나 버튼을 다시 누르면 해결되는 문제가 아닙니다. **로컬 코드는 reset을 구현한 context를 사용하도록 별도 수정되어야 다음 실행 단계에 도달할 수 있습니다.**

따라서 아래의 물리 콜백은 현재 LOAD에서는 등록까지 도달하지 못합니다. 초기화 제한이 해결된 뒤 어떤 역할을 맡을 코드인지 읽어 보세요.

```python
self.world.add_physics_callback(
    "kr_cortex_step", lambda dt: self.world.step(False, False)
)
```

두 `False`는 이 호출에서 렌더링과 물리 진행을 다시 요청하지 않는다는 뜻입니다. 물리는 이미 앱이 담당하므로 콜백에서는 Cortex의 모니터·행동·commander를 처리합니다. 여기서 물리를 또 진행시키면 역할이 겹칩니다.

### 실행 결과 확인하기

현재 코드에서는 LOAD 실패와 성공 이후 기대 상태를 구분하세요.

| UI 또는 동작 | 해석 |
|---|---|
| 창만 표시됨 | `on_startup()`에서 UI 생성 완료 |
| LOAD 후 `Failed:`와 초기화 오류 | 현재 context 제한 또는 기존 World 충돌 확인 필요 |
| `Running: left target`와 실제 손끝 운동 | 초기화가 끝난 경우의 확인 기준 |
| TARGET LEFT/RIGHT | 의도한 목표 `(0.5, ±0.25, 0.5)` m |
| RESET | 현재 코드상 마지막 목표를 다시 쓰지 않고 World/Cortex 초기화 |

초기화가 실패하면 목표·RESET의 로봇 동작을 검증한 것으로 기록하지 않습니다. 정상 로드 뒤 확장을 끄는 정리 코드는 자신이 등록한 콜백을 제거하고 World를 Pause하며, Stage의 로봇을 삭제하지는 않습니다.

## 3. 앱과 확장의 책임 정리

```text
앱: 화면 업데이트와 물리 진행
확장 UI: LOAD·RESET을 비동기 작업으로 예약
물리 콜백: Cortex의 판단과 로봇 명령 처리
종료 처리: 예약 작업 취소, 자기 콜백 제거
```

UI의 상태 문구는 작업 단계의 단서입니다. 로딩 중 오류가 난다면 원인을 해결하기 전까지 뒤의 버튼 반응을 정상 실행 결과로 읽지 않습니다. 이 구분은 큰 확장을 만들 때도 중요합니다.

## 4. 간단한 확인 실험

1절의 **공식 Franka 예제를 START한 상태에서 Selected Behavior만 `Block Stacking`에서 `Peck Game`으로** 바꿔 보세요. 새 앱을 열거나 LOAD를 다시 누르지 않습니다. 로봇과 블록이 그대로 남은 상태에서 새 행동이 적용되는지 확인합니다.

이 선택 콜백은 이미 LOAD한 경우 `load_behavior()`를 비동기로 호출합니다. 이것이 같은 로봇에서 실행 중인 행동을 교체하는 방식입니다. 초기 배치부터 다시 보려는 경우에만 RESET 후 START를 사용하세요.

`Peck Game`은 움직인 블록이 없으면 home을 선택합니다. 전환 뒤 블록 하나를 1 cm 넘게 옮겨 손끝이 그 블록을 peck하는지 확인하세요. 같은 블록 이동에 대해 쌓기 정책과 peck 정책이 어떻게 다르게 반응하는지 비교합니다. 이는 로컬 LEFT/RIGHT 버튼의 목표 좌표 변경과 달리 행동 정책 자체를 바꾸는 실험입니다.

## 실행할 때 막히면

- **LOAD에서 `NotImplementedError`**: 위의 context reset 제한을 확인하세요. 현재 로컬 구현의 문제이며 버튼 순서로 해결되지 않습니다.
- **`An existing World is active`**: 로컬 실습이 다른 Core/Cortex World가 있는 세션에서 중복 생성하려 한 것입니다. 새 앱 세션을 사용하세요.
- **확장이 검색되지 않음**: Search Paths 아래에 `extension/config/extension.toml`이 있는지와 의존 확장의 활성 상태를 확인하세요.
- **공식 예제를 Stop/Play한 뒤 상태가 이상함**: 예제의 RESET 버튼으로 초기화하세요. 타임라인 정지와 행동 상태 초기화를 구분합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Building Cortex Based Extensions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_7_cortex_extension.html)에 대응합니다. 공식 `CortexBase` 예제와 작은 로컬 확장의 수명 관리를 비교하며, 네이티브 UI 전체를 복제한 패키지는 아닙니다.

현재 로컬 LOAD 제한은 설치 SDK의 초기화 호출 경로에 근거한 설명입니다. 공식 GUI 대안과 로컬 코드의 제한을 구분해 읽으세요. `tutorial.json`의 검증 상태는 `not_run`이며 공식 GUI 실행까지 확인된 기록은 아닙니다.
