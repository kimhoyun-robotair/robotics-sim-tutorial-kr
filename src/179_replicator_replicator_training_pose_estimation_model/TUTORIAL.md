# 179. 합성 데이터로 DOPE 학습·추론·평가하기

권장 학습 순서 **179** · 사용 중단 문서와 레거시 참고 · 출처 ID `t051`

공식 **Training Pose Estimation Model with Synthetic Data** 수업을 local DOPE 실행과 컨테이너 입력으로 구현했다. 공식 수업은 **DEPRECATED**이며, Isaac Sim 생성기는 **5.1.0**으로 고정한다. DOPE 학습 코드는 별도 공식 저장소의 프로그램이다. 이 패키지는 데이터를 검사하고 실제 공식 프로세스를 실행한다. 모의 loss나 가짜 모델 파일을 만들지 않는다. 다른 로컬 패키지를 읽지 않아도 준비할 수 있다.

`run.py`의 audit·train·infer·evaluate는 별도 DOPE 명령행 프로그램이며 Isaac Sim GUI를 만들지 않는다. 따라서 GUI 유지용 `--steps`는 이 실행기에 적용되지 않는다. 학습량은 `--epochs`로 정하며, 아래 데이터 생성 컨테이너 예시는 명시적으로 `--no-window`를 전달하는 유한한 배치 작업이다.

## 준비물과 데이터 만들기

Linux, NVIDIA GPU, Isaac Sim 5.1, DOPE 공식 저장소와 그 `requirements.txt`에 맞는 **별도 Python 환경**이 필요하다. 추론에는 학습된 checkpoint와 물체 크기/카메라 설정, 평가에는 실제 ground truth가 필요하다. NVISII를 사용하는 평가는 렌더링 드라이버도 필요하다. Isaac Sim의 번들 Python에 학습 의존성을 덮어 설치하지 않는다.

```bash
cd src/179_replicator_replicator_training_pose_estimation_model
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
# 학습 코드 확보 후 기록된 revision으로 고정한다.
git clone https://github.com/NVlabs/Deep_Object_Pose.git /data/Deep_Object_Pose
git -C /data/Deep_Object_Pose checkout 035f8e75d6ab20a33425c5364a8a3481a6c99bc6
python3 -m venv /data/dope-env
/data/dope-env/bin/python -m pip install -r /data/Deep_Object_Pose/requirements.txt
```

GPU/CUDA와 위 의존성의 호환은 실제 환경에서 확인해야 한다. 이 패키지가 자동 설치하지 않는다. DOPE README에 기재된 제약을 함께 확인한다. 데이터는 다음 생성 컨테이너로 만들 수 있다. NVIDIA Container Toolkit 및 `nvcr.io` 이미지 접근을 준비하고, Isaac Sim EULA에 동의한 경우에만 `ACCEPT_EULA=Y`를 사용한다.

```bash
docker build -f Dockerfile.generation -t isaac51-dope-generation:local .
mkdir -p output/generated
docker run --rm --gpus all -e ACCEPT_EULA=Y \
  -v "$PWD/output/generated:/data" isaac51-dope-generation:local \
  --writer dope --num_mesh 20 --num_dome 20 --output_folder /data --no-window
```

`generation_config.yaml`은 컨테이너 내부 공식 설정을 교체한다. `/Isaac/Props/YCB/Axis_Aligned/`의 YCB 물체와 `/NVIDIA/Assets/Skies/`의 HDR에 접근할 수 있는 assets root가 필요하다. 원본 MESH distractor 수가 크므로 첫 시험에서는 `NUM_MESH_SHAPES`, `NUM_MESH_OBJECTS`를 각각 12, 8로 줄여도 된다. 물체 asset 자체는 포함하지 않는다.

## 단계별 로컬 학습

