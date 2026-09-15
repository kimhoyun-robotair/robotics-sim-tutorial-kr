# 149. 물체는 그대로인데 조명만 바꾸면 무엇이 달라질까요?

## 이번에 배우는 것

**방향광의 세기·방향·색을 바꾸고, 환경 텍스처를 쓰는 dome 조명과 영상 차이를 비교합니다.**

같은 빨간 큐브라도 빛이 들어오는 방향에 따라 밝은 면과 그림자가 달라집니다. 이번 장면은 카메라·큐브·바닥을 고정해 그 차이를 조명 설정과 연결합니다. 물리 시간은 0이므로 물체가 떨어져서 그림자가 바뀌는 실험은 아닙니다.

| 설정 | `scene.yaml` | `dome.yaml` |
|---|---|---|
| 주변 조명 | 세기 100의 약한 dome | 세기 1200의 dome |
| 방향광 `key_light` | 세기·Y 회전·색 무작위화 | 없음 |
| 환경 텍스처 | 없음 | 로컬 `sky.png` |
| 프레임별 난수 | 방향광에 있음 | 없음 |

## 1. 방향광이 바뀌는 세 장면 만들기

Isaac Sim 5.1, IRO 확장과 RTX GPU 환경에서 실행합니다. 저장소 루트에서 다음 폴더로 이동하세요.

```bash
cd src/149_events_ext_replicator_object_light
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

콘솔의 `output:` 폴더에 결과가 저장되고 생성 후 종료합니다. `--launch`를 빼면 `prepared.yaml`만 준비하므로 아직 조명 효과를 관찰한 것이 아닙니다. 설치 경로가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 지정하세요.

### 설정에서 볼 부분

`key_light`에서 세기와 색 설정을 찾아보세요.

```yaml
type: light
subtype: distant
intensity:
  distribution_type: set
  values: [300, 1200, 2400]
color:
  distribution_type: set
  values:
  - [1, 0.7, 0.5]
  - [0.5, 0.7, 1]
```

`set`은 목록에서 하나를 고릅니다. 세 장을 촬영한다고 세기 세 가지를 차례로 한 번씩 사용하는 것은 아닙니다. 같은 세기를 연속으로 선택할 수도 있습니다. 색 목록은 따뜻한 계열과 차가운 계열의 RGB 색조입니다.

변환에는 `rotateX: -45`와 -70~70도의 무작위 `rotateY`가 있습니다. `distant`는 멀리서 들어오는 평행광입니다. 기본 -Z 방향을 회전시켜 입사 방향을 정하므로, 광원의 위치를 옮기는 것보다 회전이 그림자 방향을 결정하는 핵심입니다.

이 장면은 Y-up·cm 단위이며 큐브 중심은 `(0,50,0)`, 한 변은 100 cm입니다. 큐브와 카메라가 고정되어 있어 서로 다른 프레임의 같은 면을 비교하기 쉽습니다.

### 실행 결과 확인하기

`images/`의 640×480 RGB를 열고 밝은 면, 그림자 방향, 전체 색조를 비교합니다. 같은 seed의 `descriptions/`에서 `key_light.intensity`와 `color`를 찾아 실제 선택과 연결하세요.

회전은 저장 description에서 최종 `global_transform` 행렬로 합쳐집니다. 원래 `rotateY` 숫자를 찾는 대신 준비 YAML에서 난수 범위를 읽고, 방향은 초기화 화면의 광원 속성이나 최종 변환으로 확인합니다.

세기 2400이 1200의 두 배여도 RGB 픽셀값이 정확히 두 배가 되지는 않습니다. 조명·재질의 상호작용, 카메라 노출과 영상의 색 변환을 거친 결과이기 때문입니다. 그림자 방향과 밝은 면의 변화부터 비교해 보세요.

## 2. 하늘 텍스처를 사용하는 dome과 비교하기

같은 폴더에서 다음 설정을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config dome.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

```yaml
dome_light:
  type: light
  subtype: dome
  intensity: 1200
  color: [1, 1, 1]
  texture_path: '@PACKAGE@/sky.png'
