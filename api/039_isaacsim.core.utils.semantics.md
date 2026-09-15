# isaacsim.core.utils.semantics

첫 등장: [16번 튜토리얼](../src/16_python_usd_environment_setup/TUTORIAL.md) · [run.py:37](../src/16_python_usd_environment_setup/run.py#L37)

합성 데이터와 인식 결과에 사용할 물체의 의미 라벨을 붙이거나 정리하는 함수 모음이다.

- `add_labels()`: Prim에 물체 분류 등의 라벨을 추가한다.
- `add_update_semantics()`: 일부 ROS 2·Replicator 예제에서 기존 방식의 의미 정보를 추가·갱신한다.
- `upgrade_prim_semantics_to_labels()`: 기존 의미 정보를 라벨 방식으로 변환한다.
- `remove_labels()`: 기존 장면의 라벨을 제거해 새 데이터 생성에 맞게 정리한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [add_labels API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.semantics.add_labels)
- [add_update_semantics API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.semantics.add_update_semantics)
- [upgrade_prim_semantics_to_labels API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.semantics.upgrade_prim_semantics_to_labels)
- [remove_labels API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.semantics.remove_labels)
