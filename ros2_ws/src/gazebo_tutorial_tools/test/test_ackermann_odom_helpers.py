import math

import pytest

from gazebo_tutorial_tools.ackermann_math import (
    bicycle_increment,
    equivalent_center_steering_angle,
    normalized_angle,
    shortest_angular_delta,
)


def test_shortest_delta_crosses_positive_pi_wrap():
    result = shortest_angular_delta(math.pi - 0.1, -math.pi + 0.1)
    assert result == pytest.approx(0.2)


def test_shortest_delta_crosses_negative_pi_wrap():
    result = shortest_angular_delta(-math.pi + 0.1, math.pi - 0.1)
    assert result == pytest.approx(-0.2)


def test_normalized_angle():
    assert normalized_angle(3.0 * math.pi) == pytest.approx(math.pi)


@pytest.mark.parametrize('center', [0.0, 0.3, 0.6, -0.3, -0.6])
def test_recovers_center_angle_from_ackermann_pair(center):
    wheelbase = 0.56
    track_width = 0.62
    tangent_center = math.tan(center)
    left = math.atan(
        tangent_center
        / (1.0 - track_width * tangent_center / (2.0 * wheelbase))
    )
    right = math.atan(
        tangent_center
        / (1.0 + track_width * tangent_center / (2.0 * wheelbase))
    )
    assert equivalent_center_steering_angle(left, right) == pytest.approx(center)


def test_center_angle_falls_back_safely_for_opposed_transient_angles():
    assert equivalent_center_steering_angle(0.2, -0.2) == pytest.approx(0.0)


def test_bicycle_increment_is_zero_when_steering_is_zero():
    assert bicycle_increment(1.0, 0.0, 0.56) == pytest.approx(0.0)


def test_bicycle_increment_matches_curvature():
    expected = 0.8 * math.tan(0.3) / 0.56
    assert bicycle_increment(0.8, 0.3, 0.56) == pytest.approx(expected)
