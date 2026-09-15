# isaacsim.cortex.framework.df

첫 등장: [98번 튜토리얼](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) · [run.py:35](../src/98_digital_twin_cortex_1_overview/run.py#L35)

`df`는 Cortex 행동 네트워크의 기본 구성 요소를 제공하는 모듈입니다. 튜토리얼에서는 목표점 선택, 집기, 들어 올리기, 배치를 상태 전환과 조건 분기로 표현합니다.

- `DfState`, `DfStateSequence`, `DfStateMachineDecider`: 개별 상태와 순차 실행을 정의하고 상태 머신을 의사결정 네트워크에 연결합니다.
- `DfAction`, `DfDecider`, `DfDecision`, `DfNetwork`: 실행할 자식 행동을 선택하고 전체 네트워크를 구성합니다.
- `DfTimedDeciderState`, `DfWaitState`: 행동 실행 시간과 대기 시간을 지정합니다.
- `DfSetLockState`, `DfWriteContextState`: 집기·배치 중 분기 변경을 잠그거나 컨텍스트의 작업 상태를 갱신합니다. `DfLogicalState`는 Peck 예제에 import되어 있지만 직접 사용하지 않습니다.
- 블록 쌓기 예제는 `from ...df import *`로 가져온 `DfRldsNode`, `DfRldsDecider`도 사용하여 조건에 따라 실행 가능한 행동을 선택합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
