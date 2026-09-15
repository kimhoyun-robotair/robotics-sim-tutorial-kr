# 16. 장면의 물체를 만들고 접촉·형상 데이터 읽기

## 이번에 배우는 것

**세 쌍의 큐브와 작은 사면체를 만들고, 화면의 배치를 위치·접촉력·장면 질의 결과와 연결합니다.**

장면에 물체를 추가한 뒤에는 “잘 보인다” 외에도 확인할 것이 있습니다. 여러 물체의 위치를 한 번에 읽거나, 특정 물체와의 접촉만 골라 보거나, 한 방향으로 어떤 물체가 있는지 질의할 수 있습니다. 이번에는 이런 작업을 하나의 작은 장면에서 이어서 수행합니다.

| 장면 구성 | 살펴볼 내용 |
|---|---|
| 빨간 `Bottom_0`~`Bottom_2` | 세 물체를 하나의 `RigidPrim`으로 묶어 상태 읽기 |
| 파란 `Top_0`~`Top_2` | 아래 큐브 위로 낙하한 뒤 접촉력 비교 |
| 초록 `/World/Mesh` | 직접 만든 사면체의 충돌·질량·시각 재질 |
| `/World/AlignedMarker` | 사면체의 초기 변환을 복사한 좌표 요소 |
| `convert.py`, `tetrahedron.obj` | 별도 파일의 메시를 USD로 변환 |

`RigidPrim`의 묶음은 여러 물체를 같은 배열로 다루는 **뷰(view)**입니다. 큐브 세 개를 하나의 큰 강체로 합치는 것은 아닙니다.

