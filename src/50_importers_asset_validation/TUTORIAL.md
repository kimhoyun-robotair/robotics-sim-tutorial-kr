# 50. t132 · 잘못된 USD를 만들고 공식 validator로 고치기

권장 학습 순서 **50** · 로봇 자산 가져오기와 제작 · 출처 ID `t132`

Isaac Sim **5.1.0**의 `isaacsim.asset.validation` 규칙을 실제로 실행한다. 작은 body에 질량/관성/주축 quaternion/숨겨진 collider purpose 결함을 넣고 두 공식 규칙의 before/after 결과를 기록한다. validator 전체 통과와 선택한 두 규칙 통과를 구분한다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, 기본 제공 `isaacsim.asset.validation` 및 asset validator가 필요하다. fixture stage는 코드에서 작성하므로 다른 package나 외부 asset이 필요 없다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/50_importers_asset_validation
"$ISAAC_SIM/python.sh" run.py --headless --frames 60
"$ISAAC_SIM/python.sh" run.py --keep-defects --output output/gui
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 120회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

기본은 `before.usda`, `after.usda`, `validation.json`을 새 output 폴더에 쓴다. 실제 공식 checker가 의도한 결함을 찾지 못하거나 수리 후 선택 규칙 issue가 남으면 실패한다. GUI 모드는 결함을 유지한 stage를 열어 둔다. invisible fixture가 안 보이는 것은 오류가 아니라 이번 검사 대상 속성이다.

## 두 규칙을 직접 비교하기

1. before에서 body의 mass=0, diagonal inertia=(0,0,0), principal axes quaternion=(2,0,0,0)을 찾는다. 단위 quaternion이 아니므로 유효한 회전이 아니다.
2. invisible CollisionAPI prim의 purpose가 default인 것을 확인한다. `InvisibleCollisionMeshHasPurposeGuide`가 guide를 요구한다.
3. 기본 실행은 0.1 m 정육면체, 질량 1 kg에 맞춰 대각 관성 `(1/600,1/600,1/600)` kg·m², principal axes identity, purpose=guide로 바꾼다. 이 값은 box 관성식에서 독립적으로 유도된다.
4. JSON의 before issue와 after 빈 목록을 비교한다. 검사하는 규칙은 `RigidBodyHasMassAPI`와 `InvisibleCollisionMeshHasPurposeGuide`뿐이다. 로봇 전체 적합성 통과를 의미하지 않는다.
5. GUI 모드에서 **Window > Asset Validator**를 열고 위 두 규칙만 선택해 검사한다. Properties에서 quaternion만 먼저 고치고 재검사해 어떤 issue가 남는지 관찰한다.

## 5.1의 전체 규칙을 읽는 방법

Asset Validator에서 다음 세 category를 선택해 개별/전체 규칙을 실행한다. 작은 box fixture는 완성된 robot asset이 아니므로 RobotRules는 의도적으로 여러 경고를 낸다. 실제 robot USD를 **복사한 파일**로 열면 아래 표를 체크하며 수정할 수 있다.

| 분류·규칙 | 확인할 데이터/수정 방향 |
|---|---|
| PhysicsJointHasDriveOrMimicAPI | fixed/excluded를 제외한 joint의 drive 또는 mimic; 두 API 공존 시 gain=0 |
| PhysicsJointMaxVelocity | PhysxJointAPI의 양수 max velocity |
| PhysicsDriveAndJointState | 유한 양수 max force, drive target과 joint state의 위치/속도 일치(허용차 1e-2) |
| DriveJointValueReasonable | stiffness 0~1,000,000, mimic gain=0, 지나친 자연진동수(500 Hz 경고) |
| JointHasCorrectTransformAndState | 양쪽 body joint frame, 회전/이동 joint의 state와 현재 pose 일치 |
| JointHasJointStateAPI | revolute angular, prismatic linear JointStateAPI; 제공되는 fix 제안 확인 |
| MimicAPICheck | reference 1개, gear/frequency/damping 값, gear 부호에 맞는 joint limits |
| RigidBodyHasMassAPI | mass, diagonal inertia, normalized principal axes |
| RigidBodyHasCollider | 활성 rigid body 계층에 collider가 존재하는지(instance proxy 포함) |
| NonAdjacentCollisionMeshesDoNotClash | 실제 physics로 non-adjacent body collider 중첩 탐지; 실행 환경 필요 |
| InvisibleCollisionMeshHasPurposeGuide | 숨긴 collider의 purpose=guide |
| HasArticulationRoot | stage에 ArticulationRootAPI 존재 |
| RobotNaming | 제조사/로봇/(버전)/로봇.usd 폴더와 파일 이름 규칙 |
| CleanFolder | 로봇 폴더의 예상 밖 파일 정리 |
| NoOverrides | open stage의 authored override 검토(/Render 제외) |
| RobotSchema | default prim의 RobotAPI와 robotLinks/robotJoints 관계 |
| JointsExist / LinksExist | JointAPI/LinkAPI가 실제 존재하는지 |
| ThumbnailExists | `.thumbs/256x256/<filename>.png` 존재 |
| CheckRobotRelationships | 관계 target과 prepend composition; 자동 fix 제안 검토 |
| VerifyRobotPhysicsAttributesSourceLayer | physics: 속성이 `_physics.usd`에 작성됐는지 |
| VerifyRobotPhysicsSchemaSourceLayer | Physics/Physx schema가 physics layer에 작성됐는지 |
| NoNestedMaterials | Material 아래 다른 Material 중첩 금지 |
| MaterialsOnTopLevelOnly | 재질이 최상위 Looks 아래에 있는지(reference/payload 내부 제외) |

위 앞 12개는 **IsaacSim.PhysicsRules**, 다음 RobotNaming부터 physics-layer schema까지는 **IsaacSim.RobotRules**, 마지막 2개는 **IsaacSim.SimReadyAssetRules**다. 수리 제안을 적용하기 전에 어느 layer가 편집 대상인지 확인하고 결과를 새 파일에 저장한다.

## API와 USD 이해

`ValidationEngine(init_rules=False)`는 명시적으로 고른 규칙만 실행한다. `enable_rule()`로 공식 rule class를 등록하고 `validate(stage).issues()`는 **현재 unsaved stage**까지 검사한다. JSON은 실제 issue 문자열을 보존한다. 원본의 권고 규칙과 물리 필수 조건은 심각도가 다르므로 issue 수만 세어 판단하지 않는다.

USD schema는 prim에 붙이는 기능 묶음이다. MassAPI/CollisionAPI/RigidBodyAPI는 다른 역할이다. visibility는 화면 표시, purpose는 geometry의 용도를 나타내며 invisible이라고 collision이 꺼지지 않는다. RobotAPI의 관계는 링크/관절 목록이고 default prim은 파일을 reference할 때 기본으로 가져올 루트다. physics layer 분리는 속성의 **출처 layer**를 검사하는 규칙이므로 값만 맞춰서는 통과하지 않는다.

문제 해결: validator 메뉴가 없으면 extension 활성화, 규칙이 안 보이면 IsaacSim category 필터를 확인한다. Physics 실행을 포함하는 규칙은 static 검사만으로 검증했다고 할 수 없다. 이 변경은 문법/CLI와 API 소스를 확인했지만 실제 validator/GUI/physics 실행은 미검증이다.

## 출처

[Isaac Sim 5.1 Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html), [PhysicsRules](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html#isaacsim-physicsrules), [RobotRules](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html#isaacsim-robotrules). checker/API 동작은 설치된 `isaacsim.asset.validation/physics_rules.py` 및 `omni.asset_validator.core`를 확인했다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
