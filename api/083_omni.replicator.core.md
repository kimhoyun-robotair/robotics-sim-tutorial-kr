# omni.replicator.core

첫 등장: [73번 튜토리얼](../src/73_sensors_sensors_rtx_radar/TUTORIAL.md) · [run.py:33](../src/73_sensors_sensors_rtx_radar/run.py#L33)

장면 무작위화, 센서 데이터 추출, 합성 데이터 저장을 연결하는 Replicator API다.

- `create`·`get`·`modify`: 객체·조명·카메라·Render Product를 만들고 Prim의 위치와 속성을 바꾼다. `functional.create`·`functional.physics`도 사용한다.
- `distribution`·`randomizer`·`trigger`: 값을 샘플링하고 색상·재질·배치를 바꾸며, 프레임 또는 사용자 이벤트에 작업을 연결한다.
- `AnnotatorRegistry`·`annotators`: RGB·깊이·분할·RTX 센서 데이터를 읽고 `Augmentation`으로 영상과 깊이에 변형을 적용한다.
- `WriterRegistry`·`writers`·`Writer`·`BackendDispatch`: 기본·사용자 Writer를 등록하고 데이터를 파일이나 ROS 2 출력에 연결한다.
- `orchestrator`: 캡처를 한 단계씩 실행하고 저장 완료를 기다린다. `set_global_seed()`와 `settings`로 난수 시드·Stage 단위·위쪽 축을 설정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_radar.html)
- [omni.replicator.core API](https://docs.omniverse.nvidia.com/kit/docs/omni_replicator/1.13.30/source/extensions/omni.replicator.core/docs/API.html#module-omni.replicator.core)
