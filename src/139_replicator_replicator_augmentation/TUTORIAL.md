# 139. 장면을 바꾸지 않고 센서 데이터를 증강하기

## 이번에 배우는 것

**동일한 캡처의 원본과 증강 배열을 비교하고, RGB 채널 교환과 거리 노이즈의 효과를 수치로 확인합니다.**

조명이나 물체 자세를 바꾸는 것은 장면의 변화입니다. 데이터 증강은 이미 얻은 센서 배열을 변환합니다. 빨간 상자가 증강 이미지에서 파랗게 보여도 USD 재질이 바뀐 것은 아닙니다. 이번 코드는 원본을 함께 저장해 이 차이를 직접 비교할 수 있게 합니다.

| 선택 | 데이터가 바뀌는 위치 |
|---|---|
| `--mode annotator` | RGB·거리 annotator 뒤에 변환을 붙이고 직접 읽습니다. |
| `--mode writer` | Writer가 저장하는 RGB·거리 경로에 변환을 붙입니다. |
| `--backend numpy` | NumPy 함수가 CPU 배열을 계산합니다. |
| `--backend warp` | Warp 커널이 픽셀별 연산을 수행합니다. |
| `filters.py` | 채널 교환과 노이즈 함수·커널의 실제 구현입니다. |

캡처 사이 Cube의 회전은 별도로 무작위화됩니다. 따라서 원본과 증강은 반드시 **같은 프레임 번호끼리** 비교해야 합니다.

## 1. 원본과 증강 결과를 나란히 저장하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트에서 실행하세요. NumPy·Pillow·Warp는 설치에 포함된 환경을 사용합니다.

```bash
~/isaacsim/python.sh src/139_replicator_replicator_augmentation/run.py --mode annotator --backend numpy --headless --frames 3 --sigma 0.1 --output /tmp/tutorial139-annotator
```

출력은 아직 없는 폴더로 지정합니다. 320×240 해상도로 세 번 촬영한 뒤 종료합니다. `--headless`를 빼면 저장 후 창을 유지하며 닫으면 종료합니다. GUI의 `--steps N`은 생성 후 관찰용 앱 갱신 수입니다. 데이터 프레임 수는 `--frames`가 정합니다.

### 코드에서 볼 부분

먼저 채널 교환 함수를 보세요.

```python
def swap_red_blue(data_in):
    result = data_in.copy()
    result[..., 0], result[..., 2] = data_in[..., 2], data_in[..., 0]
    return result
```

RGBA 배열에서 0번은 빨강, 2번은 파랑입니다. 원본 복사본에 값을 써서 다른 데이터 경로가 읽을 수 있는 입력을 보존합니다. 초록과 알파 채널은 유지합니다.

거리 노이즈는 다음과 같습니다.

```python
noise = np.random.default_rng(seed).normal(0, sigma, data_in.shape)
return np.maximum(data_in + noise, 0).astype(data_in.dtype)
```

`sigma`는 거리 오차의 표준편차이며 단위는 m입니다. 음수 거리를 만들지 않도록 0으로 제한합니다. 같은 증강 정의를 사용하되 두 번째 거리 annotator에서는 `sigma`를 다섯 배로 덮어씁니다.

### 실행 결과 확인하기

| 파일 또는 JSON 값 | 읽을 내용 |
|---|---|
| `0000_original.png`, `0000_bgr.png` | 빨강·파랑 교환 전후를 비교합니다. |
| `0000_depth_original.npy` | 원본 카메라-표면 거리이며 미터 값을 보존합니다. |
| `0000_depth_small.npy`, `0000_depth_large.npy` | 기본 sigma 0.1 m와 0.5 m의 증강 결과입니다. |
| `red_blue_swap_exact` | 같은 원본의 채널 순서를 바꾼 배열과 정확히 일치하는지 검사합니다. |
| `small_noise_std_m`, `large_noise_std_m` | 유한 거리 픽셀에서 원본과의 차이를 측정한 표준편차입니다. |

`distance_to_camera`는 표면까지의 직선 거리입니다. 카메라 광축 방향 깊이인 `distance_to_image_plane`과 구분하세요. 배경 `inf`는 표면을 얻지 못한 픽셀이므로 차이의 통계에서 제외합니다.

설정 sigma가 0.1과 0.5라고 측정 표준편차가 모든 실행에서 정확히 그 값이어야 하는 것은 아닙니다. 유한 표본 수와 0 제한의 영향을 받습니다. 채널 교환은 배열의 정확한 일치로 검사하지만 거리 노이즈는 실제 분포의 크기로 읽는 이유입니다.

## 2. Writer의 저장 경로에 증강 연결하기

```bash
~/isaacsim/python.sh src/139_replicator_replicator_augmentation/run.py --mode writer --backend numpy --headless --frames 3 --sigma 0.1 --output /tmp/tutorial139-writer
```

