"""CPU tests for failure detection; these do not exercise RTX or PhysX."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from image_checks import inspect_frame


class ImageChecksTest(unittest.TestCase):
    def good_scene(self):
        rgb = np.full((100, 120, 3), 80, dtype=np.uint8)
        rgb[30:70, 35:85] = (210, 25, 15)
        depth = np.full((100, 120, 1), 3.0, dtype=np.float32)
        return rgb, depth

    def test_structured_rgb_and_target_depth_pass(self):
        stats, errors = inspect_frame(*self.good_scene())
        self.assertEqual(errors, [])
        self.assertEqual(stats["roi_depth_median_m"], 3.0)

    def test_background_positive_infinity_is_valid(self):
        rgb, depth = self.good_scene()
        depth[:20] = np.inf
        stats, errors = inspect_frame(rgb, depth)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(stats["depth_positive_inf_fraction"], 0.2)

    def test_black_rgb_with_opaque_alpha_fails(self):
        rgb, depth = self.good_scene()
        rgba = np.zeros((*rgb.shape[:2], 4), dtype=np.uint8)
        rgba[..., 3] = 255
        stats, errors = inspect_frame(rgba, depth)
        self.assertTrue(errors)
        self.assertEqual(stats["rgb_mean"], 0.0)

    def test_uniform_red_is_not_spatial_structure(self):
        rgb, depth = self.good_scene()
        rgb[:] = (200, 0, 0)
        _, errors = inspect_frame(rgb, depth)
        self.assertTrue(any("spatial" in error for error in errors))

    def test_rgb_nan_and_out_of_range_fails(self):
        rgb, depth = self.good_scene()
        floating = rgb.astype(np.float32) / 255.0
        floating[0, 0, 0] = np.nan
        self.assertTrue(inspect_frame(floating, depth)[1])
        floating[0, 0, 0] = 255.0
        self.assertTrue(inspect_frame(floating, depth)[1])

    def test_normalized_rgb_supported(self):
        rgb, depth = self.good_scene()
        self.assertEqual(inspect_frame(rgb.astype(np.float32) / 255.0, depth)[1], [])

    def test_empty_zero_and_all_infinite_depth_fail(self):
        rgb, depth = self.good_scene()
        for value in (0.0, np.inf, np.nan, -np.inf, -1.0):
            with self.subTest(value=value):
                depth.fill(value)
                self.assertTrue(inspect_frame(rgb, depth)[1])

    def test_target_roi_cannot_be_background(self):
        rgb, depth = self.good_scene()
        depth[40:60, 48:72] = np.inf
        stats, errors = inspect_frame(rgb, depth)
        self.assertGreater(stats["depth_valid_fraction"], 0.9)
        self.assertTrue(any("ROI" in error for error in errors))

    def test_wrong_depth_units_fail(self):
        rgb, depth = self.good_scene()
        depth *= 1000.0
        self.assertTrue(any("metre" in error for error in inspect_frame(rgb, depth)[1]))

    def test_wrong_image_shapes_fail(self):
        rgb, depth = self.good_scene()
        self.assertTrue(inspect_frame(rgb[None], depth)[1])
        self.assertTrue(inspect_frame(rgb, depth[:20])[1])


if __name__ == "__main__":
    unittest.main()
