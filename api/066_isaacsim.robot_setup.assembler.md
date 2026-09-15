# isaacsim.robot_setup.assembler

첫 등장: [49번 튜토리얼](../src/49_importers_assemble_robots/TUTORIAL.md) · [run.py:36](../src/49_importers_assemble_robots/run.py#L36)

서로 다른 로봇 USD의 장착 프레임을 맞추고 고정 조인트로 연결하는 API입니다.

- `RobotAssembler.begin_assembly()`: UR10e와 Allegro Hand의 루트 및 장착 경로를 지정합니다.
- `assemble()`, `finish_assemble()`: 손의 방향을 조정한 뒤 조립하고, 물리 실행 후 조립 처리를 마칩니다.
- `cancel_assembly()`: 시작한 조립을 취소하는 예제 분기에서 사용합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [RobotAssembler](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_setup.assembler/docs/index.html#isaacsim.robot_setup.assembler.RobotAssembler)
