# 157. 사람·로봇 명령, 무작위 전이와 실시간 반응

권장 학습 순서 **157** · 액터와 공간 이벤트 데이터 · 출처 ID `t054`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

## 이 실습의 의도

사람의 행동을 고정 명령, 무작위 전이표, 실행 중 명령 주입, trigger 반응으로 제어하는 차이를 비교합니다. 기본 설정은 사람 두 명의 `Idle`/`LookAround`만 포함하므로 Queue·자동 반응·커스텀 애니메이션은 각 보조 파일을 아래 절차로 적용해야 시작됩니다. `prepare.py`는 `lesson.json`과 기본 사람·로봇 명령 파일만 출력에 복사하며 GUI 실행이나 보조 JSON의 자동 등록을 수행하지 않습니다.

## 실행 후 확인할 것

- **기본 명령:** Setup 후 실제 actor 이름을 확인하고 저장한 명령대로 Character_01의 `Idle 1 → LookAround 2`, Character_02의 `LookAround 3`이 보이는지 관찰합니다. 초기 로봇 수는 0이며 사람 둘이 보행하지 않는 것이 기본 결과입니다.
- **전이표를 적용한 경우:** `transition_map.json`을 로드한 후 **Generate Random Commands → Save Commands**로 생성된 문자열을 확인합니다. 첫 명령은 Idle이고 Idle/LookAround가 번갈아 나와야 합니다. GoTo의 초기 weight는 0이고 이 기본 전이에는 GoTo로 가는 연결이 없습니다.
- **Queue를 적용한 경우:** 통로에 맞춘 Queue_Spot과 전체 `queue_commands.txt`를 사용했을 때 각 actor가 Queue 진입, LookAround, Dequeue 출구 이동을 차례로 하는지 봅니다. 기본 90프레임은 3초이므로 줄 대기와 출구 이동 전체를 확인하려면 아래 600프레임 실행처럼 시간을 늘립니다.
- **주입·반응을 적용한 경우:** Play 중 `Idle 2`를 Inject하면 진행 중인 명령이 중단되는지 봅니다. `time_response.json`을 `lesson.json`의 `response`에 넣은 새 실행에서는 1초에 모든 actor가 `Idle 1`을 수행하고 `resume=true`에 따라 복귀하는지 확인합니다.
- **사용자 동작의 별도 조건:** Sit에는 접근·착석 Xform이 있는 의자, 커스텀 애니메이션에는 Biped에 맞춘 자산과 재Setup, behavior 교체에는 실제 Python 구현이 필요합니다. 설정 경로나 파일 등록만 성공한 상태를 그 동작의 재생 성공으로 보지 않습니다.

## 준비와 실행 방식

Isaac Sim 5.1 GUI, NVIDIA RTX GPU/드라이버, Isaac Sim 5.1 Assets 접근이 필요합니다. GUI는 설치 디렉터리의 `./isaac-sim.sh`로 실행합니다. `Window > Extensions`에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 켜고 요구되는 재시작을 마칩니다. 사람 애니메이션은 `omni.anim.people`, `omni.anim.graph`, 경로 탐색은 `omni.anim.navigation`, 로봇은 `isaacsim.anim.robot`가 담당하며 IRA 의존성으로 활성화됩니다. 클라우드 LLM·ROS·별도 Python 설치는 필요하지 않습니다.

기본 환경은 `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Environments/Simple_Warehouse/full_warehouse.usd`, 사람은 같은 Assets 루트의 `/Isaac/People/Characters/`입니다. 오프라인 자산팩을 설치했다면 `--assets-root /절대경로/Assets/Isaac/5.1`을 지정합니다. 자산팩 자체는 이 패키지에 포함하지 않습니다.

이 패키지는 원문의 **확장 UI와 YAML 설정 방식**을 유지합니다. `prepare.py`는 해당 수업 설정과 명령 파일을 실제 생성합니다. 설정을 만드는 것만으로 사람을 시뮬레이션하거나 영상을 저장하지는 않습니다. 모든 명령은 이 패키지 디렉터리에서 실행합니다.

```bash
python3 prepare.py --output ./output/run_01 --frames 90
/home/hoyunkim/isaacsim/isaac-sim.sh
```

