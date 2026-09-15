"""Capture real Nova Carter stereo views at randomized navigation destinations."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=9)
    parser.add_argument("--steps", type=int, default=None, help="Maximum app updates during generation; omitted: GUI stays open, headless uses 40000")
    parser.add_argument("--env-interval", type=int, default=3)
    parser.add_argument("--use-temp-rp", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--environments", type=Path, default=Path(__file__).with_name("environments.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (40000 if args.headless else None)
    if min(args.frames, args.env_interval) < 1:
        parser.error("frames, steps and env-interval must be positive")
    environments = json.loads(args.environments.read_text())
    if not isinstance(environments, list) or not environments or not all(isinstance(x, str) and x.startswith("/Isaac/") for x in environments):
        parser.error("environments must be a nonempty list of /Isaac/ asset paths")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a new --output; already exists: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    demo = None
    try:
        import omni.replicator.core as rep
        from navigation import NavSDGDemo
        from isaacsim.storage.native import get_assets_root_path
        if not get_assets_root_path():
            raise RuntimeError("Isaac Sim 5.1 asset root unavailable")
        demo = NavSDGDemo()
        demo.start(num_frames=args.frames, out_dir=str(output), env_urls=environments,
                   env_interval=args.env_interval, use_temp_rp=args.use_temp_rp, seed=args.seed)
        updates = 0
        while app.is_running() and demo.is_running() and (step_limit is None or updates < step_limit):
            app.update()
            updates += 1
        if not app.is_running():
            return
        if demo.is_running():
            raise RuntimeError("Navigation did not finish within --steps; inspect asset loading and robot target")
        rep.orchestrator.wait_until_complete()
        images = list(output.rglob("*.png"))
        if len(images) != args.frames * 2:
            raise RuntimeError(f"Expected two stereo images per destination, observed {len(images)} PNGs")
        print(json.dumps({"destinations": args.frames, "stereo_pngs": len(images), "app_updates": updates}))
        while args.steps is None and not args.headless and app.is_running():
            app.update()
    finally:
        try:
            if demo is not None and demo.is_running():
                demo.clear()
        finally:
            app.close()


if __name__ == "__main__":
    main()
