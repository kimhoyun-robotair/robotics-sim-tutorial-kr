"""직접 작성한 차동구동 제어기와 목표 위치 피드백 비교 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='직접 작성한 차동구동 제어기와 목표 위치 피드백 비교')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 900)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--controller", choices=["custom", "differential", "pose"], default="pose")
    parser.add_argument("--linear", type=float, default=0.2, help="Forward velocity m/s")
    parser.add_argument("--angular", type=float, default=0.785398, help="Yaw velocity rad/s (open loop)")
    parser.add_argument("--goal", type=float, nargs=2, default=[0.8, 0.8], metavar=("X", "Y"))
    parser.add_argument("--asset", help="Jetbot USD override")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 900
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.controllers import BaseController
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        from isaacsim.robot.wheeled_robots.controllers import DifferentialController, WheelBasePoseController
        class UnicycleController(BaseController):
            def __init__(self):
                super().__init__(name="local_unicycle")
                self.radius = 0.03
                self.track = 0.1125
            def forward(self, command):
                linear, angular = command
                left = (linear - angular * self.track / 2) / self.radius
                right = (linear + angular * self.track / 2) / self.radius
                return ArticulationAction(joint_velocities=np.array([left, right]))
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset jetbot.usd")
        robot = world.scene.add(WheeledRobot(prim_path="/World/Jetbot", name="jetbot",
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"], create_robot=True,
            usd_path=args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"))
        world.reset()
        custom = UnicycleController()
        differential = DifferentialController(name="differential", wheel_radius=0.03, wheel_base=0.1125)
        pose = WheelBasePoseController(name="pose", open_loop_wheel_controller=differential, is_holonomic=False)
        command = np.array([args.linear, args.angular])
        print("Custom wheel targets rad/s:", custom.forward(command).joint_velocities)
        print("Built-in wheel targets rad/s:", differential.forward(command).joint_velocities)
        goal = np.array([*args.goal, 0.0])
        def drive_robot():
            position, orientation = robot.get_world_pose()
            if args.controller == "pose":
                action = pose.forward(start_position=position, start_orientation=orientation,
                                      goal_position=goal, lateral_velocity=abs(args.linear), position_tol=0.04)
            elif args.controller == "custom":
                action = custom.forward(command)
            else:
                action = differential.forward(command)
            robot.apply_wheel_actions(action)
            world.step(render=not args.headless)

        trajectory = []
        final_position = robot.get_world_pose()[0]
        for step in range(sample_steps):
            if not app.is_running():
                return
            drive_robot()
            if not app.is_running():
                return
            final_position = robot.get_world_pose()[0]
            if step % 60 == 0:
                position = final_position
                trajectory.append({"step": step, "position_m": position.tolist(), "goal_error_m": float(np.linalg.norm(position[:2]-goal[:2]))})
                print(trajectory[-1])
        result = {"controller": args.controller, "goal_m": goal.tolist(), "samples": trajectory,
                  "final_goal_error_m": float(np.linalg.norm(final_position[:2]-goal[:2]))}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print("output=", output)
        while args.steps is None and not args.headless and app.is_running():
            drive_robot()
    finally:
        app.close()


if __name__ == "__main__":
    main()
