"""Run the installed H1 policy and record its real observation/action contract."""
import argparse
from itertools import count
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 1200")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--speed", type=float, default=0.5, help="Body-frame forward command, m/s")
    parser.add_argument("--policy", type=Path, help="An exported H1 TorchScript policy with the same 69/19 contract")
    parser.add_argument("--environment", type=Path, help="Matching H1 env.yaml")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 1200
    if (args.steps is not None and args.steps < 2) or not 0 <= args.speed <= 1:
        parser.error("steps >= 2 and 0 <= speed <= 1 are required")
    if bool(args.policy) != bool(args.environment):
        parser.error("--policy and --environment must be provided together")
    for path in (args.policy, args.environment):
        if path is not None and not path.is_file():
            parser.error(f"Missing file: {path}")
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "contract.json"
    trace_path = args.output / "trace.csv"
    if report_path.exists() or trace_path.exists():
        parser.error("Output files already exist; choose a fresh --output directory")

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy

        class InspectedH1(H1FlatTerrainPolicy):
            first_observation = None

            def _compute_observation(self, command):
                observation = super()._compute_observation(command)
                if self.first_observation is None:
                    self.first_observation = observation.copy()
                return observation

        world = World(stage_units_in_meters=1.0, physics_dt=0.005, rendering_dt=0.04)
        world.scene.add_default_ground_plane()
        controller = InspectedH1(prim_path="/World/H1", position=np.array([0.0, 0.0, 1.05]))
        if args.policy:
            controller.load_policy(str(args.policy.resolve()), str(args.environment.resolve()))
        world.set_simulation_dt(physics_dt=controller._dt, rendering_dt=8 * controller._dt)
        world.reset()
        joint_names = []
        position, _ = controller.robot.get_world_pose()
        first_step = True
        command = np.array([args.speed, 0.0, 0.0])

        def control(dt: float) -> None:
            nonlocal first_step
            if first_step:
                controller.initialize()
                first_step = False
            else:
                controller.forward(dt, command)

        world.add_physics_callback("h1_policy", control)
        with trace_path.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["physics_step", "x_m", "y_m", "z_m", "command_vx_m_s"])
            for step in count():
                if args.steps is not None and step >= args.steps:
                    break
                if not app.is_running():
                    break
                world.step(render=False)
                if not args.headless and step % 8 == 0:
                    world.render()
                if not app.is_running():
                    break
                joint_names = controller.robot.dof_names
                position, _ = controller.robot.get_world_pose()
                if not np.isfinite(position).all():
                    raise RuntimeError("Robot position became non-finite")
                writer.writerow([step, *position.tolist(), args.speed])
        if controller.first_observation is None:
            if not app.is_running():
                print("Window closed before the first policy inference; trace retained.")
                return
            raise RuntimeError("No policy inference took place")
        report = {
            "joint_names": joint_names,
            "physics_dt": controller._dt,
            "decimation": controller._decimation,
            "policy_hz": 1 / (controller._dt * controller._decimation),
            "default_joint_positions": controller.default_pos.tolist(),
            "first_observation": controller.first_observation.tolist(),
            "last_action": controller.action.tolist(),
            "final_position": position.tolist(),
        }
        with report_path.open("x") as stream:
            json.dump(report, stream, indent=2)
        print(json.dumps(report, indent=2))
    finally:
        app.close()


if __name__ == "__main__":
    main()
