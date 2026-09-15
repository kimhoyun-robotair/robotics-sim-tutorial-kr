# omni.kit.scripting

첫 등장: [141번 튜토리얼](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) · [orbit_behavior.py:6](../src/141_replicator_replicator_modular_scripting/orbit_behavior.py#L6)

USD Prim에 연결해 재생 상태에 따라 실행하는 Python 동작 스크립트의 기반이다.

- `BehaviorScript`를 상속해 `on_init()`·`on_play()`·`on_update()`·`on_stop()`·`on_destroy()`를 구현한다.
- `self.prim`과 `self.prim_path`로 대상 Prim의 노출 속성을 읽고 위치를 변경한다.
- `OrbitBehavior`는 재생 중 물체를 원운동시키고 정지하면 시작 위치로 되돌린다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [omni.kit.scripting 공식 활용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html#behavior-scripts)
