# 157. 정해진 행동 사이에 다른 명령을 넣으면 어떻게 될까요?

## 이번에 배우는 것

**사람의 기본 명령, 무작위 명령 전이, 실행 중 반응을 비교하며 행동 순서가 결정되는 위치를 이해합니다.**

“둘러보다 잠시 멈추세요”라는 행동은 미리 파일에 적을 수도 있고, 실행 중 특정 시점에 끼워 넣을 수도 있습니다. 결과 자세가 비슷해도 명령을 정하는 과정은 다릅니다. 기본 행동을 먼저 확인한 뒤 1초 시점의 반응을 추가해 봅니다.

| 파일 | 적용 시점 | 담당하는 내용 |
|---|---|---|
| `character_commands.txt` | 기본 실행 | 두 사람의 Idle·LookAround 순서 |
| `transition_map.json` | 무작위 명령 생성 | 다음 명령을 고를 상대 비중 |
| `time_response.json` | 시뮬레이션 중 | 1초에 모든 actor에게 Idle 삽입 |
| `queue_commands.txt` | 줄서기 실습 | 줄 위치, 대기, 출구 이동 |
| `custom_commands.json` | 등록 후 Setup | 외부 애니메이션 자산 목록 |

`prepare.py`는 기본 사람·로봇 명령 파일만 복사합니다. 보조 JSON과 Queue 파일은 아래에서 직접 적용해야 합니다.

## 1. 두 사람의 기본 명령 실행하기

Isaac Sim 5.1과 RTX GPU, 5.1 창고·사람 자산이 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
python3 src/157_events_ext_replicator_agent_actor_control/prepare.py --output src/157_events_ext_replicator_agent_actor_control/output/base --frames 180
~/isaacsim/isaac-sim.sh
```

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화하고 필요한 재시작을 마칩니다.
2. **Tools > Action and Event Data Generation > Actor SDG**에서 `output/base/config.yaml`을 불러옵니다. Scene은 5.1 `Simple_Warehouse/full_warehouse.usd`입니다.
3. 창고에 NavMesh가 없으면 Scene을 열어 **Create > Navigation > NavMesh Include Volume**으로 바닥을 덮고 **Window > Navigation > NavMesh**에서 Bake합니다. 새 USD로 저장해 **Scene > Asset Path**에 지정하세요.
4. **Set Up Simulation** 후 실제 Character 이름과 명령 파일 이름을 맞춥니다. **Save Commands**, 설정 **Save**, **Start Data Generation** 순서로 진행합니다.

180프레임은 30 FPS에서 6초입니다. 기본 명령과 뒤에서 넣을 반응을 구별하기 위해 관찰 시간을 넉넉히 잡았습니다. 생성이 끝나도 창은 남으며 직접 닫아 종료합니다. 설정 생성 도구 자체는 GUI를 실행하지 않습니다.

### 설정에서 볼 부분

```text
Character_01 Idle 1
Character_01 LookAround 2
Character_02 LookAround 3
```

각 줄의 첫 이름으로 명령을 나눕니다. Character_01은 Idle 다음 LookAround를 수행하고, Character_02는 시작부터 LookAround를 수행합니다. 시간 단위는 초입니다. 기본 사람 수는 2, 로봇 수는 0이므로 로봇 명령 파일의 존재만으로 로봇이 나타나지는 않습니다.

### 실행 결과 확인하기

Character_02가 처음부터 둘러보는 모습을 먼저 기억해 두세요. 다음 절에서는 같은 사람이 1초에 Idle로 바뀌는지 비교합니다. `output/base/capture`의 RGB와 actor id를 함께 보면 누구의 행동인지 추적하기 쉽습니다. 기본 명령에서 몸 위치가 거의 바뀌지 않아도 정상입니다.

## 2. 명령 전이와 시간 반응 적용하기

### 설정에서 볼 부분

`transition_map.json`의 Idle 항목은 다음과 같습니다.

```json
{
  "Idle": {
    "weight": 1,
    "transitions": {"LookAround": 1}
  }
}
```

`weight`는 **첫 명령**을 고르는 비중이고 `transitions`는 **이 명령 다음**에 올 명령의 비중입니다. 제공된 표는 Idle로 시작해 Idle과 LookAround를 번갈아 선택합니다. GoTo는 시작 비중이 0이고 다른 명령에서 들어오는 연결도 없어 선택되지 않습니다.

**Tools > Action and Event Data Generation > Command Settings**의 Command Randomization Panel에서 이 파일을 불러오세요. **Generate Random Commands**로 생성된 문자열을 읽고 **Save Commands**합니다. 전이표를 불러오는 것과 저장된 명령을 교체하는 것은 별도 단계입니다.

보행도 포함하려면 전이표 복사본의 `LookAround.transitions`에 `GoTo: 1`을 추가하고, General Command Settings에서 GoTo의 최소·최대 거리를 2·5 m로 설정하세요. 다시 명령을 생성해 `Character_01 GoTo 2 0 0 _`처럼 목적지와 마지막 방향 인수가 생기는지 읽습니다. 좌표는 m, 마지막 방향 숫자는 도이며 `_`는 방향을 강제하지 않는 자리입니다. 목적지가 NavMesh 위인지 확인한 다음 명령을 저장하세요. 기본 전이표에는 GoTo로 들어가는 연결이 없으므로 거리 범위만 바꿔서는 보행이 추가되지 않습니다.

이번에는 기본 명령을 유지한 새 실행에 시간 반응을 추가합니다.

```bash
python3 src/157_events_ext_replicator_agent_actor_control/prepare.py --output src/157_events_ext_replicator_agent_actor_control/output/response_01 --frames 180
```

생성된 `config.yaml`을 텍스트 편집기로 열고 `isaacsim.replicator.agent` 안에 `response` 항목을 추가합니다. 값으로 `time_response.json`의 **전체 JSON 객체**를 넣으세요. 핵심 구조는 다음과 같습니다.

```text
response.response_list[0].CommandResponse
    name: pause_everyone
    trigger: { type: time, time: 1.0 }
    pick_agent: all
    commands: ["Idle 1"]
    resume: true
