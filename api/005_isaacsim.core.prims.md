# isaacsim.core.prims

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:60](../src/00_core_quickstart_isaacsim/run.py#L60)

USD Prim을 감싸 위치·강체·충돌·관절 상태를 Python에서 다루는 클래스 모음이다.

- `XFormPrim` / `SingleXFormPrim`: 여러 Prim 또는 단일 Prim의 위치·회전·스케일을 읽고 변경한다.
- `RigidPrim` / `SingleRigidPrim`: 강체의 질량, 속도와 물리 상태를 다룬다.
- `GeometryPrim`: 형상의 충돌 속성을 다룬다. 00번에서는 `apply_collision_apis()`로 기존 도형에 충돌을 추가한다.
- `Articulation` / `SingleArticulation`: 여러 관절 구조 또는 단일 로봇의 관절 상태를 읽고 명령을 적용한다.
- 복수 객체용 `get_world_poses()` / `set_world_poses()`와 단일 객체용 `get_world_pose()` / `set_world_pose()`를 사용 대상에 맞게 구분한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [XFormPrim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.XFormPrim)
- [SingleXFormPrim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.SingleXFormPrim)
- [RigidPrim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim)
- [SingleRigidPrim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.SingleRigidPrim)
- [GeometryPrim API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.GeometryPrim)
- [Articulation API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.Articulation)
- [SingleArticulation API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.SingleArticulation)
