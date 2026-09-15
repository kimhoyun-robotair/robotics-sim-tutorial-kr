# isaacsim.cortex.framework.cortex_utils

첫 등장: [99번 튜토리얼](../src/99_digital_twin_cortex_2_decider_networks/TUTORIAL.md) · [run.py:21](../src/99_digital_twin_cortex_2_decider_networks/run.py#L21)

`cortex_utils`는 Cortex 실행 코드에서 행동 모듈과 자산 경로를 준비하는 보조 함수 모듈입니다.

- `load_behavior_module()`: 선택한 로컬 Python 행동 파일을 불러와 `make_decider_network(robot)`를 호출할 수 있게 합니다.
- `get_assets_root_path_or_die()`: Isaac 자산의 기본 경로를 가져온다. UR10 예제는 이 경로로 작업장과 상자 USD 경로를 구성합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
