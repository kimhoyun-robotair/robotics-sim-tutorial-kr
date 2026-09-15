# 152. 여러 물체의 난수를 함께 조정하기

## 이번에 배우는 것

**네 물체에 중복 없는 자리를 배정하고, 물체 크기를 고려해 공간 안에 배치하는 harmonizer를 비교합니다.**

각 물체가 독립적으로 네 자리 중 하나를 고르면 같은 자리를 택할 수 있습니다. 모든 자리를 한 번씩 사용하려면 서로의 선택을 함께 조정해야 합니다. IRO의 **harmonizer**는 개체들이 제출한 값을 모아 이런 공동 조건을 처리합니다.

| 파일 | 개체가 제출하는 값 `pitch` | 돌려받는 값 |
|---|---|---|
| `scene.yaml` | 개체 번호 0·1·2·3 | 중복 없는 자리 번호 `slot` |
| `bin_pack.yaml` | 한 변 60 cm인 큐브의 경계 | 상자 공간 안의 개체별 변환 |

두 설정 모두 물리 시간이 0입니다. 조정기는 초기 배치를 계산하며 낙하와 접촉으로 물체를 쌓는 역할은 하지 않습니다.

## 1. 네 자리를 중복 없이 배정하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트부터 실행합니다.

```bash
cd src/152_events_ext_replicator_object_harmonizer
~/isaacsim/python.sh run.py --launch --frames 3
```

**Tools > Action and Event Data Generation > Object SDG**의 **Description File**에 콘솔의 `configuration:` 경로를 입력하세요. 초기화 후 **Randomize scene**을 여러 번 눌러 물체의 자리 변화를 보고 **Simulate**로 데이터를 저장합니다. 초기화가 stage를 바꾸므로 편집 중인 장면은 먼저 저장합니다.

`--launch`를 빼면 출력 폴더와 `prepared.yaml` 준비에서 끝납니다. GUI는 생성 후에도 열려 있으며, 자동 생성과 종료는 `--launch --headless --frames 3`으로 요청합니다. 설치 위치가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 맞추세요.

### 설정에서 볼 부분

`subject`의 `slot`과 전역 조정기를 연결한 부분입니다.

```yaml
slot:
  distribution_type: harmonized
  harmonizer_name: permute_positions
  pitch: $[../index]
```

```yaml
permute_positions:
  harmonizer_type: permutate
```

각 subject는 자신의 `index`를 제출합니다. `permutate`는 제출된 네 값을 섞어 다시 나눠줍니다. 그러므로 `slot`을 모두 모으면 항상 0·1·2·3이 하나씩 있어야 합니다. 같은 순열이 연속으로 나올 수는 있습니다.

위치는 `($[../slot] - 1.5) * 125`로 정합니다. 이 식의 X 결과는 -187.5, -62.5, 62.5, 187.5 cm입니다. 반면 색 `[index/3, 0.2, 1-index/3]`와 Y 회전 `index*25`는 개체 번호를 사용합니다. **물체의 특징은 유지하고 자리만 바꾸는** 이유가 여기에 있습니다.

### 실행 결과 확인하기

`images/`에서 색이 다른 물체가 자리를 바꾸는지 보세요. `descriptions/`에는 각 subject의 `slot`이 남으므로 네 값을 직접 모아 중복 여부를 확인할 수 있습니다. 최종 `global_transform`의 마지막 행으로 X 위치도 대조합니다. 변환 연산은 저장 시 행렬로 합쳐져 원래 `rotateY` 목록은 남지 않습니다.

IRO는 Y-up·cm 단위입니다. 바닥도 tracked이고 가림에 따라 라벨이 달라질 수 있으므로 라벨 총수만으로 순열 성질을 검사하지 마세요. 확인할 핵심은 **네 slot의 집합과 색을 따라가는 자리 이동**입니다.

## 2. 크기가 있는 큐브를 공간에 넣기

앞의 GUI를 종료하고 다음 설정을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config bin_pack.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

```yaml
pack:
  harmonizer_type: bin_pack
  bin_size: [300, 220, 300]
```

각 큐브의 변환에는 다음 요청이 들어 있습니다.

```yaml
- translate: [0, 120, 0]
- transform:
    distribution_type: harmonized
    harmonizer_name: pack
    pitch: [[-30, -30, -30], [30, 30, 30]]
- scale: [0.6, 0.6, 0.6]
```

