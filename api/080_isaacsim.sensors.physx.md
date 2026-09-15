# isaacsim.sensors.physx

첫 등장: [68번 튜토리얼](../src/68_sensors_sensors_physics_proximity/TUTORIAL.md) · [run.py:33](../src/68_sensors_sensors_physics_proximity/run.py#L33)

`isaacsim.sensors.physx`는 주변 물체를 감지하거나 광선과 충돌체의 교차 결과로 거리를 측정하는 데 사용한다.

- `ProximitySensor`를 물체에 연결하고 `register_sensor()`로 등록한 뒤 `get_data()`를 읽으며, 종료할 때 `clear_sensors()`로 정리한다.
- `_range_sensor.acquire_generic_sensor_interface()`: Generic 센서에 광선 묶음을 전달하고 깊이 버퍼를 읽는다.
- `_range_sensor.acquire_lidar_sensor_interface()`: 회전 LiDAR의 거리·점군·방위각·천정각 데이터를 읽는다.
- `_range_sensor.acquire_lightbeam_sensor_interface()`: 여러 광선으로 만든 감지 구역의 거리와 물체 감지 결과를 읽는다. 센서 Prim은 `RangeSensorCreateGeneric`, `RangeSensorCreateLidar`, `IsaacSensorCreateLightBeamSensor` 명령으로 생성한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 PhysX Sensors API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.physx/docs/index.html)
