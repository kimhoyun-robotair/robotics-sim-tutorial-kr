"""낙하 큐브로 World, Scene, 물리 콜백 관찰 — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='낙하 큐브로 World, Scene, 물리 콜백 관찰')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 300 steps)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--height", type=float, default=1.0, help="Initial cube center height in meters")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 300
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        cube = world.scene.add(DynamicCuboid(
            prim_path="/World/FallingCube", name="falling_cube", size=0.5,
            position=np.array([0.0, 0.0, args.height]), color=np.array([0.1, 0.2, 0.9])))
        world.reset()
        assert World.instance() is world
        sample_count = 0
        with (output / "fall.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"])

            def observe(step_size):
                nonlocal sample_count
                position, quaternion = cube.get_world_pose()
                velocity = cube.get_linear_velocity()
                writer.writerow([world.current_time, *position.tolist(), *velocity.tolist()])
                sample_count += 1

            world.add_physics_callback("observe_fall", callback_fn=observe)
            try:
                for step in count():
                    if not app.is_running() or (args.steps is not None and step >= args.steps):
                        break
                    world.step(render=not args.headless)
                    if step % 60 == 0:
                        print(f"step={step} position_m={cube.get_world_pose()[0]} velocity_mps={cube.get_linear_velocity()}")
            finally:
                world.remove_physics_callback("observe_fall")
        result = {"samples": sample_count, "final_position_m": cube.get_world_pose()[0].tolist(),
                  "final_velocity_mps": cube.get_linear_velocity().tolist(), "expected_rest_height_m": 0.25}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
