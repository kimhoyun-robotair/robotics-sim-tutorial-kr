# isaacsim.storage.native

첫 등장: [03번 튜토리얼](../src/03_core_quickstart_isaacsim_robot/TUTORIAL.md) · [run.py:51](../src/03_core_quickstart_isaacsim_robot/run.py#L51)

Isaac Sim 기본 에셋이 저장된 위치를 조회하는 스토리지 유틸리티이다.

- `get_assets_root_path()`: NVIDIA 기본 로봇·소품·환경 에셋의 루트 경로를 얻는다.
- 튜토리얼에서는 반환된 경로 뒤에 `/Isaac/Robots/...` 등의 상대 경로를 붙여 USD 에셋을 불러온다.
- 공식 함수 문서는 `isaacsim.storage.native.nucleus.get_assets_root_path` 이름으로 제공된다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [get_assets_root_path API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.storage.native/docs/index.html#isaacsim.storage.native.nucleus.get_assets_root_path)
