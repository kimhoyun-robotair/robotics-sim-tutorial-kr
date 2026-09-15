# isaacsim.cortex.framework.dfb

첫 등장: [98번 튜토리얼](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) · [run.py:36](../src/98_digital_twin_cortex_1_overview/run.py#L36)

`dfb`는 Cortex 예제에서 재사용하는 로봇 행동과 컨텍스트를 제공하는 모듈입니다. 공통 동작을 직접 작성하지 않고 상태 머신이나 의사결정 노드에 연결합니다.

- `DfBasicContext`, `DfRobotApiContext`: 행동에서 사용할 로봇과 공유 상태를 보관하며, 모니터를 통해 판단에 필요한 상태를 갱신합니다.
- `DfApproachGrasp`, `DfLift`: 집기 자세로 접근하거나 물체를 들어 올리는 행동을 구성합니다.
- `DfCloseGripper`, `DfOpenGripper`: 그리퍼를 닫고 여는 행동을 상태 흐름에 넣는다.
- `make_go_home()`: 로봇을 기본 자세로 복귀시키는 행동을 만듭니다.
- `DfDiagnosticsMonitor`: UR10 상자 쌓기 예제에서 작업 상태를 주기적으로 진단하도록 상속합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
