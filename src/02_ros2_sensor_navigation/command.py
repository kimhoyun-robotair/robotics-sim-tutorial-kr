"""ROS 메시지 입력의 속도 제한과 수신 중단 시 정지."""

import math


class VelocityCommand:
    def __init__(self, timeout_s: float = 0.5):
        self.timeout_s = timeout_s
        self.received_at = -math.inf
        self.velocity = (0.0, 0.0)

    def receive(self, linear: float, angular: float, now: float) -> None:
        if not math.isfinite(linear) or not math.isfinite(angular):
            self.velocity = (0.0, 0.0)
        else:
            self.velocity = (max(-0.2, min(0.2, linear)), max(-1.0, min(1.0, angular)))
        self.received_at = now

    def current(self, now: float) -> tuple[float, float]:
        return (
            self.velocity
            if 0 <= now - self.received_at <= self.timeout_s
            else (0.0, 0.0)
        )
