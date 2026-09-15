# 146. 하나의 물체 정의에서 여러 개체와 재질 변화를 만들기

## 이번에 배우는 것

**네 큐브의 개체 번호와 무작위 속성을 구분하고, 보이는 물체와 정답 수집 대상이 어떻게 다른지 확인합니다.**

IRO의 **mutable**은 장면에서 속성을 바꿀 수 있는 객체입니다. 카메라·도형·조명이 여기에 해당합니다. 이번에는 `subject` 하나의 기술서로 큐브 네 개를 만들고, 각각의 번호로 위치를 계산합니다. 이어서 같은 방식의 속성 변경을 메시 재질에도 적용합니다.

| 파일 | 장면에서 비교하는 것 |
|---|---|
| `scene.yaml` | 네 큐브의 번호·위치·색·회전, 라벨을 붙이지 않는 구 |
| `shader.yaml` | 로컬 메시의 체크무늬 회전·반복 크기·색조 |
| `shader_image.yaml` | 같은 재질 실험에 텍스처 색 반전 추가 |
| `models/textured.usda`, `checker.png` | 메시·재질 연결과 원본 무늬 이미지 |

## 1. 번호가 있는 큐브 네 개 관찰하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트부터 실행합니다.

```bash
cd src/146_events_ext_replicator_object_mutable
~/isaacsim/python.sh run.py --launch --frames 3
```

**Tools > Action and Event Data Generation > Object SDG**의 **Description File**에 콘솔의 `configuration:` 절대 경로를 넣으세요. **Initialize scene randomization**으로 초기화한 다음 **Randomize scene**을 눌러 색과 자세를 비교합니다. IRO는 stage를 교체하므로 작업 중인 장면은 먼저 저장하세요.

`--launch`가 없는 실행은 새 출력 폴더에 `prepared.yaml`만 만듭니다. GUI 미리보기도 데이터 저장과 별개입니다. **Simulate**가 영상·정답을 저장하며 GUI는 생성 후에도 열려 있습니다. 설치 위치가 다르면 `~/isaacsim`과 `--isaac-root /설치/경로`를 함께 맞추세요.

### 설정에서 볼 부분

`subject`의 개수와 위치·크기 설정입니다.

```yaml
count: 4
transform_operators:
- translate: ['($[../index] - 1.5) * 130', 50, 0]
- rotateY:
    distribution_type: range
    start: -45
    end: 45
- scale: [0.8, 0.8, 0.8]
```

`count: 4`는 `subject_0`부터 `subject_3`까지 만듭니다. 각 `index`는 0·1·2·3입니다. 위치 연산 안의 `$[../index]`는 부모 mutable의 번호를 참조합니다. X 위치를 직접 대입하면 다음과 같습니다.

| 개체 | X 중심 위치 | 다음 개체와의 간격 |
|---|---:|---:|
| `subject_0` | -195 cm | 130 cm |
| `subject_1` | -65 cm | 130 cm |
| `subject_2` | 65 cm | 130 cm |
| `subject_3` | 195 cm | — |

IRO는 Y-up·cm 단위입니다. 기본 큐브 한 변 100에 0.8을 곱하므로 큐브는 80 cm이며 중심 Y는 50 cm입니다. 물리 시간이 0이라 바닥까지의 여유가 자동으로 낙하해 사라지지는 않습니다.

색의 각 성분은 0~1, Y 회전은 -45~45도에서 개체별로 정합니다. 번호가 정한 위치와 난수가 정한 색·회전을 분리해서 보세요. 매번 모든 큐브가 서로 다른 색을 가질 필요는 없습니다.

### 실행 결과 확인하기

초기화 후 Stage의 `/World/Shapes`에서 네 `subject`와 녹색 `untracked` 구를 찾아보세요. 구의 `tracked: false`는 **RGB에서 숨긴다는 뜻이 아닙니다.** 구는 영상에 보이고 다른 큐브를 가릴 수 있지만 객체 정답을 수집하는 대상으로 지정하지 않았습니다.

**Simulate** 후 이번 `output:` 폴더의 `images/`, `labels/`, `3d_labels/`, `segmentation/`을 대조하세요. 바닥도 tracked이므로 전체 라벨 개수만 세어 네 큐브 생성 여부를 판정하지 마세요. description의 `global_transform` 마지막 행에서 큐브별 중심 좌표를 확인할 수 있습니다. 원래 변환 연산은 저장 시 단일 최종 행렬로 정리됩니다.

## 2. 물체 대신 표면 무늬를 바꾸기

