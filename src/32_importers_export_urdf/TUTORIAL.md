# 32. 보이는 형상과 충돌 형상을 URDF로 내보내기

## 이번에 배우는 것

**같은 USD 로봇에 붙인 작은 구를 세 조건으로 내보내고, URDF의 visual과 collision이 어떻게 달라지는지 비교합니다.**

화면에서 숨긴 물체도 충돌에는 사용할 수 있습니다. 반대로 보이는 장식이 반드시 접촉을 막아야 하는 것은 아닙니다. 이번에는 두 링크로 된 로봇에 실험용 구 하나를 붙여, visibility와 Collision API가 서로 다른 역할을 한다는 점을 변환 파일에서 확인합니다.

| 출력 폴더 | 실험 구의 표시 | 실험 구의 충돌 |
|---|---|---|
| `visual/` | 보임 | Collision API 없음 |
| `both/` | 보임 | Collision API 적용 |
| `collision/` | 숨김 | Collision API 유지 |

표의 조건은 **실험 구 하나**에 대한 것입니다. 두 링크의 기본 큐브에는 모든 조건에서 collider가 있습니다. `visual/`이라는 이름이 로봇 전체의 collision을 없앴다는 뜻은 아닙니다.

## 1. 같은 로봇을 세 번 내보내기

Isaac Sim 5.1과 지원 RTX GPU가 필요합니다. 로봇은 코드에서 생성하므로 외부 모델이 필요하지 않습니다. 실행기는 `isaacsim.asset.exporter.urdf`를 켜고, 확장에 포함된 `UsdToUrdf`를 사용합니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 설치 위치로 바꾸세요.

```bash
~/isaacsim/python.sh src/32_importers_export_urdf/run.py --steps 120 --output src/32_importers_export_urdf/output/export_a
```

`export_a`는 아직 없는 경로여야 합니다. 세 변환 결과를 먼저 저장한 뒤 앱 업데이트 120회 후 종료합니다. 물리 Play나 URDF 재import는 자동으로 수행하지 않습니다. `--steps`를 빼면 GUI가 계속 열려 있고, headless에서 생략하면 기본 120회입니다. `--frames`는 단계 수를 생략한 headless의 업데이트 한도를 정하는 기존 옵션입니다.

### 코드에서 볼 부분

`run.py`는 `/Robot/base`와 `/Robot/link`에 강체·질량·관성을 작성하고, Y축 회전 관절인 `/Robot/hinge`로 연결합니다. 두 링크의 질량은 각각 1 kg과 0.5 kg입니다. hinge의 body0·body1과 로컬 기준점이 변환할 링크 관계의 근거입니다.

실험 구는 link 아래에 놓입니다.

```python
sphere = UsdGeom.Sphere.Define(stage, '/Robot/link/experiment_sphere')
sphere.CreateRadiusAttr(0.03)
sphere.AddTranslateOp().Set(Gf.Vec3d(0.13, 0, 0))
```

구의 반지름은 3 cm, 위치는 링크 기준 x=13 cm입니다. 작은 구를 링크 옆에 따로 두었기 때문에 기본 큐브와 구의 변환 결과를 구별할 수 있습니다.

각 조건을 설정한 뒤 다음 호출로 로봇만 내보냅니다.

```python
UsdToUrdf(stage, root='/Robot').save_to_file(
    str(target), mesh_dir='meshes', mesh_path_prefix='./', use_uri_file_prefix=False,
)
```

`root='/Robot'`은 변환 범위를 지정합니다. `mesh_path_prefix='./'`는 URDF 주변의 파일을 상대경로로 찾게 하므로, 필요한 mesh가 생성되면 URDF와 함께 옮겨야 합니다.

### 실행 결과 확인하기

| 출력 | 읽을 부분 |
|---|---|
| `visual/source.usda`, `both/source.usda`, `collision/source.usda` | 각 변환 직전의 구 API와 visibility |
| 각 폴더의 `robot.urdf` | 링크·관절 관계, visual·collision의 geometry |
| 필요에 따라 생성되는 `meshes/` | URDF가 참조하는 형상 파일 |
| 최상위 `counts.json` | 각 URDF에서 실제로 센 link·joint·visual·collision 요소 수 |

