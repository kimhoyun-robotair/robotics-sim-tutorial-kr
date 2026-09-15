# 96. 움직이지 않는 벨트가 상자를 운반하는 이유

## 이번에 배우는 것

**컨베이어의 표면 속도로 상자를 운반하고, 벨트의 물리 동작과 화면의 애니메이션을 구분합니다.**

컨베이어를 만들 때 벨트 모형 전체를 옆으로 이동시킬 필요는 없습니다. 제자리에 있는 충돌 표면에 속도를 주면, 그 위에 접촉한 물체가 이동합니다. 표면의 무늬가 흐르는 애니메이션은 이 운동을 눈으로 표현하는 별도 설정입니다.

이번에는 작은 벨트 하나로 접촉 운동을 확인한 뒤, Track Builder에서 여러 조각을 연결합니다.

| 구성 | 실제 파일 또는 위치 | 관찰할 역할 |
|---|---|---|
| 기본 장면 | `conveyor_lab.usda` | 벨트, 상자, 물리 장면과 조명 |
| 벨트 | `/World/Belt` | 길이 3 m인 충돌 표면 |
| 운반할 상자 | `/World/Parcel` | 한 변 0.2 m, 질량 0.5 kg인 강체 |
| Conveyor 그래프 | GUI에서 직접 생성 | 표면 속도와 애니메이션 설정 |
| Track Builder | 외부 Digital Twin 컨베이어 자산 사용 | 직선·회전 조각의 끝점 연결 |

**제공된 USDA에는 아직 Conveyor 그래프가 없습니다.** 파일을 열기만 했을 때 상자가 운반되지 않는 것은 정상입니다.

## 1. 작은 벨트에 표면 속도 주기

