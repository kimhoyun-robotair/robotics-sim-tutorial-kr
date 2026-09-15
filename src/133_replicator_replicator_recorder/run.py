"""Open a local animated recorder lab or capture with the real SyntheticRecorder API."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Run a bounded native recorder capture instead of the interactive GUI lab")
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--steps", type=int, default=None, help="GUI update limit or headless capture timeout; omitted: GUI stays open, headless uses 10000")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.frames < 1 or (args.steps is not None and args.steps < 1):
        parser.error("frames and steps must be positive")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    task = None
    try:
        import asyncio
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension("isaacsim.replicator.synthetic_recorder")
        app.update()
        import custom_writer
        from isaacsim.core.utils.semantics import add_labels
        from isaacsim.replicator.synthetic_recorder.synthetic_recorder import SyntheticRecorder
        from pxr import UsdGeom, UsdLux
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        stage.SetTimeCodesPerSecond(60)
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(120)
        cube = UsdGeom.Cube.Define(stage, "/World/Carton")
        cube.CreateSizeAttr(1)
        cube.AddTranslateOp().Set((0, 0, 0))
        add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(700)
        camera = UsdGeom.Camera.Define(stage, "/World/AnimatedCamera")
        translation = camera.AddTranslateOp()
        translation.Set((-1, 0, 7), 0)
        translation.Set((1, 0, 7), 120)
        config = {"writer_name":"BasicWriter", "num_frames":args.frames, "rt_subframes":4,
                  "control_timeline":True, "out_dir":"recording", "out_working_dir":str(output),
                  "basic_writer_params":{"rgb":True,"bounding_box_2d_tight":True,"semantic_segmentation":True},
                  "rp_data":[["/World/AnimatedCamera",512,512,"animated"]]}
        (output / "recorder_config.json").write_text(json.dumps(config,indent=2))
        stage.GetRootLayer().Export(str(output / "recorder_stage.usda"))
        if args.headless:
            recorder = SyntheticRecorder()
            for name, value in config.items():
                setattr(recorder, name, value)
            task = asyncio.ensure_future(recorder.start_stop_async())
            for _ in range(args.steps if args.steps is not None else 10000):
                if task.done() or not app.is_running():
                    break
                app.update()
            if not task.done():
                raise RuntimeError("Native recorder exceeded --steps")
            task.result()
            if not list(output.rglob("*.png")):
                raise RuntimeError("Native recorder produced no PNG files")
        else:
            print(f"Load Writer > Config: {output / 'recorder_config.json'}")
            updates = 0
            while app.is_running() and (args.steps is None or updates < args.steps):
                app.update()
                updates += 1
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
        finally:
            app.close()


if __name__ == "__main__":
    main()
