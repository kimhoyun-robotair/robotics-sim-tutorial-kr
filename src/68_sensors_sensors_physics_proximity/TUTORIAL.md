# 68. Proximity overlap과 머문 시간

권장 학습 순서 **68** · 센서와 측정 데이터 · 출처 ID `t155`

처음에 겹쳐 있는 두 큐브가 물리적으로 분리되는 동안 proximity wrapper의 overlap 기록을 저장합니다. 단순 원거리 거리계와 구별하는 실습입니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/68_sensors_sensors_physics_proximity
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

1. 기본 separation=0.8 m로 1 m 큐브 두 개를 배치합니다. 중심 간격이 크기보다 작으므로 처음 겹칩니다.
2. 실행 후 `proximity.json`의 overlaps에 `/World/Cube2`가 나타나는지 보고 분리 후 사라지는지 확인합니다. 나중에는 ground plane과의 overlap 정보가 포함될 수 있습니다.
3. 각 항목의 distance와 duration을 기록합니다. duration은 설치 구현의 `time.time()`을 사용하는 **벽시계 시간**이므로 simulation_time_s와 같은 시계로 가정하지 않습니다.
4. `--separation 1.5 --output output/separated`로 초기 간격만 바꾸고 두 큐브 사이 overlap이 사라지는지 비교합니다.
5. GUI 실행에서 큐브가 떨어져 바닥에 놓이는 것을 확인합니다. 센서가 `get_data()`에 반환하지 않은 물체까지 distance 측정이 있다고 해석하지 마세요.

## API와 USD 개념

`ProximitySensor(cube.prim)`은 PhysX scene query로 해당 prim 영역의 overlap을 확인하고 `register_sensor`가 매 프레임 갱신에 등록합니다. `get_data()`의 key는 상대 prim 경로이며 distance와 duration은 그 overlap 기록의 속성입니다. 원거리 모든 물체의 최소 표면 거리를 제공하는 센서가 아닙니다.

각 cube는 USD prim이고 DynamicCuboid는 rigid body와 collider를 갖춥니다. 초기 interpenetration은 예제의 의도이며 실제 로봇 초기화에서는 피해야 합니다. callback 등록과 해제를 같은 실행이 소유하고 finally에서 `clear_sensors`를 호출합니다.

## 확장 실습·성공 기준·문제 해결

아무 overlap도 없으면 위치·collider·등록 여부를 확인합니다. separation=1.5에서 큐브 간 정보가 없는 것은 예상 결과이므로 코드가 실패로 처리하지 않습니다. 단, 기본 separation=0.8 실험은 첫 몇 frame의 overlap을 GUI/JSON로 관찰해야 완료입니다. duration 숫자는 실행 컴퓨터 속도에 따라 달라질 수 있으므로 원문 숫자와 정확히 일치시킬 필요가 없습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Proximity Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_proximity.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
