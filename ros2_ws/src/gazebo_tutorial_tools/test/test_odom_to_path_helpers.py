from gazebo_tutorial_tools.odom_to_path import _policy_key, _stamp_to_nanoseconds


class Stamp:
    sec = 12
    nanosec = 345


def test_policy_key_accepts_hyphenated_names():
    assert _policy_key(' Best-Effort ') == 'best_effort'


def test_stamp_to_nanoseconds():
    assert _stamp_to_nanoseconds(Stamp()) == 12_000_000_345
