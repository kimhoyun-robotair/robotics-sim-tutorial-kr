# 로봇 개발자를 위한 USD 입문

**Stage·Prim·Layer의 관계를 이해하고, Python으로 USD를 작성한 뒤 Isaac Sim 5.1에서 실행해 보는 짧은 튜토리얼**입니다. NVIDIA 공식 설명을 한국어로 요약하고, 핵심 동작을 관찰할 수 있는 작은 예제를 새로 작성했습니다.

기준은 [Isaac Sim 5.1.0 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)와 [NVIDIA OpenUSD 개발자 자료](https://developer.nvidia.com/openusd)입니다. NVIDIA의 OpenUSD 학습 사이트는 `latest` 문서이므로 공통 개념을 참고하고, Isaac Sim 연동 코드는 5.1 API에 맞춥니다. 확인일: **2026-09-15**.

## 읽는 순서

| 순서 | 문서 | 읽고 나면 알 수 있는 것 |
|---|---|---|
| 1 | [CONCEPTS.md](CONCEPTS.md) | Stage/Prim/Layer, 속성·스키마, 좌표·시간, 합성·저장 |
| 2 | [LIBRARIES.md](LIBRARIES.md) | `pxr` 모듈의 역할과 일반 Python/Isaac Sim 실행 환경 |
| 3 | 아래의 예제 01–03 | USD 생성·조회, 자산 재사용, 비파괴 수정, 선택과 지연 로딩 |
| 4 | [ISAAC_SIM.md](ISAAC_SIM.md)와 예제 04 | USD와 URDF의 차이, 물리 설정과 시뮬레이션 실행 |

ROS나 URDF 경험은 필수가 아닙니다. Python의 변수·함수·import를 읽을 수 있으면 시작할 수 있습니다. 각 `.py`의 한국어 주석은 API가 무엇을 쓰고 읽는지, 왜 그 순서로 호출하는지 설명합니다.

## 1. 실행 준비

저장소 루트에서 **일반 Python용 가상환경**을 준비합니다. 01–03은 화면을 띄우지 않고 USD 파일과 출력값을 만듭니다.

```bash
python3.12 -m venv .venvs/usd-tutorial
.venvs/usd-tutorial/bin/python -m pip install "usd-core==25.5.1"
.venvs/usd-tutorial/bin/python -c 'from pxr import Usd; print(Usd.GetVersion())'
```

환경별 차이와 `usdview` 설치는 [라이브러리 안내](LIBRARIES.md)를 참고하세요. 모든 예제는 이전 예제가 만든 파일 없이 독립적으로 실행됩니다. 기본 결과는 `outputs/usd/<예제 이름>/<실행 시각>/`에 저장됩니다. `--output`으로 직접 지정할 수도 있으며, **이미 존재하는 출력 디렉터리는 거부**합니다.

## 2. 예제 01: 장면을 만들고 다시 읽기

```bash
.venvs/usd-tutorial/bin/python usd/01_stage_prims.py
```

[01_stage_prims.py](01_stage_prims.py)는 `/World/Frame/Cube`를 만들고 크기·색·사용자 속성·관계·시간별 위치를 `stage.usda`에 기록합니다.

| 확인 대상 | 기대 결과 |
|---|---|
| defaultPrim / 큐브 크기 | `/World` / `0.5` m |
| Default 위치 | local `(0.25, 0, 0.25)`, world `(1.25, 0, 0.25)` |
| 시간 코드 12의 위치 | local `(0.5, 0, 0.25)`, world `(1.5, 0, 0.25)` |
| Relationship | `/World`의 `tutorial:focus`가 `/World/Frame/Cube`를 가리킴 |

부모의 이동이 월드 위치에 반영되는지 확인하세요. 시간 코드 12는 0과 24에 작성한 위치의 중간값입니다. **바꿔보기:** 부모 `Frame`의 x 이동을 `2.0`으로 바꾸고 local 좌표와 world 좌표 중 무엇이 달라지는지 확인합니다.

## 3. 예제 02: 원본을 유지하면서 한 배치만 수정하기

```bash
.venvs/usd-tutorial/bin/python usd/02_layers_references.py
```

[02_layers_references.py](02_layers_references.py)는 한 큐브 자산을 두 번 참조하고 오른쪽 큐브에만 크기 수정을 적용합니다.

| 출력 파일 | 기록된 내용 |
|---|---|
| `cube_asset.usda` | 재사용 자산. 원본 큐브 크기 `1.0` |
| `layout.usda` | `/World/Left`, `/World/Right`에서 자산 참조. 오른쪽 크기 `1.5` |
| `overrides.usda` | 오른쪽 `/World/Right/Geometry`의 크기를 `2.0`으로 수정 |
| **`scene.usda`** | `[overrides, layout]` 순서로 합성하는 편집용 진입점 |
| `flattened.usda` | 현재 합성 결과를 한 Layer로 내보낸 비교용 사본 |

`scene.usda`를 열었을 때 최종 크기는 **Left=1.0, Right=2.0**입니다. 원본 파일은 그대로이고 `layout.usda`만 열면 오른쪽은 여전히 `1.5`입니다. `.usda` 파일들을 텍스트로 열어 각 값이 어디에 있는지 비교하세요. 이 예제는 바닥이나 물리를 추가하지 않고 크기의 합성 결과를 비교합니다.

**바꿔보기:** `overrides.usda`의 크기를 `3.0`으로 바꾸면 어느 배치가 달라질까요? `scene.usda`의 sublayer 순서를 뒤집으면 왜 결과가 달라질까요? 답을 코드의 `Usd.EditContext`와 `subLayerPaths`에서 찾아보세요.

## 4. 예제 03: 선택지와 필요한 데이터만 로드하기

```bash
.venvs/usd-tutorial/bin/python usd/03_variants_payloads.py
```

[03_variants_payloads.py](03_variants_payloads.py)는 `variant_asset.usda`에 `bodySize`의 `small`/`large` 선택지를 만들고 `payload_scene.usda`에서 로드합니다.

- 선택별 크기: `small=0.5`, `large=1.0`.
- `LoadNone`으로 열면 `/World/Robot`은 있지만 payload의 자식 `Body`는 없습니다.
- `Load()` 후에는 `Body`와 기본 `small` 값이 보입니다.
- 장면에서 `large`를 선택해도 자산 파일의 기본 선택은 `small`로 유지됩니다.
- `Unload()` 후에는 `Body`가 다시 사라집니다. 파일을 삭제한 것은 아닙니다.

저장한 `payload_scene.usda`에는 `large` 선택이 남습니다. 일반 `Open()`은 기본적으로 payload를 로드하므로 다시 열면 크기 `1.0`의 Body가 나타납니다. **바꿔보기:** 세 번째 `medium` 선택지를 추가하고 같은 Prim 경로에서 크기가 바뀌는지 확인하세요.

## 5. 예제 04: USD에 쓴 물리 설정 실행하기

Isaac Sim 5.1과 지원 GPU가 필요합니다. [실행 과정·URDF 비교·결과 읽기](ISAAC_SIM.md)를 먼저 읽으세요.

```bash
~/isaacsim/python.sh usd/04_isaacsim_physics.py --headless --steps 240
```

[04_isaacsim_physics.py](04_isaacsim_physics.py)는 외부 자산 없이 큐브와 바닥을 만들고, 강체·충돌·질량을 적용해 실제 높이를 CSV로 기록합니다. GUI로 보려면 `--headless`를 빼고, 창을 계속 열어두려면 `--steps 240`도 생략합니다. 초기 설계는 `initial_scene.usda`, 측정 결과는 `heights.csv`입니다.

## 검증과 다음 학습

실제 실행 환경과 확인 결과는 [VERIFICATION.md](VERIFICATION.md)에 기록합니다. 여기서는 핵심 데이터 모델과 API를 익히고, 로봇 가져오기·관절 설정·센서 사용은 기존 [튜토리얼 색인](../src/INDEX.md)에서 이어가면 됩니다.

## 출처 및 더 읽기

문서 전체를 번역하지 않고 입문에 필요한 개념을 요약했습니다. 각 설명 문서 끝에도 해당 주제의 세부 출처를 넣었습니다.

- [Isaac Sim 5.1.0 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html): 로봇·물리·센서와 시뮬레이터 사용법.
- [NVIDIA OpenUSD 개발자 허브](https://developer.nvidia.com/openusd?size=n_6_n&sort-field=featured&sort-direction=desc): 사용자가 지정한 OpenUSD 자료의 출발점.
- [NVIDIA Learn OpenUSD](https://docs.nvidia.com/learn-openusd/latest/index.html): NVIDIA 공식 단계별 학습 과정. 합성, 자산 구조, 재질, instancing, 데이터 교환·검증을 더 공부할 때.
- [OpenUSD 공식 문서](https://openusd.org/release/index.html): NVIDIA 자료가 연결하는 원천 명세·용어집·API 참조.