1. 생성된 `.png`와 같은 stem의 `.json`을 연다. 기본 클래스는 `003_cracker_box`, `035_power_drill`이다. DOPE는 한 물체를 대상으로 학습하므로 아래에서는 cracker box 하나를 선택한다. 이미지와 함께 `objects[].class`와 9개의 `projected_cuboid` 점을 확인한다.
2. 학습용 이미지와 별도 실행에서 만든 평가용 이미지를 각각 `/data/dope-train`, `/data/dope-heldout`에 준비한다. 같은 프레임을 양쪽에 복사하면 일반화 평가가 아니다. 아래 audit는 파일 짝과 좌표 형식을 검사하며 시각적 정확도나 데이터 분할 독립성까지 증명하지 않는다.
3. 다음 명령으로 audit 후 짧은 학습을 실행한다. 원본 train.py의 epoch 반복은 0부터 지정값까지이므로 `--epochs 1`이면 epoch 0과 1이 실행된다.

```bash
python3 run.py audit --data /data/dope-train --object 003_cracker_box
python3 run.py train --repo /data/Deep_Object_Pose --data /data/dope-train \
  --object 003_cracker_box --python /data/dope-env/bin/python \
  --epochs 1 --batchsize 2 --output output/train
```

4. `output/train/weights/`의 `.pth`, `header.txt`, TensorBoard 기록을 확인한다. epoch별 loss와 checkpoint가 생기는 것이 첫 성공 기준이다. 짧은 실험의 예측 정확도는 기대하지 않는다.
5. `/data/Deep_Object_Pose/config/config_pose.yaml`을 이 패키지의 `inference_config.yaml`로 복사한다. `dimensions`, `class_ids`, `draw_colors` 등 물체별 키에 **정확한 데이터 클래스 이름 `003_cracker_box`**를 추가한다. 원본 `cracker` 항목의 실제 USD 물체와 축 순서가 일치하는지 확인한 다음 해당 값을 사용한다. dimensions 단위는 **cm**이며, 같은 이름이라도 다른 USD이면 크기를 다시 측정한다. 물체 치수는 PnP 자세 복원의 입력이므로 임의 값을 넣지 않는다.
6. 제공한 `camera_info.yaml`은 생성 설정의 512×512, fx=fy=768, cx=cy=256에 맞춘다. 실제 데이터의 intrinsics를 바꿨다면 이 파일도 함께 바꾼다. 학습 checkpoint와 별도 heldout 데이터를 사용해 실행한다.

```bash
python3 run.py infer --repo /data/Deep_Object_Pose --data /data/dope-heldout \
  --object 003_cracker_box --python /data/dope-env/bin/python \
  --weights output/train/weights --inference-config inference_config.yaml \
  --camera camera_info.yaml --output output/inference
python3 run.py evaluate --repo /data/Deep_Object_Pose --data /data/dope-heldout \
  --object 003_cracker_box --python /data/dope-env/bin/python \
  --predictions output/inference/predictions --output output/evaluation
```

추론 그림에 투영된 cuboid와 실제 물체가 맞는지 확인한 후 `output/evaluation/metrics/result.csv`를 읽는다. `--cuboid`는 물체 mesh 전체 대신 cuboid를 이용한 ADD 평가다. 평행 이동 단위와 quaternion 순서를 writer 및 평가 코드 양쪽에서 확인한다. 코드가 정상 종료했다는 사실과 pose 정확도는 별개다.

## 코드와 API 해설

`audit_dataset`은 JSON을 읽어 RGB 짝, 학습 클래스의 존재, cuboid 9×2 모양과 유한 좌표를 검사한다. `subprocess.run(..., check=True)`는 해당 DOPE 환경에서 실제 학습·추론·평가를 실행하고 실패를 그대로 전달한다. 결과 경로는 새 폴더만 허용한다.

DOPE는 영상에서 물체 cuboid 꼭짓점의 **belief map**과 중심으로 향하는 **affinity map**을 예측한다. PyTorch의 역전파가 두 오차를 줄인다. 알려진 카메라 행렬과 3D cuboid 크기를 이용하는 PnP 단계가 2D 점을 물체의 위치·회전으로 바꾼다. 그래서 semantic 클래스 이름만 맞고 크기·카메라 좌표가 틀려도 pose는 틀릴 수 있다. `--parallel`은 DDP로 학습한 checkpoint의 이름 형식을 추론기가 해석하도록 전달한다.

