# 147. 같은 위치의 두 카메라는 왜 다른 크기로 볼까요?

## 이번에 배우는 것

**초점거리만 다른 두 카메라로 같은 큐브를 촬영하고, 물체의 픽셀 크기와 화각을 비교합니다.**

카메라를 물체에 가까이 옮기지 않아도 화면에서 물체를 크게 보이게 할 수 있습니다. 이번에는 두 카메라를 같은 위치·방향으로 고정해 초점거리 효과를 분리합니다. 한 프레임마다 두 영상이 생기므로 카메라 이름을 기준으로 짝을 맞춰야 합니다.

| 카메라 설정 | `default_camera` | `zoom_camera` |
|---|---:|---:|
| 위치 X·Y·Z | `(0,50,500)` cm | `(0,50,500)` cm |
| `focal_length` | 24 | 48 |
| `horizontal_aperture` | 24 | 24 |
| 영상 크기 | 640×480 | 640×480 |
| 근거리·원거리 절단 거리 | 1·5000 cm | 1·5000 cm |

카메라의 전방은 로컬 **-Z**, 영상 위쪽은 **+Y**입니다. 큐브 중심은 `(0,50,0)` cm이므로 두 카메라 모두 큐브를 정면으로 봅니다. 물리 시간과 중력은 0이며, 무작위 위치·회전도 없습니다.

## 1. 두 카메라의 영상 만들기

Isaac Sim 5.1과 RTX GPU가 있는 환경에서 저장소 루트부터 실행하세요.

```bash
cd src/147_events_ext_replicator_object_camera
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

이 명령은 새 출력 폴더에 `prepared.yaml`을 준비하고 IRO로 데이터를 생성한 뒤 종료합니다. `--launch`를 빼면 설정 준비에서 끝나므로 이미지가 생기지 않습니다. 설치 경로가 다르면 `~/isaacsim`과 `--isaac-root /설치/경로`를 함께 맞추세요.

### 설정에서 볼 부분

기본 카메라는 전역 파라미터를 참조합니다.

```yaml
default_camera:
  type: camera
  camera_parameters: $[/camera_parameters]
  transform_operators:
  - translate: [0, 50, 500]
