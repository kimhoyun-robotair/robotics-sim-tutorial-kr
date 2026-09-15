# isaacsim.util.debug_draw

첫 등장: [17번 튜토리얼](../src/17_python_usd_util_snippets/TUTORIAL.md) · [run.py:81](../src/17_python_usd_util_snippets/run.py#L81)

좌표나 경로를 눈으로 확인할 수 있도록 디버그용 도형을 그리는 API입니다.

- `_debug_draw.acquire_debug_draw_interface()`: 그리기 인터페이스를 가져옵니다.
- `draw_points()`, `draw_lines()`, `draw_lines_spline()`: 점, 좌표축, 열린 곡선과 닫힌 곡선을 표시합니다.
- `clear_points()`: 이전 프레임의 점을 지우고 새 위치로 다시 그립니다.
- `get_num_points()`, `get_num_lines()`: 현재 그려진 점과 선의 수를 확인합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [DebugDraw](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/docs/extsbuild/isaacsim.util.debug_draw/docs/index.html#isaacsim.util.debug_draw._debug_draw.DebugDraw)
