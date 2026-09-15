# 169. 식당 배경이 바뀌어도 같은 물체를 알아보게 하려면?

## 이번에 배우는 것

**Infinigen 식당에서 물체를 배치하고, 공중에 있는 상태와 떨어진 상태를 두 카메라로 촬영합니다.**

물체의 생김새만 다양한 데이터로는 새로운 방이나 가려진 상황을 충분히 설명하기 어렵습니다. 이번에는 방·카메라·조명·소품을 바꾸면서 대상 물체의 영상과 정답 라벨을 함께 만듭니다. 방을 생성하는 Infinigen과 촬영하는 Isaac Sim 사이에는 USD 장면과 텍스처 파일이 전달됩니다.

| 파일 또는 구성 | 역할 |
|---|---|
| `sdg_config.json` | 방 목록, 촬영 횟수, 대상과 방해 물체를 정합니다. |
| `run.py` | 설정을 검사하고 설치된 5.1 Infinigen 예제를 실행합니다. |
| `native_runner.py` | 촬영을 마친 뒤 GUI를 관찰할 시간을 제공합니다. |
| `generate_rooms.py` | 별도 Infinigen 환경에서 방 생성과 USDC export를 실행합니다. |
| 두 writer | RGB·의미 분할과 경계 상자 검토 이미지를 각각 저장합니다. |

처음에는 NVIDIA가 제공하는 방을 사용합니다. 이 경로에서는 Infinigen을 따로 설치하거나 방을 새로 만들 필요가 없습니다.

## 1. 제공된 방에서 첫 데이터 만들기

Linux용 Isaac Sim 5.1과 RTX GPU, 지원 드라이버를 준비하세요. 설치 폴더에는 `standalone_examples/replicator/infinigen/infinigen_sdg.py`와 `infinigen_sdg_utils.py`가 있어야 합니다. 자산 루트에서는 Infinigen dining rooms, YCB 물체, Office 소품을 읽을 수 있어야 합니다.

저장소 루트에서 먼저 로컬 입력을 검사합니다.

```bash
python3 src/169_replicator_replicator_infinigen_sdg/run.py \
  --isaac-root "$HOME/isaacsim" --check
```

이 검사는 설치 파일과 설정을 읽습니다. 원격 자산의 다운로드나 GPU 렌더링은 시작하지 않습니다. 실제 촬영은 다음 명령입니다.

```bash
python3 src/169_replicator_replicator_infinigen_sdg/run.py \
  --isaac-root "$HOME/isaacsim" --headless \
  --output src/169_replicator_replicator_infinigen_sdg/output/first
```

`run.py`는 일반 Python으로 시작하지만, 실제 생성기는 지정한 설치본의 `python.sh`로 실행합니다. 기존 출력 폴더는 거부하므로 새 경로를 사용하세요. GUI를 보려면 `--headless`를 빼세요. 촬영이 끝나도 창은 남습니다. `--steps 120`은 **촬영 완료 후** GUI 업데이트를 120회 수행한 뒤 종료한다는 뜻입니다. 촬영량은 `--captures` 또는 설정의 `total_captures`가 정합니다.

### 설정에서 볼 부분

`sdg_config.json`의 capture 설정을 읽어 보세요.

```text
"total_captures": 6,
"num_floating_captures_per_env": 1,
"num_dropped_captures_per_env": 2,
"num_cameras": 2,
"resolution": [640, 480]
```

한 capture는 두 카메라가 현재 배치를 촬영하는 작업입니다. 따라서 정상 저장 시 RGB 수는 **6 capture × 2 camera = 12장**입니다. 하나의 방 배치에서 공중 상태를 1회, 낙하 이후를 2회 촬영하므로 총 6회에는 두 번의 방 배치가 필요합니다. 공급한 방이 하나뿐이라면 같은 방을 다시 사용하는 것이 정상입니다.

### 실행 결과 확인하기

출력 폴더에서 다음 항목을 연결해 읽으세요.

| 결과 | 확인할 내용 |
|---|---|
| `resolved_config.json` | 실제 적용된 촬영량과 writer 출력 경로 |
| `00_BasicWriter/` | 카메라별 RGB와 색으로 표시한 semantic segmentation |
| `01_DataVisualizationWriter/` | RGB 위의 2D 상자, normal 이미지 위의 3D 상자 |
| 콘솔의 방 로딩·floating/dropped 진행 | 저장 영상이 어느 배치 단계에서 나온 것인지 |

이미지 파일 전체 개수에는 분할과 시각화도 포함됩니다. RGB만 골라 12장인지 확인한 뒤 같은 카메라·프레임의 라벨을 비교하세요. GUI의 자유 카메라는 저장 카메라와 다릅니다. 저장 시점은 `/Cameras/cam_0`, `/Cameras/cam_1`에서 확인할 수 있습니다.

## 2. 보이는 물체와 정답 물체를 구분하기

이번 설정에는 나무 블록 3개, pudding box 2개와 방해 도형 8개, 책 2개가 들어 있습니다. 이들이 모두 같은 종류의 정답을 만드는 것은 아닙니다.

### 설정에서 볼 부분

자동 라벨 설정은 파일 이름의 숫자 접두사를 제거합니다.

```text
"files": ["/Isaac/Props/YCB/Axis_Aligned/036_wood_block.usd"],
"regex_replace_pattern": "^\\d+_",
"regex_replace_repl": ""
```

