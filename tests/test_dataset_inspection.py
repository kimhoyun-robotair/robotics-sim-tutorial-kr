import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inspect_dataset.py"
spec = importlib.util.spec_from_file_location("inspect_dataset", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DatasetInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.joinpath("scene.usda").write_text('#usda 1.0\n')
        self.root.joinpath("manifest.json").write_text(json.dumps({
            "expected_frames": 1, "resolution_wh": [8, 6], "class_label": "inspection_part", "frames": [{"frame": 0}]}))
        rgb = np.zeros((6, 8, 3), dtype=np.uint8)
        rgb[:, :4] = 180
        Image.fromarray(rgb).save(self.root / "rgb_0000.png")
        Image.fromarray(rgb).save(self.root / "semantic_segmentation_0000.png")
        self.root.joinpath("semantic_segmentation_labels_0000.json").write_text(
            json.dumps({"(180, 180, 180, 255)": {"class": "inspection_part"}}))

    def test_valid_small_dataset(self):
        self.assertEqual(module.inspect(self.root)["status"], "PASS")

    def test_black_image_fails_even_when_alpha_is_opaque(self):
        rgba = np.zeros((6, 8, 4), dtype=np.uint8)
        rgba[:, :, 3] = 255
        Image.fromarray(rgba).save(self.root / "rgb_0000.png")
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_missing_mask_fails(self):
        self.root.joinpath("semantic_segmentation_0000.png").unlink()
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_mismatched_frame_id_fails(self):
        self.root.joinpath("rgb_0000.png").rename(self.root / "rgb_0001.png")
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_missing_class_fails(self):
        self.root.joinpath("semantic_segmentation_labels_0000.json").write_text('{}')
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_uniform_mask_fails(self):
        Image.fromarray(np.zeros((6, 8, 3), dtype=np.uint8)).save(self.root / "semantic_segmentation_0000.png")
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_uniform_color_rgb_fails(self):
        rgb = np.full((6, 8, 3), [255, 0, 0], dtype=np.uint8)
        Image.fromarray(rgb).save(self.root / "rgb_0000.png")
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_unused_class_color_fails(self):
        self.root.joinpath("semantic_segmentation_labels_0000.json").write_text(
            json.dumps({"(12, 34, 56, 255)": {"class": "inspection_part"}}))
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_consistently_wrong_frame_ids_fail(self):
        for path in list(self.root.glob('*0000*')):
            path.rename(path.with_name(path.name.replace('0000', '9999')))
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")

    def test_missing_scene_fails(self):
        self.root.joinpath('scene.usda').unlink()
        self.assertEqual(module.inspect(self.root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
