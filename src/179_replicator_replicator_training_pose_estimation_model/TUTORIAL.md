# 179. 합성 정답을 DOPE 학습·추론·평가로 연결하기

## 이번에 배우는 것

**영상과 9개 cuboid 점으로 한 물체를 학습하고, 별도 영상에서 예측 자세를 검토하는 과정을 연결합니다.**

학습 데이터가 있다고 곧바로 3차원 자세를 비교할 수 있는 것은 아닙니다. 클래스 이름, 카메라 행렬, 물체 치수와 좌표 규약이 단계마다 맞아야 합니다. 이번에는 그 입력을 확인하면서 데이터 검사 → 학습 → 추론 → 평가 순서로 진행합니다.

| 단계 | 필요한 입력 | 로컬 실행기의 결과 |
|---|---|---|
| `audit` | 같은 이름의 RGB·JSON과 대상 클래스 | 프레임·대상 수와 9×2 점 형식 검사 |
| `train` | 검사된 데이터와 별도 DOPE 환경 | `weights/`의 checkpoint |
| `infer` | checkpoint·클래스 치수·카메라 설정 | `predictions/`의 예측 |
| `evaluate` | 규약이 맞는 정답·예측·외부 3D 모델 | `metrics/result.csv` |

공식 튜토리얼은 사용 중단된 실습이며 데이터 생성은 **Isaac Sim 5.1**, 학습·추론·평가는 별도 DOPE 코드입니다. `run.py`는 한 번에 한 단계를 실행하며 Isaac Sim GUI를 만들지 않습니다. 특히 제공 카메라 파일에는 추론기가 읽을 P 행렬을 추가해야 하고, 생성기의 3D 정답은 평가기의 cm·축 규약에 맞춘 별도 준비가 필요합니다. 준비 없이 네 명령을 연달아 실행해 유효한 정확도 수치를 얻는 구성은 아닙니다.

## 1. 데이터를 준비하고 짧은 학습 실행하기

Linux, NVIDIA GPU와 DOPE 의존성에 맞는 별도 Python 환경을 준비하세요. 이 문서가 대조한 DOPE revision은 `035f8e75d6ab20a33425c5364a8a3481a6c99bc6`입니다. [해당 revision의 학습 안내](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/train/README.md)에 맞춰 `/data/Deep_Object_Pose`와 `/data/dope-env/bin/python`을 준비했다고 가정합니다. 최신 Python에 예전 의존성 파일을 설치하는 것만으로 호환이 보장되지는 않습니다.

처음 준비한다면 쓰기 가능한 데이터 디렉터리에서 다음처럼 checkout과 분리된 환경을 만듭니다. `/data`는 자신의 작업 위치로 바꾸고, `python3`는 선택한 의존성 조합을 지원하는 Python으로 사용하세요.

```bash
git clone https://github.com/NVlabs/Deep_Object_Pose.git /data/Deep_Object_Pose
git -C /data/Deep_Object_Pose checkout 035f8e75d6ab20a33425c5364a8a3481a6c99bc6
python3 -m venv /data/dope-env
/data/dope-env/bin/python -m pip install -r /data/Deep_Object_Pose/requirements.txt
```

NVISII 평가에는 해당 환경의 렌더링 드라이버 라이브러리도 필요합니다. 의존성 설치와 GPU 실행 확인을 구분하고 Isaac Sim의 번들 Python에 이 학습 환경을 덮어 설치하지 않습니다.

데이터를 새로 만들려면 `Dockerfile.generation`을 사용할 수 있습니다. Docker, NVIDIA Container Toolkit, `nvcr.io` 이미지 접근과 자산 루트를 준비하고, Isaac Sim EULA에 동의한 환경에서 실행하세요. 이미지 안의 설정은 `/isaac-sim/standalone_examples/replicator/pose_generation/config/dope_config.yaml`입니다. 생성기는 Isaac Sim 자산 루트에 다음 설정값을 붙여 파일을 찾습니다.

