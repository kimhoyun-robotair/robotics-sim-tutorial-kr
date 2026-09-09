"""Render and validate a fixed RGB/depth scene on Isaac Lab v3.0.0-beta2.patch1.

From the IsaacLab checkout:
  ./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p04_camera_check.py" \
    --enable_cameras --viz none --steps 120 --output-dir /tmp/lab-camera-check

The scene uses USD primitives, so the camera test has no robot-asset download.
"""

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--steps", type=int, default=120, help="Total physics/render steps, including warmup.")
parser.add_argument("--warmup", type=int, default=30, help="Initial frames excluded from numerical checks.")
parser.add_argument("--output-dir", type=Path, default=Path("outputs/p04_camera"))
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if not args.enable_cameras:
    parser.error("This example requires the explicit --enable_cameras flag.")
if args.warmup < 30 or args.steps <= args.warmup:
    parser.error("Use --warmup >= 30 and --steps > --warmup.")

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# Omniverse-dependent imports must follow AppLauncher.
import numpy as np
from PIL import Image
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.renderers import IsaacRtxRendererCfg

import isaaclab.sim as sim_utils
from isaaclab.sensors import Camera, CameraCfg

from image_checks import inspect_frame


def make_box(path, size, position, color):
    """A static collider with a matte material; no free body can fall or explode."""
    cfg = sim_utils.CuboidCfg(
        size=size,
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color, roughness=0.8, metallic=0.0),
    )
    cfg.func(path, cfg, translation=position)


def main():
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(dt=1.0 / 60.0, render_interval=1, device=args.device, physics=PhysxCfg())
    )
    # A top surface at z=0. No remote GroundPlaneCfg USD is required.
    make_box("/World/Floor", (10.0, 10.0, 0.1), (0.0, 0.0, -0.05), (0.35, 0.35, 0.35))
    make_box("/World/RedTarget", (0.8, 0.8, 1.0), (0.0, 0.0, 0.5), (0.8, 0.06, 0.04))
    make_box("/World/GreenBox", (0.6, 0.6, 0.6), (0.0, -1.0, 0.3), (0.04, 0.65, 0.08))
    make_box("/World/BlueBox", (0.6, 0.6, 0.8), (0.0, 1.0, 0.4), (0.04, 0.12, 0.8))
    light = sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0))
    light.func("/World/Light", light)
    camera = Camera(
        CameraCfg(
            prim_path="/World/Camera",
            update_period=0.0,
            width=320,
            height=240,
            data_types=["rgb", "distance_to_image_plane"],
            renderer_cfg=IsaacRtxRendererCfg(depth_clipping_behavior="none"),
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=24.0,
                horizontal_aperture=20.955,
                clipping_range=(0.1, 20.0),
            ),
        )
    )
    eye = [3.0, 0.0, 1.8]
    target = [0.0, 0.0, 0.5]
    sim.set_camera_view(eye, target)
    sim.reset()
    # Avoid hard-coded camera quaternions and world/ROS/OpenGL frame confusion.
    camera.set_world_poses_from_view([eye], [target])

    report = {
        "isaac_lab_tag": "v3.0.0-beta2.patch1",
        "physics": "PhysX",
        "renderer": "IsaacRtxRenderer",
        "steps_requested": args.steps,
        "warmup_steps": args.warmup,
        "steps_completed": 0,
        "checked_frames": 0,
        "failed_frames": [],
        "camera_eye_m": eye,
        "camera_target_m": target,
        "depth_type": "distance_to_image_plane",
        "depth_units": "metres",
        "status": "FAIL",
    }
    last_rgb = None
    last_depth = None
    first_rgb = None
    try:
        for step in range(args.steps):
            if not simulation_app.is_running():
                raise RuntimeError("Simulator closed before all requested steps completed.")
            sim.step()
            camera.update(sim.get_physics_dt(), force_recompute=True)
            report["steps_completed"] = step + 1
            if step < args.warmup:
                continue
            # 3.x output is ProxyArray. .torch is a zero-copy view; copy on CPU
            # before the next update, otherwise a saved sample may change in place.
            output = camera.data.output
            last_rgb = output["rgb"].torch[0].detach().cpu().numpy().copy()
            last_depth = output["distance_to_image_plane"].torch[0].detach().cpu().numpy().copy()
            if first_rgb is None:
                first_rgb = last_rgb.copy()
            stats, errors = inspect_frame(last_rgb, last_depth)
            report["checked_frames"] += 1
            report["last_frame"] = stats
            if errors:
                report["failed_frames"].append({"step": step + 1, "errors": errors})
        if report["failed_frames"]:
            raise RuntimeError(f"{len(report['failed_frames'])} camera frames failed; inspect camera_report.json.")
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if last_rgb is not None:
            np.save(args.output_dir / "rgb.npy", last_rgb)
            Image.fromarray(last_rgb[..., :3]).save(args.output_dir / "rgb.png")
            np.save(args.output_dir / "depth.npy", last_depth)
            report["first_last_rgb_mae_255"] = float(
                np.abs(last_rgb[..., :3].astype(np.float32) - first_rgb[..., :3].astype(np.float32)).mean()
            )
            report["temporal_change_required"] = False
        (args.output_dir / "camera_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        print(json.dumps({"status": report["status"], "output_dir": str(args.output_dir.resolve())}))


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
