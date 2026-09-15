# isaacsim.replicator.mobility_gen.impl.reader

첫 등장: [167번 튜토리얼](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) · [replay.py:48](../src/167_sdg_extra_replicator_mobility_gen/replay.py#L48)

`MobilityGenReader`는 저장된 MobilityGen 기록에서 프레임별 상태를 읽는 클래스이다.

- `len(reader)`로 기록 수를 확인하고, `read_state_dict(index=...)`로 재생할 프레임의 상태를 읽는다.
- `steps`에서 원래 기록의 step 번호를 얻어 새 센서 출력에도 같은 번호를 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 MobilityGen 확장 문서 (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.mobility_gen/docs/index.html)
- [공식 MobilityGen — Replay and Render](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#replay-and-render)
