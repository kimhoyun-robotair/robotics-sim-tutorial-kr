# 66. 같은 관절 토크를 서로 다른 시점으로 읽기

## 이번에 배우는 것

**60 Hz로 계산하는 팔의 토크를 10 Hz 센서값과 최신 물리값으로 읽고, 값뿐 아니라 측정 시점을 비교합니다.**

센서 로그에 행이 많다고 독립적인 측정도 그만큼 많다는 뜻은 아닙니다. 물리는 빠르게 진행되더라도 센서는 더 긴 주기로 값을 내보낼 수 있습니다. 이번에는 한 관절의 같은 토크를 두 방식으로 읽어 이 차이를 드러냅니다.

| 구분 | 기본 설정 또는 의미 |
|---|---|
| 물리 간격 | 1/60초, 초당 60단계 |
| 센서 주기 | `--period 0.1`, 0.1초마다 센서 시점 갱신 |
| `sampled_torque_Nm` | 센서 주기에 맞춘 시점의 토크 |
| `latest_torque_Nm` | 최신 물리 단계의 토크 |
| 측정 대상 | `/World/Arm/Joint`의 Y축 회전 effort |
| 결과 | `effort.json`에 물리 시각·센서 시각·두 토크를 함께 기록 |

정지한 팔만 보면 두 토크가 비슷해서 차이를 놓치기 쉽습니다. 팔이 처음 움직이는 구간을 시간 정보와 함께 살펴보겠습니다.

## 1. 두 읽기 방식을 한 파일에 기록하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/66_sensors_sensors_physics_effort/run.py --steps 240 --output src/66_sensors_sensors_physics_effort/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 코드가 높이 2 m의 고정 base와 길이 1.5 m 링크를 만듭니다. 목표각 0°의 관절 drive가 링크를 지지하며 240단계 동안 읽은 값을 저장하고 종료합니다.

새 출력 폴더를 지정하세요. 경로를 생략하면 이 튜토리얼의 `output/날짜_시간/`에 저장합니다. `--headless`를 추가하면 창 없이 실행합니다. `--steps 240`을 빼면 처음 240단계 기록을 저장한 뒤 GUI에서 계속 센서를 읽지만, JSON 행을 추가하지 않습니다.

### 실행 결과 확인하기

`effort.json`에서 `valid=true`인 행들을 연속해서 읽어 보세요.

| 필드 | 의미 | 비교할 부분 |
|---|---|---|
| `physics_time_s` | 현재 물리 시각 | 약 0.0167초씩 진행 |
| `sensor_time_s` | sampled 읽기가 가리키는 시각 | 기본 0.1초 주기에 따라 갱신 |
| `valid` | sampled 읽기의 유효성 | 초기 무효 행 제외 |
| `sampled_torque_Nm` | 센서 시각의 토크 | 동일 센서 시각이 유지되는 행 확인 |
| `latest_torque_Nm` | 최신 물리 토크 | 팔이 움직일 때 sampled와 차이 관찰 |

JSON은 물리 단계마다 한 행을 저장하므로 240행이 있어도 10 Hz 센서의 독립적인 시점은 그보다 적습니다. `sensor_time_s`가 반복되는 구간은 새로운 센서 시점이 아직 오지 않았다는 단서입니다.

설치 구현은 초기 두 물리 단계에서 데이터 취득을 건너뜁니다. 초기 `valid=false`를 고장이나 측정 토크 0으로 해석하지 말고, 이후 유효한 읽기가 생기는지 확인하세요.

## 2. EffortSensor의 주기와 보간 따라가기

### 코드에서 볼 부분

```python
sensor = EffortSensor(
    '/World/Arm/Joint', sensor_period=args.period,
    use_latest_data=False, enabled=True,
)
world.reset()
```

센서에는 링크 mesh가 아니라 **측정할 관절 prim 경로**를 줍니다. 이 wrapper는 별도의 센서 외형을 만들지 않고 관절의 측정 effort를 읽습니다. 따라서 Stage에 작은 센서 물체가 나타나지 않아도 정상입니다.

같은 물리 단계 뒤 두 번 읽는 부분을 보세요.

```python
sampled = sensor.get_sensor_reading(use_latest_data=False)
latest = sensor.get_sensor_reading(use_latest_data=True)
```

`False`는 센서가 정한 시점의 값을 요청합니다. 그 시점이 과거 물리 샘플 사이에 있으면 기본 선형 보간을 사용합니다. 보간은 두 기록 사이의 값을 시간 비율로 계산하는 방법입니다. `True`는 낮은 센서 주기를 거치지 않고 최신 물리 읽기를 요청합니다.

예를 들어 물리가 0.2167초까지 진행했더라도 센서가 마지막으로 정한 시점은 0.2초일 수 있습니다. 두 값이 다른 이유를 이해하려면 토크만 보지 말고 **어느 시점의 값인지** 읽어야 합니다. 초기화나 시점 정렬 때문에 처음부터 완벽한 주기표처럼 보이지 않을 수 있으므로 유효한 여러 행을 확인하세요.

### 관절에서 볼 부분

