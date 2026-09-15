# 63. 이상적 깊이와 깊이 센서 후처리 비교

권장 학습 순서 **63** · 센서와 측정 데이터 · 출처 ID `t146`

두 높이의 상자를 위에서 촬영해 이상적 image-plane depth와 stereo를 근사하는 단일 시점 depth 후처리를 함께 저장합니다. 외부 환경 없이 독립 실행하며 원문의 SingleViewDepthSensor 경로를 사용합니다.

## 이 실습의 의도

동일한 카메라에서 기하학적 깊이와 stereo 특성을 근사한 후처리 깊이를 동시에 얻어, 센서 모델의 출력이 이상적 거리와 어떻게 다른지 익힌다. 높이 0.5 m와 1.2 m의 고정 상자를 높이 4 m에서 내려다보도록 만들어 거리 차이를 장면 치수로 해석할 수 있게 했다. 기본 실행은 두 깊이 배열의 마지막 프레임과 유효 픽셀 통계를 저장하며, 별도 `add_depth_sensor.py`는 재사용할 Camera/RenderProduct 설정을 USD로 작성한다.

## 실행 후 확인할 것

- **장면 치수와 이상적 깊이**: `depth.npz`의 `distance_to_image_plane`에서 바닥은 약 4 m, 낮은 상자 윗면은 약 3.5 m, 높은 상자 윗면은 약 2.8 m인지 해당 표면 픽셀을 비교한다. 전체 이미지 중앙값이 각각의 상자 거리와 같아야 하는 것은 아니다.
- **두 출력의 유효성**: `measurements.json`에서 `DepthSensorDistance`와 `distance_to_image_plane` 각각의 `shape`, `valid_pixels`, `median_m`을 확인한다. 유한한 양수 픽셀이 두 출력 모두에 있어야 하며, 초기 AOV가 비어 있다가 채워지는 것과 마지막까지 유효 깊이가 없는 상태를 구별한다.
- **후처리 변수의 의미**: baseline 기본 55와 비교값 110의 단위는 mm이고 저장 깊이는 m다. `--noise-sigma 0`은 분산을 줄이지만 코드의 `noise_mean=0.5`와 disparity·거리 제한은 남으므로 이상적 깊이와 완전히 같아질 것을 요구하지 않는다.
- **한 프레임의 저장과 GUI**: 카메라 30 Hz를 물리·렌더 60 Hz로 갱신한 뒤 기본 240스텝 시점의 배열 한 쌍을 저장한다. 이후 GUI의 Disparity 색은 시각화이며, 기존 NPZ가 계속 갱신되거나 색 자체가 m 단위 거리가 되는 것은 아니다.
- **자산 작성의 별도 결과**: `add_depth_sensor.py`를 실행했다면 `/root/Camera`, `/root/TemplateRenderProduct` 아래 설정과 baseline 42 mm가 저장된 USD를 확인한다. 이 파일을 작성한 것만으로 장면의 깊이 측정을 수행한 것은 아니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/63_sensors_sensors_camera_depth
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 렌더링·깊이 센서 갱신이 계속됩니다. 처음 240스텝을 마친 시점의 두 깊이 배열과 통계를 한 번 저장하며, 이후 관찰 중에는 파일을 추가하거나 바꾸지 않습니다. `--steps N`에 양수를 주면 N스텝 뒤 스냅샷을 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 실행 후 `depth.npz`의 `DepthSensorDistance`와 `distance_to_image_plane`을 비교합니다. `measurements.json`에는 각 유효 픽셀 수와 거리 중앙값이 있습니다. 바닥까지의 높이는 4 m이고 상자 표면은 더 가깝습니다.
2. `--headless`와 `--steps` 없이 실행해 `/World/Depth` 카메라로 viewport를 전환합니다. **Render Settings > Post Processing > Depth Sensor**를 켜고 **RGB Depth Output Mode > Disparity**를 선택하면 disparity를 볼 수 있습니다.
3. `--baseline-mm 110 --output output/baseline-110`으로 다시 실행해 기존 55 mm와 비교합니다. 다른 값은 유지하세요.
4. `--noise-sigma 0 --output output/noise-0`으로 실행하여 노이즈가 있는 기본 출력과 구별합니다. 깊이 AOV와 시각화 이미지의 색을 실제 m 값으로 혼동하지 마세요.
5. 원문의 에셋 wrapper 실습은 Script Editor에서 아래 코드를 실행합니다. stage가 이미 열려 있는 GUI에서만 실행하며 센서 카메라 경로 목록을 보고 해당 render product의 depth schema를 확인합니다.

## API와 USD 개념

`SingleViewDepthSensor`는 `Camera`를 감싸며 **render product별** depth 후처리 속성을 설정합니다. GUI의 전역 Render Settings는 모든 render product에 영향을 주므로 비교할 때 전역 설정을 바꿨는지 기록하세요. `DepthSensorDistance`에는 disparity, noise, confidence, min/max 거리의 영향이 있고 `distance_to_image_plane`은 기하학적 기준 깊이입니다.

stereo의 disparity는 대략 `fx × baseline / depth`와 연결됩니다. baseline은 이 API에서 mm, fx는 픽셀, 반환 거리의 장면 단위는 m입니다. 이는 하나의 렌더 시점으로 stereo 특성을 근사하는 모델이며 ToF·structured light의 공통 모델이 아닙니다.

## 확장 실습·성공 기준·문제 해결

```python
from isaacsim.sensors.camera import SingleViewDepthSensorAsset
from isaacsim.storage.native import get_assets_root_path
asset = SingleViewDepthSensorAsset('/World/D455', asset_path=get_assets_root_path() + '/Isaac/Sensors/Intel/RealSense/rsd455.usd')
asset.initialize()
print(asset.get_all_depth_sensor_paths())
depth = asset.get_child_depth_sensor('/World/D455/RSD455/Camera_Pseudo_Depth')
depth.attach_annotator('DepthSensorDistance')
```

D455 자산은 NVIDIA 5.1 에셋 접근이 필요합니다. 기본 로컬 실습에는 필요 없습니다. 기존 Camera 자산에 depth 속성을 저장하는 원문 절차는 이 패키지의 `add_depth_sensor.py`로 실행합니다. 생성된 `example_camera_with_depth_sensor.usd`와 현재 열린 Stage에서 Camera에 연결된 RenderProduct와 `omni:rtx:post:depthSensor:baselineMM`을 검사합니다. 이 스크립트도 `--steps`를 생략하면 창을 직접 닫을 때까지 유지합니다. `--steps N`은 Kit 업데이트 N회 후 종료하며, `--headless`만 지정하면 파일을 저장하고 1회 업데이트 후 종료합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" add_depth_sensor.py --output output/depth-asset-01/example_camera_with_depth_sensor.usd
```

새 센서 자산은 외형 import→Camera 배치→실제 영상과 intrinsics/extrinsics 비교→render product depth schema 적용→실제 깊이와 후처리 값 비교 순서로 구성합니다. 초기 첫 프레임의 texture-size/AOV 오류는 원문에 알려진 현상이지만, 이후에도 지속되거나 유효 깊이가 없으면 정상 완료로 보지 마세요.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Depth Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
