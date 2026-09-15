"""Franka 집기와 놓기: 직접 정의한 Task와 내장 Task — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Franka 집기와 놓기: 직접 정의한 Task와 내장 Task')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 1800)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--task", choices=["custom", "builtin"], default="custom")
    parser.add_argument("--target", type=float, nargs=3, default=[-0.3, -0.3, 0.02575], metavar=("X", "Y", "Z"))
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (1800 if args.headless else None)
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.robot.manipulators.examples.franka.tasks import PickPlace
        from isaacsim.robot.manipulators.examples.franka.controllers import PickPlaceController
        from pick_task import LocalPickTask
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        task = (LocalPickTask(target=args.target) if args.task == "custom" else
                PickPlace(name="builtin_pick", target_position=np.array(args.target)))
        world.add_task(task)
        world.reset()
        params = task.get_params()
        robot = world.scene.get_object(params["robot_name"]["value"])
        cube = world.scene.get_object(params["cube_name"]["value"])
        controller = PickPlaceController(name="pick_place", gripper=robot.gripper, robot_articulation=robot)
        controller.reset()
        robot.gripper.set_joint_positions(robot.gripper.joint_opened_positions)
        completed_step = None
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            observations = world.get_observations()
            if not controller.is_done():
                robot.apply_action(controller.forward(
                    picking_position=observations[cube.name]["position"],
                    placing_position=observations[cube.name]["target_position"],
                    current_joint_positions=observations[robot.name]["joint_positions"]))
            world.step(render=not args.headless)
            if not app.is_running():
                return
            if controller.is_done() and completed_step is None:
                completed_step = step
                print("Controller state machine finished at", step, "; checking actual cube pose separately")
            if step % 120 == 0:
                print("step", step, "cube_m", cube.get_world_pose()[0], "controller_done", controller.is_done())
            if completed_step is not None and step - completed_step >= 120:
                break
        if not app.is_running():
            return
        error = float(np.linalg.norm(cube.get_world_pose()[0] - np.array(args.target)))
        result = {"task": args.task, "controller_done": bool(controller.is_done()),
                  "cube_position_m": cube.get_world_pose()[0].tolist(), "target_m": args.target,
                  "cube_target_error_m": error, "within_3cm": error < 0.03}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        app.close()


if __name__ == "__main__":
    main()