```

`zoom_camera`는 자체 `camera_parameters` 사전을 가지며, 그 안의 초점거리만 48로 지정되어 있습니다. 전역 값을 두 배로 바꾼 뒤 같은 사전을 참조하게 만든 구조가 아닙니다. 따라서 **어느 카메라의 파라미터를 편집하는지** 확인해야 합니다.

### 실행 결과 확인하기

`output:`으로 표시된 폴더의 `images/`에서 같은 seed를 가진 파일을 찾습니다.

```text
frame_11_default_camera.jpg  ↔  frame_11_zoom_camera.jpg
frame_12_default_camera.jpg  ↔  frame_12_zoom_camera.jpg
frame_13_default_camera.jpg  ↔  frame_13_zoom_camera.jpg
```

세 장면을 두 카메라로 촬영하므로 기본 RGB 기대 개수는 **6장**입니다. description은 장면 전체에 대해 `frame_11_GLOBAL.yaml`처럼 저장되어 카메라별로 두 배가 되지 않습니다.

두 이미지에서 큐브의 가로 픽셀 너비를 비교하세요. `zoom_camera`에서는 약 두 배로 커집니다. 같은 카메라의 세 프레임이 비슷한 것은 정상입니다. seed가 증가해도 이 설정에는 그 seed로 바꿀 무작위 속성이 없습니다.

## 2. 초점거리와 화각 연결하기

카메라의 **화각**은 한 번에 볼 수 있는 각도 범위입니다. 초점거리와 aperture는 함께 화각을 정합니다.

```text
가로 화각 = 2 × atan(horizontal_aperture / (2 × focal_length))
```

두 광학 길이는 같은 단위로 비교합니다. 이것들을 500 cm인 카메라 위치와 같은 종류의 거리 값으로 혼동하지 마세요. 해상도는 픽셀 수이고, 초점거리와 aperture의 비율은 시야의 넓이입니다.

| 파라미터 조합 | 가로 화각 | 이 장면에서 보이는 차이 |
|---|---:|---|
| aperture 24 / focal 24 | 약 53.1° | 주변 공간까지 넓게 보임 |
| aperture 24 / focal 48 | 약 28.1° | 중앙 큐브가 커지고 주변이 잘림 |

같은 깊이에 있는 물체의 영상 크기는 초점거리에 비례합니다. 가로 640픽셀·aperture 24인 카메라에서 focal 24는 가로 기준 초점거리 640픽셀, focal 48은 1280픽셀에 해당합니다. 그래서 동일한 큐브가 두 배 크기로 투영됩니다. 카메라 위치가 같으므로 두 영상의 차이를 스테레오 카메라의 시차라고 부르지는 않습니다.

### 설정에서 볼 부분

`near_clip: 1`과 `far_clip: 5000`은 카메라 앞에서 렌더링할 거리 구간입니다. 큐브는 한 변 100 cm라 카메라에 가까운 면은 약 450 cm, 먼 면은 약 550 cm에 있습니다. 이 구간이 기본 절단 범위 안에 들어갑니다.

만약 near clip을 너무 크게 바꾸면 물체 표면이 잘리거나 사라질 수 있습니다. 물체가 어둡거나 초점이 흐려지는 효과와는 구분하세요. clip은 표시할 공간을 자르는 설정입니다.

이를 확인하려면 `scene.yaml`을 `clipped.yaml`로 복사하고 **전역 `camera_parameters.near_clip`만 1에서 550으로** 바꾸세요. `zoom_camera` 안의 near clip은 1로 유지합니다.

```bash
~/isaacsim/python.sh run.py --config clipped.yaml --launch --headless --frames 3
```

기본 카메라에서는 큐브의 가까운 표면이 절단 범위 밖으로 밀려나 잘리거나 사라집니다. 550 cm는 먼 면의 경계에 해당하므로 경계면의 표시 여부보다, 기존의 온전한 큐브가 유지되지 않는지를 보세요. 줌 카메라는 자체 clip 범위를 사용하므로 이전처럼 큐브를 촬영합니다. 두 영상의 차이가 광량이나 물체 이동 때문인지 추측하기 전에, 같은 seed의 description에서 각 카메라의 `near_clip`을 대조해 보세요.

### 실행 결과 확인하기

GUI로 카메라 위치를 확인하려면 앞의 실행을 종료한 뒤 다음 명령을 사용합니다.

```bash
~/isaacsim/python.sh run.py --launch --frames 3
```

**Tools > Action and Event Data Generation > Object SDG**에서 이번 `configuration:` 경로를 **Description File**에 넣고 초기화하세요. Stage의 `/World/Cameras` 아래 두 카메라를 각각 선택해 변환을 비교합니다. **Simulate**가 데이터를 저장하고, GUI는 생성 후에도 유지됩니다. 원래 작업 중인 stage는 초기화 전에 저장해 두세요.

**초기화 미리보기의 카메라 속성만으로 초점거리·clip 적용을 판정하지 마세요.** 설치 IRO 0.4.13의 미리보기 카메라는 위치·방향을 반영하지만, 해당 prim에 YAML의 광학 파라미터를 설정하지 않습니다. 실제 생성에서는 별도의 Replicator 카메라에 이 값들을 전달합니다. 광학 효과는 저장 RGB로, 입력값은 `prepared.yaml`과 저장 description으로 확인해야 합니다.

저장 description에서는 카메라별 `camera_parameters`를 대조할 수 있습니다. 변환 연산은 저장 시 최종 행렬로 합쳐지므로 두 카메라의 위치가 같은지는 `global_transform`으로 확인합니다.

## 3. 카메라 설정의 역할 정리

```text
위치·방향 → 어디에서 어느 쪽을 볼지
focal_length / aperture → 얼마나 좁거나 넓게 볼지
screen_width / screen_height → 그 시야를 몇 픽셀로 기록할지
near_clip / far_clip → 어느 거리 구간을 표시할지
```

초점거리로 물체를 크게 만들면 카메라 위치는 그대로여도 시야가 좁아집니다. 단순히 이미지 해상도를 높이는 것과 효과가 다른 이유입니다.

## 4. 간단한 확인 실험

`scene.yaml`을 `wide.yaml`로 복사하고 **전역 `camera_parameters.horizontal_aperture`만 24에서 48로** 바꾸세요. `zoom_camera` 안의 값은 그대로 둡니다.

```bash
~/isaacsim/python.sh run.py --config wide.yaml --launch --headless --frames 3
```

기본 카메라의 화각은 약 90°로 넓어지고 큐브 너비는 원래의 약 절반이 됩니다. 자체 파라미터를 가진 줌 카메라는 기존 화각을 유지합니다. 두 카메라가 함께 바뀌었다면 편집 위치를 다시 확인해 보세요.

## 실행할 때 막히면

- **이미지가 3장만 보임**: 파일명 필터와 `zoom_camera` 설정을 확인하세요. 한 카메라의 파일만 세고 있지 않은지 살펴봅니다.
- **전역 값을 바꿨는데 줌 카메라가 그대로임**: 줌 카메라가 자체 파라미터 사전을 가진 결과입니다. 변경 전후 description을 대조하세요.
- **초기화한 카메라의 focal length가 YAML과 다름**: IRO 0.4.13 미리보기의 제한입니다. **Simulate**로 저장한 영상과 description에서 비교하세요.
- **카메라를 +Z에 뒀는데 큐브가 안 보임**: -Z 시선, Y 높이 50 cm, clip 범위를 확인하세요. 기본 장면은 Y-up입니다.
- **연속 프레임이 거의 같음**: 이 설정의 물체와 조명은 고정되어 있습니다. 같은 seed의 카메라 두 장 사이 차이를 비교하세요.
- **로딩 중 종료됨**: `--steps`를 제거하세요. 데이터 수는 `--frames`로 정합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/camera.html)에 대응합니다. 동일 위치의 두 pinhole 카메라로 초점거리·화각·clip을 비교하며, 렌즈 왜곡이나 스테레오 깊이 복원은 다루지 않습니다.

문서의 화각과 크기 비율은 설정에서 계산한 확인 기준입니다. 실제 영상 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
