# isaacsim.asset.validation.physics_rules

첫 등장: [50번 튜토리얼](../src/50_importers_asset_validation/TUTORIAL.md) · [run.py:30](../src/50_importers_asset_validation/run.py#L30)

Asset Validator에 등록해 사용할 Isaac Sim 물리 설정 검사 규칙입니다.

- `RigidBodyHasMassAPI`: 강체의 질량·관성 설정을 검사합니다.
- `InvisibleCollisionMeshHasPurposeGuide`: 보이지 않는 충돌 메시의 purpose 설정을 검사합니다.
- 튜토리얼에서는 `ValidationEngine.enable_rule()`로 두 규칙을 활성화하고, 설정 수정 전후의 검사 결과를 비교합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 물리 검증 규칙](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html#isaacsim-physicsrules)