설치 경로는 자신의 환경에 맞게 바꿉니다. `output/run_01/config.yaml`은 JSON 문법으로 작성한 유효한 YAML 1.2 파일이며 Isaac Sim의 YAML 로더가 읽습니다. `lesson.json`의 `{ASSETS}`, `{OUTPUT}`, `{PACKAGE}`는 준비 스크립트가 절대 경로로 치환합니다. `isaacsim.replicator.agent` 아래에 설정을 중첩하는 구조는 설치된 5.1 기본 설정과 같습니다. 설정 버전 `0.7.0`은 Sim 버전 `5.1.0`과 다른 IRA 설정 호환성 버전입니다.

1. `Tools > Action and Event Data Generation > Actor SDG`를 엽니다. `Config File Path`에서 생성한 `config.yaml`을 선택합니다.
2. 환경에 NavMesh가 없으면 창고 USD를 먼저 열고, Stage 우클릭 `Create > Navigation > NavMesh Include Volume`을 추가해 바닥을 덮습니다. `Window > Navigation > NavMesh`에서 Bake 후 `Save As`로 패키지 `output/warehouse_nav.usd`에 저장합니다. `Scene > Asset Path`를 그 복사본으로 바꾸고 설정을 저장합니다. NavMesh는 사람이 서거나 걸을 수 있는 표면입니다.
3. `Set Up Simulation`을 누르고 사람/카메라 자산 로딩이 끝날 때까지 기다립니다. Stage의 `/World/Characters`, `/World/Cameras`에서 실제 이름을 확인합니다. 명령의 `Character_01` 같은 이름은 실제 탭 이름과 일치시킵니다.
4. Character 패널에서 명령을 확인하고 디스크 아이콘으로 **Save Commands**합니다. UI의 파란색은 미저장, 빨간색은 잘못된 입력입니다. 설정만 바꾸면 화면 값과 디스크 파일이 달라질 수 있으므로 `Save`도 누릅니다.
5. 아래 수업별 조작을 진행한 다음 `Start Data Generation`을 누릅니다. 기본 90프레임은 30 FPS 기준 3초입니다. 완료 후 `output/run_01/capture`를 확인합니다. 중단 후 재실행할 때는 저장 종료를 기다립니다.

## 명령을 단계별로 바꾸기

1. 기본 `Idle 1 → LookAround 2`를 실행해 시간 단위가 초인 것을 확인합니다. 사람의 이동은 `Character_01 GoTo 2 0 0 _`이며 끝의 `_`는 도착 방향을 강제하지 않는다는 뜻입니다. 해당 지점이 NavMesh 위에 있을 때만 사용합니다. 사람의 마지막 방향은 `90`처럼 도 단위로 지정할 수도 있습니다.
2. `Tools > Action and Event Data Generation > Command Settings`의 Command Randomization Panel에서 `transition_map.json`을 엽니다. 초기 `weight`는 첫 명령 선택 비중, `transitions`는 다음 명령의 상대 비중입니다. 여기서는 Idle로 시작해 Idle/LookAround가 번갈아 나옵니다. Generate Random Commands, Save Commands, 데이터 생성을 순서대로 수행하고 실제 문자열 순서를 확인합니다.
3. General Command Settings의 GoTo 최소/최대 거리를 2/5 m로 조절합니다. 전이표에서 LookAround 다음 GoTo 비중을 1로 추가한 복사본을 로드하면 이동도 포함됩니다. 무작위 명령의 Idle은 기본 2–6초, LookAround는 2–4초라 3초 실습을 넘어갈 수 있습니다.
4. Queue는 개별 명령만으로 만들어지지 않습니다. `queue_commands.txt`의 Queue 선언·Queue_Spot 좌표를 창고 통로 안으로 옮긴 다음 전체 명령 파일로 사용합니다. `Queue → LookAround → Dequeue` 세 단계가 각 actor에 모두 있어야 줄에서 빠져나옵니다. 오래 관찰하려면 `prepare.py --frames 600 --output output/queue_run`으로 20초를 생성합니다.
5. Sit을 시험하려면 의자 Prim `/World/Chair` 아래 Xform `walk_to_offset`, `interact_offset`을 만들고 각각 접근 위치/실제 착석 위치를 맞춥니다. `Character_01 Sit /World/Chair 3`을 사용합니다. 고정된 애니메이션이므로 의자 크기가 맞아야 합니다. 준비된 의자 없이 명령만 넣어 성공했다고 판단하지 않습니다.
6. Nova Carter를 1대 추가하면 Robot 명령은 `Nova_Carter_01 GoTo 2 0 0`, `Nova_Carter_01 Idle 2`처럼 종료 회전 인수가 없습니다. iw.hub의 `LiftUp`, `LiftDown`은 적재판을 4 cm 움직입니다. 실제 탭 이름을 먼저 확인합니다.
7. Play 중 `Tools > Replicator > Command Injection`을 열고 `Character_01 Idle 2`를 Inject합니다. 메뉴가 이동되어 있으면 Action and Event Data Generation 아래의 Command Injection을 찾습니다. 배우는 현재 명령을 중단합니다. Queue 같은 전역 선언은 injection 대상이 아닙니다.
8. 자동 반응은 `time_response.json` 내용을 `lesson.json`의 `isaacsim.replicator.agent.response`에 넣고 새 설정을 생성해 시험합니다. 모든 actor가 1초 시점에 `Idle 1`을 수행한 뒤 원래 명령으로 복귀합니다. 혼합 actor에 LookAround를 주면 로봇이 지원하지 않으므로 여기서는 공통 Idle을 사용합니다. `priority`가 높을수록 기존 반응을 선점하며 `resume`이 복귀 여부입니다. trigger는 time, carb_event, incident 유형도 지원합니다.

