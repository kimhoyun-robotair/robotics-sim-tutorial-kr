# 75. 한 프레임의 점군과 한 회전의 스캔 비교하기

## 이번에 배우는 것

**하나의 Lidar에 두 annotator를 연결하고, 같은 순간에 읽은 배열도 서로 다른 시간 구간을 담을 수 있다는 점을 확인합니다.**

회전형 Lidar는 여러 방향을 순서대로 스캔합니다. 지금 들어온 반환만 필요할 때도 있고, 한 회전의 데이터를 모아 주변을 보고 싶을 때도 있습니다. 이번에는 센서와 장면을 그대로 둔 채 데이터를 모으는 방식만 비교합니다.

| 구분 | 현재 프레임 점군 | 누적 스캔 버퍼 |
|---|---|---|
| Annotator | `IsaacExtractRTXSensorPointCloudNoAccumulator` | `IsaacCreateRTXLidarScanBuffer` |
| 관찰 대상 | 지금 프레임의 반환 | 회전 중 여러 프레임에 걸친 스캔 |
| 추가 요청 | 기본 점군 | 거리·강도·timestamp |
| 파일 저장 | 마지막 시점의 배열 | 마지막 시점의 누적 배열 |

센서는 높이 1 m에 있고 사방 5 m 위치의 상자 네 개와 바닥을 읽습니다. 장면이 정적이므로 물체 이동에 의한 차이보다 **버퍼가 담는 시간 범위**에 집중할 수 있습니다.

## 1. 두 annotator를 함께 실행하기

Isaac Sim 5.1.0과 RTX GPU 환경에서 저장소 루트 기준으로 실행하세요.

센서는 기본 `Example_Rotary` 설정을 사용하며 Isaac 에셋 루트의 `/Isaac/Sensors/NVIDIA/Example_Rotary.usda`에 접근해야 합니다. 방의 표적은 코드가 만들지만 센서 설정 자산까지 이 폴더에 포함된 것은 아닙니다.

```bash
~/isaacsim/python.sh src/75_sensors_sensors_rtx_annotators/run.py --steps 240
```

240단계 뒤 `annotators.npz`와 `measurements.json`을 저장하고 종료합니다. 출력은 이 폴더의 `output/날짜_시간/`이며 터미널에 실제 경로를 표시합니다. `--headless`를 추가하면 창 없이 렌더링합니다. `--steps`를 생략한 GUI는 최초 저장 뒤 계속 실행하지만 파일은 갱신하지 않습니다.

### 코드에서 볼 부분

두 처리기는 같은 `sensor`에 붙습니다.

```python
names = ['IsaacExtractRTXSensorPointCloudNoAccumulator',
         'IsaacCreateRTXLidarScanBuffer']
sensor.attach_annotator(names[0])
sensor.attach_annotator(names[1], outputTimestamp=True,
                      outputDistance=True, outputIntensity=True)
```

두 번째 호출의 옵션은 누적 버퍼에서 추가 배열을 요청합니다. 점의 위치만 비교하면 측정 시점이 섞인 사실을 놓칠 수 있으므로 timestamp도 함께 요청한 것입니다.

매 반복에서는 `world.step(render=True)` 뒤 `sensor.get_current_frame()`을 한 번 읽습니다. 반환 사전에는 annotator 이름을 키로 하는 각 데이터가 있습니다. `counts`는 두 `data` 배열의 첫 번째 차원, 즉 점 수를 기록합니다.

## 2. 저장된 배열과 이력을 함께 읽기

### 실행 결과 확인하기

`measurements.json`의 두 항목부터 확인하세요.

- `counts`: 240번 읽은 각 시점의 두 annotator 점 수
- `arrays`: 마지막 시점에 저장한 NumPy 배열의 이름과 크기

`annotators.npz`는 여러 배열을 하나로 묶은 파일입니다. 다음 코드를 NumPy가 있는 Python에서 실행하면 어떤 배열이 실제 저장됐는지 확인할 수 있습니다. 경로는 자신의 출력 경로로 바꾸세요.

```python
from pathlib import Path
import numpy as np

result_dir = Path("src/75_sensors_sensors_rtx_annotators/output/실제_출력_폴더")
with np.load(result_dir / "annotators.npz") as saved:
    for key in saved.files:
        print(key, saved[key].shape, saved[key].dtype)
```

배열 이름은 `annotator이름__원래키` 형식입니다. 예를 들어 `IsaacCreateRTXLidarScanBuffer__data`는 누적 버퍼의 점군입니다. 같은 접두사의 `distance`, `intensity`, `timestamp` 배열도 찾아보세요. 코드는 데이터 사전의 NumPy 배열만 저장하므로, 반환된 모든 메타데이터가 NPZ에 들어가는 것은 아닙니다.

| 추가 배열 | 단위·범위 | 읽을 때 확인할 점 |
|---|---|---|
| `distance` | m | 각 반환의 거리입니다. |
| `intensity` | 0~1 | 센서 반환 강도이며 RGB 밝기가 아닙니다. |
| `timestamp` | ns | 나노초 단위의 센서 시각입니다. 차이를 초로 읽을 때는 10억으로 나눕니다. |

