import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scene = load('tutorial_ros_scene', 'examples/07_ros_scene.py')
guard = load('tutorial_ros_guard', 'scripts/ros_drive_guard.py')


class CommandTests(unittest.TestCase):
    def test_normal_command_is_preserved(self):
        self.assertEqual(scene.bounded_command(0.1, -0.2), (0.1, -0.2))

    def test_excessive_positive_and_negative_commands_are_clipped(self):
        self.assertEqual(scene.bounded_command(2.0, -3.0), (0.2, -0.6))
        self.assertEqual(scene.bounded_command(-2.0, 3.0), (-0.2, 0.6))

    def test_nan_stops_both_axes(self):
        self.assertEqual(scene.bounded_command(math.nan, 0.3), (0.0, 0.0))
        self.assertEqual(scene.bounded_command(0.1, math.nan), (0.0, 0.0))

    def test_infinity_stops_both_axes(self):
        self.assertEqual(scene.bounded_command(math.inf, 0.2), (0.0, 0.0))
        self.assertEqual(scene.bounded_command(0.1, -math.inf), (0.0, 0.0))

    def test_guard_bounds_and_nonfinite(self):
        self.assertEqual(guard.bounded(4.0, 0.2), 0.2)
        self.assertEqual(guard.bounded(-4.0, 0.2), -0.2)
        self.assertEqual(guard.bounded(math.nan, 0.2), 0.0)


if __name__ == '__main__':
    unittest.main()
