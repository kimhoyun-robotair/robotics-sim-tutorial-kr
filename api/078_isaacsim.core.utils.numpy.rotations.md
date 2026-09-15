# isaacsim.core.utils.numpy.rotations

첫 등장: [62번 튜토리얼](../src/62_sensors_sensors_camera/TUTORIAL.md) · [run.py:33](../src/62_sensors_sensors_camera/run.py#L33)

NumPy 배열로 표현한 회전값을 변환하는 유틸리티이다.

- `euler_angles_to_quats()`: 오일러 각 배열을 카메라 자세에 사용할 쿼터니언으로 바꾼다.
- 카메라·깊이 센서 튜토리얼에서는 `degrees=True`로 도 단위의 회전을 전달한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [euler_angles_to_quats API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.utils/docs/index.html#isaacsim.core.utils.numpy.rotations.euler_angles_to_quats)
