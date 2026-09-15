# 161. 상자 전도·화재·액체 누출과 배우 반응

권장 학습 순서 **161** · 액터와 공간 이벤트 데이터 · 출처 ID `t071`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

## 이 실습의 의도

물체에 붙인 사건 태그, 시간 trigger, actor의 사건 반응을 연결하여 무엇이 언제 발생했고 누가 반응했는지 영상과 로그로 확인합니다. `prepare.py`가 만드는 기본 IRA 설정은 태그된 창고에서 1초에 Topple 하나를 발생시키고 가까운 actor 한 명이 사건 쪽으로 이동하도록 구성합니다. Fire·Spill은 별도 `incident_config.yaml`을 IRI UI에 로드하는 실습이며, 설정 생성만으로 사건이 실행되거나 두 설정이 자동 합쳐지지는 않습니다.

## 실행 후 확인할 것

- **기본 설정의 사건·반응 연결:** 생성된 `config.yaml`에서 `event.event_list`의 `shelf_topple`과 `response.response_list`의 `inspect_topple`을 확인합니다. response trigger의 `type`은 `physical_event`, `event_name`은 `shelf_topple`이고 명령은 `GoToResponse → LookAround 2`여야 합니다.
- **실제 전도:** IRI가 활성화되고 loose item 태그가 있는 장면에서 실행한 뒤 사건 로그의 이름·시간·대상과 실제 상자의 움직임을 함께 봅니다. 기본 IRA의 시간은 1초이고, 독립 IRI 파일의 Topple 시간은 3초이므로 사용한 설정에 맞춰 비교합니다. 카메라는 사건 대상 쪽으로 자동 이동하지 않으므로 직접 대상도 확인합니다.
- **actor 반응:** 사건 후 선택된 actor가 사건 위치로 향하는지 관찰합니다. 기본 90프레임은 3초라 이동·LookAround·원래 명령 복귀까지 끝나지 않을 수 있으므로 아래 `--frames 300` 절차로 더 길게 확인합니다.
- **독립 IRI의 Fire·Spill:** `report_dir`를 실제 새 절대 경로로 바꾸고 세 사건을 활성화한 경우 6초 화재, 9초 누출 시작, 누출 지속 5초를 로그와 화면에서 비교합니다. 기본 IRA에 화염·액체가 없는 것은 설정대로이며 이 비교는 15초 이상 따로 기록합니다.
- **주석 범위:** 기본 writer의 RGB와 객체 bbox/semantic class에서 전도 대상의 `incident_toppled_item`을 확인합니다. `semantic_filter_predicate`에 화재·누출 class가 적혀 있어도 그 사건이 자동 활성화되거나 개별 화염 마스크·semantic segmentation 출력이 켜지는 것은 아닙니다.

## 준비와 실행 방식

Isaac Sim 5.1 GUI, NVIDIA RTX GPU/드라이버, Isaac Sim 5.1 Assets 접근이 필요합니다. GUI는 설치 디렉터리의 `./isaac-sim.sh`로 실행합니다. `Window > Extensions`에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 켜고 요구되는 재시작을 마칩니다. 사람 애니메이션은 `omni.anim.people`, `omni.anim.graph`, 경로 탐색은 `omni.anim.navigation`, 로봇은 `isaacsim.anim.robot`가 담당하며 IRA 의존성으로 활성화됩니다. 클라우드 LLM·ROS·별도 Python 설치는 필요하지 않습니다.

기본 환경은 `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Incidents/full_warehouse_with_incident_tags.usd`라는 사건 태그가 있는 창고이며, 사람은 같은 Assets 루트의 `/Isaac/People/Characters/`입니다. 오프라인 자산팩을 설치했다면 `--assets-root /절대경로/Assets/Isaac/5.1`을 지정합니다. 자산팩 자체는 이 패키지에 포함하지 않습니다.

