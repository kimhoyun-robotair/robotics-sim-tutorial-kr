# isaacsim.asset.importer.urdf

첫 등장: [06번 튜토리얼](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) · [urdf_import.py:34](../src/06_python_usd_manual_standalone_python/urdf_import.py#L34)

URDF 로봇을 USD로 변환할 때 사용하는 설정과 자료형을 제공하는 API입니다.

- `_urdf.ImportConfig`, `URDFCreateImportConfig` 명령: 베이스 고정, 자기 충돌, 단위 배율 등의 가져오기 옵션을 지정합니다.
- `_urdf.UrdfJointTargetType.JOINT_DRIVE_POSITION`: 기본 관절 구동을 위치 제어로 설정합니다.
- 튜토리얼에서는 이 설정을 `URDFParseAndImportFile` 또는 `URDFParseFile`·`URDFImportRobot` 명령에 전달하고, 중간 모델의 관절 강성·감쇠를 조정합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [_urdf](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.asset.importer.urdf/docs/index.html#module-isaacsim.asset.importer.urdf._urdf)
