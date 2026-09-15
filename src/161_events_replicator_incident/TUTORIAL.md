# 161. 상자가 쓰러지면 사람은 어떻게 반응할까요?

## 이번에 배우는 것

**물체의 사건 태그, 발생 조건, 사람의 반응을 연결하고 사건 시점과 행동을 함께 읽습니다.**

“1초에 선반의 상자가 쓰러지고 가까운 사람이 다가간다”는 장면에는 세 가지 정보가 필요합니다. 어떤 물체가 쓰러질 수 있는지, 언제 사건을 시작할지, 누가 어떤 행동으로 반응할지입니다. 이번에는 전도 사건 하나로 연결을 확인한 뒤 화재·누출의 별도 설정을 살펴봅니다.

| 파일·항목 | 이번 실습의 역할 |
|---|---|
| 태그된 창고 USD | 사건 대상으로 선택할 수 있는 물체를 제공합니다. |
| `lesson.json`의 `event` | 1초에 `shelf_topple`을 시작합니다. |
| `lesson.json`의 `response` | 가까운 actor가 사건을 확인하도록 합니다. |
| `incident_config.yaml` | IRI 단독 실행용 전도·화재·누출 설정입니다. |
| `prepare.py` | IRA 설정과 명령 파일을 생성합니다. |

두 설정은 자동으로 합쳐지지 않습니다. 기본 IRA 실행에는 전도 하나만 있고 Fire·Spill은 따로 적용합니다.

## 1. 전도 사건과 사람 반응 실행하기

Isaac Sim 5.1, RTX GPU, 5.1 사건·사람 자산이 필요합니다. 저장소 루트에서 실행하세요.

```bash
python3 src/161_events_replicator_incident/prepare.py --output src/161_events_replicator_incident/output/topple_01 --frames 300
~/isaacsim/isaac-sim.sh
```

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화합니다. `isaacsim.replicator.incident`로 검색해 설치된 IRI core/UI도 활성화하고 필요한 재시작을 마칩니다.
2. **Tools > Action and Event Data Generation > Actor SDG**에서 생성한 `output/topple_01/config.yaml`을 엽니다.
3. Scene이 5.1 Assets의 `/Isaac/Samples/Replicator/Incidents/full_warehouse_with_incident_tags.usd`인지 확인합니다. 이 장면은 사건 태그가 있는 창고입니다.
4. NavMesh가 없으면 Scene을 열어 **Create > Navigation > NavMesh Include Volume**으로 바닥을 덮고 **Window > Navigation > NavMesh**에서 Bake하세요. 태그와 NavMesh를 보존한 새 USD를 저장해 **Scene > Asset Path**로 지정합니다.
5. **Set Up Simulation** 후 사람 한 명과 카메라 한 대를 확인합니다. 실제 사람 이름에 맞춰 기본 `LookAround 3` 명령을 저장합니다.
6. Events의 `shelf_topple`, Response의 `inspect_topple`을 확인하고 설정을 저장한 뒤 **Start Data Generation**을 누릅니다.

300프레임은 30 FPS에서 10초입니다. 기본 90프레임보다 길게 설정해 사건 뒤의 이동을 관찰합니다. 카메라는 사건 위치로 자동 이동하지 않으므로 대상 상자가 보이는 뷰를 직접 확보하세요. 완료 후 GUI는 남습니다.

### 설정에서 볼 부분

전도 사건의 이름과 반응의 연결 이름이 같아야 합니다.

```text
ToppleEvent
    name: shelf_topple
    item: $random_loose_item$
    topple_nearby_radius: 1.5
    trigger: { type: time, time: 1.0 }

CommandResponse
    name: inspect_topple
    trigger: { type: physical_event, event_name: shelf_topple }
    pick_agent: nearest
    commands: [GoToResponse, LookAround 2]
    resume: true
```

`$random_loose_item$`은 태그된 loose item 중 대상을 고르는 표현입니다. 임의의 상자 모두가 자동 후보가 되는 것은 아닙니다. `GoToResponse`는 반응 대상 위치로 이동하는 명령이고, `nearest`는 그 사건에 가장 가까운 actor를 선택합니다. 이 설정의 actor는 한 명이므로 선택 대상도 한 명입니다.

### 실행 결과 확인하기

- 사건 로그에서 `shelf_topple`의 시간과 대상 물체를 찾습니다.
- 해당 물체가 실제로 움직였는지 화면과 RGB를 함께 봅니다.
- actor가 사건 뒤 이동하고 `LookAround 2`를 수행하는지 확인합니다. 거리가 멀면 10초 안에 반응이 끝나지 않을 수 있습니다.
- `capture`의 객체 정보에서 전도된 물체의 `incident_toppled_item` class를 확인합니다.

기본 writer는 RGB·카메라 정보·tight bbox를 켭니다. semantic filter에 화재·누출 class가 포함되어 있어도 해당 사건이나 segmentation 출력이 자동 활성화되는 것은 아닙니다.

## 2. IRI 단독 설정에서 사건 세 가지 비교하기

사람 반응 없이 사건 자체를 살펴보려면 **Event Config File**을 사용합니다. `incident_config.yaml`은 `isaacsim.replicator.incident` 아래에 별도 설정을 둡니다.

