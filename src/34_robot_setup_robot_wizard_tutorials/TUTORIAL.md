# 34. Robot Wizard로 도형을 세 링크 로봇으로 만들기

## 이번에 배우는 것

**도형을 함께 움직일 링크로 묶고, 고정·직선·회전 관절을 연결해 움직이는 로봇을 만듭니다.**

여러 도형이 나란히 있다고 해서 로봇이 되는 것은 아닙니다. 어떤 도형이 한 덩어리로 움직이는지, 덩어리 사이에 어떤 운동을 허용하는지 정해야 합니다. 이번에는 Robot Wizard에서 세 링크를 만들고, 두 종류의 drive 목표를 비교합니다.

| 구성 | 연결 | 관찰할 동작 |
|---|---|---|
| `fixed_joint` | world → link1 | 첫 링크가 공간에 고정 |
| `slider_joint` | link1 → link2 | X축 직선 이동, 위치 목표 사용 |
| `rotate_joint` | link2 → link3 | Z축 회전, 속도 목표 사용 |

`run.py`는 공식 원시 도형을 열고 편집할 파일을 준비합니다. 링크·관절 제작과 Play는 아래 GUI 단계에서 직접 수행합니다.

## 1. 원시 도형을 로컬 편집 장면으로 열기

Isaac Sim 5.1, 지원 RTX GPU와 GUI 화면이 필요합니다. 5.1 자산 루트의 `/Isaac/Samples/Rigging/RobotWizard/raw_blocks.usd`를 읽을 수 있어야 합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/34_robot_setup_robot_wizard_tutorials/run.py --output src/34_robot_setup_robot_wizard_tutorials/output/first
```

`~/isaacsim`은 설치 위치입니다. `first`는 새 폴더여야 하며 이미 있으면 다른 이름을 사용하세요. 실행 후 창은 계속 열려 있습니다. GUI 실습을 마치고 작업 파일을 저장한 뒤 창을 닫습니다.

### 코드에서 볼 부분

실행기는 원본 파일을 직접 편집하는 대신 새 `stage.usda`를 만들고 source를 하위 레이어로 연결합니다.

```python
layer = Sdf.Layer.CreateNew(str(output / "stage.usda"))
layer.subLayerPaths = [source]
```

이 파일을 열면 원본의 도형을 보면서 로컬에 편집 내용을 작성할 수 있습니다. 로컬 에셋을 쓰려면 `--asset /실제/경로/raw_blocks.usd`를 지정할 수 있습니다. 이미 저장한 결과를 이어 볼 때는 `--stage`를 사용하며, 이때도 새 출력 레이어가 이전 파일을 참조합니다.

### 실행 결과 확인하기

`output/first/`에서 다음을 확인하세요.

| 파일 | 의미 |
|---|---|
| `stage.usda` | 시작할 때 만든 로컬 편집 레이어 |
| `initial_inventory.json` | GUI 편집 전 source·단위·위쪽 축·강체·관절·articulation root 목록 |

초기 보고서에 joint가 적거나 없다는 이유로 실패라고 판단하지 마세요. 아직 Wizard로 관절을 만들기 전입니다. **이 보고서는 GUI 작업 후 자동 갱신되지 않습니다.** 완료 결과는 이후 Wizard가 저장한 로봇 파일과 현재 Stage에서 확인합니다.

## 2. Wizard에서 링크·관절·drive 만들기

**Window > Extensions**에서 `isaacsim.robot_setup.wizard`를 활성화하고 **Window > Robot Wizard**를 여세요. 메뉴가 보이지 않으면 확장 검색 필터를 확인합니다.

### 설정에서 볼 부분

먼저 도형을 함께 움직일 단위로 나눕니다.

1. **Configure a Robot on Stage**를 선택하고 Robot Type은 **custom**, 이름은 `wizard_robot`으로 정합니다. Robot Parent Xform은 Stage의 `/World`를 선택하고 **Prepare Files**로 넘어갑니다.
2. Robot Root Folder는 이 튜토리얼 폴더 안의 새 `output/wizard_robot`를 선택합니다. **Save a Copy in Robot Root Folder**를 켜고 Next를 누릅니다. 실제 저장 위치를 기록해 두세요.
3. **Robot Hierarchy**의 New Links Structure에 `wizard_robot/link3`를 추가합니다. Cube·Cone은 link1, Cylinder는 link2, Cylinder_01·Cube_01은 link3로 옮기고 **Add Colliders**를 누릅니다.
4. 새 Stage의 `meshes`, `visuals`, `colliders` Scope를 살펴봅니다. 자료용 원본이 겹쳐 보이면 세 Scope의 visibility를 숨깁니다. 실제 링크의 위치를 원점으로 옮겨 해결하지 마세요.
5. 이 기본 도형에는 기본 collider 구성을 사용하고 **Add Joints & Drives**로 넘어갑니다.

링크는 여러 시각 형상을 포함할 수 있는 하나의 강체입니다. 반면 Scope는 파일과 장면 정보를 정리하는 노드입니다. `meshes`는 원시 기하, `visuals`는 표시용 참조, `colliders`는 충돌용 참조를 정리합니다. 이 자료용 계층과 실제 링크의 배치를 구분하세요.

이제 **Create New Joint**로 다음 세 관절을 만듭니다. 앞 두 개는 Create, 마지막은 Create & Close를 사용합니다.

| 이름 | 종류·축 | Parent → Child | Drive |
|---|---|---|---|
| `fixed_joint` | Fixed | 비움(world) → link1 | 없음 |
| `slider_joint` | Prismatic / X | link1 → link2 | force |
| `rotate_joint` | Revolute / Z | link2 → link3 | force |

관절은 **가능한 운동**을 정하고 drive는 **그 운동을 어느 목표로 이끌지** 정합니다. slider를 만들기만 하면 위치 1로 이동하는 명령까지 자동으로 생기는 것은 아닙니다.

- `slider_joint`: 범위 0~3, target position=1, stiffness=100000, damping=20000으로 설정합니다. Prismatic 값은 Stage 길이 단위를 따르므로 초기 보고서의 `meters_per_unit`도 함께 확인하세요.
- `rotate_joint`: **Joint Range is Limited**를 끄고 target velocity=100, stiffness=0으로 설정합니다. USD 회전 drive의 속도 값은 degree/s입니다. 속도 오차에 반응할 수 있도록 damping이 양수인지 확인하세요.

회전 drive의 stiffness를 0으로 두는 이유는 특정 각도로 돌아가려는 위치 제어 성분을 없애기 위해서입니다. damping까지 0이면 속도 목표에 반응할 작용도 없어집니다. slider는 위치에 정착하지만 rotate는 각도 제한 없이 속도를 유지하도록 구성했습니다.

### 실행 결과 확인하기

1. **Save Robot**에서 articulation root로 `fixed_joint`를 선택하고 light와 Physics Scene을 추가합니다. base가 world에 고정되므로 ground는 선택 사항입니다.
2. Stage의 Joints 폴더에 세 관절이 있는지 확인하고, Property에서 body0·body1이 표의 링크를 가리키는지 확인하세요.
3. **Play**를 누릅니다. link1은 고정된 채 link2는 slider의 목표로 이동하고 link3는 계속 회전하는지 관찰합니다.
4. **Stop**한 뒤 파일을 저장합니다. Layers에서 base와 physics 구성을 확인하고, Wizard가 선택한 로컬 저장 파일에 편집이 기록되었는지 확인하세요.

Wizard는 작업 중 새 Stage와 구성 파일을 엽니다. 처음의 `output/first/stage.usda`만 보관했다고 최종 로봇까지 저장했다고 가정하지 마세요. Robot Root Folder의 최상위 로봇 USD와 참조된 구성 파일을 함께 확인해야 합니다.

## 3. 로봇 제작 과정 정리

```text
원시 도형 → 함께 움직일 링크로 묶기 → 충돌 형상 지정
    → 링크 사이 관절 연결 → drive 목표 설정
    → articulation root 지정 → 저장 → Play로 운동 확인
