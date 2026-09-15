# isaacsim.robot_motion.motion_generation.lula

첫 등장: [57번 튜토리얼](../src/57_motion_manipulators_lula_rrt/TUTORIAL.md) · [run.py:51](../src/57_motion_manipulators_lula_rrt/run.py#L51)

Lula 기반 경로 계획기를 Isaac Sim 로봇에 연결하는 모듈입니다.

- `RRT`: Franka용 설정으로 샘플링 기반 경로 계획기를 만듭니다.
- `set_max_iterations()`, `add_obstacle()`: 탐색 횟수와 장애물을 지정합니다.
- `set_end_effector_target()`, `update_world()`: 목표와 환경을 갱신하며, `PathPlannerVisualizer`를 통해 관절 action 경로를 얻습니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [RRT](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.lula.RRT)
