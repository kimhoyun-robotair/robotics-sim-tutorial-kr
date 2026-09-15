# 150. 파일·각도·위치를 서로 다른 분포에서 고르기

## 이번에 배우는 것

**모델 파일 선택, 정해진 각도 선택, 연속 위치 샘플링을 구분하고 카메라 시야를 기준으로 물체를 배치합니다.**

무작위화라고 해서 모든 값에 같은 방법을 쓰지는 않습니다. 모델은 실제 파일 목록에서 골라야 하고, 자세를 세 가지로 제한하려면 각도 목록이 필요합니다. 위치는 공간 범위에서 뽑을 수도 있고 카메라가 보는 영역에서 뽑을 수도 있습니다.

| 분포 | 이 폴더에서 쓰는 속성 | 선택 결과 |
|---|---|---|
| `folder` | `scene.yaml`의 `usd_path` | box 또는 pyramid USD 경로 |
| `set` | 같은 파일의 `rotateY` | -45·0·45도 중 하나 |
| `range` | 위치와 dome 세기 | 지정한 시작·끝 사이 값 |
| `camera_frustum` | `frustum.yaml`의 위치 | 카메라 시야 안의 중심 위치 |

## 1. 네 메시의 모양과 자세 비교하기

Isaac Sim 5.1, IRO 확장과 RTX GPU 환경에서 저장소 루트부터 실행하세요. 모델 선택에 필요한 `models/` 폴더를 함께 유지합니다.

```bash
cd src/150_events_ext_replicator_object_mutable_attribute
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

`output:`으로 표시된 새 폴더에 결과가 저장됩니다. `run.py`의 기본 동작은 `prepared.yaml` 준비이며 `--launch --headless`가 실제 앱 생성과 종료를 요청합니다. 설치 위치가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 맞추세요.

### 설정에서 볼 부분

```yaml
usd_path:
  distribution_type: folder
  value: '@PACKAGE@/models'
  suffix: usda
```

준비 도구가 `@PACKAGE@`를 절대 경로로 바꾸면 IRO가 해당 폴더에서 `.usda` 파일을 찾습니다. 제공된 선택지는 `box.usda`와 `pyramid.usda`입니다. `count: 4`인 네 subject가 각각 파일을 고르므로, 같은 모델이 여러 번 나오는 것도 정상입니다.

회전과 위치는 다른 방식으로 정합니다.

```yaml
- translate:
    distribution_type: range
    start: [-160, 50, -100]
    end: [160, 150, 100]
- rotateY:
    distribution_type: set
    values: [-45, 0, 45]
- scale: [0.6, 0.6, 0.6]
```

Y 회전은 세 각도 중 하나이고 X·Y·Z 위치는 각 성분의 범위 안에서 선택됩니다. 단위는 cm이고 Y가 위쪽입니다. `set`에 0이 있다고 가운데 자세를 더 자주 택하는 것은 아닙니다. 선택지 전체가 세 프레임 안에 꼭 나타날 필요도 없습니다.

### 실행 결과 확인하기

`images/`의 640×480 RGB와 같은 seed의 `descriptions/`를 함께 엽니다. subject별 `usd_path`를 확인해 영상의 상자·피라미드와 짝지어 보세요. 저장 description의 `global_transform` 마지막 행은 중심 위치이므로 X -160~160, Y 50~150, Z -100~100 cm 범위와 대조할 수 있습니다.

원래 `rotateY` 연산은 저장 시 최종 행렬로 합쳐집니다. 각도를 직접 보려면 `--headless`를 빼고 실행한 뒤 **Tools > Action and Event Data Generation > Object SDG**의 **Description File**에 이번 `configuration:` 경로를 넣으세요. 작업 중인 stage를 저장하고 **Initialize scene randomization → Randomize scene** 후 해당 prim의 변환을 확인합니다. **Simulate**가 저장하며 GUI는 직접 닫을 때까지 유지됩니다. 이 기본 장면은 dome 세기도 300~900에서 바뀌므로 RGB 밝기 변화가 모델 선택만의 효과는 아닙니다.

## 2. 카메라 시야 안에 큐브 중심 배치하기

이번에는 모델 파일 선택을 없애고 작은 큐브 10개의 중심 위치에 집중합니다.

```bash
~/isaacsim/python.sh run.py --config frustum.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

```yaml
- translate:
    distribution_type: camera_frustum
    camera_parameters: $[/camera_parameters]
    distance_min: 250
    distance_max: 650
    screen_space_range: 0.65
- scale: [0.25, 0.25, 0.25]
```

