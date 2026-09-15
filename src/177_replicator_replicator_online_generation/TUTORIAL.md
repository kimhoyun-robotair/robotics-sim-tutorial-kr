# 177. 메모리에서 바로 학습하는 온라인 합성 데이터

권장 학습 순서 **177** · 사용 중단 문서와 레거시 참고 · 출처 ID `t049`

Isaac Sim 5.1 공식 **Online Generation** 수업이다. 공식 문서에서 **DEPRECATED**로 표시한 예제라 후속 버전 호환을 전제하지 않는다. 이 패키지는 설치된 공식 `online_generation` 구현을 실행하는 native 실습이다. `run.py`는 ShapeNet 파일을 먼저 검사하고, 학습 횟수와 결과 저장 위치를 제한한다. 다른 로컬 튜토리얼은 필요 없다.

## 이 실습의 의도

ShapeNet 물체를 USD로 변환한 뒤 카메라·조명·물체 자세·텍스처가 매번 바뀌는 영상을 만든다. RGB, bounding box, instance mask가 `IterableDataset`에서 곧바로 Mask R-CNN 학습으로 넘어간다. 학습용 이미지 전체를 디스크에 쌓지 않고, 관찰용 PNG만 저장하는 방식이다. 기본 설정의 짧은 10회 학습은 렌더 결과와 정답이 실제 손실 계산·가중치 갱신까지 연결되는지 확인하는 용도이며 정확도 향상을 보장하지 않는다.

## 실행 후 확인할 것

- **변환·파일 검사:** `convert` 후 원본 옆 `ShapeNetCore_nomat/`에 geometry-only USD가 생기고, `audit`에서 plane·watercraft·rocket의 `size_eligible`이 모두 0보다 큰지 확인한다. 파일 검사 통과만으로 GPU 렌더링과 학습이 확인되는 것은 아니다.
- **온라인 표본:** `sample`의 `_out_gen_imgs/domain_randomization_test_image_*.png` 기본 4장을 열어 배치·조명·재질 변화와 RGB/마스크 대응을 본다. USD 파일의 synset 번호와 영상의 학습 클래스 이름을 연결해 읽는다.
- **학습 진행:** `train` 콘솔에 기본 `ITER 0`부터 `ITER 9`까지 실제 loss가 기록되는지 확인한다. loss가 유한한지 보고, 짧은 실행에서 매번 감소하거나 정확한 물체 예측이 나타나야 한다고 요구하지 않는다.
- **예측 표시:** `_out_train_imgs/`의 입력과 예측 시각화를 비교한다. 초기 모델의 예측이 confidence 기준을 넘지 못하면 overlay가 비어 있을 수 있으므로 이미지 존재와 탐지 품질을 분리해서 읽는다.
- **저장 범위:** 출력의 `asset_audit.json`, `command.json`으로 클래스와 실행 인수를 확인한다. 이 native 예제는 학습 checkpoint를 저장하지 않으므로 `.pth`가 없는 것이 이 실습의 동작이며, PNG가 배포 가능한 모델을 뜻하지 않는다.

## 준비와 실행

