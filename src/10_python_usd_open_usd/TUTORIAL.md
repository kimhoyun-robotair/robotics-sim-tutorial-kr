# 10. USD의 계층과 레이어는 어떻게 최종 장면을 만들까요?

## 이번에 배우는 것

**구 하나의 위치·재질·반지름을 여러 곳에 작성하며, 합성해서 읽는 값과 파일에 저장되는 값을 구분합니다.**

USD 장면은 객체를 한 파일에 나열하는 것보다 더 많은 일을 합니다. 부모의 변환을 자식에게 적용하고, 여러 레이어에 작성한 속성을 합쳐 최종 값을 결정합니다. 이 실습은 `/hello/world`의 구를 사용해 그 과정을 숫자로 확인합니다.

| 대상 | 역할 | 기본 실행에서 확인할 값 |
|---|---|---|
| `/hello` | 구의 부모 Xform이며 defaultPrim입니다. | 로컬 이동 `(0, 0, 1)` m |
| `/hello/world` | 구 Prim입니다. | 로컬 이동 `(1, 0, 0)` m |
| `hello.usda` | 기본 모양·변환·재질을 저장하는 루트 레이어입니다. | 반지름 0.5 m |
| `details.usda` | 별도 속성을 작성한 서브레이어입니다. | `tutorial:label` 문자열 |
| session layer | 현재 Stage에서만 반지름을 덮어씁니다. | 반지름 1.0 m |
| `inspection.json` | 위치·반지름·순회·변환 검사 결과입니다. | 합성 결과와 저장 결과 비교 |

이 장면은 물리 낙하 실습이 아닙니다. 강체나 지면을 만들지 않고 USD 데이터와 변환을 관찰합니다.

## 1. 장면을 만들고 위치·반지름 읽기

Isaac Sim 5.1과 지원 GPU·드라이버를 준비하세요. 기본 재질은 코드로 만들므로 외부 텍스처가 필요하지 않습니다. 저장소 루트에서 실행합니다.

```bash
~/isaacsim/python.sh src/10_python_usd_open_usd/run.py --steps 120 --radius 0.5
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 파일을 만든 뒤 앱을 120번 업데이트하고 종료합니다. 여기서 `--steps`는 물리 단계 수가 아닙니다. 창을 계속 열어 두려면 `--steps 120`을 빼세요. `--headless`를 추가하면 창 없이 실행하고, 이때 생략한 횟수는 120입니다.

### 코드에서 볼 부분

```python
parent = UsdGeom.Xform.Define(stage, "/hello")
stage.SetDefaultPrim(parent.GetPrim())
sphere = UsdGeom.Sphere.Define(stage, "/hello/world")
sphere.CreateRadiusAttr(args.radius)
parent.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
sphere.AddTranslateOp().Set(Gf.Vec3d(1, 0, 0))
```

`Xform`은 자식을 묶고 변환하는 Prim입니다. 부모를 z 방향으로 1 m, 구를 부모 기준 x 방향으로 1 m 옮겼으므로 구의 월드 위치는 `(1, 0, 1)`입니다. 이 예제에는 부모 회전이 없어서 두 이동을 더하면 되지만, 회전·스케일이 있으면 변환 행렬을 함께 합성해야 합니다.

코드는 `UsdGeom.XformCache().GetLocalToWorldTransform()`으로 부모까지 포함한 변환을 계산하고, `ExtractTranslation()`으로 월드 위치를 읽습니다. 구의 로컬 Translate 값 하나만 읽는 것과 구분하세요.

재질은 `/hello/Looks/Red`의 Material과 그 아래 Shader로 구성합니다.

```python
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))
mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(mat)
```

Shader는 표면 색을 계산하고 Material은 그 출력을 연결합니다. 마지막 바인딩이 구와 Material을 연결해야 구에 이 재질이 적용됩니다. 빨간 RGB 값을 작성한 것과 구에 재질을 지정한 것은 별개의 단계입니다.

### 실행 결과 확인하기

이 폴더의 `output/날짜-시간/`에서 `hello.usda`, `details.usda`, `inspection.json`을 확인하세요. `.usda`는 USD를 텍스트로 읽을 수 있는 형식입니다.

| JSON 항목 | 기본 기대값 | 해석 |
|---|---|---|
| `world_position` | `[1, 0, 1]` | 부모와 자식의 이동을 합성했습니다. |
| `session_radius` | `1.0` | 현재 Stage의 session 변경을 포함합니다. |
| `saved_radius` | `0.5` | 별도 session으로 다시 열어 읽은 값입니다. |
| `transform_max_error` | `1e-6` 이하 | 뒤에서 살펴볼 행렬 변환 비교 오차입니다. |

프로그램이 화면에 여는 파일은 저장된 `hello.usda`입니다. session에서 두 배로 바꿨다는 이유만으로 GUI에서도 반드시 반지름 1.0을 기대하지 마세요. 임시 합성과 저장 파일의 차이는 JSON의 두 반지름으로 확인합니다.

## 2. 레이어에 쓴 값과 저장 범위 따라가기

### 코드에서 볼 부분: 서브레이어와 session

```python
layer = Sdf.Layer.CreateNew(str(output / "details.usda"))
stage.GetRootLayer().subLayerPaths.append("details.usda")
with Usd.EditContext(stage, layer):
    sphere.GetPrim().CreateAttribute(
        "tutorial:label", Sdf.ValueTypeNames.String
    ).Set("layer-authored")
