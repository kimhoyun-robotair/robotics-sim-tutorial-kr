# isaacsim.cortex.framework.robot

첫 등장: [98번 튜토리얼](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) · [run.py:37](../src/98_digital_twin_cortex_1_overview/run.py#L37)

`robot` 모듈은 Cortex의 팔·그리퍼 명령을 사용할 로봇을 준비할 때 사용합니다. 생성한 로봇은 `CortexWorld.add_robot()`으로 월드에 등록합니다.

- `add_franka_to_stage()`: 지정한 Prim 경로에 Franka를 추가하고 행동 네트워크에서 제어할 로봇을 반환합니다.
- `CortexUr10`: 상자 쌓기 작업장의 기존 UR10 Prim을 Cortex 로봇으로 연결합니다.
- 예제에서는 로봇의 `arm`으로 목표 자세를 보내고 `gripper`로 집기 동작을 제어합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
