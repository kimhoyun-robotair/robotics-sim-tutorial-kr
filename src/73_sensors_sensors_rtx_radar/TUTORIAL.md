# 73. RTX Radar 만들기

권장 학습 순서 **73** · 센서와 측정 데이터 · 출처 ID `t149`

움직이는 상자를 OmniRadar로 읽어 반환 점군을 저장합니다. 외부 창고를 로컬 장면으로 바꿨고 Radar에 필요한 Motion BVH를 명시적으로 켰습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/73_sensors_sensors_rtx_radar
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

1. 기본 명령으로 실행하고 `measurements.json`의 반환 수와 대상의 최종 위치를 확인합니다. `points.npy`는 마지막으로 받은 비어 있지 않은 점군입니다.
2. GUI 실행에서 Stage의 `/World/Radar`를 골라 타입이 `OmniRadar`, 적용 schema가 `OmniSensorGenericRadarWpmDmatAPI`인지 확인합니다.
3. `--target-speed 0 --output output/static`으로 같은 표적을 정지시키고 반환 분포를 비교합니다. 기본 이동 속도는 -0.5 m/s이며 장면의 x 방향으로 접근합니다.
4. 코드를 읽어 `IsaacSensorCreateRtxRadar` 뒤 render product와 `IsaacExtractRTXSensorPointCloudNoAccumulator` 연결 순서를 확인합니다. renderer 결과는 `GenericModelOutput` AOV에서 옵니다.
5. 물체의 재질·입사각을 바꾸면 반사 반응이 달라질 수 있습니다. 센서가 물체를 바라보고 FOV 안에 있는 조건을 먼저 확인하세요.

## API와 USD 개념

Radar는 전파 영역의 반사와 Doppler를 모델링합니다. `SimulationApp(enable_motion_bvh=True)`는 시간에 따른 geometry 위치를 렌더러에 제공해 Doppler 계산이 가능하도록 합니다. 화면상 물체가 움직인다는 사실만으로 Radar의 속도 추정이 올바른 것은 아닙니다.

이 패키지의 point-cloud annotator는 Cartesian 반환 위치를 수집합니다. 저장한 점군에는 검증된 Doppler 속도 필드가 없으므로 `target_speed`와 속도 추정 정확도를 비교했다고 해석하면 안 됩니다. `target_final_position`은 물리 엔진의 상태입니다.

5.1은 OmniRadar prim을 사용합니다. 이전 Camera 기반 `sensorModelPluginName`/JSON 경로는 deprecated입니다. quaternion은 w,x,y,z이며 단위는 m입니다.

## 확장 실습·성공 기준·문제 해결

반환이 모두 비어 있으면 GPU, Motion BVH, timeline, 물체 위치를 확인합니다. `--steps 240`에서 물체는 센서 앞에 남지만 너무 긴 실행과 큰 음의 속도는 물체가 센서를 지나가게 합니다.

원문의 창고 debug draw 실험은 설치 예제 `standalone_examples/api/isaacsim.util.debug_draw/rtx_radar.py`입니다. 설치 버전 예제 자체에는 Motion BVH 설정이 빠질 수 있으므로 GUI 실행 시 아래 옵션도 적용합니다. NVIDIA Full Warehouse 에셋 접근이 필요합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/standalone_examples/api/isaacsim.util.debug_draw/rtx_radar.py" --/renderer/raytracingMotion/enabled=true --/renderer/raytracingMotion/enableHydraEngineMasking=true --/renderer/raytracingMotion/enabledForHydraEngines='0,1,2,3,4'
```

원문 command 예제의 tickRate 표기가 본문과 코드에서 다르므로 이 패키지는 기본 tickRate를 사용합니다. 변경 전 실제 OmniRadar prim의 schema 속성을 확인하세요.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — RTX Radar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_radar.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
