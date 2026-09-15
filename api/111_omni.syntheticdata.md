# omni.syntheticdata

첫 등장: [114번 튜토리얼](../src/114_ros2_ros2_camera_publishing/TUTORIAL.md) · [run.py:26](../src/114_ros2_ros2_camera_publishing/run.py#L26)

렌더링으로 만들어지는 센서 데이터의 처리 노드 연결을 다룬다.

- `SyntheticData._get_node_path()`로 Render Product의 `IsaacSimulationGate` 노드를 찾아 ROS 2 카메라 발행 주기를 설정한다.
- `SyntheticData.NodeConnectionTemplate`으로 사용자 영상 Writer에 시뮬레이션 시간 입력을 연결한다.
- `convert_sensor_type_to_rendervar()`로 RGB·깊이 센서 종류에 해당하는 렌더 변수 이름을 얻는다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [omni.syntheticdata 공식 활용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html#publish-rgb-images)
