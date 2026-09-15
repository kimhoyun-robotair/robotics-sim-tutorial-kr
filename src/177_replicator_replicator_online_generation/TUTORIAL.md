# 177. 합성 이미지를 저장하지 않고 곧바로 학습에 쓰기

## 이번에 배우는 것

**새로 렌더링한 영상·상자·마스크를 PyTorch 텐서로 전달해 Mask R-CNN의 학습 단계까지 연결합니다.**

보통 데이터셋은 이미지를 디스크에 저장한 뒤 학습기가 다시 읽습니다. 온라인 생성에서는 학습기가 다음 표본을 요청할 때 시뮬레이터가 새 배치를 만들고 결과를 바로 넘깁니다. 데이터 생성과 학습이 같은 실행 흐름 안에 있는 셈입니다.

| 실행 단계 | 입력 | 결과 |
|---|---|---|
| `convert` | 사용자가 준비한 ShapeNet OBJ | geometry-only USD |
| `audit` | 변환된 USD 폴더 | 클래스별 사용 가능 파일 수 |
| `sample` | USD와 `experiment.json` | 관찰용 PNG, 기본 4장 |
| `train` | 실시간 합성 표본 | 기본 10회 손실 계산·가중치 갱신과 관찰 이미지 |

이 튜토리얼은 공식적으로 사용 중단된 **Isaac Sim 5.1 예제**를 실행합니다. 짧은 학습은 데이터 연결을 확인하는 용도이며 학습 정확도를 보장하지 않습니다.

## 1. 변환·검사·샘플 생성 순서로 실행하기