```

기하와 링크 구조는 로봇의 기본 구성을 설명합니다. 강체·충돌·관절·drive 설정은 물리 동작을 설명합니다. Wizard가 base와 physics 레이어를 나누는 이유도 이 두 종류의 정보를 구분해 관리하기 위해서입니다.

## 4. 간단한 확인 실험

Stop 상태에서 `slider_joint`의 target position만 1에서 2로 바꾼 뒤 다시 Play하세요. 범위 0~3, stiffness·damping과 rotate 설정은 유지합니다.

link2의 정착 위치는 slider 좌표에서 달라지고, 그 자식 link3도 함께 이동해야 합니다. rotate의 속도 목표 100 degree/s는 그대로입니다. 회전하는 링크가 다른 위치에 보이는 현상을 회전축 설정이 바뀐 것으로 오해하지 말고, 부모 링크 이동과 자식 회전을 나눠 관찰하세요.

## 실행할 때 막히면

- **원시 도형을 열 수 없음**: 5.1 자산 루트와 `raw_blocks.usd` 경로를 확인하세요. 로컬 자산이 있다면 `--asset`으로 지정할 수 있습니다.
- **도형이 원점에 중복되어 보임**: 자료용 `meshes`·`visuals`·`colliders` Scope를 확인하고 숨기세요. 실제 링크 transform은 유지합니다.
- **회전 관절이 움직이지 않음**: Play 상태, body 연결, 양수 damping, stiffness=0, 각도 제한 해제를 확인하세요.
- **로봇 전체가 떨어짐**: fixed_joint의 parent가 world이고 child가 link1인지, articulation root를 올바르게 지정했는지 확인하세요.
- **창이 제작 중 닫힘**: GUI 실습에는 양수 `--steps`를 생략하세요. Headless는 양수 `--steps`가 필요하며 GUI 제작을 수행할 수 없습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Robot Wizard Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/robot_wizard_tutorials.html)에 대응합니다. 공식 도형과 세 관절 구성을 사용하며, 로컬 실행기는 원본을 참조하는 편집 레이어와 초기 구조 보고서를 준비합니다.

`tutorial.json`의 검증 상태는 `not_run`입니다. 위 절차는 실행기와 공식 5.1 구성에 따른 확인 기준입니다. Wizard 제작·저장·물리 운동을 포함한 실제 GUI 완료는 아직 검증하지 않았습니다.
