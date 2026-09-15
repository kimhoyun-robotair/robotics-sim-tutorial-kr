# 71. Lightbeam으로 빛의 장막 만들기

권장 학습 순서 **71** · 센서와 측정 데이터 · 출처 ID `t158`

수직으로 놓인 여러 광선 앞을 큐브가 가로지를 때 beam hit와 거리를 기록합니다. 원문의 Lightbeam UI 개념을 실제 command/API로 구현한 독립 예제입니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/71_sensors_sensors_physx_lightbeam
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

1. 기본 실행에서 9개 광선과 높이 1.5 m의 curtain을 만듭니다. 큐브는 센서 앞 x=3 m에서 y방향으로 움직입니다.
2. `lightbeam.json`의 beam_hit와 depth_m를 확인합니다. 큐브가 광선에서 벗어난 시점과 가로막은 시점을 비교합니다.
3. `--rays 3 --output output/rays3`으로 광선 수만 줄여 같은 큐브를 놓치는 구간이 늘어나는지 관찰합니다. curtain_length는 유지합니다.
4. `--headless`와 `--steps` 없이 실행해 그려진 ray를 봅니다. 이 예제는 시각적으로 이동하는 **static collider**를 매 frame 옮겨 intersection을 검사하므로 질량에 의한 운동을 측정하는 예제는 아닙니다.
5. 원래 GUI 경로 **Window > Examples > Robotics Examples > Sensors > Lightbeam**을 열고 Play합니다. 데이터 표의 hit, linear depth, xyz hit position을 확인한 뒤 Shift+왼쪽 드래그로 큐브나 센서를 움직입니다.

## API와 USD 개념

`IsaacSensorCreateLightBeamSensor`의 num_rays와 curtain_length가 광선 수와 수직 범위를 정합니다. forward_axis=(1,0,0), curtain_axis=(0,0,1)이므로 x방향 광선을 z방향으로 쌓습니다. `_range_sensor.acquire_lightbeam_sensor_interface()`에서 hit와 linear depth를 읽습니다.

이 모델은 PhysX collider intersection입니다. 실제 안전 장비의 전기 회로·응답 지연·인증 특성을 모델링하거나 보증하지 않습니다. beam 사이를 지나가는 작은 물체는 기하학적으로 검출되지 않을 수 있습니다. ray가 맞은 여부와 거리 값을 같이 해석하세요.

## 확장 실습·성공 기준·문제 해결

항상 miss면 대상 collider, 축, 최소거리 .1 m와 최대거리 10 m, Play 상태를 확인합니다. num_rays=1은 curtain 전체를 연속적으로 덮는 센서가 아닙니다. 마지막 JSON의 ray 수와 지정한 수가 맞는지, 시간에 따라 hit 패턴이 바뀌는지를 성공 기준으로 사용합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — PhysX SDK Lightbeam Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lightbeam.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
