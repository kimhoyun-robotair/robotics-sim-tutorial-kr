# 171. 이미지 속 물체와 관계를 장면 그래프로 읽기

## 이번에 배우는 것

**카메라에 보이는 물체를 노드로, 물체 사이 관계를 연결선으로 저장하고 문장 생성에 필요한 입력을 이해합니다.**

“컵이 탁자 위에 있습니다”라는 설명에는 물체 이름과 지지 관계가 함께 들어 있습니다. 장면 그래프는 이런 정보를 구조화한 표현입니다. 이번에는 먼저 실제 장면에서 그래프를 만들고, 관계를 줄인 그래프와 비교합니다. 문장 생성은 별도 모델을 연결한 뒤 선택적으로 수행합니다.

| 파일 | 역할 |
|---|---|
| `prepare.py`, `caption_config.json` | 장면·카메라·출력 경로를 담은 설정을 만듭니다. |
| `generate_scene_graph.py` | 이미 실행 중인 Isaac Sim 안에서 그래프를 생성합니다. |
| `prepare_ira.py`, `lesson.json` | 배우 시뮬레이션에 SceneGraphWriter를 연결합니다. |
| `patch_iro.py` | 기존 IRO 설정에 caption writer를 추가합니다. |

기본 설정은 full/pruned graph와 시각화를 저장하며 `global_caption`, `brief_caption`, `qa_caption`은 모두 false입니다. 이 상태에서는 NIM API key가 필요하지 않습니다.

## 1. 먼저 그래프만 생성하기

Isaac Sim 5.1 GUI, RTX GPU와 `isaacsim.replicator.caption.core` 확장을 준비하세요. 기본 입력은 5.1 자산팩의 `Isaac/Samples/Replicator/Captioning/test_caption.usda`입니다. 원격 자산 또는 같은 구조의 로컬 자산팩에 접근할 수 있어야 합니다.

저장소 루트에서 설정을 만든 뒤 앱을 시작합니다.

```bash
python3 src/171_events_replicator_caption/prepare.py \
  --output src/171_events_replicator_caption/output/graph_first
~/isaacsim/isaac-sim.sh
```

첫 명령은 `config.yaml`을 만들고 종료합니다. 그래프나 이미지가 아직 없는 것이 정상입니다. 이 파일은 JSON 표기로 작성한 YAML입니다.

1. **Window > Extensions**에서 caption core 확장을 켭니다.
2. **Tools > Action and Event Data Generation > VLM Scene Captioning**에서 기본 샘플을 Load Scene으로 열고 카메라 경로를 확인하세요. 기본 설정은 `/World/Cameras/Camera`입니다.
3. 다른 카메라를 사용한다면 `prepare.py --camera /실제/카메라/경로`와 새 출력 경로로 설정을 다시 만듭니다. 로컬 장면은 `--scene /절대경로/scene.usda`로 지정할 수 있습니다.
4. **Window > Script Editor**에서 `generate_scene_graph.py` 전체를 실행합니다. 이 파일은 함수를 정의하며 그 자체로 작업을 시작하지 않습니다.
5. 아래 코드를 실행합니다. 절대 경로는 첫 명령이 출력한 경로로 바꾸세요. 함수는 설정의 장면을 새로 열므로 작업 중인 기존 장면은 먼저 저장합니다.

```python
import asyncio
caption_task = asyncio.ensure_future(
    run_caption_config('/절대경로/output/graph_first/config.yaml')
)
```

### 코드에서 볼 부분

이 함수는 카메라가 실제 `UsdGeom.Camera`인지 검사한 뒤 설치된 `StageInfoManager`를 사용합니다.

```python
manager.refresh_configs()
manager.refresh_camera_path()
graph = await manager.async_generate_camera_scene_graph_stage()
```

`await`는 그래프 생성에 필요한 렌더링과 앱 처리가 진행되는 동안 내 작업을 기다리게 합니다. 앱 안에서 이미 실행하므로 `SimulationApp`을 다시 만들지 않습니다. 설정 작성용 `prepare.py`와 실행용 Script Editor 코드가 나뉜 이유입니다.

### 실행 결과 확인하기