Linux, RTX GPU, Isaac Sim **5.1.0** 전체 설치, 설치본의 `torch`, `torchvision`, `warp`, `matplotlib`가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 폴더다. ShapeNetCore 데이터는 [ShapeNet](https://shapenet.org)에서 사용 조건에 맞게 직접 확보한다. 이 패키지는 데이터나 모델을 다운로드하지 않는다. 설치된 torchvision의 ResNet backbone 초기화가 사전학습 가중치를 요청할 수 있으므로 네트워크 또는 해당 torch 캐시도 확인한다.

```bash
cd src/177_replicator_replicator_online_generation
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
# /data/ShapeNetCore에는 02691156, 04530566, 04099429 하위 폴더가 있어야 한다.
python3 run.py convert --root /data/ShapeNetCore --max-models 10 --headless --output output/convert
python3 run.py audit --root /data/ShapeNetCore_nomat
python3 run.py sample --root /data/ShapeNetCore_nomat --headless --output output/sample
python3 run.py train --root /data/ShapeNetCore_nomat --headless --output output/train
```

실행기는 Isaac Sim의 `python.sh`를 자식 프로세스로 호출한다. 변환물은 공식 converter 규약대로 **원본 경로 옆 `ShapeNetCore_nomat/`**에 생긴다. 이미 존재하면 덮어쓰지 않는다. sample/train 결과는 지정한 `output` 아래에 저장하며 새 디렉터리를 사용한다. Windows의 원본 진입점은 `python.bat`이지만 이 패키지 실행기는 Linux 기준이다.

`--headless`를 빼고 `--steps`도 생략하면 변환·샘플 생성·학습을 설정한 횟수만큼 완료한 뒤 사용자가 닫을 때까지 Isaac Sim GUI를 유지한다. `--steps 120`은 작업 완료 후 GUI 업데이트를 120회 수행하고 종료한다(`--steps`에는 양의 정수를 지정). `num_test_images`, `training_steps`, `--max-models`는 작업량이며 GUI 대기 시간과 독립적이다. `audit`은 파일 검사만 하므로 창을 열지 않는다. 위 `--headless` 명령은 기존처럼 유한한 작업 후 종료한다.

## 단계별 실습

1. `experiment.json`에서 `categories`와 `synsets`를 함께 읽는다. plane=`02691156`, watercraft=`04530566`, rocket=`04099429`이다. 이름은 표시·학습 클래스, 숫자는 데이터 디렉터리 이름이다.
2. `convert`로 geometry-only USD를 만든다. 재질 없이 변환하는 이유는 randomizer가 재질을 교체하고, 큰 메시를 여러 번 로드할 때 메모리 부담을 줄이기 위해서다.
3. `audit` 출력에서 세 클래스 모두 `size_eligible > 0`인지 확인한다. `max_asset_size_mb`는 USD 파일의 크기 한도이며 GPU 총 메모리 한도가 아니다. 원본 dataset은 기본 70%를 학습에 사용하므로 클래스마다 여러 모델을 준비한다.
4. `sample` 후 `output/sample/_out_gen_imgs/domain_randomization_test_image_*.png` 네 장을 연다. RGB 영상과 마스크에서 같은 물체가 대응하는지, 배경까지 한 물체로 묶이지 않는지 본다.
5. `train` 콘솔의 `ITER`와 loss를 확인한다. `output/train/_out_train_imgs/`에는 예측 시각화가 생긴다. 공식 학습 예제는 가중치 checkpoint 저장을 구현하지 않으므로 이 결과를 배포 가능한 모델 파일로 오해하지 않는다.
6. 설치본 `standalone_examples/replicator/online_generation/generate_shapenet.py`의 `__next__`, `setup_replicator`, `_instantiate_category`를 열고 아래 설명과 대응시킨다. 설치본을 수정하지 않고 실험 변수는 로컬 JSON에서 바꾼다.

## API와 USD 개념

`SimulationApp`이 Kit와 확장을 시작한 뒤 Replicator API를 사용할 수 있다. `rep.randomizer.instantiate(..., mode="reference")`는 USD asset을 reference로 조합한다. **Prim**은 장면 그래프의 물체·카메라·조명 같은 노드이고 **reference**는 다른 USD 파일의 내용을 연결하는 구성 방식이다.

`rep.trigger.on_frame()` 안의 그래프가 `rep.orchestrator.step()`마다 실행된다. `get_data(device="cuda")`로 읽은 영상·마스크를 `warp.to_torch`로 PyTorch 텐서로 연결한다. RGB는 alpha를 제외하고 `[H,W,3] → [3,H,W]`, 값은 `0..255 → 0..1`로 바뀐다. box의 `semanticId`를 클래스 번호로 바꾸며 배경은 0, 물체 클래스는 1부터 시작한다. 자식 mesh들의 instance mask는 같은 상위 물체 prim 기준으로 합친다. box 면적이 0이거나 화면 전체인 표본은 제거한다.

`DataLoader`의 `collate_fn`은 영상마다 물체 수가 달라도 목록으로 묶어 준다. Kit 한 인스턴스에 묶인 생성기이므로 여러 worker 프로세스를 추가하지 않는다. 학습은 `model(images, targets) → loss → zero_grad → backward → optimizer.step` 순서다. 이 패키지는 원본의 `i > max_iters` 종료 조건을 고려해 정확히 `training_steps`회 업데이트하도록 한도를 전달한다.

## 하나만 바꿔 보기와 문제 해결

다른 값은 그대로 두고 `max_asset_size_mb`를 10에서 5로 낮춘 뒤 `audit`의 사용 가능 파일 수와 sample 속도를 비교한다. 새 `--output output/sample_5mb`를 쓴다. 분할 뒤 쓸 모델이 없으면 모델 수를 늘리거나 크기 제한을 완화한다. CUDA out-of-memory이면 다른 GPU 앱을 종료하고 학습 횟수·모델 크기를 줄인다. `No module named ...`는 system Python에 설치하라는 뜻이 아니라 `ISAAC_SIM_PATH`와 공식 배포본의 환경을 먼저 점검할 신호다.

검증 범위: Python 문법·`--help` 확인. ShapeNet 변환, RTX 생성, 실제 학습은 데이터/GPU 조건을 갖춘 환경에서 별도 실행해야 한다.

`native_runner.py`는 설치된 예제를 실행하면서 앱 종료만 이 패키지에서 관리한다. 정상적으로 작업을 끝낸 뒤 `app.update()`로 창을 유지하며 학습이나 샘플 생성을 다시 반복하지 않는다. 오류 또는 원본 예제의 조기 `sys.exit()`에서는 GUI 대기를 수행하지 않는다. Isaac Sim 설치 파일은 수정하지 않는다.

## 출처

- [Isaac Sim 5.1 Online Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html)
- [Mesh Converter](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html#mesh-converter), [DataLoader core](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html#the-dataloader-core), [Train](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html#train)
- 구현 근거: Isaac Sim 5.1 배포본 `standalone_examples/replicator/online_generation/{usd_convertor,generate_shapenet,train_shapenet}.py`.
