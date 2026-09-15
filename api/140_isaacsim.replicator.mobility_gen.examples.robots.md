# isaacsim.replicator.mobility_gen.examples.robots

첫 등장: [167번 튜토리얼](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) · [custom_robot.py:2](../src/167_sdg_extra_replicator_mobility_gen/custom_robot.py#L2)

MobilityGen에서 사용할 수 있는 예제 로봇 클래스를 제공하는 모듈이다.

- `JetbotRobot`을 상속해 튜토리얼 전용 `TutorialSlowJetbot`을 정의한다.
- `keyboard_linear_velocity_gain`, `gamepad_linear_velocity_gain`, `path_following_speed`를 낮춰 입력 장치와 경로 추종의 이동 속도를 조정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 MobilityGen — Add a Custom Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#add-a-custom-robot)