로컬 팔의 회전축은 Y이고 drive의 stiffness는 100, damping은 10, 목표각은 0°입니다. 중력이 작용하는 긴 링크가 목표 자세를 향해 움직이면서 토크가 변합니다. `sampled_torque_Nm`은 모터에 직접 준 명령이 아니라 관절에서 측정한 회전 effort입니다.

출력의 `valid`와 `sensor_time_s`는 sampled 읽기에만 해당합니다. 이 파일은 latest 읽기의 유효성과 시각을 별도 필드로 저장하지 않습니다. 특히 초기 행에서 두 값의 차이를 판단할 때 이 범위를 기억하세요.

### GUI에서 관절 구동과 센서 주기 비교하기

1. 1절을 새 출력 경로에서 `--steps` 없이 실행하세요. **Window > Graph Editors > Action Graph**로 새 그래프를 만들고 **On Playback Tick**, **Isaac Read Effort Node**, **To String**, **Print Text**를 추가합니다.
2. Tick → Read Effort → Print Text의 실행 포트를 연결하고 **Effort Value → To String → Print Text의 text**를 연결하세요.
3. Read Effort의 **Prim Path**에 `/World/Arm/Joint`, **Sensor Period**에 `0.1`, **Use Latest Data**에 False를 지정합니다. Print Text는 Warning 로그로 두세요. 그래프 노드는 자신의 센서를 사용하므로 로컬 Python 센서와 시점 정렬이 완전히 같을 것을 요구하지 않습니다.
4. **Sensor Time**의 진행을 확인하고 Use Latest Data만 True로 바꿔 보세요. 관절 경로는 같고 읽을 시점의 선택이 달라집니다.

움직이는 구간을 더 살펴보려면 Stop 후 `/World/Arm/Joint`의 Angular Drive에서 Stiffness를 0, Target Velocity를 90 deg/s로 바꾸고 Play하세요. Damping은 10을 유지합니다. 이는 위치 유지에서 속도 구동으로 바꾸는 별도 실습이며, 관절에는 ±80° 한계가 있어 끝에서도 회전이 계속되지는 않습니다. GUI에서 바꾼 이후의 동작은 이미 저장된 `effort.json`에 추가되지 않으므로 그래프 출력을 관찰하세요. [공식 Effort Sensor의 GUI 흐름](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html#omnigraph-workflow)과 연결되는 과정입니다.

## 3. 기록 주기와 센서 주기의 차이 정리

```text
물리 60 Hz → 매 단계의 관절 토크
    ├─ 최신 읽기 → latest_torque_Nm
    └─ 센서 시점 10 Hz + 보간 → sampled_torque_Nm

매 물리 단계마다 두 읽기를 JSON 한 행에 저장
```

센서값을 같은 토크와 함께 저장하더라도 시간축은 다를 수 있습니다. 빠르게 변하는 동작에서는 차이가 잘 드러나고, 정지 구간에서는 두 토크가 비슷할 수 있습니다. **값이 비슷하다는 사실만으로 센서 주기가 무시되었다고 판단하지 마세요.** 갱신된 `sensor_time_s`의 간격이 더 직접적인 확인 기준입니다.

## 4. 간단한 확인 실험

센서 주기만 0.1초에서 0.2초로 늘려 보세요.

```bash
~/isaacsim/python.sh src/66_sensors_sensors_physics_effort/run.py --steps 240 --period 0.2 --output src/66_sensors_sensors_physics_effort/output/period02
```

물리 간격은 그대로이고 센서 주파수는 10 Hz에서 5 Hz로 줄어듭니다. 유효 구간에서 `sensor_time_s`가 바뀌는 횟수와 같은 값이 유지되는 행 수를 비교하세요. 예상 변화는 토크가 절반이 되는 것이 아니라 **센서 시점 사이 간격이 길어지는 것**입니다.

## 실행할 때 막히면

- **`Effort sensor never initialized`**: 너무 짧게 실행했는지, 센서 경로가 실제 회전 관절인지 확인하세요. 전체 예제를 240단계로 실행합니다.
- **sampled와 latest가 거의 같음**: 뒤쪽 정지 구간보다 초기 움직임을 보고 센서 시각도 함께 비교하세요.
- **토크가 음수임**: 회전 effort의 부호는 관절 축 기준입니다. 음수 자체가 오류는 아니며 크기와 시간 변화로 해석합니다.
- **공식 예제의 import 경로가 작동하지 않음**: 이 파일처럼 `from isaacsim.sensors.physics import EffortSensor`를 사용하세요. 설치 5.1의 공개 import 경로입니다.
- **속도 목표를 바꿨는데 계속 회전하지 않음**: 로컬 관절에는 -80°~80° 한계가 있습니다. 목표 속도가 관절 한계에서도 유지될 것으로 기대하지 마세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Effort Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html)에 대응합니다. 로컬 한 관절 팔에서 주기 읽기와 최신 읽기를 한 시계열로 비교합니다. 보간과 초기화 설명은 설치된 `effort_sensor.py`도 함께 대조했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 주기의 headless 120단계에서 유효값, 0이 아닌 토크, 진행하는 센서 시각을 확인한 과거 기록입니다. 마지막 토크 약 -11.04 N·m는 그 실행의 관찰값이며 고정 기대값이 아닙니다. 현재 파일을 재실행한 결과는 아니며 주기 변경·OmniGraph·속도 구동은 별도로 확인해야 합니다.
