# 67. 멈춘 상자의 IMU가 0이 아닌 가속도를 읽는 이유

## 이번에 배우는 것

**낙하하는 상자의 IMU 기록을 높이와 함께 읽고, 자유낙하·충돌·정지에서 가속도가 무엇을 뜻하는지 비교합니다.**

위치가 변하는데 가속도 센서값은 0에 가까울 수 있고, 물체가 멈췄는데도 센서값이 0이 아닐 수 있습니다. 가속도계가 보고하는 값에는 중력을 다루는 관례가 있기 때문입니다. 이번에는 방향을 맞춘 IMU를 상자 중심에 붙여 그 의미를 살펴봅니다.

| 구성 | 기본 설정 |
|---|---|
| 상자 | 1 kg, 한 변 0.5 m, 중심 높이 2 m |
| 센서 경로 | `/World/Cube/Imu` |
| 센서 축 | 상자의 로컬 xyz와 일치 |
| 물리·센서 주기 | 60 Hz |
| 중력 읽기 | 기본 `--read-gravity` 활성화 |
| 필터 폭 | 기본 1 |

`imu.json`은 가속도·각속도와 상자 중심 높이를 함께 저장합니다. IMU 위치가 상자 중심이므로 낙하 과정과 센서 기록을 연결하기 쉽습니다.

## 1. 낙하와 착지 동안 IMU 기록하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/67_sensors_sensors_physics_imu/run.py --steps 240 --output src/67_sensors_sensors_physics_imu/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 상자가 낙하하고 물리 240단계가 끝나면 `imu.json`, `scene.usda`를 저장한 뒤 앱이 종료됩니다. 출력 폴더는 아직 없는 경로를 지정합니다. `--output`을 생략하면 이 튜토리얼의 `output/날짜_시간/`에 저장합니다.

창 없이 기록하려면 `--headless`를 추가하세요. `--steps 240`을 빼면 첫 240단계를 저장한 뒤 GUI에서 계속 읽지만 파일에는 추가하지 않습니다. 새로 움직인 구간까지 기록하려면 새 출력 경로로 다시 실행해야 합니다.

### 실행 결과 확인하기

먼저 `valid=true`인 행에서 높이의 변화를 찾으세요. 중심 높이가 감소하는 구간은 낙하, 약 0.25 m에 머무는 구간은 착지 후입니다.

| 구간 | 기본 중력 읽기에서의 가속도 예상 | 함께 볼 항목 |
|---|---|---|
| 자유낙하 | 대체로 0 부근 | 높이는 계속 감소 |
| 바닥 충돌 | 순간적으로 큰 값 | 높이 감소가 멈추는 시점 |
| 정지 | z 성분 약 +9.81 m/s² | 높이 약 0.25 m, 작은 각속도 |

`linear_acceleration`과 `angular_velocity`는 각각 `[x,y,z]` 배열입니다. 가속도는 m/s², 각속도는 rad/s입니다. `linear_acceleration[2]`가 센서 z 가속도입니다. 초기 무효값과 충돌 순간을 정지 상태의 대표값으로 쓰지 마세요.

## 2. 센서 축·중력 읽기·필터 연결하기

### 코드에서 볼 부분

```python
sensor = IMUSensor(
    '/World/Cube/Imu', frequency=60,
    translation=np.zeros(3), orientation=np.array([1.,0.,0.,0.]),
    linear_acceleration_filter_size=args.filter_width,
    angular_velocity_filter_size=args.filter_width,
    orientation_filter_size=args.filter_width,
)
```

위치가 `(0,0,0)`이고 회전이 WXYZ 순서의 `(1,0,0,0)`이므로 센서는 부모 상자의 중심과 축을 그대로 사용합니다. 상자가 회전하면 센서 축도 함께 회전합니다. 따라서 센서 z와 월드 z가 언제나 같지는 않습니다. 기본 낙하에서는 크게 회전하지 않는 구간을 골라 위의 기대값과 비교하세요.

```python
reading = interface.get_sensor_reading(
    '/World/Cube/Imu', use_latest_data=True,
    read_gravity=args.read_gravity,
)
```

`use_latest_data=True`는 최신 물리 읽기를 선택합니다. `read_gravity`는 가속도 출력에서 중력 성분을 어떻게 반영할지 정합니다. 기본 설정의 가속도는 **비중력 힘에 의한 가속도(specific force)**로 생각하면 낙하와 정지 결과를 이해하기 쉽습니다.

상자가 거의 회전하지 않는 경우의 관계는 다음과 같습니다.

```text
기본 IMU 가속도 ≈ 상자의 운동 가속도 - 중력 가속도

자유낙하: -9.81 - (-9.81) ≈ 0
정지:      0 - (-9.81) ≈ +9.81  (z 방향)
```

바닥에 놓였을 때의 양수 읽기는 바닥의 지지를 반영합니다. 단순히 위치를 두 번 미분한 운동 가속도와 기본 IMU 읽기를 같은 값으로 취급하면 이 차이가 사라집니다.

### 필터에서 볼 부분

