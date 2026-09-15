# 176. SceneBlox로 규칙에 맞는 미로 생성하기

권장 학습 순서 **176** · 사용 중단 문서와 레거시 참고 · 출처 ID `t052`

공식 **Scene Generation with SceneBlox**를 로컬 구성 파일과 실제 SceneBlox API로 구현했다. 원본은 **DEPRECATED**로 표시되며 이 수업은 Isaac Sim **5.1.0**을 대상으로 한다. 다른 패키지의 공통 코드가 필요 없다.

## 이 실습의 의도

교차로·직선·모서리·막다른 길 tile을 인접 규칙과 경계 제약에 맞게 선택하여 7×7 미로 USD를 생성한다. 통로 구조를 결정하는 규칙과 콘·장애물 더미를 추가하는 확률 설정을 분리해, 같은 생성 과정에서 구조와 소품이 각각 어떻게 바뀌는지 관찰한다. 기본은 미로 한 장면의 생성·저장까지이며, 출발점에서 도착점까지의 연결성이나 로봇 주행은 따로 검사해야 한다. 공식 사용 중단 예제를 보존한 Isaac Sim 5.1 실습이다.

## 실행 후 확인할 것

- **저장 결과:** `generation.json`에 기본 variant 0의 `rows=7`, `cols=7`, `attempts`, `usd`가 기록되고 해당 `generated_0.usd`가 열리는지 확인한다. 파일 존재에 더해 tile 자산의 실제 형상까지 보여야 한다.
- **고정 칸:** Stage에서 `/World/tile_0_0`과 `/World/tile_6_6`을 선택해 corridor 회전 0인지 확인한다. 다른 격자 크기에서는 마지막 행·열에 맞춰 경로를 바꿔 확인한다.
- **미로 제약:** 이웃 통로가 맞물리고, 전체 dead_end가 4개 이하이며 border에 cross·dead_end가 없는지 본다. 개별 인접 규칙을 통과해도 두 지정 모서리를 잇는 전체 경로는 보장되지 않는다.
- **소품 확률:** corridor·cross의 콘은 3개 후보 각각 `spawn_proba=0.33`으로 뽑으므로 tile마다 3개가 있어야 하는 것이 아니다. corner에는 0.7 가중치로 장애물 더미가 생기지 않을 수 있다.
- **생성 후 상태:** 창을 유지하는 동안 미로가 계속 재생성되지 않는 것이 정상이다. `--variants`가 생성 장면 수를 정하고 GUI에는 마지막 장면을 남기므로 여러 결과는 저장된 USD별로 비교한다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 장면 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--variants`로 요청한 장면 수가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비

Linux와 RTX GPU, Isaac Sim 5.1 전체 설치, `isaacsim.replicator.scene_blox` 확장이 필요하다. 설치본 assets root에서 `/Isaac/Samples/Scene_Blox/Tutorial/`, `/Isaac/Environments/Simple_Warehouse/Props/`, `/NVIDIA/Assets/Skies/Dynamic/CumulusHeavy.usd`를 읽을 수 있어야 한다. 기본 tile 크기는 5 m이고 생성 stage 단위는 1 m다.

```bash
cd src/176_replicator_replicator_sceneblox
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --headless --rows 7 --cols 7 --seed 42 --output output/seed42
# GUI에서 matplotlib의 격자 풀이도 보고 싶을 때:
"$ISAAC_SIM_PATH/python.sh" run.py --display --rows 7 --cols 7 --seed 43 --output output/seed43
```

GUI 실행은 마지막으로 생성한 장면을 그대로 열어 두므로 바로 관찰할 수 있다. Headless 결과는 Isaac Sim의 **File → Open**에서 `output/seed42/generated_0.usd`를 선택해 확인한다. generator는 유한 회수의 시도로 장면 생성을 마치고 성공한 장면 경로와 시도 횟수를 `generation.json`에 기록한다. 기존 결과를 보존하도록 새 `--output` 경로만 허용한다.

## 단계별 실습

1. `config/generation.yaml`의 `tile_size: 5.0`과 네 tile의 USD 경로를 읽는다. `/World/tile_행_열`은 tile의 Xform이고 base USD를 reference한다. 원본 tile 파일을 복사해 붙이는 대신 USD reference로 장면을 조합한다.
2. `config/rules.yaml`에서 `adjacencies` 한 항목을 고른다. 이 규칙은 **현재 tile 오른쪽의 이웃**을 기준으로 정의한다. `self_rotation`과 `neighbor_rotation`은 0/1/2/3, 즉 반시계 90도 단위다. 쌍 전체를 돌려 다른 방향 이웃도 검사한다. `tiles[].weights`는 각 회전 선택의 상대 확률이다.
3. `config/constraints.yaml`의 첫 규칙은 `(0,0)`을 corridor 회전 0으로, 다음 규칙은 마지막 칸 `(-1,-1)`도 같은 종류로 제한한다. row/col 구간 양 끝은 포함한다. `-1`은 마지막 행/열이다. `restrict_count`는 전체 dead_end를 4개 이하로 제한한다.
4. 첫 생성물을 열고 Stage에서 `/World/tile_0_0`과 마지막 tile을 선택한다. 직선 방향과 경계 바깥으로 나가는 통로가 허용된 두 모서리에 한정되는지 확인한다. 다른 border에는 cross/dead_end가 없어야 한다.
5. `hazards_corridors.yaml`에서 `spawn_count: 3`, `spawn_proba: 0.33`을 확인한다. 각 콘마다 독립적으로 생성 여부를 뽑는다. `normal` position noise와 `uniform` orientation noise는 부모 tile의 local 좌표에 적용된다. `scale: 0.01`은 asset의 단위를 장면에 맞춘다.
6. `generation.yaml`의 `corner`는 `None`과 `obstacle_pile_2.yaml` 중 0.7/0.3 가중치로 **하나를 선택**한다. 목록으로 나열한 여러 generation 항목은 순서대로 적용되지만, 한 항목의 config 배열은 상호 배타적 선택이다. pile의 `apply_children: true`는 부모 Xform 대신 하위 Mesh에 collision을 적용한다.
7. 같은 seed에서 `spawn_proba`만 0.33→0.66으로 바꿔 새 output으로 만든다. 여러 tile의 콘 개수와 겹침을 비교한다. 한 번의 무작위 결과만으로 정확히 두 배라고 결론 내리지 않는다.

## API와 알고리즘

`tile_loader`가 tile 종류·회전·확률·인접 규칙을 읽는다. `TileSuperposition`은 각 칸이 선택할 수 있는 후보 집합이다. `GridConstraints.from_yaml`로 초기 후보를 제한한다. `Grid.solve`는 entropy가 작은 칸을 골라 하나로 **collapse**하고, 이웃 후보 중 불가능한 것을 제거하며 전파한다. 모순이 생기면 되돌아가 다른 선택을 시도한다. 확률 seed는 `config.GlobalRNG().rng`로 설정한다.

`SceneGenerator.generate_scene`은 완성된 격자에 USD reference·랜덤 소품·물리 장면을 작성한다. `World(stage_units_in_meters=1.0)`이 중력 등 물리 단위를 맞춘다. 기본 충돌 검사는 rigid body 소품을 추가할 때 이미 존재하는 물체와 겹치는지 검사한다. 뒤늦게 추가되는 비동적 물체까지 모든 교차를 보장하지 않으므로 저장된 장면에서 실제 접촉도 점검한다. `--no-collisions`는 비교 실험용이다.

## 직접 규칙 만들기와 warehouse 확장

새 타일은 한 변이 같은 길이여야 한다. GUI에서 예제 tile들을 인접한 쌍으로 배치한 stage를 만든다. tile 이름은 종류 판별에 사용되므로 임의로 바꾸지 않는다. 설치본의 `tools/scene_blox/src/scene_blox/rules_builder.py`는 `stage save_path tile_size`를 받아 USD 예시에서 규칙을 추출한다. `rules_combiner.py`는 여러 결과를 합친다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/tools/scene_blox/src/scene_blox/rules_builder.py" \
  /absolute/path/to/example_pairs.usd /absolute/path/to/rules_part.yaml 5.0
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/tools/scene_blox/src/scene_blox/rules_combiner.py" \
  /absolute/path/to/combined_rules.yaml --config_files /absolute/path/to/rules_part.yaml
```

