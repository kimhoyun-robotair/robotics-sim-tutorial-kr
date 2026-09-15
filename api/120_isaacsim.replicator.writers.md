# isaacsim.replicator.writers

첫 등장: [133번 튜토리얼](../src/133_replicator_replicator_recorder/TUTORIAL.md) · [TUTORIAL.md:53](../src/133_replicator_replicator_recorder/TUTORIAL.md#L53)

`isaacsim.replicator.writers`는 Isaac Sim용 합성 데이터 Writer를 제공하는 Python 모듈입니다. 133번에서는 `DataVisualizationWriter`를 사용합니다.

- `from isaacsim.replicator.writers import DataVisualizationWriter`로 불러온 뒤 Recorder의 Custom Writer로 선택합니다.
- 매개변수 JSON으로 RGB·법선 영상 위에 표시할 2D·3D 경계 상자와 색상을 지정합니다.
- 기록된 시각화 이미지로 물체 라벨과 경계 상자가 맞는지 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 DataVisualizationWriter API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.writers/docs/index.html#isaacsim.replicator.writers.DataVisualizationWriter)
