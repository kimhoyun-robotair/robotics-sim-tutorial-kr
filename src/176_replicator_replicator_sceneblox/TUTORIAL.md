# 176. 이웃 규칙을 지키면서 미로를 생성하기

## 이번에 배우는 것

**타일의 인접 규칙과 경계 제약으로 7×7 미로를 만들고, 통로 구조와 소품 확률을 나누어 해석합니다.**

무작위로 통로 타일을 놓으면 옆 칸과 길이 맞지 않을 수 있습니다. SceneBlox는 각 칸에 가능한 타일 후보를 두고, 선택한 타일과 연결될 수 없는 이웃 후보를 제거하며 장면을 만듭니다. 이 과정을 WFC(Wave Function Collapse) 방식으로 살펴봅니다.

| 파일 | 결정하는 내용 |
|---|---|
| `config/rules.yaml` | 타일 종류·회전 후보와 이웃 관계 |
| `config/constraints.yaml` | 모서리 고정, 막다른 길 개수, 경계 제한 |
| `config/generation.yaml` | 선택한 타일을 어떤 USD로 표현할지 |
| `hazards_corridors.yaml` | 통로에 놓을 콘의 개수·확률·배치 |
| `run.py` | 격자를 풀고 USD와 생성 기록을 저장하는 과정 |

이 공식 튜토리얼은 사용 중단된 예제입니다. 여기서는 **Isaac Sim 5.1**에 남아 있는 SceneBlox API를 사용하며 후속 버전의 호환을 전제하지 않습니다.

## 1. 먼저 7×7 미로 하나 만들기

Isaac Sim 5.1과 RTX GPU, `isaacsim.replicator.scene_blox` 확장을 준비하세요. 자산 루트의 `Isaac/Samples/Scene_Blox/Tutorial/`, 창고 소품과 `NVIDIA/Assets/Skies/Dynamic/CumulusHeavy.usd`를 읽을 수 있어야 합니다. YAML은 포함되어 있지만 타일 USD와 소품 자산은 별도입니다.

저장소 루트에서 실행합니다.

```bash
~/isaacsim/python.sh src/176_replicator_replicator_sceneblox/run.py \
  --rows 7 --cols 7 --seed 42 \
  --output src/176_replicator_replicator_sceneblox/output/seed42
```

풀이와 저장 후 마지막 장면이 창에 남습니다. 직접 닫거나 `--steps 120`으로 저장 후 GUI 업데이트를 제한할 수 있습니다. `--headless`는 장면 생성·저장을 마친 뒤 종료합니다. `--display`는 별도 matplotlib 풀이 화면을 보여 주므로 `--headless`와 함께 사용할 수 없습니다.

출력 폴더는 새 경로를 사용하세요. `--variants`가 생성할 장면 수이고 `--steps`는 관찰 시간입니다. 창을 오래 열어 두어도 미로가 계속 재생성되는 것은 아닙니다.

### 코드에서 볼 부분

```python
tiles, weights = tile_loader(str(cfg / "rules.yaml"))
superposition = TileSuperposition(tiles, weights)
constraints = GridConstraints.from_yaml(str(cfg / "constraints.yaml"), args.rows, args.cols)
grid = Grid(args.rows, args.cols, superposition)
```

`superposition`은 아직 선택되지 않은 후보 집합입니다. `Grid.solve()`가 가능한 후보 중 하나를 선택하고 그 선택을 이웃에 전파합니다. 모순이 생겨 한 칸에 후보가 남지 않으면 다른 선택을 시도합니다. 실행기는 기본 최대 20회까지 풀이를 시도하고, 성공해야 USD 생성 단계로 넘어갑니다.

격자를 푸는 것과 USD를 만드는 것도 다른 단계입니다. `SceneGenerator.generate_scene()`이 최종 격자에 타일 reference와 소품을 배치합니다. 기본 `World(stage_units_in_meters=1.0)`과 `tile_size: 5.0`이므로 타일 한 변은 5 m 기준입니다.

### 실행 결과 확인하기

`output/seed42/generation.json`을 열고 다음을 확인하세요.

| 항목 | 기본 실행에서 의미 |
|---|---|
| `variant` | 첫 장면은 0입니다. |
| `rows`, `cols` | 각각 7입니다. |
| `attempts` | 일관된 격자를 얻기까지 시도한 횟수입니다. |
| `usd` | 실제 저장된 `generated_0.usd` 경로입니다. |