## 1. 먼저 장면을 실행하고 최종 상태 읽기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/16_python_usd_environment_setup/run.py --mass 1 --steps 240
```

한 변 0.5 m인 위 큐브가 아래 큐브 위로 떨어집니다. 물리 간격은 1/60초이므로 240단계는 시뮬레이션 시간 4초입니다. 결과를 저장한 뒤 앱이 종료됩니다.

`--steps 240`을 빼면 첫 240단계 뒤 결과를 한 번 저장하고 창을 닫을 때까지 물리를 계속 진행합니다. 이후 변화는 보고서에 추가하지 않습니다. `--headless`를 추가하면 창 없이 실행하며, 단계 수를 생략해도 240단계 후 종료합니다.

기본 출력은 이 폴더의 `output/날짜-시간/`입니다. 직접 `--output`을 지정할 때는 새 폴더를 사용하세요.

### 코드에서 볼 부분

아래 큐브의 뷰를 만들면서 접촉 기록도 준비합니다.

```python
RigidPrim(
    "/World/Bottom_[0-2]",
    name="bottom_view",
    track_contact_forces=True,
    contact_filter_prim_paths_expr=["/World/Top_.*"],
    max_contact_count=60,
)
```

`Bottom_[0-2]`는 이름 끝이 0, 1, 2인 큐브와 대응합니다. `[0-2]`는 한 자리 문자 범위이며, 이런 표기를 임의의 정수 범위로 읽으면 안 됩니다.

`track_contact_forces`는 아래 큐브들의 접촉력 기록을 켜고, 필터는 그중 `Top_` 물체와의 접촉을 구분하도록 합니다. 뷰를 `world.scene.add()`에 등록하고 `world.reset()`한 뒤 상태를 읽습니다. 초기화 전에 물리 상태를 요청하는 순서로 바꾸지 마세요.

### 실행 결과 확인하기

`scene_queries.json`의 물리 데이터는 시간 이력 대신 **실험 종료 시점의 상태 한 묶음**으로 저장됩니다. 같은 파일의 초기 사면체 측정값은 2절에서 별도로 읽습니다.

| 항목 | 읽는 방법 |
|---|---|
| `bottom_positions`, `top_positions` | 각각 세 큐브의 월드 위치 `[x, y, z]`, m |
| `net_contact_forces_N` | 아래 큐브가 받는 전체 접촉의 합력 `[Fx, Fy, Fz]` |
| `top_bottom_contact_matrix_N` | 아래 큐브와 Top 필터 사이의 접촉력 |
| `raycast` | 아래 방향 광선의 충돌 여부·거리·강체 경로 |
| `overlap_bodies` | 지정한 공간 상자와 겹치는 강체 경로 목록 |

정착한 쌓기 상태라면 아래 큐브 중심은 약 0.25 m, 위 큐브 중심은 약 0.75 m 부근을 기대할 수 있습니다. 접촉 중 흔들리거나 배치가 바뀌었다면 화면과 실제 위치부터 함께 확인하세요.

**아래 큐브의 전체 접촉력은 바닥이 미는 힘만을 뜻하지 않습니다.** 바닥이 위로 미는 힘과 위 큐브가 아래로 누르는 힘이 함께 들어갑니다. 필터 결과는 그중 Top과의 접촉만 담으므로 축과 부호를 읽어야 합니다.

## 2. 접촉 배열과 사면체 구성 따라가기

### 코드에서 볼 부분

접촉을 읽을 때 물리 간격을 전달합니다.

```python
contact = bottoms.get_contact_force_data(dt=1 / 60)
friction = bottoms.get_friction_data(dt=1 / 60)
```

접촉의 내부 임펄스를 힘으로 환산하려면 시간 간격이 필요합니다. 여기서는 실제 물리 간격인 1/60초를 사용하므로 보고서의 힘은 N으로 해석합니다.

`contact_data`에는 법선 힘, 접촉점, 법선, 분리거리, 쌍별 접촉 개수, 시작 인덱스가 순서대로 들어갑니다. `friction_data`에는 접선 힘, 점, 개수, 시작 인덱스가 들어갑니다. 먼저 어떤 쌍의 시작 인덱스가 `s`, 개수가 `n`인지 읽고 해당 배열의 `s`부터 `s+n` 직전까지만 확인하세요. 미리 확보한 버퍼의 모든 행이 실제 접촉은 아닙니다.

중간 단계에서 Top 세 개에 수평 힘을 한 번 가합니다. 그러나 JSON은 마지막 단계만 기록하므로, 그 순간의 마찰 반응을 모두 담은 시간 그래프로 해석할 수는 없습니다.

사면체에는 다음 설정을 각각 붙입니다.

```python
UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr("convexHull")
UsdPhysics.MassAPI.Apply(mesh.GetPrim()).CreateMassAttr(2.0)
UsdPhysics.RigidBodyAPI.Apply(mesh.GetPrim())
```

정점 네 개와 삼각형 네 개가 시각 형상을 정의하고, 위 설정이 접촉 형상·질량·강체 운동을 추가합니다. 초록 `UsdPreviewSurface`는 렌더링용 재질입니다. 큐브에 사용한 `PhysicsMaterial`의 마찰계수 0.5와는 별도 설정입니다.

### 실행 결과 확인하기

`initial_scene.usda`를 열어 `/World/Mesh`의 재질, `class` 라벨, 질량 2 kg과 `convexHull` 설정을 살펴보세요. 이 파일은 물리 진행 **전** 장면입니다.

보고서의 `mesh_world_size_m`은 초기 월드 축에 정렬된 경계상자의 크기이며, `mesh_world_position`은 초기 변환의 위치 `(0, 2, 0.1)`입니다. `AlignedMarker`도 그 초기 변환을 한 번 복사합니다. 사면체가 떨어진 뒤의 위치를 계속 추적하는 마커는 아닙니다.

두 요소의 부모가 모두 항등 변환인 `/World`이므로 이 실습에서는 월드 변환을 그대로 복사할 수 있습니다. 부모 변환이 다른 장면에 같은 코드를 옮길 때는 대상 부모 좌표계로 변환해야 합니다.

최종 raycast는 `(0, 0, 3)`에서 아래로 5 m를 검사합니다. `hit`가 참이면 `rigid_body`와 `distance_m`를 읽고, 거짓이면 거리는 `null`입니다. overlap 상자의 중심은 `(0, 0, 0.5)` m, 반쪽 크기인 half extent는 `(2, 0.4, 0.6)` m입니다. 따라서 검사 범위는 X=-2~2, Y=-0.4~0.4, Z=-0.1~1.1 m입니다. 반환 경로는 이 공간과 겹치는 강체이며, 실제 접촉 중인 쌍의 목록과 같지는 않습니다.

### 별도 OBJ 파일 변환하기

장면 생성과 별도로, 제공된 사면체 OBJ도 USD로 바꿀 수 있습니다.

```bash
~/isaacsim/python.sh src/16_python_usd_environment_setup/convert.py --headless
```

변환기는 기본 `tetrahedron.obj`를 읽어 `output/convert-날짜-시간.usda`를 만듭니다. `--input`과 `--output`으로 입력 파일과 새 출력 파일을 지정할 수 있습니다. 이때 `--output`은 폴더가 아닌 **USD 파일 경로**입니다.

`convert.py`는 `omni.kit.asset_converter`의 비동기 작업을 기다리고, 실제 성공 여부와 출력 파일 존재를 검사합니다. 출력 USD를 GUI에서 열어 사면체 모양을 확인하세요. `run.py`는 이 변환 결과를 자동으로 불러오는 코드가 아니라 같은 정점을 직접 만드는 별도 실습입니다.

### MDL 재질로 같은 메시 표현하기

가시 재질의 다른 경로도 비교하려면 새 Isaac Sim GUI에서 출력 `initial_scene.usda`를 열고 Script Editor에 다음을 실행하세요. 설치의 `OmniGlass.mdl`을 사용하며, `run.py`의 접촉 계산을 다시 실행하는 코드는 아닙니다.

```python
import omni.kit.commands
import omni.usd
from pxr import Gf, Sdf, UsdShade