```

dome은 장면을 둘러싼 방향별 환경광을 표현합니다. `texture_path`는 그 환경에 사용할 이미지를 지정합니다. `run.py`는 `@PACKAGE@`를 이 폴더의 절대 경로로 바꿉니다. 이 치환이 성공했다는 것과 렌더러가 텍스처를 읽어 조명에 사용했다는 것은 별도 확인입니다.

`dome.yaml`에는 `key_light`가 없습니다. 따라서 기본 실행과 비교하면 **방향광이 포함된 구성과 텍스처 dome만 있는 구성**의 차이를 보게 됩니다. 두 설정의 전체 밝기 차이를 텍스처 하나의 효과로만 설명하지 마세요. 광원 구성과 세기도 함께 다릅니다.

### 실행 결과 확인하기

새 출력의 description에서 dome 세기 1200, 흰색 color, 해소된 `texture_path`를 확인합니다. RGB에서는 환경 배경과 큐브 면의 조명 차이를 봅니다. 이 파일에는 무작위 조명 항목이 없으므로 세 프레임의 조명이 같아도 정상입니다.

제공된 `sky.png`는 작은 LDR 학습 이미지입니다. 밝기를 제한된 범위로 저장한 이미지이므로 실제 하늘의 넓은 광량 범위를 기록한 HDRI와 같은 보정 자료로 해석하지 않습니다. 이 실습의 목적은 텍스처가 환경 조명으로 연결되는 경로를 이해하는 것입니다.

환경의 방향만 바꾸는 비교도 해 보세요. `dome.yaml`을 `dome_rotated.yaml`로 복사하고 `dome_light`에 아래 변환만 추가합니다. `intensity`와 텍스처 경로는 유지합니다.

```yaml
  transform_operators:
  - rotateY: 90
```

```bash
~/isaacsim/python.sh run.py --config dome_rotated.yaml --launch --headless --frames 3
```

이 연산은 큐브가 아니라 환경광을 Y축 주위로 90도 돌립니다. 원래 dome 실행과 같은 seed의 RGB에서 하늘 무늬 방향과 큐브 면의 조명 차이를 비교하세요. 제공 텍스처가 작아 표면 밝기의 차이는 미묘할 수 있으므로, 배경 무늬와 description의 dome 변환도 함께 확인합니다. 이렇게 광원 세기·색·텍스처를 고정하면 환경 방향의 효과를 따로 읽을 수 있습니다.

GUI로 보고 싶다면 `--headless`를 빼고 실행한 뒤 **Tools > Action and Event Data Generation > Object SDG**에서 이번 `configuration:`을 **Description File**에 넣으세요. 초기화와 **Randomize scene**은 미리보기이며 **Simulate**가 저장합니다. 초기화 전 작업 중인 stage를 저장하고, 생성 후 유지되는 GUI는 직접 닫습니다.

## 3. 조명 속성과 영상 변화 정리

| 바꾸는 값 | 먼저 관찰할 부분 |
|---|---|
| distant의 회전 | 어느 면이 빛을 받고 그림자가 어느 쪽으로 생기는지 |
| `intensity` | 표면 밝기가 어떻게 달라지는지 |
| `color` | 조명이 표면 색에 어떤 색조를 더하는지 |
| dome의 `texture_path` | 환경 배경과 방향별 주변 조명 |

RGB는 최종 관측값이고 YAML의 light 속성은 그 관측을 만드는 입력입니다. 둘을 함께 보면 데이터의 조명 다양성이 어떤 규칙에서 나왔는지 설명할 수 있습니다.

## 4. 간단한 확인 실험

`scene.yaml`을 `fixed_intensity.yaml`로 복사하고 **`key_light.intensity.values`만 `[1200]`으로** 바꾸세요.

```bash
~/isaacsim/python.sh run.py --config fixed_intensity.yaml --launch --headless --frames 3
```

description의 세기는 모든 프레임에서 1200이어야 합니다. 그림자 방향과 색조는 계속 달라질 수 있습니다. 세기를 고정했다고 영상 전체가 동일해지는 것은 아니라는 점을 확인해 보세요.

## 실행할 때 막히면

- **세 프레임에 300·1200·2400이 한 번씩 안 나옴**: `set`은 순회 목록이 아니라 무작위 선택입니다. 선택값이 목록 안에 있는지 확인하세요.
- **광원을 이동했는데 그림자 방향이 그대로임**: distant 조명의 방향은 회전으로 정합니다. `transform_operators`의 회전을 확인하세요.
- **dome 텍스처를 찾지 못함**: `sky.png`와 `prepared.yaml`의 절대 경로를 확인하세요. 다른 위치로 옮길 때 파일 전체를 유지합니다.
- **빨간 큐브가 푸른 조명 아래 다르게 보임**: 재질 색과 광원 색이 함께 영상에 영향을 줍니다. 큐브의 `color`가 바뀌었는지 description과 대조하세요.
- **창은 떴는데 출력이 없음**: GUI에서 Description File을 지정하고 **Simulate**를 눌렀는지 확인하세요. `--steps`는 생성을 끝내는 기준이 아닙니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Light](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/light.html)에 대응합니다. 원문의 방향광 설명에 해당하는 설치 IRO 입력 이름은 `distant`이며, 로컬 `sky.png`로 dome 텍스처 연결을 실습합니다.

이 자료는 광량 보정이나 실제 HDRI 측정 실험을 포함하지 않습니다. 실제 렌더링 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