앞의 GUI를 닫고 같은 폴더에서 다음 명령을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config shader.yaml --launch --headless --frames 3
```

이번 `subject`는 네 기본 큐브가 아니라 **`models/textured.usda`의 메시 하나**입니다. 이 USD에는 Mesh와 OmniPBR 재질의 연결, UV 좌표, `../checker.png` 텍스처 경로가 포함되어 있습니다. `@PACKAGE@`는 준비 도구가 패키지 절대 경로로 바꾸며, USD 안의 상대 텍스처 경로는 USD 파일 위치를 기준으로 해석됩니다.

### 설정에서 볼 부분

```yaml
shader_attributes:
  texture_rotate:
    distribution_type: range
    start: -90
    end: 90
  texture_scale:
    distribution_type: range
    start: [0.5, 0.5]
    end: [2, 2]
  diffuse_tint:
    distribution_type: range
    start: [0.2, 0.2, 0.2]
    end: [1, 1, 1]
```

`texture_rotate`는 표면 무늬의 회전, `texture_scale`은 두 UV 방향의 반복 크기, `diffuse_tint`는 재질 색조를 바꿉니다. 기하학적 `scale`과 이름은 비슷하지만, `texture_scale`을 바꾼다고 메시가 커지지는 않습니다.

색 반전까지 적용하려면 비교 파일을 선택하세요.

```bash
~/isaacsim/python.sh run.py --config shader_image.yaml --launch --headless --frames 3
```

이 파일에는 `diffuse_texture: <invert_color>`가 추가되어 있습니다. 설치된 IRO 0.4.13의 메시 처리 코드가 이 문자열을 이미지 연산으로 해석합니다. 두 실행을 같은 seed로 짝지어 무늬 색을 비교하세요. 최종 RGB는 조명과 색조도 적용되므로 화면 픽셀을 단순히 `1-RGB`로 계산한 결과와 같다고 기대하지 않습니다.

### 실행 결과 확인하기

`descriptions/`의 `shader_attributes`에서 선택된 값을 확인하고 대응 RGB에서 무늬 방향·밀도·색을 살펴보세요. 메시 외곽과 위치는 유지되어야 합니다. 형상이 움직였다면 재질 변화와 별도의 transform 변경을 혼동하지 않았는지 확인하세요.

## 3. 개체·가시성·재질의 차이 정리

```text
count와 index → 어떤 개체를 몇 개 만들고 어디에 둘지
color와 rotateY → 각 개체의 모습과 자세
tracked → 정답 수집 대상으로 지정할지
shader_attributes → 기존 메시의 표면 표현
```

한 mutable의 정의 안에 이 설정들이 함께 있어도 역할은 다릅니다. 객체 수가 맞는지, 화면에 보이는지, 라벨이 붙는지, 표면 무늬가 바뀌는지를 각각 관찰하면 문제를 좁힐 수 있습니다.

## 4. 간단한 확인 실험

`scene.yaml`을 `two_cubes.yaml`로 복사하고 **`subject.count`만 4에서 2로** 바꾸세요.

```bash
~/isaacsim/python.sh run.py --config two_cubes.yaml --launch --headless --frames 3
```

두 큐브의 X는 -195와 -65 cm가 됩니다. 식의 `1.5`를 그대로 두었기 때문에 중앙에 대칭으로 재배치되지 않습니다. 이 결과를 설명할 수 있으면 개체 수와 위치 계산이 서로 다른 설정이라는 점을 이해한 것입니다.

## 실행할 때 막히면

- **녹색 구가 보이는데 라벨이 없음**: `tracked: false`의 의도된 결과입니다. 화면에 보이는 것과 정답 수집을 구분하세요.
- **셰이더 실행에서 파일을 찾지 못함**: `models/`와 `checker.png`까지 폴더 전체가 있는지, `prepared.yaml`의 `usd_path`가 맞는지 확인하세요.
- **`shader attribute ... does not exist`**: 임의의 USD로 바꾸었다면 그 재질에 같은 입력이 있는지 확인하세요. 제공 메시에는 필요한 OmniPBR 입력을 정의했습니다.
- **색 반전 설정을 사전 형태로 바꾸자 parser 오류**: 제공된 `<invert_color>` 문자열로 되돌리세요. 공식 문서의 텍스처 분포 예시와 설치 0.4.13의 입력 방식에는 차이가 있습니다.
- **생성이 중간에 종료됨**: `--steps`를 생략하세요. 이 옵션은 앱 업데이트 수이며 `--frames`와 다릅니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Mutable](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable.html)에 대응합니다. 원문의 개체 확장과 셰이더 변경을 네 큐브 및 로컬 체크무늬 메시로 비교합니다. 여러 이미지 연산 중 여기서는 색 반전만 다룹니다.

입력 키와 재질 연결은 로컬 YAML·USD 및 설치 IRO 0.4.13을 기준으로 설명했습니다. 실제 RGB·재질 렌더링 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