최상위 파일은 이 모드에서도 원본입니다. 증강된 결과는 `writer/` 아래 BasicWriter의 RGB와 거리 출력에 있습니다. Writer 모드의 `measurements.json`은 프레임과 원본 shape를 기록하며, annotator 모드의 채널 교환 검사나 small/large 통계까지 만들지는 않습니다.

### 코드에서 볼 부분

```python
composed = rep.annotators.get('rgb').augment_compose([hsv, noise, rgb], name='rgb')
writer.add_annotator(composed)
writer.augment_annotator('distance_to_camera',
    rep.AnnotatorRegistry.get_augmentation('lesson_depth_noise'))
```

RGB는 색 공간을 HSV로 바꾸고 채널에 노이즈를 더한 다음 다시 RGB로 되돌립니다. 앞 변환의 결과가 다음 변환의 입력이므로 순서가 중요합니다. `name='rgb'`로 Writer의 RGB 항목에 이 경로를 연결합니다.

Writer RGB 노이즈의 sigma는 코드에 `6.0`으로 설정되어 있습니다. CLI의 **`--sigma`는 두 모드 모두 거리 노이즈만 조절**합니다. `--sigma 0`을 주어도 Writer의 RGB 노이즈가 사라지는 것은 아닙니다.

GPU 경로를 확인하려면 같은 명령에서 `--backend warp`로 바꾸고 새 출력 경로를 사용하세요. Warp는 `data_out`에 픽셀별 결과를 기록합니다. 같은 seed라도 NumPy와 Warp는 난수 생성 방식이 달라 픽셀별 노이즈가 똑같아야 하는 것은 아닙니다.

노이즈 함수의 `seed`가 매번 CLI의 숫자를 그대로 받는 것도 아닙니다. 설치된 Replicator 1.12.27의 CPU·GPU augmentation 노드는 `seed` 인자를 특별히 처리하여 내부 난수 흐름에서 뽑은 정수를 각 compute에 전달합니다. 따라서 함수 안에서 `default_rng(seed)`를 만들어도 고정 `--seed`가 같은 잡음 이미지를 매 프레임 반복한다는 뜻은 아닙니다. 반복 실행을 비교할 때는 seed와 함께 backend·그래프 구성·캡처 순서를 유지하고 실제 저장 배열을 대조하세요.

## 3. 장면 무작위화와 데이터 증강의 차이 정리

```text
Cube 회전 변경 → 렌더 → 원본 RGB·거리
                       ├→ 그대로 저장
                       └→ 채널 교환 / 노이즈 / 색 공간 변환 → 증강 저장
```

두 경로를 같은 캡처에서 읽으므로 차이를 장면 변화와 혼동하지 않고 측정할 수 있습니다. `Augmentation.from_function()`은 함수나 커널을 Replicator 처리 흐름에 연결하고, `wait_until_complete()`는 Writer의 파일 쓰기가 끝날 때까지 기다립니다. `.npy`를 사용하는 이유는 거리값을 보기 좋은 8비트 색으로 바꾸지 않고 보존하기 위해서입니다.

## 4. 간단한 확인 실험

첫 annotator 명령에서 **`--sigma`만 0으로 바꾸어** 새 폴더에 실행하세요.

- 유한 거리 픽셀에서 small·large의 원본 대비 차이는 0이어야 합니다.
- `small_noise_std_m`, `large_noise_std_m`도 0을 기준으로 확인합니다.
- 빨강·파랑 교환은 그대로 유지되어 `red_blue_swap_exact`는 참이어야 합니다.

이 실험은 거리 변환과 색 변환이 독립된 경로라는 점을 확인합니다. 배경의 `inf - inf`는 0이 아니라 유효하지 않은 계산이므로 비교 대상에서 제외하세요.

## 실행할 때 막히면

- **`Renderer returned empty annotator data`**: 카메라·render product 연결과 렌더 오류를 확인하세요. 빈 배열은 증강의 성공 결과가 아닙니다.
- **유한 거리 픽셀이 없음**: 카메라가 실제 표면을 바라보는지 확인하세요. 배경만 비교해 노이즈를 계산할 수 없습니다.
- **Warp 또는 ScriptNode 오류**: Isaac Sim 5.1에 포함된 확장 조합인지 확인하고 NumPy 경로와 오류 지점을 비교하세요.
- **Writer 모드에 bgr 파일이 없음**: Writer RGB는 HSV 노이즈 합성 경로를 사용합니다. annotator 모드의 출력 목록과 다릅니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Data Augmentation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_augmentation.html)에 대응합니다. 공식 annotator·Writer 증강 경로를 빨간 Cube와 자체 평면으로 구성했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 기존 NumPy annotator 한 프레임에서는 채널 교환 일치와 거리 오차 표준편차 약 0.1005 m·0.5024 m를 기록했습니다. 이는 해당 실행의 측정 사례이며 Warp·Writer·GUI 전체 검증은 아닙니다. 이번 문서 개정에서는 새 GPU 측정을 수행하지 않았습니다.