GUI에서는 `/World/tile_0_0`과 `/World/tile_6_6`을 선택하세요. 두 칸은 corridor 회전 0으로 제한되어 있습니다. 전체 dead_end가 4개 이하이고 경계에 cross·dead_end가 없는지 살펴봅니다. 저장 파일이 열려도 자산 reference가 실패하면 빈 타일처럼 보일 수 있으므로 실제 형상까지 확인해야 합니다.

## 2. 타일 규칙과 소품 확률 읽기

### 설정에서 볼 부분

`constraints.yaml`의 첫 두 규칙은 한 칸의 종류와 회전을 따로 제한합니다.

```yaml
- type: restrict_type
  identifiers: ["corridor"]
  area:
    rows: [[0, 0]]
    cols: [[0, 0]]
- type: restrict_rotation
  identifier: ["corridor"]
  rotations: [0]
  area:
    rows: [[0, 0]]
    cols: [[0, 0]]
```

구간 양 끝을 포함하므로 `[0,0]`은 첫 번째 칸 하나입니다. `[-1,-1]`은 마지막 칸을 뜻합니다. 회전 값 0/1/2/3은 반시계 90도 단위입니다. 인접 규칙은 기본적으로 현재 타일 오른쪽 이웃을 기준으로 정의하고 그 쌍을 회전시켜 다른 방향에도 적용합니다.

이웃 규칙이 맞는다고 미로 전체가 출발점에서 도착점까지 연결된다는 보장은 없습니다. **국소적인 연결 조건과 전체 경로 존재는 별도 속성**이므로 실제 통로를 따라가며 확인해야 합니다.

소품 설정은 이미 선택된 타일에 적용됩니다. `hazards_corridors.yaml`을 보세요.

```yaml
spawn_proba: 0.33
spawn_count: 3
```

콘 후보 세 개 각각의 생성 여부를 확률 0.33으로 정합니다. 그래서 통로마다 콘이 반드시 세 개 생기는 것이 아닙니다. 후보 선택의 기대 개수는 `3 × 0.33 = 0.99`개이지만, 실제 장면은 무작위 선택과 배치·충돌 처리의 영향을 받습니다.

`position.noise`의 정규분포는 타일 안의 위치를 흔들고 `orientation.noise`는 회전을 바꿉니다. 이 값은 부모 타일의 로컬 좌표에 적용됩니다. 타일이 회전하면 같은 로컬 배치도 세계 방향은 달라집니다.

corner 설정은 다음처럼 둘 중 하나를 선택합니다.

```yaml
config: ["None", "obstacle_pile_2.yaml"]
weights: [0.7, 0.3]
```

가중치 0.7로 장애물 더미를 추가하지 않고, 0.3으로 지정 더미를 사용합니다. 이는 배열의 두 설정을 모두 실행한다는 뜻이 아닙니다. 더미 설정의 `apply_children: true`는 부모 Xform 아래의 mesh들에 충돌 설정을 적용하는 데 쓰입니다.

### 자신의 타일과 창고로 확장하려면

타일은 한 변 길이와 연결 위치를 맞춰 제작합니다. 새 Stage의 `/World` 바로 아래에 예시 타일 Xform을 놓고, 붙일 수 있는 타일 쌍을 5 m 간격으로 배치하세요. 이름은 `corridor_0`, `corner_1`처럼 종류를 구분할 수 있게 유지합니다. 규칙 추출기는 숫자 접미사를 제거한 이름 또는 `tile_name` custom data로 종류를 식별합니다. 완성한 예시를 새 `example_pairs.usd`로 저장합니다.

다음 명령은 저장소 루트에서 실행하며 입력 USD 경로를 실제 파일로 바꿉니다. 출력 파일도 기존 결과와 겹치지 않게 선택하세요.

```bash
~/isaacsim/python.sh ~/isaacsim/tools/scene_blox/src/scene_blox/rules_builder.py \
  /절대경로/example_pairs.usd /절대경로/rules_part.yaml 5.0
~/isaacsim/python.sh ~/isaacsim/tools/scene_blox/src/scene_blox/rules_combiner.py \
  /절대경로/combined_rules.yaml --config_files /절대경로/rules_part.yaml
```