Script Editor에서 `caption_task.done()`으로 완료 여부를 확인하고, True가 되면 `caption_task.result()`를 실행하세요. 작업 내부의 오류가 있다면 여기서 확인할 수 있습니다.

기본 카메라 이름이면 결과는 `output/graph_first/capture/Camera/Captions/` 아래에 저장됩니다. `full_scene_graph.json`, `pruned_scene_graph.json`과 시각화를 열어 보세요.

- 노드의 물체 이름을 이미지의 물체와 대응시킵니다.
- 연결선이 어떤 물체 사이 관계를 나타내는지 읽습니다.
- full과 pruned에서 남은 관계를 비교합니다.
- 문장 파일이 없어도 기본 그래프 전용 실행은 정상입니다.

파일 존재만 확인하지 말고 카메라에 실제로 보이는 물체와 비교하세요. 잘못된 카메라를 선택하면 문법적으로 올바른 그래프도 원하는 이미지의 설명이 되지 않습니다.

## 2. 관계를 줄이고 문장·프레임 출력에 연결하기

### 설정에서 볼 부분

`caption_config.json`의 다음 항목을 함께 읽어 보세요.

```text
"attach_label_to_usd": true,
"use_ai_label": false,
"save_full_scene_graph": true,
"save_pruned_scene_graph": true,
"pruning_ratio": 1.0
```

