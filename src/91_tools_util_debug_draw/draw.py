"""Run in a fresh Isaac Sim session with isaacsim.util.debug_draw enabled."""
import math
from isaacsim.util.debug_draw import _debug_draw

draw = _debug_draw.acquire_debug_draw_interface()
if draw.get_num_points() or draw.get_num_lines():
    raise RuntimeError("Debug drawer already contains data; use a clean session")
points = [(math.cos(i * math.tau / 32), math.sin(i * math.tau / 32), 0.5) for i in range(32)]
draw.draw_points(points, [(0.2, 0.8, 1.0, 1.0)] * len(points), [8.0] * len(points))
draw.draw_lines([(0, 0, 0)] * 3, [(1, 0, 0), (0, 1, 0), (0, 0, 1)],
                [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)], [4.0] * 3)
spline = [(-1.0, -1.0, 0.2), (-0.5, -1.0, 0.8), (0.5, -1.0, 0.2), (1.0, -1.0, 0.8)]
draw.draw_lines_spline(spline, (1.0, 1.0, 0.0, 1.0), 4, False)
draw.draw_lines_spline([(x, y-0.3, z) for x, y, z in spline], (1.0, 0.2, 1.0, 1.0), 4, True)
print("point count", draw.get_num_points(), "line count", draw.get_num_lines())
