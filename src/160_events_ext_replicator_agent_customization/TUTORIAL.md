# 160. 직접 만든 방에서 사람이 움직이게 하기

## 이번에 배우는 것

**로컬 USD 방에 이동 영역을 만들고, 환경·캐릭터·애니메이션을 IRA에 연결할 때 맞춰야 할 조건을 이해합니다.**

방의 메시가 보인다고 사람이 그 안에서 길을 찾을 수 있는 것은 아닙니다. 방에는 실제 크기와 방향이 필요하고, 사람에게는 이동 가능한 바닥 영역이 필요합니다. 이번에는 단순한 바닥과 상자로 이 조건을 확인한 뒤 사용자 캐릭터와 애니메이션으로 확장합니다.

| 파일 | 포함한 내용 | 별도로 준비할 내용 |
|---|---|---|
| `custom_room.usda` | 바닥, 중앙 상자, 조명 | NavMesh |
| `lesson.json` | 로컬 방과 사람 한 명의 설정 | 실제 5.1 사람 자산 접근 |
| `prepare.py` | 실행 설정과 기본 명령 생성 | Bake·애니메이션 변환 |
| `retarget_animation.py` | 설치본 retarget 명령 호출 | 원본·대상 skeleton과 관절 매핑 |

기본 명령은 `Character_01 LookAround 3`입니다. 먼저 방 안에서 사람의 크기와 방향을 확인한 뒤 GoTo를 추가합니다.

## 1. 로컬 방에 NavMesh 만들기

Isaac Sim 5.1과 RTX GPU가 필요합니다. 방은 이 폴더에 있지만 사람은 5.1 Assets의 `/Isaac/People/Characters/`에서 불러옵니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화하고 필요한 재시작을 마칩니다.
2. **File > Open**으로 `src/160_events_ext_replicator_agent_customization/custom_room.usda`를 엽니다.
3. 바닥과 상자를 확인한 뒤 **Create > Navigation > NavMesh Include Volume**을 추가합니다. 중심 `(0,0,1)`, scale `(6,6,2)` 정도로 방의 바닥을 덮도록 조절하세요.
4. **Window > Navigation > NavMesh**에서 Bake하고 이동 영역을 시각화합니다. 바닥 위 영역이 생기고 중앙 상자를 피하는지 확인합니다.
5. 원본을 남겨 두고 `src/160_events_ext_replicator_agent_customization/output/room_nav.usd`로 **Save As**합니다. 저장 폴더가 없으면 먼저 만드세요.

### 설정에서 볼 부분

USD의 단위와 형상은 다음처럼 맞춰져 있습니다.

```text
metersPerUnit = 1, upAxis = Z
Floor:   (-6,-6,0)에서 (6,6,0)까지 → 12 × 12 m
Obstacle: size 2, scale (1,0.5,1)   → 2 × 1 × 2 m
Obstacle 중심: (0,0,1)             → 밑면이 z=0에 놓임
```

바닥 메시와 상자는 환경의 모양이고, Bake한 NavMesh는 사람의 이동 영역입니다. 경로 탐색에 쓸 수 있는 영역을 화면으로 확인해야 합니다. Include Volume을 줄여도 큰 바닥 폴리곤과 교차하는 방식에 따라 기대보다 넓은 영역이 포함될 수 있습니다.

이제 저장한 장면의 **실제 절대 경로**를 넣어 설정을 만듭니다.

```bash
python3 src/160_events_ext_replicator_agent_customization/prepare.py --scene /절대경로/저장소/src/160_events_ext_replicator_agent_customization/output/room_nav.usd --output src/160_events_ext_replicator_agent_customization/output/room_run --frames 300
```

`--scene`을 생략하면 NavMesh가 없는 원본 방을 참조합니다. `prepare.py`는 Bake를 대신하지 않습니다.

### 실행 결과 확인하기

**Tools > Action and Event Data Generation > Actor SDG**에서 `output/room_run/config.yaml`을 로드하고 **Set Up Simulation**을 누릅니다. 실제 사람 이름에 맞춰 명령을 저장한 뒤 생성하세요. 기본 LookAround에서는 사람의 위치가 유지되는지, 바닥과 사람의 크기가 자연스럽게 맞는지 봅니다.

300프레임은 30 FPS에서 10초입니다. 생성이 끝나도 GUI는 남습니다. 저장을 마친 후 직접 닫으세요.

## 2. 방의 길과 캐릭터의 관절 연결하기

### 설정에서 볼 부분

사람을 걷게 하려면 Character 명령에서 다음 두 목적지를 사용해 보세요. 실제 사람 이름과 NavMesh의 유효 영역을 먼저 확인합니다.

```text
Character_01 GoTo 4 4 0 _
Character_01 GoTo -4 -4 0 _
```

두 목적지 사이에는 중앙 상자가 있습니다. **Save Commands**한 뒤 새 생성에서 사람이 상자 내부를 가로질러 가는지, 이동 영역을 따라 우회하는지 관찰하세요. 전체 이동이 끝나지 않으면 프레임 수를 늘립니다. NavMesh의 명명된 영역을 따로 만든 경우 `spawn_area`는 시작 위치를, `navigation_area`는 목적지 선택을 제한합니다. 영역을 만들지 않았다면 빈 배열을 유지합니다.

