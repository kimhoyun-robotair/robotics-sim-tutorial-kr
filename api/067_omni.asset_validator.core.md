# omni.asset_validator.core

첫 등장: [50번 튜토리얼](../src/50_importers_asset_validation/TUTORIAL.md) · [run.py:29](../src/50_importers_asset_validation/run.py#L29)

USD Stage에 선택한 검사 규칙을 실행하고 발견된 문제를 모은다.

- `ValidationEngine(init_rules=False)`를 만든 뒤 `enable_rule()`로 Isaac Sim 물리 검사 규칙을 선택한다.
- `validate(stage).issues()`로 질량·관성·충돌 메시 속성의 문제를 확인한다.
- 튜토리얼에서는 같은 검사를 수정 전후에 실행해 문제가 사라졌는지 비교한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)
- [omni.asset_validator.core API](https://docs.omniverse.nvidia.com/kit/docs/asset-validator/latest/source/extensions/omni.asset_validator.core/docs/api.html#omni-asset-validator-core-api)
