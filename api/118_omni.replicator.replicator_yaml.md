# omni.replicator.replicator_yaml

첫 등장: [132번 튜토리얼](../src/132_replicator_replicator_overview/TUTORIAL.md) · [workflow.yaml:1](../src/132_replicator_replicator_overview/workflow.yaml#L1)

`omni.replicator.replicator_yaml`은 합성 데이터 생성 흐름을 YAML로 작성하는 확장입니다. 132번은 `workflow.yaml` 설정으로 사용합니다.

- `create.camera`, `create.render_product`, `create.cube`로 카메라·출력 영상·물체를 선언합니다.
- `writers.get`으로 `BasicWriter`와 저장할 데이터 종류를 지정합니다.
- `trigger.on_frame`, `modify.pose`, `distribution.uniform`으로 프레임마다 물체 자세를 바꿉니다. 각 키는 YAML 설정 문법입니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Replicator YAML 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#replicator-yaml)
- [NVIDIA Replicator YAML 설정 문서](https://docs.omniverse.nvidia.com/kit/docs/omni_replicator/1.13.30/source/extensions/omni.replicator.replicator_yaml/docs/README.html)
