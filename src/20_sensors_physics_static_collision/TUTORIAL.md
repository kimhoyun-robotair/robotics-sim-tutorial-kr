# 20. Physics API Editor로 static collider 일괄 편집

권장 학습 순서 **20** · 물리 기초와 Core API 확장 · 출처 ID `t161`

보이는 상자와 숨긴 상자를 포함한 로컬 subtree를 만들고 static collision의 적용 범위를 직접 비교합니다. 도구 이름은 Physics API Editor입니다.

## 이 실습의 의도

`/World/StaticSet` 아래의 보이는 Box0과 숨긴 Box1을 비교해, Physics API Editor가 **선택한 하위 prim과 visibility 조건에 따라** 충돌 속성을 어디에 적용하는지 확인합니다. 기본 스크립트는 충돌이 없는 두 시각 상자를 만들고 타임라인을 정지시킨 채 편집할 장면을 제공합니다. Apply/Remove 조작은 GUI에서 직접 수행하며, 움직이는 강체의 낙하나 접촉을 자동 검사하는 실행은 아닙니다.

## 실행 후 확인할 것

- Stage에는 `/World/StaticSet/Box0`과 `Box1`이 모두 존재하지만 viewport에는 Box0만 보여야 합니다. 처음에는 둘 다 VisualCuboid이므로 CollisionAPI가 없어야 하며, Box1이 안 보이는 것은 의도된 visibility 설정입니다.
- `/World/StaticSet`을 선택하고 **Apply to children=On, Visible only=On**으로 Apply Static한 뒤, Raw USD Properties에서 Box0에만 CollisionAPI가 추가됐는지 확인합니다. 상자가 움직이는지보다 어느 prim에 속성이 생겼는지가 기준입니다.
- 같은 선택에서 **Visible only=Off**로 다시 적용하면 숨긴 Box1도 CollisionAPI를 갖는지 봅니다. 충돌 시각화를 켜거나 Box1의 visibility를 복구해 적용 범위를 비교합니다.
- Remove Collision API 후에는 두 상자의 해당 API가 제거되었는지 확인합니다. `static_scene.usda`는 GUI 조작 전 출력이므로 편집 결과를 다시 확인하려면 **File > Save As**로 별도 저장해야 합니다. headless 실행으로 파일이 생긴 것만으로 이 수동 편집 단계를 완료한 것은 아닙니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/20_sensors_physics_static_collision
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다. GUI 실행에서 `--steps`를 생략하면 사용자가 창을 닫을 때까지 창을 유지합니다. 장면을 만든 뒤 타임라인은 정지하고, 화면과 도구를 위한 `app.update()`만 반복합니다. `--steps N`을 지정하면 이 앱 업데이트를 최대 N번 수행한 뒤 종료하며 N은 양수여야 합니다. `--headless`는 창 없이 실행하고, `--steps` 생략 시 240번 업데이트 후 종료합니다. 이전 명령과 호환되는 `--interactive`는 더 이상 필요하지 않으며 명시한 `--steps`의 종료 조건을 바꾸지 않습니다. `--headless`와 `--interactive`는 함께 쓰지 않습니다. run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다.

## 실습 순서와 관찰

1. 위 GUI 명령으로 실행해 `/World/StaticSet/Box0`, `Box1`을 확인합니다. Box1은 hidden이고 두 물체 모두 처음에는 visual geometry입니다.
2. **Window > Extensions**에서 `isaacsim.util.physics` 또는 설치 UI에서 표시되는 Physics API Editor 확장을 확인합니다. 5.1 문서에는 `isaacsim.utils.physics` 검색 이름이 쓰여 있으므로 목록의 실제 이름을 확인하세요.
3. **Tools > Physics API Editor**를 엽니다. `/World/StaticSet`을 선택하고 **Apply to children=On**, **Visible only=On**, Collision Type을 **Convex Hull**로 설정한 뒤 **Apply Static**을 누릅니다.
4. Box0의 CollisionAPI가 생기고 hidden Box1은 제외됐는지 Raw USD Properties에서 확인합니다. viewport 눈 아이콘 **Show By Type > Physics Mesh > All**로 collision geometry를 표시합니다. 설치 UI에서 Colliders로 보이면 해당 항목을 선택합니다.
5. 시각화를 끄고 동일 subtree에서 **Visible only=Off**로 Apply Static을 반복합니다. Box1을 보이게 했을 때도 collision이 적용됐는지 확인합니다.
6. 선택 subtree에서 **Remove Collision API**를 수행하고 두 상자의 collision 속성을 검사합니다. 이 실습 장면에서만 **Remove All Physics APIs**와의 차이를 비교합니다. 사용자 작업 장면에는 적용하지 않습니다.
7. **File > Save As**로 새 경로에 결과를 저장합니다. 코드가 내보낸 static_scene.usda는 GUI 수정 전 장면입니다.

## API와 USD 개념

Static collider는 움직이지 않는 환경의 충돌 형상입니다. VisualCuboid는 화면 geometry이고 Apply Static은 선택 범위에 CollisionAPI를 추가합니다. RigidBodyAPI를 붙여 동적으로 만드는 도구와 다르며 원문은 dynamic object를 지원하지 않는다고 명시합니다.

Apply to children은 USD subtree 탐색, Visible only는 prim의 visibility를 고려하는 필터입니다. 부모 Xform 자체는 geometry가 아닐 수 있으므로 children 옵션을 끄면 기대한 mesh에 API가 적용되지 않을 수 있습니다. Collision Type은 실제 mesh와 다른 근사 충돌 형상을 선택합니다.

## 확장 실습·성공 기준·문제 해결

숨긴 물체에 collision이 없으면 Visible only 설정을 먼저 확인합니다. Apply/Remove 중 실시간 collision 시각화를 켜면 subtree 순회와 함께 비용이 커질 수 있어 **적용 후** 켭니다. 한 변수 실험은 Visible only의 On/Off 비교이며 geometry·selection을 유지합니다. 성공 기준은 API가 붙은 prim의 실제 차이를 확인하는 것입니다. 파일 export만으로 GUI 도구를 검증한 것은 아닙니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Physics Static Collision Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/physics_static_collision.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·프레임 수 옵션·출력 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
