# isaacsim.replicator.mobility_gen.impl.writer

첫 등장: [167번 튜토리얼](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) · [replay.py:49](../src/167_sdg_extra_replicator_mobility_gen/replay.py#L49)

`MobilityGenWriter`는 재생한 로봇 상태와 센서 결과를 MobilityGen 데이터 형식으로 저장하는 클래스이다.

- `copy_init()`으로 원본 기록의 초기 설정과 장면 자료를 출력 디렉터리에 복사한다.
- `write_state_dict_common()`으로 공통 상태를 원본 step 번호에 맞춰 저장한다.
- `write_state_dict_rgb()`, `write_state_dict_segmentation()`, `write_state_dict_depth()`, `write_state_dict_normals()`로 선택한 센서 결과를 저장한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 MobilityGen 확장 문서 (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.mobility_gen/docs/index.html)
- [공식 MobilityGen — Replay and Render](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#replay-and-render)
