"""Numerical checks for the fixed scene in p04_camera_check.py; no simulator import.

RGB inputs are uint8 [0,255] or floating point [0,1]. An optional alpha
channel is deliberately ignored. Depth is optical-axis distance in metres.
These thresholds belong to this lit scene, not to arbitrary robot datasets.
"""

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class ImageThresholds:
    min_rgb_mean: float = 0.02
    min_lit_fraction: float = 0.10
    min_spatial_std: float = 0.015
    max_white_fraction: float = 0.99
    min_depth_valid_fraction: float = 0.30
    min_roi_valid_fraction: float = 0.90
    roi_depth_min_m: float = 2.2
    roi_depth_max_m: float = 3.7


def inspect_frame(rgb, depth, thresholds=None):
    """Return JSON-safe statistics and errors; preserve +inf sky/background depth.

    The central 20% by 20% ROI views the red box in the fixed scene. It must
    contain a nearby surface, so an illuminated sky cannot pass the checks.
    An unchanged static scene is valid: temporal image variation is not a gate.
    """
    limits = thresholds or ImageThresholds()
    stats = {"thresholds": asdict(limits)}
    errors = []
    rgb = np.asarray(rgb)
    depth = np.asarray(depth)
    if rgb.ndim != 3 or rgb.shape[-1] not in (3, 4) or min(rgb.shape[:2], default=0) < 10:
        return stats, [f"RGB shape must be H x W x 3/4 with H,W >= 10; got {rgb.shape}"]
    rgb = rgb[..., :3]  # Opaque alpha=255 must never make a black image pass.
    if depth.ndim == 3 and depth.shape[-1] == 1:
        depth = depth[..., 0]
    if depth.shape != rgb.shape[:2]:
        return stats, [f"Depth shape {depth.shape} does not match RGB {rgb.shape[:2]}"]
    stats["image_shape"] = list(rgb.shape)
    if rgb.dtype == np.uint8:
        normalized = rgb.astype(np.float64) / 255.0
    elif np.issubdtype(rgb.dtype, np.floating):
        normalized = rgb.astype(np.float64)
    else:
        return stats, [f"RGB dtype must be uint8 or floating point [0,1]; got {rgb.dtype}"]
    if not np.isfinite(normalized).all():
        errors.append("RGB contains NaN or infinity")
    elif normalized.min() < 0 or normalized.max() > 1:
        errors.append("Floating point RGB must be normalized to [0,1]")
    else:
        stats["rgb_mean"] = float(normalized.mean())
        stats["rgb_lit_fraction"] = float((normalized.max(axis=-1) > 8.0 / 255.0).mean())
        # Per-channel spatial std rejects a uniform red frame as well as gray.
        stats["rgb_spatial_std"] = float(normalized.std(axis=(0, 1)).mean())
        stats["rgb_white_fraction"] = float((normalized >= 250.0 / 255.0).all(axis=-1).mean())
        if stats["rgb_mean"] < limits.min_rgb_mean:
            errors.append("RGB mean is too low: possible blackout or absent light")
        if stats["rgb_lit_fraction"] < limits.min_lit_fraction:
            errors.append("Too few RGB pixels contain visible signal")
        if stats["rgb_spatial_std"] < limits.min_spatial_std:
            errors.append("RGB lacks spatial structure: possible empty/flat image")
        if stats["rgb_white_fraction"] > limits.max_white_fraction:
            errors.append("RGB is almost entirely saturated white")

    if not np.issubdtype(depth.dtype, np.number) or np.iscomplexobj(depth):
        return stats, errors + ["Depth must be a real numeric array"]
    depth = depth.astype(np.float64)
    valid = np.isfinite(depth) & (depth > 0)
    stats["depth_valid_fraction"] = float(valid.mean())
    stats["depth_positive_inf_fraction"] = float(np.isposinf(depth).mean())
    stats["depth_zero_fraction"] = float((depth == 0).mean())
    stats["depth_median_m"] = float(np.median(depth[valid])) if valid.any() else None
    if np.isnan(depth).any() or np.isneginf(depth).any() or (depth < 0).any():
        errors.append("Depth contains NaN, negative infinity, or negative distances")
    if stats["depth_valid_fraction"] < limits.min_depth_valid_fraction:
        errors.append("Too few depth pixels contain finite positive distances")
    height, width = depth.shape
    roi = depth[height * 2 // 5 : height * 3 // 5, width * 2 // 5 : width * 3 // 5]
    roi_valid = np.isfinite(roi) & (roi > 0)
    stats["roi_depth_valid_fraction"] = float(roi_valid.mean())
    stats["roi_depth_median_m"] = float(np.median(roi[roi_valid])) if roi_valid.any() else None
    if stats["roi_depth_valid_fraction"] < limits.min_roi_valid_fraction:
        errors.append("Central target ROI lacks finite positive depth")
    roi_median = stats["roi_depth_median_m"]
    if roi_median is not None and not limits.roi_depth_min_m <= roi_median <= limits.roi_depth_max_m:
        errors.append("Central target depth is outside the expected metre range")
    return stats, errors