실행 창에는 마지막 collision 조건이 남습니다. 구가 보이지 않는 것은 그 조건에서 설정한 visibility 때문일 수 있습니다. 앞의 두 조건은 저장된 `source.usda`를 열어 확인하세요.

## 2. 내보낸 URDF를 다시 열어 비교하기

XML 요소 수만 비교하면 형상 보존을 놓칠 수 있습니다. exporter가 여러 형상을 합쳐 표현할 수 있어 `visual` 요소 하나가 구 하나와 반드시 대응하지는 않기 때문입니다.

1. Isaac Sim의 새 장면에서 `isaacsim.asset.importer.urdf`를 활성화하세요.
2. **File > Import**로 `export_a/visual/robot.urdf`를 가져옵니다. 재import 출력은 별도 새 폴더로 정하세요.
3. 링크 옆의 작은 구가 화면에 보이는지 확인하고, **Show by type > Physics > Colliders > All**로 충돌 윤곽을 확인하세요.
4. 새 장면에서 both와 collision 파일도 같은 조건으로 가져와 비교하세요. 세 모델을 겹쳐 놓으면 어떤 구를 보고 있는지 구분하기 어렵습니다.

### 코드에서 볼 부분

세 조건을 만드는 반복문은 Collision API를 추가한 뒤 마지막 조건에서 표시만 숨깁니다.

```python
if mode != 'visual':
    UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
sphere.CreateVisibilityAttr(UsdGeom.Tokens.invisible if mode == 'collision' else UsdGeom.Tokens.inherited)
```

both에서 적용한 Collision API는 collision에서도 남아 있습니다. visibility를 invisible로 바꾸는 것이 물리 형상을 제거하는 일과 다르다는 것을 이 순서에서 볼 수 있습니다.

### 실행 결과 확인하기

세 URDF에서 base와 link의 연결, hinge의 Y축, 구의 링크 기준 위치를 비교하세요. visual에서는 구가 표시 쪽에, both에서는 표시와 충돌 양쪽에, collision에서는 충돌 쪽에 보존되는지 확인합니다. exporter와 importer가 형상을 어떤 XML 구조로 표현했는지도 함께 보세요.

`counts.json`은 XML을 실제로 파싱해 요소 수를 기록하지만, 이 재import 화면 검사나 동역학 검증까지 수행하지는 않습니다. 가만히 있는 USD 생성 장면만 보고 관절 구동을 확인했다고 결론 내리지 마세요.

### 공식 Franka에서도 같은 조건 만들기

작은 두 링크 모델과 비교하려면 별도 GUI에서 공식 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 엽니다. 이 선택 실습만 공식 Franka와 종속 mesh 접근이 필요합니다.

1. **Window > Extensions**에서 `isaacsim.asset.exporter.urdf`를 켭니다.
2. **File > URDF Exporter**를 엽니다. 설치된 5.1 확장의 메뉴 이름이며 공식 문서에서는 **Export to URDF**로 안내하기도 합니다.
3. Root Prim Path는 Stage에서 확인한 Franka root, Mesh Folder Name은 `meshes`, Mesh Path Prefix는 `./`로 지정하고 새 폴더에 `franka.urdf`를 내보냅니다. **Visualize Collisions는 끕니다.**
4. `panda_hand`를 찾아 그 아래에 **Create > Mesh > Sphere**로 구를 추가하고 Scale을 `(0.3, 0.3, 0.3)`으로 설정합니다. 세 축을 같은 비율로 유지하세요. 링크 기준 위치와 실제 크기도 확인합니다.
5. 구에 Collider가 없는 상태, **+ Add > Physics > Colliders Preset**을 적용한 상태, Collider를 유지하고 visibility만 숨긴 상태를 각각 다른 출력 폴더에 내보냅니다.
6. 각 결과를 새 장면으로 다시 가져와 손 위의 구가 표시·충돌 형상 중 어디에 남았는지 비교합니다. 원본 Franka USD를 저장할 필요는 없습니다.

