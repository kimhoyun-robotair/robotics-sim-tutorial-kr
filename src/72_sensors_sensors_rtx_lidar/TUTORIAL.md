# 72. RTX Lidar의 점군은 어떻게 만들어지는가?

## 이번에 배우는 것

**사방에 놓인 상자를 RTX Lidar로 읽고, 센서 설정부터 마지막 점군 파일까지 데이터가 만들어지는 과정을 따라갑니다.**

Lidar가 장면에 있다는 것과 거리 측정값을 읽을 수 있다는 것은 서로 다른 단계입니다. 센서의 위치와 스캔 방식을 정한 다음, 렌더러가 계산한 결과를 Python 배열로 가져오는 연결이 필요합니다. 이 실습의 `LidarRtx`는 그 연결을 묶어 다루는 클래스입니다.

| 구성 | 이 실습의 값 | 확인할 의미 |
|---|---|---|
| 센서 | `/World/Lidar`, 높이 1 m | 거리를 관찰하는 위치 |
| 표적 | 사방 5 m 지점의 상자 네 개와 바닥 | 스캔할 장면 |
| 설정 | `Example_Rotary`, 10 Hz | 회전형 스캔과 초당 회전 수 |
| 읽기 방식 | `IsaacExtractRTXSensorPointCloudNoAccumulator` | 여러 프레임을 합치지 않은 점군 |
| 저장 파일 | `measurements.json`, `points.npy`, `scene.usda` | 반환 수 이력, 마지막 점군, 장면 |

표적 상자의 중심은 센서에서 수평으로 5 m 떨어져 있습니다. 상자에는 두께가 있으므로 센서가 만나는 표면까지의 거리가 모두 정확히 5 m인 것은 아닙니다.

## 1. 먼저 점군을 저장하기

Isaac Sim 5.1.0과 RTX 렌더링을 지원하는 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

기본 센서 설정은 Isaac 에셋 루트의 `/Isaac/Sensors/NVIDIA/Example_Rotary.usda`를 참조합니다. 표적은 코드로 만들지만 이 센서 USD와 참조 파일은 접근 가능해야 합니다. 이름 `Example_Rotary`가 Python 안에 등록되어 있다는 사실만으로 자산이 이 폴더에 포함되는 것은 아닙니다.

```bash
~/isaacsim/python.sh src/72_sensors_sensors_rtx_lidar/run.py --steps 240
```

240단계를 렌더링하고 결과를 저장한 뒤 앱이 종료됩니다. 창 없이 수집하려면 `--headless`를 추가합니다. **Headless에서도 RTX 센서는 렌더링이 필요합니다.** 창 표시만 생략합니다.

출력은 이 폴더의 `output/날짜_시간/`에 생기며 터미널에 `Output:` 경로가 나옵니다. `--output`으로 경로를 지정할 수도 있지만, 이미 존재하는 폴더는 거부합니다. GUI를 계속 관찰하려면 `--steps 240`을 빼세요. 처음 240단계의 결과를 한 번 저장한 뒤 창을 닫을 때까지 실행하고, 저장 파일은 더 이상 갱신하지 않습니다.

### 코드에서 볼 부분

`run.py`에서 센서를 초기화한 직후의 연결을 살펴보세요.

```python
world.reset()
sensor.initialize()
name = 'IsaacExtractRTXSensorPointCloudNoAccumulator'
sensor.attach_annotator(name)
```

`world.reset()`은 물리 장면을 초기화합니다. `sensor.initialize()`는 센서를 사용할 준비를 하고, `attach_annotator()`는 센서 출력을 읽을 처리기를 연결합니다. **Annotator**는 렌더러의 센서 버퍼를 사용자가 읽기 좋은 배열로 바꾸는 처리기입니다.

실제 데이터 수집은 반복문 안에서 이루어집니다.

```python
world.step(render=True)
data = sensor.get_current_frame().get(name, {})
points = np.asarray(data.get('data', np.empty((0, 3))))
counts.append(int(len(points)))
```

먼저 물리와 렌더 프레임을 진행한 뒤 데이터를 읽습니다. 아직 결과가 없으면 빈 배열을 사용하므로 초기 반환 수가 0일 수 있습니다. 센서 생성 호출만 끝내고 이 갱신을 생략하면 점군 수집까지 이루어진 것이 아닙니다.

### 실행 결과 확인하기

`measurements.json`에서 `returns_per_frame`의 길이가 240인지, 준비 구간 뒤에 양수인 반환 수가 생겼는지 확인하세요. `last_shape`는 `points.npy`의 배열 크기와 같아야 합니다.

저장된 경로를 아래 `result_dir`에 넣어 배열을 직접 열어 보세요. 이 코드는 NumPy가 있는 Python에서 실행합니다.

```python
from pathlib import Path
import numpy as np

result_dir = Path("src/72_sensors_sensors_rtx_lidar/output/실제_출력_폴더")
points = np.load(result_dir / "points.npy")
print("배열 크기:", points.shape)
print("처음 다섯 점:", points[:5])
```

`(N, 3)`은 점이 N개이고 각 점이 m 단위의 Cartesian 좌표 세 성분으로 표현되었다는 뜻입니다. Stage의 물체 위치와 직접 대조하려면 센서의 `omni:sensor:Core:outputFrameOfReference`도 확인하세요. `SENSOR`는 센서 기준, `WORLD`는 월드 기준, `CUSTOM`은 별도로 정의한 기준입니다. 이 장면은 센서가 높이 1 m에 있으므로 두 기준에서 Z의 원점부터 다릅니다.

