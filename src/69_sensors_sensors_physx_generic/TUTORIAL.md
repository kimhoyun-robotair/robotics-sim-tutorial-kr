# 69. 직접 만든 광선 패턴으로 벽을 스캔하기

## 이번에 배우는 것

**PhysX Generic Sensor에 광선 방향 배열을 공급하고, 보낸 패턴 전체와 마지막에 읽은 거리 버퍼를 구별합니다.**

일반적인 회전 센서는 정해진 각도 순서대로 스캔합니다. Generic Sensor에서는 사용자가 광선 하나하나의 방향을 배열로 만들어 보낼 수 있습니다. 이번에는 넓은 벽 앞에서 가로로 왕복하고 세로로 움직이는 패턴을 만들어, 방향 입력이 측정으로 이어지는 과정을 살펴봅니다.

| 구성 | 이 실습의 값 |
|---|---|
| 센서 위치 | `(0,0,1)` m |
| 벽 | 중심 x=5 m, 두께 0.2 m, 너비 8 m, 높이 4 m |
| 정면 벽 표면 | 센서 앞 x=4.9 m |
| 패턴 배치 | 광선 12,000개의 방향 |
| 처리율 | 초당 2,400광선 |
| 물리·렌더 간격 | 1/60초 |

여기서 **배치(batch)**는 한 번에 전달하는 여러 광선의 묶음입니다. 배치를 보냈다는 사실과 그 모든 광선의 결과를 저장했다는 사실은 다릅니다.

## 1. 기본 지그재그 패턴 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU 환경에서 저장소 루트 기준으로 실행하세요.

```bash
~/isaacsim/python.sh src/69_sensors_sensors_physx_generic/run.py --steps 240 --output src/69_sensors_sensors_physx_generic/output/zigzag
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 240단계 후 입력 패턴과 마지막 거리 버퍼를 저장하고 종료합니다. 출력 폴더는 새 경로여야 합니다. 생략하면 이 튜토리얼의 `output/날짜_시간/`에 저장합니다.

GUI를 계속 보려면 `--steps 240`을 빼세요. 처음 기록을 저장한 뒤 재생을 재개하고 요청에 따라 광선 패턴을 계속 공급합니다. 벽에 그려지는 점을 관찰할 수 있지만 저장 NPZ에는 이후 측정이 추가되지 않습니다. `--headless`를 추가하면 창 없이 결과를 만듭니다.

### 실행 결과 확인하기

`pattern_and_depth.npz`에는 세 배열이 있습니다.

| 배열 | 기본 형태 | 의미 |
|---|---|---|
| `angles_rad` | `[2,12000]` | 첫 행은 수평각, 둘째 행은 수직 방향 각도 |
| `origin_offsets_m` | `[12000,3]` | 각 광선의 원점 이동량; 이 실습에서는 모두 0 |
| `depth_m` | 마지막 거리 버퍼의 형태 | 마지막 측정 묶음의 거리(m) |

`measurements.json`에서는 `batches_sent`, `rays_in_batch`, `last_depth_count`, `min_depth_m`을 비교하세요. 입력은 12,000개인데 마지막 거리는 약 40개일 수 있습니다. 2,400광선/초를 60 Hz로 처리하면 **한 프레임 분량은 약 40광선**이기 때문입니다.

벽에 맞은 거리는 정면 기준 4.9 m 부근이지만 기울어진 광선은 사선으로 더 멀리 이동합니다. 최대거리 20 m의 값만 있는지, 실제 벽까지의 반환이 있는지 구분하세요. 코드의 자동 검사는 깊이 버퍼가 비었는지만 확인합니다.

## 2. 방향 배열과 다음 배치 요청 따라가기

### 코드에서 볼 부분

```python
phase = np.linspace(0,1,12000,endpoint=False)
azimuth = .5*(2/np.pi)*np.arcsin(np.sin(2*np.pi*10*phase))
elevation = .2*np.sin(2*np.pi*phase)
pattern = np.stack((azimuth,elevation)).copy()
offsets = np.zeros((pattern.shape[1],3))
```

`phase`는 패턴 처음부터 끝까지의 진행 비율입니다. 수평각은 약 -0.5~0.5 rad 범위를 열 번 왕복하고 수직각은 약 -0.2~0.2 rad 범위를 천천히 오르내립니다. 빠른 가로 왕복에 느린 세로 이동이 겹쳐져 지그재그가 됩니다.

배열을 `np.stack`하면 두 행에 각도를 담는 `[2,N]` 형태가 됩니다. 원문에서 패턴을 `[N,2]`로 설명하는 부분과 실제 binding 입력 형태를 혼동하지 마세요. 로컬 코드와 설치 5.1 테스트는 `[2,N]`을 사용합니다. 각도는 rad이고, 이 구현에서 두 번째 각도 0은 수평 광선입니다.

```python
if interface.send_next_batch(path):
    interface.set_next_batch_rays(path, pattern)
    interface.set_next_batch_offsets(path, offsets)
    batches += 1
