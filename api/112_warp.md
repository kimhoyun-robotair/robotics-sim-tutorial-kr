# warp

첫 등장: [115번 튜토리얼](../src/115_ros2_ros2_camera_noise/TUTORIAL.md) · [noise_warp.py:2](../src/115_ros2_ros2_camera_noise/noise_warp.py#L2)

카메라 영상과 깊이 데이터의 노이즈·색상 변환을 GPU에서 처리할 커널을 작성한다.

- `@wp.kernel`, `wp.tid`: 픽셀별로 실행할 계산과 현재 픽셀 좌표를 정의한다.
- `wp.array2d`, `wp.array3d`: 깊이·RGB·RGBA 입력과 출력 버퍼의 타입을 지정한다.
- `wp.rand_init`, `wp.randn`: 픽셀별 난수를 만들어 가우시안 노이즈를 더한다.
- `wp.clamp`, `wp.max`: 색상 범위와 음수가 될 수 없는 깊이값을 제한한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [NVIDIA Warp Python API: kernel](https://nvidia.github.io/warp/v1.8/modules/runtime.html#warp.kernel)
- [Isaac Sim: Data Augmentation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_augmentation.html)
