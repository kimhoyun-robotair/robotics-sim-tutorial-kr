# omni.kit.commands

첫 등장: [06번 튜토리얼](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) · [urdf_import.py:26](../src/06_python_usd_manual_standalone_python/urdf_import.py#L26)

등록된 명령을 이름으로 실행해 장면 편집, 로봇 가져오기, 센서 생성을 수행한다.

- `execute()`로 명령을 실행하고 반환된 성공 여부와 결과를 확인하며, `register()`로 메시 병합 명령을 등록한다.
- 로봇 가져오기: `URDFCreateImportConfig`, `URDFParseAndImportFile`, `URDFParseFile`, `URDFImportRobot`, `MJCFCreateImportConfig`, `MJCFCreateAsset`.
- 장면 편집: `CreateMeshPrimCommand`, `CreateMeshPrimWithDefaultXform`, `ChangeProperty`, `CopyPrim`, `DeletePrimsCommand`, `isaacsim.util.merge_mesh.commands.MergeMeshes`.
- 재질·애니메이션: `CreateAndBindMdlMaterialFromLibrary`, `CreateMdlMaterialPrim`, `CreateRetargetAnimationsCommand`.
- 센서 생성: `RangeSensorCreateGeneric`, `RangeSensorCreateLidar`, `IsaacSensorCreateLightBeamSensor`, `IsaacSensorCreateRtxRadar`, `IsaacSensorCreateRtxLidar`.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [omni.kit.commands API](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.commands/latest/omni.kit.commands.html#module-omni.kit.commands)
