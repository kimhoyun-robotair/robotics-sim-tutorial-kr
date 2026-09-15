# 95. 창고 외곽을 그리고 벽과 기둥 배치 바꾸기

## 이번에 배우는 것

**Warehouse Creator로 4×3 tile 외곽을 만들고, 벽 style과 기둥 편집의 Confirm·Cancel이 어떤 결과를 남기는지 확인합니다.**

모듈형 창고는 정해진 크기의 벽·모서리·바닥 부품을 이어서 만듭니다. 외곽을 자유로운 meter 좌표로 그리는 대신 부품의 tile 격자에 맞추면 연결되는 구조를 만들기 쉽습니다. 여기서는 작은 직사각형을 기준으로 생성과 편집을 이어서 수행합니다.

| 구성 | 역할 | 이 실습의 기준 |
|---|---|---|
| `omni.warehouse_creator` | 공식 생성·편집 UI | Tools의 Modular Warehouse Creator |
| Dataset Source | 조립할 모듈 자산 위치 | Modular_Warehouse의 Props 폴더 |
| `floor_plan.json` | 사람이 따라 그릴 로컬 설계도 | 4×3 tile, 반시계 방향 |
| wall style | 같은 종류 부품의 형태 선택 | 직선 벽 하나만 변경 |
| column editor | 여러 부품에 걸친 기둥 배치 조정 | 한 기둥 Confirm, Flip All 후 Cancel |

`floor_plan.json`은 자동 생성기가 읽는 실행 입력이 아닙니다. 이 폴더에는 JSON을 불러와 창고를 만드는 Python 코드가 없으며, 아래 단계에서 사용자가 GUI로 외곽을 그립니다.

## 1. 설계도를 따라 창고 외곽 만들기

Isaac Sim 5.1 GUI, 지원 NVIDIA RTX GPU·드라이버, Warehouse Creator와 모듈 자산 접근 환경이 필요합니다. 저장소 루트에서 앱을 시작하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. 새 Stage를 준비합니다.
2. **Window > Extensions**에서 Warehouse Creator를 검색하고 `omni.warehouse_creator`를 설치·활성화합니다. 5.1 환경과 맞는 확장을 사용합니다.
3. **Tools > Modular Warehouse Creator**를 엽니다.
4. Dataset Source에 원격 모듈 자산 또는 다운로드한 `[Isaac Sim Assets]/Isaac/Environments/Modular_Warehouse/Props` 폴더를 선택합니다.
5. **Build Warehouse**를 누릅니다. 이때 나타나는 curve draw dialog는 따로 조작하지 마세요.
6. Viewport의 격자에 맞추어 아래 순서로 외곽을 그립니다.

### 설정에서 볼 부분

로컬 `floor_plan.json`의 핵심은 다음 좌표입니다.

```json
"vertices_tiles": [
  [0, 0],
  [4, 0],
  [4, 3],
  [0, 3],
  [0, 0]
]
```

`(0,0)`에서 오른쪽으로 4 tile, 위로 3 tile, 왼쪽으로 4 tile, 아래로 3 tile을 이동하는 직사각형입니다. 마지막 점은 시작점과 같아서 닫힌 외곽을 나타냅니다.

```text
(0,3) ←──────── (4,3)
  │                ↑
  │                │
  ↓                │
(0,0) ────────→ (4,0)
```

위 좌표는 **tile 단위의 설계 기준**입니다. GUI는 선택한 dataset의 모듈 크기에 맞춰 위치를 정렬합니다. 한 tile의 한 변이 s m인 정사각 격자라면 기준 외곽 길이는 4s와 3s m입니다. 4×3을 곧바로 4 m×3 m로 읽지 마세요.

마지막 클릭을 시작점 근처에 두어 닫거나, 마지막 점이 시작점과 정렬된 상태에서 Finish를 누릅니다. `crossing_edges: false`는 선이 서로 교차하지 않는 설계라는 뜻입니다. 생성기가 JSON 값을 검사하는 것이 아니므로 실제로 그린 선도 교차하지 않아야 합니다.

### 실행 결과 확인하기

외곽이 닫힌 직사각형이 되고 내부 tile이 채워지는지 확인합니다. 벽만 일부 생겼다면 완료된 창고로 판단하지 마세요. 시작점을 닫았는지와 자산 로딩이 끝났는지 확인해야 합니다.

Stage에서 창고 구조를 묶는 floor plan prim을 찾아두세요. 다음 절의 기둥 편집은 그 prim을 선택한 상태에서 시작합니다.

## 2. 벽 style과 기둥 배치 편집하기

### 설정에서 볼 부분

먼저 벽 하나의 용도를 바꿉니다.

1. Viewport toolbar를 우클릭하여 **Select Mode > Component**로 바꿉니다.
2. 직선 벽 block 하나를 선택합니다.
3. Property의 style에서 dataset이 제공하는 다른 형태를 선택합니다. 예를 들어 loading dock이나 access 형태를 사용합니다.
4. 선택한 벽만 바뀌고 외곽은 유지되는지 확인합니다.

USD의 **variant**는 같은 부품에 준비된 여러 구성을 선택하는 방식입니다. 직선 벽, 바깥 모서리, 안쪽 모서리와 중앙 부품은 종류가 다르므로 가능한 style도 다릅니다. 여러 block을 선택하면 같은 종류의 선택된 block들에 style이 함께 적용될 수 있습니다. 처음에는 한 개만 고르세요.

