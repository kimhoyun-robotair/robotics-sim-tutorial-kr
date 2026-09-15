# isaacsim.asset.importer.mjcf

첫 등장: [31번 튜토리얼](../src/31_importers_import_mjcf/TUTORIAL.md) · [run.py:30](../src/31_importers_import_mjcf/run.py#L30)

`isaacsim.asset.importer.mjcf`는 MJCF 모델을 Isaac Sim의 USD 장면에 가져오는 확장입니다. 튜토리얼에서는 `omni.kit.commands.execute()`로 명령을 호출합니다.

- `MJCFCreateImportConfig`로 가져오기 설정을 만들고 `set_fix_base()` 등으로 옵션을 지정합니다.
- `MJCFCreateAsset`에 XML 경로, 설정, 대상 Prim 경로를 전달합니다.
- 31번은 진자·Ant·Humanoid 모델을 가져온 뒤 생성된 USD 관절을 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 MJCFCreateImportConfig](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.asset.importer.mjcf/docs/index.html#isaacsim.asset.importer.mjcf.impl.commands.MJCFCreateImportConfig)
- [Isaac Sim 5.1 MJCFCreateAsset](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.asset.importer.mjcf/docs/index.html#isaacsim.asset.importer.mjcf.impl.commands.MJCFCreateAsset)
