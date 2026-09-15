# 170. t043 · Carter 주행 영상을 Cosmos 입력 데이터로 저장하기

권장 학습 순서 **170** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t043`

창고를 주행하는 Nova Carter의 전방 카메라에서 RGB, 깊이 시각화, 객체 분할, 음영이 있는 분할, edge 영상을 같은 프레임 번호로 저장한다. 이 결과는 Cosmos Transfer의 입력 제어 신호이다. **이 실습의 `run.py`는 Isaac Sim 렌더링을 실행하며, 생성형 Cosmos 모델 추론은 실행하지 않는다.** `prepare_transfer.py`는 실제 캡처 결과를 검사하고 원문 형식의 Transfer 입력 JSON을 만든다.

공식 튜토리얼의 standalone 방식을 로컬 실행 코드로 구현했다. 카메라·창고·Carter 경로와 Writer API는 Isaac Sim **5.1.0**을 따른다. 다른 로컬 패키지나 공통 모듈이 필요 없다.

## 이 실습의 의도

Carter의 같은 주행 시점을 RGB·깊이 시각화·분할·음영 분할·edge라는 다섯 표현으로 저장하고, 이들이 Cosmos Transfer에 넘길 제어 입력으로 어떻게 대응하는지 익힌다. 여러 clip으로 나누어도 로봇 위치를 초기화하지 않아 연속 주행의 구간을 비교할 수 있다. 기본 실행은 시뮬레이션 캡처와 영상 인코딩까지이며, `prepare_transfer.py`도 입력 JSON만 만들고 Cosmos 모델 추론을 시작하지 않는다.

## 실행 후 확인할 것

- **주행 장면:** GUI에서 `/NavWorld/CarterNav`와 그 아래 `targetXform`, 전방 카메라가 존재하고 목표 방향으로 장면이 변하는지 본다. 기본 두 clip × 10프레임은 짧은 캡처이므로 목표 도달까지 요구하지 않는다.
- **프레임 대응:** 각 `clip_0000`, `clip_0001`에서 같은 번호의 `rgb`, `depth`, `segmentation`, `shaded_seg`, `edges` PNG를 열어 물체 위치와 경계가 대응하는지 확인한다. depth는 미터값 원본 배열이 아니라 시각화 영상이다.
- **clip 저장:** 각 clip의 다섯 MP4가 존재하고 실제 재생되는지 본다. 번호는 다음 clip에서 다시 시작하지만 주행은 이어지므로, clip 경계에서 첫 로봇 위치로 되돌아가야 하는 것은 아니다.
- **시간 해석:** `capture_times.json`의 `clip`, `frame`, `timeline_seconds`를 비교한다. 파일의 시뮬레이션 시각을 기준으로 표본 간격을 읽고, MP4 재생 FPS를 물리 진행 속도로 대신 해석하지 않는다.
- **Transfer 준비 범위:** `prepare_transfer.py`가 같은 PNG 번호 집합을 확인한 뒤 만든 JSON의 `input_video_path`, `depth.input_control`, `seg.input_control`이 실제 clip 파일을 가리키는지 확인한다. 이 검사는 영상 디코딩이나 생성형 모델 결과를 검증하지 않는다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 데이터 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--frames` 등으로 요청한 데이터가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비 및 첫 실행

- Isaac Sim 5.1.0, RTX GPU와 지원 드라이버가 필요하다. `CosmosWriter`의 CUDA annotator 및 video encoding 기능을 사용한다.
- 5.1 asset root에서 `/Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd`와 `/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd` 및 해당 참조 자산을 읽을 수 있어야 한다. 원격 자산 사용 시 네트워크가 필요하다.
- 이 두 stage에는 주행을 위한 OmniGraph와 Script Node가 포함된다. 프로그램은 공식 예제처럼 Script Node opt-in을 켠다. 사용자 로봇으로 교체하려면 같은 navigation target/camera prim 경로 계약을 직접 맞춰야 한다.

```bash
cd /path/to/170_replicator_replicator_cosmos
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py --headless --clips 2 --frames 10 --output output/first
```

