# simulation_interfaces.srv

첫 등장: [121번 튜토리얼](../src/121_ros2_ros2_simulation_control/TUTORIAL.md) · [control.py:18](../src/121_ros2_ros2_simulation_control/control.py#L18)

`simulation_interfaces.srv`는 외부 ROS 2 노드에서 Isaac Sim을 제어하기 위한 요청·응답 타입이다. 튜토리얼에서는 각 타입의 `Request()`를 만들어 서비스 클라이언트로 보낸다.

- `GetSimulatorFeatures`: 시뮬레이터가 지원하는 기능을 조회한다.
- `SetSimulationState`·`GetSimulationState`: 재생·일시정지 상태를 설정하고 확인한다.
- `SpawnEntity`·`DeleteEntity`: USD 파일에서 물체를 생성하고, 선택적으로 실습에서 생성한 물체를 삭제한다.
- `SetEntityState`·`GetEntityState`: 물체를 월드 좌표로 이동시키고 실제 위치를 다시 읽어 확인한다.
- `StepSimulation`: 일시정지 상태에서 지정한 횟수만큼 진행한 뒤 일시정지 상태로 돌아왔는지 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Simulation Interfaces 1.1.0 SpawnEntity 서비스 정의](https://github.com/ros-simulation/simulation_interfaces/blob/1.1.0/srv/SpawnEntity.srv)
- [Isaac Sim 5.1 ROS2 Simulation Control 서비스](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html#using-the-ros-2-simulation-control-services)
