# isaacsim.util.merge_mesh.commands

첫 등장: [33번 튜토리얼](../src/33_importers_util_merge_mesh/TUTORIAL.md) · [run.py:35](../src/33_importers_util_merge_mesh/run.py#L35)

선택한 USD 메시들을 합치면서 재질과 원본 활성 상태를 처리하는 명령입니다.

- `MergeMeshesCommand`: `omni.kit.commands.register()`에 등록한 뒤 `isaacsim.util.merge_mesh.commands.MergeMeshes`로 실행합니다.
- `source`, `clear_transform`, `deactivate_source`: 합칠 대상, 변환 초기화, 원본 비활성화 여부를 지정합니다.
- `combine_materials`, `materials_destination`: 재질 통합과 저장 경로를 설정하고, 반환된 Prim 경로로 결과 메시를 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.util.merge_mesh 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.util.merge_mesh/docs/index.html)
