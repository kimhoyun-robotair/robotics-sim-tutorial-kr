# isaacsim.sensors.physics

첫 등장: [65번 튜토리얼](../src/65_sensors_sensors_physics_contact/TUTORIAL.md) · [run.py:32](../src/65_sensors_sensors_physics_contact/run.py#L32)

`isaacsim.sensors.physics`는 물체의 접촉과 움직임, 관절에 걸리는 힘을 센서 데이터로 확인하는 데 사용한다.

- `ContactSensor`: 낙하하는 큐브에 센서를 붙이고 `_sensor.acquire_contact_sensor_interface()`로 접촉 여부와 힘을 읽는다.
- `EffortSensor`: 관절의 토크를 읽고 센서 주기에 따른 값과 `use_latest_data=True`로 얻는 최신 값을 비교한다.
- `IMUSensor`: 필터 폭을 설정하고 `_sensor.acquire_imu_sensor_interface()`로 선형 가속도와 각속도를 읽는다.
- 측정 결과의 `is_valid`와 시간을 함께 확인하며, IMU 실습에서는 `read_gravity`로 중력 포함 여부를 바꾼다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 ContactSensor API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.physics/docs/index.html#isaacsim.sensors.physics.ContactSensor)
- [Isaac Sim 5.1 EffortSensor API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.physics/docs/index.html#isaacsim.sensors.physics.EffortSensor)
- [Isaac Sim 5.1 IMUSensor API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.physics/docs/index.html#isaacsim.sensors.physics.IMUSensor)