Isaac Sim 5.1과 지원 NVIDIA RTX GPU, GUI 세션이 필요합니다. 저장소 루트에서 다음 명령으로 앱을 시작하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
mkdir -p src/96_digital_twin_asset_gen_conveyor/output
~/isaacsim/isaac-sim.sh
```

`output/`은 아래에서 편집한 장면을 저장할 폴더입니다.

1. **File > Open**에서 `src/96_digital_twin_asset_gen_conveyor/conveyor_lab.usda`를 엽니다.
2. **Window > Extensions**에서 `isaacsim.asset.gen.conveyor.ui`를 검색하고 활성화합니다.
3. Stage에서 **`/World/Belt`**를 선택한 뒤 **Create > Isaac Sim > Warehouse Items > Conveyor**를 실행합니다.
4. Stage의 생성된 그래프 Prim을 우클릭해 **Open Graph**로 엽니다. Conveyor 노드의 대상과 방향을 아래 표에 맞추고, 그래프 Prim을 선택해 속도 변수를 `0.2`로 설정하세요.
5. **Play**를 누르고 상자가 벨트에 닿은 뒤 움직이는 모습을 관찰합니다. 상자가 끝에서 떨어지면 **Stop**으로 초기 배치로 돌아가세요.

### 설정에서 볼 부분

| 설정 | 실습 값 | 이 값이 필요한 이유 |
|---|---|---|
| `conveyorPrim` | `/World/Belt` | 접촉 속도를 줄 표면을 지정합니다. |
| `Direction` | `(1, 0, 0)` | 벨트의 로컬 +X 방향으로 운반합니다. |
| `Curved` | `false` | 직선 표면 속도를 사용합니다. |
| `Enabled` | `true` | 컨베이어 동작을 활성화합니다. |
| 속도 변수 → `Velocity` | `0.2` | 이 미터 단위 장면에서 0.2 m/s를 설정합니다. |

자동 생성 그래프는 속도 변수를 읽어 Conveyor 노드에 전달합니다. 연결된 `Velocity` 입력을 따로 고치기보다 **그래프의 속도 변수**를 바꾸세요. 여러 벨트를 묶을 때도 각 `read_speed`가 같은 변수를 읽도록 하면 한 값으로 속도를 맞출 수 있습니다.

USDA의 벨트 크기는 다음 두 값의 곱으로 정해집니다.

```usda
double size = 2
double3 xformOp:scale = (1.5, 0.3, 0.1)
double3 xformOp:translate = (0, 0, 0.1)
```

실제 크기는 `(3, 0.6, 0.2)` m이며 윗면 높이는 0.2 m입니다. 따라서 상자가 평평하게 얹히면 중심 높이는 약 0.3 m가 됩니다. 시작 중심 `(-1, 0, 0.6)`에서는 아직 공중에 있으므로, 낙하 중의 움직임으로 컨베이어 효과를 판단하지 마세요.

### 실행 결과 확인하기

- `/World/Belt`의 위치는 유지되고, 착지한 `/World/Parcel`의 X 위치가 증가하는지 봅니다.
- 상자가 벨트 위에 머무는 동안 비교합니다. 끝을 지난 뒤에는 이를 받칠 바닥이 없는 장면입니다.
- 단색 벨트에는 흐르는 무늬가 보이지 않습니다. **상자 이동이 물리 동작의 확인 기준**입니다.

무늬가 있는 자산으로 표시를 비교할 때는 Conveyor 노드의 `Animate Texture`를 켜고, `Animate Direction`으로 UV 방향을, `Animate Scale`로 물리 속도 대비 무늬 이동 비율을 조절합니다. 재질을 여러 조각이 공유하면 무늬 변경도 함께 적용될 수 있으므로 조각마다 다른 애니메이션이 필요할 때는 재질도 분리합니다.

편집 결과를 남기려면 **File > Save As**로 이 폴더의 새 `output/conveyor.usd`에 저장하세요. 원본 USDA는 다음 비교를 위한 초기 장면으로 남겨 둡니다.

## 2. Track Builder로 경로 연결하기

이번에는 외부 Digital Twin 컨베이어 자산이 필요합니다. 기본 Track Builder는 설정된 클라우드 자산 폴더에서 조각을 읽으므로 최초 사용 때 다운로드를 기다려야 할 수 있습니다. 작은 벨트 실습의 USDA와 Track Builder의 자산 묶음은 서로 다른 입력입니다.

1. 앞 장면을 저장한 뒤 **File > New**로 새 장면을 엽니다.
2. **Tools > Conveyor Track Builder**를 엽니다.
3. Style을 하나 선택하고 시작 조각을 넣습니다. 그 조각을 선택해 **Selected Endpoint**에서 비어 있는 출구를 고릅니다.
4. 직선 조각, 회전 조각, 끝 조각을 차례로 연결합니다. 필요한 경우 New Track의 입력 끝점이나 Mirror를 조절합니다.
5. 위에서 내려다보며 조각 사이의 틈과 진행 방향을 확인하고 `output/conveyor_track.usd`처럼 별도 이름으로 저장합니다.

### 설정에서 볼 부분

Builder가 조각을 정렬하려면 **어디가 입구이고 출구인지** 알아야 합니다. 자산의 USD에는 실제 형상이, metadata JSON의 `anchors`에는 연결할 끝점 경로가 들어갑니다. `conveyor_nodes`는 조각 안에서 속도를 적용할 Belt나 Rollers를 지정합니다.

사용자 자산을 넣을 때는 **Edit > Preferences > Conveyor Builder**에서 자산 폴더와 JSON 경로를 함께 바꿉니다. 설치본 `exts/isaacsim.asset.gen.conveyor.ui/data/track_types.json`을 구조 참고용으로 읽어 보세요. 자산 USD들은 지정한 폴더 바로 아래에 두고, 각각 defaultPrim을 지정해야 합니다. 기본 Prim의 이동·회전은 0, 입구는 원점, 진행 방향은 +X로 맞춥니다. JSON의 `anchors`에서 빈 문자열은 루트 입구, `/Anchorpoint` 같은 경로는 자식 끝점을 가리킵니다. 입구와 끝점의 축이 일관되어야 조각이 어긋나지 않고 연결됩니다.

곡선 조각의 `Curved=true`에서는 `Direction`이 회전축을 뜻합니다. 앞에서 쓴 직선의 `(1,0,0)`을 모든 곡선에 그대로 적용하지 마세요. 자산별 곡선 설정을 기준으로 읽는 편이 좋습니다.

## 3. 형상·접촉·표시의 역할 정리

```text
USD와 끝점 정보 → 벨트 경로의 모양과 연결 위치
Conveyor 속도   → 접촉한 상자의 이동
Texture 설정   → 벨트 무늬가 흐르는 모습
```

세 가지는 서로 다른 관찰값을 만듭니다. 조각이 잘 연결되었어도 상자가 운반되는지 확인해야 하며, 무늬가 움직여도 접촉 운동이 설정되었다고 단정할 수 없습니다.

## 4. 간단한 확인 실험

작은 벨트 장면에서 **속도 변수만 `0.2`에서 `-0.2`로** 바꿔 보세요. Direction과 상자의 시작 위치는 유지합니다.

상자가 접촉 중이라면 X 위치의 변화가 감소 방향으로 바뀌어야 합니다. 이미 벨트 끝을 지났다면 Stop 후 다시 시작하세요. 접촉과 마찰 때문에 상자 속도가 명령값으로 즉시 바뀌어야 하는 것은 아닙니다.

## 실행할 때 막히면

- **상자가 떨어진 뒤 움직이지 않음**: Conveyor 대상이 Parcel이 아니라 Belt인지, 속도 변수가 0이 아닌지, Enabled가 켜져 있는지 확인하세요.
- **벨트 자체가 낙하하거나 상자가 통과함**: 자동 생성 뒤 Belt의 강체·충돌 구성을 확인하세요. 그래프 생성 전후 장면을 구분해 보면 잘못 선택한 대상을 찾기 쉽습니다.
- **속도를 고쳐도 효과가 없음**: 노드 입력에 연결된 `read_speed`를 확인하고 원천 변수를 바꾸세요.
- **Track Builder 목록이 비거나 로딩이 멈춘 듯 보임**: Preferences의 Digital Twin 자산 경로에 접근할 수 있는지 확인하세요. 필요하면 준비된 로컬 자산 폴더를 지정합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Conveyor Belt Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor.html)에 대응합니다. 작은 접촉 장면은 로컬 학습용 입력이고, 컨베이어 그래프 생성과 Track Builder 조립은 공식 확장의 GUI에서 수행합니다.

위 상자 이동과 Track Builder 연결은 실제 실행에서 확인할 기준입니다. `tutorial.json`의 검증 상태는 `not_run`이며 GUI 운반·조립 성공을 기록한 자료는 없습니다.
