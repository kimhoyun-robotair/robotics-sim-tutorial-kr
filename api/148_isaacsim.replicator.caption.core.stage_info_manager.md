# isaacsim.replicator.caption.core.stage_info_manager

첫 등장: [171번 튜토리얼](../src/171_events_replicator_caption/TUTORIAL.md) · [generate_scene_graph.py:9](../src/171_events_replicator_caption/generate_scene_graph.py#L9)

`StageInfoManager`는 카메라 기준의 장면 정보를 모아 장면 그래프 생성을 실행하는 클래스이다.

- `get_instance()`로 관리자를 얻고, `refresh_configs()`와 `refresh_camera_path()`로 현재 설정을 반영한다.
- 모델 캡션을 요청한 경우 `set_model_params()`에 모델 URL·이름·API 키를 전달한다.
- `async_generate_camera_scene_graph_stage()`를 기다린 뒤 생성된 장면 그래프와 JSON 출력 파일을 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 VLM Scene Captioning (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html)
