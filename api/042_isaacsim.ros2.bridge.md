# isaacsim.ros2.bridge

첫 등장: [17번 튜토리얼](../src/17_python_usd_util_snippets/TUTORIAL.md) · [run.py:37](../src/17_python_usd_util_snippets/run.py#L37)

`isaacsim.ros2.bridge`는 ROS 2 통신용 OmniGraph 노드와 Python 보조 함수를 제공한다. 튜토리얼에서는 확장을 활성화한 뒤 그래프에 노드 타입 문자열을 지정해 사용한다.

- `ROS2Context`·`ROS2QoSProfile`: 통신 컨텍스트와 전달 정책을 설정한다. `ROS2Publisher`·`ROS2Subscriber`는 지정한 메시지 타입을 송수신한다.
- `ROS2SubscribeTwist`·`ROS2SubscribeAckermannDrive`로 주행 명령을 받고, `ROS2PublishJointState`·`ROS2SubscribeJointState`로 관절 상태와 명령을 연결한다.
- `ROS2PublishClock`·`ROS2SubscribeClock`은 시간을, `ROS2PublishTransformTree`·`ROS2PublishRawTransformTree`는 좌표계 변환을 전달한다.
- `ROS2CameraHelper`·`ROS2CameraInfoHelper`·`ROS2PublishImage`·`ROS2RtxLidarHelper`로 센서 데이터를 발행한다. `read_camera_info()`는 렌더 결과 경로에서 해상도·내부 행렬·왜곡 계수를 읽어 CameraInfo writer에 전달한다.
- `OgnROS2ServiceServerRequest`·`OgnROS2ServiceServerResponse`·`OgnROS2ServiceClient`는 서비스 요청·응답을 연결하고, `ROS2ServicePrim`은 USD Prim 속성 조회·수정 서비스를 제공한다.

첫 등장은 17번의 `publish_multithreading_disabled` 실행 설정이다. ROS 2 노드 연결은 105번부터 다룬다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 ROS 2 Bridge API 및 OmniGraph 노드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.ros2.bridge/docs/index.html)
- [Isaac Sim 5.1 read_camera_info 사용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html#publish-camera-intrinsics-to-camerainfo-topic)
