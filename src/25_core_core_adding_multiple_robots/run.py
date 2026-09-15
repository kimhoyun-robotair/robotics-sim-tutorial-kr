"""두 로봇의 작업 인계: Jetbot 이동, 후퇴, Franka pick-and-place — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='두 로봇의 작업 인계: Jetbot 이동, 후퇴, Franka pick-and-place')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 2400)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--retreat-steps", type=int, default=200, help="Backward motion steps before picking")
    parser.add_argument("--asset", help="Jetbot USD override")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (2400 if args.headless else None)
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.robot.manipulators.examples.franka.controllers import PickPlaceController
        from isaacsim.robot.wheeled_robots.controllers import DifferentialController, WheelBasePoseController
        from handover_task import HandoverTask
        if args.retreat_steps < 1:
            raise ValueError("--retreat-steps must be positive")
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset jetbot.usd")
        asset = args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        tasks = [HandoverTask(name="handover", jetbot_asset=asset, retreat_steps=args.retreat_steps)]
        for task in tasks:
            world.add_task(task)
        world.reset()
        controllers = []
        for task in tasks:
            drive = WheelBasePoseController(name=task.name + "_pose", open_loop_wheel_controller=
                DifferentialController(name=task.name + "_drive", wheel_radius=0.03, wheel_base=0.1125))
            pick = PickPlaceController(name=task.name + "_pick_control", gripper=task.franka.gripper,
                robot_articulation=task.franka,
                events_dt=[0.008, 0.002, 0.5, 0.1, 0.05, 0.05, 0.0025, 1.0, 0.008, 0.08])
            drive.reset()
            pick.reset()
            controllers.append((drive, pick))
            print("task", task.name, "parameters", task.get_params())
        completed_step = None
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            observations = world.get_observations()
            for task, (drive, pick) in zip(tasks, controllers):
                state = observations[task.name + "_event"]
                if state == 0:
                    pose = observations[task.jetbot.name]
                    task.jetbot.apply_wheel_actions(drive.forward(start_position=pose["position"],
                        start_orientation=pose["orientation"], goal_position=pose["goal_position"]))
                elif state == 1:
                    task.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=np.array([-8.0, -8.0])))
                else:
                    task.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=np.zeros(2)))
                    if not pick.is_done():
                        cube = observations[task.cube.name]
                        task.franka.apply_action(pick.forward(picking_position=cube["position"],
                            placing_position=cube["target_position"],
                            current_joint_positions=observations[task.franka.name]["joint_positions"]))
            world.step(render=not args.headless)
            if step % 120 == 0:
                print("step", step, "events", {task.name: task.event for task in tasks})
            if args.steps is None and not args.headless:
                if completed_step is None and all(pick.is_done() for _, pick in controllers):
                    completed_step = step
                if completed_step is not None and step - completed_step >= 120:
                    break
        if not app.is_running():
            return
        results = []
        for task, (_, pick) in zip(tasks, controllers):
            cube = task.get_observations()[task.cube.name]
            error = float(np.linalg.norm(cube["position"] - cube["target_position"]))
            results.append({"task": task.name, "event": task.event, "controller_done": bool(pick.is_done()),
                "jetbot_position_m": task.jetbot.get_world_pose()[0].tolist(), "cube_position_m": cube["position"].tolist(),
                "target_m": cube["target_position"].tolist(), "cube_target_error_m": error, "within_3cm": error < 0.03})
        (output / "result.json").write_text(json.dumps(results, indent=2))
        print(json.dumps(results), "output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        app.close()


if __name__ == "__main__":
    main()
