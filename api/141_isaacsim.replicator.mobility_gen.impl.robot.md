# isaacsim.replicator.mobility_gen.impl.robot

첫 등장: [167번 튜토리얼](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) · [custom_robot.py:3](../src/167_sdg_extra_replicator_mobility_gen/custom_robot.py#L3)

MobilityGen 로봇 구현을 등록하는 `ROBOTS` 레지스트리를 제공하는 모듈이다.

- `ROBOTS`는 MobilityGen이 로봇 클래스를 찾을 때 사용하는 등록 목록이다.
- `@ROBOTS.register()`로 `TutorialSlowJetbot` 클래스를 등록해 사용자 로봇을 사용할 수 있게 한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 MobilityGen 확장 문서 (내부 모듈 개별 참조 미제공)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.mobility_gen/docs/index.html)
- [공식 MobilityGen — 사용자 로봇 등록](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#add-a-custom-robot)
