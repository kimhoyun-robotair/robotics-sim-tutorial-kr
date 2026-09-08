"""Independent range references for the original Building Editor world."""
from pathlib import Path

import pytest

from scripts.check_humble_runtime import expected_box_range, ray_box_distance


def test_ray_box_hit_miss_and_inside():
    assert ray_box_distance((-3, 0, 0), (1, 0, 0), (2, 2, 2)) == 2
    assert ray_box_distance((-3, 2, 0), (1, 0, 0), (2, 2, 2)) is None
    assert ray_box_distance((0, 0, 0), (0, 1, 0), (2, 2, 2)) == 1
    assert ray_box_distance((3, 0, 0), (1, 0, 0), (2, 2, 2)) is None


def test_nested_building_editor_wall_poses(tmp_path):
    world = tmp_path / "building.sdf"
    # Model + link + collision put a 2 m wide wall at world (5, 3, 1).
    # The model's 90 degree rotation changes its local X axis to world Y.
    world.write_text('''<sdf version="1.7"><world name="test"><model name="building">
      <pose>5 0 0 0 0 1.5707963267948966</pose><link name="wall">
      <pose>2 0 0 0 0 0</pose><collision name="wall_collision">
      <pose>1 0 1 0 0 0</pose><geometry><box><size>2 4 2</size></box></geometry>
      </collision></link></model></world></sdf>''')
    hit = expected_box_range(world, (5, 0, 1), (0, 1, 0))
    assert hit["distance_m"] == pytest.approx(2)
    assert hit["world_collision"] == "building/wall"


def test_real_sensor_world_front_wall():
    root = Path(__file__).resolve().parents[1]
    world = root / "ros2_ws/src/gazebo_tutorial_bringup/worlds/sensor.world"
    hit = expected_box_range(world, (0.4, 0.13, 0.39), (1, 0, 0))
    assert hit["world_collision"] == "front_wall/link"
    assert hit["distance_m"] == pytest.approx(5.525)


def test_relative_to_is_rejected_instead_of_misinterpreted(tmp_path):
    world = tmp_path / "unsupported.sdf"
    world.write_text('''<sdf><world><model name="building"><pose relative_to="other">
      0 0 0 0 0 0</pose><link name="wall"><collision name="box">
      <geometry><box><size>2 2 2</size></box></geometry>
      </collision></link></model></world></sdf>''')
    with pytest.raises(AssertionError, match="parent-relative"):
        expected_box_range(world, (-3, 0, 0), (1, 0, 0))
