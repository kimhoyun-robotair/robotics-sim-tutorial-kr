"""Generate and physically evaluate antipodal grasps with Isaac Sim 5.1 GraspingManager."""
import argparse
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=package / "grasp_config.yaml")
    parser.add_argument("--scene", default="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Stage/sdg_grasping_xarm.usd")
    parser.add_argument("--output", type=Path, default=package / "output" / "grasps_01")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted: GUI until closed, headless evaluation limit 10000")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--physics-scene", help="Optional existing PhysicsScene prim for isolated evaluation")
    parser.add_argument("--timeline", action="store_true", help="Use timeline rather than direct physics steps")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 10000
    if args.samples < 1 or (args.steps is not None and args.steps < 1):
        parser.error("--samples and --steps must be positive")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Choose a new --output directory")
    if not args.config.is_file():
        parser.error("Config file does not exist")
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    manager = None
    task = None
    try:
        import asyncio
        import json
        import omni.kit.app
        import omni.usd
        from pxr import UsdPhysics
        extensions = omni.kit.app.get_app().get_extension_manager()
        extensions.set_extension_enabled_immediate("isaacsim.replicator.grasping", True)
        from isaacsim.replicator.grasping.grasping_manager import GraspingManager
        if not omni.usd.get_context().open_stage(args.scene):
            raise RuntimeError(f"Could not open grasping stage: {args.scene}")
        stage = omni.usd.get_context().get_stage()
        if args.physics_scene and not stage.GetPrimAtPath(args.physics_scene).IsA(UsdPhysics.Scene):
            raise ValueError("--physics-scene must name an existing PhysicsScene")
        manager = GraspingManager()
        statuses = manager.load_config(str(args.config.resolve()))
        failures = {key: value for key, value in statuses.items() if value.startswith(("Failed", "Error"))}
        if failures:
            raise RuntimeError(f"Invalid grasp configuration: {failures}")
        if not manager.get_object_prim_path() or not manager.gripper_path:
            raise ValueError("Gripper and target object must both exist")
        manager.sampler_config["num_candidates"] = args.samples
        if not manager.generate_grasp_poses() or not manager.grasp_locations:
            raise RuntimeError("Antipodal sampler produced no candidates")
        poses = manager.get_grasp_poses(in_world_frame=True)[:args.samples]
        if not poses:
            raise RuntimeError("No world-space grasp poses are available")
        output.mkdir(parents=True)
        manager.store_initial_gripper_pose()
        manager.set_results_output_dir(str(output))
        manager.set_overwrite_results_output(False)
        task = asyncio.ensure_future(manager.evaluate_grasp_poses(
            grasp_poses=poses, render=True, physics_scene_path=args.physics_scene,
            isolate_simulation=bool(args.physics_scene), simulate_using_timeline=args.timeline,
        ))
        step = 0
        while not task.done() and (args.steps is None or step < args.steps):
            if not app.is_running():
                raise RuntimeError("Application closed before evaluation finished")
            app.update()
            step += 1
        if not task.done():
            raise TimeoutError("Evaluation exceeded --steps; partial output is retained")
        task.result()
        captures = sorted(output.glob("capture_*.yaml"))
        if len(captures) != len(poses):
            raise RuntimeError(f"Expected {len(poses)} pose records, got {len(captures)}")
        summary = {"sampled_poses":len(manager.grasp_locations), "evaluated_poses":len(poses),
                   "result_files":[path.name for path in captures],
                   "interpretation":"Gripper state records; no automatic grasp-success label is inferred."}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
        if not args.headless:
            while app.is_running() and (args.steps is None or step < args.steps):
                app.update()
                step += 1
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
            if manager is not None:
                manager.clear()
        finally:
            app.close()


if __name__ == "__main__":
    main()
