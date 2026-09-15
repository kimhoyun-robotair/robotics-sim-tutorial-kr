# isaacsim.replicator.synthetic_recorder.synthetic_recorder

첫 등장: [133번 튜토리얼](../src/133_replicator_replicator_recorder/TUTORIAL.md) · [run.py:31](../src/133_replicator_replicator_recorder/run.py#L31)

`SyntheticRecorder`는 카메라의 합성 데이터를 설정된 writer로 기록하는 클래스이다.

- `writer_name`, `basic_writer_params`로 RGB·2D 경계 상자·의미 분할 출력 항목을 정한다.
- `rp_data`, `num_frames`, `rt_subframes`, 출력 경로 속성으로 카메라·해상도·촬영량을 설정한다.
- `start_stop_async()`로 headless 기록을 실행하며, `control_timeline`으로 애니메이션 재생도 함께 제어한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 Synthetic Recorder 확장 문서 (개별 클래스 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.synthetic_recorder/docs/index.html)
