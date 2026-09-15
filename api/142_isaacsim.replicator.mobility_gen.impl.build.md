# isaacsim.replicator.mobility_gen.impl.build

첫 등장: [167번 튜토리얼](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) · [replay.py:47](../src/167_sdg_extra_replicator_mobility_gen/replay.py#L47)

MobilityGen 기록 디렉터리에서 재생할 시나리오를 구성하는 모듈이다.

- `load_scenario()`로 기록된 설정과 장면을 불러와 시나리오 객체를 얻는다.
- 반환된 시나리오의 `enable_*_rendering()` 메서드로 RGB·분할·깊이·법선 출력을 선택한다.
- `load_state_dict()`와 `write_replay_data()`로 기록 상태를 복원한 뒤, `update_state()` 및 `state_dict_*()`로 렌더링 결과를 가져온다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 MobilityGen 확장 문서 (내부 모듈 개별 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.mobility_gen/docs/index.html)
- [공식 MobilityGen — Replay and Render](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#replay-and-render)