`pitch`의 두 벡터는 축에 나란한 경계 상자, 즉 **AABB의 최소·최대 좌표**입니다. 기본 큐브 한 변 100 cm에 배율 0.6을 곱하면 60 cm이므로 중심 기준 경계가 ±30입니다. 조정기는 이 크기를 받아 300×220×300 cm 공간에 12개를 배치합니다.

반환된 `transform`은 개체별 위치·방향입니다. 앞의 `[0,120,0]` 이동은 그 전체 배치를 위로 옮깁니다. `bin_size`는 계산상의 공간 제약이며 눈에 보이는 용기 메시나 충돌 벽을 만드는 설정이 아닙니다.

### 실행 결과 확인하기

RGB에서 큐브 무리를 보고 description의 개체별 `global_transform`을 비교하세요. 큐브가 겹치지 않는지 판단할 때는 중심 간 거리만 보지 말고 크기 60 cm를 함께 고려해야 합니다. 이 예제는 크기를 알고 있으므로 pitch를 직접 검산할 수 있습니다.

개체에 임의의 외부 회전이나 다른 배율을 추가하면 제출한 경계와 실제 형상이 달라질 수 있습니다. 조정기가 받는 크기와 렌더링되는 크기가 맞는지가 배치 품질의 출발점입니다.

## 3. 독립 선택과 공동 조정의 차이 정리

```text
독립 set 선택: 각 물체가 목록에서 선택 → 같은 자리가 나올 수 있음
permutate: 제출한 모든 값을 모아 섞음 → 각 자리 한 번씩 배정
bin_pack: 모든 경계 크기를 모음 → 공간 안의 배치 변환 계산
```

`harmonized` 속성은 입력이 모일 때까지 기다립니다. 필요한 값 수집, 조정, 결과 반영 순서로 해석하므로 YAML의 위에서 아래로 한 번 읽는 것만으로 계산이 끝나는 구조는 아닙니다.

## 4. 간단한 확인 실험

`bin_pack.yaml`을 `small_bin.yaml`로 복사하고 **`bin_size`만 `[120,120,120]`으로** 줄여 보세요.

```bash
~/isaacsim/python.sh run.py --config small_bin.yaml --launch --headless --frames 3
```

한 변 120인 공간에 한 변 60인 큐브는 단순 격자로 최대 2×2×2=8개입니다. 12개 모두 들어갈 수 없습니다. 설치 IRO 0.4.13은 넣지 못한 항목에 X=10000 cm 이동 변환을 반환하므로 일부 큐브가 화면에서 사라질 수 있습니다. 반드시 오류 로그가 난다고 기다리지 말고, 저장된 개체 위치와 시야 안 개수를 비교하세요.

## 실행할 때 막히면

- **Randomize를 눌러도 순서가 같은 때가 있음**: 같은 순열 재선택은 가능합니다. 매번 다른 순서를 요구하지 말고 중복 없는 slot을 검사하세요.
- **bin을 줄이자 일부 큐브가 사라짐**: 배치 불가 항목의 최종 위치를 확인하세요. 카메라 문제가 아니라 공간 부족일 수 있습니다.
- **조정 후 큐브가 겹침**: 실제 scale과 pitch 경계가 일치하는지 확인하세요. 크기를 바꿨다면 ±30 경계를 그대로 사용해도 되는지 다시 계산해야 합니다.
- **화면에 용기가 없음**: `bin_size`는 용기 형상이 아니라 배치 제약입니다. 제공 설정에 용기 메시가 없습니다.
- **준비 YAML에는 slot 숫자가 없음**: harmonizer는 실제 IRO 해석 단계에서 값을 정합니다. 생성된 description을 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Harmonizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/harmonizer.html)에 대응합니다. 순열과 고정 크기 큐브 packing을 비교하며, 런타임에 경계를 측정하는 `local_aabb` 입력은 이 예제에서 사용하지 않습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 기본 순열 설정 한 프레임의 이미지 1장·주석 5개 생성 기록이 있습니다. 설정 파일은 기록 당시와 같지만 현재 `run.py`는 그 뒤 변경되었습니다. 따라서 당시 기록을 현재 실행 파일이나 bin packing·GUI 조작 전체의 검증으로 확대하지 않습니다. 설정별 검증 범위는 `tutorial.json`을 함께 참고하세요.