다음으로 기둥을 편집합니다.

1. floor plan prim을 선택하고 **Edit Column Placement**를 누릅니다.
2. 천장과 세부 요소가 숨겨진 상태에서 내부 기둥 하나를 클릭합니다.
3. disabled 미리보기인 **반투명 녹색**을 확인합니다.
4. **Confirm**을 눌러 배치를 확정합니다.
5. 다시 기둥 편집 모드로 들어가 **Flip All**을 누릅니다.
6. 이번에는 **Cancel**을 누릅니다.

다시 편집 모드에 들어가 클릭·드래그로 여러 기둥을 선택하거나 전체 Enable/Disable 버튼도 비교할 수 있습니다. 미리보기를 관찰한 뒤 Cancel을 누르면 이번 편집을 시작하기 전의 배치가 유지됩니다.

왜 기둥 메시를 바로 지우지 않을까요? 각 모듈의 안쪽 모서리에 기둥의 일부가 들어 있고, 인접 모듈들의 부분이 모여 기둥 하나처럼 보이기 때문입니다. 전용 편집기는 이 연결을 함께 다룹니다.

### 실행 결과 확인하기

| 작업 | 편집 중 모습 | 편집 모드를 나온 뒤 |
|---|---|---|
| 기둥 하나 끄기 → Confirm | 해당 기둥이 반투명 녹색 | 바뀐 기둥 배치 유지 |
| Flip All → Cancel | 모든 기둥 상태가 뒤집힌 미리보기 | 두 번째 편집 진입 전 상태로 복귀 |

**Cancel은 창고를 처음 만든 상태로 되돌리는 버튼이 아닙니다.** 앞에서 Confirm한 변경은 남고, 이번 편집에서만 바꾼 내용을 취소합니다.

기둥 배치를 확인한 뒤 저장소 루트의 별도 터미널에서 출력 폴더를 만드세요.

```bash
mkdir -p src/95_digital_twin_ext_omni_warehouse_creator/output
realpath src/95_digital_twin_ext_omni_warehouse_creator/output
```

**File > Save As**로 위 폴더의 `warehouse.usd`에 저장합니다. 다른 Stage를 열었다가 저장 파일을 다시 열어 변경한 wall style과 확정한 기둥 상태가 유지되는지 확인하세요. 앱 종료는 관찰과 저장을 마친 뒤 직접 수행합니다.

## 3. 설계·미리보기·저장의 차이 정리

```text
floor_plan.json의 tile 설계 → 사람이 외곽 클릭 → 창고 모듈 생성
                                                       ↓
벽 variant 선택 + 기둥 편집 미리보기
                   ├─ Confirm → 현재 Stage에 변경 유지
                   └─ Cancel  → 편집 시작 시 상태로 복귀
                                                       ↓
                                           Save As → USD 파일
```

**생성, 편집 확정, 파일 저장은 별도의 단계입니다.** Confirm으로 모양을 정해도 파일에 보관하려면 Save As가 필요합니다.

저장한 창고는 dataset의 자산을 참조할 수 있습니다. USD 하나를 옮겼다고 모든 모듈과 텍스처가 함께 복사되는 것은 아니므로 다시 열 때도 reference 경로가 유효해야 합니다. 이 실습은 창고 구조와 편집 상태를 다루며 로봇 주행이나 충돌 품질을 검사하지 않습니다.

## 4. 간단한 확인 실험

외곽과 기둥 배치를 그대로 둔 채 **같은 직선 벽 한 개의 style만** 두 번 바꿔 보세요. 각 선택의 이름과 벽의 변화를 기록합니다.

관찰할 것은 벽의 기능적 모양이 달라지는지, 벽이 차지한 tile 위치와 나머지 구조는 유지되는지입니다. 여러 벽이 함께 바뀌면 다중 선택 상태를 확인하세요. 실험 후 사용할 style 하나를 정하고 저장하면 파일을 다시 열어 선택이 보존되는지도 확인할 수 있습니다.

## 실행할 때 막히면

- **Warehouse Creator가 검색되지 않음:** 5.1 환경의 extension registry 연결과 설치 상태를 확인하세요.
- **외곽은 그렸지만 내부가 채워지지 않음:** 시작점으로 닫았는지, 마지막 점이 Finish로 닫을 수 있는 위치인지 확인하세요.
- **마지막 점을 찍기 어려움:** 시작점 주변을 확대하세요. 너무 가까운 점을 새로 추가하지 못하도록 UI가 제한할 수 있습니다.
- **벽이나 바닥이 비어 있음:** Dataset Source가 Props 폴더인지, 참조 자산 다운로드가 완료되었는지 확인하세요.
- **기둥 편집 버튼이 원하는 대상을 찾지 못함:** 개별 벽 대신 floor plan prim을 선택하세요.
- **Cancel 후 처음 상태로 돌아오지 않음:** 직전 Confirm 상태가 이번 편집의 시작 상태입니다. 취소 범위를 앞 표와 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Warehouse Creator Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_omni_warehouse_creator.html)에 대응합니다. 로컬 JSON은 작은 직사각형과 관찰 순서를 정한 학습용 설계도입니다.

이번 개정에서는 JSON 좌표와 공식 GUI의 생성·style·기둥 편집 절차를 대조했습니다. 확장 설치, dataset 로딩, 창고 생성·재열기는 실행하지 않았으며 `tutorial.json`의 검증 상태는 `not_run`입니다.
