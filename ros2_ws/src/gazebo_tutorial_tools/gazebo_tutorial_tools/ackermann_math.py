"""Pure planar kinematics helpers for Ackermann encoder odometry."""

import math


def shortest_angular_delta(previous: float, current: float) -> float:
    """Return a continuous-joint delta in [-pi, pi], including wrap-around."""
    return math.atan2(math.sin(current - previous), math.cos(current - previous))


def normalized_angle(angle: float) -> float:
    """Normalize a heading to [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


def equivalent_center_steering_angle(left: float, right: float) -> float:
    """Recover the bicycle-model steering angle from Ackermann wheel angles.

    For an ideal Ackermann pair, the cotangents of the inner and outer wheel
    angles average to the cotangent of the virtual center wheel.  When the two
    steering actuators momentarily disagree in sign, returning their arithmetic
    mean is a bounded fallback until they settle onto a valid Ackermann pair.
    """
    tangent_left = math.tan(left)
    tangent_right = math.tan(right)
    denominator = tangent_left + tangent_right

    if (
        abs(denominator) < 1.0e-12
        or tangent_left * tangent_right <= 0.0
    ):
        return 0.5 * (left + right)

    tangent_center = (
        2.0 * tangent_left * tangent_right / denominator
    )
    return math.atan(tangent_center)


def bicycle_increment(
    distance: float,
    steering_angle: float,
    wheelbase: float,
) -> float:
    """Return yaw change for a center-line bicycle model."""
    return distance * math.tan(steering_angle) / wheelbase