```

`subLayerPaths`는 루트 레이어에 함께 합성할 레이어를 연결합니다. `Usd.EditContext` 안에서는 속성 변경이 `details.usda`에 기록됩니다. 따라서 `hello.usda`에서 그 문자열을 찾지 못해도 합성된 Stage에서는 읽을 수 있습니다. 두 파일을 옮길 때 상대 경로 관계를 유지해야 합니다.

반지름 변경은 다른 편집 대상으로 보냅니다.

```python
with Usd.EditContext(stage, stage.GetSessionLayer()):
    sphere.GetRadiusAttr().Set(args.radius * 2)
session_radius = sphere.GetRadiusAttr().Get()
stage.GetRootLayer().Save()
reopened = Usd.Stage.Open(stage.GetRootLayer(), Sdf.Layer.CreateAnonymous())
```

session layer의 반지름이 현재 Stage에서는 더 강한 값으로 적용됩니다. 하지만 `GetRootLayer().Save()`는 **루트 레이어를 저장**합니다. session의 변경까지 자동으로 옮겨 저장하지 않습니다. 새 익명 session으로 다시 열면 원래 반지름을 읽게 됩니다.

이처럼 레이어에 작성한 속성 값을 USD에서는 **의견(opinion)**이라고 부릅니다. 코드가 읽는 최종 값은 여러 의견을 합성한 결과일 수 있습니다.

### 코드에서 볼 부분: 순회와 행렬 분해

`stage.Traverse()`는 Stage의 전체 Prim을 순회하고, `Usd.PrimRange(stage.GetDefaultPrim())`는 `/hello` 아래만 순회합니다. defaultPrim은 파일을 대표하는 루트이지 모든 Prim을 자동으로 포함하는 가상 폴더가 아닙니다.

별도의 `/hello/MatrixExample`에는 이동 `(2, 3, 4)`, Z축 30도 회전, 균일 스케일 2를 하나의 행렬로 작성합니다. 그 행렬을 다시 이동·회전·스케일 연산으로 나눈 뒤 비교합니다.

```python
before = prim.GetLocalTransformation()
decomposed = Gf.Transform(before)
prim.ClearXformOpOrder()
prim.AddTranslateOp().Set(decomposed.GetTranslation())
prim.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(decomposed.GetRotation().GetQuat())
prim.AddScaleOp().Set(Gf.Vec3f(*decomposed.GetScale()))
```

`ClearXformOpOrder()`는 기존 행렬 연산이 새 연산과 중복 적용되지 않도록 활성 변환 순서를 비웁니다. 이후 행렬 원소 차이의 최댓값을 계산해 `1e-6`보다 크면 오류를 냅니다. 이 검사는 제공된 **양의 균일 스케일과 회전·이동**에 대한 것으로, 기울임(shear)이나 음수 스케일 전반을 검증하지 않습니다.

### 실행 결과 확인하기

`inspection.json`의 `traversal`에는 `/Light`가 있지만 `default_prim_subtree`에는 없어야 합니다. `/Light`는 `/hello`의 자식이 아니기 때문입니다. `property_names`에는 직접 작성한 속성뿐 아니라 Sphere 스키마가 제공하는 속성 이름도 포함될 수 있습니다.

재질을 더 비교하고 싶다면 저장한 `hello.usda`를 GUI에서 열고 Script Editor에서 다음을 실행할 수 있습니다. 이 선택 실습은 NVIDIA 기본 MDL 라이브러리가 필요합니다.

```python
import omni.kit.commands
import omni.usd
from pxr import Gf, Sdf, UsdShade
created = []
omni.kit.commands.execute(
    "CreateAndBindMdlMaterialFromLibrary", mdl_name="OmniPBR.mdl",
    mtl_name="OmniPBR", mtl_created_list=created)
