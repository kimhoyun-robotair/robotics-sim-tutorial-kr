# isaacsim.core.cloner

첫 등장: [163번 튜토리얼](../src/163_motion_cloner/TUTORIAL.md) · [run.py:38](../src/163_motion_cloner/run.py#L38)

원본 환경을 여러 경로에 복제하고 배치·물리 복제·충돌 관계를 설정하는 클래스 모음이다.

- `Cloner` / `GridCloner`: 지정한 위치 또는 일정한 격자 간격으로 환경을 복제한다.
- `define_base_env()` / `generate_paths()`: 복제 환경의 공통 경로와 각 인스턴스 경로를 준비한다.
- `clone()`: 원본 환경을 복제한다. 튜토리얼은 `copy_from_source`와 `replicate_physics` 옵션을 비교한다.
- `filter_collisions()`: 복제 환경 사이의 충돌을 구분하고 공통 지면과의 충돌은 유지한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Cloner API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.cloner/docs/index.html#isaacsim.core.cloner.Cloner)
- [GridCloner API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.cloner/docs/index.html#isaacsim.core.cloner.GridCloner)
