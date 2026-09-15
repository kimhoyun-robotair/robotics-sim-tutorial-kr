# isaacsim.core.api.objects

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:56](../src/00_core_quickstart_isaacsim/run.py#L56)

위치·크기·색상 등을 지정해 튜토리얼에 필요한 기본 도형을 만드는 클래스 모음이다.

- `DynamicCuboid`: 외형·강체·충돌을 갖는 상자를 만들어 낙하, 쌓기, 집기 실험에 사용한다.
- `FixedCuboid`: 움직이지 않는 충돌 상자로 바닥이나 장애물을 만든다.
- `VisualCuboid` / `VisualSphere` / `VisualCapsule`: 물리 속성 없이 상자·구·캡슐 모양을 표시한다.
- 생성한 객체의 `get_world_pose()` / `set_world_pose()`로 자세를 읽고 바꾸거나, 물리·시각 재질을 적용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [DynamicCuboid API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.objects.DynamicCuboid)
- [FixedCuboid API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.objects.FixedCuboid)
- [VisualCuboid API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.objects.VisualCuboid)
- [VisualSphere API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.objects.VisualSphere)
- [VisualCapsule API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.objects.VisualCapsule)
