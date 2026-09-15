import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Core API Overview")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )

    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 120
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from isaacsim.core.prims import RigidPrim
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics, PhysxSchema

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        physics = world.get_physics_context().prim_path
        scene = UsdPhysics.Scene.Get(stage, physics)
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)
        PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateEnableCCDAttr(True)
        raw_cube = UsdGeom.Cube.Define(stage, "/World/RawCube")
        raw_cube.CreateSizeAttr(0.4)
        raw_cube.AddTranslateOp().Set(Gf.Vec3d(-0.5, 0, 2))
        UsdPhysics.RigidBodyAPI.Apply(raw_cube.GetPrim())
        UsdPhysics.CollisionAPI.Apply(raw_cube.GetPrim())
        UsdPhysics.MassAPI.Apply(raw_cube.GetPrim()).CreateMassAttr(1.0)
        raw = world.scene.add(RigidPrim("/World/RawCube", name="raw"))
        wrapped = world.scene.add(
            DynamicCuboid(
                prim_path="/World/WrappedCube",
                name="wrapped",
                position=np.array([0.5, 0, 2]),
                size=0.4,
                mass=1.0,
            )
        )
        report = {
            str(p.GetPath()): p.GetAppliedSchemas()
            for p in (raw_cube.GetPrim(), stage.GetPrimAtPath("/World/WrappedCube"))
        }
        (output / "schemas.json").write_text(json.dumps(report, indent=2))
        stage.GetRootLayer().Export(str(output / "scene.usda"))
        world.reset()
        with (output / "heights.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["step", "raw_z_m", "wrapped_z_m"])
            for i in count():
                if not app.is_running() or (args.steps is not None and i >= args.steps):
                    break
                world.step(render=not args.headless)
                writer.writerow(
                    [
                        i + 1,
                        float(raw.get_world_poses()[0][0, 2]),
                        float(wrapped.get_world_pose()[0][2]),
                    ]
                )
        print(
            "Scene registry:",
            world.scene.get_object("raw").name,
            world.scene.get_object("wrapped").name,
        )
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
