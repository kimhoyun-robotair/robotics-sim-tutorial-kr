# 69. 사용자 패턴을 보내는 PhysX 거리 센서

권장 학습 순서 **69** · 센서와 측정 데이터 · 출처 ID `t156`

로컬 벽에 지그재그 광선을 보내고 마지막 깊이 버퍼와 실제 입력 패턴을 저장합니다. 원문의 배치 전송을 작은 샘플로 구현했습니다.

## 이 실습의 의도

PhysX Generic Sensor에 직접 만든 광선 방향 배열을 공급하여, 거리 측정이 센서 생성만으로 끝나지 않고 배치 요청과 패턴 전송을 필요로 함을 익힌다. x=5 m의 넓은 벽과 고정 센서를 사용해 입력 각도 변화가 벽 위의 스캔 자국과 거리로 나타나게 했다. 기본 실행은 요청이 있을 때 12,000개 패턴을 다시 공급하고, 입력 패턴 전체와 마지막 깊이 버퍼를 저장한다.

## 실행 후 확인할 것

- **실제로 보낸 입력**: `pattern_and_depth.npz`의 `angles_rad`는 `[2,12000]`, `origin_offsets_m`는 `[12000,3]`이며 기본 offset은 0이다. 첫 행은 azimuth, 둘째 행은 이 구현에서 수평을 0으로 쓰는 elevation 형태의 각도이며 단위는 rad다.
- **벽까지의 거리**: `depth_m`이 비어 있지 않고 벽에 맞은 광선에 20 m 미만의 실제 거리가 있는지 본다. 벽 앞면 x=4.9 m는 정면 기준이며, 기울어진 광선의 사선 거리는 그보다 길 수 있다.
- **배치와 프레임을 구별**: `measurements.json`의 `batches_sent`, `rays_in_batch`, `last_depth_count`를 비교한다. 2,400 rays/s를 60 Hz로 처리하므로 프레임당 약 40개가 기준이고, 마지막 `depth_m`을 12,000개 입력 전체의 일대일 측정 결과로 연결하지 않는다.
- **패턴 변경**: GUI의 `/World/Wall` 위 점과 `angles_rad`를 함께 보며 `zigzag`와 `two-band`의 세로 방향 분포를 비교한다. `--steps 600`에서는 `send_next_batch` 요청에 따라 계속 공급되는지 보고 배치 요청 횟수 자체를 고정하지 않는다.
- **저장 시점과 유효성**: 기본 240스텝 후 잠시 pause하여 마지막 버퍼를 저장하고 GUI에서는 재생을 재개한다. 이후 패턴은 계속 공급하지만 NPZ는 추가되지 않으며, 최대거리 20 m의 값은 벽 검출의 증거로 세지 않는다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/69_sensors_sensors_physx_generic
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·렌더링·센서 갱신 및 패턴 공급이 계속됩니다. 처음 240스텝 뒤 입력 패턴과 마지막 깊이 버퍼를 한 번 저장하며, 이후 관찰 중에는 파일을 추가하거나 바꾸지 않습니다. `--steps N`에 양수를 주면 N스텝 뒤 스냅샷을 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 기본 실행 후 `pattern_and_depth.npz`의 angles_rad, origin_offsets_m, depth_m를 확인합니다. 벽 중심은 x=5 m이고 앞면은 4.9 m이므로 정면 광선은 그 부근을 읽습니다.
2. `measurements.json`의 batches_sent와 rays_in_batch를 봅니다. batch=12,000, sampling_rate=2,400이면 약 5초 분량이며 60 fps에서 40개 광선/프레임을 공급할 수 있습니다.
3. `--steps 600 --output output/long`으로 여러 배치 요청을 관찰합니다. send_next_batch가 true일 때만 새 배열을 보냅니다.
4. `--pattern two-band --output output/two-band`로 패턴 형태만 바꿔 연속 세로 스윕과 두 높이 띠를 비교합니다. 로컬 코드는 두 패턴 모두 필요할 때 같은 배치를 다시 공급합니다. 확장 내부의 별도 반복 모드를 설정했다고 주장하지 않습니다.
5. GUI 실행에서 벽에 맞는 점 모양을 봅니다. 원래 UI 실습은 **Window > Examples > Robotics Examples > Sensors > Custom Pattern Range Sensor > Load Sensor > Load Scene > Set Sensor Pattern > Play** 순서입니다. **Save Pattern Image**로 지그재그 자국 이미지를 저장할 수 있습니다.

## API와 USD 개념

Generic sensor는 PhysX raycast로 collider까지 기하학적 깊이를 측정합니다. `RangeSensorCreateGeneric`가 sensor prim을 생성하고 `_range_sensor.acquire_generic_sensor_interface()`가 batching과 읽기를 제공합니다.

문서의 입력 CSV 설명은 N×2 [azimuth,zenith]이고 실제 binding에 보내는 배열은 **2×N, radians, 연속 메모리**입니다. 따라서 CSV degrees는 `np.deg2rad(np.loadtxt(path,delimiter=',')).T.copy()`로 변환합니다. origin_offsets는 N×3입니다. 설치 5.1 테스트에서는 두 번째 각 0이 수평 광선이므로 본 코드도 수평 기준 elevation 형태의 숫자를 사용합니다. 원문의 'z축 기준 zenith' 설명만 믿고 π/2를 더하지 마세요.

batch가 프레임당 필요한 광선보다 작으면 원하는 sampling_rate를 유지하지 못합니다. streaming은 소비 전에 다음 배치를 공급하는 방식입니다. 원문 GUI 예제에는 한번 보낸 패턴을 반복하는 모드도 있으며 Open Source Code의 `_streaming=False` 변형으로 비교할 수 있습니다.

## 확장 실습·성공 기준·문제 해결

광선 원점 offset을 모두 z=0.2 m로 변경하는 추가 실험은 패턴을 유지한 채 맞는 위치만 옮깁니다. 본 패키지에는 원점 0 배열을 저장하므로 재현하기 쉽습니다. depth가 비어 있으면 timeline Play, send_next_batch 응답, collision 설정과 단위를 확인합니다. max_range=20에 도달한 값은 벽 표면 거리로 세지 마세요. 이 PhysX 모델은 RTX의 재질 투과·반사 모델이 아닙니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — PhysX SDK Generic Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_generic.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
