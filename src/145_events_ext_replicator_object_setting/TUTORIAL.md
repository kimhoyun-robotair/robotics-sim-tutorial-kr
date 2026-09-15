# 145. 같은 장면에서 어떤 데이터를 저장할지 정하기

## 이번에 배우는 것

**큐브 장면은 유지하면서 해상도·출력 스위치·seed가 결과 파일을 어떻게 바꾸는지 비교합니다.**

물체를 더 많이 만드는 것과 데이터를 더 많이 저장하는 것은 다른 선택입니다. RGB만 필요한 작업과 깊이·분할 정답도 필요한 작업은 같은 장면을 사용해도 출력 구성이 달라집니다. 이번에는 두 개의 완전한 YAML 설정을 비교하며 장면 전역 설정이 카메라와 writer까지 전달되는 흐름을 살펴봅니다.

| 비교 항목 | `scene.yaml` | `rgb_only.yaml` |
|---|---|---|
| RGB 해상도 | 640×480 | 320×240 |
| RGB·description | 저장 | 저장 |
| 2D·3D 라벨, 분할 | 저장 | 저장 안 함 |
| 깊이·법선 | 저장 | 저장 안 함 |
| 큐브 배치·회전 규칙 | 동일 | 동일 |

두 설정 모두 물리 시간과 중력이 0입니다. 큐브는 중심 `(0,50,0)` cm에 머물고 Y 회전만 -90~90도에서 선택됩니다. 여기서 Y는 위쪽이며 1단위는 1 cm입니다.

## 1. 기본 출력 만들기

Isaac Sim 5.1과 RTX GPU 환경에서 실행합니다. 저장소 루트에서 아래 폴더로 이동하세요.

```bash
cd src/145_events_ext_replicator_object_setting
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

`run.py`는 새 `output/<UTC시간>-<고유값>/`에 `prepared.yaml`을 만든 다음 실제 IRO 확장을 실행합니다. 정상 생성이 끝나면 창 없이 종료합니다. `--launch`를 빼면 YAML 준비만 수행합니다. 설치 위치가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 바꾸세요.

### 설정에서 볼 부분

```yaml
screen_width: 640
screen_height: 480
camera_parameters:
  screen_width: $[/screen_width]
  screen_height: $[/screen_height]
  focal_length: 24
  horizontal_aperture: 24
  near_clip: 1
  far_clip: 5000
```

`$[/screen_width]`의 `/`는 설정 루트에서 값을 찾는다는 뜻입니다. 카메라에 640을 다시 적는 대신 전역 값을 참조하므로, 출력 해상도를 바꿀 때 카메라의 영상 크기도 같이 바뀝니다. 준비 단계에서는 이 참조가 남고 IRO가 실행될 때 숫자로 해석됩니다.

`output_switches`에서는 `images`, `labels`, `3d_labels`, `segmentation`, `descriptions`, `depth`, `normal`이 켜져 있습니다. 각 키는 **별도 종류의 결과를 저장할지** 정합니다. 렌더링한 RGB 한 장에서 깊이나 법선을 자동으로 추정해 만드는 설정으로 이해하지 마세요. IRO가 해당 센서·주석 출력을 함께 기록합니다.

### 실행 결과 확인하기

콘솔의 `output:` 경로를 열고 `images/`의 RGB 세 장이 640×480인지 확인하세요. `labels/`, `3d_labels/`, `segmentation/`, `depth/`, `normal/`, `descriptions/`도 대조합니다. 라벨은 빨간 큐브와 `tracked: true`인 바닥을 포함할 수 있습니다.

깊이와 법선은 각각 `depth/`·`normal/`의 `.npy` 배열로 저장됩니다. 깊이에는 `distance_to_image_plane`이 사용됩니다. 카메라의 앞쪽 축을 따른 깊이이므로, 화면 가장자리까지 카메라 중심에서 잰 직선거리와는 다릅니다. 법선은 표면 방향 정보이며 RGB의 밝기를 깊이나 표면 방향으로 해석하면 안 됩니다.

IRO의 저장 코드는 깊이 배열의 양의 무한대와 NaN을 0으로 바꿉니다. 따라서 배경 등에 있는 0을 카메라에 붙어 있는 표면으로 해석하지 마세요. 먼저 RGB와 깊이 배열의 같은 픽셀을 짝지어 물체 영역과 유효하지 않은 영역을 구분해 봅니다.

## 2. 작은 RGB와 description만 저장하기

앞의 실행이 끝난 뒤 같은 터미널에서 비교 설정을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config rgb_only.yaml --launch --headless --frames 3
```

이번 실행의 새 `output:` 경로를 확인하세요. 이름이 `rgb_only`여도 **description은 유지**됩니다. 영상만 보고는 난수 회전을 구분하기 어려울 수 있으므로 장면 기록을 함께 남긴 구성입니다.

### 설정에서 볼 부분

```yaml
output_name: frame_$[seed]_$(camera_name)
output_switches:
  images: true
  labels: false
  3d_labels: false
  segmentation: false
  descriptions: true
  depth: false
  normal: false
```

