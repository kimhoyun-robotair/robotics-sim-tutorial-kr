# isaacsim.core.api.loggers.DataLogger

첫 등장: [27번 튜토리얼](../src/27_core_advanced_data_logging/TUTORIAL.md) · [run.py:39](../src/27_core_advanced_data_logging/run.py#L39)

시뮬레이션 중 관절·목표 상태를 프레임별로 기록하고 다시 읽는 클래스이다.

- `world.get_data_logger()`: World에 연결된 기록기를 얻는다.
- `add_data_frame_logging_func()` / `start()` / `pause()`: 기록할 데이터를 반환하는 함수를 등록하고 기록을 시작·중지한다.
- `save()` / `load()`: 궤적 JSON을 저장하거나 불러온다.
- `get_num_of_data_frames()` / `get_data_frame()`: 프레임 개수와 기록된 상태·시간을 읽어 관절 명령 및 장면을 재생한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [DataLogger API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.loggers.DataLogger)