`--headless`와 `--steps`를 생략하면 정해진 프레임의 캡처와 저장을 마친 뒤에도 창을 직접 닫을 때까지 유지한다. 기존 출력 경로에는 쓰지 않는다. `--frames`는 **clip 하나당** 프레임 수다. 기본값으로 두 clip, 각 10장, 총 20개의 동기화된 시점을 저장한다.

## 단계별 실습

1. 먼저 도움말을 읽고 기본 `capture-interval=2`, `start-delay=0.1`을 확인한다. 최초 0.1초는 자산·주행 준비 시간이며 저장할 데이터에는 포함하지 않는다.
2. 위 명령을 실행한다. 창고 stage를 연 뒤 `/NavWorld/CarterNav`에 로봇을 참조로 추가하고 시작 위치 `(-6,4,0)`, 목표 위치 `(3,3,0)`를 설정한다.
3. `output/first/clip_0000/rgb/rgb_0000.png`와 같은 번호의 `depth`, `segmentation`, `shaded_seg`, `edges` 파일을 비교한다. 물체 경계가 같은 영상 위치에 있어야 한다. depth는 거리값을 색으로 변환한 **시각화**이며, PNG 채널 값을 미터 단위 거리로 직접 읽으면 안 된다.
4. 각 clip의 `rgb.mp4`, `depth.mp4`, `segmentation.mp4`, `shaded_seg.mp4`, `edges.mp4`를 재생한다. clip 전환 시 프레임 번호는 0000부터 다시 시작한다. 로봇 위치는 reset하지 않아 연속 주행의 다음 구간이 된다.
5. `capture_times.json`을 열어 실제 관측한 timeline 초를 비교한다. capture 사이에 app update를 넣기 때문에 장면이 진행한다. 이 값은 측정값이며 영상 인코딩 FPS와 같다고 가정하지 않는다.
6. 다음 명령으로 다섯 모달리티의 PNG 번호 집합과 비어 있지 않은 MP4 파일을 검사하고 Transfer 입력을 만든다.

```bash
python3 prepare_transfer.py --clip output/first/clip_0000 \
  --output output/first/transfer_control.json
```

검사는 PNG 번호의 일치와 MP4 존재·크기를 확인한다. 동영상 디코딩, 물리 주행 정확성, 모델 추론 품질은 별도 관찰 대상이다.

## 코드에서 배우는 API와 USD

| 코드 | 이 실습에서의 역할 |
|---|---|
| `SimulationApp` | standalone 프로세스에서 Kit 런타임을 시작한다. `omni`, `carb`, `pxr` 기반 scene 작업은 이 뒤에 실행한다. |
| `open_stage()` | 창고 USD와 그 reference를 합성하여 Stage를 만든다. Stage는 전체 장면, prim은 경로로 찾는 개별 객체다. |
| `add_reference_to_stage()` | 로봇 파일을 `/NavWorld/CarterNav` prim 아래에 합성한다. 파일을 직접 수정하지 않고 현재 장면의 위치를 설정한다. |
| `UsdGeom.Xformable` / `xformOp:translate` | prim의 이동 연산이다. 목표점은 `/targetXform`, 카메라는 `/chassis_link/sensors/front_hawk/left/camera_left`이다. |
| `rep.create.render_product` | 전방 Camera prim과 1280×720 렌더 출력을 연결한다. 이것이 writer의 입력이다. |
| `rep.WriterRegistry.get("CosmosWriter")` | 다섯 모달리티를 같이 저장하는 내장 writer를 얻는다. 별도 학습 모델을 불러오는 API가 아니다. |
| `set_capture_on_play(False)` | Play에 따른 자동 저장을 끄고, 명시한 `step()`만 저장하게 한다. |
| `step(pause_timeline=False)` | 렌더 데이터 한 시점을 수집하면서 주행 timeline을 계속 실행한다. |
| `writer.next_clip()` | 현재 clip의 PNG 쓰기를 완료하고 MP4를 인코딩한 뒤 다음 clip 번호를 준비한다. 마지막 clip에도 호출하여 인코딩을 마친다. |
| `wait_until_complete()` / `detach()` | 남은 데이터를 기다리고 writer 연결을 해제한다. `finally`에서 render product와 앱도 정리한다. |

