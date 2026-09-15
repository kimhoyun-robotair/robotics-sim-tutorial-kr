# isaacsim.replicator.behavior.utils.behavior_utils

첫 등장: [141번 튜토리얼](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) · [run.py:41](../src/141_replicator_replicator_modular_scripting/run.py#L41)

Behavior 스크립트를 Prim에 연결하고 완료 이벤트를 기다리는 비동기 도우미 모듈이다.

- `add_behavior_script_with_parameters_async()`로 기본 behavior 또는 로컬 스크립트를 연결하고 노출 USD 속성을 설정한다.
- `publish_event_and_wait_for_completion_async()`로 동작을 요청한 뒤 예상 상태의 응답을 기다린다. 튜토리얼에서는 궤도 이동과 상자 쌓기에 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 Modular Behavior Scripting — 도우미 함수 사용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html)
