# 178. 영상 속 상자에서 물체의 6D 자세 정답까지 읽기

## 이번에 배우는 것

**가림과 조명이 바뀌는 장면을 만들고, RGB와 물체 위치·회전·투영된 cuboid 정답을 함께 확인합니다.**

물체가 영상의 어느 사각형 안에 있는지만 알아도 탐지를 할 수 있습니다. 로봇이 집을 방향까지 정하려면 물체의 3차원 위치와 회전이 필요합니다. 이 여섯 자유도를 묶어 6D pose라고 부릅니다. 물체를 둘러싼 3차원 직육면체인 cuboid를 영상에 겹쳐 그리면 그 자세를 눈으로 확인할 수 있습니다. 이번에는 추정 모델에 사용할 영상과 자세 정답을 생성합니다.

| writer 선택 | 대상과 설정 | 주로 확인할 출력 |
|---|---|---|
| `dope` | cracker box·power drill, 512×512 | RGB·JSON·debug cuboid |
| `centerpose` | 네 종류 mug, 1920×1440 | 범주 대상의 자세 정답 |
| `ycbvideo` | YCB 두 물체, 1280×720 | YCBVideo 규약의 이미지·MAT |

공식 실습은 사용 중단된 **Isaac Sim 5.1 예제**입니다. 로컬 `run.py`는 설치된 생성기를 새 출력 폴더에 복사하고 이 폴더의 YAML을 적용합니다. 모델 학습이나 추론은 수행하지 않습니다.

## 1. 먼저 DOPE 형식의 8프레임 만들기

Linux, RTX GPU와 Isaac Sim 5.1 전체 설치를 준비하세요. 설치 폴더의 `standalone_examples/replicator/pose_generation/`과 자산 루트의 YCB·HDR 배경이 필요합니다. CenterPose에는 `Isaac/Props/Mugs/` 자산도 필요합니다.

저장소 루트에서 실행합니다. 기본 설치는 `~/isaacsim`이며 다른 위치라면 `--isaac-sim`을 지정하세요.

```bash
python3 src/178_replicator_replicator_pose_estimation/run.py \
  --writer dope --num-mesh 4 --num-dome 4 --headless \
  --output src/178_replicator_replicator_pose_estimation/output/dope_first
```

MESH 배경 4프레임과 DOME 배경 4프레임을 요청합니다. 여기서 `--num-mesh`는 mesh 물체 개수가 아니라 **MESH 방식의 촬영 프레임 수**입니다. 물체 수는 YAML의 별도 항목입니다.

새 출력 경로를 사용하세요. `--headless`를 빼면 생성 중 GUI와 마지막 장면을 볼 수 있습니다. 창은 직접 닫을 때까지 남으며 `--steps 120`은 저장 후 120회 GUI 업데이트 뒤 닫는 옵션입니다. 창을 유지하는 동안 새 학습 프레임이 계속 생기지는 않습니다.

### 설정에서 볼 부분

`config/dope_config.yaml`의 관심 물체입니다.

```yaml
OBJECTS_TO_GENERATE:
- { part_name: 003_cracker_box, num: 1, prim_type: _03_cracker_box }
- { part_name: 035_power_drill, num: 1, prim_type: _35_power_drill }
```

`part_name`은 자산 파일 이름, `prim_type`은 그 USD 안에서 찾을 실제 prim 이름입니다. 숫자 표기까지 서로 다르므로 같은 문자열로 바꾸면 로딩이 깨질 수 있습니다. 사용자 자산으로 확장할 때는 먼저 USD를 열어 Stage 계층에서 이름을 확인하세요.

기본 카메라는 `WIDTH=HEIGHT=512`, `F_X=F_Y=768`이고 대상의 카메라 광축 방향 거리는 0.4~1.4 m 범위입니다. F_X/F_Y는 픽셀 단위 초점 거리이므로 거리와 함께 물체가 차지하는 화면 크기를 결정합니다.

### 실행 결과 확인하기

`output/dope_first/data/`에서 같은 번호의 RGB와 JSON을 열고 debug overlay와 비교하세요.

