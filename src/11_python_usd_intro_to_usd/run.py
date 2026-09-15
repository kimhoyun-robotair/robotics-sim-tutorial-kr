import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Working with USD")
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
        import omni.usd
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics

        asset = Usd.Stage.CreateNew(str(output / "robot.usda"))
        UsdGeom.SetStageMetersPerUnit(asset, 1.0)
        UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
        robot = UsdGeom.Xform.Define(asset, "/mock_robot")
        body = UsdGeom.Cube.Define(asset, "/mock_robot/body")
        body.CreateSizeAttr(0.6)
        body.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
        for name, y in (("wheel_left", 0.4), ("wheel_right", -0.4)):
            wheel = UsdGeom.Cylinder.Define(asset, "/mock_robot/" + name)
            wheel.CreateRadiusAttr(0.2)
            wheel.CreateHeightAttr(0.1)
            wheel.CreateAxisAttr("Y")
            wheel.AddTranslateOp().Set(Gf.Vec3d(0, y, 0.2))
        UsdGeom.Xform.Define(asset, "/World")
        UsdPhysics.Scene.Define(asset, "/World/PhysicsScene")
        UsdLux.DistantLight.Define(asset, "/World/Light").CreateIntensityAttr(1500)
        asset.SetDefaultPrim(robot.GetPrim())
        asset.GetRootLayer().Save()
        assembly = Usd.Stage.CreateNew(str(output / "assembly.usda"))
        UsdGeom.SetStageMetersPerUnit(assembly, 1.0)
        UsdGeom.SetStageUpAxis(assembly, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(assembly, "/World")
        assembly.SetDefaultPrim(root.GetPrim())
        UsdLux.DistantLight.Define(assembly, "/World/Light").CreateIntensityAttr(1500)
        UsdPhysics.Scene.Define(assembly, "/World/PhysicsScene")
        for name, x in (("RobotA", -1.0), ("RobotB", 1.0)):
            prim = UsdGeom.Xform.Define(assembly, "/World/" + name)
            prim.GetPrim().GetReferences().AddReference("robot.usda")
            prim.AddTranslateOp().Set(Gf.Vec3d(x, 0, 0))
        UsdGeom.Cube.Get(assembly, "/World/RobotB/body").CreateDisplayColorAttr(
            [Gf.Vec3f(0.2, 0.5, 1.0)]
        )
        assembly.GetRootLayer().Save()
        assembly.Export(str(output / "flattened.usda"))
        if assembly.GetPrimAtPath("/World/RobotA/PhysicsScene").IsValid():
            raise RuntimeError("Environment unexpectedly leaked through defaultPrim")
        flattened = Usd.Stage.Open(str(output / "flattened.usda"))
        report = {
            "asset_default_prim": str(asset.GetDefaultPrim().GetPath()),
            "asset_prims": [str(p.GetPath()) for p in asset.Traverse()],
            "assembly_prims": [str(p.GetPath()) for p in assembly.Traverse()],
            "flattened_prims": [str(p.GetPath()) for p in flattened.Traverse()],
        }
        (output / "composition.json").write_text(json.dumps(report, indent=2))
        omni.usd.get_context().open_stage(str(output / "assembly.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0.4])
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            app.update()
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
