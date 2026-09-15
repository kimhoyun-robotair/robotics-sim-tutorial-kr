# 50. 잘못된 USD 속성은 어떻게 찾아 고칠까?

## 이번에 배우는 것

**일부러 결함을 넣은 작은 강체를 검사하고, 같은 규칙으로 수정 전후를 비교합니다.**

USD 파일이 열리고 장면이 표시된다고 물리 속성까지 올바른 것은 아닙니다. 질량이나 관성을 잘못 작성했거나 숨긴 충돌 형상의 용도가 맞지 않을 수 있습니다. 이번 실습에서는 눈으로 발견하기 어려운 속성을 Asset Validator로 찾아봅니다.

| 요소 | 이번 실습에서 맡은 역할 |
|---|---|
| `/World/DefectiveBody` | 검사할 한 변 0.1인 cube |
| `RigidBodyAPI`, `CollisionAPI` | 강체와 충돌체 기능 부여 |
| `MassAPI` | 질량, 대각 관성, 관성 주축 정보 |
| `RigidBodyHasMassAPI` | 질량·관성 정보 검사 |
| `InvisibleCollisionMeshHasPurposeGuide` | 숨긴 collider의 purpose 검사 |

검사 대상은 코드가 만든 작은 stage입니다. 다른 로봇이나 외부 자산을 준비할 필요가 없습니다.

## 1. 결함 검사와 수정을 한 번에 실행하기

Isaac Sim 5.1이 설치된 환경에서 **저장소 루트**를 기준으로 실행하세요. 설치 경로가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/50_importers_asset_validation/run.py \
  --headless --steps 5 \
  --output src/50_importers_asset_validation/output/repaired
```

검사와 수정은 앱 업데이트 반복문에 들어가기 전에 끝납니다. 여기서 `--steps 5`는 검사 횟수나 물리 계산 횟수가 아니라 **검사 후 앱 업데이트 횟수**입니다. `--headless`를 빼면 창을 볼 수 있고, GUI에서 `--steps`도 생략하면 결과 장면을 계속 열어 둡니다. 기존 출력 폴더는 덮어쓰지 않습니다.

### 코드에서 볼 부분

처음에는 다음과 같은 값을 작성합니다.

```python
mass.CreateMassAttr(0.0)
mass.CreateDiagonalInertiaAttr(Gf.Vec3f(0, 0, 0))
mass.CreatePrincipalAxesAttr(Gf.Quatf(2.0))
cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
```

`Gf.Quatf(2.0)`은 스칼라 성분이 2인 quaternion입니다. 크기가 1로 정규화되지 않았으므로 관성 주축의 회전 정보로 적합하지 않습니다. cube는 숨겨 두지만 CollisionAPI는 그대로 있습니다. **화면에 안 보이는 것과 충돌이 꺼진 것은 다른 설정**입니다.

검사기는 필요한 두 규칙만 켭니다.

```python
engine = ValidationEngine(init_rules=False)
engine.enable_rule(RigidBodyHasMassAPI)
engine.enable_rule(InvisibleCollisionMeshHasPurposeGuide)
before = [str(issue) for issue in engine.validate(stage).issues()]
```

`init_rules=False`가 빠진 전체 검사와 결과 수를 바로 비교하면 안 됩니다. 이 실행의 질문은 “이 두 규칙이 지적한 속성을 제대로 고쳤는가?”입니다. 검사 대상은 메모리에 열린 stage이므로 파일을 저장하기 전 수정도 반영됩니다.

### 실행 결과 확인하기

이 튜토리얼 폴더의 `output/repaired`에서 다음 파일을 열어 보세요.

| 파일 | 확인할 내용 |
|---|---|
| `before.usda` | 결함이 있는 원래 속성 |
| `after.usda` | 질량 1, 대각 관성 각 1/600, 단위 quaternion, purpose `guide` |
| `validation.json` | `enabled_rules`, 수정 전 `before`, 수정 후 `after` issue 목록 |

정상적으로 끝났다면 `before`에는 실제 issue 문자열이 있고 `after`는 빈 배열입니다. 코드도 결함을 하나도 찾지 못하거나 수정 후 issue가 남으면 오류를 냅니다. JSON의 문자열을 읽으며 어느 속성이 어떤 지적과 연결되는지 확인하세요.

수정 뒤에도 visibility는 `invisible`입니다. 화면에 cube가 나타나는 것을 수정 성공 조건으로 삼지 않습니다. 또한 이 코드는 stage의 길이 단위를 명시적으로 작성하지 않으므로 단위를 다른 자산과 합칠 때는 stage 설정을 확인해야 합니다. 관성 값은 아래의 m·kg 가정으로 정한 실습 값입니다.

## 2. GUI에서 한 속성씩 고쳐 보기

이번에는 자동 수리를 생략한 장면을 여세요.

```bash
~/isaacsim/python.sh src/50_importers_asset_validation/run.py \
  --keep-defects --output src/50_importers_asset_validation/output/manual
