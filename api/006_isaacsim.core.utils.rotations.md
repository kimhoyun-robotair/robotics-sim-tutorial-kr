# isaacsim.core.utils.rotations

첫 등장: [00번 튜토리얼](../src/00_core_quickstart_isaacsim/TUTORIAL.md) · [run.py:67](../src/00_core_quickstart_isaacsim/run.py#L67)

오일러 각과 쿼터니언 사이에서 회전 표현을 변환하는 함수 모음이다.

- `euler_angles_to_quat()`: 물체나 로봇의 오일러 각을 자세 설정에 사용할 쿼터니언으로 바꾼다.
- `quat_to_euler_angles()`: 회전에서 오일러 각을 얻어 합성 데이터 장면 배치에 사용한다.
- 기본 각도 단위는 라디안이며, 도 단위를 사용할 때는 `degrees=True`를 지정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [euler_angles_to_quat API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.rotations.euler_angles_to_quat)
- [quat_to_euler_angles API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.rotations.quat_to_euler_angles)
