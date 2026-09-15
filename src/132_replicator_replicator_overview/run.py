"""Create a labeled stage and inspect Replicator RGB/semantic outputs."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--interactive", action="store_true", help="Legacy GUI flag; GUI stays open by default, and --steps still limits inspection")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames < 1 or (args.interactive and args.headless):
        parser.error("frames must be positive; interactive needs a GUI")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.replicator.core as rep
        import omni.usd
        from isaacsim.core.utils.semantics import add_labels
        from pxr import UsdGeom, UsdLux
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(600)
        for name, x in [("Labeled", -1.5), ("Unlabeled", 1.5)]:
            cube = UsdGeom.Cube.Define(stage, f"/World/{name}")
            cube.CreateSizeAttr(1)
            cube.AddTranslateOp().Set((x, 0, 0.5))
            if name == "Labeled":
                add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        camera = rep.create.camera(position=(5, 6, 4), look_at=(0, 0, 0.5))
        rp = rep.create.render_product(camera, (512, 512))
        rep.orchestrator.set_capture_on_play(False)
        writer = rep.writers.get("BasicWriter")
        writer.initialize(output_dir=str(output), rgb=True, semantic_segmentation=True,
                          colorize_semantic_segmentation=True, bounding_box_2d_tight=True)
        writer.attach(rp)
        for _ in range(args.frames):
            rep.orchestrator.step(delta_time=0.0, rt_subframes=4)
        rep.orchestrator.wait_until_complete()
        writer.detach()
        rp.destroy()
        stage.GetRootLayer().Export(str(output / "labels.usda"))
        print(f"Labeled=/World/Labeled; Unlabeled=/World/Unlabeled; inspect {output}")
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