```

1. **Window > Asset Validator**를 열고 위 표의 두 규칙을 선택하세요. 규칙이 보이지 않으면 IsaacSim category를 확인합니다.
2. Stage에서 `/World/DefectiveBody`를 선택하고 Property에서 질량, 대각 관성, 주축 quaternion을 찾으세요.
3. 먼저 검사를 실행해 issue와 속성을 대조합니다. 다른 규칙도 켜져 있으면 자동 실행과 보고 내용이 달라집니다.
4. 속성을 수정할 때마다 다시 검사하세요. 주축만 고친 상태에서는 질량·관성·purpose 관련 지적이 여전히 남을 수 있습니다.
5. 수정을 끝낸 stage는 **Save As**로 이 튜토리얼 폴더의 `output/manual/manually_repaired.usda`에 저장하세요. 저장 대화상자에는 절대 경로를 지정합니다.

### 설정에서 볼 부분

한 변이 0.1 m이고 질량이 1 kg인 균일한 정육면체의 중심 관성은 다음과 같습니다.

```text
Ixx = m × (y² + z²) / 12
    = 1 × (0.1² + 0.1²) / 12
    = 1/600 kg·m²
```

정육면체이므로 `Iyy`, `Izz`도 같습니다. 임의의 양수를 넣어 규칙을 통과시키는 것보다 **형상과 질량에 맞는 값인지 설명할 수 있어야** 합니다. 관성 주축은 identity quaternion `(1, 0, 0, 0)`, 숨긴 collider의 purpose는 `guide`로 둡니다.

`--keep-defects`에서는 `before.usda`와 `validation.json`만 자동 생성합니다. JSON에 `after`가 없는 것은 빈 배열과 다릅니다. 전자는 **수정 후 검사를 실행하지 않음**, 후자는 **실행했지만 issue가 없음**을 뜻합니다. GUI에서 수정해도 이 JSON을 스크립트가 자동 갱신하지는 않습니다.

## 3. 검사 결과를 해석하는 순서 정리

```text
어떤 규칙을 켰는가?
    → 어느 prim의 어떤 속성이 지적됐는가?
    → 수정값이 물리적으로 타당한가?
    → 같은 규칙을 다시 실행했는가?
```

두 규칙의 issue가 사라져도 이 stage가 완성된 로봇이 되는 것은 아닙니다. 예를 들어 로봇 링크 관계, 관절 drive, 물리 속성을 작성한 layer는 이번 두 규칙에서 다루지 않습니다. 실제 로봇을 검사할 때는 해당 목적에 맞는 규칙을 추가해야 합니다. [공식 Asset Validation 규칙 목록](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)에서 검사 대상을 확인할 수 있습니다.

**issue 수는 수정 범위를 알려주는 단서입니다.** 파일 열기, 선택 규칙 통과, 물리 재생 중 안정성은 각각 다른 확인 과정입니다.

## 4. 간단한 확인 실험

2절의 결함 장면에서 **principal axes의 스칼라 성분만 2에서 1로** 바꾸세요. 나머지 값과 활성 규칙은 유지하고 다시 검사합니다.

quaternion 관련 지적이 어떻게 바뀌는지 읽어 보세요. 다른 issue가 남아 있는 이유도 각 속성과 연결해 설명해 보세요. 그 뒤 자동 수리 결과와 비교하면 한 속성 수정과 전체 수리의 차이가 드러납니다.

## 실행할 때 막히면

- **장면이 비어 보임**: 검사 입력을 의도적으로 숨겼습니다. Stage에서 `DefectiveBody`를 선택해 속성을 확인하세요.
- **`after.usda`가 없음**: `--keep-defects`를 사용했는지 확인하세요. 기본 실행이라면 콘솔의 검사 오류를 먼저 읽습니다.
- **GUI와 JSON의 issue 수가 다름**: 동일한 두 규칙, 동일한 수정 상태를 검사했는지 확인하세요.
- **기존 출력 경로 오류**: 비교할 결과를 남기고 `--output`에 새 경로를 지정하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)에 대응합니다. 실제 공식 규칙을 작은 결함 stage에 적용하고 수리 전후를 기록하는 실습입니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 headless 기본 실행에서 issue가 **4개에서 0개**로 바뀐 관찰이 있습니다. 해당 두 규칙을 수리한 과거 실행의 기록이며, 현재 코드 재실행이나 GUI 편집·전체 로봇 검사의 결과는 아닙니다. 이 실습에서는 활성 규칙과 실제 `before`·`after` 목록을 함께 확인하세요.
