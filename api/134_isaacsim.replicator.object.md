# isaacsim.replicator.object

첫 등장: [144번 튜토리얼](../src/144_events_replicator_object/TUTORIAL.md) · [run.py:32](../src/144_events_replicator_object/run.py#L32)

`isaacsim.replicator.object`는 Object SDG의 YAML 최상위 설정 키입니다. 144–155번과 171번에서 물체 중심의 합성 데이터 생성에 사용합니다.

- `type`, `subtype`, `transform_operators`로 물체·카메라·조명과 배치를 선언합니다.
- 분포·참조·매크로·의존 관계로 여러 프레임의 외형과 배치를 바꿉니다.
- `num_frames`, `output_path`, `output_switches`로 생성 수와 이미지·라벨·깊이 등의 출력을 설정합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Object SDG 설정 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#embedded-interface)
