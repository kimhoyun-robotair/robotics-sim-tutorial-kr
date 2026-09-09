"""Small, simulator-independent quality gates for the tutorial's controlled scenes.

These thresholds are fixture checks, not universal sensor accuracy specifications.
"""
from __future__ import annotations

import numpy as np


def camera_metrics(rgb, depth, expected_shape=(240, 320)):
    rgb = np.asarray(rgb)
    depth = np.asarray(depth)
    if depth.ndim == 3 and depth.shape[-1] == 1:
        depth = depth[..., 0]
    failures = []
    result = {"rgb_shape": list(rgb.shape), "depth_shape": list(depth.shape)}
    if rgb.ndim != 3 or rgb.shape[:2] != expected_shape or rgb.shape[2] not in (3, 4):
        failures.append("RGB shape differs from the requested image size")
    if depth.shape != expected_shape:
        failures.append("Depth shape differs from the requested image size")
    if failures:
        return dict(result, passed=False, failures=failures)
    color = rgb[..., :3].astype(np.float64)
    if not np.isfinite(color).all():
        return dict(result, passed=False, failures=["RGB contains non-finite values"])
    # This fixture expects the documented uint8 RGB output; reject guessed scaling.
    if rgb.dtype != np.uint8:
        return dict(result, passed=False, failures=["Expected uint8 RGB output"])
    result.update(rgb_mean=float(color.mean()), rgb_std=float(color.std()), spatial_std=float(color.std(axis=(0, 1)).max()),
                  black_fraction=float(np.mean(np.max(color, axis=-1) <= 2)))
    if result["rgb_mean"] <= 2 or result["spatial_std"] <= 2 or result["black_fraction"] >= .98:
        failures.append("Black or nearly uniform RGB frame in the lit color-target scene")
    valid = np.isfinite(depth) & (depth > 0) & (depth < 10)
    result["depth_valid_fraction"] = float(valid.mean())
    result["depth_median_m"] = float(np.median(depth[valid])) if valid.any() else None
    if result["depth_valid_fraction"] < .9:
        failures.append("Too few finite positive depth pixels in the fully covered scene")
    if result["depth_median_m"] is None or not 2.0 <= result["depth_median_m"] <= 3.2:
        failures.append("Depth is inconsistent with the target 3 m below the camera")
    height, width = expected_shape
    roi_checks = {}
    # Interior image patches, away from cube silhouette edges. These coordinates
    # belong to the camera pose/intrinsics and two boxes in 04_camera_check.py.
    for name, y0, y1, x0, x1, expected_depth in [
        ("floor", .05, .10, .05, .10, 3.0),
        ("red", .45, .55, .275, .325, 2.6),
        ("blue", .45, .55, .6875, .7375, 2.4),
    ]:
        rows = slice(int(height*y0), int(height*y1))
        columns = slice(int(width*x0), int(width*x1))
        patch, patch_valid = depth[rows, columns], valid[rows, columns]
        ratio = float(patch_valid.mean()) if patch_valid.size else 0.0
        median = float(np.median(patch[patch_valid])) if patch_valid.any() else None
        depth_ok = ratio >= .95 and median is not None and abs(median-expected_depth) <= .05
        roi_checks[name] = {"valid_fraction": ratio, "median_depth_m": median,
                            "expected_depth_m": expected_depth, "depth_passed": depth_ok}
        if not depth_ok:
            failures.append(f"{name} target depth does not match the known fixture geometry")
        if name in ("red", "blue"):
            mean_color = color[rows, columns].mean(axis=(0, 1))
            channel = 0 if name == "red" else 2
            other = [index for index in range(3) if index != channel]
            color_ok = bool(mean_color[channel] > 1.3*mean_color[other].max())
            roi_checks[name]["color_passed"] = color_ok
            if not color_ok:
                failures.append(f"{name} color target is absent from its expected image region")
    result["target_regions"] = roi_checks
    return dict(result, passed=not failures, failures=failures)


def point_cloud_metrics(points):
    """Validate sensor-local XYZ from the bounded room fixture (walls at +/-3 m)."""
    points = np.asarray(points)
    if points.ndim != 2 or points.shape[1] != 3 or points.shape[0] < 100:
        return {"passed": False, "failures": ["Expected at least 100 XYZ points"],
                "shape": list(points.shape)}
    finite = np.isfinite(points).all(axis=1)
    failures = []
    if not finite.all():
        failures.append("Point cloud contains NaN or infinity")
    usable = points[finite]
    ranges = np.linalg.norm(usable, axis=1)
    valid = (ranges > .1) & (ranges < 10)
    valid_fraction = float(valid.sum() / len(points))
    if valid_fraction < .95:
        failures.append("Points fall outside the controlled room's expected range")
    usable = usable[valid]
    # At least 11 of 12 angular sectors should have returns in an enclosed room.
    sectors = np.floor((np.arctan2(usable[:, 1], usable[:, 0]) + np.pi) / (2*np.pi) * 12).astype(int) % 12
    occupied = int(len(np.unique(sectors)))
    if occupied < 11:
        failures.append("Angular coverage is incomplete; check scan accumulation and tick rate")
    if len(usable):
        absolute = np.abs(usable)
        inside_room = (absolute <= np.array([3.1, 3.1, 1.6])).all(axis=1)
        residual = np.min(np.abs(absolute - np.array([3., 3., 1.5])), axis=1)
        surface_fraction = float(np.mean(inside_room & (residual <= .1)))
    else:
        surface_fraction = 0.0
    if surface_fraction < .95:
        failures.append("Points do not lie on the known room walls, floor or ceiling")
    return {"passed": not failures, "failures": failures, "point_count": len(points),
            "room_surface_fraction": surface_fraction,
            "valid_fraction": valid_fraction, "occupied_30deg_sectors": occupied,
            "median_range_m": float(np.median(ranges[valid])) if valid.any() else None}


def quaternion_tilt_deg(quaternion):
    q = np.asarray(quaternion, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q)-1) > 1e-3:
        raise ValueError("Expected a finite unit quaternion in wxyz order")
    w, x, y, z = q
    return float(np.degrees(np.arccos(np.clip(1 - 2*(x*x+y*y), -1, 1))))