이 패키지는 원문의 **확장 UI와 YAML 설정 방식**을 유지합니다. `prepare.py`는 해당 수업 설정과 명령 파일을 실제 생성합니다. 설정을 만드는 것만으로 사람을 시뮬레이션하거나 영상을 저장하지는 않습니다. 모든 명령은 이 패키지 디렉터리에서 실행합니다.

```bash
python3 prepare.py --output ./output/run_01 --frames 90
/home/hoyunkim/isaacsim/isaac-sim.sh
```

설치 경로는 자신의 환경에 맞게 바꿉니다. `output/run_01/config.yaml`은 JSON 문법으로 작성한 유효한 YAML 1.2 파일이며 Isaac Sim의 YAML 로더가 읽습니다. `lesson.json`의 `{ASSETS}`, `{OUTPUT}`, `{PACKAGE}`는 준비 스크립트가 절대 경로로 치환합니다. `isaacsim.replicator.agent` 아래에 설정을 중첩하는 구조는 설치된 5.1 기본 설정과 같습니다. 설정 버전 `0.7.0`은 Sim 버전 `5.1.0`과 다른 IRA 설정 호환성 버전입니다.

1. `Tools > Action and Event Data Generation > Actor SDG`를 엽니다. `Config File Path`에서 생성한 `config.yaml`을 선택합니다.
2. 환경에 NavMesh가 없으면 태그된 기본 창고 USD를 먼저 열고, Stage 우클릭 `Create > Navigation > NavMesh Include Volume`을 추가해 바닥을 덮습니다. `Window > Navigation > NavMesh`에서 Bake 후 `Save As`로 패키지 `output/warehouse_nav.usd`에 저장합니다. `Scene > Asset Path`를 그 복사본으로 바꾸고 설정을 저장합니다. NavMesh는 사람이 서거나 걸을 수 있는 표면입니다.
3. `Set Up Simulation`을 누르고 사람/카메라 자산 로딩이 끝날 때까지 기다립니다. Stage의 `/World/Characters`, `/World/Cameras`에서 실제 이름을 확인합니다. 명령의 `Character_01` 같은 이름은 실제 탭 이름과 일치시킵니다.
4. Character 패널에서 명령을 확인하고 디스크 아이콘으로 **Save Commands**합니다. UI의 파란색은 미저장, 빨간색은 잘못된 입력입니다. 설정만 바꾸면 화면 값과 디스크 파일이 달라질 수 있으므로 `Save`도 누릅니다.
5. 아래 수업별 조작을 진행한 다음 `Start Data Generation`을 누릅니다. 기본 90프레임은 30 FPS 기준 3초입니다. 완료 후 `output/run_01/capture`를 확인합니다. 중단 후 재실행할 때는 저장 종료를 기다립니다.

## 외부 확장과 장면 준비

추가로 `Window > Extensions`에서 `isaacsim.replicator.incident`를 검색해 설치된 IRI core/UI를 활성화합니다. UI가 요구하는 의존 확장도 켭니다. 사건 자산/시각 효과는 Isaac Sim Assets에서 가져옵니다. `lesson.json`은 `/Isaac/Samples/Replicator/Incidents/full_warehouse_with_incident_tags.usd`의 이미 태그된 공식 장면을 사용합니다. 화염을 임의 파티클로 흉내 내지 않고 IRI의 실제 효과를 사용합니다.

## IRI 단독 UI에서 세 사건 만들기

