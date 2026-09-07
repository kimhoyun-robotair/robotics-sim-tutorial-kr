import math

import pytest

from gazebo_tutorial_tools.ackermann_math import (
    bicycle_increment,
    equivalent_center_steering_angle,
    normalized_angle,
    reference_point_increment,
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


@pytest.mark.parametrize('turn_sign', [1.0, -1.0])
def test_body_centre_follows_its_own_circle_not_the_rear_axle(turn_sign):
    # A quarter turn about ICR=(-offset, +/-radius) ends at the body centre,
    # whose path differs from the rear encoder axle by a rotated rigid offset.
    radius, offset = 2.0, 0.28
    result = reference_point_increment(
        radius * math.pi / 2, turn_sign * math.pi / 2, offset)
    assert result == pytest.approx((radius - offset, turn_sign * (radius + offset)))


@pytest.mark.parametrize('distance', [0.0, 1.2, -0.4])
def test_straight_motion_does_not_depend_on_reference_offset(distance):
    assert reference_point_increment(distance, 0.0, 0.28) == pytest.approx((distance, 0.0))


def test_two_quarter_steps_equal_one_half_circle_for_body_centre():
    quarter = reference_point_increment(math.pi, math.pi / 2, 0.28)
    combined = (quarter[0] - quarter[1], quarter[1] + quarter[0])
    half = reference_point_increment(2 * math.pi, math.pi, 0.28)
    assert combined == pytest.approx(half)
    assert half == pytest.approx((-0.56, 4.0))