GUI의 **Visualize Collisions**를 켜면 숨긴 collider도 표시 형상으로 포함할 수 있어 이번 visibility 실험의 조건이 달라집니다. 또 Mesh Path Prefix의 기본값은 `file://`이므로 위에서 `./`를 명시해 코드 실행과 맞춥니다. `package://`를 선택할 때는 Package Name과 실제 ROS 패키지의 mesh 위치까지 함께 구성해야 합니다. 경로 종류를 바꾸는 것은 mesh 파일을 자동 배포하는 작업이 아닙니다.

## 3. 표시와 충돌의 변환 정리

```text
USD visibility ───────────────→ 표시 형상 판단
USD Collision API ────────────→ 충돌 형상 판단
USD body·joint·mass·inertia ───→ 로봇 링크와 관절 구조
                         ↓
                URDF + 필요한 geometry 파일
```

내보내기는 파일 확장자만 바꾸는 작업이 아닙니다. USD에서 표현한 정보를 URDF 구조로 옮기는 과정입니다. 따라서 결과 XML의 존재, 구조의 연결, 형상의 표시·충돌 보존을 각각 확인해야 합니다.

이 exporter는 관절이 트리로 연결된 로봇을 대상으로 합니다. 닫힌 고리를 그대로 내보내거나 임의의 USD 기능을 모두 옮길 수는 없습니다. 연결의 Body0/Body1과 양쪽 joint 기준점이 맞아야 하며, sphere는 세 축 scale이 같고 cylinder는 반지름 방향 두 축 scale이 같아야 합니다. 변환 오류가 생기면 파일 경로에 앞서 해당 geometry와 관절 구조가 지원되는 표현인지 살펴보세요.

## 4. 간단한 확인 실험

생성된 `both/source.usda`를 별도 GUI에서 열고 `/Robot/link/experiment_sphere`의 **visibility만** invisible로 바꿔 보세요. Collision API와 크기·위치는 그대로 둡니다.

`isaacsim.asset.exporter.urdf`를 활성화하고 **File > URDF Exporter**에서 Root Prim Path를 `/Robot`, Mesh Path Prefix를 `./`, Visualize Collisions를 끈 상태로 맞춰 새 경로에 내보내세요. 원래 both 결과와 비교하면 구의 표시 쪽만 달라지고 충돌 형상은 유지되는 것이 기대 결과입니다. 앞에서 자동 생성한 collision 결과와도 대조할 수 있습니다.

## 실행할 때 막히면

- **URDF 내보내기 메뉴가 없음**: Extensions에서 `isaacsim.asset.exporter.urdf`를 활성화하고 File의 **URDF Exporter**를 찾으세요. 공식 문서의 Export to URDF와 이름이 다를 수 있습니다.
- **URDF는 열리지만 mesh가 없음**: XML의 mesh 경로와 `meshes/` 위치를 확인하세요. 상대경로 파일은 함께 보관해야 합니다.
- **visual 폴더에도 collision 요소가 있음**: 조건은 실험 구에만 적용했습니다. 기본 두 큐브는 계속 collider를 가집니다.
- **세 조건의 요소 수 차이가 예상과 다름**: 형상이 합쳐졌는지 XML geometry와 재import 결과를 확인하세요. 요소 수를 shape 수와 같다고 가정하지 마세요.
- **exporter가 링크 구조를 거부함**: 임의 장면을 추가했다면 로봇 루트, body0·body1, 관절 기준점을 확인하세요. USD의 모든 장면 기능이 URDF로 그대로 옮겨지는 것은 아닙니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial: Export URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/export_urdf.html)에 대응합니다. 원문의 표시·충돌 실험을 외부 에셋 없이 생성하는 두 링크 로봇으로 구성하고, 공식 Franka의 GUI export도 선택적으로 비교합니다. 더 자세한 표현 제약은 공식 페이지에서 확인할 수 있습니다.

`tutorial.json`은 `not_run`입니다. 세 조건과 파일 구조는 코드에 따른 확인 기준입니다. exporter 실행, URDF 재import, GUI 형상 보존은 아직 검증하지 않았습니다.
