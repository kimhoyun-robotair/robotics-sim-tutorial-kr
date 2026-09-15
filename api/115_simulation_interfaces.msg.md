# simulation_interfaces.msg

첫 등장: [121번 튜토리얼](../src/121_ros2_ros2_simulation_control/TUTORIAL.md) · [control.py:17](../src/121_ros2_ros2_simulation_control/control.py#L17)

`simulation_interfaces.msg`는 Isaac Sim의 ROS 2 Simulation Control 서비스를 호출할 때 사용하는 공통 메시지 타입이다.

- `SimulationState`: `STATE_PLAYING`과 `STATE_PAUSED`로 실행 상태를 지정하고, 스텝 실행 후 다시 일시정지 상태인지 확인한다.
- `Result`: 응답의 결과 코드를 `RESULT_OK`와 비교하고 실패하면 `error_message`를 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Simulation Interfaces 1.1.0 SimulationState 메시지 정의](https://github.com/ros-simulation/simulation_interfaces/blob/1.1.0/msg/SimulationState.msg)
- [Simulation Interfaces 1.1.0 Result 메시지 정의](https://github.com/ros-simulation/simulation_interfaces/blob/1.1.0/msg/Result.msg)
- [Isaac Sim 5.1 ROS2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)