| 설정 키 | 자산 루트 아래 경로 | 용도 |
|---|---|---|
| `TRAIN_ASSET_PATH` | `/Isaac/Props/YCB/Axis_Aligned/` | cracker box·power drill 학습 대상 USD |
| `DISTRACTOR_ASSET_PATH` | 같은 YCB 폴더 | 주변 방해 물체 USD |
| `DOME_TEXTURE_PATH` | `/NVIDIA/Assets/Skies/` | `DOME_TEXTURES` 목록의 HDR 배경 |

기본 원격 자산을 사용하면 컨테이너 안에서도 해당 경로에 접근할 수 있어야 합니다. 로컬 5.1 자산팩을 사용하려면 `Isaac/`과 `NVIDIA/`를 함께 포함하는 루트를 `/assets`에 마운트하고, 생성기에 `--/persistent/isaac/asset_root/default=/assets`를 전달합니다. 예를 들어 아래 `docker run`에서 이미지 이름 앞에 `-v /data/Assets/Isaac/5.1:/assets:ro`를, 이미지 이름 뒤의 생성 옵션에 그 설정을 추가하세요. 호스트에만 있는 절대 경로는 컨테이너에서 자동으로 보이지 않습니다.

아래 명령은 기본 자산 루트를 사용하는 예이며 저장소 루트 기준입니다.

```bash
docker build -f src/179_replicator_replicator_training_pose_estimation_model/Dockerfile.generation \
  -t isaac51-dope-generation:local src/179_replicator_replicator_training_pose_estimation_model
mkdir -p src/179_replicator_replicator_training_pose_estimation_model/output/generated_first
docker run --rm --gpus all -e ACCEPT_EULA=Y \
  -v "$PWD/src/179_replicator_replicator_training_pose_estimation_model/output/generated_first:/data" \
  isaac51-dope-generation:local \
  --writer dope --num_mesh 20 --num_dome 20 --output_folder /data --no-window
```

컨테이너는 `generation_config.yaml`을 위 DOPE 설정 위치에 복사합니다. 기본 MESH 방해 도형/물체가 400/150개이므로 짧은 40프레임도 초기 장면 부하가 작다고 가정하지 마세요. 자원에 맞게 `NUM_MESH_SHAPES`, `NUM_MESH_OBJECTS` 등을 줄이려면 설정을 바꾼 뒤 이미지를 다시 빌드해야 합니다.

컨테이너의 `/data`는 호스트의 `output/generated_first`와 연결되어 있습니다. 따라서 생성기의 `000000.png`·`000000.json` 같은 짝이 그 호스트 폴더에 생깁니다. 이 생성 실행을 학습용으로 사용하고, 별도 실행의 평가용 프레임은 다음처럼 새 폴더에 만드세요.

```bash
mkdir -p src/179_replicator_replicator_training_pose_estimation_model/output/generated_heldout
docker run --rm --gpus all -e ACCEPT_EULA=Y \
  -v "$PWD/src/179_replicator_replicator_training_pose_estimation_model/output/generated_heldout:/data" \
  isaac51-dope-generation:local \
  --writer dope --num_mesh 20 --num_dome 20 --output_folder /data --no-window
```

앞 실행에 로컬 자산 마운트·설정을 추가했다면 여기에도 같은 조건을 적용합니다. 두 폴더의 RGB·JSON을 확인한 뒤, 아래 대상 경로가 아직 없을 때 각각 사본을 만듭니다. 출력 전체에 실행 기록이나 debug overlay를 추가해 두었다면 학습 사본에는 원본 RGB·정답 JSON 쌍만 남기세요.

```bash
cp -a src/179_replicator_replicator_training_pose_estimation_model/output/generated_first /data/dope-train
cp -a src/179_replicator_replicator_training_pose_estimation_model/output/generated_heldout /data/dope-heldout
```

두 실행의 프레임 번호가 같아도 서로 다른 폴더에서 관리하므로 충돌하지 않습니다. 같은 생성 결과를 양쪽에 복사하면 새로운 데이터에 대한 성능을 평가할 수 없습니다. 이 평가용 원본은 추론에 사용하고, 3D 평가용 좌표 변환은 2절에서 다시 별도 사본에 적용합니다.

