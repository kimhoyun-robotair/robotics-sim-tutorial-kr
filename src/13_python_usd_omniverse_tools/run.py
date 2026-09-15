import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Commands")
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
        import omni.kit.actions.core
        import omni.kit.commands
        import omni.kit.undo
        import omni.usd
        from pxr import Gf, UsdGeom

        stage = omni.usd.get_context().get_stage()
        success, path = omni.kit.commands.execute(
            "CreateMeshPrimCommand", prim_type="Cube"
        )
        if not success:
            raise RuntimeError(
                "CreateMeshPrimCommand failed; enable the mesh primitive extension"
            )
        prim = stage.GetPrimAtPath(path)
        color = UsdGeom.Gprim(prim).CreateDisplayColorAttr([Gf.Vec3f(1, 0, 0)])
        registry = omni.kit.actions.core.get_action_registry()
        extension_id = "tutorial.commands.local"
        action_id = "make_blue"

        def make_blue():
            success, _ = omni.kit.commands.execute(
                "ChangeProperty",
                prop_path=color.GetPath(),
                value=[Gf.Vec3f(0, 0, 1)],
                prev=color.Get(),
            )
            if not success:
                raise RuntimeError("ChangeProperty failed")

        registry.register_action(extension_id, action_id, make_blue)
        try:
            before = list(color.Get()[0])
            omni.kit.actions.core.execute_action(extension_id, action_id)
            changed = list(color.Get()[0])
            omni.kit.undo.undo()
            undone = list(color.Get()[0])
            omni.kit.undo.redo()
            redone = list(color.Get()[0])
            if (before, changed, undone, redone) != (
                [1, 0, 0],
                [0, 0, 1],
                [1, 0, 0],
                [0, 0, 1],
            ):
                raise RuntimeError(
                    "Command undo/redo did not restore the expected colors"
                )
            report = {
                "prim_path": str(path),
                "before": before,
                "after_action": changed,
                "after_undo": undone,
                "after_redo": redone,
            }
            (output / "command_history.json").write_text(json.dumps(report, indent=2))
            stage.GetRootLayer().Export(str(output / "commands.usda"))
            for step in count():
                if not app.is_running() or (args.steps is not None and step >= args.steps):
                    break
                app.update()
        finally:
            registry.deregister_action(extension_id, action_id)
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
