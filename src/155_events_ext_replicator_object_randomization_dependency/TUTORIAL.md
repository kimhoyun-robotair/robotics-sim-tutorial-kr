# 155. 크기·색·배치를 하나의 난수 관계로 연결하기

## 이번에 배우는 것

**독립 색상 난수에서 시작해 크기와 색을 연결하고, 물체 크기를 반영한 그룹 배치까지 확장합니다.**

물체의 색·크기·위치를 모두 따로 뽑으면 각각 다양해지지만 그 사이에 원하는 관계는 생기지 않습니다. 예를 들어 큰 물체를 붉게 만들려면 같은 난수 계수를 크기와 색에 함께 사용해야 합니다. 이번에는 세 설정을 비교하며 관계를 한 단계씩 늘립니다.

| 파일 | 크기와 색 | 배치 |
|---|---|---|
| `scene.yaml` | 크기 0.7 고정, RGB 독립 난수 | X·Z를 개체별 선택 |
| `dependent.yaml` | 같은 계수로 크기와 빨강·파랑 결정 | 크기에 맞춘 초기 중심 높이 |
| `packed.yaml` | 위의 크기·색 관계 유지 | 크기를 반영한 packing과 공유 그룹 변환 |

세 설정 모두 큐브 8개에 `rigidbody`를 적용하고 0.5초 물리 계산 후 촬영합니다. 초기 규칙과 촬영 당시 위치를 구분하는 것이 이 실습의 중요한 부분입니다.

## 1. 독립 난수와 의존 난수 비교하기

Isaac Sim 5.1, IRO 확장과 RTX GPU 환경에서 저장소 루트부터 실행하세요.

```bash
cd src/155_events_ext_replicator_object_randomization_dependency
~/isaacsim/python.sh run.py --launch --headless --frames 3
~/isaacsim/python.sh run.py --config dependent.yaml --launch --headless --frames 3
```

각 실행은 새 출력 폴더를 사용합니다. 콘솔의 두 `output:` 경로를 기록해 두세요. `--launch`가 없는 호출은 `prepared.yaml` 준비만 하므로 영상 비교는 실제 생성이 끝난 뒤 진행합니다. 설치 위치가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 맞춥니다.

기본 장면은 모든 큐브 배율이 0.7이고 RGB 각 성분을 0~1에서 선택합니다. IRO의 기본 큐브 한 변은 100 cm이므로 크기는 70 cm입니다. 중심 Y=50 cm에서 시작하며 중력 981 cm/s²로 움직입니다. 높이 축은 Y입니다.

### 설정에서 볼 부분

`dependent.yaml`의 루트에는 계수 분포가 있습니다.

```yaml
size_min: 0.35
size_max: 0.85
size_coef:
  count: 8
  distribution_type: range
  start: 0.0
  end: 1.0
```

`count: 8`은 `size_coef_0`부터 `size_coef_7`까지 계수를 만듭니다. subject의 번호와 같은 계수를 고르는 표현이 `$[/size_coef_$[index]]`입니다. 안쪽 index가 2라면 바깥 참조는 `/size_coef_2`를 가리킵니다.

```yaml
size: $[/size_min] + $[/size_coef_$[index]] * ($[/size_max] - $[/size_min])
color:
- $[/size_coef_$[index]]
- 0
- 1 - $[/size_coef_$[index]]
```

계수를 `c`라고 부르면 크기 배율은 `0.35 + 0.5c`, 색은 `[c,0,1-c]`입니다. 같은 계수를 참조하므로 커질수록 빨강 성분이 늘고 파랑 성분이 줄어듭니다. 각 참조가 새 난수를 다시 뽑는 구조라면 이런 관계가 유지되지 않습니다.

### 실행 결과 확인하기

각 `output:` 폴더의 `images/`에서 640×480 RGB를 열고, 같은 seed의 `descriptions/`에서 `size_coef_i`, `subject_i.size`, `subject_i.color`를 비교하세요. `labels/`, `3d_labels/`, `segmentation/`은 영상에 대응하는 정답입니다. 바닥도 tracked이므로 라벨 총수를 큐브 수 8과 같다고 요구하지 않습니다.

| 예시 계수 c | 배율 size | 한 변 길이 | 재질 색 |
|---:|---:|---:|---|
| 0 | 0.35 | 35 cm | `[0,0,1]` |
| 0.5 | 0.60 | 60 cm | `[0.5,0,0.5]` |
| 1 | 0.85 | 85 cm | `[1,0,0]` |

표는 식을 설명하기 위한 예시이며 세 값이 실제 표본으로 꼭 선택된다는 뜻은 아닙니다. RGB에서는 큰 큐브가 붉은 계열인지 살펴보되, 조명이 적용된 픽셀값을 재질의 R·B와 직접 같다고 비교하지 않습니다.

초기 Y 위치는 `size*50`입니다. 한 변 `100*size`의 절반만큼 중심을 올려 밑면을 Y=0에 맞춥니다. 다만 X·Z는 독립적으로 선택하므로 큐브끼리 겹칠 수 있고, 이후 물리가 초기 배치를 바꿀 수 있습니다.

## 2. 크기를 반영한 packing과 그룹 이동 연결하기

