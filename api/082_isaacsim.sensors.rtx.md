# isaacsim.sensors.rtx

첫 등장: [72번 튜토리얼](../src/72_sensors_sensors_rtx_lidar/TUTORIAL.md) · [run.py:34](../src/72_sensors_sensors_rtx_lidar/run.py#L34)

`isaacsim.sensors.rtx`는 RTX 센서를 구성하고 annotator가 추출한 측정 결과를 읽는 데 사용한다.

- `LidarRtx`: 센서 설정 파일과 스캔 주기를 지정해 LiDAR를 만들고 `initialize()`로 준비한다.
- `attach_annotator()`로 점군 추출기와 스캔 버퍼를 연결하고 `get_current_frame()`으로 점군·거리·강도·타임스탬프를 읽는다.
- `detach_all_annotators()`로 연결한 데이터 추출기를 해제한다.
- `apply_nonvisual_material()`: 시각 재질에 기본 재료·코팅·동작 특성을 추가하고 생성된 센서용 속성을 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 LidarRtx API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.rtx/docs/index.html#isaacsim.sensors.rtx.LidarRtx)
- [Isaac Sim 5.1 RTX Sensor Non-Visual Materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html)
