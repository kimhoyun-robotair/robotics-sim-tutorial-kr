# 75. RTX annotator의 한 프레임과 누적 스캔

권장 학습 순서 **75** · 센서와 측정 데이터 · 출처 ID `t150`

하나의 OmniLidar render product에 두 annotator를 연결해 프레임별 점군과 한 회전 누적 스캔의 차이를 직접 기록합니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/75_sensors_sensors_rtx_annotators
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

1. 실행 후 `measurements.json`의 counts에서 `IsaacExtractRTXSensorPointCloudNoAccumulator`와 `IsaacCreateRTXLidarScanBuffer`의 프레임별 점 수를 비교합니다.
2. `annotators.npz`에서 누적 annotator의 data, distance, intensity, timestamp 배열을 확인합니다. 옵션은 attach 전에 initialize되어야 하며 코드의 `attach_annotator(..., outputTimestamp=True, ...)`가 이를 수행합니다.
3. `--scan-hz 5 --output output/slow-scan`으로 한 값만 바꿉니다. 60 Hz 렌더링에서 한 회전에 필요한 프레임이 늘면서 두 버퍼의 의미가 어떻게 달라지는지 봅니다.
4. 센서를 움직이는 실험을 추가하면 누적 점군에 이전 프레임 위치가 섞일 수 있습니다. 현재 프레임 점군과 같은 시간의 측정이라고 비교하지 마세요.
5. 평면 스캔은 `IsaacComputeRTXLidarFlatScan`으로 읽지만 elevation이 0이 아닌 3D Lidar에는 결과가 없습니다. 본 Example_Rotary에 무조건 flat scan을 붙이지 마세요.

## API와 USD 개념

Annotator는 AOV를 사용자가 읽을 배열로 변환하는 데이터 처리기이고 Writer는 저장/표시 목적의 소비자입니다. `LidarRtx.get_current_frame()`은 annotator 이름별 데이터 사전입니다. `GenericModelOutput`은 센서 렌더러의 원시 출력 버퍼입니다.

RTX annotator는 timeline이 Play여야 데이터가 갱신됩니다. GMO 내부 timestamp는 App Ready부터 증가하는 시계여서 animation timeline pause와 별개입니다. pause/resume 사이 timestamp가 불연속일 수 있습니다. RTX 데이터 수집은 `app.update` 또는 이를 사용하는 `world.step`으로 하며 Replicator orchestrator.step으로 대체하지 않습니다.

GPU 내부 버퍼 설정 `/app/sensors/nv/lidar/outputBufferOnGPU`와 radar 대응 설정을 false로 바꾸면 annotator가 제대로 동작하지 않을 수 있습니다. 출력 numpy 배열이 CPU에서 읽힌다는 것과 내부 GMO가 GPU에 있어야 한다는 조건은 다릅니다.

## 확장 실습·성공 기준·문제 해결

추가 출력 조건: emitterId는 auxOutputType BASIC 이상, materialId/objectId는 EXTRA 이상, normal/velocity는 FULL이 필요합니다. normal은 `/app/sensors/nv/lidar/publishNormals=true`도 필요하며 VRAM 비용이 있습니다. objectId는 `/rtx-transient/stableIds/enabled=true`가 필요합니다.

Object ID는 `uint8` 한 개가 아니라 **16바이트씩 묶은 128-bit ID**입니다. `LidarRtx.get_object_ids`로 해석하고 `decode_stable_id_mapping`으로 StableIdMap을 prim 경로에 연결한 뒤 prim의 semantic label을 읽습니다. 버퍼를 uint8 숫자 하나씩 class 번호처럼 사용하지 마세요. 이 경로의 설치 원본 예제는 `standalone_examples/api/isaacsim.sensors.rtx/resolve_object_ids_from_gmo.py`이고, GMO 구조를 직접 읽는 예제는 `inspect_lidar_metadata.py`입니다. 각각 실행 전 소스의 센서 설정/필요 에셋을 확인하고 출력 objectId를 Stage prim 경로와 대조하세요.

4.5의 RtxSensorCpu/GpuIsaacCompute*PointCloud와 IsaacReadRTXLidarData는 5.0에 제거/대체되었습니다. 본 예제는 새로운 공통 point-cloud annotator를 사용합니다. 반환이 없으면 한 회전 이상의 프레임, timeline, GPU buffer 설정부터 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
