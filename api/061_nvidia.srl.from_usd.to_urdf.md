# nvidia.srl.from_usd.to_urdf

첫 등장: [32번 튜토리얼](../src/32_importers_export_urdf/TUTORIAL.md) · [run.py:30](../src/32_importers_export_urdf/run.py#L30)

USD의 로봇 구조를 URDF로 변환하는 클래스이며, Isaac Sim의 URDF exporter 확장을 활성화한 뒤 사용합니다.

- `UsdToUrdf`: 변환할 Stage와 로봇 루트 Prim을 지정합니다.
- `save_to_file()`: URDF 저장 위치, 메시 폴더, 메시 경로 접두사를 지정해 내보냅니다.
- 튜토리얼에서는 같은 형상의 visibility·collision 설정을 바꿔 URDF의 `visual`과 `collision` 결과를 비교합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [isaacsim.asset.exporter.urdf 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.asset.exporter.urdf/docs/index.html)
- [USD to URDF Exporter 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_omni_exporter_urdf.html)
