import argparse
from itertools import count
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Scripting Concepts")
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
        import csv
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from pxr import UsdLux

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        UsdLux.DistantLight.Define(
            omni.usd.get_context().get_stage(), "/World/Light"
        ).CreateIntensityAttr(1500)
        cube = world.scene.add(
            DynamicCuboid(
                prim_path="/World/FallingCube",
                name="cube",
                position=np.array([0, 0, 2.0]),
                size=0.4,
            )
        )
        world.reset()
        callback_count = 0
        elapsed_time = 0.0

        def on_physics(dt):
            nonlocal callback_count, elapsed_time
            callback_count += 1
            elapsed_time += float(dt)

        world.add_physics_callback("count_physics", on_physics)
        with (output / "timeline.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "loop_iteration",
                    "physics_callbacks",
                    "simulated_time_s",
                    "cube_height_m",
                ]
            )
            for i in count():
                if not app.is_running() or (args.steps is not None and i >= args.steps):
                    break
                world.step(render=not args.headless)
                writer.writerow(
                    [
                        i + 1,
                        callback_count,
                        elapsed_time,
                        float(cube.get_world_pose()[0][2]),
                    ]
                )
        world.remove_physics_callback("count_physics")
        print(
            f"Physics callbacks: {callback_count}, elapsed simulation time: {elapsed_time:.3f} s"
        )
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