같은 터미널에서 세 번째 설정을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config packed.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

```yaml
- translate: $[/bin_translate]
- rotateY: $[/bin_rotate]
- transform:
    distribution_type: harmonized
    harmonizer_name: bin_pack
    pitch:
    - ['-$[../../size] * 50', '-$[../../size] * 50', '-$[../../size] * 50']
    - ['$[../../size] * 50', '$[../../size] * 50', '$[../../size] * 50']
- scale: ['$[../size]', '$[../size]', '$[../size]']
```

조정기에 제출하는 `pitch`는 물체의 축에 나란한 경계 상자입니다. size가 0.6이면 각 축 ±30 cm이고, size가 0.85이면 ±42.5 cm입니다. **물체가 커지면 packing이 차지한다고 계산하는 공간도 같이 커집니다.** 크기만 바꾸고 경계를 고정했을 때 생길 수 있는 불일치를 피합니다.

`bin_pack`은 280×220×280 cm 공간 안의 개체별 변환을 구합니다. 그 바깥의 `bin_translate`·`bin_rotate`는 모든 큐브가 같은 전역 값을 참조합니다. X·Z 이동은 각각 -60~60 cm, Y는 130 cm, Y 회전은 -60~60도입니다. 개체마다 그룹 이동을 다시 뽑지 않기 때문에 조정된 배치가 한 묶음으로 이동합니다.

### 실행 결과 확인하기

초기 배치를 보려면 `--headless`를 빼고 실행한 뒤 **Tools > Action and Event Data Generation > Object SDG**의 **Description File**에 이번 `configuration:` 경로를 입력하세요. 초기화·무작위화 때의 packing과 **Simulate** 후 결과를 비교합니다. stage가 교체되므로 편집 중인 작업은 먼저 저장합니다. GUI는 생성 후에도 유지됩니다.

저장 description에는 공통 `bin_translate`·`bin_rotate`와 물체별 `size`·`color`가 남습니다. 그러나 각 물체의 원래 변환 연산 목록은 **촬영 시점의 최종 `global_transform`과 단일 transform**으로 바뀝니다. 저장 파일에서 첫 translate가 공통 값인지 검사하지 마세요. 그 목록은 물리 이전의 입력이므로 `prepared.yaml`과 초기화 Stage에서 확인합니다.

packing 공간은 물체를 붙잡는 용기나 관절이 아닙니다. Y=130 cm 부근에 놓인 그룹은 이후 중력과 충돌로 움직입니다. 0.5초 후에도 모든 큐브가 원래 bin 안에 남거나 완전히 정착해야 한다는 조건은 없습니다.

## 3. 의존 관계와 물리 진행 정리

```text
개체별 size_coef
    ├→ 재질 색
    └→ size → 초기 높이 또는 경계 pitch → packing 변환
공통 bin_translate·bin_rotate → 그룹의 초기 월드 배치
초기 배치 → 0.5초 물리 계산 → 최종 변환과 RGB·정답
```

이 관계는 방향이 있고 순환이 없는 그래프로 볼 수 있습니다. 먼저 알아야 할 값이 다음 값을 결정합니다. 크기와 색을 같은 계수에 연결하는 것과 물체 여러 개를 같은 그룹 이동에 연결하는 것은 모두 **참조 범위를 선택하는 일**입니다.

## 4. 간단한 확인 실험

`dependent.yaml`을 `larger.yaml`로 복사하고 **`size_max`만 0.85에서 1.2로** 바꿉니다.

```bash
~/isaacsim/python.sh run.py --config larger.yaml --launch --headless --frames 3
```

같은 계수 0.5라면 배율은 0.60에서 0.775로, 한 변은 60에서 77.5 cm로 커집니다. 색 `[0.5,0,0.5]`는 같습니다. 실제 같은 seed의 계수·색·size를 description에서 비교하세요. 초기 높이도 size에 따라 올라가며 X·Z 범위는 같으므로 접촉과 가림 양상이 달라질 수 있습니다.

## 실행할 때 막히면

- **크기와 색이 연결되지 않음**: size와 color가 같은 `/size_coef_i`를 참조하는지 확인하세요. 각 속성에 독립 range를 넣으면 관계가 사라집니다.
- **`size_coef_i` 참조를 찾지 못함**: 계수의 count와 subject count, 중첩 `$[...]`의 괄호를 확인합니다.
- **최종 높이가 `size*50`과 다름**: 그 식은 초기 높이입니다. 물리 접촉 이후 위치는 description의 `global_transform`으로 읽으세요.
- **packing 후 물체가 흩어짐**: packing은 초기 배치만 만듭니다. 물리 전 미리보기와 0.5초 후 촬영을 구분하세요.
- **그룹이 함께 이동하지 않음**: `bin_translate` 참조를 개체 내부의 독립 range로 바꾸지 않았는지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Randomization Dependency: Incremental Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/randomization_dependency.html)에 대응합니다. 독립 난수, 속성 간 참조, 공동 배치의 관계를 여덟 기본 큐브로 비교합니다.

식과 저장 형태는 로컬 YAML 및 설치 IRO 0.4.13의 parser·scene 코드를 대조했습니다. 실제 packing·충돌·영상 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
