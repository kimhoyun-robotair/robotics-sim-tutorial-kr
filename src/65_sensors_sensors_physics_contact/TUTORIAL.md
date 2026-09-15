# 65. 낙하 상자의 접촉 센서

권장 학습 순서 **65** · 센서와 측정 데이터 · 출처 ID `t152`

질량 1 kg, 한 변 0.5 m 상자를 2 m에서 떨어뜨려 접촉 전·충돌·정지의 실제 force를 기록합니다. 원문의 생성/읽기 API를 독립 장면에 연결했습니다.

## 이 실습의 의도

낙하 상자의 공중 이동, 바닥 충돌, 정지 지지를 한 장면에서 비교하여 접촉 센서의 힘이 언제 생기는지 익힌다. 한 변 0.5 m, 기본 질량 1 kg인 상자의 중심을 z=2 m에 두고 전체 부모 collider를 읽는 센서를 붙여, 충돌 전후를 높이와 힘의 시계열로 연결한다. 기본 실행은 60 Hz 물리의 최신 접촉값을 처음 240스텝 동안 기록한다.

## 실행 후 확인할 것

- **낙하와 착지**: GUI의 `/World/Cube` 또는 `contact.json`의 `height_m`에서 중심 높이가 2 m에서 바닥 위 약 0.25 m로 내려가 멈추는지 확인한다. 이 상자는 collider가 있어 바닥을 통과하며 계속 떨어지는 장면이 아니다.
- **접촉 전후의 상태**: JSON을 시간순으로 읽어 `valid`와 `contact`를 먼저 확인한다. 유효한 공중 샘플의 비접촉 상태와 착지 후 `valid=true, contact=true`를 구별하며, 초기 invalid 값을 실제 힘 0의 측정으로 사용하지 않는다.
- **힘의 해석**: `force_N`은 N이고 정지 후 값은 콘솔의 `weight_N=mass×9.81` 부근인지 비교한다. 충돌 순간의 큰 peak는 무게와 다른 동적 하중이며, peak의 정확한 숫자를 고정 성공 기준으로 삼지 않는다.
- **질량만 변경**: `--mass 2`에서 충분히 정지한 구간의 힘이 기본 질량보다 커지는지 확인한다. `radius=-1`인 `/World/Cube/Contact`는 상자 전체 collider의 접촉을 읽으므로 센서 원점이 바닥에 직접 닿을 필요는 없다.
- **완료와 저장**: 실제 유효 접촉이 한 번도 없으면 코드가 파일 저장 전에 실패한다. 착지 전에 끝나는 짧은 `--steps`는 측정 실패를 일으킬 수 있고, 기본 240스텝 뒤 계속 열린 GUI는 기존 `contact.json`에 추가 기록하지 않는다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/65_sensors_sensors_physics_contact
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

1. 실행 후 `contact.json`에서 `valid`, `contact`, `force_N`, `height_m`을 시간순으로 봅니다. 상자가 공중에 있을 때와 바닥에 정지한 뒤를 비교합니다.
2. 마지막 force와 출력된 `weight_N`을 비교합니다. 1 kg의 정지 무게는 약 9.81 N입니다. 충돌 순간 force는 무게보다 클 수 있습니다.
3. `--mass 2 --output output/mass2`로 질량만 바꿔 정지 force의 변화를 비교합니다.
4. GUI 실행에서 `/World/Cube/Contact`를 선택해 sensor period, radius, threshold를 확인합니다. radius=-1은 전체 부모 collider의 접촉을 사용합니다.
5. GUI로 만들려면 Cube 선택 후 **Create > Sensors > Contact Sensor**, 부모에는 **Add > Physics > Rigid Body with Colliders Preset**이 필요합니다. Physics Scene과 Ground Plane도 있어야 합니다.

## API와 USD 개념

`ContactSensor`는 PhysX Contact Report를 부모 물체와 구형 관심영역으로 걸러 읽습니다. 단순 contact force 센서와 raw contact pair/normal/impulse는 다른 수준의 데이터입니다. 위치를 반경으로 제한해도 접촉 자체는 물체 표면에서 일어납니다.

`_sensor.acquire_contact_sensor_interface().get_sensor_reading(path,use_latest_data=True)`는 현재 물리 step의 CsSensorReading을 반환합니다. is_valid, time, value, in_contact를 함께 봅니다. 기본 읽기는 센서 주기를 따르고 latest는 더 낮은 센서 주기를 우회해 최신 물리를 읽습니다. 센서 Hz는 physics Hz를 넘는 새 정보를 만들지 못합니다.

wrapper/command는 부모에 ContactReportAPI를 추가하지만 ColliderAPI가 있어야 유효한 접촉이 생깁니다. min_threshold는 감지 시작 힘, max_threshold는 출력 포화값입니다.

## 확장 실습·성공 기준·문제 해결

OmniGraph 실습: **Window > Graph Editors > Action Graph > New Action Graph**에서 On Playback Tick→Isaac Read Contact Sensor→Print Text의 exec를 잇고, 센서 value→To String→Print Text의 text를 연결합니다. Contact Sensor Prim=`/World/Cube/Contact`, Log Level=Warning으로 설정합니다. radius 표시에는 Isaac xPrim Radius Visualizer의 xPrim을 같은 센서로 지정하고 tick을 exec에 연결합니다.

직접 raw 접촉을 읽으려면 `get_contact_sensor_raw_data('/World/Cube/Contact')`를 사용해 body0/body1, normal, impulse를 보세요. force와 impulse를 같은 단위로 비교하지 않습니다.

기존 UI 예제는 **Window > Examples > Robotics Examples > Sensors > Contact Sensor**입니다. Play 후 Shift+왼쪽 드래그로 Ant의 접촉 변화를 봅니다. 센서 부모를 바꾸거나 센서 prim을 옮길 때는 **Stop→편집→Play** 순서로 재초기화합니다. 접촉이 없으면 collider·경로·재생 여부를 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
