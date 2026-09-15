# carb.eventdispatcher

첫 등장: [136번 튜토리얼](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) · [run.py:32](../src/136_replicator_replicator_isaac_snippets/run.py#L32)

이름이 붙은 앱 이벤트와 사용자 이벤트를 구독하거나 전달한다.

- `get_eventdispatcher().observe_event()`로 렌더 프레임·앱 업데이트 또는 사용자 이벤트를 받는다.
- `dispatch_event()`로 Prim 경로와 상태를 담은 payload를 전달해 동작 변경과 완료를 알린다.
- Behavior 예제는 이벤트를 특정 Prim에 연결하고 종료할 때 구독을 해제한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html)
- [carb.eventdispatcher API](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/carb.eventdispatcher.html#module-carb.eventdispatcher)
