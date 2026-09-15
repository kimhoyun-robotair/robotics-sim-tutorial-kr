# omni.simready.explorer

첫 등장: [135번 튜토리얼](../src/135_replicator_replicator_isaac_randomizers/TUTORIAL.md) · [simready_lab.py:14](../src/135_replicator_replicator_isaac_randomizers/simready_lab.py#L14)

SimReady 애셋 카탈로그에서 실습 장면에 사용할 물체를 찾는다.

- `find_assets()`로 table·plate·fruit 등의 검색어에 맞는 애셋을 비동기로 조회한다.
- 검색 결과의 `main_url`을 USD 참조로 사용하고 `name`을 생성 기록에 남긴다.
- `get_instance().browser_model`을 확인하고 필요할 때 Explorer 창을 연다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html)
- [omni.simready.explorer API](https://docs.omniverse.nvidia.com/kit/docs/omni.simready.explorer/latest/omni.simready.explorer.html#module-omni.simready.explorer)
