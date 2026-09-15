# usdrt.Usd

첫 등장: [138번 튜토리얼](../src/138_replicator_replicator_object_based_sdg/TUTORIAL.md) · [object_based_sdg.py:139](../src/138_replicator_replicator_object_based_sdg/object_based_sdg.py#L139)

Fabric 장면에 연결해 특정 API 스키마가 적용된 prim을 조회한다.

- `usdrt.Usd.Stage.Attach`: 현재 USD Stage ID를 사용해 USDRT Stage를 얻는다.
- `GetPrimsWithAppliedAPIName("PhysxSceneAPI")`: 물리 장면을 찾아 객체 기반 합성 데이터 생성의 물리 설정에 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [NVIDIA USDRT Python API: Usd.Stage](https://docs.omniverse.nvidia.com/kit/docs/usdrt.scenegraph/latest/py_api/py_api.html#usdrt.Usd.Stage)
- [Isaac Sim: Object Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html)