카메라의 **frustum**은 시야를 입체 공간으로 펼친 영역입니다. 이 분포는 카메라 파라미터로 시야 크기를 계산하고, 그 안에서 중심을 뽑습니다. `screen_space_range: 0.65`는 화면 중심을 기준으로 좌우·상하 범위를 전체 반폭·반높이의 65%까지 사용합니다.

`distance_min`·`distance_max`는 카메라 전방 축을 따른 깊이 범위입니다. 설치 IRO는 결과 Z를 `-distance`로 놓습니다. 따라서 이를 카메라와 물체 사이의 유클리드 거리와 항상 같은 값으로 읽지 마세요. 화면 가장자리로 갈수록 직선거리는 더 길어집니다.

이 YAML의 카메라는 `transform_operators: []`로 원점에 있습니다. 그래서 분포가 만든 카메라 좌표와 월드 좌표가 일치합니다. 다른 카메라 위치로 바꿀 때는 위치 분포에 대응 변환도 필요합니다. `camera_parameters` 참조만으로 카메라의 월드 pose를 자동 추적하는 설정은 아닙니다.

### 실행 결과 확인하기

새 RGB에서 큐브 중심이 화면 중앙 영역에 모이는지 확인하고, description의 최종 중심 Z가 -650~-250 cm인지 살펴보세요. 큐브 한 변은 25 cm입니다. 이 분포가 제한하는 것은 **중심**이므로 물체 외곽 전체의 화면 포함, 서로 겹치지 않음, 가려지지 않음을 보장하지 않습니다.

`frustum.yaml`에는 바닥이 없지만 큐브끼리 서로 가릴 수 있습니다. RGB에서 보이는 개수만으로 생성된 개수를 판단하지 말고 description의 개체도 함께 확인하세요. 두 설정 모두 물리 시간과 중력이 0이라 겹침이나 공중 배치를 물리로 정리하지 않습니다.

## 3. 월드 공간 범위와 화면 공간 범위 정리

```text
range 위치
월드 X·Y·Z 범위에서 선택 → 카메라에 투영 → 화면 밖일 수도 있음

camera_frustum 위치
화면 중심 범위와 깊이를 선택 → 카메라 좌표의 위치 계산 → 월드 배치
```

frustum의 깊이는 단순한 균등 거리 분포가 아닙니다. 설치 소스는 역수 방식으로 거리를 샘플링해 투영 크기 변화를 고려합니다. 따라서 250~650 cm를 같은 간격으로 나눈 거리 구간마다 같은 개수를 기대하지 마세요. 세 프레임만으로 분포의 통계적 균일성까지 판단할 수도 없습니다.

## 4. 간단한 확인 실험

`frustum.yaml`을 `central.yaml`로 복사하고 **`screen_space_range`만 0.65에서 0.25로** 줄입니다.

```bash
~/isaacsim/python.sh run.py --config central.yaml --launch --headless --frames 3
```

깊이 범위와 큐브 크기는 같지만 중심의 투영 범위가 더 좁아집니다. 전후 RGB에서 가장자리 중심 위치를 비교해 보세요. 중앙에 모으는 과정에서 가림이 늘어날 수도 있습니다. 화면 안 배치와 가림 방지는 다른 조건입니다.

## 실행할 때 막히면

- **`folder ... is empty`**: `models/`에 `.usda` 파일이 있는지, `prepared.yaml`의 경로와 `suffix`가 맞는지 확인하세요.
- **세 각도가 순서대로 나오지 않음**: `set`은 순회가 아닌 선택입니다. 반복 선택을 오류로 보지 마세요.
- **카메라를 옮긴 뒤 frustum 큐브가 안 보임**: 원점 카메라와 위치 샘플의 좌표계가 달라진 것입니다. 우선 제공 설정의 빈 카메라 변환으로 되돌려 비교하세요.
- **큐브 중심은 시야 안인데 일부가 안 보임**: 외곽 절단과 가림을 확인하세요. 이 분포에는 충돌 회피 조건이 없습니다.
- **`camera_frustum`을 `frustum`으로 바꾸자 오류**: 실행 키는 `camera_frustum`입니다. 카메라 파라미터 참조도 `$[/camera_parameters]`를 유지하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Mutable Attribute](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable_attribute.html)에 대응합니다. 로컬 모델 두 개와 원점 카메라를 사용해 파일 선택·각도 선택·위치 분포의 차이를 비교합니다.

좌표와 frustum 의미는 설치 IRO 0.4.13의 `AttributeCameraFrustum`을 대조했습니다. 실제 영상 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
