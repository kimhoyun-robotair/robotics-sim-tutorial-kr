# 139. RGB와 깊이 데이터를 촬영 후 증강하기

권장 학습 순서 **139** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t044`

이 패키지는 Isaac Sim **5.1.0**의 Data Augmentation 실습을 독립 실행형으로 구성합니다. 빨간 상자의 원본 RGB와 깊이를 촬영하고, **원본 장면은 그대로 두면서 출력 배열을 바꾸는 과정**을 배웁니다. `annotator` 모드는 빨강/파랑 채널 교환과 두 강도의 깊이 노이즈를, `writer` 모드는 RGB→HSV→노이즈→RGB 합성과 파일 저장 직전 깊이 증강을 실행합니다. 각 모드는 NumPy CPU 함수와 Warp GPU 커널을 선택할 수 있습니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 데이터 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--frames` 등으로 요청한 데이터가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0, 지원되는 NVIDIA RTX GPU/드라이버가 필요합니다. 설치에 포함된 NumPy, Pillow, Warp, `omni.replicator.core`를 사용합니다. 다른 로컬 튜토리얼이나 별도 공통 모듈은 필요 없습니다. 여기서는 기본 도형과 내장 OmniPBR 재질을 만들어 외부 환경 USD를 내려받지 않습니다.

Linux 터미널에서 이 패키지 폴더로 이동한 뒤 실행합니다. 설치 경로가 다르면 첫 줄을 바꿉니다.

```bash
ISAACSIM="$HOME/isaacsim"
python3 run.py --help
"$ISAACSIM/python.sh" run.py --headless --frames 3 --output output/numpy_annotator
"$ISAACSIM/python.sh" run.py --headless --backend warp --frames 3 --output output/warp_annotator
"$ISAACSIM/python.sh" run.py --headless --mode writer --output output/numpy_writer
"$ISAACSIM/python.sh" run.py --headless --mode writer --backend warp --output output/warp_writer
```

Windows에서는 같은 인수를 설치 폴더의 `python.bat`에 전달합니다. 기본 출력 위치는 이 패키지의 `output/`입니다. **출력 폴더가 이미 존재하면 중단**하므로 반복 실습에는 새 `--output` 경로를 지정합니다. `--headless`와 `--steps`를 생략하면 지정한 프레임의 캡처와 저장을 마친 뒤에도 화면을 직접 닫을 때까지 유지합니다.

## 순서대로 해보기

1. `filters.py`의 `swap_red_blue()`를 읽습니다. RGBA 배열의 앞 세 채널은 색이고 마지막 채널은 투명도입니다. 함수가 복사본을 만드는 이유는 다른 annotator가 공유할 수 있는 원본 배열을 손상하지 않기 위해서입니다.
2. 첫 명령을 실행하고 `0000_original.png`와 `0000_bgr.png`를 나란히 엽니다. 빨간 물체가 파란 물체로 보여야 합니다. 이것은 실제 USD 재질 변경이 아닌 **출력 데이터 변환**입니다.
3. `measurements.json`을 확인합니다. `red_blue_swap_exact`는 채널별 배열 대조 결과입니다. `small_noise_std_m`과 `large_noise_std_m`는 원본과 차이를 계산한 **유한 깊이 픽셀의 실제 표준편차**입니다. 후자는 전자보다 대체로 커야 합니다. 작은 이미지와 클리핑 때문에 비율이 정확히 5가 되지는 않을 수 있습니다.
4. 원본과 증강 깊이는 `.npy`로 저장됩니다. 8비트 그림으로 정규화하지 않아 미터 단위를 보존합니다. 배경의 `inf`는 광선이 물체와 만나지 않았다는 뜻이고, 비교 통계에서 제외합니다.
5. Warp 모드를 실행합니다. 같은 의미의 연산을 픽셀마다 병렬 실행하지만 NumPy와 Warp의 난수 생성 방식이 달라 두 파일이 비트 단위로 같아야 한다는 요구는 없습니다.
6. Writer 모드의 `writer/` 폴더에서 RGB와 `distance_to_camera` 출력을 확인합니다. 패키지 최상위의 원본 이미지와 비교하십시오. Writer 모드에서 RGB 노이즈 강도는 `run.py`의 `sigma=6.0`이며, CLI `--sigma`는 **깊이 노이즈의 미터 값**입니다.

## API와 USD 개념