공식 warehouse 예시는 아래 명령으로 실행한다. grid의 **15 columns × 11 rows**는 건물 폭과 end/middle piece 배치 제약에 연결되어 있으므로 숫자만 바꾸지 않는다. local 미로와 별개로 공식 warehouse 구성을 그대로 사용하는 native 확장 실습이다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/tools/scene_blox/src/scene_blox/generate_scene.py" \
  "$PWD/output/warehouse" \
  --grid_config "$ISAAC_SIM_PATH/tools/scene_blox/parameters/warehouse/tile_config.yaml" \
  --generation_config "$ISAAC_SIM_PATH/tools/scene_blox/parameters/warehouse/tile_generation.yaml" \
  --constraints_config "$ISAAC_SIM_PATH/tools/scene_blox/parameters/warehouse/constraints.yaml" \
  --cols 15 --rows 11 --variants 1 --units_in_meters 1.0 --collisions --no-window
```

`Could not solve`면 seed를 바꾸거나 상충하는 경계·개수 제한을 확인한다. 규칙을 모두 제거하면 결과를 만들 수 있어도 의도한 미로가 아니다. 확장 로딩 실패면 5.1 설치 및 확장 존재를 확인한다. USD가 비어 있으면 원격 asset 경로 접근 로그를 확인한다. 검증 범위는 문법·CLI이며 실제 WFC/RTX/USD 생성은 별도 실행이 필요하다.

## 출처

- [Isaac Sim 5.1 SceneBlox](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html)
- [Constraints](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#constraints), [Tile randomization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#tile-randomization), [Warehouse](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html#warehouse-generation-example)
- API 호출 근거는 5.1 설치본 `tools/scene_blox/src/scene_blox/generate_scene.py`. `config/`는 공식 labyrinth YAML이며 원본 copyright 헤더와 동봉 Apache-2.0 라이선스를 유지했다.
