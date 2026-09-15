# isaacsim.core.api.physics_context.PhysicsContext

첫 등장: [09번 튜토리얼](../src/09_python_usd_core_api_overview/TUTORIAL.md) · [run.py:43](../src/09_python_usd_core_api_overview/run.py#L43)

World가 사용하는 물리 장면과 PhysX 설정에 접근하는 클래스이다.

- `world.get_physics_context()`: 현재 World의 물리 컨텍스트를 얻는다.
- `prim_path` / `get_current_physics_scene_prim()`: 물리 장면의 USD 경로 또는 Prim을 얻어 중력 등 USD 물리 속성을 설정한다.
- `enable_residual_reporting(True)`: 22번에서 물리 해석 잔차 정보를 읽을 수 있도록 보고 기능을 켠다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [PhysicsContext API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.physics_context.PhysicsContext)
