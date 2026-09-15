# 67. IMU의 중력과 필터

권장 학습 순서 **67** · 센서와 측정 데이터 · 출처 ID `t154`

떨어지는 큐브에 IMU를 부착해 낙하·충돌·정지 중의 가속도와 각속도를 기록합니다. 원문의 IMU wrapper와 저수준 읽기를 실제 물리 장면에 연결했습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/67_sensors_sensors_physics_imu
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·렌더링·센서 갱신이 계속됩니다. 처음 240스텝의 측정 결과를 한 번 저장하며, 이후 관찰 중에는 파일이나 기록 배열을 계속 늘리지 않습니다. `--steps N`에 양수를 주면 N스텝의 결과를 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 실행 후 `imu.json`에서 높이와 linear_acceleration의 시간을 맞춰 봅니다. 낙하 중, 충돌 순간, 바닥 정지 후를 따로 기록합니다.
2. `--no-read-gravity --output output/no-gravity`로 읽기 옵션만 바꿔 중력 포함 여부가 결과에 미치는 영향을 비교합니다.
3. 별도 실험에서는 `--filter-width 10 --output output/filter10`으로 rolling average를 키우고 충돌 peak와 지연을 기본값 1과 비교합니다. 한 실험에서 두 옵션을 동시에 바꾸지 마세요.
4. GUI에서 `/World/Cube/Imu`의 local transform을 봅니다. IMU 축을 바꾸려면 Stop한 상태에서 회전을 수정하고 다시 Play합니다.
5. GUI 센서 생성은 rigid body를 선택한 뒤 **Create > Sensors > Imu Sensor**입니다. **Raw USD Properties**에서 sensor_period와 filter width를 확인합니다.

## API와 USD 개념

IMU는 센서 **로컬 축**의 가속도와 각속도를 반환합니다. 이 장면은 m, s 단위이므로 가속도는 m/s², 각속도 API는 rad/s입니다. 정지 상태의 중력 포함 측정과 자유낙하의 specific force를 구분하고 부호는 센서 축을 기준으로 해석합니다.

`get_sensor_reading(...,use_latest_data=True,read_gravity=...)`는 IsSensorReading을 반환합니다. 부모는 rigid body여야 하고 physics Hz보다 빠른 설정으로 독립적인 새 샘플이 생기지는 않습니다. 필터 버퍼는 너비에 따른 과거 샘플을 사용하므로 초기 transient를 버리고 비교하세요. position/translation, frequency/dt는 각각 동시에 지정하지 않습니다.

wrapper `get_current_frame(read_gravity=True)`는 lin_acc, ang_vel, orientation, time, physics_step을 사전으로 제공합니다. 저수준 interface의 quaternion과 다른 외부 시스템의 quaternion 순서를 섞지 마세요.

## 확장 실습·성공 기준·문제 해결

OmniGraph는 On Playback Tick→Isaac Read IMU Node→Print Text exec를 연결하고 IMU Prim=`/World/Cube/Imu`로 지정합니다. angular velocity→To String→Print Text text를 연결하며 read gravity와 Warning 로그를 확인합니다.

원문의 회전 실습을 위해 NVIDIA 자산 `/Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd`를 열 수 있습니다. `/World/simple_articulation/Arm/RevoluteJoint`의 Target Velocity=90 deg/s, Stiffness=0을 설정하고 Arm 아래 IMU를 만듭니다. 기본 UI 예제는 **Window > Examples > Robotics Examples > Sensors > IMU Sensor > Load Scene**이고 Shift+왼쪽 드래그로 Ant를 움직입니다.

사용자 interpolation callback을 줄 때는 buffer와 time에 대해 실제 수치 보간을 구현해야 하며 read_gravity 변환은 callback 뒤 적용됩니다. 센서 위치/부모 변경은 Stop 후 수행합니다. invalid가 계속되면 parent rigid body, 경로, Play 상태를 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
