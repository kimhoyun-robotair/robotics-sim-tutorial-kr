# omni.syntheticdata._syntheticdata

첫 등장: [119번 튜토리얼](../src/119_ros2_ros2_python/TUTORIAL.md) · [camera_manual.py:139](../src/119_ros2_ros2_python/camera_manual.py#L139)

수동 카메라 발행 예제에서 센서 종류를 나타내는 열거형을 사용한다.

- `SensorType.Rgb`와 `SensorType.DistanceToImagePlane`로 RGB·깊이 채널을 지정한다.
- 열거형의 `name`을 `SyntheticData.convert_sensor_type_to_rendervar()`에 전달해 해당 발행 게이트를 찾는다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [omni.syntheticdata._syntheticdata 공식 활용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html#manual-image-publishing)
