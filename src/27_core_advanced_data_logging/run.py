"""DataLogger로 Franka 목표 추종 기록과 action/scene 재생 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='DataLogger로 Franka 목표 추종 기록과 action/scene 재생')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 600)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--mode", choices=["record", "trajectory", "scene"], default="record")
    parser.add_argument("--input", type=Path, help="Previously recorded trajectory.json for replay")
    parser.add_argument("--amplitude", type=float, default=0.1, help="Target Y motion amplitude in meters")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 600
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget
        from isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller import RMPFlowController
        if args.mode != "record" and (args.input is None or not args.input.is_file()):
            raise ValueError("Replay requires --input pointing to a recorded trajectory.json")
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        task = FollowTarget(name="follow_for_logging")
        world.add_task(task)
        world.reset()
        params = task.get_params()
        robot = world.scene.get_object(params["robot_name"]["value"])
        target = world.scene.get_object(params["target_name"]["value"])
        logger = world.get_data_logger()
        controller = RMPFlowController(name="follow", robot_articulation=robot)
        replay_errors = []

        def follow_target(step):
            target.set_world_pose(position=np.array([0.45, args.amplitude*np.sin(step/120), 0.45]))
            observation = task.get_observations()[target.name]
            action = controller.forward(target_end_effector_position=observation["position"],
                                        target_end_effector_orientation=observation["orientation"])
            robot.apply_action(action)
            world.step(render=not args.headless)

        if args.mode == "record":
            def log_frame(tasks, scene):
                position, orientation = target.get_world_pose()
                return {"joint_positions": robot.get_joint_positions().tolist(),
                        "applied_joint_positions": robot.get_applied_action().joint_positions.tolist(),
                        "target_position": position.tolist(), "target_orientation": orientation.tolist()}
            logger.add_data_frame_logging_func(log_frame)
            logger.start()
            for step in range(sample_steps):
                if not app.is_running():
                    break
                follow_target(step)
            logger.pause()
            logger.save(log_path=str(output / "trajectory.json"))
        else:
            logger.load(log_path=str(args.input))
            frame_count = logger.get_num_of_data_frames()
            if frame_count == 0:
                raise ValueError("Input log has no frames")
            first = logger.get_data_frame(data_frame_index=0).data
            robot.set_joint_positions(np.array(first["joint_positions"]))
            replay_steps = min(args.steps, frame_count) if args.steps is not None else (min(sample_steps, frame_count) if args.headless else frame_count)
            for index in range(replay_steps):
                if not app.is_running():
                    break
                frame = logger.get_data_frame(data_frame_index=index)
                robot.apply_action(ArticulationAction(joint_positions=np.array(frame.data["applied_joint_positions"])))
                if args.mode == "scene":
                    target.set_world_pose(position=np.array(frame.data["target_position"]),
                                          orientation=np.array(frame.data["target_orientation"]))
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                error = float(np.linalg.norm(robot.get_joint_positions()-np.array(frame.data["joint_positions"])))
                replay_errors.append(error)
                if index % 120 == 0:
                    print("frame", index, "recorded_time_s", frame.current_time, "joint_state_L2_error", error)
        if not app.is_running():
            return
        result = {"mode": args.mode, "data_frames": logger.get_num_of_data_frames(),
                  "replayed_frames": len(replay_errors), "mean_joint_state_L2_error": float(np.mean(replay_errors)) if replay_errors else None,
                  "final_target_m": target.get_world_pose()[0].tolist()}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
        step = sample_steps
        while args.steps is None and not args.headless and app.is_running():
            if args.mode == "record":
                follow_target(step)
                step += 1
            else:
                world.step(render=True)
    finally:
        app.close()


if __name__ == "__main__":
    main()