created = []
success, _ = omni.kit.commands.execute(
    "CreateAndBindMdlMaterialFromLibrary",
    mdl_name="OmniGlass.mdl", mtl_name="OmniGlass", mtl_created_list=created,
)
if not success or not created:
    raise RuntimeError("OmniGlass 재질 생성 결과를 확인하세요.")
stage = omni.usd.get_context().get_stage()
material = stage.GetPrimAtPath(created[0])
omni.usd.create_material_input(
    material, "glass_color", Gf.Vec3f(0, 1, 0), Sdf.ValueTypeNames.Color3f
)
UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/World/Mesh")).Bind(
    UsdShade.Material(material)
)
```

사면체가 새 시각 재질을 사용하고 질량·충돌 속성은 그대로인지 Property에서 확인하세요. MDL은 렌더링용 재질 언어이므로 유리 모양을 적용해도 접촉의 마찰계수를 함께 바꾸지는 않습니다. 결과는 **File > Save As**로 별도 저장합니다.

원문의 텍스처 단계까지 비교한다면 같은 생성 명령에서 `mdl_name="OmniPBR.mdl"`, `mtl_name="OmniPBR"`를 사용합니다. 새 Material에 `diffuse_texture`를 `Sdf.ValueTypeNames.Asset` 타입으로 만들고, 실제 접근 가능한 `/Isaac/Samples/DR/Materials/Textures/marble_tile.png` 자산 경로를 지정한 뒤 Mesh에 바인딩하세요. 이 텍스처는 로컬 패키지에 포함되지 않습니다. 경로가 끊어진 결과를 재질 적용 성공으로 판단하지 마세요.

## 3. 장면 작성과 측정의 관계 정리

```text
정점·재질·물리 속성 작성 → initial_scene.usda
    → World 초기화 → 240단계 물리 계산
    → 위치·접촉력·raycast·overlap 읽기 → scene_queries.json
```

한 보고서 안에도 초기 형상 크기와 최종 물리 상태가 함께 들어 있습니다. 값을 읽을 때는 **어느 물체를, 어느 시점에, 어떤 단위로 측정했는지** 확인하세요. 특히 시각 재질·물리 재질·접촉 측정은 화면에서는 함께 작용해도 코드에서는 다른 설정입니다.

## 4. 간단한 확인 실험

같은 240단계에서 `--mass`만 1에서 2로 바꿔보세요.

```bash
~/isaacsim/python.sh src/16_python_usd_environment_setup/run.py --mass 2 --steps 240
```

이 옵션은 위·아래 큐브 여섯 개의 질량을 함께 바꿉니다. 사면체의 질량 2 kg과 마찰계수는 그대로입니다. 두 실행 모두 같은 쌓기 상태에 정착했다면 Top이 아래 큐브를 누르는 힘의 크기가 대략 두 배가 되는지 필터된 힘으로 비교하세요. 기본 질량 1 kg에서 한 Top의 무게는 약 9.81 N입니다.

충돌 순간의 힘이나 다른 배치가 된 결과를 이 정적 기준과 바로 비교하지 마세요. 먼저 위치 배열로 같은 접촉 상태인지 확인합니다.

## 실행할 때 막히면

- **접촉 데이터가 비거나 예상과 다름**: 최종 위치에서 실제로 닿아 있는지 확인하세요. 버퍼 전체가 아니라 개수·시작 인덱스로 유효 구간을 읽습니다.
- **사면체가 초기 위치와 다름**: 낙하한 화면과 초기 값을 비교했을 수 있습니다. `mesh_world_position`은 초기 측정입니다.
- **OBJ 변환 시간 초과**: `--steps`는 변환을 기다릴 앱 업데이트 한도입니다. 너무 작은 값을 지정했다면 빼거나 늘리세요. Headless 기본 한도는 3600회입니다.
- **변환 USD가 실행 화면에 자동으로 안 보임**: 변환 스크립트는 파일을 생성합니다. 출력 경로를 확인하고 **File > Open**으로 여세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Scene Setup Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html)에 대응합니다. 기본 장면은 외부 자산 없이 직접 만들며 시각 재질은 `UsdPreviewSurface`를 사용합니다. MDL·외부 텍스처 비교는 별도의 GUI 작업입니다.

`tutorial.json`은 `not_run`입니다. 이번 개정에서는 로컬 코드와 설치된 5.1 접촉 API의 배열·단위 설명을 대조했으며, PhysX 측정·OBJ 변환·MDL 표시를 새로 실행하지 않았습니다. 위 수치는 조건을 갖춘 실행에서 비교할 기준입니다.