```

`send_next_batch()`는 다음 데이터를 보낼 시점인지 확인하는 요청입니다. 참일 때 방향과 원점 배열을 함께 전달합니다. 센서를 만들기만 하고 방향을 공급하지 않으면 의도한 광선이 생기지 않습니다. 같은 패턴을 반복해 보내더라도 매 프레임 무조건 덮어쓰는 방식은 아닙니다.

### 입력과 출력의 대응에서 볼 부분

12,000개를 초당 2,400개씩 소비하면 한 배치는 명목상 5초 분량입니다. 기본 240단계는 약 4초이므로 패턴 전체를 한 번 모두 관찰하는 시간보다 짧습니다. GUI를 계속 열어 두면 더 긴 스캔을 볼 수 있습니다.

스크립트는 마지막에 `world.pause()`와 앱 업데이트를 거친 뒤 깊이를 읽습니다. **NPZ의 첫 번째 입력 광선과 첫 번째 저장 깊이가 같은 광선이라고 대응시키면 안 됩니다.** 파일에는 전체 입력과 마지막 출력만 있으며, 전 구간의 광선별 시간·인덱스를 누적하지 않습니다.

### GUI의 패턴 예제와 비교하기

현재 실행을 닫고 새 Isaac Sim 창에서 **Window > Examples > Robotics Examples > Sensors > Custom Pattern Range Sensor**를 여세요. **Load Sensor → Load Scene → Set Sensor Pattern → Play** 순서로 진행합니다. 센서와 장면만 불러온 뒤 패턴을 공급하지 않으면 원하는 스캔이 시작되지 않는다는 점을 UI에서도 확인할 수 있습니다.

벽에 나타나는 스캔 자국을 살펴보고 **Save Pattern Image**로 이미지를 저장해 보세요. **Open Source Code**에서는 패턴의 방향 배열과 반복 공급 부분을 찾아 로컬 `send_next_batch()` 흐름과 비교합니다. 공식 GUI 예제에는 자체 반복 모드도 있지만 로컬 실행은 요청이 올 때 동일 배치를 다시 보내는 방식입니다. GUI 이미지와 로컬 NPZ는 서로 다른 결과 파일입니다. [공식 Generic Sensor GUI 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_generic.html#physx-sdk-generic-sensor-example)를 참고하세요.

## 3. 패턴 공급과 센서 측정의 흐름 정리

```text
수평·수직 각도로 12,000개 광선 준비
    → 센서의 다음 배치 요청 확인
    → 방향 배열과 원점 배열 전달
    → 프레임마다 일부 광선의 collider 거리 계산
    → 마지막 깊이 버퍼 저장
```

입력 배열은 센서가 어디를 보게 할지 정하고, 처리율은 그 입력을 얼마나 빠르게 사용할지 정합니다. 벽의 collider는 실제로 맞는 표면을 정합니다. 출력 개수만 보고 입력 누락으로 판단하기 전에 **한 배치·한 프레임·저장 범위**를 구분해 보세요.

## 4. 간단한 확인 실험

패턴만 두 개의 높이 띠로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/69_sensors_sensors_physx_generic/run.py --steps 240 --pattern two-band --output src/69_sensors_sensors_physx_generic/output/two-band
```

이 모드의 수직각은 배치 앞 절반에서 -0.2 rad, 뒤 절반에서 +0.2 rad입니다. `angles_rad`의 두 번째 행이 연속적으로 변하던 기본 패턴과 비교하세요. 수평 왕복과 광선 수, 처리율은 그대로입니다. GUI에서는 연속적인 세로 스윕 대신 두 높이로 점이 모이는지 관찰합니다. 마지막 깊이 버퍼 하나에 두 띠의 모든 결과가 들어 있을 것을 요구하지 마세요.

## 실행할 때 막히면

- **`No generic sensor depth`**: timeline이 진행했는지, 다음 배치 요청에 방향 배열을 보냈는지 확인하세요. 너무 짧은 실행은 초기 공급 후 측정 시간을 확보하지 못할 수 있습니다.
- **방향이 엉뚱함**: `[2,N]` 형태, rad 단위, 두 번째 각도의 수평 기준을 대조하세요.
- **거리 배열이 12,000개보다 작음**: 마지막 프레임 버퍼이므로 가능한 결과입니다. `last_depth_count`와 초당 광선 수를 비교하세요.
- **깊이가 모두 최대거리임**: 벽 collider와 광선 방향을 확인하세요. 버퍼 존재만으로 벽 검출이 확인되지는 않습니다.
- **배치 전송 횟수가 예상과 다름**: 요청은 내부 버퍼 공급 상태에 따라 발생합니다. 정확히 몇 번이라는 숫자보다 요청에 응답하고 실제 깊이가 나오는지 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [PhysX SDK Generic Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_generic.html)에 대응합니다. 공식 패턴 공급 개념을 작은 배치와 로컬 벽으로 구성했습니다. 입력 형태와 수평 기준 각도는 설치된 `test_generic.py`를 대조했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 패턴의 headless 30단계에서 배치 전송 2회, 마지막 깊이 40개, 최소 거리 약 4.975 m를 확인한 과거 기록입니다. 현재 파일의 재실행이나 두 띠·GUI 패턴 시험까지 확인한 결과는 아닙니다. 이번 문서 작업에서는 실제 센서를 새로 실행하지 않았으며, 전체 스캔 누적도 이 실습의 구현 범위에 포함되지 않습니다.
