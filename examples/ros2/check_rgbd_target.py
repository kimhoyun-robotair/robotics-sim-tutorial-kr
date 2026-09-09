#!/usr/bin/env python3
"""Estimate the visible red surface from camera_imu.py's saved RGB-D frame.

This is an offline geometry exercise, not a detector for arbitrary objects.
Run with Ubuntu's Python and numpy, or with Isaac Sim's python.sh.
"""

import argparse
import json
from pathlib import Path

import numpy as np


def estimate_target(data):
    if "camera_axes" in data and str(data["camera_axes"]) != "world":
        raise ValueError("camera pose must use camera_axes='world'")
    if "quaternion_order" in data and str(data["quaternion_order"]) != "wxyz":
        raise ValueError("camera orientation must use wxyz order")
    rgba = np.asarray(data["rgba"])
    depth = np.asarray(data["depth"])
    intrinsics = np.asarray(data["intrinsics"], dtype=float)
    position = np.asarray(data["camera_position"], dtype=float).reshape(3)
    quaternion = np.asarray(data["camera_orientation"], dtype=float).reshape(4)
    if rgba.ndim != 3 or rgba.shape[2] not in (3, 4) or rgba.dtype != np.uint8:
        raise ValueError("rgba must be an H x W x 3/4 uint8 image")
    if depth.shape != rgba.shape[:2]:
        raise ValueError("RGB and depth must have the same H x W resolution")
    if intrinsics.shape != (3, 3) or not np.isfinite(intrinsics).all():
        raise ValueError("intrinsics must be a finite 3 x 3 matrix")
    if intrinsics[0, 0] <= 0 or intrinsics[1, 1] <= 0:
        raise ValueError("focal lengths must be positive")
    if not np.allclose(intrinsics[2], [0, 0, 1]) or abs(np.linalg.det(intrinsics)) < 1e-12:
        raise ValueError("intrinsics must be a nonsingular pinhole camera matrix")
    if not np.isfinite(position).all() or not np.isfinite(quaternion).all():
        raise ValueError("camera pose contains a non-finite value")
    if not np.isclose(np.linalg.norm(quaternion), 1.0, atol=1e-3):
        raise ValueError("camera orientation must be a normalized wxyz quaternion")

    rgb = rgba[:, :, :3].astype(float)
    red = (rgb[:, :, 0] > 100) & (rgb[:, :, 0] > 1.6 * rgb[:, :, 1])
    red &= rgb[:, :, 0] > 1.6 * rgb[:, :, 2]
    rows, columns = np.nonzero(red)
    if len(rows) < 25:
        raise ValueError("fewer than 25 red pixels: check lighting and camera direction")
    u, v = int(np.median(columns)), int(np.median(rows))
    row_min, row_max = max(0, v - 2), min(depth.shape[0], v + 3)
    col_min, col_max = max(0, u - 2), min(depth.shape[1], u + 3)
    values = depth[row_min:row_max, col_min:col_max]
    valid = np.isfinite(values) & (values > 0)
    valid &= red[row_min:row_max, col_min:col_max]
    if np.count_nonzero(valid) < 9:
        raise ValueError("red center has fewer than 9 finite positive depth samples")
    z = float(np.median(values[valid]))
    ray = np.linalg.solve(intrinsics, np.array([u, v, 1.0]))
    optical = ray * (z / ray[2])

    # Camera.get_world_pose(camera_axes='world') uses +X forward, +Z up.
    # A ROS optical camera uses +Z forward, +X right, +Y down.
    camera_local = np.array([optical[2], -optical[0], -optical[1]])
    w, x, y, zq = quaternion / np.linalg.norm(quaternion)
    rotation = np.array([
        [1 - 2 * (y*y + zq*zq), 2 * (x*y - zq*w), 2 * (x*zq + y*w)],
        [2 * (x*y + zq*w), 1 - 2 * (x*x + zq*zq), 2 * (y*zq - x*w)],
        [2 * (x*zq - y*w), 2 * (y*zq + x*w), 1 - 2 * (x*x + y*y)],
    ])
    world_point = position + rotation @ camera_local
    if not np.isfinite(world_point).all():
        raise ValueError("computed world point is non-finite")
    return {
        "pixel_uv": [u, v],
        "red_pixels": len(rows),
        "depth_z_m": z,
        "optical_point_m": optical.tolist(),
        "world_surface_point_m": world_point.tolist(),
        "camera_axes": "world: +X forward, +Z up; quaternion wxyz",
        "depth_kind": "distance_to_image_plane, meters",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="sensor_data.npz from camera_imu.py")
    parser.add_argument("--output", type=Path, default=Path("target.json"))
    parser.add_argument("--expected-surface-z", type=float)
    parser.add_argument("--tolerance", type=float, default=0.04)
    args = parser.parse_args()
    if not np.isfinite(args.tolerance) or args.tolerance <= 0:
        parser.error("--tolerance must be finite and positive")
    with np.load(args.input, allow_pickle=False) as data:
        result = estimate_target(data)
    if args.expected_surface_z is not None:
        error = abs(result["world_surface_point_m"][2] - args.expected_surface_z)
        result["surface_z_error_m"] = error
        if not np.isfinite(error) or error > args.tolerance:
            raise ValueError(f"surface Z error {error:.6f} m exceeds tolerance")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