1. 태그된 창고를 열고 **Tools > Action and Event Data Generation > Event Scene Tagger**에서 태그를 확인합니다.
2. 일반 창고를 사용한다면 선반 상자에 **Tag loose items: NavMesh**를 적용하세요. NavMesh 가장자리 방향은 전도 방향을 정하는 데 쓰입니다. 화재 대상은 **Tag flammable items**에서, 누출 대상은 **Tag leakable items: Item**, 받는 바닥은 **Tag spillable areas: Floor**로 태그합니다. 화재에는 보이는 Mesh를 가진 물체를 선택하세요.
3. 태그를 새 USD에 저장합니다. `incident_config.yaml`을 복사해 `report_dir`의 `REPLACE_WITH_ABSOLUTE_OUTPUT_DIRECTORY`를 새 절대 경로로 바꾸세요.
4. **Tools > Action and Event Data Generation > Event Config File**에서 복사본을 로드합니다. 처음에는 Fire·Spill을 제거하고 Topple만 남겨 **Set Up Events → Record Events**로 실행합니다.
5. 전도를 확인한 뒤 새 기록에서 세 사건을 복원하고 15초 이상 기록합니다. **Stop Record**로 끝내고 로그와 화면을 비교하세요.

### 전도 방향을 비교하는 경우

Scene Tagger의 **RandomDir**은 무작위 방향을, **ClosestWaypoint**는 가까운 waypoint 쪽을 전도 방향으로 사용합니다. 후자는 **AddWaypointPrim**으로 통로 쪽에 waypoint를 만든 뒤 위치와 크기를 맞추고 태그해야 합니다. waypoint는 필요하면 숨길 수 있습니다. 새 USD 복사본에서 한 방향 방식씩 비교하고, **UntagLooseItems**가 선택 Prim의 하위 태그까지 지운다는 점도 확인하세요.

### 설정에서 볼 부분

| 사건 | 시작 시간 | 관찰할 조건 |
|---|---|---|
| `shelf_topple` | 3초 | loose item과 반경 1.5 m의 주변 대상 |
| `small_fire` | 6초 | flammable 태그 물체에서 화재 시작 |
| `floor_spill` | 9초 | leakable 태그 물체에서 5초 동안 누출 |

이 파일의 전도 시작은 **3초**입니다. 앞의 IRA 설정의 1초와 혼동하지 마세요. 누출의 `target_size: 1.5`와 `leak_duration: 5.0`도 각각 크기와 시간으로 다른 역할을 합니다. 액체를 받을 바닥 태그가 없으면 기대한 선반이나 바닥 대신 z=0에 효과가 놓일 수 있습니다.

화재 대상은 `incident_flaming_item`, 누출 대상은 `incident_leaking_item`, 액체 면은 `incident_liquid_spill` class를 가집니다. RGB에 불꽃이 보이는 것과 불꽃 자체의 개별 마스크가 저장되는 것은 별개입니다. 필요한 주석을 실제 writer 출력에서 확인하세요.

## 3. 사건과 반응의 인과관계 정리

```text
물체 태그 → 사건의 대상 후보
시간 trigger → 사건 발생 → 이름·시간·대상 로그
사건 이름에 연결된 response → actor 선택 → 이동·둘러보기
카메라 + writer → 해당 장면의 영상·객체 주석
```

사건 로그는 “무엇이 언제 일어났는가”를, actor의 행동은 “누가 어떻게 반응했는가”를 보여 줍니다. 상자가 쓰러졌다고 사람 반응도 확인한 것은 아니며, 사람이 이동했다고 지정한 사건이 실제로 발생했다고 단정할 수도 없습니다. 사건 이름과 시점을 연결해 읽으세요.

## 4. 간단한 확인 실험

IRA 실행의 `topple_nearby_radius`만 1.5 m에서 0.2 m로 줄여 보세요. 같은 Scene·seed·actor 명령을 사용하고 새 출력으로 기록합니다.

- 로그에서 선택한 중심 대상이 같은지 먼저 확인합니다.
- 함께 전도되는 이웃 물체 수가 줄어드는지 화면과 주석에서 봅니다.
- 주변에 다른 loose item이 없었다면 차이가 없을 수 있습니다. 반경 값만 보고 항상 다른 결과를 기대하지 않습니다.

## 실행할 때 막히면

- **시간이 지나도 사건이 없음**: IRI 활성화, Set Up Events 또는 IRA Setup, 대상 물체의 사건 태그를 확인하세요.
- **상자는 쓰러지는데 사람이 반응하지 않음**: `physical_event`의 `event_name`이 `shelf_topple`과 같은지 확인하고 이동할 NavMesh가 있는지 봅니다.
- **화재·누출이 없음**: 기본 IRA 설정에는 전도만 있습니다. IRI 단독 설정과 해당 물체 태그를 별도로 적용하세요.
- **로그 저장 경로 오류**: 독립 IRI 파일의 `report_dir` 자리표시자를 실제 절대 경로로 바꾸세요. `prepare.py`는 이 파일을 수정하지 않습니다.
- **카메라에 사건이 보이지 않음**: 사건 발생 시 카메라는 자동 이동하지 않습니다. 해당 대상이 보이는 위치로 직접 옮기세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Physical Space Event Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html)에 대응합니다. 로컬 `lesson.json`은 `event.event_list`와 `physical_event` 반응을 사용해 전도 하나를 연결합니다. 별도 IRI 파일은 사건 종류를 비교하기 위한 설정입니다.

`tutorial.json`은 `not_run`입니다. 설정 생성과 실제 전도·화재·액체 효과·actor 반응은 다른 확인 단계이며 이 문서의 관찰 항목은 실행 시 확인할 기준입니다.