stage = omni.usd.get_context().get_stage()
material = stage.GetPrimAtPath(created[0])
omni.usd.create_material_input(
    material, "diffuse_color_constant", Gf.Vec3f(0, 0, 1), Sdf.ValueTypeNames.Color3f)
UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/hello/world")).Bind(UsdShade.Material(material))
```

파란 OmniPBR로 재질 연결이 바뀌는지 Property에서 확인하세요. `OmniSurface.mdl`과 `OmniSurface`를 사용한 비교도 가능하지만, 입력 이름은 재질마다 다르므로 같은 색상 입력을 그대로 가정하면 안 됩니다.

## 3. 계층과 레이어 합성 정리

```text
부모 변환 + 자식 로컬 변환 → 구의 월드 위치
hello.usda + details.usda + session 의견 → 현재 Stage에서 읽는 값
루트 레이어 저장 + 새 session으로 다시 열기 → 저장된 반지름
```

계층은 **어느 부모 아래에 있는가**, 레이어는 **어느 파일에 값을 작성했는가**에 관한 구조입니다. 둘을 구분하면 같은 구의 위치는 부모 때문에 바뀌고 반지름은 session 의견 때문에 바뀐다는 사실을 설명할 수 있습니다. 이 장면은 `metersPerUnit=1.0`, Z-up을 명시합니다.

## 4. 간단한 확인 실험

반지름만 0.5에서 0.25로 줄여 실행하세요.

```bash
~/isaacsim/python.sh src/10_python_usd_open_usd/run.py --steps 120 --radius 0.25
```

`session_radius`는 0.5, `saved_radius`는 0.25로 예상합니다. `world_position`은 여전히 `[1, 0, 1]`입니다. 구 크기의 변경과 중심 위치의 변경이 독립적인지 확인하고, 원래 실행의 두 반지름과 비교하세요.

## 실행할 때 막히면

- **파일을 옮긴 뒤 `tutorial:label`이 사라짐**: `details.usda`가 `hello.usda` 옆에 있고 서브레이어 상대 경로가 해결되는지 확인하세요.
- **재개방 후 두 배 반지름이 사라짐**: session에만 작성한 값이라 예상된 결과입니다. `saved_radius`를 읽으세요.
- **구가 떨어지지 않음**: 물리 강체를 만들지 않은 USD 편집 실습입니다. `--steps`를 늘려도 낙하가 추가되지 않습니다.
- **MDL 코드에서 재질 생성에 실패함**: 기본 실행의 UsdPreviewSurface와 달리 MDL 비교에는 설치의 재질 라이브러리가 필요합니다. 생성 명령 결과와 라이브러리를 확인하세요.
- **반지름 입력 오류**: `--radius`는 0보다 크고 10보다 작은 값을 사용합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html)에 대응합니다. 원문의 속성·재질·변환·레이어를 구 하나와 검사 보고서로 연결했습니다. 기본 실행은 외부 MDL 대신 UsdPreviewSurface를 사용하고 MDL은 선택 실습으로 남겼습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 이전 코드에서 Headless 2회 앱 업데이트로 기본 반지름의 session·저장 차이와 행렬 오차를 확인한 기록입니다. 현재 파일의 실행 결과는 위 표의 기준으로 다시 확인하세요. `tutorial.json`의 부분 실행 검증은 GUI·MDL·다른 반지름 조건까지 포함하지 않습니다.
