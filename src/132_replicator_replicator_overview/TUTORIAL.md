# 132. 사진에 보이는 물체는 모두 정답이 될까요?

## 이번에 배우는 것

**같은 크기의 상자 두 개를 촬영하고, 의미 라벨이 RGB와 학습용 정답을 어떻게 연결하는지 확인합니다.**

사진에는 상자가 보이는데 검출 정답에는 상자가 없을 수 있습니다. 렌더러가 물체를 그리는 데 필요한 정보와, 그 물체를 `carton`이라는 종류로 분류하는 정보가 서로 다르기 때문입니다. 이번에는 한 상자에만 라벨을 붙여 이 차이를 눈으로 확인합니다.

| 구성 | 이 실습에서 하는 일 |
|---|---|
| `/World/Labeled` | x=-1.5 m에 있는 상자이며 `class=carton`을 가집니다. |
| `/World/Unlabeled` | x=1.5 m에 있는 상자이며 의미 라벨이 없습니다. |
| 카메라와 render product | 같은 장면을 512×512 픽셀로 촬영합니다. |
| BasicWriter | RGB, 의미 분할, 2D 검출 상자를 파일로 저장합니다. |
| `workflow.yaml` | 별도 장면에서 라벨 있는 상자 하나의 회전을 바꾸는 대안입니다. |

두 상자의 한 변은 1 m이고 중심 높이는 0.5 m입니다. 이 장면은 물리 낙하를 실행하지 않으므로 같은 위치를 여러 번 촬영합니다.

## 1. 라벨이 다른 두 상자 촬영하기

Isaac Sim 5.1 전체 설치와 지원되는 NVIDIA RTX GPU가 필요합니다. 저장소 루트에서 다음 명령을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/132_replicator_replicator_overview/run.py --frames 3 --output /tmp/tutorial132-first
```

출력은 **아직 없는 폴더**를 지정합니다. 세 번 촬영하고 저장을 마치면 창은 관찰용으로 남습니다. 창을 닫으면 종료합니다. `--headless`를 추가하면 저장 후 바로 종료하고, GUI에서 `--steps 120`을 추가하면 저장 후 앱을 120번 갱신하고 종료합니다. `--steps`는 사진 개수가 아닙니다.

### 코드에서 볼 부분

`run.py`는 두 상자를 같은 반복문에서 만들지만 라벨을 붙이는 부분에만 조건을 둡니다.

```python
if name == "Labeled":
    add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
```

`class`는 라벨의 종류이고 `carton`은 그 값입니다. USD 장면의 한 요소를 **prim**이라고 부르며 `/World/Labeled`는 그 prim의 주소입니다. 화면의 왼쪽·오른쪽은 카메라 방향에 따라 달라지므로 주소로 두 상자를 구분하세요.

```python
writer.initialize(output_dir=str(output), rgb=True, semantic_segmentation=True,
                  colorize_semantic_segmentation=True, bounding_box_2d_tight=True)
writer.attach(rp)
```

카메라는 시점을, `rp`는 카메라와 해상도의 연결을 나타냅니다. **Annotator**가 렌더 결과에서 분할·검출 정보를 만들고 **Writer**가 그 결과를 저장합니다. `bounding_box_2d_tight`는 화면에서 보이는 대상의 경계를 둘러싼 2D 상자입니다.

### 실행 결과 확인하기

`/tmp/tutorial132-first`에서 다음 결과를 함께 보세요.

| 결과 | 읽을 때 확인할 내용 |
|---|---|
| RGB PNG | 두 상자가 모두 보이는지 확인합니다. |
| Semantic segmentation 이미지와 라벨 JSON | `carton`에 대응하는 영역이 라벨 있는 상자인지 확인합니다. 분할 색은 재질 색이 아닙니다. |
| Bounding box 배열과 라벨 정보 | `carton` 검출이 `/World/Labeled`에 대응하는지 확인합니다. 좌표는 이미지 픽셀 기준입니다. |
| `labels.usda` | 상자 배치와 라벨을 저장한 텍스트 USD입니다. 사진 자체를 담는 파일은 아닙니다. |

기본 장면에는 무작위화가 없으므로 세 RGB의 배치가 같아도 정상입니다. 의미 정답에 라벨 없는 상자가 빠졌다고 해서 RGB 렌더링이 실패한 것은 아닙니다.

## 2. GUI와 YAML에서 같은 연결 살펴보기

창이 남아 있는 동안 Stage에서 두 prim을 차례로 선택하세요. **Tools > Replicator > Semantics Schema Editor**에서 `/World/Labeled`의 `carton`을 확인하고, Viewport의 **Synthetic Data Visualizer**에서 의미 분할을 선택해 보세요. 시각화는 현재 장면을 관찰하는 기능이며 이미 저장된 파일을 다시 쓰지는 않습니다.

GUI로 새 데이터를 기록하려면 **Tools > Replicator > Synthetic Data Recorder**를 엽니다. 새 render product에 Stage에서 확인한 Camera prim 경로와 512×512 해상도를 넣고, RGB·Semantic Segmentation·Bounding Box 2D Tight를 선택합니다. 프레임 수는 3, 출력은 새 폴더로 지정한 뒤 Start하세요.

### 설정에서 볼 부분

`workflow.yaml`은 Python 장면을 다시 불러오는 파일이 아니라 **별도 장면을 구성하는 명세**입니다.

```yaml
carton:
  create.cube:
    semantics: [["class", "carton"]]
    scale: 1
