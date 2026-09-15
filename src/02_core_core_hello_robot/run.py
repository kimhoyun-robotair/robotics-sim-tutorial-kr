"""Jetbot USD 참조와 Robot/WheeledRobot 관절 명령 비교 — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Jetbot USD 참조와 Robot/WheeledRobot 관절 명령 비교')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 600 steps)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--api", choices=["robot", "wheeled"], default="robot")
    parser.add_argument("--wheel-speeds", type=float, nargs=2, default=[4.0, 4.0], metavar=("LEFT", "RIGHT"))
    parser.add_argument("--asset", help="Jetbot USD override, absolute file path or URL")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 600
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.robots import Robot
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac 5.1 asset root unavailable; provide --asset /absolute/path/jetbot.usd")
        asset = args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        wheel_names = ["left_wheel_joint", "right_wheel_joint"]
        if args.api == "robot":
            add_reference_to_stage(usd_path=asset, prim_path="/World/Jetbot")
            robot = world.scene.add(Robot(prim_path="/World/Jetbot", name="jetbot"))
        else:
            robot = world.scene.add(WheeledRobot(prim_path="/World/Jetbot", name="jetbot",
                wheel_dof_names=wheel_names, create_robot=True, usd_path=asset))
        print("DOF before reset:", robot.num_dof)
        world.reset()
        wheel_indices = np.array([robot.get_dof_index(name) for name in wheel_names])
        initial_position = robot.get_world_pose()[0].copy()
        print("DOF after reset:", robot.num_dof, "names:", robot.dof_names, "wheel indices:", wheel_indices)
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            if args.api == "robot":
                robot.get_articulation_controller().apply_action(ArticulationAction(
                    joint_velocities=np.array(args.wheel_speeds), joint_indices=wheel_indices))
            else:
                robot.apply_wheel_actions(ArticulationAction(joint_velocities=np.array(args.wheel_speeds)))
            world.step(render=not args.headless)
            if step % 120 == 0:
                print("step", step, "position_m", robot.get_world_pose()[0], "wheel_rad_s", robot.get_joint_velocities()[wheel_indices])
        final_position, orientation = robot.get_world_pose()
        result = {"api": args.api, "dof_names": robot.dof_names, "wheel_indices": wheel_indices.tolist(),
                  "command_rad_s": args.wheel_speeds, "displacement_m": (final_position-initial_position).tolist(),
                  "final_position_m": final_position.tolist(), "orientation_wxyz": orientation.tolist()}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
