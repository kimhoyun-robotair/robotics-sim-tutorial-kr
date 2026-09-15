# 33. t116 · 여러 mesh와 재질을 하나의 mesh로 병합하기

권장 학습 순서 **33** · 로봇 자산 가져오기와 제작 · 출처 ID `t116`

Isaac Sim **5.1.0**의 native Mesh Merge Tool로 두 개의 box mesh를 병합한다. 각 box는 6개 면과 다른 재질을 갖는다. `run.py`는 실제 `MergeMeshesCommand`를 호출하고 12개 면/2개 material subset을 검사한다. 물리 링크 병합이나 robot articulation 조립을 수행하는 도구가 아니다.

## 이 실습의 의도

서로 다른 위치와 재질을 가진 두 box를 하나의 Mesh로 합치면서 표면 위치와 재질 구분을 보존하는 방법을 배운다. 빨간색·파란색 원본은 각각 6개 면을 가져, 병합 후 면 수와 material subset으로 중복 병합이나 재질 손실을 확인할 수 있다. 기본 실행은 병합과 구조 검사를 자동 수행하고, `--prepare-only`는 사용자가 GUI 도구에서 병합할 두 원본만 준비한다.

## 실행 후 확인할 것

- **보이는 결과:** 기본 실행에서 빨간 box와 파란 box의 표면은 원래 월드 위치를 유지해야 한다. Stage에서 `report.json`의 `merged_path`가 가리키는 prim은 두 물체의 면을 담은 하나의 Mesh여야 한다.
- **면과 재질:** 기본 `report.json`의 `faces=12`, `subsets=2`를 확인하고 결과 Mesh의 두 `GeomSubset`에 각각 올바른 색의 재질이 연결되었는지 조사한다. 이 수는 이 패키지의 두 6면 box 입력에 대한 기준이다.
- **원본 상태:** 기본 설정의 `sources_active`는 `[false, false]`여야 한다. 원본 `/World/Source_0`, `/World/Source_1`은 삭제된 것이 아니라 비활성화되어 있고, `--keep-sources`를 쓰면 `[true, true]`로 남아 결과와 겹쳐 보이는 것이 정상이다.
- **기준점 비교:** 새 출력으로 `--clear-transform`을 실행해 mesh의 transform 기준점은 world origin으로 바뀌고 표면의 월드 위치는 같은지 비교한다. 이 실험에서는 색이나 재질 수가 달라질 이유가 없다.
- **GUI 준비 모드:** `--prepare-only`에서는 선택된 두 Xform과 `scene.usda`만 준비되며 자동 `report.json`은 생성되지 않는다. GUI 병합 때는 자식 `Geometry`가 아닌 부모 Xform 둘을 선택하고, 병합 결과는 직접 Save As한다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.util.merge_mesh`가 필요하다. 코드가 mesh와 `UsdPreviewSurface` 재질을 모두 작성하므로 외부 자산과 다른 로컬 패키지가 필요 없다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/33_importers_util_merge_mesh
"$ISAAC_SIM/python.sh" run.py
"$ISAAC_SIM/python.sh" run.py --prepare-only --output output/gui
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 240회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

기본은 API 병합 후 `output/scene.usda`와 `report.json`을 저장한다. GUI용 `--prepare-only`는 두 원본만 준비하고 창을 유지한다. GUI 편집 결과를 보관할 때에는 별도 파일명으로 Save As한다. `--headless`에서는 0 frames를 사용할 수 없다.

## native UI로 병합하기

1. GUI 준비 명령으로 시작하고 **Tools > Robotics > Asset Editors > Mesh Merge Tool**을 연다. extension이 꺼져 있으면 Window > Extensions에서 `isaacsim.util.merge_mesh`를 켠다.
2. Stage의 `/World/Source_0`, `/World/Source_1` **Xform 부모**를 순서대로 선택한다. 각 부모 아래 `Geometry` Mesh가 하나씩 있다. **Source Prim**에 두 부모가 표시되고 mesh/material 개수를 확인한다. 첫 선택이 결과의 origin을 결정한다.
3. **Clear Parent Transform**을 끈다. **Deactivate source assets**는 켜고 **Combine Materials**를 켜 재질 목적지를 `/World/MergedLooks`로 지정한다.
4. 병합을 실행하고 Destination Prim을 선택한다. 결과 mesh 아래 `GeomSubset` 두 개와 각각의 material binding을 확인한다. 원본은 inactive지만 삭제된 파일이 아니며 다시 활성화할 수 있다.
5. Undo 후 같은 선택으로 **Clear Parent Transform**만 켜서 다시 병합한다. 표면의 월드 위치는 유지되고 mesh transform의 기준점이 world origin으로 바뀌는지 확인한다.
6. origin을 다른 곳으로 옮기려면 빈 Xform을 원하는 위치에 놓고 먼저 선택한 다음 두 source Xform 부모를 선택한다. 첫 선택 프레임의 효과를 확인한다.

## 코드/API와 USD 개념

`UsdGeom.Mesh`의 points는 로컬 좌표, faceVertexCounts/Indices는 topology다. 두 box의 translate가 달라도 병합 시 같은 기준 좌표로 변환해야 표면 위치를 유지할 수 있다. `UsdShade.MaterialBindingAPI`는 mesh에 재질을 연결하고 `GeomSubset`은 합쳐진 mesh의 면 일부에 재질을 배정한다.

설치된 5.1 merger는 선택 prim의 `Usd.PrimRange`에 선택 prim을 한 번 더 추가한다. Mesh 자체를 선택하면 같은 면을 두 번 병합하므로 이 실습은 각 Mesh를 Xform 아래에 두고 **부모 Xform만 선택**한다. 각 cube의 6개 면을 한 번씩 읽어 결과가 12개 면인지 검사하며, source 부모의 활성 상태도 `--keep-sources` 설정과 대조한다.

`MergeMeshesCommand(source, clear_transform, deactivate_source, combine_materials, materials_destination)`는 설치된 native 도구와 같은 backend를 사용한다. 성공 결과로 반환한 prim을 읽어 face와 subset 수를 검사한다. `Combine Materials`는 재질 이름을 기준으로 같은 것을 합치므로 이름만 같은 다른 재질을 무심코 섞지 않는다. CAD에서 중첩 Looks를 정리할 때 결과 재질 값도 확인한다.

5.1에 설치된 extension은 command 클래스를 자동 등록하지 않으므로 실행기가 `omni.kit.commands.register(MergeMeshesCommand)`로 등록한다. 모듈 전체 이름 `isaacsim.util.merge_mesh.commands.MergeMeshes`를 사용해 다른 extension의 동명 명령과 구분한다. 오류가 나면 Kit 종료 전에 traceback을 남긴다. 종료 코드만 확인하지 말고 `report.json`의 12 faces/2 subsets와 저장된 Mesh를 확인한다.

실험 명령 `--clear-transform --output output/world_origin`으로 기준점 하나만 바꿔 비교할 수 있다. `--keep-sources`는 원본을 활성 상태로 남기므로 원본과 결과가 겹쳐 보일 수 있다. 이 경우 겹침을 병합 실패로 오해하지 않는다. 기본 headless 병합의 12 faces·2 subsets·원본 비활성화 실행 기록은 아래 `RUNTIME_CHECK.md`에 있으며, 다른 옵션과 GUI 조작은 해당 기록의 확인 범위 밖이다.

## 출처

[Isaac Sim 5.1 Merge Mesh Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_util_merge_mesh.html), [설정 옵션](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_util_merge_mesh.html#configuration-options). API 호출은 5.1 `isaacsim.util.merge_mesh/commands.py`, `tests/merge_mesh.py`와 대조했다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
