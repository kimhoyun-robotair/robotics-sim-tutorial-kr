# 171. 3D 장면 그래프로 이미지와 문장을 연결하기

권장 학습 순서 **171** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t070`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

## 기대 결과와 준비

카메라에 보이는 객체/공간 관계를 실제 annotator로 읽어 `full_scene_graph.json`, `pruned_scene_graph.json`, 관계를 그린 이미지를 만듭니다. 선택적으로 외부 모델에 그래프를 전달해 brief/global/QA caption을 추가합니다. **기본 실습은 그래프 생성**이고 AI 문장 생성 성공을 의미하지 않습니다.

Isaac Sim 5.1 GUI, RTX GPU, `isaacsim.replicator.caption.core` 확장을 `Window > Extensions`에서 활성화합니다. 그래프만 만들 때 API key는 필요 없습니다. 공식 Assets의 `/Isaac/Samples/Replicator/Captioning/test_caption.usda`를 사용하며 인터넷 Assets 접근 또는 해당 경로의 로컬 5.1 자산팩이 필요합니다. GUI에서 기본 샘플이 다른 URL을 표시하면 Content Browser에서 실제 샘플 경로를 복사해 `--scene`으로 지정합니다. 패키지 외 공통 모듈은 사용하지 않습니다.

```bash
python3 prepare.py --output output/graph_01
/home/hoyunkim/isaacsim/isaac-sim.sh
```

위 명령은 이 패키지 디렉터리에서 실행하며 설치 경로는 자신의 환경에 맞춥니다. `prepare.py`는 현재 경로를 포함한 완전한 IRC 설정을 만들고 기존 output을 덮어쓰지 않습니다.

## GUI와 Script Editor 실습

1. `Tools > Action and Event Data Generation > VLM Scene Captioning`에서 Caption Settings를 엽니다. 샘플 USD를 선택해 `Load Scene`을 누릅니다. Stage에서 Camera Prim을 찾아 경로를 확인합니다. `/World/Cameras/Camera`가 아니면 `--camera`로 맞춘 새 설정을 생성합니다.
2. `Window > Script Editor`에서 `generate_scene_graph.py` 파일을 열어 실행한 후 아래를 실행합니다. 이것은 설치된 5.1 IRC의 `StageInfoManager`를 사용하는 보조 자동화이며 UI와 동일한 그래프 생성 기능을 호출합니다. 잘못된 카메라/빈 출력은 오류로 표시합니다. 새로운 장면을 여는 작업이므로 기존 작업 장면은 먼저 저장합니다.

```python
import asyncio
caption_task = asyncio.ensure_future(run_caption_config('/절대경로/output/graph_01/config.yaml'))
```

3. 생성이 끝나면 `caption_task.result()`를 실행해 비동기 예외를 확인합니다. Capture 아래 카메라별 Captions 폴더에서 full/pruned 그래프와 시각화 이미지를 엽니다. 각 객체 node가 이미지에 실제 존재하고 edge가 공간 관계를 나타내는지 직접 대조합니다. `caption_only=false`, `use_ai_label=false`는 별도 caption DB 없이 semantic label을 쓰도록 합니다.
4. 다음에는 `python3 prepare.py --output output/graph_half --pruning-ratio 0.5`로 만들고 재실행합니다. full graph와 pruned graph를 비교합니다. pruning=1도 모든 원래 edge를 보존한다는 뜻이 아니라 MST를 만든 뒤 추가 삭제하지 않는다는 뜻입니다. 0.5는 MST의 일부 edge를 더 제거합니다.

## 모델 문장 생성과 외부 서비스

문장까지 만들려면 NVIDIA API Catalog의 사용할 모델 페이지에서 NIM API key를 발급받거나 직접 배포한 NVIDIA NIM endpoint를 준비합니다. 계정·API 사용량·서비스 가용성은 사용자가 관리합니다. 서비스 URL/모델명을 해당 endpoint의 현재 값으로 직접 설정하며 오래된 예시 모델이 항상 가동 중이라고 가정하지 않습니다. 키는 소스/설정 파일에 기록하지 않습니다. `NIM_API_KEY` 환경변수를 설정한 동일 터미널에서 Isaac Sim을 실행하거나 Model Settings의 API key에 입력하고 Accept합니다. 본 도구는 실제 호출을 대신 실행하지 않았습니다.

```bash
python3 prepare.py --output output/caption_01 --captions
```

위 새 설정으로 `run_caption_config(path, model_url='사용할 endpoint URL', model_name='사용할 model id')`를 호출합니다. GUI만 쓰려면 Brief Caption/Full Caption 선택 후 Generate Scene Graph를 누릅니다. 출력 `scene_graph_caption.json`의 문장이 영상/그래프와 맞는지 검토합니다. `qa_caption=true`는 full graph도 저장하도록 해야 합니다. 원문 서비스 예시는 meta/llama3-8b-instruct 등이며 현재 계정에 제공되는 모델로 교체할 수 있습니다.

## IRA 프레임별 통합을 이 패키지만으로 실행

1. `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`와 IRC를 켭니다. `python3 prepare_ira.py --output output/ira_01 --frames 90`으로 완전한 Actor SDG 설정과 두 배우의 명령을 생성합니다. Assets는 창고 `.../Isaac/Environments/Simple_Warehouse/full_warehouse.usd`와 `/Isaac/People/Characters/`입니다.
2. Actor SDG의 Config File Path에서 설정을 로드합니다. NavMesh가 없으면 Stage 우클릭 Create > Navigation > NavMesh Include Volume을 바닥에 맞추고 Window > Navigation > NavMesh에서 Bake 후 새 USD를 저장하여 Scene 경로를 바꿉니다. Setup → 실제 배우 이름 확인 → Save Commands → Start Data Generation을 수행합니다.
3. SceneGraphWriter는 RGB writer와 함께 `scene_graph_interval=10`, `caption_interval=30`, `writer_interval=1`로 동작합니다. 기본 그래프 전용 설정입니다. 모델 caption을 활성화하려면 `lesson.json`의 caption_config에서 global/brief를 true로 바꾸고 NIM_API_KEY를 준비한 새 실행을 만듭니다. interval은 프레임 단위입니다. actor id와 frame id를 비교해 잘못된 시점의 이미지/문장을 묶지 않습니다.

## IRO 통합

`isaacsim.replicator.object`의 UI에서 기본 object 장면을 한 번 설정하고 완전한 YAML을 Save As 합니다. IRO가 사용하는 USD 자산과 카메라를 실제로 로드해 단일 frame 생성까지 확인합니다. 그런 다음 이 패키지의 `patch_iro.py`가 기존 설정의 scene/camera를 유지하면서 caption writer를 추가합니다. Isaac Sim의 Python은 PyYAML을 제공합니다.

```bash
/home/hoyunkim/isaacsim/python.sh patch_iro.py --input /절대경로/object_config.yaml --output output/object_with_graph.yaml
```

생성 설정을 IRO에 다시 로드해 실행합니다. 기본 CombinedIROSceneGraphWriter는 기존 object 출력도 유지합니다. `--caption-only-writer`는 IROSceneGraphWriter로 바꿔 다른 label 출력을 억제합니다. `--captions` 사용 시 NIM 서비스를 먼저 준비합니다. 새 기본 object scene을 복제하지 않고 사용자의 완전한 native 설정을 실제 수정하는 통합 실습입니다.

## 개념, 확인과 문제 해결

USD Prim 주소는 객체의 장면 내 위치이고 파일 경로는 자산의 저장 위치입니다. semantic label이 있어야 annotator에 잡힌 객체를 graph node로 쓸 수 있습니다. Support Tree는 floor→table→cup 같은 지지 계층이고 graph edge는 상대 위치 관계입니다. `max_object_capacity`는 bbox 크기 순으로 포함할 물체 수를 제한합니다. 세계 좌표와 카메라 좌표를 혼동하지 않습니다. 5.1 설치 구현은 `export_world`를 false로 고정하는 경로가 있으므로 출력 좌표계를 확인한 뒤 사용합니다.

그래프가 비면 카메라 경로/화면 안 객체/semantic label을 확인합니다. 문장만 없으면 global/brief/QA 플래그와 모델 인증을 확인합니다. UI가 느리면 Assets URL 접근을 별도로 확인합니다. 기본 설정으로 만들지 않은 caption 문장을 결과로 간주하지 않습니다. 한 변수 실험은 pruning_ratio만 1.0→0.5로 변경하는 것입니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [IRC 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html#example-isaacsim-replicator-caption-core-configuration-file)
- [UI 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html#using-the-ui-panel)
- [IRA writer 통합](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html#use-irc-in-isaacsim-replicator-agent)
- [IRO writer 통합](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html#use-irc-in-isaacsim-replicator-object)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