trigger:
  trigger.on_frame:
    max_execs: 3
```

YAML 아래쪽의 `modify.pose`는 Z 회전을 0~90도에서 고릅니다. 먼저 새 장면을 열고 YAML의 `output_dir`를 아직 없는 절대경로로 바꾸세요. **Tools > Replicator > Replicator YAML**에서 파일을 불러와 실행하면, 상자 하나를 세 번 촬영하는 구성을 비교할 수 있습니다. 이 YAML은 RGB와 의미 분할만 요청하며 Python의 2D 상자 출력까지 동일하지는 않습니다.

## 3. 장면에서 정답 파일까지의 흐름 정리

```text
USD 물체 + class 라벨
    → 카메라와 해상도로 렌더
    → annotator가 RGB·분할·검출 계산
    → writer가 파일 저장
```

Python, Recorder, YAML은 이 연결을 설정하는 서로 다른 방법입니다. `set_capture_on_play(False)`는 Play와 자동 기록을 분리하고, `step(delta_time=0.0)`은 시간을 진행시키지 않은 상태를 촬영합니다. 마지막 `wait_until_complete()`가 파일 쓰기를 기다린 뒤 writer와 render product를 해제합니다. 그래서 창이 계속 열려 있어도 첫 데이터셋의 장수가 늘어나지 않습니다.

## 4. 간단한 확인 실험

`/World/Unlabeled`에도 **class 라벨 `carton` 하나만 추가**하세요. 카메라와 조명은 그대로 두고 Recorder로 새 폴더에 기록합니다.

- RGB에는 여전히 두 상자가 보입니다.
- 의미 분할에서는 두 상자가 같은 클래스에 속합니다.
- 검출 정답에는 두 물체에 대응하는 상자가 나타나야 합니다.

같은 클래스라고 해서 같은 물체 인스턴스가 되는 것은 아닙니다. 두 이미지의 색보다 **라벨 매핑과 검출 개수**를 비교하세요.

## 실행할 때 막히면

- **출력 경로가 이미 있다는 오류**: 새 `--output`을 지정하세요. 초기 실행에서 폴더가 생성된 뒤 실패했어도 그 경로는 다시 사용할 수 없습니다.
- **Replicator 메뉴가 없음**: Window > Extensions에서 `isaacsim.replicator.synthetic_recorder`, `omni.replicator.replicator_yaml`과 Semantics 관련 확장을 확인하세요.
- **라벨을 추가했는데 기존 파일이 그대로임**: 편집 후 새로 촬영해야 합니다. 장면 편집과 저장된 데이터 갱신은 별도 작업입니다.
- **상자는 보이는데 검출이 비어 있음**: 해당 prim의 class 라벨과 카메라 시야를 함께 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html)에 대응합니다. 공식 문서의 라벨 편집·시각화·Recorder·YAML 연결을 로컬 상자 장면으로 익히는 실습입니다.

두 상자 비교와 `labels.usda` 저장은 이 폴더의 구성입니다. [VERIFICATION.md](VERIFICATION.md)는 문법·도움말·설정 확인을 기록하며, `tutorial.json`의 실행 상태는 `not_run`입니다. 위 이미지와 정답 설명은 실제 환경에서 확인할 기준이며 GPU 캡처와 GUI 조작을 이번 문서 개정에서 실행하지는 않았습니다.
