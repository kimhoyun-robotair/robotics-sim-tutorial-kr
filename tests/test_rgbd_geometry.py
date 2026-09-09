"""Offline geometry checks using synthetic pixels, not Isaac Sim render results."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np

MODULE_PATH = Path(__file__).resolve().parents[1] / 'examples/ros2/check_rgbd_target.py'
spec = importlib.util.spec_from_file_location('rgbd_geometry', MODULE_PATH)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


class GeometryTests(unittest.TestCase):
    def sample(self, u=20, v=20):
        rgba = np.zeros((41, 41, 4), dtype=np.uint8)
        rgba[v-5:v+6, u-5:u+6] = [220, 10, 10, 255]
        depth = np.full((41, 41), np.inf)
        depth[v-5:v+6, u-5:u+6] = 2.5
        return {
            'rgba': rgba, 'depth': depth,
            'intrinsics': np.array([[100., 0, 20], [0, 100., 20], [0, 0, 1]]),
            'camera_position': np.array([0, 0, 3]),
            'camera_orientation': np.array([2**-.5, 0, 2**-.5, 0]),
        }

    def test_downward_camera_sees_top_surface(self):
        result = geometry.estimate_target(self.sample())
        np.testing.assert_allclose(result['world_surface_point_m'], [0, 0, .5], atol=1e-8)

    def test_right_pixel_moves_in_negative_world_y(self):
        # Four pixels at f=100 and optical depth 2.5 m represent 0.1 m.
        result = geometry.estimate_target(self.sample(u=24))
        np.testing.assert_allclose(result['world_surface_point_m'], [0, -.1, .5], atol=1e-8)

    def test_background_infinity_is_allowed(self):
        result = geometry.estimate_target(self.sample())
        self.assertEqual(result['depth_z_m'], 2.5)

    def test_invalid_target_depth_is_rejected(self):
        for value in [0.0, np.nan, np.inf, -1.0]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                data = self.sample()
                data['depth'][:] = value
                geometry.estimate_target(data)

    def test_black_image_is_rejected(self):
        data = self.sample()
        data['rgba'][:] = 0
        with self.assertRaises(ValueError):
            geometry.estimate_target(data)

    def test_bad_calibration_is_rejected(self):
        for key, value in [
            ('intrinsics', np.full((3, 3), np.nan)),
            ('camera_orientation', np.zeros(4)),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                data = self.sample()
                data[key] = value
                geometry.estimate_target(data)


if __name__ == '__main__':
    unittest.main()
