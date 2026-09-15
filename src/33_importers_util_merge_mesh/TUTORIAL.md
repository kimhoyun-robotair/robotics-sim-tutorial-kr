# 33. 두 색의 상자를 하나의 Mesh로 합치기

## 이번에 배우는 것

**서로 다른 위치와 재질을 가진 두 Mesh를 합치고, 면·재질·기준 좌표가 어떻게 보존되는지 확인합니다.**

여러 물체를 한 Mesh로 합쳐도 화면에서 보이는 모양과 색이 같게 남을 수 있습니다. 내부적으로는 각 Mesh의 로컬 좌표를 공통 기준으로 바꾸고, 어떤 면에 어느 재질을 쓸지 기록해야 합니다. 이번에는 면 수를 직접 셀 수 있는 두 상자로 이 과정을 살펴봅니다.

| 입력 | 월드 중심 | 구성 |
|---|---|---|
| `/World/Source_0/Geometry` | `(1, 0, 0.2)` | 빨간 상자, 사각형 면 6개 |
| `/World/Source_1/Geometry` | `(1.3, 0, 0.2)` | 파란 상자, 사각형 면 6개 |
| 병합 결과 | 선택한 기준에 따라 결정 | 하나의 Mesh, 면 12개와 재질 구역 2개 |

GeomSubset은 하나의 Mesh에서 일부 면을 묶는 구조입니다. 이번 결과에서는 빨간 면과 파란 면을 나눠 각각 재질을 연결합니다.

## 1. API로 두 Mesh 병합하기

Isaac Sim 5.1과 지원 RTX GPU가 필요합니다. 코드는 상자의 기하와 `UsdPreviewSurface` 재질을 직접 만들고 `isaacsim.util.merge_mesh`를 활성화합니다. 외부 CAD나 로봇 파일은 필요하지 않습니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 실제 설치 위치입니다.

```bash
~/isaacsim/python.sh src/33_importers_util_merge_mesh/run.py --steps 120 --output src/33_importers_util_merge_mesh/output/merge_a
```

병합과 결과 검사를 먼저 수행한 뒤 앱을 120번 업데이트하고 종료합니다. 물리 시뮬레이션 단계가 아니며 로봇 링크를 조립하는 코드도 없습니다. `--steps`를 빼면 GUI가 계속 열립니다. Headless의 기본 업데이트 수는 240회이며, `--frames`는 headless에서 단계를 생략했을 때 사용하는 기존 한도 옵션입니다.

### 코드에서 볼 부분

각 상자는 같은 로컬 정점 배열과 여섯 사각형 면을 사용합니다. 위치 차이는 부모 Xform의 translate에 들어 있습니다. 부모 Xform 두 개를 `paths`에 담아 다음 명령으로 병합합니다.

```python
ok, merged_path = omni.kit.commands.execute(
    'isaacsim.util.merge_mesh.commands.MergeMeshes', source=paths, clear_transform=args.clear_transform,
    deactivate_source=not args.keep_sources, combine_materials=True, materials_destination='/World/MergedLooks',
)
```

- `source`는 병합할 부모 Prim 목록입니다.
- `clear_transform`은 결과 Mesh의 기준점을 세계 원점으로 둘지 선택합니다.
- `deactivate_source`는 병합 후 원본을 비활성화할지 결정합니다.
- `combine_materials`와 목적지 경로는 결과의 재질 정리를 지정합니다.

로컬 실행기는 native `MergeMeshesCommand`를 명시적으로 등록한 뒤 호출합니다. 반환된 경로를 다시 읽어 정말 Mesh가 생성됐는지도 검사합니다.

### 실행 결과 확인하기

출력 폴더의 `scene.usda`는 저장한 병합 장면이고, `report.json`은 실제 결과 Mesh에서 조회한 값입니다.

| 필드 | 기본 입력의 기대 결과 |
|---|---|
| `merged_path` | 생성된 Mesh의 실제 Prim 경로 |
| `faces` | `6 + 6 = 12` |
| `subsets` | 재질 구역 2개 |
| `sources_active` | `[false, false]` |

기본 실행은 원본을 삭제하는 대신 inactive로 둡니다. 화면에 보이는 결과의 빨간색·파란색 위치가 원래 배치와 같은지, 결과 Mesh의 두 subset에 재질이 연결되는지 확인하세요. 프로그램도 면 수·subset 수·원본 활성 상태가 예상과 다르면 오류를 냅니다.

## 2. 같은 입력을 GUI 도구에서 병합하기

이번에는 자동 병합을 건너뛰고 두 원본만 준비합니다.

```bash
~/isaacsim/python.sh src/33_importers_util_merge_mesh/run.py --prepare-only --output src/33_importers_util_merge_mesh/output/prepare_a
```

이 모드는 `scene.usda`만 저장하고 창을 유지합니다. `report.json`이 없는 것이 정상입니다. 다음 순서로 GUI에서 직접 병합하세요.

