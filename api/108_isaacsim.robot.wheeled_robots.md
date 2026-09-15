# isaacsim.robot.wheeled_robots

첫 등장: [105번 튜토리얼](../src/105_ros2_ros2_drive_turtlebot/TUTORIAL.md) · [run.py:26](../src/105_ros2_ros2_drive_turtlebot/run.py#L26)

여기서는 `isaacsim.robot.wheeled_robots` 확장의 OmniGraph 제어 노드를 다룹니다.

- `isaacsim.robot.wheeled_robots.DifferentialController`: 105번에서 선속도·각속도와 바퀴 크기·간격으로 좌우 바퀴 속도를 계산합니다.
- `isaacsim.robot.wheeled_robots.AckermannController`: 118번에서 속도·조향각으로 조향 관절의 각도와 구동 바퀴의 속도를 계산합니다.
- 계산한 출력을 `IsaacArticulationController` 노드에 연결해 로봇 관절에 적용합니다. 이 문서의 이름들은 그래프 노드 타입입니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Differential Controller 노드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/ogn/OgnDifferentialController.html)
- [Isaac Sim 5.1 Ackermann Controller 노드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/ogn/OgnAckermannController.html)
