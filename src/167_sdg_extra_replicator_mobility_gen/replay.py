"""Replay one real MobilityGen recording and render bounded sensor samples in Isaac Sim 5.1."""
import argparse
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="One recording directory, containing config.json and stage.usd")
    parser.add_argument("--output", type=Path, default=package / "output" / "replay_01")
    parser.add_argument("--frames", type=int, default=30, help="Maximum number of rendered samples")
    parser.add_argument("--render-interval", type=int, default=40, help="Recording indices skipped between rendered samples")
    parser.add_argument("--subframes", type=int, default=1)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="GUI updates after bounded replay; omitted keeps GUI open")
    parser.add_argument("--no-rgb", action="store_true")
    parser.add_argument("--segmentation", action="store_true")
    parser.add_argument("--depth", action="store_true")
    parser.add_argument("--normals", action="store_true")
    parser.add_argument("--custom-robot", action="store_true", help="Register this package's TutorialSlowJetbot")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if min(args.frames, args.render_interval, args.subframes) < 1:
        parser.error("--frames, --render-interval and --subframes must be positive")
    if args.no_rgb and not any((args.segmentation, args.depth, args.normals)):
        parser.error("Enable at least one rendering output")
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    for name in ("config.json", "stage.usd", "occupancy_map/map.yaml", "occupancy_map/map.png"):
        if not (source / name).is_file():
            parser.error(f"Recording lacks {name}")
    if output.exists():
        parser.error("Choose a new --output directory")
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import json
        import runpy
        import omni.kit.app
        import omni.replicator.core as rep
        extensions = omni.kit.app.get_app().get_extension_manager()
        extensions.set_extension_enabled_immediate("isaacsim.replicator.mobility_gen", True)
        extensions.set_extension_enabled_immediate("isaacsim.replicator.mobility_gen.examples", True)
        if args.custom_robot:
            runpy.run_path(str(package / "custom_robot.py"))
        from isaacsim.replicator.mobility_gen.impl.build import load_scenario
        from isaacsim.replicator.mobility_gen.impl.reader import MobilityGenReader
        from isaacsim.replicator.mobility_gen.impl.writer import MobilityGenWriter
        from isaacsim.replicator.mobility_gen.impl.utils.global_utils import get_world
        reader = MobilityGenReader(str(source))
        if not len(reader):
            raise ValueError("Recording has no state/common frames")
        scenario = load_scenario(str(source))
        get_world().reset()
        if not args.no_rgb:
            scenario.enable_rgb_rendering()
        for enabled, method in ((args.segmentation, scenario.enable_segmentation_rendering),
                                (args.depth, scenario.enable_depth_rendering),
                                (args.normals, scenario.enable_normals_rendering)):
            if enabled:
                method()
        app.update()
        rep.orchestrator.step(rt_subframes=args.subframes, delta_time=0.0, pause_timeline=False)
        output.mkdir(parents=True)
        writer = MobilityGenWriter(str(output))
        writer.copy_init(str(source))
        indices = list(range(0, len(reader), args.render_interval))[:args.frames]
        actual_steps = []
        for index in indices:
            if not app.is_running():
                raise RuntimeError("Application closed before replay completed")
            original = reader.read_state_dict(index=index)
            scenario.load_state_dict(original)
            scenario.write_replay_data()
            app.update()
            rep.orchestrator.step(rt_subframes=args.subframes, delta_time=0.0, pause_timeline=False)
            scenario.update_state()
            state = scenario.state_dict_common()
            state.update({key: value for key, value in original.items() if value is not None})
            step = reader.steps[index]
            writer.write_state_dict_common(state, step)
            if not args.no_rgb:
                writer.write_state_dict_rgb(scenario.state_dict_rgb(), step)
            if args.segmentation:
                writer.write_state_dict_segmentation(scenario.state_dict_segmentation(), step)
            if args.depth:
                writer.write_state_dict_depth(scenario.state_dict_depth(), step)
            if args.normals:
                writer.write_state_dict_normals(scenario.state_dict_normals(), step)
            actual_steps.append(step)
        modalities = [name for name, enabled in (("rgb",not args.no_rgb),("segmentation",args.segmentation),("depth",args.depth),("normals",args.normals)) if enabled]
        counts = {name:len(list((output / "state" / name).rglob("*.jpg" if name=="rgb" else "*.npy" if name=="normals" else "*.png"))) for name in modalities}
        if any(count == 0 for count in counts.values()):
            raise RuntimeError(f"A selected sensor modality produced no files: {counts}")
        summary = {"recorded_steps":len(reader),"rendered_samples":len(actual_steps),"source_step_ids":actual_steps,"sensor_file_counts":counts}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
        if not args.headless:
            import omni.timeline
            omni.timeline.get_timeline_interface().pause()
            step = 0
            while app.is_running() and (args.steps is None or step < args.steps):
                app.update()
                step += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
