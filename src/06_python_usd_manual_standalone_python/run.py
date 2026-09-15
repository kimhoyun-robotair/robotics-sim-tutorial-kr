import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Environment")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--stage", type=Path, help="Optional local USD stage to open")
    parser.add_argument(
        "--extension",
        action="append",
        default=[],
        help="Extension ID to enable; repeatable",
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

    app = SimulationApp(
        {"headless": args.headless, "width": args.width, "height": args.height}
    )
    try:
        import os
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from isaacsim.core.utils.extensions import enable_extension

        for extension in args.extension:
            enable_extension(extension)
        app.update()
        if args.stage:
            if not args.stage.is_file():
                raise FileNotFoundError(args.stage)
            if not omni.usd.get_context().open_stage(str(args.stage.resolve())):
                raise RuntimeError(f"Could not open {args.stage}")
            app.update()
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 30)
        if not args.stage:
            world.scene.add_default_ground_plane()
            world.scene.add(
                DynamicCuboid(
                    prim_path="/World/Cube",
                    name="cube",
                    position=np.array([0, 0, 2]),
                    size=0.4,
                )
            )
        world.reset()
        counts = {"physics_callbacks": 0, "requested_steps": args.steps}

        def count_physics(dt):
            counts["physics_callbacks"] += 1

        world.add_physics_callback("environment_count", count_physics)
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            world.step(render=not args.headless)
        world.remove_physics_callback("environment_count")
        counts["physics_time_s"] = float(world.current_time)
        counts["environment"] = {
            key: os.environ.get(key)
            for key in ("ISAAC_PATH", "EXP_PATH", "CARB_APP_PATH")
        }
        counts["enabled_extensions"] = args.extension
        counts["requested_resolution"] = [args.width, args.height]
        (output / "environment.json").write_text(json.dumps(counts, indent=2))
        omni.usd.get_context().get_stage().GetRootLayer().Export(
            str(output / "scene.usda")
        )
        print(json.dumps(counts, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
