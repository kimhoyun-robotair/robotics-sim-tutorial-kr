"""Run genuine installed H1 or Spot policies with a timed velocity sequence."""
import argparse
from itertools import count
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", choices=("h1", "spot"), default="spot")
    parser.add_argument("--robots", type=int, default=1)
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 2000")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output" / "trajectory.csv")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 2000
    if (args.steps is not None and args.steps < 2) or not 1 <= args.robots <= 10:
        parser.error("steps >= 2 and 1 <= robots <= 10 are required")
    if args.output.exists():
        parser.error("Output exists; choose another --output")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy, SpotFlatTerrainPolicy

        dt = 0.005 if args.robot == "h1" else 0.002
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=0.02)
        world.scene.add_default_ground_plane()
        robot_type = H1FlatTerrainPolicy if args.robot == "h1" else SpotFlatTerrainPolicy
        robots = [
            robot_type(
                prim_path=f"/World/Robot_{i}", name=f"robot_{i}",
                position=np.array([0.0, i * 2.0, 1.05 if args.robot == "h1" else 0.8]),
            )
            for i in range(args.robots)
        ]
        world.reset()
        initialized = False
        command = np.zeros(3)

        def control(step_size: float) -> None:
            nonlocal initialized
            if not initialized:
                for robot in robots:
                    robot.initialize()
                initialized = True
            else:
                for robot in robots:
                    robot.forward(step_size, command)

        world.add_physics_callback("policy_sequence", control)
        with args.output.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "robot", "vx_command", "vy_command", "yaw_command", "x", "y", "z"])
            for step in count():
                if args.steps is not None and step >= args.steps:
                    break
                if not app.is_running():
                    break
                phase = int(step * dt / 2) % 3
                command[:] = [(0.4, 0, 0), (0.3, 0, 0.4), (0, 0, 0)][phase]
                world.step(render=False)
                if not args.headless and step % round(0.02 / dt) == 0:
                    world.render()
                if not app.is_running():
                    break
                if step % round(0.1 / dt) == 0:
                    for i, robot in enumerate(robots):
                        position, _ = robot.robot.get_world_pose()
                        writer.writerow([step * dt, i, *command.tolist(), *position.tolist()])
            if app.is_running():
                for robot in robots:
                    print(robot.robot.name, "final world pose:", robot.robot.get_world_pose())
    finally:
        app.close()


if __name__ == "__main__":
    main()