이 파일은 **마지막 수집 프레임 하나**의 점군입니다. 240프레임 전체를 모은 점군으로 해석하지 마세요. 코드는 마지막 배열이 비어 있으면 오류를 내므로, 중간에 반환이 있었다는 것만으로 저장까지 성공하지는 않습니다.

## 2. Stage에서 센서와 스캔 설정 읽기

`--steps` 없이 새로 실행해 장면을 열어 둡니다. Stage에서 `/World/Lidar`를 선택하고 `OmniLidar` 타입과 `omni:sensor:Core:scanRateBaseHz` 속성을 확인하세요. `/World/Wall0`부터 `Wall3`까지는 움직이지 않는 표적입니다.

### 설정에서 볼 부분

센서 생성 시 다음 두 입력이 서로 다른 역할을 합니다.

```python
sensor = LidarRtx(
    '/World/Lidar', translation=np.array([0., 0., 1.]),
    orientation=np.array([1., 0., 0., 0.]),
    config_file_name=args.config,
    **{'omni:sensor:Core:scanRateBaseHz': args.scan_hz}
)
```

`args.config`의 기본값 `Example_Rotary`는 사용할 센서 구성을 선택합니다. `args.scan_hz`의 기본값 10은 그 센서의 스캔 속도를 지정합니다. `**`는 속성 이름과 값을 담은 사전을 키워드 인수로 전달하는 Python 문법입니다.

화면에 점이 보이지 않아도 바로 실패로 판단하지 마세요. 이 코드는 점군을 읽는 annotator를 연결하지만, 점을 뷰포트에 그리는 debug draw는 추가하지 않습니다. 장면은 Stage와 뷰포트에서, 측정은 JSON과 NumPy 배열에서 각각 확인합니다.

### 센서 패턴도 바꾸어 보기

설정 이름을 바꾸는 별도 실행도 가능합니다.

```bash
~/isaacsim/python.sh src/72_sensors_sensors_rtx_lidar/run.py --steps 240 --config Example_Solid_State
```

이 실행은 회전 속도 비교와 구분해 기록하세요. `--config`는 등록된 센서 모델을 선택하므로 방위·고도 방향의 발사 패턴 자체가 바뀔 수 있습니다. 새 JSON의 `config`와 점군 분포를 비교하고, Solid State 결과에 아래의 회전형 센서 한 회전 해석을 그대로 적용하지 않습니다. 이 설정도 대응하는 NVIDIA 센서 자산이 필요합니다.

## 3. 센서에서 파일까지 정리

```text
OmniLidar의 위치·스캔 속성
    → render product를 통한 RTX 계산
    → annotator에서 현재 점군 읽기
    → 매 프레임 점 수 기록
    → 마지막 점군만 points.npy에 저장
```

물리·렌더 간격은 모두 1/60초입니다. 10 Hz 회전이라면 한 회전의 시간은 0.1초이고, 설정상 약 6개의 렌더 간격에 해당합니다. 다만 초기 로딩과 스캔 경계가 있으므로 매 프레임의 점 수가 같거나 여섯 프레임마다 같은 숫자가 반복된다고 기대하지는 않습니다.

## 4. 간단한 확인 실험

스캔 속도만 20 Hz로 바꿔 실행해 보세요.

```bash
~/isaacsim/python.sh src/72_sensors_sensors_rtx_lidar/run.py --steps 240 --scan-hz 20
```

기본 실행과 `scan_hz`, `returns_per_frame`, `last_shape`를 비교하세요. 한 회전 시간은 0.05초로 줄지만, 저장 점 수가 정확히 두 배가 된다는 뜻은 아닙니다. 각 렌더 프레임이 어떤 스캔 구간을 담는지가 달라집니다. 센서 모델과 단계 수는 그대로 두어 속도 변경의 영향을 살펴보세요.

## 실행할 때 막히면

- **`No module named isaacsim`**: 일반 `python3` 대신 설치의 `python.sh`로 실행하세요.
- **`No returns from RTX Lidar`**: 마지막 프레임이 비었습니다. 240단계로 실행하고 센서 설정 로딩, timeline 재생, RTX GPU를 확인하세요. 아주 짧은 실행은 준비 구간만 읽을 수 있습니다.
- **센서 USD 참조를 찾지 못함**: Isaac 에셋 루트와 `Example_Rotary.usda` 접근을 확인하세요. 이 코드의 `--config`는 등록된 모델 이름이며 임의의 로컬 USD 절대 경로를 받는 옵션이 아닙니다.
- **출력 폴더가 이미 있다는 오류**: 새 `--output` 경로를 쓰거나 옵션을 생략해 자동 경로를 사용하세요.
- **창을 닫았는데 파일이 없음**: 수집 구간이 끝나기 전에 닫으면 저장 단계에 도달하지 못할 수 있습니다. `Output:` 메시지를 확인한 뒤 닫으세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)에 대응합니다. 원문의 센서 생성 개념에 네 표적과 프레임별 반환 수 기록을 더한 실습입니다. 모델별 자산과 구형 JSON profile 변환은 공식 문서의 별도 범위입니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 Headless 60단계 실행에서 `(41315, 3)` 점군을 얻은 기록이 있습니다. 그 숫자는 고정 정답이 아니며, 과거 코드의 결과이므로 현재 코드 전체의 검증을 대신하지 않습니다. 현재 GUI·다른 스캔 설정은 실행해 확인하지 않았습니다.
