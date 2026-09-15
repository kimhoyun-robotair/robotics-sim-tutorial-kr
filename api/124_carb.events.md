# carb.events

첫 등장: [136번 튜토리얼](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) · [run.py:188](../src/136_replicator_replicator_isaac_snippets/run.py#L188)

Kit 이벤트 스트림을 구독하고 콜백으로 전달된 이벤트를 읽는 모듈이다.

- 136번의 `IEventStream.create_subscription_to_pop()`은 Timeline 이벤트를 받아 재생 시각을 기록한다.
- `create_subscription_to_pop_by_type()`으로 Stage 종료나 특정 Timeline 이벤트만 받는다.
- 142·143번의 `carb.events.IEvent`는 콜백 인자 형식이다. `type`과 `payload`로 이벤트 종류와 데이터를 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html)
- [공식 Kit API — carb.events.IEvent](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/carb.events/carb.events.IEvent.html#carb.events.IEvent)