## Behavior Script를 교체하는 경우

Actor 명령의 해석은 USD Stage 이벤트를 구독하는 Behavior Script가 담당합니다. 이미 준비한 `omni.kit.scripting.BehaviorScript` 기반 Python 구현이 있다면 Script Editor에서 `set_actor_behavior.py`를 열어 실행하고 `set_actor_behavior(character='/절대경로/my_behavior.py')`를 호출한 뒤 Setup합니다. Nova Carter/iw.hub는 `nova_carter=...`, `iw_hub=...`로 별도 지정합니다. 초기 명령 실습에는 사용자 behavior 파일이 필요 없습니다. 기본 동작을 복원하려면 확장 기본 behavior script 경로를 다시 설정하고 Setup합니다. 설정 경로만 바꾸는 것은 새 behavior 구현을 자동으로 작성하는 일이 아닙니다. 원문 예시의 slash 형태 설정 경로와 미정의 script_path 변수를 그대로 복사하지 않고, 설치된 5.1 extension.toml의 `/exts/isaacsim.replicator.agent/behavior_script_settings/` 키와 전달된 실제 파일을 사용합니다.

## 커스텀 애니메이션 실습

Command Settings의 Custom Command Panel에서 `custom_commands.json`을 로드하거나 Add로 파일 두 개를 등록합니다. 두 USD는 5.1 공식 Assets에 이미 NVIDIA Biped용으로 설정되어 있습니다. `Set Up Simulation`을 다시 해야 Biped_Setup에 애니메이션 노드가 만들어집니다. USD를 열어 루트가 SkelAnimation인지, `CustomCommandName`, `CustomCommandTemplate`을 확인하고 표시된 명령 이름을 사용합니다.

새 애니메이션은 Biped skeleton으로 retarget된 자산이어야 합니다. Timing은 시간만, TimingToObject는 대상 Prim+시간, GoToBlend는 걷기와 blend합니다. 무작위 Timing에는 `CustomCommandRandomMinTime`, `CustomCommandRandomMaxTime`, 객체 상호작용에는 `CustomCommandInteractObjectFilter`와 일치하는 `class` semantic label도 필요합니다. 파일 등록만으로 임의 skeleton 애니메이션을 재생할 수는 없습니다.

완료 기준은 지정 순서의 자세 변화, Queue의 출구 이동, injection 직후 Idle 전환을 각 실습에서 직접 관찰하는 것입니다. 한 변수 실험으로 response 시간만 1초에서 2초로 바꾸어 개입 시점을 비교합니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [사람 및 로봇 명령](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html#character)
- [커스텀 명령과 전이](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html#custom-commands-and-randomization)
- [명령 주입](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html#command-injection)
- [반응과 trigger](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html#actor-response-and-triggers)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