1. 위 태그된 장면을 열거나 일반 창고에서 작업합니다. 일반 창고라면 NavMesh를 Bake한 후 선반의 상자 Prim을 선택하고 `Tools > Action and Event Data Generation > Event Scene Tagger`에서 `Tag Loose Items: Navmesh`를 누릅니다. 힘은 가까운 NavMesh 가장자리 방향으로 가해집니다. 태그를 저장하려면 File > Save As로 새 USD를 만듭니다.
2. 같은 창에서 Random Direction 태그와 Closest Waypoint Direction 태그도 비교합니다. 후자는 Add Waypoint Prim으로 통로 위치의 상자를 만들고 크기/위치를 조절해야 합니다. waypoint는 필요하면 visibility를 꺼도 됩니다. Untag는 선택 Prim뿐 아니라 하위 Prim까지 지웁니다.
3. 화재를 위한 보이는 Mesh가 있는 물체를 Flammable Items로, 통을 Spillable Items로, 바닥을 Spillable Area Floor로 태그합니다. 누출 영역 태그가 없으면 z=0 바닥에 액체가 생성될 수 있습니다.
4. `incident_config.yaml`의 `report_dir`를 새로운 절대 출력 경로로 바꾼 복사본을 만듭니다. `Tools > Action and Event Data Generation > Event Config File`에서 복사본을 로드합니다. 첫 실행은 Fire/Spill을 UI에서 제거하고 Topple만 남깁니다. `topple_item=$random_loose_item$`, 반경 1.5 m, time=3 s를 확인합니다.
5. `Set Up Events`를 누른 뒤 `Record Events`로 실행합니다. 사건의 시점/물체를 이벤트 로그에서 확인하고 `Stop Record`로 끝냅니다. 시점이 지나도 카메라가 사건 위치로 자동 이동하지 않으므로 직접 상자 근처를 봅니다.
6. 태그된 장면에 Fire와 Spill을 복원한 새 설정으로 15초 이상 기록합니다. 각각 6초에 점화, 9초에 5초 동안 누출하도록 되어 있습니다. `target_size=1.5`는 액체 최종 크기, `leak_duration=5`는 퍼지는 시간입니다.

## IRA와 사건 반응 함께 생성

1. `prepare.py --frames 300 --output output/actor_event`로 새 설정을 만들고 Actor SDG에서 로드합니다. 이 설정은 의도적으로 Topple 하나만 1초에 일어나게 합니다. 배우 한 명·카메라 한 대로 사건과 반응을 따라가기 쉽습니다.
2. Events 패널에서 `shelf_topple`, Response 패널에서 `inspect_topple`을 확인합니다. `physical_event` trigger의 `event_name`이 정확히 `shelf_topple`이어야 합니다. `GoToResponse`는 사건 위치로 이동하는 특수 명령이며 뒤의 `LookAround 2`를 함께 실행합니다.
3. Setup → Generate Random Commands → Save → Start Data Generation 순서로 실행합니다. 사건 로그와 actor 동작, RGB 및 객체 bbox에 붙은 semantic class를 함께 비교합니다. 기본 설정은 semantic segmentation 이미지를 켜지 않습니다. generic actor 문서의 `incident`와 이 IRI 통합 설정의 `event` 표기가 섞여 있으므로 본 패키지는 설치된 5.1 `incident_bridge.py`가 읽는 **event/event_list** 구조를 사용합니다.

전도된 물체는 `incident_toppled_item`, 불붙은 물체는 `incident_flaming_item`, 새는 물체는 `incident_leaking_item`, 액체 면은 `incident_liquid_spill` semantic label을 가집니다. 화염 자체를 쓰려면 별도 writer가 필요하므로 RGB 화염이 보인다고 개별 화염 마스크까지 생성됐다고 판단하지 않습니다.

완료 기준은 실제 사건 로그의 시간/대상, 움직인 상자 또는 생성된 액체/화염, 대응 actor가 사건 쪽으로 이동하는 것입니다. 한 변수 실험은 topple 반경만 1.5 → 0.2 m로 줄여 함께 떨어지는 이웃 물체 수를 비교합니다. 태그 없는 물체만 있으면 `$random_*` 대상이 없으므로 Scene Tagger부터 확인합니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [IRI 단독 UI](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html#iri-standalone-ui-example)
- [태그 종류](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html#scene-tagging)
- [설정 파일](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html#event-configuration-in-iri-script)
- [IRA 통합](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html#ira-integration)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
