# omni.kit.asset_converter

첫 등장: [16번 튜토리얼](../src/16_python_usd_environment_setup/TUTORIAL.md) · [convert.py:41](../src/16_python_usd_environment_setup/convert.py#L41)

로컬 OBJ 메시를 USD 파일로 변환하는 비동기 작업을 만든다.

- `AssetConverterContext`의 `use_meter_as_world_unit`으로 변환 단위를 설정한다.
- `get_instance().create_converter_task()`에 입력·출력 경로와 진행 콜백을 전달한다.
- `wait_until_finished()`로 완료를 기다리고 실패 시 `get_detailed_error()`를 확인한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html)
- [omni.kit.asset_converter API](https://docs.omniverse.nvidia.com/extensions/latest/ext_asset-converter.html#programming-guide)