외부 환경을 가져올 때는 미터 단위의 Z-up Stage에서 Content Browser의 USD를 끌어와 Xform reference로 넣고 전체 크기와 방향을 확인하세요. 비-USD 형식은 제작 도구의 USD export나 변환기로 먼저 변환합니다. 외부 환경을 배치한 뒤에는 그 장면에서 NavMesh를 다시 Bake하세요. `metersPerUnit` 숫자만 바꿔도 메시 좌표가 자동으로 1/100이 되는 것은 아닙니다. 사람을 옆에 세워 문 높이·바닥 크기를 비교하면 단위 오류를 찾기 쉽습니다.

캐릭터는 메시와 skeleton, 애니메이션을 함께 맞춰야 합니다. 메시 점만 줄이고 skeleton을 그대로 두면 관절 기준 자세와 피부 변형이 어긋납니다. 제작 도구에서 함께 미터 단위로 내보내는 방법부터 검토하세요. IRA의 사용자 캐릭터는 Z-up, 전방 -Y와 Biped 호환성을 확인하고 `characters/person_a/person_a.usd`처럼 하위 폴더에 둔 뒤 `character.asset_path`를 상위 폴더로 지정합니다.

### 코드에서 볼 부분

애니메이션 retarget은 원본의 관절 움직임을 대상 skeleton에 맞춰 옮기는 작업입니다. 한 Stage에 실제 source Skeleton, target NVIDIA Biped Skeleton, source SkelAnimation을 배치하세요. Animation Retargeting 도구에서 source·target 관절 매핑과 retarget pose를 먼저 맞춘 뒤 Script Editor에서 `retarget_animation.py`를 실행합니다. 이 함수에는 매핑을 새로 만드는 인수가 없으므로 준비하지 않은 두 skeleton의 이름을 전달하는 것만으로 대응 관절이 정해지지는 않습니다.

```python
retarget_animation('/World/Source/Skeleton', '/World/Biped/Skeleton',
                   '/World/Source/Walk', '/World/RetargetedWalk')
```

위 경로는 예시이며 열린 Stage의 실제 Prim으로 바꿉니다. 마지막 인수는 새 애니메이션을 넣을 부모 경로입니다. 함수는 두 Skeleton과 SkelAnimation의 타입을 검사하고 기존 출력 부모가 있으면 중단합니다. 실제 변환은 설치본의 `CreateRetargetAnimationsCommand`가 수행합니다.

### 실행 결과 확인하기

생성된 애니메이션을 target Biped에서 재생해 발 미끄러짐과 팔 꼬임을 봅니다. 파일 생성만으로 관절 매핑이 올바른지는 알 수 없습니다. 결과를 별도 애니메이션 USD로 저장하고 `CustomCommandName`, `CustomCommandTemplate`을 준비해 Custom Command Panel에 등록한 뒤 Setup을 다시 실행합니다.

방의 우회 보행, 사용자 캐릭터의 올바른 크기, retarget된 애니메이션의 관절 움직임은 각각 확인할 결과입니다. 제공된 폴더에는 사용자 skeleton이나 애니메이션 매핑 자체가 들어 있지 않습니다.

## 3. 환경과 애니메이션의 준비 조건 정리

```text
환경: 크기·축·조명 → NavMesh Bake → 시작 위치와 이동 경로
캐릭터: 메시·skeleton 일치 → Biped 호환 → actor 자산으로 로드
애니메이션: 원본 동작·관절 매핑 → retarget → 명령 등록 → 재Setup
```

방이 너무 작으면 경로 선택부터 잘못되고, 관절 매핑이 틀리면 유효한 경로를 따라가도 자세가 어색해집니다. 환경의 좌표 문제와 캐릭터의 관절 문제를 나누어 확인하면 어떤 자산을 수정해야 하는지 분명해집니다.

## 4. 간단한 확인 실험

NavMesh의 **agent radius만** 키워 Bake해 보세요. 원본과 다른 USD로 저장하고 같은 두 GoTo 목적지를 사용합니다.

- 중앙 상자 모서리와 이동 영역 사이의 여유가 늘어나는지 봅니다.
- 통로가 좁으면 이동 영역이 끊길 수도 있습니다.
- 실제 사람의 우회 경로와 Bake 결과를 함께 비교하세요. 상자 크기와 목적지는 유지합니다.

## 실행할 때 막히면

- **방은 열리는데 사람이 없음**: 로컬 방과 외부 사람 자산은 별개입니다. 5.1 사람 자산 접근과 `character.asset_path`를 확인하세요.
- **NavMesh가 없음**: 원본 방 대신 Bake한 `room_nav.usd`가 실행 설정에 지정됐는지 확인하세요.
- **사람이 걷지 않음**: 기본 명령은 LookAround입니다. GoTo를 저장했는지와 목적지가 같은 이동 영역에 있는지 확인하세요.
- **retarget의 타입 오류**: 메시나 SkelRoot 대신 실제 Skeleton·SkelAnimation Prim 경로를 전달하세요.
- **팔이 꼬이거나 발이 미끄러짐**: source/target 관절 매핑과 기준 자세, 단위 변환을 먼저 확인하세요. 명령 등록만 다시 해서는 해결되지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Customization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html)에 대응합니다. 로컬 방으로 환경 준비를 시작하고, 사용자 자산이 있는 경우 retarget까지 확장합니다.

`tutorial.json`은 `not_run`입니다. 방 USD와 설정 생성 도구가 제공되지만 NavMesh Bake, 실제 보행, 사용자 애니메이션 재생은 별도로 확인해야 합니다.