`--filter-width`는 과거 여러 샘플을 사용해 읽기를 부드럽게 하는 폭입니다. 폭이 커지면 급격한 충돌 peak가 완만해지거나 변화가 늦게 보일 수 있습니다. 물리 충돌 자체가 느려지는 것은 아닙니다.

이 코드에서는 가속도·각속도·자세 필터를 함께 설정하지만 JSON에는 자세 quaternion을 저장하지 않습니다. 저장된 것은 `time_s`, `valid`, 두 3성분 벡터와 `height_m`입니다. 자세가 필요한 분석이라면 현재 파일만으로 충분하다고 가정하지 마세요.

### GUI에서 IMU 읽기와 회전 관찰하기

1. 기본 실행을 새 출력 폴더에서 `--steps` 없이 열어 두고 **Window > Graph Editors > Action Graph**에서 새 그래프를 만드세요.
2. **On Playback Tick → Isaac Read IMU Node → Print Text**의 실행 포트를 연결합니다. **Angular Velocity Vector → To String → Print Text의 text**도 연결하세요.
3. **IMU Prim**을 `/World/Cube/Imu`로 지정하고 **Read Gravity**, **Use Latest Data**를 True로 맞춥니다. Print Text의 **Log Level**을 Warning으로 설정해 각속도를 읽고, 필요하면 출력 벡터를 **Linear Acceleration Vector**로 바꾸어 기본 중력 읽기와 비교하세요.
4. 센서 자체를 GUI로 만드는 연습은 별도 stage에서 rigid body를 선택한 뒤 **Create > Sensors > Imu Sensor**로 진행합니다. Raw USD Properties의 period와 filter width를 확인하고 위치·방향 편집은 Stop 상태에서 하세요.

낙하 장면은 각속도가 작을 수 있습니다. 회전도 보고 싶으면 새 세션에서 **Window > Examples > Robotics Examples > Sensors > IMU Sensor > Load Scene**을 열고 Play하세요. 예제의 Ant를 Shift+왼쪽 드래그로 움직이며 세 축의 가속도와 각속도를 비교합니다. 이 예제의 화면 출력은 로컬 `imu.json`과 별개입니다. [공식 IMU 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html#imu-example)에서 같은 관찰 흐름을 확인할 수 있습니다.

## 3. 높이와 IMU를 함께 읽는 이유 정리

```text
height_m → 상자가 실제로 떨어지는지, 멈췄는지 확인
linear_acceleration → 센서 축에서 읽은 가속도 의미 확인
angular_velocity → 그 축이 회전하고 있는지 확인
valid → 해당 읽기를 해석할 수 있는지 확인
```

한 값만 보면 낙하 중 0과 정지 중 +9.81이 이상해 보일 수 있습니다. 운동 상태, 센서 축, 중력 옵션을 함께 보면 두 결과는 같은 모델로 설명됩니다. 충돌 peak의 정확한 숫자보다 **낙하→충돌→정지의 관계가 일관적인지** 먼저 확인하세요.

## 4. 간단한 확인 실험

중력 읽기 옵션만 끄고 실행하세요.

```bash
~/isaacsim/python.sh src/67_sensors_sensors_physics_imu/run.py --steps 240 --no-read-gravity --output src/67_sensors_sensors_physics_imu/output/no-gravity
```

센서 방향과 필터 폭은 그대로입니다. 거의 회전하지 않는 구간에서 자유낙하의 z 가속도는 약 -9.81 m/s², 정지 후에는 약 0 부근이 되는지 비교해 보세요. 높이의 운동은 같은데 읽기 기준이 달라지는 실험입니다. 충돌 peak나 초기 행 대신 두 구간의 여러 유효 샘플을 비교하세요.

## 실행할 때 막히면

- **`No valid IMU readings`**: 센서가 강체 `/World/Cube`의 자식인지, 충분한 물리 단계가 진행되는지 확인하세요.
- **정지했는데 z가 약 9.81임**: 기본 중력 읽기의 예상 결과입니다. 중력 옵션을 확인하고 정지 높이와 함께 해석하세요.
- **가속도가 여러 축에 나뉨**: 상자나 IMU가 회전했을 수 있습니다. 센서의 로컬 축을 월드 축과 구분합니다.
- **필터를 키웠더니 충돌 시점과 peak가 어긋남**: 평균에 과거 샘플이 포함되기 때문입니다. 초기 버퍼가 채워지는 구간도 제외해 비교하세요.
- **센서 위치 변경 후 데이터가 이상함**: Stop 상태에서 transform이나 부모를 편집하고 다시 Play하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)에 대응합니다. 로컬 낙하 상자로 가속도 읽기와 실제 이동을 연결하고 중력·필터 옵션을 제공합니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 설정의 headless 120단계에서 자유낙하와 정지 중력 읽기를 확인했으며 정지 z 가속도 약 +9.81 m/s²를 기록합니다. 이는 과거 조건의 결과로, 현재 파일의 재실행이나 중력 옵션·필터·GUI 비교까지 확인한 것은 아닙니다. 당시 실행 조건은 `tutorial.json`을 참고하세요.
