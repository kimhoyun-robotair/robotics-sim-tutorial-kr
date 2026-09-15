"""Compare visual geometry, rigid bodies, and collision shapes in Isaac Sim 5.1."""

import argparse
from itertools import count
import csv
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 240 steps)"
    )
    parser.add_argument(
        "--height", type=float, default=1.5, help="Initial cube center height in metres"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; an existing directory is rejected",
    )
    args = parser.parse_args()
    if (args.steps is not None and args.steps < 1) or not 0.3 <= args.height <= 10.0:
        parser.error(
            "--steps must be positive and --height must be between 0.3 and 10 metres"
        )
    if args.steps is None and args.headless:
        args.steps = 240
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid, VisualCuboid
        from isaacsim.core.prims import GeometryPrim, RigidPrim, XFormPrim
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, UsdGeom, UsdLux

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1000)
        set_camera_view(eye=[5.0, 5.0, 4.0], target=[0.0, 0.0, 0.8])

        visual = world.scene.add(
            VisualCuboid(
                prim_path="/World/Visual",
                name="visual",
                position=np.array([-1.0, 0.0, args.height]),
                size=0.3,
                color=np.array([1.0, 1.0, 0.0]),
            )
        )
        VisualCuboid(
            prim_path="/World/RigidOnly",
            name="rigid_geometry",
            position=np.array([0.0, 0.0, args.height]),
            size=0.3,
            color=np.array([1.0, 0.2, 0.2]),
        )
        rigid_only = world.scene.add(
            RigidPrim(
                "/World/RigidOnly",
                name="rigid_only",
                masses=np.array([1.0]),
            )
        )
        VisualCuboid(
            prim_path="/World/Converted",
            name="converted_geometry",
            position=np.array([1.0, 0.0, args.height]),
            size=0.3,
            color=np.array([0.0, 1.0, 1.0]),
        )
        converted = world.scene.add(
            RigidPrim("/World/Converted", name="converted", masses=np.array([1.0]))
        )
        GeometryPrim("/World/Converted").apply_collision_apis()
        dynamic = world.scene.add(
            DynamicCuboid(
                prim_path="/World/Dynamic",
                name="dynamic",
                position=np.array([2.0, 0.0, args.height]),
                size=0.3,
                mass=1.0,
                color=np.array([0.1, 0.4, 1.0]),
            )
        )

        raw = UsdGeom.Cube.Define(stage, "/World/RawUsd")
        raw.CreateSizeAttr(0.3)
        raw.CreateDisplayColorAttr([Gf.Vec3f(0.7, 0.3, 0.9)])
        raw.AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 1.0))
        raw.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, 45.0))
        raw.AddScaleOp().Set(Gf.Vec3f(1.0, 1.5, 0.5))
        core_transform = XFormPrim("/World/Visual", name="visual_transform")
        core_transform.set_world_poses(
            positions=np.array([[-1.0, 0.0, args.height]]),
            orientations=np.array(
                [euler_angles_to_quat(np.array([0.0, 0.0, np.pi / 4]))]
            ),
        )
        core_transform.set_local_scales(np.array([[1.0, 1.5, 0.5]]))
        stage.GetRootLayer().Export(str(output / "initial_scene.usda"))
        world.reset()
        with (output / "heights.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "step",
                    "time_s",
                    "visual_z_m",
                    "rigid_only_z_m",
                    "converted_z_m",
                    "dynamic_z_m",
                ]
            )
            for step in count():
                if not app.is_running() or (args.steps is not None and step >= args.steps):
                    break
                world.step(render=not args.headless)
                heights = [
                    float(visual.get_world_pose()[0][2]),
                    float(rigid_only.get_world_poses()[0][0, 2]),
                    float(converted.get_world_poses()[0][0, 2]),
                    float(dynamic.get_world_pose()[0][2]),
                ]
                writer.writerow([step + 1, (step + 1) / 60, *heights])
                if step % 60 == 0 or (args.steps is not None and step == args.steps - 1):
                    print(
                        f"step={step + 1}: z(visual, rigid-only, converted, dynamic)={heights}"
                    )
        print(f"Scene and measured heights: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
