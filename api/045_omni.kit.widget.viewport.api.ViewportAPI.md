# omni.kit.widget.viewport.api.ViewportAPI

첫 등장: [17번 튜토리얼](../src/17_python_usd_util_snippets/TUTORIAL.md) · [TUTORIAL.md:47](../src/17_python_usd_util_snippets/TUTORIAL.md#L47)

`get_active_viewport()`가 반환하는 객체로, 활성 viewport의 렌더 해상도·카메라·render product를 다룬다.

- `set_texture_resolution()`과 `get_texture_resolution()`으로 화면에 렌더링할 픽셀 크기를 설정하고 읽는다.
- `camera_path`로 현재 카메라 prim 경로를 읽어 USD 카메라 속성을 조회한다.
- 119번에서는 `get_render_product_path()`로 ROS 카메라 출력에 연결된 render product 경로를 얻는다.
- 제목은 5.1 설치본의 구현 경로이며, 공식 Kit 문서에서는 `omni.kit.widget.viewport.ViewportAPI`로 표기한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/util_snippets.html)
- [공식 Kit API — ViewportAPI](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.widget.viewport/latest/omni.kit.widget.viewport/omni.kit.widget.viewport.ViewportAPI.html)