`use_instance_id=True`는 semantic label 없이 개체를 구분하는 기본 방식이다. 분할 색은 학습 클래스 이름을 뜻하지 않는다. 제공한 `semantic_mapping.json`은 `floor`, `wall`, `rack` 클래스에 RGBA를 지정한다. 다음 실행은 **stage에 그 semantic class가 실제로 붙어 있을 때** 의미가 있다.

```bash
"$HOME/isaacsim/python.sh" run.py --headless --frames 10 \
  --semantic-mapping semantic_mapping.json --output output/semantic
```

mapping이 있으면 writer는 instance ID 설정보다 semantic mapping을 우선한다. class label이 없는 사용자 자산에 mapping 파일만 공급해도 라벨이 자동 생성되지는 않는다.

## Cosmos Transfer로 넘기는 경계

`transfer_control.json`에는 `input_video_path`와 `vis`, `edge`, `depth`, `seg` 제어 가지가 있다. 기본은 각 weight 0.25로 합이 1이다. `depth`와 `seg`의 `input_control`은 캡처한 파일의 절대 경로다. 단일 edge 실험은 `prepare_transfer.py --edge-only`로 별도 JSON을 만든다.

이 JSON 스키마는 [Isaac Sim 5.1의 Using Data with Cosmos Transfer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html#using-data-with-cosmos-transfer)에 수록된 Transfer 방식이다. 모델을 실제 실행하려면 [NVIDIA Cosmos Transfer 공식 참조](https://docs.nvidia.com/cosmos/latest/transfer/reference.html)의 **해당 Transfer 모델 버전** 환경, 모델 가중치, 요구 GPU 메모리, 입력 해상도/길이 조건을 별도로 준비한다. 짧은 10프레임 검증 clip이 선택한 모델의 길이 조건을 충족한다고 가정하지 않는다. 외부 문서의 `latest`는 Isaac Sim 5.1에 고정되지 않으므로 선택한 모델 버전과 명령을 결과와 함께 기록한다. 생성형 결과가 원본 semantic/depth의 완벽한 정답 영상이라고도 가정하지 않는다.

## 한 변수 실험

`--canny-low 30 --canny-high 150`만 바꾸고 새로운 출력 경로에 실행한다. 기본 10/100과 `edges.mp4`의 약한 경계·노이즈 양을 비교한다. 이 Writer의 edge 입력은 shaded segmentation annotator에 Canny를 적용한 결과이다. 단순히 RGB의 모든 텍스처 경계가 추출될 것이라고 예상하면 관찰이 어긋난다.

또 다른 실험으로 `--capture-interval`만 4로 바꾸면 저장 프레임 사이 장면 변화가 커질 수 있다. MP4 인코딩은 writer가 읽은 timeline FPS를 사용하므로 `capture_times.json` 없이 영상 재생 시간만으로 시뮬레이션 속도를 추론하지 않는다.

## 문제 해결과 검증 범위

- stage/camera 누락 오류: 5.1 공식 자산 경로와 asset root 연결을 확인한다. warehouse만 열리고 Carter reference가 실패하면 카메라도 없다.
- 움직이지 않는 로봇: Script Node opt-in, navigation graph, 장애물과 target 위치를 확인한다. `--target X Y Z`로 창고 내부의 접근 가능한 목표를 설정한다.
- 분할이 배경뿐이면 semantic label 유무를 확인하고 기본 instance ID 모드로 돌아가 비교한다.
- PNG만 있고 MP4가 없으면 video encoding 오류를 확인한다. 코드는 파일 누락을 실제 실패로 보고하며 성공 메시지를 내지 않는다.
- 작성 과정에서는 Python compile·도움말 및 설치본 API 대조만 수행했다. GPU 캡처, MP4 디코딩 및 Cosmos 모델 추론은 실행하지 않았다.

## 출처

- [Isaac Sim 5.1 · Cosmos Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html)
- [출력 구조](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html#output-structure), [semantic mapping와 edge 조절](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html#advanced-usage)
- API 대조: 설치본 `standalone_examples/api/isaacsim.replicator.examples/cosmos_writer_warehouse.py`, `omni.replicator.core` 1.12.27의 `scripts/writers_default/cosmos.py`. 공식 문서의 여러 clip 실습을 로컬 argparse 실행으로 재구성했다.
