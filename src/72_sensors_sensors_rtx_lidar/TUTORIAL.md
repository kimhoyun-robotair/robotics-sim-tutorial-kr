# 72. RTX Lidar의 prim·렌더·점군

권장 학습 순서 **72** · 센서와 측정 데이터 · 출처 ID `t147`

네 방향의 상자와 바닥을 실제 RTX Lidar로 읽고 프레임별 반환 수와 마지막 점군을 저장합니다. 5.1 OmniLidar와 LidarRtx를 사용합니다.

## 이 실습의 의도

OmniLidar prim, render product, annotator가 연결되어야 RTX 점군이 생성된다는 흐름을 익힌다. 센서 주위 네 방향의 상자와 바닥을 고정하여 초기 렌더 준비, 스캔 설정, 반환 수의 관계를 관찰할 수 있게 했다. 기본 `Example_Rotary` 10 Hz 센서는 누적하지 않는 annotator를 사용하며 프레임별 반환 수와 마지막 프레임 점군을 저장한다.

## 실행 후 확인할 것

- **장면과 센서 구성**: Stage에서 높이 1 m의 `/World/Lidar`가 `OmniLidar`이고, 주변 `/World/Wall0`~`Wall3` 및 바닥이 센서 시야에 있는지 확인한다. 기본 실행은 점군 debug draw를 별도로 붙이지 않으므로 viewport에 점이 안 그려진다는 사실만으로 측정 실패를 판단하지 않는다.
- **초기 빈 프레임과 이후 반환**: `measurements.json`의 `returns_per_frame`을 따라 초기 0 이후 실제 반환이 생기는지 확인한다. 마지막 프레임이 비어 있으면 이 코드는 실패하므로 스캔과 렌더 준비가 진행될 만큼 실행한다.
- **저장된 점군**: `points.npy`와 `last_shape`를 대조해 비어 있지 않은 N×3 Cartesian 배열인지 확인한다. `NoAccumulator` 출력은 마지막 프레임 결과이므로 실행 전체의 점이나 매번 정확히 같은 N을 기대하지 않는다.
- **스캔 설정 비교**: `--scan-hz 20` 결과의 `scan_hz`, 프레임별 반환 수와 점군 분포를 기본 10 Hz와 비교한다. 스캔 속도 변화가 반환 수의 정확한 두 배를 보장하지 않으며, `Example_Solid_State` 실험은 다른 패턴으로 별도 비교한다.
- **저장 이후 관찰**: 기본 240스텝의 반환 수 이력과 마지막 점군을 저장한 뒤 GUI에서는 렌더·센서 갱신만 계속한다. 이후 장면을 바꿔도 기존 `points.npy`와 JSON은 갱신되지 않는다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/72_sensors_sensors_rtx_lidar
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·렌더링·센서 갱신이 계속됩니다. 처음 240스텝의 반환 수 이력과 마지막 프레임 점군을 한 번 저장하며, 이후 관찰 중에는 파일이나 기록 배열을 계속 늘리지 않습니다. `--steps N`에 양수를 주면 N스텝의 반환 수와 마지막 점군을 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 기본 실행의 `measurements.json`에서 프레임별 점 수를 봅니다. `points.npy`는 마지막 프레임의 Cartesian 점군입니다. 초기 프레임은 비어 있을 수 있습니다.
2. `--headless`와 `--steps` 없이 실행해 Stage의 `/World/Lidar`를 선택합니다. 타입이 `OmniLidar`인지 확인하고 `omni:sensor:Core:scanRateBaseHz`를 봅니다. `Example_Rotary`는 설치된 센서 설정입니다.
3. `--scan-hz 20 --output output/scan20`으로 다시 실행합니다. 같은 렌더 프레임 수에서 스캔 속도와 한 프레임 점군이 어떻게 달라지는지 비교합니다.
4. `--config Example_Solid_State --output output/solid`로 다른 센서 패턴을 봅니다. 이는 후속 확장 실험으로 scan-rate 실험과 결과를 따로 기록하세요.
5. 정확한 모델을 사용하려면 Content Browser의 RTX Lidar 이름을 확인해 `--config HESAI_XT32_SD10`처럼 지정합니다. 모델 자산이 별도 NVIDIA 에셋 경로에 있으면 해당 자산 접근이 필요합니다.

## API와 USD 개념

`LidarRtx`는 센서 생성 command, OmniLidar prim, render product, annotator를 묶는 wrapper입니다. `initialize()` 뒤 `attach_annotator()`하고 **timeline이 재생된 상태**에서 `world.step(render=True)`로 프레임을 갱신합니다. `get_current_frame()`의 annotator 항목에서 실제 numpy 버퍼를 얻습니다.

4.5 방식의 Camera prim 센서와 JSON profile만을 사용하는 경로는 5.0부터 deprecated입니다. 본 코드는 `OmniSensorGenericLidarCoreAPI`가 붙은 OmniLidar 경로입니다. 명령 API로 직접 생성할 때도 `IsaacSensorCreateRtxLidar`를 쓰며 `config=None`이면 generic 센서 속성을 직접 작성해야 합니다. 모델 variant는 USD variant set이며, 예를 들어 `config='picoScan150', variant='Normal_11'`처럼 선택합니다.

RTX Lidar는 광학·비가시 재질과 상호작용합니다. collider가 없는 시각 mesh도 RTX 렌더 장면에 속하면 관측 대상이며 PhysX raycast와 의미가 다릅니다.

## 확장 실습·성공 기준·문제 해결

점이 없으면 timeline Play, 렌더 활성화, 센서가 물체 안에 들어가지 않았는지, 설정 자산 로딩을 확인합니다. 최소 한 회전 이상 렌더링하세요. 물체/센서가 움직일 때 누적 점군의 과거 점이 남는 현상은 현재 프레임 점군과 구별해야 합니다.

구형 JSON 설정을 가지고 있다면 원본을 새 폴더에 복사한 뒤 설치된 공식 변환기를 사용합니다. `--files`는 복사본을 지정하고 출력 USDA의 OmniLidar schema·scanRate와 emitter 속성을 Stage에서 확인합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/tools/isaacsim.sensors.rtx/convert_lidar_json_to_usda.py" --help
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/tools/isaacsim.sensors.rtx/convert_lidar_json_to_usda.py" --files /absolute/path/to/copied_profile.json
```

여러 profile은 `--variant-to-json-map`으로 variant set에 통합할 수 있습니다. 이 패키지는 JSON 변환기를 복제하지 않고 5.1 설치 도구를 사용합니다. GMO 메타데이터의 원문 보조 예제는 `standalone_examples/api/isaacsim.sensors.rtx/inspect_lidar_metadata.py`, 움직이는 스캐너는 `rotating_lidar_rtx.py`입니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