| DOPE JSON 항목 | 의미 | 관찰 지점 |
|---|---|---|
| `objects[].class` | 학습 대상 클래스 | RGB에 있는 대상과 연결합니다. |
| `location` | writer가 기록한 카메라 기준 위치 | 세계 위치와 혼동하지 않습니다. |
| `quaternion_xyzw` | 회전 quaternion, x·y·z·w 순서 | w가 첫 성분인 API에 그대로 넘기지 않습니다. |
| `projected_cuboid` | 8개 꼭짓점과 중심점의 화면 위치 | 총 9점이 물체의 상자와 맞는지 봅니다. |

정답에는 화면 안에서 보이는 대상만 포함될 수 있습니다. 설치된 DOPE·CenterPose 생성기는 `skip_empty_frames=False`를 사용하므로 `objects`가 빈 프레임도 RGB·JSON으로 저장합니다. **프레임 수, 정답 객체 수, debug PNG 수는 서로 다릅니다.** 기본 8프레임의 촬영 기록을 객체 8개와 같은 것으로 세지 마세요.

`command.json`에는 외부 생성기 인수가, `native/config/`에는 실제 적용된 YAML이 남습니다. 다음 실행에서 원본 설정을 바꿔도 이전 결과의 설정을 다시 확인할 수 있습니다.

## 2. 물리 배치와 writer의 좌표 규약 살펴보기

### 코드에서 볼 부분

실제 생성 코드는 출력의 `native/pose_generation.py`에 있습니다. `_setup_collision_box`, `_setup_distractors`, `_setup_train_objects`, `__next__` 순서로 읽어 보세요.

방해 물체는 중력이 0인 공간에서 힘을 받아 움직이고, 보이지 않는 collision box가 바깥으로 나가는 것을 제한합니다. 이렇게 하면 단순히 mesh를 겹쳐 놓는 배경보다 접촉을 반영한 가림 장면을 만들 수 있습니다. 관심 물체의 자세는 카메라 시야 안으로 별도 배치합니다. 바닥으로 모두 떨어지는 장면을 기대하지 않는 이유입니다.

MESH 단계는 도형·물체와 sphere light를 중심으로, DOME 단계는 HDR 배경을 중심으로 구성됩니다. DOPE 설정의 도형/물체 수는 MESH 12/8, DOME 6/4입니다. 이 수와 앞 절의 촬영 4/4를 구분하세요.

카메라 설정의 회전은 다음과 같습니다.

```yaml
CAMERA_RIG_ROTATION: [0, 0, 0]
CAMERA_ROTATION: [180, 0, 0]
```

일반 USD 카메라는 -Z 방향을 바라보고 +Y가 위입니다. 이 예제는 카메라를 rig에 대해 X축으로 180도 돌려 rig를 +Z 전방·+Y 아래의 좌표처럼 사용합니다. **rig 기준 물체 배치와 writer가 기록하는 camera 기준 pose를 구분**해야 합니다. YAML 설명만으로 JSON 위치의 부호나 다른 데이터셋의 pose 규약까지 같다고 가정하지 마세요.

3D 자세를 다른 평가기에 사용할 때는 설치본 PoseWriter의 변환도 확인해야 합니다. 이 설치본은 행 벡터 규약의 cuboid 점을 `점 @ local_to_world @ world_to_camera`로 투영하지만, `location`·quaternion을 만들 행렬은 `world_to_camera @ local_to_world` 순서로 계산합니다. 두 경로의 순서가 다르므로 **debug cuboid가 영상에 맞는 것만으로 3D 위치·회전도 맞다고 보증할 수 없습니다.** 알려진 물체 자세 하나에서 실제 카메라 변환과 기록을 대조한 뒤 사용하세요. 또한 DOPE 형식으로 출력할 때 cm 변환을 별도로 하지 않으므로 저장 위치의 단위는 생성 Stage와 대조해야 합니다.

### 다른 writer로 비교하기

