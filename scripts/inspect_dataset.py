"""BasicWriter 출력의 누락, 손상, 검은 RGB, 단색 영상과 라벨 유무를 검사한다."""
import argparse
import ast
import json
from pathlib import Path

import numpy as np
from PIL import Image


def inspect(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    expected = int(manifest["expected_frames"])
    width, height = manifest["resolution_wh"]
    rgb_files = sorted(root.rglob("rgb*.png"))
    mask_files = sorted(root.rglob("semantic_segmentation*.png"))
    label_files = sorted(root.rglob("semantic_segmentation*.json"))
    problems = []
    scene = root / "scene.usda"
    if not scene.is_file() or scene.stat().st_size == 0:
        problems.append("scene.usda missing or empty")
    if expected <= 0:
        problems.append("expected_frames must be positive")
    if len(rgb_files) != expected:
        problems.append(f"RGB count {len(rgb_files)} != {expected}")
    if len(mask_files) != expected:
        problems.append(f"segmentation count {len(mask_files)} != {expected}")
    if len(label_files) != expected:
        problems.append(f"label count {len(label_files)} != {expected}")
    metrics = []
    for path in rgb_files:
        with Image.open(path) as img:
            rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
        mean, std = float(rgb.mean()), float(rgb.std())
        spatial_std = float(rgb.std(axis=(0, 1)).max())
        dark = float((rgb.max(axis=2) <= 2).mean())
        if rgb.shape != (height, width, 3) or dark > 0.98 or spatial_std < 1.0:
            problems.append(f"invalid RGB shape/blackout/flat image: {path.name}")
        metrics.append({"file": str(path.relative_to(root)), "mean": mean,
                        "std": std, "spatial_std": spatial_std, "dark_fraction": dark})
    for path in mask_files:
        with Image.open(path) as img:
            mask = np.asarray(img.convert("RGB"))
        if mask.shape[:2] != (height, width) or len(np.unique(mask.reshape(-1, 3), axis=0)) < 2:
            problems.append(f"invalid/empty segmentation: {path.name}")
    masks_by_id = {p.stem.rsplit("_", 1)[-1]: p for p in mask_files}
    for path in label_files:
        label_text = path.read_text(encoding="utf-8")
        labels = json.loads(label_text)
        if not isinstance(labels, dict):
            raise ValueError(f"labels must be an object: {path.name}")
        labels = labels.get("idToLabels", labels)
        if not isinstance(labels, dict):
            raise ValueError(f"invalid idToLabels: {path.name}")
        colors = []
        for key, value in labels.items():
            if not isinstance(value, dict) or value.get("class") != manifest["class_label"]:
                continue
            try:
                color = ast.literal_eval(key)
                if isinstance(color, (list, tuple)) and len(color) in (3, 4) and all(
                    isinstance(v, int) and 0 <= v <= 255 for v in color
                ):
                    colors.append(color[:3])
            except (ValueError, SyntaxError):
                continue
        mask_path = masks_by_id.get(path.stem.rsplit("_", 1)[-1])
        if not colors or mask_path is None:
            problems.append(f"class color mapping or mask missing: {path.name}")
            continue
        with Image.open(mask_path) as img:
            mask = np.asarray(img.convert("RGB"))
        target_pixels = np.zeros(mask.shape[:2], dtype=bool)
        for color in colors:
            target_pixels |= (mask == np.asarray(color)).all(axis=2)
        ratio = float(target_pixels.mean())
        if not 0.001 <= ratio <= 0.95:
            problems.append(f"target class absent or implausible coverage: {path.name}: {ratio}")
    # 파일 개수만 같고 frame ID가 어긋난 데이터도 실패로 처리한다.
    def frame_ids(paths):
        return {p.stem.rsplit("_", 1)[-1] for p in paths}
    if frame_ids(rgb_files) != frame_ids(mask_files) or frame_ids(rgb_files) != frame_ids(label_files):
        problems.append("RGB/segmentation/label frame IDs differ")
    try:
        recorded = [int(frame["frame"]) for frame in manifest["frames"]]
        actual = {int(value) for value in frame_ids(rgb_files)}
        if recorded != list(range(expected)) or actual != set(recorded):
            problems.append("file IDs or manifest records differ from expected sequence")
    except (KeyError, TypeError, ValueError):
        problems.append("invalid manifest frame sequence")
    return {"status": "PASS" if not problems else "FAIL", "expected_frames": expected,
            "rgb_count": len(rgb_files), "problems": problems, "rgb_metrics": metrics,
            "scope": "file and image sanity only; visual label alignment still requires inspection"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.directory)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "FAIL", "problems": [str(exc)]}
    if args.directory.is_dir():
        (args.directory / "inspection.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