이 코드는 주요 스위치만 발췌한 것입니다. 전체 `rgb_only.yaml`은 그 밖의 출력도 명시적으로 끕니다. **키를 삭제하는 것과 `false`로 지정하는 것은 다릅니다.** 설치 IRO는 생략된 키에 기본값을 적용하며, 깊이·법선·라벨 등에는 켜진 기본값이 있습니다. 필요 없는 결과를 확실히 제외하려면 제공 파일처럼 해당 스위치를 `false`로 유지하세요.

파일명은 두 단계로 완성됩니다. IRO가 `$[seed]`를 프레임 seed로 바꾸고, writer가 `$(camera_name)`을 카메라 이름으로 바꿉니다. 시작 seed가 11이고 세 프레임이면 RGB 이름은 `frame_11_default_camera.jpg`부터 seed 12·13으로 이어집니다. 전체 장면 description은 `frame_11_GLOBAL.yaml`처럼 저장됩니다.

### 실행 결과 확인하기

| 관찰 지점 | 비교할 내용 |
|---|---|
| `prepared.yaml` | 전역 해상도 320×240, 출력 스위치의 참·거짓 |
| `images/` | 실제 RGB 크기 320×240, 기본 실행과 대응하는 seed |
| `descriptions/`의 카메라 설정 | 해석된 `screen_width: 320`, `screen_height: 240` |
| 기타 출력 | 꺼 둔 라벨·분할·깊이·법선 파일이 생성되지 않는지 |

가로·세로가 각각 절반이면 픽셀 수는 307,200개에서 76,800개로 4분의 1이 됩니다. 화각에 사용하는 초점거리와 aperture는 같으므로 해상도 감소를 줌아웃으로 해석하지 마세요. 같은 장면을 더 적은 픽셀로 표현합니다.

GUI로 확인하려면 `--headless`를 빼고 실행한 뒤 **Tools > Action and Event Data Generation > Object SDG**의 **Description File**에 이번 `configuration:` 경로를 넣고 **Simulate**를 누르세요. GUI는 생성 후에도 유지됩니다. `--steps`는 앱 업데이트 제한이므로 데이터 수를 정할 때는 `--frames`를 사용합니다.

## 3. 설정이 결과로 전달되는 과정 정리

```text
전역 해상도 → 카메라 파라미터 참조 → 실제 영상의 픽셀 수
output_switches → writer의 저장 종류 → 결과 폴더 구성
시작 seed + 프레임 순서 → 난수 선택과 파일명 → 대응 장면 비교
```

저장 description의 물체 변환은 IRO 0.4.13에서 최종 `global_transform`과 단일 `transform` 행렬로 정리됩니다. 원래 `rotateY` 항목을 찾기보다 같은 seed의 변환 행렬을 비교하세요. `prepared.yaml`은 규칙, description은 촬영 시점의 장면 기록입니다.

## 4. 간단한 확인 실험

기본 명령에서 **시작 seed만 12로** 바꿔 보세요.

```bash
~/isaacsim/python.sh run.py --launch --headless --frames 3 --seed 12
```

이 실행의 첫 프레임을 seed 11 실행의 두 번째 프레임과 비교합니다. 같은 장면 설정과 환경에서는 seed 12에 대응하는 물체 변환을 확인할 수 있습니다. 먼저 description의 `global_transform`을 대조하고 RGB를 보세요. 서로 다른 GPU·렌더 설정 사이의 픽셀 완전 일치를 재현성의 기준으로 삼지는 않습니다.

## 실행할 때 막히면

- **작은 RGB 실행에도 라벨이 보임**: 이전 출력 폴더를 열지 않았는지 확인하세요. 호출마다 새 경로를 출력합니다.
- **전역 해상도를 바꿨는데 카메라 값이 그대로임**: 카메라 파라미터를 숫자로 덮어썼는지 확인하세요. 제공 설정은 루트 해상도를 참조합니다.
- **파일명에 `$(camera_name)`이 남음**: `prepared.yaml`에서는 정상입니다. writer가 저장하는 최종 이미지 이름에서 치환 여부를 확인하세요.
- **`--output`에서 경로 존재 오류**: 이 도구는 기존 폴더를 덮어쓰지 않습니다. 새 경로를 지정하거나 기본 출력을 사용하세요.
- **RGB가 생성되기 전에 종료됨**: 앱 업데이트를 제한하는 `--steps`를 제거하고 다시 생성하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Setting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/setting.html)에 대응합니다. 설정 상속까지 확장하기 전에 출력 차이를 비교하도록 두 YAML에 전체 설정을 넣었습니다. 현재 `run.py`는 `parent_config`가 있는 입력을 거부합니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 2026-09-14 기본 설정 한 프레임의 640×480 이미지, 주석 2개, 깊이·법선 출력 확인이 기록되어 있습니다. 설정 파일은 기록 당시와 같지만 현재 `run.py`는 그 뒤 변경되었습니다. 따라서 이 기록은 당시 실행 조건에 한정되며 현재 실행 파일·비교 설정·GUI 전체의 검증을 뜻하지 않습니다. `tutorial.json`의 검증 범위를 함께 참고하세요.
