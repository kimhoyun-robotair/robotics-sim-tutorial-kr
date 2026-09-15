# isaacsim.examples.interactive.ur10_palletizing.ur10_palletizing

첫 등장: [143번 튜토리얼](../src/143_replicator_replicator_ur10_palletizing/TUTORIAL.md) · [run.py:36](../src/143_replicator_replicator_ur10_palletizing/run.py#L36)

UR10의 상자 쌓기 예제 장면을 불러와 실행하는 BinStacking 클래스를 제공한다.

- `BinStacking()`: 상자 쌓기 샘플 객체를 만든다.
- `load_world_async()` / `on_event_async()`: 예제 World를 비동기로 불러오고 쌓기 동작을 시작한다.
- 143번은 이 동작 위에 접촉 이벤트별 합성 데이터 촬영을 추가한다.
- 5.1 문서에 클래스별 API 항목이 없어 같은 import와 메서드를 사용하는 공식 예제를 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [BinStacking 공식 사용 예](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html)