| 코드 | 이 실습에서의 역할 |
|---|---|
| `SimulationApp` | Kit, 렌더러, 확장을 초기화합니다. `omni`와 `pxr`를 먼저 import하면 확장 로더가 준비되지 않을 수 있습니다. |
| `rep.create.cube/material_omnipbr/camera` | USD Stage에 도형, 재질, 카메라 prim을 만듭니다. Prim은 `/World/...` 같은 경로로 식별되는 장면 요소입니다. |
| `create.render_product(camera, resolution)` | 카메라와 해상도를 연결한 렌더 출력입니다. 카메라 prim만으로 픽셀 배열이 생기지는 않습니다. |
| `AnnotatorRegistry.get_annotator()` | RGB나 거리 같은 데이터 계산기를 가져옵니다. `attach(product)`로 어느 출력에서 읽을지 지정합니다. |
| `Augmentation.from_function()` | NumPy 함수 또는 Warp 커널을 Replicator 증강 노드로 연결합니다. Warp의 `data_out`은 별도 출력 버퍼입니다. |
| `annotator.augment()` | 그 annotator 뒤에 변환을 붙이고 매개변수를 덮어쓸 수 있습니다. |
| `augment_compose()` | 앞 변환의 결과를 다음 변환의 입력으로 순서대로 전달합니다. |
| `writer.add_annotator()` / `augment_annotator()` | Writer가 저장하는 데이터 경로에 증강을 적용합니다. `name='rgb'`는 기존 RGB 슬롯을 대체합니다. |
| `orchestrator.step(rt_subframes=8)` | 무작위화와 렌더링·데이터 수집을 실행합니다. subframe은 같은 시점에서 렌더 품질을 안정시키는 반복입니다. |

USD Stage의 길이 단위는 미터로 설정합니다. `distance_to_camera`는 카메라에서 픽셀에 해당하는 표면점까지의 거리이며, 카메라 광축 방향의 깊이인 `distance_to_image_plane`과 다릅니다. 이 구현은 배경 `inf`를 원본 그대로 남기고 음수 깊이만 0으로 제한합니다.

`/app/omni.graph.scriptnode/opt_in`은 이번 실행에서 함수 기반 증강을 실행할 수 있도록 설정합니다. 프로젝트 전체 설정 파일을 변경하지 않습니다. `finally: app.close()`는 오류가 나도 Kit 자원을 닫습니다.

## 한 변수만 바꾸는 실험

같은 `--seed 23`으로 `--sigma 0.02`와 `--sigma 0.2`를 각각 새 출력 폴더에 실행합니다. 그림의 밝기 대신 `.npy` 차이의 표준편차를 비교하십시오. 깊이 노이즈 강도가 10배가 되었는지 측정하고, `sigma`가 0일 때 깊이 차이가 0인지도 확인할 수 있습니다.

## 문제 해결과 범위

- `No module named isaacsim/omni`: 일반 Python은 도움말만 지원합니다. 실행에는 설치의 `python.sh`/`python.bat`를 사용합니다.
- 증강 컴파일/ScriptNode 오류: 5.1 설치의 Warp/Replicator 조합인지 확인하고, NumPy 모드로 동일한 장면을 먼저 관찰합니다.
- 모든 깊이가 무한대: 빈 stage 또는 카메라 방향 문제입니다. 이 스크립트는 유한 픽셀이 없으면 성공으로 처리하지 않습니다.
- 원본 문서의 Grid 환경 로드는 이 패키지에서 자체 생성 평면으로 대체했습니다. 공식 문서의 두 적용 경로와 CPU/GPU 커널은 모두 실제 코드에 포함됩니다.
- 저장된 값과 속도 수치는 실행 때 생성됩니다. 문법/도움말 검사만으로 GPU 실행이나 성능을 검증했다고 간주하지 않습니다.

## 출처

- [Isaac Sim 5.1.0: Data Augmentation — Annotator Augmentation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_augmentation.html#annotator-augmentation)
- [Isaac Sim 5.1.0: Writer Augmentation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_augmentation.html#writer-augmentation)
- 설치본 비교 경로: `standalone_examples/replicator/augmentation/annotator_augmentation.py`, `writer_augmentation.py`. 이 패키지는 위 예제를 그대로 실행하는 래퍼가 아니라 같은 API 흐름을 작은 장면으로 다시 구성한 코드입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
