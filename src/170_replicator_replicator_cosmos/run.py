"""Capture synchronized CosmosWriter clips from the official warehouse/Carter scene."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--clips", type=int, default=2)
    parser.add_argument("--frames", type=int, default=10, help="Frames per clip")
    parser.add_argument("--capture-interval", type=int, default=2)
    parser.add_argument("--start-delay", type=float, default=0.1)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--canny-low", type=int, default=10)
    parser.add_argument("--canny-high", type=int, default=100)
    parser.add_argument("--semantic-mapping", type=Path, help="Optional semantic class to RGBA JSON mapping")
    parser.add_argument("--target", type=float, nargs=3, default=(3, 3, 0), metavar=("X", "Y", "Z"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output")
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if min(args.clips, args.frames, args.capture_interval, args.width, args.height) < 1:
        parser.error("Clip/frame/interval/resolution values must be positive")
    if args.start_delay < 0 or not 0 <= args.canny_low <= args.canny_high <= 255:
        parser.error("Nonnegative delay and 0 <= Canny low <= high <= 255 are required")
    mapping = json.loads(args.semantic_mapping.read_text(encoding="utf-8")) if args.semantic_mapping else None
    if mapping is not None and (not isinstance(mapping, dict) or not mapping or any(
        not isinstance(key, str) or not isinstance(color, list) or len(color) != 4
        or any(not isinstance(v, int) or not 0 <= v <= 255 for v in color)
        for key, color in mapping.items()
    )):
        parser.error("Semantic mapping must be a nonempty object of class names to four integer RGBA components")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output exists; choose a new path: {output}")

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        from pxr import UsdGeom

        assets = get_assets_root_path()
        if not assets:
            raise RuntimeError("Isaac Sim 5.1 asset root is unavailable")
        context = omni.usd.get_context()
        scene = assets + "/Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd"
        if not context.open_stage(scene):
            raise RuntimeError(f"Cannot open warehouse: {scene}")
        app.update()
        stage = context.get_stage()
        carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)
        carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)
        rep.orchestrator.set_capture_on_play(False)
        robot_path = "/NavWorld/CarterNav"
        robot = add_reference_to_stage(
            usd_path=assets + "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd",
            prim_path=robot_path,
        )
        app.update()
        target = stage.GetPrimAtPath(robot_path + "/targetXform")
        camera = stage.GetPrimAtPath(robot_path + "/chassis_link/sensors/front_hawk/left/camera_left")
        if not target.IsValid() or not camera.IsValid():
            raise RuntimeError("Carter navigation target or front camera is missing; verify 5.1 sample assets")
        for prim, position in ((robot, (-6, 4, 0)), (target, args.target)):
            attr = prim.GetAttribute("xformOp:translate")
            if not attr:
                attr = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
            attr.Set(tuple(position))
        timeline = omni.timeline.get_timeline_interface()
        timeline.set_end_time(max(timeline.get_end_time(), 1000000.0))
        timeline.play()
        delay_end = timeline.get_current_time() + args.start_delay
        for _ in range(1000):
            if timeline.get_current_time() >= delay_end:
                break
            app.update()
        else:
            raise RuntimeError("Timeline failed to reach the requested start delay in 1000 updates")

        output.mkdir(parents=True, exist_ok=False)
        render_product = rep.create.render_product(camera.GetPath(), (args.width, args.height))
        writer = rep.WriterRegistry.get("CosmosWriter")
        writer.initialize(output_dir=str(output), use_instance_id=True, segmentation_mapping=mapping,
                          canny_threshold_low=args.canny_low, canny_threshold_high=args.canny_high)
        writer.attach(render_product)
        observations = []
        try:
            for clip in range(args.clips):
                for frame in range(args.frames):
                    if not app.is_running():
                        raise RuntimeError("Application closed before capture completed")
                    rep.orchestrator.step(pause_timeline=False)
                    observations.append({"clip": clip, "frame": frame, "timeline_seconds": timeline.get_current_time()})
                    if frame < args.frames - 1:
                        for _ in range(args.capture_interval - 1):
                            app.update()
                rep.orchestrator.wait_until_complete()
                writer.next_clip()
            rep.orchestrator.wait_until_complete()
        finally:
            writer.detach()
            render_product.destroy()
            timeline.pause()
        (output / "capture_times.json").write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
        missing = [str(output / f"clip_{clip:04}" / f"{modality}.mp4")
                   for clip in range(args.clips) for modality in ("rgb", "depth", "segmentation", "shaded_seg", "edges")
                   if not (output / f"clip_{clip:04}" / f"{modality}.mp4").is_file()]
        if missing:
            raise RuntimeError(f"Video encoding did not produce expected files: {missing}")
        print(f"Captured {args.clips} clips × {args.frames} frames into {output}")
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