```bash
python3 src/179_replicator_replicator_training_pose_estimation_model/run.py audit \
  --data /data/dope-train --object 003_cracker_box
python3 src/179_replicator_replicator_training_pose_estimation_model/run.py train \
  --repo /data/Deep_Object_Pose --data /data/dope-train --object 003_cracker_box \
  --python /data/dope-env/bin/python --epochs 1 --batchsize 2 \
  --output src/179_replicator_replicator_training_pose_estimation_model/output/train_first
```

새 출력 경로를 사용하세요. 여기에는 GUI 수명을 정하는 `--steps`가 없습니다. 학습량은 `--epochs`로 전달합니다. 고정 revision의 신규 학습 루프는 epoch 0부터 지정값까지 포함하므로 **`--epochs 1`은 epoch 0과 1을 실행**합니다. [실제 학습 루프](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/train/train.py#L248)를 기준으로 로그를 읽으세요.

### 코드에서 볼 부분

`audit_dataset()`은 대상의 투영점을 다음 조건으로 검사합니다.

```python
points = obj.get("projected_cuboid", [])
if len(points) != 9 or any(len(point) != 2 for point in points):
    raise ValueError(...)
```

9는 여덟 꼭짓점과 중심점, 2는 화면의 x·y 좌표입니다. 같은 stem의 PNG/JPG/JPEG가 있는지와 좌표가 유한한 수도 확인합니다. 이 검사는 **이미지 디코딩, 점이 실제 윤곽과 맞는지, 위치 단위와 회전 축**까지 확인하지 않습니다.

학습 단계는 `torch.distributed.launch`로 공식 `train.py`를 실행합니다. 로컬 도구는 `--workers 0`, `--manualseed 42`를 전달하며 실제 명령은 `command.json`에 기록합니다. 학습이 끝난 뒤 `.pth`가 없으면 오류로 처리합니다.

### 실행 결과 확인하기

`audit`의 `frames`와 `matching_instances`를 읽고 실제 RGB·JSON 한 쌍을 열어 9개 점을 대조하세요. 이후 `output/train_first/input_audit.json`, `command.json`, `weights/`의 checkpoint와 학습 로그를 확인합니다.

손실 값과 모델 파일이 생기는 것은 학습 연결을 확인하는 첫 기준입니다. 짧은 학습에서 바로 좋은 자세 예측이 나와야 하는 것은 아닙니다.

## 2. 추론 설정과 평가의 좌표 규약 맞추기

### 설정에서 볼 부분

Cuboid는 물체를 둘러싼 3차원 직육면체입니다. DOPE는 영상에서 그 꼭짓점의 위치를 예측하고, 알려진 3D 치수와 카메라 행렬을 이용해 자세를 복원합니다. 이처럼 3D 점과 영상의 2D 점 대응으로 위치·회전을 구하는 방법이 PnP입니다. 따라서 클래스명만 맞추고 크기나 카메라를 임의로 넣으면 위치 추정도 달라집니다.

먼저 외부 저장소의 `config/config_pose.yaml`을 별도 `inference_config.yaml`로 복사합니다. `dimensions`, `class_ids`, `draw_colors`에 정확한 클래스 **`003_cracker_box`**를 추가하세요. `dimensions`는 cm 단위이며 원래 `cracker` 값의 축 순서·물체 형상이 실제 USD와 일치하는지 확인한 뒤 사용해야 합니다. 같은 512×512 픽셀 좌표로 overlay를 비교하려면 복사본의 `downscale_height`도 512로 맞추세요. 원본 기본값 400은 영상을 높이 400으로 줄이며 카메라 행렬도 같은 비율로 바꿉니다.

제공한 `camera_info.yaml`의 내부 행렬은 512×512 영상의 `fx=fy=768`, `cx=cy=256`입니다. 하지만 고정 revision의 추론기는 `input_is_rectified: true`일 때 **`projection_matrix.data`라는 3×4 행렬**을 읽습니다. 제공 파일에는 이 항목이 없으므로 다음 준비가 필요합니다.

1. `camera_info.yaml`을 별도 `camera_inference.yaml`로 복사합니다.
2. 영상이 왜곡 없는 기본 512×512 생성 조건인지 확인합니다.
3. 복사본의 최상위에 아래 항목을 추가하고 추론에는 그 파일을 전달합니다.

```yaml
projection_matrix:
  rows: 3
  cols: 4
  data: [768, 0, 256, 0, 0, 768, 256, 0, 0, 0, 1, 0]
```

이 값은 제공 K 행렬에 0 열을 붙인 것입니다. 해상도나 초점 거리를 바꿨다면 실제 카메라에 맞춰 K와 P를 함께 바꾸세요. `input_is_rectified`를 false로 바꾸는 것으로 누락을 우회하지 않습니다. 고정 추론기의 그 경로는 다른 카메라 객체 인터페이스를 기대합니다. [추론기의 카메라 처리](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/inference/inference.py#L76)를 참고하세요.

준비한 두 파일을 `/data/`에 두었다면 다음처럼 실행합니다.

```bash
python3 src/179_replicator_replicator_training_pose_estimation_model/run.py infer \
  --repo /data/Deep_Object_Pose --data /data/dope-heldout --object 003_cracker_box \
  --python /data/dope-env/bin/python \
  --weights src/179_replicator_replicator_training_pose_estimation_model/output/train_first/weights \
  --inference-config /data/inference_config.yaml --camera /data/camera_inference.yaml \
  --output src/179_replicator_replicator_training_pose_estimation_model/output/inference_first
```

`--weights`는 checkpoint들이 있는 폴더로 전달하세요. 원본은 여러 가중치를 순회할 수 있으므로 결과에서도 어느 checkpoint의 예측인지 확인합니다. 이 wrapper는 원본 추론기의 기본 확장자 `png`를 바꾸지 않습니다. audit가 JPG/JPEG를 허용하더라도 위 추론 명령에는 PNG 데이터를 준비하세요. 추론 wrapper는 실행 후 예측의 개수·정확성을 자동 판정하지 않으므로 JSON과 overlay를 직접 열어야 합니다.

### 평가 전에 확인할 입력

고정 평가기는 `--cuboid`를 받아도 외부 3D 모델을 읽어 cuboid를 만듭니다. 기본 경로는 DOPE checkout의 `3d_models/YCB_models/`이며, 클래스와 같은 이름의 하위 폴더에 `textured_simple.obj`, `texture_map.png`가 필요합니다. 모델 로더는 OBJ에 **scale 0.01을 고정 적용**하므로 원본 모델 좌표도 cm 기준인지 확인하세요. 이미 m로 된 모델에 이 배율을 다시 적용하면 100배 작아집니다. 로컬 wrapper에는 `--models` 전달 옵션이 없습니다.

평가기는 다음 규칙을 실제로 적용합니다.

| 항목 | 고정 평가기의 계산 |
|---|---|
| 정답·예측 `location` | 각각 100으로 나누어 cm에서 m로 변환합니다. |
| 정답 quaternion | JSON의 xyzw를 NVISII의 wxyz 인수 순서로 전달합니다. |
| 예측 quaternion | 같은 순서 변경 후 `q_pred × q_x(1.57) × q_z(1.57)`을 적용합니다. |
| 모델 형상 | OBJ를 0.01배 하고 그 형상에서 9개 cuboid 점을 만듭니다. |

`q_x`, `q_z`는 각 축 주위 회전이고 1.57의 단위는 rad입니다. **예측에만 후곱하는 두 회전**은 해당 모델 좌표계를 맞추기 위한 고정 규칙이지 모든 데이터의 보편적인 카메라 변환은 아닙니다. 곱 순서를 바꾸거나 정답에도 같은 보정을 중복 적용하면 다른 자세가 됩니다.

5.1 PoseWriter의 DOPE 출력은 cm로 환산하지 않은 장면 변환값을 기록합니다. 또 설치본의 3D pose 계산과 cuboid 투영에는 서로 다른 행렬 곱 순서가 사용됩니다. 따라서 overlay가 맞는다는 사실만으로 `location`과 quaternion을 평가기에 바로 전달해서는 안 됩니다.

평가 규약에 맞춘 **별도 정답 사본**을 `/data/dope-heldout-eval`에 준비할 때는 다음 순서로 확인하세요.

1. 위치·회전과 크기를 알고 있는 물체 한 자세를 기준으로 정합니다. Stage 단위, 카메라 세계 변환, 물체 원점과 cuboid 중심의 차이를 기록합니다.
2. 그 물체의 실제 카메라 기준 위치·회전을 구하고 기록된 값과 대조합니다. 이미 올바른 위치가 m로 확인된 경우에만 cm 사본에서는 100을 곱합니다. 예를 들어 실제 전방 거리 1 m라면 평가기 입력의 대응 축 값은 100 cm이고 평가기 내부에서는 다시 1 m여야 합니다. 부호는 사용한 카메라 축에 따라 확인합니다.
3. 위 예측 전용 회전까지 적용한 모델과 정답 모델이 같은 방향·크기·중심에 놓이는지 확인합니다. 카메라 축을 바꾸는 회전과 물체의 모델 축을 바꾸는 회전은 구분합니다. 이 조건을 맞추지 못했다면 3D 평가는 아직 준비되지 않은 상태입니다.
4. 한 물체만 평가할 경우 사본의 `objects`에서 `003_cracker_box` 이외의 레코드를 제외합니다. wrapper의 `--object`는 입력 감사에만 사용되고 **evaluate.py에 전달되지 않습니다.** 그대로 두면 power drill 등 다른 정답도 평가 대상에 포함됩니다.
5. RGB와 9개 투영점, 상대 파일 경로를 유지합니다. 추론 결과는 `predictions/체크포인트이름/원래상대경로.json` 구조여야 하며 평가기에는 상위 `predictions` 폴더를 전달합니다. 데이터 폴더에는 실행 기록용 JSON을 섞지 않습니다.

이 저장소는 위 단위·축 정합을 자동 수행하지 않습니다. 원본을 보존하고 사본에 적용한 변환과 기준 자세 결과를 기록하세요. [평가기](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/evaluate/evaluate.py)와 [모델 로더](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/evaluate/utils_eval.py#L112)가 이 입력 규약의 근거입니다.

위 준비와 NVISII 환경을 확인한 뒤 평가합니다.

```bash
python3 src/179_replicator_replicator_training_pose_estimation_model/run.py evaluate \
  --repo /data/Deep_Object_Pose --data /data/dope-heldout-eval --object 003_cracker_box \
  --python /data/dope-env/bin/python \
  --predictions src/179_replicator_replicator_training_pose_estimation_model/output/inference_first/predictions \
  --output src/179_replicator_replicator_training_pose_estimation_model/output/evaluation_first
```

`metrics/result.csv`의 설정 행과 `Weights`, `Object`, `Total AUC`, 거리 임계값별 열을 읽습니다. 이 wrapper의 평가는 cuboid 기반 ADD이며 mesh 전체 표면을 비교하는 평가와 다릅니다. 헤더만 있는 CSV를 유효한 성능 결과로 세지 말고 실제 대상·예측 행과 평가된 프레임 수를 확인하세요.

여기서 **ADD는 정답 자세와 예측 자세에 놓인 cuboid의 대응 9점 사이 거리 평균**이며, 단위는 m이고 작을수록 잘 맞습니다. 기본 임계값 열 `0.02`~`0.10`은 각각 2~10 cm 이하 오차로 대응된 예측 수를 해당 클래스의 정답 객체 수로 나눈 값이고, `Total AUC`는 0~0.1 m 구간에서 이 비율 곡선을 적분한 뒤 0.1로 나눈 면적이므로 같은 평가 조건에서는 클수록 좋습니다. 다만 이 고정 평가기는 이미 대응된 정답을 후보에서 제거하지 않으므로 중복 예측이 비율을 부풀릴 수 있습니다. 값이 1을 넘거나 한 물체에 여러 예측이 겹치면 좋은 성능으로 해석하지 말고 중복 대응부터 확인하세요. [실제 지표 계산](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/evaluate/utils_eval.py#L211)을 기준으로 읽습니다.

## 3. 2D 학습과 3D 평가의 연결 정리

```text
RGB + 9개 투영점 → belief/affinity map 학습 → checkpoint
checkpoint + 별도 영상 → 2D 점 예측
2D 점 + 카메라 행렬 + 물체 치수 → PnP 자세
정답과 예측의 단위·축·모델 일치 → 의미 있는 3D 오차 평가
```

Belief map은 각 꼭짓점이 있을 법한 영상 위치를, affinity map은 꼭짓점과 물체 중심의 연결 방향을 나타냅니다. 학습은 이 중간 표현의 오차를 줄이고, PnP가 예측한 점들을 3D 자세로 연결합니다.

학습 입력 형식 검사가 통과하는 것과 3D 평가 규약이 맞는 것은 다른 조건입니다. 중간 overlay가 유용한 이유도 여기에 있습니다. 수치 평가 전에 물체 위로 예측 cuboid가 제대로 투영되는지 확인할 수 있습니다.

### 선택 실습: NGC에서 생성과 학습을 나누기

공식 NGC workflow는 **OVX 생성 → S3 저장 → DGX 학습·평가**로 작업 장소를 나눕니다. OVX의 RTX 렌더링으로 만든 데이터를 S3에 두면 학습 장비가 같은 bucket에서 읽을 수 있습니다. 로컬 생성과 학습 연결을 확인한 뒤, NGC 조직·팀의 registry 및 해당 클러스터 접근 권한, S3 endpoint와 bucket을 별도로 준비하세요. 5.1 문서에 소개된 서비스가 현재 계정에서도 제공되는지는 확인해야 합니다.

1. 앞서 만든 생성 이미지를 본인 registry 이름으로 태그하고 push합니다. 아래 `YOUR_ORG`, `YOUR_TEAM`은 자신의 값으로 바꾸세요. 로그인에는 계정에서 안내하는 인증 방식을 사용합니다.

   ```bash
   docker tag isaac51-dope-generation:local nvcr.io/YOUR_ORG/YOUR_TEAM/dope-generation:isaac51
   docker login nvcr.io
   docker push nvcr.io/YOUR_ORG/YOUR_TEAM/dope-generation:isaac51
   ```

2. OVX 생성 job에 해당 이미지와 GPU 자원을 선택하고, 공식 절차의 **Preemption Options → Resumable**을 설정합니다. 이 이미지에는 생성기가 entrypoint로 들어 있으므로 job 인수에는 다음 옵션을 전달합니다. endpoint와 bucket은 본인 값으로 바꾸세요.

   ```text
   --writer dope --num_mesh 1000 --num_dome 1000 --use_s3 --endpoint https://YOUR_ENDPOINT --bucket YOUR_TRAIN_BUCKET --no-window
   ```

   S3 자격증명은 런타임 credential 파일이나 플랫폼이 지원하는 전달 수단으로 제공합니다. 이미지 빌드 파일에 비밀 값을 넣지 않습니다. 생성 로그가 끝난 뒤 bucket의 RGB·JSON 짝을 확인하고, 평가 영상은 별도 생성 실행으로 준비합니다.

3. DGX에는 앞서 고정한 DOPE 소스와 호환 의존성이 들어 있는 학습 이미지를 준비합니다. 공식 안내의 `train/docker/get_nvidia_libs.sh`는 NVISII 평가용 호스트 드라이버 파일을 `drivers/`에 복사하는 절차입니다. 실행 전 그 디렉터리와 복사 대상 라이브러리의 존재를 확인하세요. **고정 revision의 `train/docker/Dockerfile`은 다른 `andrewyguo/dope_training` 저장소를 clone합니다.** 그대로 빌드한 이미지를 이 문서의 고정 DOPE 환경으로 간주하면 안 됩니다. 빌드 사본이 실제로 포함하는 소스 revision·작업 디렉터리·NVISII 환경을 맞춘 뒤 본인 registry에 올립니다. [해당 Dockerfile](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/train/docker/Dockerfile)을 먼저 확인하세요.

4. 준비한 학습 이미지의 DOPE `train/`을 작업 디렉터리로 선택하고 다음 명령을 실행합니다. 출력 checkpoint가 job 종료 후에도 남도록 `/results/weights`를 영속 저장소에 연결하세요. 학습 job에도 S3 읽기 자격증명이 필요합니다.

   ```bash
   python -m torch.distributed.launch --nproc_per_node=1 train.py \
     --use_s3 --train_buckets YOUR_TRAIN_BUCKET --endpoint https://YOUR_ENDPOINT \
     --object 003_cracker_box --batchsize 2 --epochs 1 --outf /results/weights
   ```

5. checkpoint와 독립된 평가 데이터를 내려받아 2절의 카메라 준비·추론·좌표 정합·평가를 적용합니다. 원격 장비에서 실행하더라도 동일한 파일 경로 대응과 cm·축 규칙이 필요합니다. 결과 업로드는 평가가 끝난 뒤 실제 checkpoint, 예측과 CSV를 대상으로 별도 수행합니다.

공식 문서의 통합 예시 `train/run_pipeline_on_ngc.py`는 이 문서에서 고정한 revision에는 없습니다. 따라서 여기서는 위 개별 단계를 사용하며, 없는 통합 파일의 명령을 실행하지 않습니다. [공식 NGC 단계](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html#generating-data-on-ngc)와 실제 checkout의 차이를 확인하는 것도 이 선택 실습의 준비 과정입니다. 로컬 `run.py`는 클라우드 job 제출이나 업로드를 수행하지 않습니다.

## 4. 간단한 확인 실험

같은 학습 데이터에서 `--batchsize`만 **2 → 4**로 바꾸고 새 출력 경로에 학습합니다. seed 42와 epoch 설정은 유지됩니다.

한 번에 처리하는 영상 수가 늘어 GPU 메모리 사용량이 커질 수 있습니다. 한 epoch의 optimizer 갱신 횟수도 달라지므로 loss 한 줄만 나란히 비교하지 말고 처리한 표본 수·epoch와 함께 보세요. 메모리 부족이면 batchsize를 줄입니다.

## 실행할 때 막히면

- **대상 클래스가 없다는 audit 오류**: JSON의 실제 `class`와 `--object`를 대조하세요. `cracker`와 `003_cracker_box`는 다릅니다.
- **`projection_matrix` 키 오류**: 제공 카메라 파일의 복사본에 위 3×4 P를 추가했는지 확인하세요.
- **치수·class ID 키 오류**: 추론 설정의 사전 키가 학습 클래스명과 같은지 확인하세요.
- **평가 중 모델 이름 오류**: `--cuboid`에도 OBJ·텍스처가 필요합니다. 기본 모델 폴더와 클래스 이름을 맞추세요.
- **평가 오차가 비정상적으로 큼**: 단위, 고정 축 보정과 사용한 모델의 좌표를 먼저 대조하세요. loss 감소만으로 이 불일치를 해결할 수 없습니다.
- **CSV에 결과 행이 없음**: 예측 폴더에 모든 정답 상대 경로가 있는지와 실제 처리된 프레임 수를 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Training Pose Estimation Model with Synthetic Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html)에 대응합니다. 공식 생성 컨테이너와 고정 DOPE revision의 개별 실행을 연결하며, 제공 설정의 저작권 헤더와 라이선스를 보존합니다.

이번 개정에서는 wrapper·Dockerfile·YAML과 고정 DOPE의 학습·추론·평가 소스를 대조했습니다. 실제 학습, NVISII 평가, 컨테이너 생성과 NGC 실행은 수행하지 않았습니다. `tutorial.json`은 `not_run`이며, 특히 평가용 단위·축 정합은 사용 데이터에서 별도 확인할 범위입니다.