## NGC/OVX/DGX와 S3 실습

공식 문서의 구조는 **OVX에서 RTX 데이터 생성 → S3 → DGX에서 학습·평가**다. NGC 조직/팀 및 해당 클러스터 접근 권한, Docker registry 로그인, 본인 S3 bucket/endpoint가 있어야 한다. 5.1 문서의 서비스 가용성을 현재 계정에서도 보장하지 않는다.

1. 위 Dockerfile로 이미지를 만들고 `nvcr.io/조직/팀/이름:태그`로 태그한다. NGC registry에서 안내하는 방식으로 로그인한 뒤 본인 registry로 push한다.
2. OVX 생성 job에는 해당 이미지, GPU 자원, 공식 수업의 **Preemption Options → Resumable**을 지정한다. 런타임에 credential 파일을 마운트하거나 플랫폼이 제공하는 자격증명 전달 수단을 사용한다. 비밀 값을 Dockerfile 또는 명령 기록에 넣지 않는다.
3. 생성 인수로 `--writer dope --num_mesh 1000 --num_dome 1000 --use_s3 --endpoint https://YOUR_ENDPOINT --bucket YOUR_BUCKET --no-window`를 사용한다. local 생성이 검증된 뒤 수행한다.
4. 학습 컨테이너는 DOPE `train/docker/Dockerfile`과 `get_nvidia_libs.sh`를 사용한다. 후자는 NVISII 평가에 필요한 드라이버 라이브러리를 포함시키는 원본 절차다. DGX job에서는 저장소 `train/`을 작업 폴더로 하고 `python -m torch.distributed.launch --nproc_per_node=1 train.py --use_s3 --train_buckets YOUR_BUCKET --endpoint https://YOUR_ENDPOINT --object 003_cracker_box --batchsize 2 --epochs 1`을 실행한다.
5. 원본 통합 실행 파일 `train/run_pipeline_on_ngc.py`의 `--help`를 먼저 확인한다. 수업의 `--num_gpus`, `--endpoint`, `--object`, `--train_buckets`, `--inference_bucket`, `--output_bucket`을 본인 값으로 지정하면 생성 후 학습·추론·평가 결과를 연결할 수 있다. upstream revision에 해당 파일이 없으면 검증된 개별 local 명령을 사용하며 존재하지 않는 기능을 가정하지 않는다.

이 패키지에서는 클라우드 작업 제출·업로드를 실행하지 않았다. 초보자 비교 실험은 **batchsize만 2→4**로 바꾸고 같은 데이터/seed에서 GPU 사용량과 loss 기록을 비교하는 것으로 충분하다. OOM이면 batchsize를 줄인다. 클래스가 없다는 audit 오류는 JSON의 실제 `class` 값부터 확인한다. inference 설정 키 오류는 학습 클래스명과 설정 사전의 키가 일치하는지 본다.

검증 범위: 로컬 Python 문법·CLI·입력 검사. 실제 학습, NVISII 평가, Docker/NGC 실행은 미검증이다.

## 출처

- [Isaac Sim 5.1 Training Pose Estimation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html)
- [NGC 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html#generating-data-on-ngc), [전체 pipeline](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html#running-the-entire-pipeline-in-one-command)
- [공식 DOPE training README, 고정 revision](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/train/README.md), [train.py](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/train/train.py), [inference.py](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/inference/inference.py), [evaluate.py](https://github.com/NVlabs/Deep_Object_Pose/blob/035f8e75d6ab20a33425c5364a8a3481a6c99bc6/evaluate/evaluate.py)
- `generation_config.yaml`: Isaac Sim 5.1 배포본의 DOPE 설정. NVIDIA Apache-2.0 헤더와 동봉 라이선스를 유지했다.
