# isaacsim.replicator.incident

첫 등장: [161번 튜토리얼](../src/161_events_replicator_incident/TUTORIAL.md) · [incident_config.yaml:2](../src/161_events_replicator_incident/incident_config.yaml#L2)

`isaacsim.replicator.incident`는 Incident SDG 설정의 최상위 키입니다. 161번의 `incident_config.yaml`에서 사용합니다.

- `event.event_list`에 `ToppleEvent`, `FireEvent`, `SpillEvent`를 나열합니다.
- 사건별 대상 물체와 `trigger`의 시간 등을 지정합니다.
- `global.seed`와 `global.report_dir`로 시드와 사건 보고서 저장 경로를 설정하고, Actor SDG 장면과 함께 실행합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Incident SDG 이벤트 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html#event-configuration-in-iri-script)
