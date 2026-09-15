# isaacsim.cortex.framework.cortex_world

첫 등장: [98번 튜토리얼](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) · [run.py:34](../src/98_digital_twin_cortex_1_overview/run.py#L34)

`CortexWorld`는 로봇의 행동 판단과 물리 시뮬레이션을 함께 진행하는 월드 클래스입니다. 튜토리얼에서는 Franka와 UR10의 행동 네트워크를 실행할 때 사용합니다.

- `CortexWorld()`로 월드를 만들고 `add_robot()`으로 Cortex 로봇을 등록합니다.
- `add_decider_network()`로 행동 네트워크를 연결하고 `run()`으로 실행합니다.
- `CortexWorld.instance()`로 현재 월드에 접근하며, 확장 예제에서는 비동기 초기화와 프레임 갱신을 연결합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
