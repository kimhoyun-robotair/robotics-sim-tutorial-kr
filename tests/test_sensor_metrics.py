"""Meaningful rejection tests for corrupted sensor frames; no simulator required."""
import unittest
import numpy as np
from examples.sensor_metrics import camera_metrics, point_cloud_metrics, quaternion_tilt_deg


class SensorMetricsTests(unittest.TestCase):
    def image(self):
        rgb = np.full((240, 320, 3), 80, dtype=np.uint8)
        rgb[80:160, 60:130] = [200, 30, 30]
        rgb[80:160, 190:270] = [30, 40, 200]
        depth = np.full((240, 320), 3., dtype=np.float32)
        depth[80:160, 60:130] = 2.6
        depth[80:160, 190:270] = 2.4
        return rgb, depth

    def test_controlled_camera_fixture_passes(self):
        self.assertTrue(camera_metrics(*self.image())["passed"])

    def test_empty_black_nonfinite_and_wrong_size_fail(self):
        rgb, depth = self.image()
        for color, distance in [(np.array([]), np.array([])), (rgb*0, depth),
                                (rgb, depth*np.nan), (rgb, depth*np.inf),
                                (rgb, depth*0), (rgb[:10], depth)]:
            with self.subTest(shape=color.shape):
                self.assertFalse(camera_metrics(color, distance)["passed"])

    def test_uniform_color_is_not_a_valid_target_scene(self):
        rgb, depth = self.image()
        rgb[:] = [255, 0, 0]
        self.assertFalse(camera_metrics(rgb, depth)["passed"])

    def test_full_scan_passes_partial_scan_and_nonfinite_fail(self):
        angle = np.linspace(-np.pi, np.pi, 720, endpoint=False)
        distance = 3 / np.maximum(np.abs(np.cos(angle)), np.abs(np.sin(angle)))
        points = np.stack([distance*np.cos(angle), distance*np.sin(angle), np.zeros(720)], axis=1)
        self.assertTrue(point_cloud_metrics(points)["passed"])
        self.assertFalse(point_cloud_metrics(points[:180])["passed"])
        points[0, 0] = np.nan
        self.assertFalse(point_cloud_metrics(points)["passed"])
        self.assertFalse(point_cloud_metrics(np.empty((0, 3)))["passed"])

    def test_wrong_scene_geometry_fails(self):
        rgb, depth = self.image()
        for distance in [2.0, 2.5, 3.0, 3.2]:
            with self.subTest(camera_depth=distance):
                self.assertFalse(camera_metrics(rgb, np.full_like(depth, distance))["passed"])
        angle = np.linspace(-np.pi, np.pi, 720, endpoint=False)
        for radius in [.2, 1., 3., 8.]:
            points = np.stack([radius*np.cos(angle), radius*np.sin(angle), np.zeros(720)], axis=1)
            with self.subTest(lidar_radius=radius):
                self.assertFalse(point_cloud_metrics(points)["passed"])

    def test_tilt_and_invalid_quaternion(self):
        self.assertAlmostEqual(quaternion_tilt_deg([1, 0, 0, 0]), 0)
        self.assertAlmostEqual(quaternion_tilt_deg([2**-.5, 2**-.5, 0, 0]), 90)
        with self.assertRaises(ValueError):
            quaternion_tilt_deg([0, 0, 0, 0])


if __name__ == '__main__':
    unittest.main()