1. **Tools > Robotics > Asset Editors > Mesh Merge Tool**을 엽니다.
2. `/World/Source_0`, `/World/Source_1`의 **부모 Xform** 두 개를 순서대로 선택합니다. 자식 `Geometry`를 선택하지 않습니다.
3. Source Prim 목록을 확인하고 **Clear Parent Transform**은 끕니다.
4. **Deactivate source assets**, **Combine Materials**를 켜고 재질 목적지는 `/World/MergedLooks`로 정합니다.
5. 병합한 뒤 Destination Prim에서 Mesh·subset·재질을 확인합니다. GUI 편집 결과는 **Save As**로 새 파일에 저장하세요.

### 설정에서 볼 부분

첫 번째 선택 Prim은 기본 결과의 좌표 기준이 됩니다. 표면을 같은 공간에 남기려면 나머지 Mesh의 점들도 이 기준으로 변환해야 합니다. 두 입력이 서로 다른 translate를 갖는데 단순히 점 배열만 이어 붙이면 겹쳐질 수 있는 이유입니다.

다른 기준점을 직접 고르고 싶다면 먼저 **Undo로 앞의 병합을 되돌려 원본 두 개를 활성 상태로** 복구합니다. 빈 Xform을 원하는 위치에 만든 뒤 **빈 Xform을 먼저**, 두 source 부모를 그다음 선택하고 Clear Parent Transform을 끈 채 병합하세요. 빈 Xform은 면을 추가하지 않지만 결과 좌표의 기준을 제공합니다. 원래 두 상자의 월드 표면 위치와 면 수는 유지되는지 확인합니다.

Combine Materials는 재질 이름을 기준으로 정리합니다. 이번 입력은 `Material_0`, `Material_1`로 구별되지만, CAD에서 가져온 서로 다른 재질의 이름이 같다면 합친 뒤 실제 색과 재질 속성도 확인해야 합니다.

이 실습은 Mesh 자체 대신 Xform 부모를 선택하도록 구성했습니다. 코드의 입력 선택과 GUI 선택을 맞추는 방법이며, 설치된 merger의 Mesh 직접 선택 시 중복 수집 문제도 피합니다. 결과가 24면처럼 두 배가 되었다면 원본 선택과 중복 입력을 먼저 확인하세요.

### 실행 결과 확인하기

API 결과와 GUI 결과 모두 상자는 두 개처럼 보여도 Stage에서는 하나의 결과 Mesh여야 합니다. `GeomSubset` 두 개는 다시 두 개의 독립 로봇 링크가 생겼다는 뜻이 아니라 같은 Mesh 안에서 재질을 나눴다는 뜻입니다. 원본 두 개가 inactive인지도 함께 보세요.

## 3. 병합 후 무엇이 바뀌는지 정리

```text
Source_0의 로컬 점 ─┐
                   ├─ 공통 기준 좌표로 변환 → 하나의 Mesh
Source_1의 로컬 점 ─┘                           ├ 빨간 면 subset
                                              └ 파란 면 subset
```

표면의 월드 위치는 유지하면서 장면의 Mesh 수와 로컬 좌표 표현이 바뀝니다. 두 재질을 한 색으로 바꾸거나 두 물체 사이의 관절을 만드는 과정은 아닙니다. 원본 활성 상태까지 확인해야 결과와 원본이 겹쳐 보이는 것도 구분할 수 있습니다.

## 4. 간단한 확인 실험

기준점 옵션만 바꿔 실행해 보세요.

```bash
~/isaacsim/python.sh src/33_importers_util_merge_mesh/run.py --clear-transform --steps 120 --output src/33_importers_util_merge_mesh/output/world_origin
```

기본 결과와 비교하면 Mesh의 transform 기준점은 세계 원점으로 바뀌지만 상자 표면의 월드 위치는 같아야 합니다. 두 실행의 `scene.usda`에서 결과 Prim의 transform과 정점 좌표를 비교하세요. 면 12개·subset 2개·원본 inactive 기준은 바뀌지 않습니다. 기준점 변경과 물체 이동을 구분하는 실험입니다.

## 실행할 때 막히면

- **Mesh Merge Tool 메뉴가 없음**: Extensions에서 `isaacsim.util.merge_mesh`를 켜세요.
- **면 수가 12가 아님**: 부모 Xform 두 개만 선택했는지, 같은 입력을 중복 선택하거나 이미 병합한 결과까지 포함했는지 확인하세요.
- **같은 자리에 표면이 겹쳐 보임**: `--keep-sources`를 사용하면 원본과 결과가 모두 활성 상태로 남습니다. `sources_active`와 원본 상태를 확인하세요.
- **prepare-only 실행에 보고서가 없음**: 자동 병합·검사를 생략하는 모드입니다. GUI 결과는 직접 확인하고 Save As로 저장하세요.
- **이미 존재하는 출력 경로 오류**: 기존 결과를 보관하고 새 `--output` 이름을 사용하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Merge Mesh Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_util_merge_mesh.html)에 대응합니다. native 도구의 선택·기준점·원본 활성·재질 옵션을 두 상자의 로컬 입력으로 비교하고 결과 구조를 검사합니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 2026-09-14의 기본 headless 병합에서 12면·2 subset·원본 비활성화를 확인한 기록입니다. `--clear-transform`, `--keep-sources`, GUI 조작의 실행 검증은 포함하지 않습니다. 당시 실행 조건의 기록이며 현재 코드의 병합을 다시 검증한 결과는 아닙니다.
