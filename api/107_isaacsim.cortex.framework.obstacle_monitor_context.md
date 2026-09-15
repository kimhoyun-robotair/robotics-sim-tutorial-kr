# isaacsim.cortex.framework.obstacle_monitor_context

첫 등장: [102번 튜토리얼](../src/102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) · [bin_stacking_behavior.py:38](../src/102_digital_twin_cortex_5_ur10_bin_stacking/bin_stacking_behavior.py#L38)

`obstacle_monitor_context`는 UR10 상자 쌓기에서 팔의 위치와 작업 단계에 따라 장애물 사용 여부를 갱신할 때 사용합니다.

- `ObstacleMonitor`: 뒤집기 작업대와 이동 경로용 모니터가 상속하며, `is_obstacle_required()`에서 해당 장애물이 필요한지 판단합니다.
- `ObstacleMonitorContext`: 로봇 팔의 명령 객체를 받아 작업 컨텍스트의 기반이 됩니다.
- `add_obstacle_monitors()`로 여러 모니터를 등록하여 작업 중 회피 조건을 갱신합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
