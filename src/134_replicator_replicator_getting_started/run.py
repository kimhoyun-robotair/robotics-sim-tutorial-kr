"""Four independent Replicator lessons: writer, multi-camera, events and randomizers."""
import argparse
import json
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--example", choices=["basic", "multi", "randomize", "events"], default="basic")
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument("--steps", type=int, default=None, help="Maximum physics updates in events mode; omitted: 300 for capture, then GUI stays open")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--rt-subframes", type=int, default=4)
    parser.add_argument("--pose-writer", action="store_true", help="Also attach PoseWriter in multi mode")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    keep_open = args.steps is None and not args.headless
    capture_steps = args.steps if args.steps is not None else 300
    if min(args.frames, capture_steps, args.rt_subframes) < 1:
        parser.error("frames, steps and rt-subframes must be positive")
    output = (args.output or Path(__file__).with_name("output") / args.example).resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import carb.settings
        import numpy as np
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd
        from isaacsim.core.utils.semantics import add_labels
        from pxr import UsdGeom, UsdLux, UsdPhysics
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        rep.orchestrator.set_capture_on_play(False)
        carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
        rep.set_global_seed(42)
        random.seed(42)
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(600)
        cube = UsdGeom.Cube.Define(stage, "/World/Cube")
        cube.CreateSizeAttr(0.6)
        translation = cube.AddTranslateOp()
        translation.Set((0, 0, 2 if args.example == "events" else 0))
        add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        camera = rep.create.camera(position=(4, 4, 3), look_at=(0, 0, 1 if args.example == "events" else 0))
        products = [rep.create.render_product(camera, (512, 512), name="front")]
        writers = []
        rgb_annotators = []
        writer = rep.writers.get("BasicWriter")
        writer.initialize(output_dir=str(output), rgb=True, bounding_box_2d_tight=True,
                          semantic_segmentation=True, colorize_semantic_segmentation=True)
        writers.append(writer)
        if args.example == "multi":
            camera2 = rep.create.camera(position=(-4, 3, 2), look_at=(0, 0, 0))
            products.append(rep.create.render_product(camera2, (320, 240), name="side"))

            def serializable(value):
                if isinstance(value, np.ndarray):
                    return value.tolist()
                if isinstance(value, np.generic):
                    return value.item()
                if isinstance(value, dict):
                    return {str(k): serializable(v) for k, v in value.items()}
                if isinstance(value, (tuple, list)):
                    return [serializable(v) for v in value]
                return value

            class CameraMetadataWriter(rep.Writer):
                def __init__(self):
                    self.data_structure = "renderProduct"
                    self.annotators = [rep.annotators.get("camera_params"), rep.annotators.get("bounding_box_3d")]
                    self.frame = 0

                def write(self, data):
                    (output / f"camera_metadata_{self.frame:04d}.json").write_text(json.dumps(serializable(data), indent=2))
                    self.frame += 1

            writers.append(CameraMetadataWriter())
            if args.pose_writer:
                pose = rep.writers.get("PoseWriter")
                pose.initialize(output_dir=str(output / "pose"), write_debug_images=True, skip_empty_frames=False)
                writers.append(pose)
            for product in products:
                annotator = rep.annotators.get("rgb")
                annotator.attach(product)
                rgb_annotators.append(annotator)
        for item in writers:
            item.attach(products)
        if args.example == "randomize":
            with rep.trigger.on_custom_event(event_name="change_light"):
                rep.create.light(light_type="Dome", intensity=600, color=rep.distribution.uniform((0.2, 0.2, 0.2), (1, 1, 1)))
        observations = []
        captures = 0
        if args.example == "events":
            physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
            physics.CreateGravityDirectionAttr((0, 0, -1))
            physics.CreateGravityMagnitudeAttr(9.81)
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
            UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
            timeline = omni.timeline.get_timeline_interface()
            timeline.play()
            previous_height = 2.0
            for step in range(capture_steps):
                app.update()
                height = float(translation.Get()[2])
                if height < 0:
                    break
                if previous_height - height >= 0.4:
                    timeline.pause()
                    rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                    UsdGeom.Imageable(cube).MakeInvisible()
                    try:
                        rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                    finally:
                        UsdGeom.Imageable(cube).MakeVisible()
                    observations.append({"step":step,"height":height,"pair":[captures,captures+1]})
                    captures += 2
                    previous_height = height
                    if captures >= args.frames * 2:
                        break
                    timeline.play()
            timeline.stop()
            if not observations:
                raise RuntimeError("No falling-height event observed; inspect physics and USD transform updates")
        else:
            for frame in range(args.frames):
                if args.example == "randomize":
                    translation.Set((random.uniform(-1, 1), random.uniform(-1, 1), 0))
                    if frame % 2 == 0:
                        rep.utils.send_og_event(event_name="change_light")
                rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                observations.append({"frame":frame,"position":list(translation.Get()),
                                     "rgb_shapes":[list(a.get_data().shape) for a in rgb_annotators]})
                captures += 1
        rep.orchestrator.wait_until_complete()
        for item in writers:
            item.detach()
        for annotator in rgb_annotators:
            annotator.detach()
        for product in products:
            product.destroy()
        (output / "observations.json").write_text(json.dumps(observations, indent=2))
        print(f"Capture steps: {captures}; actual observations: {output / 'observations.json'}")
        while keep_open and app.is_running():
            app.update()
    finally:
        app.close()


if __name__ == "__main__":
    main()
