"""평가 판정은 controller가 끝났는지가 아니라 실제 이동과 자세로 계산한다."""

import math


def upright(wxyz) -> float:
    w, x, y, z = wxyz
    norm = w * w + x * x + y * y + z * z
    if not math.isfinite(norm) or norm < 1e-12:
        return -1.0
    return 1.0 - 2.0 * (x * x + y * y) / norm


def episode_success(
    distance_m: float, elapsed_s: float, command_m_s: float, fell: bool
) -> bool:
    return not fell and elapsed_s > 0 and distance_m >= 0.5 * command_m_s * elapsed_s
