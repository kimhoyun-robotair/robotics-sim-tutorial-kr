# 66. Effort Sensor의 샘플 주기

권장 학습 순서 **66** · 센서와 측정 데이터 · 출처 ID `t153`

한 관절 팔의 실제 torque를 10 Hz 센서값과 최신 physics step 값으로 함께 읽습니다. 원문의 Simple Articulation을 이 패키지가 직접 만드는 작은 팔로 대체했습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/66_sensors_sensors_physics_effort
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

1. 실행 후 `effort.json`의 physics_time_s와 sensor_time_s를 비교합니다. 기본 sensor_period=0.1초, physics_dt=1/60초이므로 값의 갱신 주기가 다릅니다.
2. sampled_torque_Nm과 latest_torque_Nm을 비교하고 valid=false인 초기값은 측정으로 사용하지 않습니다.
3. `--period .2 --output output/period02`로 센서 주기만 바꿔 timestamp가 유지되는 구간을 관찰합니다.
4. `--headless`와 `--steps` 없이 실행해 `/World/Arm/Joint`의 Y축, drive stiffness=100, damping=10, 목표각 0°를 확인합니다.
5. 원문 속도 제어를 반복하려면 Stop 후 Angular Drive의 Stiffness=0, Target Velocity=90 deg/s로 바꾸고 Play합니다. 이 로컬 팔에는 ±80° 한계가 있으므로 끝에서 속도가 유지되지 않는 것을 함께 기록하세요.

## API와 USD 개념

EffortSensor는 별도의 눈에 보이는 USD 센서 mesh를 추가하지 않고 **관절 prim 경로**를 받아 힘/토크를 샘플링하는 Python wrapper입니다. 5.1 설치에서 `from isaacsim.sensors.physics import EffortSensor`로 가져옵니다. 원문의 `scripts.effort_sensor` 표기와 실제 모듈 구성이 달라 공개 re-export를 사용했습니다.

revolute joint effort는 토크 N·m, linear/prismatic joint effort는 힘 N입니다. `get_sensor_reading`은 is_valid,time,value를 반환합니다. `sensor_period`, `enabled`, `use_latest_data`를 변경할 수 있고 다른 DOF는 `update_dof_name`, 버퍼 크기는 `change_buffer_size`로 바꿉니다. 사용자 interpolation callback은 과거 샘플과 요청 시간을 받아 실제 보간을 해야 하며 빈 reading을 반환하는 원문 개념 코드는 실행 예제가 아닙니다.

## 확장 실습·성공 기준·문제 해결

OmniGraph 경로도 이 장면에서 실습할 수 있습니다. Action Graph를 만들고 On Playback Tick→Isaac Read Effort Node→Print Text exec를 연결합니다. Effort Prim=`/World/Arm/Joint`, effort 출력→To String→Print Text text를 연결하고 Log Level=Warning, To Screen을 켭니다.

원문의 원래 자산은 `/Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd`, joint는 `/World/simple_articulation/Arm/RevoluteJoint`입니다. 사용할 때는 NVIDIA 에셋 접근이 필요합니다. 센서가 계속 invalid라면 joint 이름, articulation handle 초기화, 2 step 이상의 재생, 축 설정을 확인합니다. Sampled와 latest의 차이가 거의 없으면 정지 구간 대신 초기 움직임 구간을 비교하세요.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Effort Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
