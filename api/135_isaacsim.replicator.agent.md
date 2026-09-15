# isaacsim.replicator.agent

첫 등장: [156번 튜토리얼](../src/156_events_replicator_agent/TUTORIAL.md) · [lesson.json:1](../src/156_events_replicator_agent/lesson.json#L1)

`isaacsim.replicator.agent`는 Actor SDG의 YAML/JSON 설정 키이며, 관련 확장 설정 경로에서도 사용됩니다.

- `scene`, `character`, `robot`으로 환경 자산·배우 수·행동 명령 파일을 지정합니다.
- `sensor`와 `replicator`로 카메라와 `IRABasicWriter` 등의 기록 옵션을 설정합니다.
- 배우 행동 스크립트와 카메라 범위는 `carb.settings`를 통해 확장 설정에 전달하기도 합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Actor SDG Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html#data-generation-from-script)