```bash
python3 src/178_replicator_replicator_pose_estimation/run.py \
  --writer centerpose --num-mesh 4 --num-dome 4 --headless \
  --output src/178_replicator_replicator_pose_estimation/output/centerpose_first
python3 src/178_replicator_replicator_pose_estimation/run.py \
  --writer ycbvideo --num-mesh 4 --num-dome 0 --headless \
  --output src/178_replicator_replicator_pose_estimation/output/ycb_first
```

writer 선택은 출력 확장자만 바꾸지 않습니다. CenterPose는 여러 mug를 사용하고 카메라 해상도와 초점 거리도 바뀝니다. YCBVideo는 `CLASS_NAME_TO_INDEX`와 MAT 규약을 사용하므로 DOPE JSON 판독기를 그대로 쓰지 않습니다.

CenterPose의 MESH 도형/물체는 500/200, DOME은 100/100이며 YCBVideo의 MESH도 500/200입니다. 짧은 촬영 명령이어도 DOPE 기본 설정보다 장면 부하가 클 수 있습니다. 각 YAML을 먼저 읽고 GPU 용량에 맞는 소규모 조건을 준비하세요.

S3 출력은 이 wrapper에서 `dope`만 허용합니다. 본인의 endpoint·bucket과 boto3 자격증명 환경을 준비한 경우 `--use-s3 --endpoint ... --bucket ...`으로 실제 원격 저장을 실행할 수 있습니다. 로컬 파일을 확인하는 첫 실습과는 별도 단계입니다.

## 3. 6D 정답과 화면 좌표의 관계 정리

```text
물체의 3D 위치·회전 + 카메라
    → RGB 렌더링
    → 같은 물체의 cuboid를 화면에 투영
    → writer 규약의 위치·quaternion·9개 점 저장
```

이미지에 찍힌 9개 점은 자세 정답을 눈으로 점검할 수 있는 연결고리입니다. 상자가 물체와 어긋나면 학습을 시작하기 전에 카메라, scale, cuboid 기준과 대상 prim을 확인할 수 있습니다. 파일이 생성되었다는 사실만으로 6D 정답이 후속 모델의 단위·축 규약과 맞는 것은 아닙니다.

## 4. 간단한 확인 실험

`config/dope_config.yaml`의 `NUM_MESH_SHAPES`만 **12 → 24**로 바꾸고 새 출력 폴더에서 같은 DOPE 명령을 실행하세요. 다른 수량·광원·프레임 설정은 유지합니다.

MESH 단계에서 대상이 가려지는 정도와 `objects`의 수를 비교하세요. 촬영 요청은 여전히 8프레임이므로 물체 수를 두 배로 늘렸다고 데이터 프레임도 두 배가 되지는 않습니다. 이 실습은 seed를 CLI로 고정하지 않으므로 단일 영상 한 쌍보다 여러 프레임의 경향을 비교하는 편이 적절합니다.

## 실행할 때 막히면

- **대상 prim 로딩 실패**: `part_name`, `prim_type`, 자산 루트와 실제 USD 계층을 대조하세요.
- **HDR·YCB 자산을 찾지 못함**: JSON/YAML이 있다는 것과 자산이 있다는 것은 다릅니다. 참조 URL 또는 로컬 자산팩을 확인하세요.
- **CenterPose 실행에서 메모리 부족**: 해당 YAML의 해상도와 수백 개 방해 물체 수를 확인하세요. 프레임 수만 줄여도 초기 장면 메모리는 줄지 않을 수 있습니다.
- **빈 `objects`가 저장됨**: 대상 가시성과 writer의 빈 프레임 저장 설정을 함께 확인하세요.
- **회전이 뒤집혀 해석됨**: `xyzw` 순서와 rig·camera·world 기준을 차례로 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Pose Estimation Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_pose_estimation.html)에 대응합니다. 공식 생성기의 복사본과 로컬 YAML을 사용하며 NVIDIA 저작권 헤더와 동봉 라이선스를 유지합니다.

문서에서는 wrapper, YAML과 설치된 PoseWriter의 JSON 필드·빈 프레임 설정을 대조했습니다. RTX 생성, writer별 출력과 S3 저장은 이번 개정에서 실행하지 않았으며 `tutorial.json`은 `not_run`입니다. 공식 예제의 사용 중단 상태도 함께 확인하세요.
