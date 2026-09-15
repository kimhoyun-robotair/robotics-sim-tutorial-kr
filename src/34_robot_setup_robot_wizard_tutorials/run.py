"""Prepare this lesson's editable USD stage and keep Isaac Sim open for the GUI lab."""
import argparse
import json
from pathlib import Path


def build_fixture(stage):

    raise ValueError("This native GUI lab requires a source --asset or saved --stage")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", default='/Isaac/Samples/Rigging/RobotWizard/raw_blocks.usd', help="Official asset-root-relative path, absolute local USD, or URL")
    parser.add_argument("--stage", type=Path, help="Open your saved result instead of creating a fresh lesson stage")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="UI update limit; omitted or 0 keeps the GUI open; headless requires a positive value")
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("headless requires positive --steps; GUI stays open when --steps is omitted")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        from pxr import Sdf, UsdGeom, UsdPhysics
        from isaacsim.storage.native import get_assets_root_path
        context = omni.usd.get_context()
        if args.stage:
            path = args.stage.expanduser().resolve(strict=True)
            if not context.open_stage(str(path)):
                raise RuntimeError(f"Cannot open {path}")
            stage = context.get_stage()
            # Author changes into a new local layer even when inspecting an earlier result.
            source = str(path)
        else:
            source = args.asset
        layer = Sdf.Layer.CreateNew(str(output / "stage.usda"))
        if source:
            if source.startswith("/Isaac/"):
                root = get_assets_root_path()
                if not root:
                    raise RuntimeError("Isaac Sim 5.1 assets root is unavailable")
                source = root + source
            if not Sdf.Layer.FindOrOpen(source):
                raise RuntimeError(f"Cannot resolve source USD: {source}")
            layer.subLayerPaths = [source]
        layer.Save()
        if not context.open_stage(str(output / "stage.usda")):
            raise RuntimeError("Failed to open the local lesson layer")
        stage = context.get_stage()
        if not source:
            build_fixture(stage)
        for _ in range(1200):
            app.update()
            if not context.is_stage_loading():
                break
        if context.is_stage_loading():
            raise RuntimeError("Stage loading did not finish after 1200 updates")
        report = {"source": source or "local procedural fixture", "meters_per_unit": UsdGeom.GetStageMetersPerUnit(stage),
                  "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
                  "rigid_bodies": [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)],
                  "joints": [str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)],
                  "articulation_roots": [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.ArticulationRootAPI)]}
        if len(list(stage.Traverse())) < 2:
            raise RuntimeError("The lesson stage has no usable content")
        stage.GetRootLayer().Save()
        (output / "initial_inventory.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        print("Follow TUTORIAL.md, save your edits to the local root layer, then close the window.")
        updates = 0
        while app.is_running() and (args.steps == 0 or updates < args.steps):
            app.update()
            updates += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
