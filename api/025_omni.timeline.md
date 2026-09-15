# omni.timeline

첫 등장: [06번 튜토리얼](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) · [urdf_import.py:27](../src/06_python_usd_manual_standalone_python/urdf_import.py#L27)

시뮬레이션의 재생 상태와 현재 시간을 제어하는 타임라인 인터페이스다.

- `get_timeline_interface()`로 가져온 타임라인에서 `play()`·`pause()`·`stop()`을 호출한다.
- `get_current_time()`으로 시간을 읽고, 시간 범위·반복 재생·프레임 속도를 설정한다.
- `get_timeline_event_stream()`과 `TimelineEventType`으로 시간 갱신을 관찰해 캡처나 주변 물체 확인을 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [omni.timeline API](https://docs.omniverse.nvidia.com/kit/docs/omni.timeline/latest/omni.timeline.html#module-omni.timeline)