### 코드에서 볼 부분

저장은 반복문이 끝난 **뒤**에 이루어집니다.

```python
for key, value in data.items():
    if isinstance(value, np.ndarray):
        arrays[name + '__' + key] = value
```

따라서 `counts`는 전체 수집 이력이지만 NPZ는 마지막 시점의 스냅샷입니다. 이 둘을 혼동하면 “240프레임의 점군을 모두 저장했다”고 잘못 해석하기 쉽습니다.

현재 프레임과 누적 버퍼 모두 마지막 `data`가 비어 있지 않아야 저장 단계가 통과합니다. 초기 몇 프레임의 0은 전체 이력 속에서 해석하고, 처음부터 마지막까지 모두 비었는지와 구분하세요. 뷰포트 점군 표시용 writer는 붙이지 않았으므로 화면의 점 개수를 결과로 세지 않습니다.

## 3. 배열의 시간 범위 정리

기본 스캔은 10 Hz, 렌더 간격은 1/60초입니다. 한 회전은 설정상 약 6개의 렌더 간격에 걸칩니다.

```text
시간 →       프레임 1   프레임 2   프레임 3   ...
현재 점군       A          B          C
누적 버퍼     회전 진행에 따라 여러 프레임의 반환을 포함
파일 저장                         수집 마지막 시점에 한 번
```

누적 배열이 더 많은 점을 담는다고 센서 자체의 정확도가 올라간 것은 아닙니다. **얼마나 오랜 시간의 반환을 함께 보고 있는지**가 달라집니다. 센서나 물체가 움직이는 장면에서는 과거 위치의 점이 섞일 수 있으므로, 배열을 읽은 시각이 같다고 모든 점의 측정 시각도 같다고 보지 마세요.

Timestamp는 로그의 `App Ready` 시점부터 증가하는 센서 내부 시계를 사용합니다. 애니메이션 timeline과 별개이므로 Pause 중에도 시간이 이어지고, 재생을 재개한 뒤 받은 점들의 timestamp 사이에 간격이 생길 수 있습니다. ns 값을 초로 환산하더라도 `world.current_time`과 같은 시작점이라고 가정하지 마세요.

좌표도 같은 방식으로 기준을 확인합니다. 두 점군의 `data`는 m 단위이며, 센서의 `omni:sensor:Core:outputFrameOfReference`가 `SENSOR`인지 `WORLD`인지 먼저 읽으세요. 누적 버퍼에 보조 `transform`이 반환되더라도 이는 마지막 스캔 시점의 센서→월드 변환이지 모든 점의 개별 취득 자세를 담은 이력은 아닙니다.

## 4. 간단한 확인 실험

스캔 속도만 5 Hz로 줄여 실행합니다.

```bash
~/isaacsim/python.sh src/75_sensors_sensors_rtx_annotators/run.py --steps 240 --scan-hz 5
```

한 회전 시간은 0.2초로 늘어 설정상 약 12개의 렌더 간격에 해당합니다. 두 실행의 `counts`를 순서대로 읽으며 현재 프레임 점 수와 누적 점 수의 변화 양상을 비교하세요. 마지막 점 수 하나만 보면 회전 중 어느 시점에 종료했는지의 영향을 놓칠 수 있습니다.

비교할 때 `--steps`와 센서 모델은 유지합니다. 누적 점 수가 정확히 두 배가 되거나 두 annotator 사이의 비율이 항상 같을 필요는 없습니다.

## 실행할 때 막히면

- **`No data in ...`**: 종료 시 해당 annotator의 점군이 비었습니다. 아주 짧은 실행 대신 준비와 회전을 포함할 만큼 렌더링하고, timeline과 센서 설정을 확인하세요.
- **배열이 계속 그대로임**: GUI가 Pause 상태인지 확인하세요. 파일은 최초 저장 후 바뀌지 않으므로 새 수집은 새 실행으로 비교합니다.
- **NPZ의 키를 찾지 못함**: 짧은 이름만 추측하지 말고 `saved.files`로 실제 `annotator이름__키`를 확인하세요.
- **GPU 버퍼 설정을 바꾼 뒤 반환이 없음**: CPU에서 NumPy를 읽는 것과 RTX 내부 출력 버퍼 위치는 다른 문제입니다. 임의로 바꾼 센서 GPU 버퍼 설정을 기본값으로 복구한 뒤 다시 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)에 대응합니다. 두 처리기의 시간 범위를 비교하기 위한 정적 장면과 NPZ 기록을 추가했습니다. 평면 스캔, object ID 해석, 법선·속도와 같은 고급 출력은 별도 설정이 필요한 원문의 확장 범위입니다.

코드와 자료를 대조했으며 이번 개정에서는 RTX 실행을 하지 않았습니다. `tutorial.json`은 `not_run`이고, 배열 크기와 점 수는 사용 환경에서 실제 결과로 확인해야 합니다.