그래서 `036_wood_block`은 `wood_block` 클래스가 됩니다. pudding box는 `manual_label`에서 `pudding_box`라는 이름을 직접 지정합니다. 도형과 책은 시야를 복잡하게 만드는 방해 물체이며, 이 설정에서 대상 클래스 라벨을 붙이지 않습니다. **RGB에 보이는 개수와 학습 정답 객체 수가 다른 이유**입니다.

또한 각 자산 그룹의 `gravity_disabled_chance=0.25`는 일부 물체의 중력을 끕니다. 낙하 후 촬영에서도 떠 있는 물체가 있을 수 있습니다. 모든 물체가 식탁에 내려앉아야 한다고 판단하기보다, 같은 카메라에서 중력이 적용된 물체의 배치 변화를 확인하세요.

설치된 생성기는 방의 `TableDining` 이름을 포함하는 prim에서 식탁 위치를 찾아 배치 기준으로 씁니다. 짧은 물리 진행으로 초기 겹침을 완화하고, 더 긴 물리 진행으로 낙하를 계산한 뒤 촬영합니다. `rep.orchestrator.step(delta_time=0.0)`은 그 순간의 배치를 촬영하고, `rt_subframes=8`은 렌더 안정화를 돕습니다. subframe 8회가 서로 다른 물리 장면 8개를 의미하지는 않습니다.

### 직접 만든 방을 연결하려면

별도 [Infinigen 설치 안내](https://github.com/princeton-vl/infinigen/blob/main/docs/Installation.md)와 [Hello Room](https://github.com/princeton-vl/infinigen/blob/main/docs/HelloRoom.md)에 맞는 환경을 준비한 뒤 실행하세요. 외부 프로젝트의 `main`은 5.1에 고정된 버전이 아니므로 사용한 revision을 기록합니다.

```bash
python3 src/169_replicator_replicator_infinigen_sdg/generate_rooms.py \
  --infinigen-root /data/infinigen --python /data/infinigen-env/bin/python \
  --seeds 1 2 --output /data/generated-dining-rooms
```

이 도구는 DiningRoom으로 제한한 방을 생성한 뒤 USDC와 1024 해상도 텍스처를 export합니다. 출력 목록에서 방 전체의 루트 USD를 선택하고 텍스처가 있는 전체 폴더를 유지하세요.

```bash
python3 src/169_replicator_replicator_infinigen_sdg/run.py \
  --isaac-root "$HOME/isaacsim" --environment /data/exported-room/root.usdc \
  --headless --output src/169_replicator_replicator_infinigen_sdg/output/custom
```

`--environment`는 실제 파일 경로로 바꿔야 합니다. 여러 번 지정하면 여러 방을 공급합니다. 실행기는 로컬 경로를 `file://` URI로 변환해 설치본 helper가 원격 자산 경로로 오해하지 않도록 합니다. 식탁을 찾는 `TableDining` 구조도 유지되어야 하므로 임의의 가구 USD 하나를 방 입력으로 사용하지 않습니다.

## 3. 배경·물리·라벨의 관계 정리

```text
방 USD → 식탁 위치 찾기 → 대상과 방해 물체 배치
                                  ↓
                       공중 촬영 → 물리 낙하 → 추가 촬영
                                  ↓
                    같은 카메라의 RGB + 대상 라벨 + 검토 영상
```

방은 물체를 놓는 맥락을, 물리는 가능한 배치를, semantic label은 학습할 대상을 정합니다. 이 셋을 구분하면 “영상에 책이 있는데 라벨에는 없다”거나 “낙하 단계인데 블록이 떠 있다”는 결과를 설정과 연결해 설명할 수 있습니다.

## 4. 간단한 확인 실험

`sdg_config.json`을 복사한 뒤 `capture.path_tracing`만 **false → true**로 바꾸고 `--config`로 전달하세요. 같은 촬영량과 카메라 수를 유지하고 새 출력 경로를 사용합니다.

두 실행의 RGB에서 간접광·그림자와 촬영에 걸린 시간을 비교하세요. 기본 `debug_mode=true`는 설치본에서 난수 seed를 10으로 맞추므로 무작위 배치 차이를 줄이는 데 도움이 됩니다. 렌더 방식이 바뀌어도 정답 클래스가 새로 생기는 것은 아닙니다.

## 실행할 때 막히면

- **환경 목록이 비거나 `StopIteration` 발생**: 자산 루트의 dining rooms 폴더에 접근할 수 있는지 확인하세요. `--check`는 이 접근까지 검사하지 않습니다.
- **카메라가 식탁 밖을 촬영함**: 사용자 방의 `TableDining` prim 위치와 장면 단위를 확인하세요.
- **재질이 검거나 빠짐**: export된 텍스처와 상대 경로를 확인하세요. `rt_subframes`를 늘려도 없는 텍스처는 복구되지 않습니다.
- **일부 물체가 계속 떠 있음**: `gravity_disabled_chance`에 따른 결과인지 먼저 확인하세요.
- **창은 열렸는데 데이터가 없음**: GUI 시작 이후의 자산·writer 오류를 확인하세요. 앱 생성만으로 촬영 완료를 판단하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Environment Based Synthetic Dataset Generation with Infinigen](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html)에 대응합니다. 로컬 실행기는 설치본의 생성 알고리즘을 사용하고, 이 폴더의 완전한 설정과 출력 기록을 전달합니다.

문서 개정에서는 로컬 실행기·설정과 설치 예제의 역할을 확인했습니다. 실제 RTX 촬영과 외부 Infinigen 생성은 새로 실행하지 않았으며, `tutorial.json`의 검증 상태는 `not_run`입니다.
