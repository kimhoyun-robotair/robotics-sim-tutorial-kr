# omni.physx

첫 등장: [16번 튜토리얼](../src/16_python_usd_environment_setup/TUTORIAL.md) · [run.py:38](../src/16_python_usd_environment_setup/run.py#L38)

실행 중인 PhysX 장면에 질의하거나 물리 스텝 이벤트를 구독한다.

- `get_physx_scene_query_interface()`에서 `raycast_closest()`로 광선에 처음 닿는 물체를 찾는다.
- `overlap_box()`로 상자 영역과 겹치는 강체를 찾아 접촉 주변 상황을 확인한다.
- `get_physx_interface().subscribe_physics_step_events()`로 물리 스텝마다 콜백을 실행한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html)
- [omni.physx API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/runtime/source/omni.physx/docs/api/python.html)
