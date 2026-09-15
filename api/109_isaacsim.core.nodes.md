# isaacsim.core.nodes

첫 등장: [105번 튜토리얼](../src/105_ros2_ros2_drive_turtlebot/TUTORIAL.md) · [run.py:49](../src/105_ros2_ros2_drive_turtlebot/run.py#L49)

로봇 제어·시간·렌더링을 OmniGraph에 연결하는 노드와 Python 노드의 상태 관리 클래스를 제공한다.

- `IsaacArticulationController` / `IsaacJointNameResolver`: 그래프의 관절 명령을 적용하고 관절 이름을 해석한다.
- `IsaacReadSystemTime` / `IsaacReadSimulationTime` / `IsaacRealTimeFactor`: 시스템 시간·시뮬레이션 시간과 실시간 대비 실행 비율을 읽는다.
- `IsaacCreateRenderProduct` / `OgnIsaacRunOneSimulationFrame`: 카메라 렌더 출력을 만들고 시작 시 파이프라인을 한 번만 실행하도록 신호를 보낸다.
- `IsaacCreateViewport` / `IsaacGetViewportRenderProduct` / `IsaacSetCameraOnRenderProduct`: 뷰포트와 렌더 출력·카메라를 연결한다.
- `BaseResetNode`: 130번 Python 노드의 상태 기반 클래스이다. `custom_reset()`에서 ROS 자원을 정리하며, 5.1의 개별 Python API 항목 대신 공식 사용 예를 연결한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Core OmniGraph Nodes 확장·노드 API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.nodes/docs/index.html)
- [BaseResetNode 공식 Python 사용 예](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html)
