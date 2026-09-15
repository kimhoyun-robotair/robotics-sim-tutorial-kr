# 16. 장면 구성 모음: 접촉, 질량, 메시, 재질, 질의

권장 학습 순서 **16** · Python 실행 환경과 USD 기초 · 출처 ID `t095`

## 이 실습의 의도

붉은 아래 큐브 세 개, 파란 위 큐브 세 개와 초록 사면체를 한 장면에 놓아, 화면의 물체와 일괄 상태·접촉 데이터·USD 속성을 대응시킵니다. 큐브 쌍은 전체 접촉력과 지정한 상대 물체에 대한 접촉력을 비교하기 위한 구성이고, 사면체는 직접 만든 메시의 질량·충돌·시각 재질·라벨·변환을 조사하기 위한 구성입니다. 기본 실행은 240단계 후 장면 질의 결과를 한 번 저장하며, OBJ 변환과 MDL 재질 적용은 아래의 별도 실습입니다.

## 실행 후 확인할 것

- GUI에서 `/World/Top_0`~`Top_2`가 대응하는 `/World/Bottom_0`~`Bottom_2` 위로 떨어지는지 봅니다. `scene_queries.json`의 `bottom_positions`와 `top_positions`는 각각 세 물체의 최종 위치이며, 충분히 진행한 실행에서 두 층의 높이 차이와 화면이 대응해야 합니다.
- 같은 JSON의 `net_contact_forces_N`은 아래 큐브의 전체 접촉을, `top_bottom_contact_matrix_N`은 Top과의 접촉만 담습니다. 바닥 접촉까지 포함하는 값과 필터된 값을 같다고 해석하지 말고, 정착 후 `--mass`만 바꾼 실행의 힘 크기를 비교합니다.
- `contact_data`와 `friction_data`는 쌍별 개수·시작 인덱스로 유효한 행을 골라 읽습니다. 최종 프레임의 자료이므로 중간에 한 번 가한 수평 힘의 마찰 응답이 마지막까지 남아 있거나 모든 배열 행에 접촉이 있어야 하는 것은 아닙니다.
- `initial_scene.usda`에서 `/World/Mesh`의 초록 시각 재질, `class` 라벨, 질량 2 kg, convexHull 충돌 설정을 확인합니다. `mesh_world_size_m`, `mesh_world_position`, `/World/AlignedMarker`는 초기 구성 기준이며, 마커가 낙하하는 메시를 계속 추적하지는 않습니다.
- 최종 `raycast.hit`, `distance_m`, `rigid_body`와 `overlap_bodies`를 봅니다. raycast는 `(0,0,3)`에서 아래로 5 m를 검사하며 hit가 없으면 거리는 `null`입니다. 실제 최종 배치와 맞는 경로가 반환되는지를 확인하고 고정된 접촉 개수를 요구하지 않습니다.
- OBJ 변환을 따로 실행했다면 출력 USD가 실제로 생기고, 열었을 때 `tetrahedron.obj`의 네 꼭짓점·네 삼각형으로 된 사면체가 보이는지 비교합니다. 기본 `run.py` 실행만으로 변환이 수행되지는 않습니다.

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 240단계를 사용합니다. 장면의 기본 물리 실험 240단계와 결과 저장을 마친 뒤에도 물리 시뮬레이션과 GUI는 계속 유지됩니다. `convert.py`도 GUI로 실행하면 변환 완료 후 창을 유지하며, 창 없는 변환은 기존처럼 `--headless`를 사용합니다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py --mass 1`을 실행한다. 위 큐브 세 개가 아래 큐브 위에 떨어지고, 작은 사면체 Mesh도 지면에 놓인다.
2. `RigidPrim("/World/Bottom_[0-2]")`가 세 Prim을 하나의 view로 묶는 부분을 찾는다. 정규식 `[0-2]`는 0·1·2 한 자리와 대응한다. `[0-100]`을 숫자 범위 0~100으로 해석하면 안 된다.
3. `world.scene.add(view)`와 `world.reset()` 이후 `get_world_poses`를 호출한다. `scene_queries.json`의 bottom/top positions에서 각 행이 각각의 큐브인지 확인한다.
4. `contact_filter_prim_paths_expr`는 관심 대상인 Top 큐브와 Bottom 큐브의 접촉만 분리한다. `net_contact_forces_N`과 `top_bottom_contact_matrix_N`을 비교한다. 아래 큐브는 지면과 위 큐브 양쪽에 접촉하므로 두 결과의 의미가 다르다.
5. `contact_data`는 힘·접촉점·법선·분리거리·쌍별 개수·시작 인덱스다. `friction_data`는 접선 힘·점·개수·시작 인덱스다. 개수/시작 인덱스로 유효한 행만 선택한다. 미리 할당된 배열의 모든 행이 실제 접촉은 아니다. `dt=1/60`을 전달해 임펄스를 힘으로 해석한다.
6. `--mass`와 `PhysicsMaterial(static_friction=0.5, dynamic_friction=0.5)`가 서로 다른 속성임을 확인한다. 중간 스텝에는 위 큐브에 한 번 수평 힘을 가해 마찰 응답을 살펴본다.
7. 사면체의 `Mesh`는 정점·면 목록으로 생성된다. `MassAPI`, `RigidBodyAPI`, `CollisionAPI`, convexHull 근사를 각각 적용한다. `BBoxCache.ComputeWorldBound().ComputeAlignedRange()`는 월드 축에 정렬된 경계상자를 계산한다.
8. Stage 순회로 Mesh에 `add_labels(..., instance_name="class")`를 적용한다. 초기 USD를 열고 사면체 Prim에 semantic label과 MaterialBinding이 생겼는지 확인한다.
9. `AlignedMarker`는 사면체의 월드 변환을 복사한 Xform이다. 둘 다 부모 `/World`가 항등 변환인 실습이므로 이 행렬을 local transform에 그대로 쓸 수 있다. 부모가 다른 일반 상황에서는 대상 부모의 월드 역행렬을 곱해야 한다.
10. 마지막에 위에서 아래로 raycast와 상자 overlap을 수행한다. JSON에서 hit 여부·거리·body 경로와 overlap 목록을 확인한다. 부딪히는 대상이 없을 때 `distance_m`은 `null`이다.

## 실제 OBJ 변환

```bash
~/isaacsim/python.sh convert.py --headless
```

`tetrahedron.obj`의 정점과 면을 읽어 `omni.kit.asset_converter`로 변환한다. 기본 출력은 `output/convert-날짜.usda`다. `--input`과 `--output`으로 다른 입력/새 출력 경로를 지정할 수 있다. 생성된 USD를 GUI **File > Open**으로 열어 정점 배치를 비교한다. 변환 task의 실제 결과와 파일 존재를 확인하며 실패/시간 초과를 성공으로 처리하지 않는다.

## 원문의 추가 재질 실습

이 패키지 기본 재질은 자산이 필요 없는 `UsdPreviewSurface`다. 원문의 MDL 예제를 비교하려면 GUI에서 초기 Stage를 연 후 Script Editor에 아래를 실행한다.

```python
import omni.kit.commands
import omni.usd
from pxr import Gf, Sdf, UsdShade
created = []
omni.kit.commands.execute("CreateAndBindMdlMaterialFromLibrary", mdl_name="OmniGlass.mdl", mtl_name="OmniGlass", mtl_created_list=created)
stage = omni.usd.get_context().get_stage()
material = stage.GetPrimAtPath(created[0])
omni.usd.create_material_input(material, "glass_color", Gf.Vec3f(0,1,0), Sdf.ValueTypeNames.Color3f)
UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/World/Mesh")).Bind(UsdShade.Material(material))
```

MDL은 렌더러용 재질 언어다. PhysicsMaterial의 마찰계수와는 별개다. 원문 OmniPBR 텍스처 예제는 자산 루트의 `/Isaac/Samples/DR/Materials/Textures/marble_tile.png`가 필요하다. `mdl_name="OmniPBR.mdl"`, `mtl_name="OmniPBR"`로 새 재질을 만들고 `diffuse_texture` Asset 입력을 해당 실제 경로로 설정해 비교한다.

## 한 가지 변수 실험과 문제 해결

`--mass`만 1에서 2로 바꾼다. 정착 후 지지 접촉력 크기가 질량에 따라 어떻게 변하는지 비교한다. 부호는 관측 대상 방향에 따라 다르므로 절댓값과 축을 함께 읽는다. 짧은 실행의 접촉력은 충격값일 수 있다. 메시가 사라지면 카메라의 선택 프레이밍을 사용하고 **Play** 상태인지 확인한다. raycast/overlap은 물리 초기화 후 실행해야 한다. 원문에 cm 기준 중력 981 예제가 있지만 이 패키지는 m 기준 9.81을 사용한다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Scene Setup Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
