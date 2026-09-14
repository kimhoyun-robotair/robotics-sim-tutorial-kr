"""시간 기반 차동구동 명령. 물리 엔진 없이 읽고 실험할 수 있는 부분."""

import math


def motion_command(
    time_s: float, pattern: str, speed: float, side: float
) -> tuple[float, float]:
    """반환값은 (전진 속도 m/s, yaw 각속도 rad/s). 사각형은 open-loop이다."""
    if pattern == "straight":
        return speed, 0.0
    turn_rate = math.pi / 4
    if pattern == "turn":
        return 0.0, turn_rate
    if pattern != "square":
        raise ValueError(f"알 수 없는 주행 패턴: {pattern}")
    straight_time = side / speed
    turn_time = (math.pi / 2) / turn_rate
    phase = time_s % (straight_time + turn_time)
    return (speed, 0.0) if phase < straight_time else (0.0, turn_rate)
