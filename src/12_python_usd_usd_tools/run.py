import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="USD Tools")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--variant", choices=["red", "blue"], default="red")
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
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdUtils

        assets = output / "moved_assets"
        assets.mkdir()
        asset = Usd.Stage.CreateNew(str(assets / "body.usda"))
        UsdGeom.SetStageMetersPerUnit(asset, 1.0)
        UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
        robot = UsdGeom.Xform.Define(asset, "/Robot")
        asset.SetDefaultPrim(robot.GetPrim())
        cube = UsdGeom.Cube.Define(asset, "/Robot/Body")
        cube.CreateSizeAttr(0.5)
        variants = robot.GetPrim().GetVariantSets().AddVariantSet("finish")
        for name, color in (("red", Gf.Vec3f(1, 0, 0)), ("blue", Gf.Vec3f(0, 0, 1))):
            variants.AddVariant(name)
            variants.SetVariantSelection(name)
            with variants.GetVariantEditContext():
                cube.CreateDisplayColorAttr([color])
        variants.SetVariantSelection(args.variant)
        asset.GetRootLayer().Save()
        assembly = Usd.Stage.CreateNew(str(output / "broken.usda"))
        UsdGeom.SetStageMetersPerUnit(assembly, 1.0)
        UsdGeom.SetStageUpAxis(assembly, UsdGeom.Tokens.z)
        UsdLux.DistantLight.Define(assembly, "/World/Light").CreateIntensityAttr(1500)
        root = UsdGeom.Xform.Define(assembly, "/World")
        assembly.SetDefaultPrim(root.GetPrim())
        instance = UsdGeom.Xform.Define(assembly, "/World/Robot")
        instance.GetPrim().GetReferences().AddReference("old_assets/body.usda")
        assembly.GetRootLayer().Save()
        broken_has_body = assembly.GetPrimAtPath("/World/Robot/Body").IsValid()
        fixed_layer = Sdf.Layer.CreateNew(str(output / "repaired.usda"))
        fixed_layer.TransferContent(assembly.GetRootLayer())
        path_changes = []

        def repair(path):
            new = (
                path.replace("old_assets/", "moved_assets/", 1)
                if path.startswith("old_assets/")
                else path
            )
            if new != path:
                path_changes.append([path, new])
            return new

        UsdUtils.ModifyAssetPaths(fixed_layer, repair)
        fixed_layer.Save()
        fixed = Usd.Stage.Open(fixed_layer)
        selection = fixed.GetPrimAtPath("/World/Robot").GetVariantSet("finish")
        selection.SetVariantSelection(args.variant)
        fixed.GetRootLayer().Save()
        if not fixed.GetPrimAtPath("/World/Robot/Body").IsValid():
            raise RuntimeError("Asset path repair failed")
        report = {
            "broken_has_body": broken_has_body,
            "repaired_has_body": fixed.GetPrimAtPath("/World/Robot/Body").IsValid(),
            "path_changes": path_changes,
            "variants": selection.GetVariantNames(),
            "selection": selection.GetVariantSelection(),
            "color": list(
                UsdGeom.Cube.Get(fixed, "/World/Robot/Body")
                .GetDisplayColorAttr()
                .Get()[0]
            ),
        }
        (output / "tools_report.json").write_text(json.dumps(report, indent=2))
        omni.usd.get_context().open_stage(str(output / "repaired.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0])
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