```

새 설정에도 준비한 NavMesh Scene 경로를 지정한 뒤 Actor SDG에서 다시 Setup·저장·생성합니다. `pick_agent: all`은 모든 actor를 선택하고, `resume: true`는 반응 후 원래 명령으로 돌아가도록 합니다. Idle은 사람과 로봇이 함께 사용하는 명령이어서 혼합 장면의 반응에도 적합합니다.

### 실행 결과 확인하기

Character_02가 LookAround 도중 1초에 Idle로 전환하고, 반응 후 원래 동작으로 돌아가는지 보세요. Character_01은 원래도 처음 1초가 Idle이므로 자세만으로 개입 시점을 구별하기 더 어렵습니다.

Play 중 **Command Injection** 창에서 `Character_02 Idle 2`를 Inject하면 수동 개입도 비교할 수 있습니다. 메뉴에서 찾기 어렵다면 **Tools > Replicator** 또는 **Action and Event Data Generation** 아래를 확인하세요. 이 경우 시작 시점은 시간 trigger가 아니라 사용자의 클릭입니다. Queue·Queue_Spot처럼 줄 자체를 선언하는 행은 개별 actor에게 주입할 명령과 구분하세요.

로봇을 비교할 때는 새 설정에서 `robot.nova_carter_num`을 1로 바꾸고 Setup한 뒤 Robot 탭 이름에 `Nova_Carter_01 GoTo 2 0 0`, `Nova_Carter_01 Idle 2`를 저장합니다. 사람과 달리 GoTo에 마지막 yaw를 붙이지 않습니다. iw.hub도 비교하려면 새 설정의 `robot.iw_hub_num`을 1로 바꾸고 재Setup한 뒤 실제 Robot 탭 이름에 `LiftUp`, `Idle 2`, `LiftDown`을 순서대로 저장해 적재판의 올라감·대기·내려감을 관찰하세요. LookAround는 로봇 공통 명령이 아니므로 모든 actor를 선택하는 반응에는 제공 예시처럼 Idle을 사용하세요.

### 줄서기와 사용자 동작으로 확장하기

`queue_commands.txt`에는 Queue 선언, Queue_Spot, 사람별 `Queue → LookAround → Dequeue`가 함께 있습니다. 새 출력의 명령 파일을 이 **전체 파일**로 교체하고 줄 위치와 출구를 실제 NavMesh 위에 맞추세요. Queue 한 줄만 복사하면 줄 위치와 출구가 준비되지 않습니다. `--frames 600` 정도로 시간을 늘려 대기와 출구 이동까지 봅니다.

Sit에는 `/World/Chair` 같은 의자 아래 접근 위치 `walk_to_offset`과 착석 위치 `interact_offset`이 필요합니다. 이를 준비한 뒤 `Character_01 Sit /World/Chair 3`을 사용하세요. 의자 크기와 접근 위치를 맞추지 않은 상태에서는 명령만으로 착석이 완성되지 않습니다.

커스텀 애니메이션은 Custom Command Panel에 `custom_commands.json`을 로드하고 Setup을 다시 실행합니다. 이 파일은 5.1 Assets의 `push_button.skelanim.usd`, `type_keyboard.skelanim.usd`를 가리킵니다. USD의 `CustomCommandName`과 `CustomCommandTemplate`을 확인하고 그 이름으로 명령을 저장하세요. `Timing`은 시간, `TimingToObject`는 대상 Prim과 시간, `GoToBlend`는 이동과 혼합할 동작에 해당합니다. 객체 상호작용에는 `CustomCommandInteractObjectFilter`와 맞는 대상의 class semantic label이 필요합니다. 무작위 지속 시간을 사용할 때는 `CustomCommandRandomMinTime`·`CustomCommandRandomMaxTime`도 확인합니다. 임의 skeleton 자산은 Biped에 맞추는 retarget 작업이 먼저 필요합니다.

별도 Python 행동 구현이 있다면 Script Editor에서 `set_actor_behavior.py`를 실행한 뒤 `set_actor_behavior(character='/절대경로/my_behavior.py')`를 호출할 수 있습니다. 이 함수는 기존 `.py` 파일을 검사하고 behavior 경로를 바꿉니다. 변경한 뒤 **Set Up Simulation**을 다시 실행해야 새 actor에 반영됩니다. Nova Carter와 iw.hub의 구현은 `nova_carter=...`, `iw_hub=...` 인수로 각각 지정합니다. 새 행동 코드를 작성하거나 JSON을 자동 등록하지는 않습니다.

## 3. 행동을 결정하는 시점 정리

```text
고정 명령 → 실행 전에 순서와 시간 결정
전이표 → 무작위 명령 생성 때 순서 선택 → 명령 저장
시간 반응 → 실행 중 trigger 성립 → 임시 명령 → 원래 행동 복귀
수동 주입 → 사용자가 Inject한 시점에 현재 행동 변경
```

**전이표는 명령을 만드는 규칙이고 반응은 실행 중인 행동에 개입하는 규칙입니다.** 화면에 Idle이 보인다는 사실만으로 어느 규칙이 적용됐는지는 알 수 없습니다. 저장된 명령과 개입 시점을 함께 비교하세요.

## 4. 간단한 확인 실험

`response_01` 설정을 복사한 새 실행에서 `trigger.time`만 `1.0`에서 `2.0`으로 바꿔 보세요. 결과 저장 경로는 새 폴더로 지정합니다.

- Character_02가 더 오래 둘러본 뒤 멈추는지 봅니다.
- 반응 지속 시간 `Idle 1`과 `resume: true`는 유지합니다.
- 30 FPS라면 개입 시점이 약 30프레임 뒤로 옮겨지는지 같은 actor의 RGB에서 비교합니다.

## 실행할 때 막히면

- **전이표를 바꿔도 행동이 같음**: 명령을 다시 생성하고 Save Commands했는지 확인하세요.
- **반응이 시작되지 않음**: 설정의 `response.response_list` 위치를 확인하세요. 보조 JSON은 자동 병합되지 않습니다.
- **Queue에서 나오지 않음**: 해당 actor의 Dequeue와 유효한 출구 좌표를 확인하고 관찰 시간을 늘리세요.
- **커스텀 명령이 없음**: 등록 후 Setup을 다시 실행했는지, 명령 이름이 USD의 이름과 같은지 확인하세요.
- **behavior 교체 오류**: IRA를 활성화하고 실제 `.py` 파일 경로를 전달하세요. 기본 행동으로 돌아갈 때는 기존 확장 behavior 경로를 복원하고 Setup합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Actor Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html)에 대응합니다. 로컬 전이표·반응·Queue 파일로 명령 생성과 실행 중 개입을 비교하도록 구성했습니다.

`tutorial.json`은 `not_run`입니다. 기본 명령, Queue, 사용자 애니메이션은 각각 준비 조건이 다르며 설정 저장이 실제 행동 재생을 보증하지 않습니다.
