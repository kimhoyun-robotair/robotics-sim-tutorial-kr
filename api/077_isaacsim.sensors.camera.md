# isaacsim.sensors.camera

첫 등장: [62번 튜토리얼](../src/62_sensors_sensors_camera/TUTORIAL.md) · [run.py:32](../src/62_sensors_sensors_camera/run.py#L32)

`isaacsim.sensors.camera`는 장면에 카메라를 만들고 렌더링 결과를 배열로 읽는 데 사용한다.

- `Camera`: 위치·방향·해상도·주기를 설정하고 `initialize()` 후 `get_rgba()`와 `get_current_frame()`으로 영상과 모션 벡터를 읽는다.
- 렌즈 실습에서는 초점거리와 조리개, OpenCV pinhole·fisheye 왜곡을 설정하고 `get_view_matrix_ros()`로 투영에 필요한 좌표 변환을 구한다.
- `SingleViewDepthSensor`: baseline·노이즈·측정 거리 등을 설정하고 `DepthSensorDistance`와 `distance_to_image_plane` 결과를 비교한다.
- `SingleViewDepthSensorAsset.add_template_render_product()`: 깊이 센서 설정을 재사용할 USD 카메라 에셋에 저장한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Camera API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.camera/docs/index.html#isaacsim.sensors.camera.Camera)
- [Isaac Sim 5.1 Depth Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html)