Linux, RTX GPU와 Isaac Sim 5.1 전체 설치가 필요합니다. 설치된 online generation 예제가 사용하는 `torch`, `torchvision`, `warp`, `matplotlib`도 준비되어 있어야 합니다. ShapeNet 데이터는 [ShapeNet](https://shapenet.org)의 사용 조건에 맞게 직접 확보하세요. 이 저장소는 해당 데이터셋을 포함하지 않습니다.

`/data/ShapeNetCore`에 아래 세 종류의 원본이 있다고 가정합니다.

| 클래스 | 폴더 이름인 synset |
|---|---|
| plane | `02691156` |
| watercraft | `04530566` |
| rocket | `04099429` |

저장소 루트에서 실행합니다. 설치 위치가 다르면 각 명령에 `--isaac-sim /실제/설치경로`를 추가하세요. 기본은 `~/isaacsim` 또는 `ISAAC_SIM_PATH` 환경변수입니다.

```bash
python3 src/177_replicator_replicator_online_generation/run.py convert \
  --root /data/ShapeNetCore --max-models 10 --headless \
  --output src/177_replicator_replicator_online_generation/output/convert_first
python3 src/177_replicator_replicator_online_generation/run.py audit \
  --root /data/ShapeNetCore_nomat
python3 src/177_replicator_replicator_online_generation/run.py sample \
  --root /data/ShapeNetCore_nomat --headless \
  --output src/177_replicator_replicator_online_generation/output/sample_first
```

변환물은 `--output`이 아니라 원본 옆의 **`ShapeNetCore_nomat/`**에 생깁니다. 이는 설치된 converter의 규약입니다. 기존 변환 폴더가 있으면 덮어쓰지 않습니다. `--output`에는 실행 기록과 관찰 결과를 남기며 매번 새 경로를 사용합니다.

`audit`은 일반 Python으로 파일을 읽고 종료합니다. 다른 단계는 Isaac Sim `python.sh`로 설치된 예제를 시작합니다. `--headless`를 빼면 GUI를 볼 수 있고 작업이 끝나도 창이 남습니다. `--steps 120`은 **작업 완료 후** GUI 업데이트 횟수입니다.

### 설정에서 볼 부분

`experiment.json`의 주요 값입니다.

```text
"max_asset_size_mb": 10,
"num_test_images": 4,
"training_steps": 10,
"learning_rate": 0.0001
```

파일 크기 한도는 USD 하나가 읽을 대상에 포함되는지 판단하는 조건입니다. GPU 총 메모리를 10 MB로 제한하는 설정은 아닙니다. `audit`은 클래스마다 한도 이하 파일이 있는지 확인하지만, 원본 생성기의 학습 분할 이후까지 충분한지는 별도로 살펴봐야 합니다. 각 클래스에 여러 모델을 준비하세요.

### 실행 결과 확인하기

`audit`의 `files`는 검색된 파일 수, `size_eligible`은 크기 조건을 통과한 수입니다. 모든 클래스에서 0보다 커야 다음 단계로 진행할 수 있습니다.

`output/sample_first/_out_gen_imgs/domain_randomization_test_image_*.png` 기본 4장을 열어 보세요. 물체 자세·조명·재질이 달라지는지, RGB와 마스크가 같은 물체를 가리키는지 확인합니다. 출력의 `asset_audit.json`, `command.json`에는 실제 사용한 파일 수와 외부 실행 인수가 남습니다.

## 2. 렌더링 표본을 학습 텐서로 연결하기

샘플이 의도대로 보이면 학습을 실행합니다.

```bash
python3 src/177_replicator_replicator_online_generation/run.py train \
  --root /data/ShapeNetCore_nomat --headless \
  --output src/177_replicator_replicator_online_generation/output/train_first
```

### 코드에서 볼 부분

실제 표본 생성은 설치본의 `standalone_examples/replicator/online_generation/generate_shapenet.py`에 있습니다. `IterableDataset`이 다음 표본을 만들 때 Replicator의 장면을 바꾸고 annotator를 읽습니다.

```python
gt = {
    "rgb": self.rgb.get_data(device="cuda"),
    "boundingBox2DTight": self.bbox_2d_tight.get_data(device="cpu"),
    "instanceSegmentation": self.instance_seg.get_data(device="cuda"),
}
```

RGB와 마스크는 CUDA 데이터에서 `warp.to_torch`로 연결합니다. RGB는 alpha를 제외하고 `[높이,너비,3]`에서 `[3,높이,너비]`로 축을 바꾸며 값 범위를 `0..255`에서 `0..1`로 맞춥니다. 상자의 semantic ID는 배경 0, 대상 클래스 1부터의 학습 번호로 바꿉니다. 자식 mesh의 instance mask를 같은 상위 물체로 묶는 작업도 필요합니다.

영상마다 보이는 물체 수가 다르므로 정답 상자·마스크 수가 다릅니다. DataLoader의 `collate_fn`은 이런 표본을 같은 크기의 고정 배열로 억지로 합치지 않고 목록으로 전달합니다. 생성기는 Kit 인스턴스에 연결되어 있으므로 임의로 여러 worker 프로세스를 추가하지 않습니다.

설치본 `train_shapenet.py`의 학습 순서는 다음과 같습니다.

```python
loss_dict = model(images, targets)
loss = sum(loss for loss in loss_dict.values())
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

모델은 영상과 정답으로 손실을 계산하고, 역전파로 기울기를 얻은 뒤 가중치를 갱신합니다. 로컬 실행기는 원본 종료 조건 `i > max_iters`를 고려해 `training_steps - 1`을 넘깁니다. 기본 10회이면 `ITER 0`부터 `ITER 9`까지 실제 갱신합니다.

### 실행 결과 확인하기

콘솔의 loss가 유한한 값인지 확인하고 `_out_train_imgs/`의 입력·예측 시각화를 살펴보세요. 설치본은 10회 간격으로 예측을 시각화하므로 기본 10회 학습에서 매번 PNG가 생기는 것은 아닙니다. 초기에는 confidence 기준을 넘는 예측이 없어 overlay가 비어 있을 수 있습니다.

이 예제에는 **학습 checkpoint 저장이 구현되어 있지 않습니다.** PNG와 loss 로그는 학습 연결을 관찰하는 결과이며 배포할 `.pth` 모델 파일이 아닙니다. torchvision의 backbone 초기화가 사전학습 가중치를 요청할 수 있으므로 네트워크 또는 해당 환경의 torch 캐시도 확인하세요.

## 3. 디스크 데이터셋과 온라인 생성의 차이 정리

```text
디스크 방식: 생성 → 전체 이미지·정답 저장 → 학습기가 다시 읽기
온라인 방식: 학습기의 다음 표본 요청 → 장면 생성·렌더링 → 텐서 → 손실·갱신
```

온라인 방식에서도 원본 USD 자산은 디스크에서 읽습니다. 저장하지 않는 것은 매번 만들어지는 학습 영상 전체입니다. 이 실습의 PNG는 중간 결과를 눈으로 점검하기 위한 일부 관찰 자료입니다.

## 4. 간단한 확인 실험

`experiment.json`을 복사하고 `max_asset_size_mb`만 **10 → 5**로 바꾼 뒤 `--config`로 전달하세요. 먼저 `audit`을 실행하고 기존 결과와 `size_eligible`을 비교합니다.

통과 파일 수는 같거나 줄어야 합니다. 그다음 새 출력에서 `sample`을 실행해 사용할 수 있는 모델과 생성 시간을 비교하세요. 파일 크기가 작다고 모든 모델의 렌더 시간이 일정 비율로 줄지는 않습니다. 클래스별 파일이 없어지면 그것도 크기 제한의 관찰 결과입니다.

## 실행할 때 막히면

- **변환 뒤에도 USD를 찾지 못함**: sample/train의 `--root`가 원본 OBJ 폴더가 아닌 `_nomat` 폴더인지 확인하세요.
- **특정 클래스의 사용 가능 파일이 0개**: synset 경로, 변환 결과, 크기 제한을 대조하세요.
- **분할 뒤 사용할 모델이 없음**: 클래스마다 여러 모델을 준비하거나 파일 크기 제한을 완화하세요. audit 통과만으로 분할 후 수량이 보장되지는 않습니다.
- **CUDA 메모리 부족**: 다른 GPU 앱을 종료하고 자산 크기와 실제 학습 배치·모델 부하를 확인하세요. 반복 횟수만 줄여도 한 단계의 최대 메모리는 그대로일 수 있습니다.
- **모델 파일이 없음**: 원본은 checkpoint를 저장하지 않습니다. 관찰 이미지를 가중치 파일로 해석하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Online Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html)에 대응합니다. 설치된 converter·generator·trainer를 로컬 설정으로 실행하는 사용 중단 예제입니다.

문서에서는 로컬 wrapper와 설치본의 텐서 변환·학습 루프를 대조했습니다. ShapeNet 변환, RTX 표본 생성과 실제 학습은 이번 개정에서 실행하지 않았으며 `tutorial.json`은 `not_run`입니다.
