# isaacsim.robot.policy.examples.robots

첫 등장: [164번 튜토리얼](../src/164_motion_robot_policy_example/TUTORIAL.md) · [run.py:30](../src/164_motion_robot_policy_example/run.py#L30)

`robots` 모듈의 정책 클래스는 로봇 상태와 속도 명령을 받아 학습된 보행 정책을 실행합니다. 튜토리얼에서는 H1·Spot의 이동 궤적을 기록하고 H1 정책의 입력 구성을 확인합니다.

- `H1FlatTerrainPolicy`, `SpotFlatTerrainPolicy`: Prim 경로와 초기 위치를 지정하여 해당 로봇의 정책 제어기를 만듭니다.
- `initialize()` 이후 물리 콜백에서 `forward(dt, command)`를 호출하여 전진·횡이동·회전 속도 명령을 전달합니다.
- `robot.get_world_pose()`로 이동 결과를 읽으며, `robot.dof_names`로 관절 순서를 기록합니다.
- 배포 예제는 `load_policy()`로 정책·환경 설정 파일을 불러오고, H1 클래스를 상속하여 `_compute_observation()`의 첫 관측값을 기록합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.robot.policy.examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.policy.examples/docs/index.html)