첫 도구는 예시의 위치·회전에서 인접 관계를 추출하고, 둘째 도구는 `--config_files`로 나열한 여러 규칙 파일을 합칩니다. 새 규칙의 타일 식별자에 대응하는 USD를 `generation.yaml`에도 등록해야 장면으로 만들 수 있습니다. 규칙 추출만으로 경계 제약이나 전체 경로가 생기지는 않습니다.

공식 창고 예제는 미로와 별도의 타일·생성·제약 파일을 사용합니다. 다음은 설치본의 세 설정을 그대로 연결하는 명령입니다.

```bash
~/isaacsim/python.sh ~/isaacsim/tools/scene_blox/src/scene_blox/generate_scene.py \
  "$PWD/src/176_replicator_replicator_sceneblox/output/warehouse_first" \
  --grid_config "$HOME/isaacsim/tools/scene_blox/parameters/warehouse/tile_config.yaml" \
  --generation_config "$HOME/isaacsim/tools/scene_blox/parameters/warehouse/tile_generation.yaml" \
  --constraints_config "$HOME/isaacsim/tools/scene_blox/parameters/warehouse/constraints.yaml" \
  --cols 15 --rows 11 --variants 1 --units_in_meters 1.0 --collisions --no-window
```

15 columns × 11 rows는 건물의 end/middle piece 배치 제약과 연결됩니다. 저장한 USD를 **File > Open**으로 열어 건물과 통로 연결을 확인하세요. 이 명령은 설치본을 직접 실행하므로 로컬 `run.py`의 `generation.json` 기록이나 생성 후 GUI 유지 기능을 제공하지 않습니다. [공식 Warehouse 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#warehouse-generation-example)와 결과를 비교하되 미로의 행·열 수만 바꾸는 실행과 구분합니다.

## 3. 구조 생성과 소품 생성의 차이 정리

```text
타일 후보 + 이웃 규칙 + 경계 제약
    → 일관된 격자 풀이
    → 타일 USD reference 배치
    → 각 타일의 소품 확률·위치 적용
    → USD와 생성 시도 기록 저장
```

격자를 풀지 못하면 규칙·제약을 살펴보고, 격자는 생겼지만 소품이 예상과 다르면 확률과 물리 배치를 살펴봅니다. 기본 충돌 검사는 소품 배치의 겹침을 줄이는 데 쓰이지만 모든 후속 배치의 교차나 로봇 주행 가능성을 보장하지는 않습니다.

## 4. 간단한 확인 실험

`config/`를 새 폴더에 복사하고 `hazards_corridors.yaml`의 `spawn_proba`만 **0.33 → 0.66**으로 바꾸세요. 새 폴더를 `--config`로 전달하고 같은 seed·행·열 수로 새 출력에 실행합니다.

타일별 콘 개수와 가림·겹침을 비교하세요. 후보 선택의 기대 개수는 늘지만 한 장면에서 정확히 두 배의 콘이 생겨야 하는 것은 아닙니다. 이후 난수 소비도 달라질 수 있으므로 동일 seed가 모든 소품 위치까지 완전히 같게 유지한다는 뜻도 아닙니다.

## 실행할 때 막히면

- **일관된 격자를 찾지 못함**: 서로 충돌하는 경계·회전·개수 제한을 확인하고 seed를 바꿔 비교하세요. 규칙을 모두 없애는 것은 같은 실험이 아닙니다.
- **확장이 로드되지 않음**: 사용 중단 기능이 남아 있는 5.1 설치인지 확인하세요.
- **USD는 있는데 타일이 비어 보임**: 타일·하늘·소품의 자산 루트와 reference 오류를 확인하세요.
- **`--display` 조합 오류**: 풀이 창을 보려면 GUI 실행에서 사용하세요.
- **시작점과 도착점이 연결되지 않음**: 국소 인접 규칙과 전체 길찾기 조건을 구분하고 별도 연결성 검사를 수행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Scene Generation with SceneBlox](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html)에 대응합니다. 공식 labyrinth YAML의 저작권 헤더와 `LICENSE-NVIDIA-EXAMPLES.txt`를 보존하고 로컬 실행기에 seed·시도 횟수·출력 기록을 연결했습니다.

설정과 실행기를 대조했습니다. 실제 WFC 풀이·RTX 렌더링·USD 생성은 이번 개정에서 실행하지 않았으며 `tutorial.json`은 `not_run`입니다. 공식 페이지의 사용 중단 범위도 유지합니다.