`attach_label_to_usd=true`는 기존 semantic label이 없는 prim에 이름 기반 라벨을 붙일 수 있게 합니다. 따라서 `use_ai_label=false`가 “기존 라벨 없는 물체는 무조건 제외”라는 뜻은 아닙니다. 자동 이름은 장면의 prim 이름에서 오므로 `Cube_01`처럼 의미가 약한 이름은 그래프 해석에도 영향을 줍니다. 이 동작은 [공식 caption 설정 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html#caption-configurations)을 참고하세요.

Support Tree는 바닥 → 탁자 → 컵처럼 지지 관계의 층을 표현합니다. Pruned graph는 관계에서 최소 신장 트리(MST)를 만든 뒤 일부 연결을 더 줄입니다. `pruning_ratio=1.0`은 원래의 모든 연결을 남긴다는 뜻이 아니라 **MST를 만든 뒤 추가로 줄이지 않는 조건**입니다.

문장까지 필요하면 NIM endpoint와 모델 이름, API key를 준비합니다. 키는 `NIM_API_KEY` 환경변수로 설정한 동일 터미널에서 앱을 실행하세요. 사용할 endpoint의 현재 모델·인증 조건은 해당 서비스에서 확인합니다.

```bash
python3 src/171_events_replicator_caption/prepare.py --captions \
  --output src/171_events_replicator_caption/output/caption_first
```

새 설정을 `run_caption_config(path, model_url='endpoint URL', model_name='model id')`로 실행합니다. 보조 함수는 환경변수 키와 명시적인 URL·모델 이름을 모두 요구합니다. 생성된 `scene_graph_caption.json`을 이미지와 대조해 그래프의 관계가 문장에서 유지되는지 확인하세요.

Script Editor 대신 UI만으로도 생성할 수 있습니다. **VLM Scene Captioning > Caption Settings**에서 장면과 Camera를 선택하고, **Model Settings**에 해당 endpoint의 URL·모델·키를 입력한 뒤 **Accept**합니다. Brief Caption 또는 Full Caption을 선택하고 **Generate Scene Graph**를 누르세요. QA 문장을 선택한다면 `qa_caption`과 full graph 저장도 함께 켭니다. UI의 모델 설정을 입력하는 방식과 환경변수를 검사하는 로컬 함수의 실행 조건은 구별하세요. 키를 저장소의 JSON이나 소스에 적지 않습니다.

### IRA와 IRO로 확장하기

배우의 행동을 프레임별로 기록하려면 IRA core/UI 확장을 준비한 뒤 다음 설정을 만듭니다.

```bash
python3 src/171_events_replicator_caption/prepare_ira.py --frames 90 \
  --output src/171_events_replicator_caption/output/ira_first
```

이 설정은 창고, 카메라 1대, 배우 2명을 사용합니다. Actor SDG의 Config File Path에 로드하고 Setup 후 실제 배우 이름을 확인하세요. 명령은 `Character_01 LookAround 3`, `Character_02 Idle 3`입니다. 이름을 맞춰 Save Commands한 뒤 Start Data Generation을 실행합니다. NavMesh가 필요하면 바닥에 Include Volume을 만들고 Navigation의 NavMesh 패널에서 Bake한 장면을 저장해 `--scene`으로 연결하세요.

`lesson.json`은 `scene_graph_interval=10`, `caption_interval=30`, `writer_interval=1`을 사용합니다. 기본 문장 생성 플래그는 꺼져 있으므로 30프레임 간격이 있어도 문장은 생기지 않습니다. 이미지와 그래프를 묶을 때는 실제 frame id를 확인합니다.

IRO에서는 먼저 object UI에서 자산·카메라가 포함된 완전한 YAML을 저장하세요. 다음 명령은 그 설정에 writer를 추가합니다.

```bash
~/isaacsim/python.sh src/171_events_replicator_caption/patch_iro.py \
  --input /data/object_config.yaml \
  --output src/171_events_replicator_caption/output/object_with_graph.yaml
```

기본 `CombinedIROSceneGraphWriter`는 object 출력과 그래프를 함께 사용합니다. `--caption-only-writer`는 `IROSceneGraphWriter`를 선택합니다. 새 설정을 IRO에 다시 로드하고 생성해야 데이터가 생깁니다. `patch_iro.py` 실행 자체는 설정 변경까지만 수행합니다.

## 3. 장면·그래프·문장의 관계 정리

```text
카메라와 의미 라벨 → 객체와 관계를 가진 full graph
                                  ↓
                            MST와 가지치기
                                  ↓
                    선택한 NIM 모델 → 문장 또는 질의응답
```

노드 이름, 지지 관계, 문장의 정확성은 각각 확인할 대상입니다. `max_object_capacity=100`은 그래프에 포함할 물체 수의 상한이며, 관계가 많은 장면을 무조건 전부 담는 것은 아닙니다. 좌표를 후속 처리에 사용한다면 설정의 `export_world`만 보고 세계 좌표라고 단정하지 마세요. 대조한 5.1 Caption core 0.0.32의 설정 로더는 이 값을 항상 false로 덮어씁니다. 또한 물체 노드의 `world_3d_bbox`는 `export_edges`, 캐릭터 노드의 같은 필드는 `export_world`에 따라 포함 여부가 달라집니다. 따라서 실제 노드 종류와 출력 필드를 확인하고 카메라 기준 정보와 세계 좌표 정보를 구별해서 읽어야 합니다.

## 4. 간단한 확인 실험

`prepare.py`에 `--pruning-ratio 0.5`만 추가해 새 설정을 만드세요. 장면·카메라·seed는 그대로 유지합니다.

두 실행의 full graph를 기준으로 pruned graph의 남은 연결을 비교하세요. 0.5는 MST 연결의 일부를 더 줄이므로 일반적으로 관계가 단순해집니다. 원래 full graph 연결 수의 정확히 절반이 남는다는 뜻은 아닙니다.

## 실행할 때 막히면

- **`config.yaml`만 있음**: 준비 단계까지만 끝난 상태입니다. Script Editor에서 비동기 함수를 실행하세요.
- **카메라가 없다는 오류**: 파일 경로와 prim 경로를 구분하고 Stage에서 실제 Camera 경로를 확인하세요.
- **`result()`가 아직 준비되지 않았다는 오류**: `done()`이 True가 될 때까지 앱 처리를 기다리세요.
- **그래프는 있는데 문장이 없음**: 기본 플래그 상태, 모델 URL·이름·키와 서비스 응답을 확인하세요.
- **출력 폴더가 이미 있다는 오류**: 캡처 재실행에는 새로 준비한 설정과 새 출력 경로를 사용하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [VLM Scene Captioning](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html)에 대응합니다. 로컬 도구는 그래프 전용 실행을 기본으로 하고, IRC·IRA·IRO 설정을 각각 준비합니다.

설정과 호출 흐름을 대조했으며 실제 GPU 그래프 생성, 배우 애니메이션과 NIM 요청은 이번 개정에서 실행하지 않았습니다. `tutorial.json`의 상태는 `not_run`입니다.
