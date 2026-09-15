# usdrt.Sdf

첫 등장: [119번 튜토리얼](../src/119_ros2_ros2_python/TUTORIAL.md) · [camera_manual.py:44](../src/119_ros2_ros2_python/camera_manual.py#L44)

OmniGraph의 카메라 대상 입력에 전달할 USDRT 경로 값을 만든다.

- `usdrt.Sdf.Path(CAMERA_STAGE_PATH)`로 카메라 prim 경로를 표현한다.
- 생성한 경로를 목록에 담아 `setCamera.inputs:cameraPrim`에 지정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [NVIDIA USDRT Python API: Sdf.Path](https://docs.omniverse.nvidia.com/kit/docs/usdrt.scenegraph/latest/py_api/py_api.html#usdrt.Sdf.Path)
- [Isaac Sim: ROS 2 Python 카메라 그래프](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html)
